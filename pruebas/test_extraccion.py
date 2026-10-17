"""Prueba de la extracción por código (parte 3.6) contra el banco del 14 de Octubre, que es el banco de AJUSTE.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_extraccion
Falla si algún dato sale EQUIVOCADO o si los aciertos bajan del mínimo logrado. El banco de validación (6 de Octubre)
no se usa aquí. Se mide aparte con pruebas.medir_extraccion 06, solo al final.
"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
from motor.extraccion import extraer
from motor.partidor import es_partidor, normalizar

MINIMOS = {"fecha_remate": 60, "hora_remate": 60, "minimo": 61, "garantia": 61, "modalidad": 59, "tribunal": 61}   # logrados el 2026-10-15 (etapas 1 a 5). Tribunal sin contar partidores, que se descartan. Solo pueden subir.


def _resumen_minimo(m):
    els = m.get("lista") or [m]
    if all(e.get("monto") is None for e in els): return None
    return [(round(e["monto"], 6), e.get("moneda"), e.get("costas_clp")) for e in els]

D = RAIZ / "banco_pruebas" / "2026-10-14"
r, m = construir_rollo([(n, leer_pagina(D / f"mercurio_2026-10-14_{n}.txt")) for n in ("B11", "C8")])
av = {a.orden: a for a in cortar(r, m)}
banco = json.loads((D / "banco_nivel2_2026-10-14.json").read_text(encoding="utf-8"))["avisos"]

fallas, aciertos = [], {c: 0 for c in MINIMOS}
for e in banco:
    todo = extraer(av[e["n"]].texto, "2026-10-14")
    x = {"fecha_remate": todo["fecha_remate"], "hora_remate": todo["hora_remate"], "alertas": todo["alertas"]}
    mc = {"minimo": todo["minimo"], "alertas": []}
    x["minimo"] = {"valor": _resumen_minimo(mc["minimo"]), "cita": (mc["minimo"].get("lista") or [mc["minimo"]])[0].get("cita")}
    e = dict(e, minimo={"valor": _resumen_minimo(e["minimo"])})
    gx = todo["garantia"]
    x["garantia"] = {"valor": (gx["porcentaje"], gx["base"], gx["monto"]), "cita": gx["cita"]}
    ge = e["garantia"]
    e = dict(e, garantia={"valor": (ge.get("porcentaje"), ge.get("base") or "sin_dato", ge.get("monto"))})
    mo = todo["modalidad"]
    x["modalidad"] = {"valor": None if mo["valor"] == "sin_dato" else mo["valor"], "cita": mo["cita"]}
    e = dict(e, modalidad={"valor": None if e["modalidad"]["valor"] in (None, "sin_dato") else e["modalidad"]["valor"]})
    tr = todo["tribunal"]
    x["tribunal"] = {"valor": normalizar(tr["valor"]) if tr["valor"] else None, "cita": tr["cita"]}
    e = dict(e, tribunal={"valor": normalizar(e["tribunal"])})
    if es_partidor(None, av[e["n"]].texto):
        x["tribunal"]["valor"] = e["tribunal"]["valor"]
    for c in MINIMOS:
        esperado, obtenido = e[c]["valor"], x[c]["valor"]
        if obtenido is not None and obtenido != esperado:
            fallas.append(f"EQUIVOCADO {c} aviso {e['n']} esperado {esperado} obtenido {obtenido}")
        if obtenido == esperado:
            aciertos[c] += 1
        if obtenido is not None and x[c]["cita"] is not None and x[c]["cita"] not in av[e["n"]].texto:
            fallas.append(f"cita que no está en el aviso {c} aviso {e['n']}")
# Casos fijos de tribunal, tomados de textos reales de otras ediciones (cada uno motivó una regla)
CASOS_TRIBUNAL = {
    "EN AUTOS ROL C-2237-2025, del 2° Juzgado de Letras Civil de Chillán, caratulados": "2° Juzgado Civil de Chillán",
    "7° JUZGADO CIVIL, EN calle Huérfanos 1409, piso 2, Santiago, se rematará": "7° Juzgado Civil de Santiago",
    "EXTRACTO 17° JUZGADO DE LEtras de Santiago. Causa hipotecaria": "17° Juzgado Civil de Santiago",
    "EXTRACTO JUZGADO DE LETRAS de Cobranza Laboral de Temuco. Rit C-357- 2024.": "Juzgado de Cobranza Laboral de Temuco",
    "REMATE ANTE EL JUZgado de Letras del Trabajo de San Bernardo, Urmeneta 467": "Juzgado de Letras del Trabajo de San Bernardo",
    "REMATE ANTE DÉCIMO QUINTO (15°) JUZGADO CIVIL DE SANTIAGO, Huérfanos": "15° Juzgado Civil de Santiago",
    "VIGÉSIMO CUARTO JUZgado Civil de Santiago, Huérfanos 1409": "24° Juzgado Civil de Santiago",
    "REMATE 1° JUZGADO CIVIL DE SAN Miguel, Ureta Cox 855": "1° Juzgado Civil de San Miguel",
}
for texto, esperado in CASOS_TRIBUNAL.items():
    obtenido = extraer(texto)["tribunal"]["valor"]
    if obtenido != esperado:
        fallas.append(f"tribunal fijo. '{texto[:40]}' dio {obtenido} y debía dar {esperado}")
print(f"casos fijos de tribunal {len(CASOS_TRIBUNAL)}")

# Parte 3.7b (17 de Octubre). Inscripción en el Conservador, casos reales de las ediciones capturadas. Solo identifica la
# propiedad (decisión de Diego), no filtra. Se esperan fojas, número y año sin puntos.
from motor.extraccion import inscripcion, minimo_y_costas
CASOS_INSCRIPCION = {
    # 01-09 aviso 44
    "Inscripción a Fojas 7.694, Número 6.390 del Registro de Propiedad del año 2009 del Conservador de Bienes Raíces de La Serena. Mínimo":
        "fojas 7694 n 6390 2009",
    # 01-09 aviso 50, el año va después del conservador
    "Inscripción a fojas 39.341, número 59.430 del Registro de Propiedad del Conservador de Bienes Raíces de Santiago correspondiente al año 2010. Mínimo":
        "fojas 39341 n 59430 2010",
    # 06-10 aviso 73, "N" pegado al número y "vuelta"
    "inscrito a fojas 57.106 N81.820 del Registro de Propiedad del año 2017": "fojas 57106 n 81820 2017",
    "inscrito a fojas 5.431 vuelta N° 6.193 del Registro de Propiedad del año 2017": "fojas 5431 n 6193 2017",
    # 09-10 aviso 83, dos inscripciones (depto y bodega) que comparten el año
    "inscrito a fojas 44321, número 64342 y fojas 44321, número 64343 respectivamente, Registro Propiedad año 2023, Conservador":
        "fojas 44321 n 64342 2023 + fojas 44321 n 64343 2023",
    # 14-10 aviso 30, "bajo el N°"
    "inscritos a nombre de CE Inmobiliaria III S.A. a fojas 44773 bajo el N° 66273 del Registro de Propiedad del Conservador de Bienes Raíces de Santiago correspondiente al año 2015":
        "fojas 44773 n 66273 2015",
    # formas vistas el 17 de Octubre
    "a Fojas 5914v N° 6254, en el Registro de Propiedad del Conservador de Bienes Raíces de Antofagasta del año 2016.": "fojas 5914 n 6254 2016",
    "la inscripción de fojas 24.045 No. 38.549 del Registro de Propiedad del Conservador de Bienes Raíces de Santiago del año 2.007.": "fojas 24045 n 38549 2007",
    "inscrito a fojas 14. 515 N° 13.762 del registro de propiedad correspondiente al año 2008": "fojas 14515 n 13762 2008",
    "Propiedad inscrita fojas Fs. 76060 N° 106266 Registro Propiedad Conservador Bienes Raíces Santiago del año 2025.": "fojas 76060 n 106266 2025",
    "Fojas 77233, Número 112258, del Registro de Propiedad del 2021, del Conservador": "fojas 77233 n 112258 2021",
    # 06-10 aviso 53, tres inscripciones con el año al final
    "fojas 79793, n° 112451, fojas 79794 n° 112452, y fojas 79795, n° 112453, todas del registro de propiedad del año 2020 del Conservador":
        "fojas 79793 n 112451 2020 + fojas 79794 n 112452 2020 + fojas 79795 n 112453 2020",
    # inventado a propósito. La hipoteca no identifica la propiedad
    "inscrito a fojas 100 número 200 del Registro de Propiedad del año 2010, y la hipoteca a fojas 300 número 400 del Registro de Hipotecas del año 2011.":
        "fojas 100 n 200 2010",
    "El inmueble no trae inscripción en este aviso.": None,
}
for texto, esperado in CASOS_INSCRIPCION.items():
    obtenido = inscripcion(texto)["clave"]
    if obtenido != esperado:
        fallas.append(f"inscripción. '{texto[:50]}' dio {obtenido} y debía dar {esperado}")
for el in inscripcion(" ".join(CASOS_INSCRIPCION))["inscripcion"]:
    if el["cita"] not in " ".join(CASOS_INSCRIPCION):
        fallas.append(f"inscripción. cita que no está en el texto ({el['cita'][:50]})")
alerta = inscripcion("fojas 68126 N° 102.893, Registro Propiedad año 2033, Conservador Bienes Raíces Santiago", "2026-10-09")["alertas"]
if not (alerta and alerta[0][0] == "error_escritura"):
    fallas.append("inscripción. año 2033 sin alerta de error de escritura (09-10 aviso 119)")
print(f"casos fijos de inscripción {len(CASOS_INSCRIPCION)}")
# Marcha blanca del 17 de Octubre. Las alertas muestran las fechas con el mes en palabras, nunca en número (pedido de Diego).
_al = extraer("REMATE 28° JUZGADO CIVIL DE Santiago, se rematará el día 26 de mayo de 2026, a las 13:50 horas. Mínimo $ 1.000.000.", "2026-10-15")["alertas"]
if not any(t == "La fecha del remate (26 de Mayo de 2026) es anterior a la edición del diario (15 de Octubre de 2026)." for _, t in _al):
    fallas.append(f"alerta de fecha pasada sin el mes en palabras {_al}")

# Etiqueta de cada mínimo en las listas (17 de Octubre). Primero la nombrada junto al mínimo, si no, la primera después
# del mínimo anterior. 14-10 aviso 30 (lote 4) y 06-10 aviso 73 (departamento 41) quedaban con la pieza equivocada.
lista30 = [x["inmueble"] for x in extraer(av[30].texto)["minimo"]["lista"]]
if lista30 != ["lote 1", "lote 2", "lote 3", "lote 4"]:
    fallas.append(f"etiqueta. aviso 30 del 14-10 dio {lista30}")
T73 = ("se rematarán, en forma presencial, el día 5 de noviembre de 2026, a las 12:30 horas, los siguientes inmuebles: 1) Departamento N° 41 "
       "del 4 piso, bodega N° 41 del subterráneo y estacionamiento N° 22, del edificio ubicado en Avenida Holanda N° 280. Mínimo para "
       "comenzar las posturas: $130.690.779.- y 2) Departamento N° 31 del 3er piso del edificio ubicado en Avenida Perú N° 674-680. "
       "Mínimo para comenzar las posturas: $ 92.362.264.-.")
lista73 = [x["inmueble"] for x in minimo_y_costas(T73)["minimo"].get("lista", [])]
if lista73 != ["departamento 41", "departamento 31"]:
    fallas.append(f"etiqueta. aviso 73 del 06-10 dio {lista73}")
print("etiquetas de listas. aviso 30 del 14-10", lista30, "y aviso 73 del 06-10", lista73)
for c, n in aciertos.items():
    print(f"{c:12} aciertos {n} de {len(banco)} (mínimo {MINIMOS[c]})")
    if n < MINIMOS[c]: fallas.append(f"{c} bajó a {n} aciertos")
for f in fallas: print("FALLA", f)
print("\nRESULTADO.", "TODO OK" if not fallas else f"{len(fallas)} fallas")
sys.exit(1 if fallas else 0)
