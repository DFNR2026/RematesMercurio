import sys, json, re, hashlib
sys.path.insert(0, '.')
from pathlib import Path
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
from motor.numeros_texto import numeros_en, _sin_tildes
def C(calle, numero, unidad, comuna, **k): return dict(tipo="calle", calle=calle, numero=numero, unidad=unidad, comuna=comuna, descripcion=None, **k)
def S(descripcion, comuna, unidad=None, **k): return dict(tipo="sin_calle", calle=None, numero=None, unidad=unidad, comuna=comuna, descripcion=descripcion, **k)
REGLAS = {
 "objetivo": "Dirección del inmueble para mostrarla en la ficha (decisión de Diego del 17 de Octubre). No se usa para la clave del bien ni para filtrar.",
 "calle": "Nombre de la calle tal como lo imprime el aviso, con su tipo si lo trae (calle, Avenida, Pasaje, Camino). Se compara sin tildes, sin mayúsculas y sin el tipo.",
 "numero": "Número de la calle en cifras, conservando el cero inicial (0337). Si viene en palabras se pasa a cifras. Rangos y dos números se escriben como en el aviso (0344-0358, 575 y 577). Se compara por los números que contiene, sin ceros a la izquierda.",
 "unidad": "Solo la pieza principal que se vende dentro de un edificio o condominio (departamento, casa, oficina, local, vivienda, unidad). No el lote o sitio del plano de una casa con calle y número. Si se venden depto, bodega y estacionamiento juntos, va el depto. Se compara por tipo y número.",
 "comuna": "La comuna del inmueble, no la del tribunal. Si el aviso dice 'comuna San Miguel, hoy comuna San Joaquín' va la de hoy. Si el aviso no nombra la comuna, null (no se deduce del conservador).",
 "sin_calle": "Terreno o sitio sin calle ni número (parcela, lote, hijuela, sitio de un conjunto sin calle). Va su descripción corta. Solo se comparan el tipo y la comuna.",
 "lista": "Un aviso con varios remates (lista de mínimos) lleva una dirección por remate, en el mismo orden.",
 "alternativas": "Lectura distinta que también se acepta cuando el aviso es ambiguo (se dice por qué en la nota).",
}
B06 = {
 1: [C("calle Las Acacias", "02927", None, "San Bernardo")],
 2: [C("calle Alicahue", "18453", "casa 10-C", "San Bernardo")],
 3: [C("Avenida El Canal", "21500", "casa 71", "Pudahuel")],
 4: [C("Avenida Santa Ana", "079", "departamento 307", "La Granja")],
 5: [C("calle el bosque", "091", None, "Buin")],
 6: [C("Los Sanhuezas", "9", None, "Tomé")],
 8: [C("pasaje lanceros del rey", "5946", None, "estación central")],
 9: [S("Lote 30-24, Parcela número Treinta, Parcelación Culiprán", "Melipilla")],
 12: [C("calle Pablo Urzúa", "1481", "departamento 601-A", "Independencia")],
 13: [S("sitio 39 de la manzana 3, conjunto habitacional La Abadía De San Pablo II", "Pudahuel")],
 14: [C("calle Jardín Oriente", "0181", "casa 9", "Til Til")],
 22: [C("calle Ciprés de la Cordillera", "8768", None, "La Florida")],
 23: [C("Pasaje San Camilo", "10906", None, "La Pintana")],
 24: [C("Pasaje Asturcón", "1588", None, "Huechuraba")],
 25: [C("calle Filomena Bonell González", "393", None, "Buin")],
 26: [C("Avenida Costanera del Río", "213", "departamento 228", "La Serena")],
 28: [C("pasaje Chonchi", "247", None, "San Joaquín")],
 29: [C("calle Portugal", "910", "departamento 606", "Santiago")],
 30: [C("calle San Francisco", "15321", None, "San Bernardo")],
 31: [C("calle Los Olmos", "3031", "departamento 1110", "Macul")],
 35: [C("calle Cardenal Raúl Silva", "1636", None, "Buin")],
 36: [C("pasaje la reconquista", "2355", None, "Maipú")],
 45: [C("calle Maipú", "636", "casa 1", "Santiago"), C("calle Maipú", "636", "casa 3", "Santiago"),
      C("calle Maipú", "636", "casa 5", "Santiago"), C("calle Maipú", "636", "estacionamiento 6", "Santiago")],
 47: [C("La Capilla", "1415", "vivienda 1415-23", "Huechuraba", unidad_opcional=True)],
 49: [C("calle Gerónimo de Alderete", "1944", "departamento 1303", "La Florida")],
 51: [C("calle Ejército", "381", "departamento 303", "Puerto Montt")],
 55: [C("Avenida Mauque", "0525", "departamento 248", "Rancagua")],
 56: [C("Avenida Presidente Ibáñez", "1004", None, "linares")],
 58: [C("Pasaje Estación Casma", "3257", None, "Puente Alto")],
 59: [C("calle Eleuterio Ramírez", "1491", "departamento 1104", "Santiago")],
 61: [C("Avenida Vicuña Mackenna Poniente", "6130", "departamento 913", "La Florida")],
 63: [C("Avenida Vicuña Mackenna", "4927", "departamento 2605", "San Joaquín")],
 65: [S("Edificio Buena Vista", "Puerto Varas", unidad="departamento D102")],
 66: [C("Calle Palqui Sur", "587", None, None)],
 68: [C("calle Diagonal Teniente Cruz", "555", "departamento 101", "Pudahuel")],
 69: [C("calle Sergio Valdovinos", "1410", "departamento 107-B", "Quinta Normal")],
 70: [C("Pasaje Bretón", "7860", None, "Huechuraba")],
 72: [C("Avenida El Bosque", "1234", "departamento 902", "Providencia")],
 75: [C("Avenida Padre Alberto Hurtado", "0131", "departamento 403", "Estación Central")],
 78: [C("calle Carvajal", "0344-0358", "departamento 1501", "La Cisterna")],
 79: [C("Avenida Ecuador", "4698", "departamento 2002", "Estación Central")],
 80: [C("calle Ahumada", "312", "oficina 213", "Santiago")],
 82: [C("calle Alcalde Julio Arangua Nuñez Sur", "304", None, "Peñaflor")],
 83: [C("Avenida Eleodoro Yáñez", "2566", "departamento 41", "providencia")],
 85: [C("pasaje Cerdeña", "1324", None, "Maipú")],
 86: [C("Pasaje Brahms", "10516", None, "La Florida")],
 87: [C("Avenida General San Martín", "3275", "departamento 217", "Maipú")],
 88: [C("Pasaje Pintor Mauricio Rugendas", "2743", None, "Cerrillos")],
 89: [C("Pasaje Mangostino", "3029", None, "Rancagua")],
 90: [S("Parcela número 4 del Loteo Los Tilos", None)],
 91: [C("Avenida Las Naciones", "2251", "casa 18", "Maipú")],
 92: [C("calle Santa Amalia", "0161", "departamento 311", "La Florida")],
 93: [C("Pasaje Volcán Isluga", "3695", None, "Puente Alto")],
 94: [C("calle Padre Alberto de Agostini O.S.", "1698", None, "Padre Hurtado")],
 95: [C("calle Carretera Panamericana Presidente Roosevelt", "670", "departamento 12", "Santiago")],
 97: [S("Lote A-Uno del plano de subdivisión del resto del lote A del Fundo Los Chenques", "Santa Bárbara")],
 98: [C("Pasaje Los Vientos", "149", None, "Til Til")],
 102: [C("calle Uno", "6590/6594", "departamento 807", "La Cisterna")],
 103: [C("calle Apóstol Bartolomé", "4090", None, "Puente Alto")],
}
ALT06 = {14: ([C("Pasaje La Vendimia D", "17", "casa 9", "Til Til")], "La casa tiene acceso particular por Pasaje La Vendimia D diecisiete y el condominio está en calle Jardín Oriente número cero ciento ochenta y uno. Se aceptan las dos."),
         28: ([C("pasaje Chonchi", "247", None, "San Miguel")], "El aviso dice 'comuna San Miguel, hoy comuna San Joaquín'. Se anota la de hoy y se acepta la antigua."),
         95: ([C("calle Carretera Panamericana Presidente Roosevelt", "670", "departamento 12", "Santiago")], "Depto 12 del edificio colectivo 14. Se anota el depto.")}
