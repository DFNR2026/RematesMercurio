"""Compara dos salidas de regre.py (antes y después de un arreglo) aviso por aviso.
Uso. python3 -I comparar.py antes.json despues.json
Criterio de aceptación. Cero carátulas PERDIDAS o CAMBIADAS y cero direcciones de verde a rojo o cambiadas, salvo las que el arreglo busca."""
import json, sys, collections
a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
c, vistos = collections.Counter(), set()
for k in a:
    x, y = a[k], b.get(k)
    if y is None: c["falta en después"] += 1; continue
    if x == y: c["igual"] += 1; continue
    h = k.split("/")[-1]
    if h in vistos: c["mismo aviso repetido otro día"] += 1; continue
    vistos.add(h)
    if x["car"] != y["car"]:
        t = "carátula NUEVA" if x["car"] is None else ("carátula PERDIDA" if y["car"] is None else "carátula CAMBIADA")
        c[t] += 1; print(t, k, x["rol"], "|", x["car"], "->", y["car"])
    if x["color"] != y["color"] or x["dirs"] != y["dirs"]:
        t = f"dirección {x['color']} a {y['color']}" if x["color"] != y["color"] else "dirección CAMBIADA mismo color"
        c[t] += 1; print(t, k, x["rol"], "|", x["dirs"], "->", y["dirs"])
    if x["n"] != y["n"]:
        c["cantidad de remates cambia"] += 1; print("n", k, x["rol"], x["n"], "->", y["n"])
print(dict(c))
