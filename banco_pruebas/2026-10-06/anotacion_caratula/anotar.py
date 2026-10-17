import sys, json, hashlib
sys.path.insert(0, '.')
from pathlib import Path
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
REGLAS = {
 "objetivo": "Carátula de la causa para mostrarla en la ficha (decisión de Diego del 17 de Octubre, basta la carátula, no se separa en demandante y demandado). La lee el código, sin IA.",
 "valor": "El texto de la carátula tal como lo imprime el aviso, sin las comillas.",
 "comparacion": "Sin tildes ni mayúsculas, sin puntuación, y sin las palabras 'con' ni '/' entre las partes.",
 "sin_dato": "null si el aviso no trae carátula.",
 "variantes": "Si el aviso la imprime dos veces sin diferencias relevantes (S.A., Ltda o Limitada) cuenta como una (decisión de Diego). Dos carátulas distintas de verdad son duda de lectura.",
}
B06 = {1: "Banco de Crédito e Inversiones/ Bahamondes", 2: "Banco de Crédito e Inversiones/ Gallardo Olivares", 3: "Banco Security/ Soto",
 4: "Renta Nacional Compañía de Seguros de Vida S.A. con Contreras", 5: "Banco Estado de Chile con Claudia Francisca Acevedo Torres", 6: "Mendéz/ Méndez",
 8: "Scotiabank Chile con Figueroa Espinoza, Ulises Nicolas", 9: "Banco de Crédito e Inversiones con González Díaz, Roberto Patricio",
 12: "Scotiabank Chile S.A/ Parra", 13: "Banco de Chile / Hormazábal", 14: "Banco Itaú Chile/ Lagos", 22: "Banco Estado con Castro Quiroz",
 23: "Banco Estado con Figueroa Reyes", 24: "Banco de Crédito e Inversiones con Nicholls", 25: "Banco Santander-Chile con Muñoz",
 26: "Compañía de Seguros Vida Consorcio Nacional de Seguros S.A. con Arque", 28: "Banco Santander - Chile Con Valdés Arépulos",
 29: "Bice con Menendez-Azcarraga", 30: "Banco Estado con Huilitraro Calfucan", 31: "Banco Santander Chile S.A/Peinado Rondón, Elinor Del Valle y Otra",
 35: "Fondo de Inversión Deuda Hipotecaria con Subsidio Habitacional con Aguilar", 36: "Banco Santander Chile con Hernández",
 45: "Banco Internacional con Ce Inmobiliaria III S.A.", 47: "Scotiabank Chile con Lastra", 49: "Scotiabank Chile con Fuentealba",
 51: "Scotiabank Chile/González", 55: None, 56: "Servicios Financieros Sumar / Urrutia", 58: "Banco Estado con Gonzalez Navarro",
 59: "Banco Santander Chile con Celis", 61: "Scotiabank Chile/Parada", 63: "Banco de Crédito e Inversiones con Flores",
 65: "Tanner Servicios Financieros S.A./Investment Advisors Inntegral SpA", 66: "Fondo de Inversión Activa Deuda Hipotecaria con Subsidio Habitacional II/ Castillo",
 68: "Banco de Chile con Comercial Tapia y Cía. Ltda", 69: "Banco Estado con Medina Duarte", 70: "Banco de Crédito e Inversiones con Miranda Castro",
 72: "Soto con Inversiones Harissa Limitada", 75: "Banco Santander-Chile con Gatica", 78: "Scotiabank Chile S.A./Garcia",
 79: "Banco del Estado de Chile con Francisco Gabriel Villalobos Villagra", 80: "Itau-Corpbanca S.A./ Sociedad", 82: "Banco de Crédito e Inversiones/ Díaz",
 83: "Banco del Estado de Chile con Barría", 85: "Banco Estado con Flores González", 86: "Urra / Empresa de Construcción ConstrupartnerS SpA",
 87: "Banco Estado con Palma Lagos", 88: "Banco Estado con Moya Miranda", 89: "Compañía de Seguros de Vida Consorcio Nacional de Seguros S.A. con Zuñiga",
 90: "Banco Falabella/ Olmedo", 91: "Banco Estado con Guzmán Guerra", 92: "Cooperativa de Ahorro y Crédito Coopeuch/ Carilao",
 93: "Banco Santander-Chile con Torrejón Velásquez Lily", 94: "Banco de Chile/ Chacón", 95: "Itaú Corpbanca/ Azabache",
 97: "Agrícola, Forestal y Ganadera San José de Colliguay Limitada/ Empresa Eléctrica Blanco SpA.", 98: "Banco de Chile/ Aguirre",
 102: "Banco de Crédito e Inversiones con Guevara", 103: "Banco Estado con Rojas Barrera"}
NOTAS06 = {75: "Al final del aviso viene pegado un aviso de posesión efectiva con la carátula 'Charad/ Charad'. Si el programa lo marca como duda de lectura, cuenta como no leído (aceptable).",
           68: "La imprime dos veces, con Ltda y con Limitada. Es la misma (decisión de Diego).", 55: "El aviso no trae carátula."}
