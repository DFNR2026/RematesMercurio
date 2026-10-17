"""Pruebas de la lógica de navegación contra la evidencia reunida.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_navegacion_logica"""
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.navegacion_logica import Pagina, analizar_pagina, ordenar

fallas = []
def revisar(nombre, cond, detalle=""):
    print(("OK   " if cond else "FALLA"), nombre, detalle)
    if not cond: fallas.append(nombre)

# 1. Textos reales del banco de pruebas
B = RAIZ / "banco_pruebas"
b11 = analizar_pagina(Pagina("B", 11, "B-20261014-011", (B/"2026-10-14/mercurio_2026-10-14_B11.txt").read_text(encoding="utf-8")))
c8 = analizar_pagina(Pagina("C", 8, "L64MFDBT", (B/"2026-10-14/mercurio_2026-10-14_C8.txt").read_text(encoding="utf-8")))
revisar("14-10 B11 detecta salida a C8 escrita PÁGINA", b11.salidas == [("C", 8)], str(b11.salidas))
revisar("14-10 C8 detecta entrada desde B11", c8.entradas == [("B", 11)], str(c8.entradas))
revisar("14-10 cornisas B11=5 y C8=8 (igual que el reconocimiento)", (b11.cornisas, c8.cornisas) == (5, 8), str((b11.cornisas, c8.cornisas)))
r = ordenar([b11, c8])
revisar("14-10 un solo rollo B11-C8 sin alarmas", [[p.nombre for p in x] for x in r.rollos] == [["B11", "C8"]] and not r.alarmas, str(r.alarmas))

pags = []
for n in (11, 12, 13):
    a = (B/f"2026-08-06/payload_B-20260806-0{n}.0.txt").read_text(encoding="utf-8")
    b = (B/f"2026-08-06/payload_B-20260806-0{n}.1.txt").read_text(encoding="utf-8")
    pags.append(analizar_pagina(Pagina("B", n, f"B-20260806-0{n}", a + b[2000:])))
r = ordenar(pags)
revisar("06-08 un solo rollo B11-B12-B13 sin alarmas", [[p.nombre for p in x] for x in r.rollos] == [["B11", "B12", "B13"]] and not r.alarmas, str(r.alarmas))

# 2. Frases que no deben confundirse
p = analizar_pagina(Pagina("C", 5, "x", "texto MÁS AVISOS DEFUNCIÓN EN PÁG. C 6 texto"))
revisar("flecha de defunciones ignorada", p.salidas == [], str(p.salidas))
p = analizar_pagina(Pagina("B", 9, "x", "MÁS AVISOS ECONÓMICOS CLASIFICADOS EN PÁG. B 10"))
revisar("flecha abreviada PÁG. reconocida", p.salidas == [("B", 10)])
p = analizar_pagina(Pagina("B", 9, "x", "ParcelaMÁS AVISOS ECONÓMICOS\nCLASIFICADOS EN PÁGINA C 8"))
revisar("flecha pegada a la palabra anterior y con salto de línea", p.salidas == [("C", 8)])

p = analizar_pagina(Pagina("C", 8, "x", "VIENEN DE PÁGINA B 111616 Remates de propiedades"))
revisar("número de página pegado a la cornisa no se lee como B111 (alarma falsa vista en vivo el 2026-10-14)", p.entradas == [], str(p.entradas))
p = analizar_pagina(Pagina("C", 8, "x", "VIENEN DE PÁGINA B 11\n1616 Remates de propiedades"))
revisar("entrada con salto de línea antes de la cornisa", p.entradas == [("B", 11)], str(p.entradas))

# 3. Las 36 ediciones del reconocimiento (cornisas y flechas observadas)
def ed(paginas):
    lista = []
    for txt in paginas.split():
        nombre, *fl = txt.split(":")
        c, n = nombre[0], int(nombre[1:])
        pg = Pagina(c, n, nombre, "", cornisas=1)
        for f in fl:
            if f.startswith(">"): pg.salidas.append((f[1], int(f[2:])))
            if f.startswith("<"): pg.entradas.append((f[1], int(f[2:])))
        lista.append(pg)
    return lista
