import sys, json, os, hashlib
from pathlib import Path
raiz = sys.argv[1]; sys.path.insert(0, raiz); os.chdir(raiz)
from motor.edicion import procesar, paginas_desde_captura
from motor import filtros as F, direccion as DR
from motor.ia_comun import buscar_frase
out = {"avisos": {}, "tablas": {}, "ia": {}}
carp = [p for p in sorted(Path("Capturas").glob("2026-*")) + sorted(Path("banco_pruebas").glob("2026-*")) if (p / "navegacion.json").exists()]
for c in carp:
    rollos, _ = paginas_desde_captura(c); f = c.name; ed = f"{c.parent.name}/{f}"
    res = procesar(rollos, f, cliente=None)
    out["ia"][ed] = res.get("ia", {}).get("colores") if isinstance(res.get("ia"), dict) else None
    for av in [a for x in res["causas"] for a in x["avisos"]] + res["sin_rol"]:
        h = hashlib.sha1(av["texto"].encode()).hexdigest()[:10]
        out["avisos"][f"{ed}/{h}"] = {"rol": f"{av['rol']}-{av['anio']}", "trib": av.get("tribunal"), "car": av["caratula"], "color": av["dir_color"],
                                      "dirs": av["direcciones"], "n": av["n_remates"], "texto": av["texto"], "alertas": av.get("alertas")}
    r = F.aplicar([res], {})
    for tabla in ("principal", "excluidas_cbr", "descartados", "ya_informadas"):
        for x in r[tabla]:
            k = f"{ed}|{x.get('rol')}-{x.get('anio')}|{x.get('tribunal')}"
            out["tablas"][k] = {"tabla": tabla, "motivo": x.get("motivo"), "dir": x.get("direccion"), "comuna": x.get("comuna"), "obs": x.get("observaciones"), "cbr": x.get("cbr_anio")}
    out["tablas"][f"{ed}|SINROL"] = {"tabla": "sin_rol", "n": len(r["sin_rol"]), "det": [(s.get("direccion"), s.get("comuna")) for s in r["sin_rol"]]}
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False)
from collections import Counter
print(len(carp), "ediciones", len(out["avisos"]), "avisos", Counter(a["color"] for a in out["avisos"].values()), Counter(t["tabla"] for t in out["tablas"].values()))