NOTAS06 = {66: "El aviso no nombra la comuna (solo el Conservador de Casablanca).", 90: "El aviso no nombra la comuna (solo el Conservador de Buin).",
           65: "Departamento sin calle, solo 'edificio Buena Vista, ubicado en la ciudad y comuna de Puerto Varas'.",
           47: "'la vivienda 1415-23 ubicada en La Capilla 1415, lote 23'. La unidad es opcional.",
           55: "El aviso nombra también calle Nueva Trapiche N° 2555 (el terreno del condominio). La dirección es el acceso del depto, Avenida Mauque 0525.",
           29: "También nombra el acceso a estacionamientos por Avenida Portugal N° 918. La dirección es calle Portugal N° 910."}
B14 = {
 1: [C("calle Santiago Bueras", "3951", None, "Peñaflor")], 2: [C("calle La Viña", "1544", None, "Puente Alto")],
 3: [C("Avenida Pajaritos", "3195", "oficina 602", "Maipú"), C("Avenida Pajaritos", "3195", "oficina 603", "Maipú")],
 4: [C("calle Álvarez de Toledo", "861", None, "San Miguel")], 5: [C("El Maitén", "28", None, "Til Til")],
 6: [C("Avenida Vicuña Mackenna Oriente", "7320", "departamento 1504", "La Florida")], 7: [C("Pasaje Rio Rapel", "13362", None, "El Bosque")],
 8: [C("calle Laura Rodig", "9225", None, "La Florida")], 9: [C("Avenida Central", "1725", "vivienda 77", "Puente Alto")],
 10: [C("Avenida Santa Clara", "301", "oficina 7801", "Huechuraba")], 11: [C("calle 20 Norte", "1715", "departamento 403", "Talca")],
 12: [C("Avenida Américo Vespucio", "0337", None, "La Granja")], 13: [C("calle Santa Inés Oriente", "2118", None, "San Bernardo")],
 14: [C("Pasaje Los Universitarios", "2116", None, "Maipú")], 15: [C("Avenida Américo Vespucio", "1414", None, "Maipú")],
 16: [C("calle Agustinas", "1888", "departamento 302 D", "Santiago")], 17: [C("Pasaje Río La Ligua", "9555", None, "Pudahuel")],
 18: [C("calle Piedemonte", "18551", "unidad 112", "San Bernardo")], 19: [C("Pasaje Ríos de Chile", "2942", None, "Maipú")],
 20: [C("Avenida Paseo Pie Andino", "02639", "casa 67", "Puente Alto")],
 21: [S("Lote Dos, Hijuela Segunda, Antiguo Fundo Cuesta Vieja", "Curacaví")], 22: [C("Pasaje Cerro Puntiagudo", "9525", None, "Pudahuel")],
 23: [C("calle Cuarta Avenida", "1447", "departamento 705", "San Miguel")], 24: [C("Pasaje Ocho", "55", None, "Buin")],
 25: [C("General Gana", "1063", "departamento 2302-B", "Santiago")], 26: [C("Calle Pedrales", "01867", None, "Puente Alto")],
 27: [C("calle Apóstol Santiago", "32", "departamento 2017", "Estación Central")], 28: [C("Avenida Transversal Uno", "939", None, "Pudahuel")],
 29: [C("calle Valle La Reserva", "588", None, "Isla de Maipo")],
 30: [C("calle Maipú", "636", "casa 1", "Santiago"), C("calle Maipú", "636", "casa 3", "Santiago"), C("calle Maipú", "636", "casa 5", "Santiago"), C("calle Maipú", "636", "estacionamiento 6", "Santiago")],
 31: [C("Avenida Macul", "4747", "departamento 68", "Macul")], 32: [C("calle Abtao", "24", "departamento 1109", "Estación Central")],
 33: [C("calle Los Alerces", "3330", "departamento 306-A", "Ñuñoa")], 34: [S("Parcela N° 21, Parcelación El Cuadro de Sorrento", "Talagante")],
 35: [S("Parcela 112, Resto del Fundo Monterrey", "Curacaví")], 36: [C("calle Alcalde Pedro Alarcón", "777", "departamento 310", "San Miguel")],
 37: [C("calle Jenequeo", "5765", None, "Quinta Normal")], 38: [C("Avenida Bernardo O’Higgins", "4050", "oficina 1316", "Estación Central")],
 39: [C("Avenida Las Perdices", "3462", "departamento 302", "Puente Alto")], 40: [C("Camino al Volcán", "29016", None, "San José de Maipo")],
 41: [C("Pasaje Jose Salum Arcuch", "768", None, "Peñaflor")], 42: [C("Avenida Lo Ovalle", "0926", "departamento A 309", "La Cisterna")],
 43: [C("calle Emilia Téllez", "4849", "departamento 59", "Ñuñoa")], 44: [C("Avenida Macul", "3700", "departamento 810-B", "Macul")],
 45: [C("calle Asunción", "2659", None, "Maipú")], 46: [S("sitio número 5 de la manzana 1, loteo El Manzano", None)],
 47: [C("calle Álvarez de Toledo", "924", "departamento 1306", "San Miguel")], 48: [C("Avenida Presidente Balmaceda", "2914", "departamento 2104", "Santiago")],
 49: [C("Avenida Brasil", "875", "departamento 1020", "Santiago")], 50: [C("calle Camino Nuevo", "2065", "departamento C-2302", "Chillán")],
 51: [C("calle Merced", "22", "departamento 402", "Santiago")], 52: [C("calle Las Cimas", "734", "unidad 75", "Til Til")],
 53: [C("calle Sotomayor", "575 y 577", None, "Santiago")], 54: [C("Avenida Ossa", "480", "departamento 211", "La Cisterna")],
 56: [S("Lote o Hijuela Cuatro A, Chiquio", "Puerto Montt")], 59: [C("calle Juan Moya Morales", "22", "departamento 603", "Ñuñoa")],
 61: [C("calle Mapocho", "2676", "departamento 406", "Santiago")],
}
NO_MIDE14 = [55, 57, 58, 60]; NO_MIDE06 = [104, 105, 107]
def norm(t): return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", _sin_tildes(t or ""))).strip()
def avisos(cual):
    if cual == '06': d, pags, ed = Path('banco_pruebas/2026-10-06'), ('B7', 'B8', 'B9', 'B10'), '2026-10-06'
    else: d, pags, ed = Path('banco_pruebas/2026-10-14'), ('B11', 'C8'), '2026-10-14'
    r, m = construir_rollo([(n, leer_pagina(d / f'mercurio_{ed}_{n}.txt')) for n in pags])
    return d, ed, {a.orden: a for a in cortar(r, m)}
