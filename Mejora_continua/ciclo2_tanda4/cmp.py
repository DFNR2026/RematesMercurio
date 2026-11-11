import json, sys
a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
n = 0
for k in sorted(set(a["avisos"]) | set(b["avisos"])):
    x, y = a["avisos"].get(k), b["avisos"].get(k)
    if x != y:
        n += 1
        if not x or not y: print("AVISO solo en uno", k); continue
        dif = [c for c in x if x[c] != y[c]]
        print("AVISO", k.split("/")[1], x["rol"], dif, "|", x["color"], x["dirs"], "->", y["color"], y["dirs"])
print(n, "avisos cambian")
m = 0
for k in sorted(set(a["tablas"]) | set(b["tablas"])):
    x, y = a["tablas"].get(k), b["tablas"].get(k)
    if x != y:
        m += 1
        print("TABLA", k, "|", x and x["tabla"], x and x.get("motivo"), x and x.get("comuna"), "->", y and y["tabla"], y and y.get("motivo"), y and y.get("comuna"), "| obs", (y or {}).get("obs"))
print(m, "filas de tabla cambian")