B14 = {1: "Banco del Estado Con Covarruvias Leiva", 2: "Banco del Estado Con Bustamante González", 3: "Banco Santander - Chile S.A./Arh Empresa de Servicios Transitorios SpA",
 4: "Banco de Chile con Aguilera", 5: "Banco de Crédito e Inversiones con Montecino", 6: "Banco de Crédito e Inversiones/Pérez",
 7: "Banco del Estado de Chile con Rodolfo Antonio Ulloa Batista", 8: "Banco del Estado de Chile con Amaya Faura, Juan Ernesto",
 9: "Banco del Estado con Fuenzalida Moraga, José Miguel y otra", 10: "Seguros con Inmobiliaria",
 11: "Fondo de Inversión Activa Deuda Hipotecaria Con Subsidio Habitacional II/Ravello", 12: "Banco Estado con Riveros Gallardo",
 13: "Banco Estado con Morales Chamorro", 14: "Banco de Chile con Sepúlveda", 15: "Banco Estado con Alfaro", 16: "Banco Itaú Chile S.A/ Mera",
 17: "Augustar Seguros de Vida S.A./Herrera", 18: "Seguros Vida Security Prevision S.A. con Diaz", 19: "Banco Estado con Ibañez Rojas",
 20: "Banco Estado con Reyes Ibazeta", 21: "Scotiabank Chile con Huenhupi Ayala, Jose Francisco", 22: "Securitizadora Security S.A. con Tilleria",
 23: "Banco de Chile/López", 24: "Banco Estado con Adasme Soto", 25: "4 Life con Sociedad", 26: "Banco de Crédito e Inversiones/ Flores",
 27: "Banco Santander Chile con Fuentes", 28: "Banco de Crédito e Inversiones/Pastrián", 29: "Banco Falabella/Ojeda",
 30: "Banco Internacional con Ce Inmobiliaria III S.A.", 31: "Banco Estado con Westermeier López", 32: "Scotiabank Chile con Pachon",
 33: "Banco Itaú Chile S.A/ Carrasco", 34: "Banco Santander-Chile S.A. con Gutiérrez", 35: "Banco de Chile con Salmiq SpA",
 36: "Metlife Chile Seguros de Vida S.A. con Galvez Oyarce, Paulina Andrea", 37: "Banco Estado con Azócar Reyes",
 38: "Metlife Chile Seguros de Vida S.A. con Román", 39: "Banco de Crédito e Inversiones con Baeza", 40: "Seguros con González",
 41: "Scotiabank Chile con Barahona", 42: "Banco de Chile con Miranda", 43: "Banco Falabella con Bodaleo", 44: "Scotiabank Chile S.A./Gil",
 45: "Banco del Estado con Contreras Ríos", 46: "CAT Administradora de Tarjetas S.A./ Moreno", 47: "Banco de Crédito e Inversiones con Barraza",
 48: "Banco Estado con Valdés Galaz", 49: "Banco Itaú Chile S.A./ Rubilar", 50: "Fondo con Villegas", 51: "Banco Santander-Chile con Vera",
 52: "Bice Vida Compañía de Seguros S.A. Con Quiroga Brant", 53: "Banco del Estado de Chile con Francisco Javier Ruiz Godoy",
 54: "Scotiabank Chile con Arevalo Arevalo Daniel", 56: "Navarrete con Tresam Ingenieria y Servicios Mecanicos Ltda.",
 59: "Banco de Crédito e Inversiones con Velasco", 61: "Barrera con López"}
for cual, B, NOTAS, NOM in (('06', B06, NOTAS06, [104, 105, 107]), ('14', B14, {}, [55, 57, 58, 60])):
    if cual == '06': d, pags, ed = Path('banco_pruebas/2026-10-06'), ('B7','B8','B9','B10'), '2026-10-06'; ns = [x['n'] for x in json.load(open(d/'banco_vale_vista_2026-10-06.json', encoding='utf-8'))['avisos']]
    else: d, pags, ed = Path('banco_pruebas/2026-10-14'), ('B11','C8'), '2026-10-14'; ns = [x['n'] for x in json.load(open(d/'banco_nivel2_2026-10-14.json', encoding='utf-8'))['avisos']]
    r, m = construir_rollo([(n, leer_pagina(d / f'mercurio_{ed}_{n}.txt')) for n in pags]); av = {a.orden: a for a in cortar(r, m)}
    assert sorted(set(ns)) == sorted(set(B) | set(NOM)), (cual, set(ns) ^ (set(B) | set(NOM)))
    regs, prob = [], 0
    for n in ns:
        if n in NOM: regs.append({"n": n, "no_se_mide": "partición (se descarta)"}); continue
        if B[n] and B[n] not in av[n].texto: prob += 1; print(cual, n, 'NO ESTÁ', B[n])
        x = {"n": n, "caratula": B[n]}
        if n in NOTAS: x["nota"] = NOTAS[n]
        regs.append(x)
    out = {"edicion": ed, "anotado_por": "Claude (Opus 5.5), 17 de Octubre de 2026, ANTES de escribir el código de la carátula",
           "uso": "VALIDACIÓN de la parte 3.7c. Se corre una sola vez con el código congelado." if cual == '06' else "AJUSTE de la parte 3.7c.",
           "reglas": REGLAS, "avisos": regs}
    txt = json.dumps(out, ensure_ascii=False, indent=1); (d / f'banco_caratula_{ed}.json').write_text(txt, encoding='utf-8')
    print(cual, 'medibles', sum(1 for r in regs if 'caratula' in r), 'problemas', prob, 'md5', hashlib.md5(txt.encode('utf-8')).hexdigest())
