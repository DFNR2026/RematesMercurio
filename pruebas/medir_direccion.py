"""Parte 3.7b. Mide la dirección (IA más verificador) contra un banco de dirección.

Uso (desde D:\\Agendar_Remates).
  python -m pruebas.medir_direccion 14              usa solo respuestas guardadas (sin internet)
  python -m pruebas.medir_direccion 14 --exportar   escribe _avisos_direccion_14.json con los avisos que faltan por leer
14 = banco de AJUSTE (2026-10-14). 06 = banco de VALIDACIÓN (2026-10-06), que se corre UNA sola vez con el código congelado.
La cantidad de remates de cada aviso la da el código (extraer(), lista de mínimos).

Clasificación por remate.
  acierto. Verde y calle, número, unidad y comuna iguales a lo anotado (o a la alternativa aceptada).
  unidad_de_mas. Verde, todo igual, pero el programa agrega una unidad que lo anotado no trae (no es error).
  no_leido. Rojo o sin dato cuando lo anotado tiene dirección (Diego la lee en el aviso, no es error).
  EQUIVOCADO. Verde con algún dato distinto.
"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
from motor.extraccion import extraer
from motor import direccion as D

PRECIO = {"entrada": 0.10, "salida": 0.50, "cache_lectura": 0.01, "cache_escritura": 0.125}   # dólares por millón, Haiku 5.5 (16-10-2026)


def cargar(cual):
    d, pags, edicion = ((RAIZ / "banco_pruebas" / "2026-10-14", ("B11", "C8"), "2026-10-14") if cual == "14" else
                        (RAIZ / "banco_pruebas" / "2026-10-06", ("B7", "B8", "B9", "B10"), "2026-10-06"))
    banco = json.loads((d / f"banco_direccion_{edicion}.json").read_text(encoding="utf-8"))["avisos"]
    rollo, m = construir_rollo([(n, leer_pagina(d / f"mercurio_{edicion}_{n}.txt")) for n in pags])
    av = {a.orden: a for a in cortar(rollo, m)}
    return d, edicion, av, {x["n"]: x for x in banco if "remates" in x}


def n_remates(texto, edicion):
    mi = extraer(texto, edicion)["minimo"] or {}
    return len(mi["lista"]) if mi.get("lista") else 1


def comparar(x, e):
    """x = inmueble leído (ya verificado), e = anotado. Devuelve acierto, unidad_de_mas o EQUIVOCADO."""
    if x.get("tipo") != e["tipo"]:
        return "EQUIVOCADO"
    if D.norm(x.get("comuna")) != D.norm(e["comuna"]):
        return "EQUIVOCADO"
    if e["tipo"] == "calle":
        if D.calle_clave(x.get("calle")) != D.calle_clave(e["calle"]) or D.numeros_clave(x.get("numero")) != D.numeros_clave(e["numero"]):
            return "EQUIVOCADO"
    ux, ue = D.unidad_clave(x.get("unidad")), D.unidad_clave(e["unidad"])
    if ux == ue or (e.get("unidad_opcional") and ux is None):
        return "acierto"
    if ue is None:
        return "unidad_de_mas"
    return "EQUIVOCADO"


def main():
    cual = sys.argv[1] if len(sys.argv) > 1 else "14"
    d, edicion, av, banco = cargar(cual)
    if "--exportar" in sys.argv:
        faltan = [{"n": n, "n_remates": n_remates(av[n].texto, edicion), "texto": av[n].texto} for n in sorted(banco)
                  if not D.leer_guardada(av[n].texto, n_remates(av[n].texto, edicion))]
        (RAIZ / f"_avisos_direccion_{cual}.json").write_text(json.dumps(faltan, ensure_ascii=False), encoding="utf-8")
        print(f"{len(faltan)} avisos sin respuesta guardada exportados a _avisos_direccion_{cual}.json"); return
    lineas, cuenta, uso = [], {}, {k: 0 for k in PRECIO}
    for n in sorted(banco):
        e, a = banco[n], av[n]
        nr = n_remates(a.texto, edicion)
        g = D.leer_guardada(a.texto, nr)
        if not g:
            lineas.append(f"{n:>3} SIN RESPUESTA GUARDADA"); cuenta["sin_respuesta"] = cuenta.get("sin_respuesta", 0) + len(e["remates"]); continue
        for u in g.get("uso", []):
            for k in uso: uso[k] += u.get(k, 0)
        res = D.resolver(g["lecturas"], a.texto, nr)
        if res["color"] == "verde":
            leidos = g["lecturas"][0]["inmuebles"]
            if len(leidos) != len(e["remates"]):
                clases = ["EQUIVOCADO"] * len(e["remates"])
            else:
                clases = []
                for x, guardado, ee in zip(leidos, res["inmuebles"], e["remates"]):
                    # se compara la comuna que GUARDA el verificador, no la que copió la IA (17 de Octubre, tras la validación)
                    x = dict(x, comuna=guardado["comuna"])
                    c = comparar(x, ee)
                    if c == "EQUIVOCADO" and e.get("alternativas"):
                        c = min((comparar(x, alt) for alt in e["alternativas"][0][:1]), key=["acierto", "unidad_de_mas", "EQUIVOCADO"].index)
                    clases.append(c)
        else:
            clases = ["no_leido"] * len(e["remates"])
        for c in clases:
            cuenta[c] = cuenta.get(c, 0) + 1
        prog = " / ".join(i["direccion"] + (f", comuna {i['comuna']}" if i["comuna"] else "") for i in res["inmuebles"]) or res["color"]
        anot = " / ".join(D.legible(x) for x in e["remates"])
        lineas.append(f"{n:>3} {','.join(sorted(set(clases))):<14} programa {prog} | anotado {anot}" + (f" | {'; '.join(res['motivos'])}" if res["motivos"] else "")
                      + (f" | errores IA {g['errores']}" if g.get("errores") else ""))
    costo = sum(uso[k] * PRECIO[k] / 1e6 for k in PRECIO)
    resumen = (f"Banco de dirección {edicion}. Modelo {D.MODELO}, instrucciones {D.VERSION_INSTRUCCIONES}. Por remate. "
               + ", ".join(f"{k} {v}" for k, v in sorted(cuenta.items()))
               + f". Tokens entrada {uso['entrada']}, salida {uso['salida']}, caché leída {uso['cache_lectura']}, caché escrita {uso['cache_escritura']}."
               + f" Costo de las llamadas guardadas {costo:.4f} dólares.")
    salida = resumen + "\n\n" + "\n".join(lineas) + "\n"
    print(salida)
    if "--guardar" in sys.argv:
        (d / f"MEDICION_DIR_{edicion}_{D.VERSION_INSTRUCCIONES}.txt").write_text(salida, encoding="utf-8")


if __name__ == "__main__":
    main()
