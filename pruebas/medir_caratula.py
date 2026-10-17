"""Parte 3.7c. Mide la carátula (código) contra un banco de carátula.
Uso (desde D:\\Agendar_Remates). python -m pruebas.medir_caratula 14   (o 06, la validación, una sola vez con el código congelado)
Por aviso. acierto (igual a lo anotado, o vacío cuando el aviso no la trae), no_leido (vacío con alerta cuando el aviso la
trae), EQUIVOCADO (el programa da una carátula distinta, o da una cuando el aviso no la trae).
"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
from motor.extraccion import caratula, clave_caratula


def clave(t):
    return clave_caratula(t).replace(" ", "")


def main():
    cual = sys.argv[1] if len(sys.argv) > 1 else "14"
    d, pags, ed = ((RAIZ / "banco_pruebas" / "2026-10-14", ("B11", "C8"), "2026-10-14") if cual == "14" else
                   (RAIZ / "banco_pruebas" / "2026-10-06", ("B7", "B8", "B9", "B10"), "2026-10-06"))
    banco = json.loads((d / f"banco_caratula_{ed}.json").read_text(encoding="utf-8"))["avisos"]
    r, m = construir_rollo([(n, leer_pagina(d / f"mercurio_{ed}_{n}.txt")) for n in pags])
    av = {a.orden: a for a in cortar(r, m)}
    cuenta, lineas = {}, []
    for x in banco:
        if "caratula" not in x:
            continue
        res = caratula(av[x["n"]].texto)
        v, e = res["caratula"]["valor"], x["caratula"]
        if v is None:
            c = "acierto" if e is None else "no_leido"
        else:
            c = "acierto" if e is not None and clave(v) == clave(e) else "EQUIVOCADO"
        if v is not None and res["caratula"]["cita"] not in av[x["n"]].texto:
            c = "EQUIVOCADO"
        cuenta[c] = cuenta.get(c, 0) + 1
        lineas.append(f"{x['n']:>3} {c:<11} programa {v!r} | anotado {e!r}" + (f" | {res['alertas'][0][1][:150]}" if res["alertas"] else ""))
    resumen = f"Banco de carátula {ed}. Por aviso. " + ", ".join(f"{k} {v}" for k, v in sorted(cuenta.items())) + "."
    salida = resumen + "\n\n" + "\n".join(lineas) + "\n"
    print(salida)
    if "--guardar" in sys.argv:
        (d / f"MEDICION_CARATULA_{ed}.txt").write_text(salida, encoding="utf-8")


if __name__ == "__main__":
    main()
