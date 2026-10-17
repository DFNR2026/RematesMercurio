"""Mide el cortador contra el inventario correcto del banco de pruebas.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_cortador  (agrega -v para ver el detalle)"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina

B = RAIZ / "banco_pruebas"
VERBOSO = "-v" in sys.argv

def paginas_0806():
    out = []
    for n in (11, 12, 13):
        a = (B / f"2026-08-06/payload_B-20260806-0{n}.0.txt").read_text(encoding="utf-8")
        b = (B / f"2026-08-06/payload_B-20260806-0{n}.1.txt").read_text(encoding="utf-8")
        out.append((f"B{n}", a + b[2000:]))
    return out

def paginas_1014():
    return [("B11", (B / "2026-10-14/mercurio_2026-10-14_B11.txt").read_text(encoding="utf-8")),
            ("C8", (B / "2026-10-14/mercurio_2026-10-14_C8.txt").read_text(encoding="utf-8"))]

def paginas_1014_posicion():
    # Mismas dos páginas, ordenadas por la posición impresa (.geo.json capturado el 2026-10-15; el .txt es idéntico al del banco)
    return [("B11", leer_pagina(B / "2026-10-14/mercurio_2026-10-14_B11.txt")),
            ("C8", leer_pagina(B / "2026-10-14/mercurio_2026-10-14_C8.txt"))]

fallas = 0
for etiqueta, paginas in (("2026-08-06", paginas_0806()), ("2026-10-14", paginas_1014()),
                          ("2026-10-14 (orden por posición)", paginas_1014_posicion())):
    fecha = etiqueta[:10]
    inv = json.loads((B / fecha / f"inventario_correcto_{fecha}.json").read_text(encoding="utf-8"))["avisos"]
    rollo, marcas = construir_rollo(paginas)
    avisos = cortar(rollo, marcas)
    esperados = [a["rol"] for a in inv if a["rol"]]
    sin_rol_esperados = sum(1 for a in inv if not a["rol"])
    aislados = {f"{a.rol}-{a.anio}" for a in avisos if len(a.roles) == 1}
    todos = {f"{n}-{y}" for a in avisos for _, n, y in a.roles}
    no_aislados = [r for r in esperados if r not in aislados]
    inventados = sorted(todos - set(esperados))
    sin_rol = [a for a in avisos if not a.roles]
    dudosos = [a for a in avisos if a.revisar or len(a.roles) > 1]
    print(f"\n=== {etiqueta} ===")
    print(f"Avisos esperados {len(inv)} ({len(esperados)} con rol, {sin_rol_esperados} sin rol) | avisos cortados {len(avisos)}")
    print(f"Roles aislados correctamente {len(esperados) - len(no_aislados)} de {len(esperados)}")
    print(f"Roles inventados {len(inventados)} {inventados}")
    print(f"Trozos sin rol {len(sin_rol)} (esperados {sin_rol_esperados})")
    print(f"Trozos marcados para revisión o con dos roles {len(dudosos)}")
    if no_aislados: print("  NO AISLADOS.", no_aislados)
    for a in sin_rol if VERBOSO or len(sin_rol) != sin_rol_esperados else []:
        print(f"  sin rol #{a.orden} {a.paginas} {a.texto[:110]!r} ... {a.texto[-60:]!r}")
    for a in dudosos:
        print(f"  dudoso #{a.orden} {a.roles} {a.revisar} {a.texto[:90]!r}")
    if no_aislados or inventados or len(sin_rol) != sin_rol_esperados or dudosos:
        fallas += 1
# --- Orden por posición. Casos reales donde el orden del visor falla ---------------------------------
def _cortar_sola(nombre):
    t = leer_pagina(B / f"2026-10-11/mercurio_2026-10-11_{nombre}.txt")
    rollo, marcas = construir_rollo([(nombre, t)])
    return rollo, cortar(rollo, marcas)

# F9 del 2026-10-11. El visor entrega las columnas 1,2,4,5,6,7,3 y deja 3 trozos dudosos.
# Por posición solo debe quedar dudoso el primero (empieza en minúscula porque viene de F8, que aquí no se incluye).
rollo, avisos = _cortar_sola("F09")
dudosos = [a.orden for a in avisos if a.revisar or len(a.roles) > 1]
print(f"\n=== 2026-10-11 F9 sola (orden por posición) ===\nAvisos {len(avisos)} (esperados 19) | dudosos {dudosos} (esperado [1])")
if len(avisos) != 19 or dudosos != [1]:
    fallas += 1

# F15 del 2026-10-11. Al pie hay una franja "1300 EMPLEOS" que cruza las columnas. No debe mezclarse con los remates.
# Además trae tres avisos que antes salían pegados en un solo trozo (corregido el 2026-10-15):
# Temuco (RIT C-357-2024, sin cierre) | JUZGADO DE LETRAS DE COLINA (Rol C-10387-2019) | COMUNA PROVIDENCIA REMATA (partidor, sin rol).
# Desde el 2026-10-15 (tarde) son 13 y no 12. El partidor "JUEZ PARTIDOR SEBASTIÁN SANchez Lopez" iba pegado al de Paulina Urzua Davis.
rollo, avisos = _cortar_sola("F15")
intrusos = [w for w in ("Profesionales se necesitan", "MUNDO LABORAL", "EMPLEOS") if w in rollo]
dudosos = [a.orden for a in avisos if a.revisar or len(a.roles) > 1]
separados = (any(a.rol == "357" and len(a.roles) == 1 for a in avisos)
             and any(a.rol == "10387" and a.texto.startswith("JUZGADO DE LETRAS DE COLINA") and "REMATA" not in a.texto for a in avisos)
             and any(a.texto.startswith("COMUNA PROVIDENCIA REMATA") for a in avisos)
             and any(a.texto.startswith("JUEZ PARTIDOR SEBASTIÁN") for a in avisos))
print(f"\n=== 2026-10-11 F15 sola (orden por posición) ===\nAvisos {len(avisos)} (esperados 13) | empleos dentro del rollo {intrusos} (esperado []) | dudosos {dudosos} (esperado []) | Temuco, Colina y partidor separados {separados}")
if len(avisos) != 13 or intrusos or dudosos or not separados:
    fallas += 1

# B11 del 2026-10-09. "entregado materialmente en la secretaría del tribunal" no es un cierre: el aviso del rol 1911-2020
# termina en "Secretaria." y el siguiente empieza en "POR RESOLUCIÓN DEL 1° JUZGADO" (rol 5598-2024).
# Quedan dudosos solo el 10 (un aviso que imprime dos roles, C-3673-2025 y C-14254-2025: errata del diario a revisar)
# y el 43 (termina cortado porque sigue en B12, que aquí no se incluye).
t = leer_pagina(B / "2026-10-09/mercurio_2026-10-09_B11.txt")
rollo, marcas = construir_rollo([("B11", t)])
avisos = cortar(rollo, marcas)
dudosos = [a.orden for a in avisos if a.revisar or len(a.roles) > 1]
ok_5598 = any(a.rol == "5598" and a.texto.startswith("POR RESOLUCIÓN DEL 1° JUZGADO") for a in avisos)
ok_1911 = any(a.rol == "1911" and a.texto.endswith("Secretaria.") for a in avisos)
print(f"\n=== 2026-10-09 B11 sola (orden por posición) ===\nAvisos {len(avisos)} (esperados 43) | dudosos {dudosos} (esperado [10, 43]) | 1911 y 5598 bien partidos {ok_1911 and ok_5598}")
if len(avisos) != 43 or dudosos != [10, 43] or not (ok_1911 and ok_5598):
    fallas += 1

# 2026-10-06 completo (B7 a B10). Parte 3.6b. Tres avisos iban pegados a otro.
# 55. "pagarse al contado 15° JUZGADO CIVIL SANTIAGO. ... Rematará" (sin punto antes). Rancagua sin rol | Linares rol C-2991-2024.
# 102. 30° Civil (rol C-9481-2023) | "EXTRACTO. ANTE EL SEÑOR JUEZ Árbitro Juan Pablo Gracia Domic".
# 106. Juzgado de Cobranza | "JUEZ ÁRBITRO ARTURO GÓMEZ Tomás". La edición pasa de 107 a 110 avisos.
def _rollo(fecha, nombres):
    return construir_rollo([(n, leer_pagina(B / f"{fecha}/mercurio_{fecha}_{n}.txt")) for n in nombres])

rollo, marcas = _rollo("2026-10-06", ("B7", "B8", "B9", "B10"))
avisos = cortar(rollo, marcas)
por = {a.orden: a for a in avisos}
c06 = {
    "15° Civil Rancagua sin rol": por[55].rol is None and por[55].texto.endswith("deberá pagarse al contado"),
    "15° Civil Linares": por[56].rol == "2991" and por[56].texto.startswith("15° JUZGADO CIVIL SANTIAGO"),
    "30° Civil solo": por[103].rol == "9481" and "Árbitro" not in por[103].texto,
    "Gracia Domic aparte": por[104].texto.startswith("EXTRACTO. ANTE EL SEÑOR JUEZ Árbitro Juan Pablo Gracia Domic"),
    "Cobranza sola": por[108].texto.startswith("EXTRACTO. JUZGADO COBRANZA") and "GÓMEZ" not in por[108].texto,
    "Gómez aparte": por[109].texto.startswith("JUEZ ÁRBITRO ARTURO GÓMEZ"),
}
dudosos = [a.orden for a in avisos if a.revisar or len(a.roles) > 1]
print(f"\n=== 2026-10-06 (B7 a B10) ===\nAvisos {len(avisos)} (esperados 110) | dudosos {dudosos} (esperado []) | {c06}")
if len(avisos) != 110 or dudosos or not all(c06.values()):
    fallas += 1

# 2026-10-13 completo (B8 a B10). El aviso de Gracia Domic iba pegado al 30° Civil (rol C-3014-2021). Pasa de 66 a 67 avisos.
rollo, marcas = _rollo("2026-10-13", ("B8", "B9", "B10"))
avisos = cortar(rollo, marcas)
ok13 = (any(a.rol == "3014" and a.texto.endswith("Secretaría.") for a in avisos)
        and any(a.texto.startswith("EXTRACTO. ANTE EL SEÑOR JUEZ Árbitro Juan Pablo Gracia Domic") for a in avisos))
dudosos = [a.orden for a in avisos if a.revisar or len(a.roles) > 1]
print(f"\n=== 2026-10-13 (B8 a B10) ===\nAvisos {len(avisos)} (esperados 67) | dudosos {dudosos} (esperado []) | 30° Civil y Gracia Domic separados {ok13}")
if len(avisos) != 67 or dudosos or not ok13:
    fallas += 1

# Guion al final de renglón (2026-10-16). Solo se une sin guion la palabra cortada (letra + minúscula). El guion real se deja.
# Casos reales verificados en el texto crudo. Antes salían "C-24622022", "C2461-2022" (alertas falsas de rol) y "614.precio".
rollo14, m14 = construir_rollo([(n, leer_pagina(B / f"2026-10-14/mercurio_2026-10-14_{n}.txt")) for n in ("B11", "C8")])
p14 = {a.orden: a for a in cortar(rollo14, m14)}
rollo06, m06 = construir_rollo([(n, leer_pagina(B / f"2026-10-06/mercurio_2026-10-06_{n}.txt")) for n in ("B7", "B8", "B9", "B10")])
p06 = {a.orden: a for a in cortar(rollo06, m06)}
gui = {
    "14-10 aviso 6 Rol: C-2462-2022": p14[6].rol_impreso == "Rol: C-2462-2022",
    "14-10 aviso 45 rol C-18207-2017": p14[45].rol_impreso == "rol C-18207-2017",
    "14-10 aviso 48 Rol N° C-28690-2019": p14[48].rol_impreso == "Rol N° C-28690-2019",
    "14-10 aviso 17 sigue CC-936-2026 (errata real)": p14[17].rol_impreso == "Rol N° CC-936-2026",
    "06-10 aviso 2 Rol C-2461-2022": p06[2].rol_impreso == "Rol C-2461-2022",
    "06-10 monto 614.- precio": "$54.327.614.- precio" in rollo06 and "614.precio" not in rollo06,
    "Santander-Chile con guion": "Santander-Chile" in rollo06 and "SantanderChile" not in rollo06,
    "SAN-tiago unido": "SAN- tiago" not in rollo14 + rollo06 and "SAN-tiago" not in rollo14 + rollo06,
    "Condo-minio unido": "Condo- minio" not in rollo06 and "Condominio" in rollo06,
}
print(f"\n=== Guion al final de renglón ===\n{gui}")
if not all(gui.values()):
    fallas += 1

print("\nRESULTADO.", "TODO OK" if not fallas else f"{fallas} ediciones con diferencias")
sys.exit(1 if fallas else 0)
