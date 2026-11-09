"""Ciclo 2 de mejora, tanda 2 (8 de Noviembre de 2026). Formato de condominios y edificios en la columna Dirección.
Aplica sobre una COPIA del proyecto que ya tiene la tanda 1. Uso. python aplicar_tanda2.py RAIZ_DE_LA_COPIA
Copia motor/conjunto.py (nuevo, junto a este script) y hace dos cambios chicos. direccion.py entrega también la calle que
comprobó la IA, y edicion.py arma el formato cuando la dirección sale en verde y el aviso trae un solo remate.
Cada reemplazo exige encontrar el texto original exactamente una vez. Si el código cambió, se detiene sin escribir nada."""
import sys, os, shutil
RAIZ = sys.argv[1]
AQUI = os.path.dirname(os.path.abspath(__file__))
pendientes = {}
def rep(p, pares):
    ruta = os.path.join(RAIZ, *p.split("/"))
    s = pendientes.get(ruta) or open(ruta, encoding="utf-8").read()
    for a, b in pares:
        assert s.count(a) == 1, (p, a[:80]); s = s.replace(a, b, 1)
    pendientes[ruta] = s

rep("motor/direccion.py", [
('''    return {"ok": True, "motivos": [], "direccion": direccion, "comuna": comuna.strip() if comuna else None, "cita": frase, "citas_extra": citas_extra}''',
 '''    return {"ok": True, "motivos": [], "direccion": direccion, "comuna": comuna.strip() if comuna else None, "cita": frase, "citas_extra": citas_extra,
            "calle": x.get("calle") if tipo == "calle" else None}     # la usa motor/conjunto.py (tanda 2 del ciclo 2)'''),
('''            base["inmuebles"].append({k2: v[k2] for k2 in ("direccion", "comuna", "cita", "citas_extra")})''',
 '''            base["inmuebles"].append({k2: v.get(k2) for k2 in ("direccion", "comuna", "cita", "citas_extra", "calle")})'''),
])
rep("motor/edicion.py", [
("from motor import direccion as DR\n", "from motor import direccion as DR\nfrom motor import conjunto as CJ\n"),
('''        return [{"direccion": i["direccion"], "comuna": i["comuna"]} for i in res["inmuebles"]], "verde", []''',
 '''        # Tanda 2 del ciclo 2. Con un remate, si el aviso habla de condominio o edificio, la dirección va en ese formato.
        return [{"direccion": CJ.describir(texto, i["direccion"], i.get("calle")) if n == 1 else i["direccion"],
                 "comuna": i["comuna"]} for i in res["inmuebles"]], "verde", []'''),
])
destino = os.path.join(RAIZ, "motor", "conjunto.py")
assert not os.path.exists(destino), "motor/conjunto.py ya existe"
for ruta, s in pendientes.items():
    fin = "\r\n" if b"\r\n" in open(ruta, "rb").read() else "\n"
    open(ruta, "w", encoding="utf-8", newline=fin).write(s)
shutil.copyfile(os.path.join(AQUI, "conjunto.py"), destino)
print("Tanda 2 aplicada en", len(pendientes), "archivos más motor/conjunto.py")
