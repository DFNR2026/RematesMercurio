import sys,json,re,hashlib,collections
sys.path.insert(0,".")
from motor import direccion as DR
from motor.edicion import procesar, paginas_desde_captura
vistos={}; out=[]
for fecha in ["2026-10-14","2026-10-15","2026-10-16","2026-10-17","2026-10-18"]:
    rollos,_=paginas_desde_captura(f"Capturas/{fecha}")
    res=procesar(rollos,fecha,cliente=None)
    print(fecha,res["ia"]["colores"],"sin_ia",res["ia"]["sin_ia"],"avisos con rol",sum(len(c["avisos"]) for c in res["causas"]))
    avs=[(c["rol"]+"-"+str(c["año"]),c["tribunal"],av) for c in res["causas"] for av in c["avisos"]]+[("SIN ROL",av.get("tribunal"),av) for av in res["sin_rol"]]
    for rol,trib,av in avs:
        h=hashlib.sha1(av["texto"].encode()).hexdigest()
        malas=[a for a in av["alertas"] if a.startswith(("Falla de la IA","Dirección no leída","La IA no encontró")) or "carátula" in a]
        if not malas: continue
        if h in vistos: vistos[h]["fechas"].append(fecha); continue
        r={"rol":rol,"tribunal":trib,"fechas":[fecha],"alertas":malas,"texto":av["texto"],"n":av["n_remates"]}
        if av["dir_color"]=="rojo":
            g=DR.leer_guardada(av["texto"],av["n_remates"]); r["lecturas"]=g["lecturas"]
            r["motivos"]=DR.resolver(g["lecturas"],av["texto"],av["n_remates"])["motivos"]
        vistos[h]=r; out.append(r)
json.dump(out,open(sys.argv[1]+"/banco_14_18.json","w"),ensure_ascii=False,indent=1)
print("avisos distintos con fallo",len(out))
for r in out:
    print("\n>>",r["rol"],r["tribunal"],r["fechas"])
    for m in r.get("motivos",[]): print("   MOTIVO:",m)
    for a in r["alertas"]:
        if "carátula" in a: print("   CAR:",a[:200])
        if a.startswith("La IA no encontró"): print("   SIN_DATO")
