import sys,json,hashlib,os
from pathlib import Path
raiz=sys.argv[1]; sys.path.insert(0,raiz); os.chdir(raiz)
from motor.edicion import procesar, paginas_desde_captura
out={}
carpetas=[p for p in sorted(Path("Capturas").glob("*"))+sorted(Path("banco_pruebas").glob("2026-*")) if (p/"navegacion.json").exists()]
for c in carpetas:
    rollos,_=paginas_desde_captura(c); f=c.name
    res=procesar(rollos,f,cliente=None)
    for av in [a for x in res["causas"] for a in x["avisos"]]+res["sin_rol"]:
        k=f"{c.parent.name}/{f}/{hashlib.sha1(av['texto'].encode()).hexdigest()[:10]}"
        out[k]={"rol":f"{av['rol']}-{av['anio']}","car":av["caratula"],"color":av["dir_color"],"dirs":av["direcciones"],"n":av["n_remates"]}
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False)
print(len(carpetas),"ediciones",len(out),"avisos")