rango = lambda c, a, b: " ".join(f"{c}{k}" for k in range(a, b + 1))
EDICIONES = {
 "10-14": ("B11:>C8 C8:<B11", ["B11-C8"]),
 "10-13": ("B8 B9:>B10 B10:<B9", ["B8-B9-B10"]),
 "10-12": ("B6 B7:>B8 B8:<B7", ["B6-B7-B8"]),
 "10-11": (rango("F", 7, 15), [rango("F", 7, 15).replace(" ", "-")]),
 "10-10": (rango("D", 5, 12), [rango("D", 5, 12).replace(" ", "-")]),
 "10-09": (rango("B", 11, 13) + " " + rango("G", 5, 12), ["B11-B12-B13", rango("G", 5, 12).replace(" ", "-")]),
 "10-08": (rango("B", 11, 13), ["B11-B12-B13"]),
 "10-07": (rango("B", 9, 11), ["B9-B10-B11"]),
 "10-06": ("B7 B8 B9:>B10 B10:<B9", ["B7-B8-B9-B10"]),
 "10-05": (rango("B", 7, 9), ["B7-B8-B9"]),
 "10-04": (rango("F", 7, 15), [rango("F", 7, 15).replace(" ", "-")]),
 "10-03": (rango("D", 9, 15), [rango("D", 9, 15).replace(" ", "-")]),
 "10-02": (rango("B", 11, 13) + " " + rango("G", 7, 12), ["B11-B12-B13", rango("G", 7, 12).replace(" ", "-")]),
 "10-01": (rango("B", 13, 15), ["B13-B14-B15"]),
 "09-30": (rango("B", 15, 17), ["B15-B16-B17"]),
 "09-27": (rango("F", 8, 15), [rango("F", 8, 15).replace(" ", "-")]),
 "09-26": (rango("D", 6, 12), [rango("D", 6, 12).replace(" ", "-")]),
 "09-23": (rango("B", 10, 11), ["B10-B11"]),
 "09-20": (rango("F", 6, 11), [rango("F", 6, 11).replace(" ", "-")]),
 "09-19": (rango("D", 4, 8), [rango("D", 4, 8).replace(" ", "-")]),
 "09-15": (rango("B", 9, 11), ["B9-B10-B11"]),
 "09-13": (rango("F", 7, 12), [rango("F", 7, 12).replace(" ", "-")]),
 "09-12": (rango("D", 6, 12), [rango("D", 6, 12).replace(" ", "-")]),
 "09-08": (rango("B", 11, 13), ["B11-B12-B13"]),
 "09-06": (rango("F", 5, 11), [rango("F", 5, 11).replace(" ", "-")]),
 "09-05": (rango("D", 5, 11), [rango("D", 5, 11).replace(" ", "-")]),
 "09-01": ("B15:>C8 C8:<B15", ["B15-C8"]),
 "08-30": (rango("F", 9, 12), [rango("F", 9, 12).replace(" ", "-")]),
 "08-29": (rango("D", 8, 12), [rango("D", 8, 12).replace(" ", "-")]),
 "08-22": (rango("D", 6, 12), [rango("D", 6, 12).replace(" ", "-")]),
 "08-15": (rango("D", 5, 12), [rango("D", 5, 12).replace(" ", "-")]),
 "08-06": (rango("B", 11, 13), ["B11-B12-B13"]),
 "08-01": (rango("D", 9, 15), [rango("D", 9, 15).replace(" ", "-")]),
 "07-05": (rango("F", 6, 8), ["F6-F7-F8"]),
 "07-04": (rango("D", 6, 8), ["D6-D7-D8"]),
 "06-04": (rango("B", 13, 15), ["B13-B14-B15"]),
}
ok36 = 0
for fecha, (pags, esperado) in EDICIONES.items():
    r = ordenar(ed(pags))
    obtenido = ["-".join(p.nombre for p in x) for x in r.rollos]
    bien = obtenido == esperado and not r.alarmas
    ok36 += bien
    if not bien: revisar(f"edición {fecha}", False, f"obtenido {obtenido} alarmas {r.alarmas}")
revisar(f"36 ediciones del reconocimiento ordenadas como se esperaba", ok36 == 36, f"{ok36} de 36")

# 4. Casos que deben alarmar
r = ordenar(ed("B11:>C8"))
revisar("alarma si la página destino no existe", any("no existe" in a for a in r.alarmas), str(r.alarmas))
r = ordenar(ed("B11:>C8") + [Pagina("C", 8, "x", "", cornisas=1)])
revisar("alarma si el destino no confirma la flecha de vuelta", any("no confirma" in a for a in r.alarmas), str(r.alarmas))
r = ordenar(ed("B8 B10"))
revisar("alarma por hueco dentro del cuerpo", any("Hueco" in a for a in r.alarmas), str(r.alarmas))
r = ordenar([Pagina("B", 1, "x", "", cornisas=0)])
revisar("alarma si ninguna página trae remates", any("Ninguna" in a for a in r.alarmas))

print("\nRESULTADO.", "TODO OK" if not fallas else f"{len(fallas)} FALLAS. " + "; ".join(fallas))
sys.exit(1 if fallas else 0)