def revisar(texto, x):
    p = []; nt = norm(texto); nums = {n.lstrip('0') or '0' for n in numeros_en(texto)}
    if x["calle"] and norm(x["calle"]) not in nt: p.append(f"calle '{x['calle']}' no está")
    if x["numero"]:
        for n in re.findall(r"\d+", x["numero"]):
            if (n.lstrip('0') or '0') not in nums: p.append(f"número {n} no está")
    if x["unidad"]:
        for n in re.findall(r"\d+", x["unidad"]):
            if (n.lstrip('0') or '0') not in nums: p.append(f"número de unidad {n} no está")
    if x["comuna"] and norm(x["comuna"]) not in nt: p.append(f"comuna '{x['comuna']}' no está")
    return p
for cual, B, ALT, NOTAS, NOM in (('06', B06, ALT06, NOTAS06, NO_MIDE06), ('14', B14, {}, {}, NO_MIDE14)):
    d, ed, av = avisos(cual)
    if cual == '06':
        ns = [x['n'] for x in json.load(open(d / 'banco_vale_vista_2026-10-06.json', encoding='utf-8'))['avisos']]
    else:
        ns = [x['n'] for x in json.load(open(d / 'banco_nivel2_2026-10-14.json', encoding='utf-8'))['avisos']]
    faltan = [n for n in ns if n not in B and n not in NOM]; sobran = [n for n in B if n not in ns]
    assert not faltan and not sobran, (cual, faltan, sobran)
    regs, problemas = [], 0
    for n in ns:
        if n in NOM:
            regs.append({"n": n, "no_se_mide": "partición (se descarta)"}); continue
        r = {"n": n, "remates": B[n]}
        for x in B[n]:
            pr = revisar(av[n].texto, x)
            if pr: problemas += 1; print(cual, n, pr)
        if n in ALT: r["alternativas"] = [ALT[n][0]]; r["nota"] = ALT[n][1]
        if n in NOTAS: r["nota"] = (r.get("nota", "") + " " + NOTAS[n]).strip()
        regs.append(r)
    out = {"edicion": ed, "anotado_por": "Claude (Opus 5.5), 17 de Octubre de 2026, ANTES de escribir instrucciones o código de la IA de la dirección",
           "uso": "VALIDACIÓN de la parte 3.7b. Se corre una sola vez con el código congelado." if cual == '06' else "AJUSTE de la parte 3.7b. Reanotado desde banco_nivel2_2026-10-14.json (campo direccion), que queda igual.",
           "reglas": REGLAS, "avisos": regs}
    nombre = d / f'banco_direccion_{ed}.json'
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    nombre.write_text(txt, encoding='utf-8')
    print(cual, 'registros', len(regs), 'medibles', sum(1 for r in regs if 'remates' in r), 'remates', sum(len(r.get('remates', [])) for r in regs), 'problemas', problemas, 'md5', hashlib.md5(txt.encode('utf-8')).hexdigest())
