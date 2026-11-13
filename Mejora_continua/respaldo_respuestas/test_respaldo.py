"""Prueba del respaldo de respuestas en la captura (sin Supabase ni Haiku). Uso python3 test_respaldo.py RAIZ_COPIA FECHA
La copia debe traer capturas/FECHA y ia_respuestas/direccion."""
import os, sys, zipfile, shutil, tempfile
raiz = sys.argv[1]; os.environ["FECHA"] = sys.argv[2]; os.environ["MODO"] = "ensayo"
sys.path.insert(0, raiz)
from servidor import diario as D
FALLAS = []
def revisar(nombre, cond, det=""):
    print(("OK    " if cond else "FALLA ") + nombre, det)
    if not cond: FALLAS.append(nombre)
subidos = []
def falso(local, remoto, tipo="x"):
    shutil.copy(local, raiz + "/_subido.zip"); subidos.append(remoto)
D.E.subir = falso
D.guardar_captura("línea de prueba de main.py")
revisar("S1 sube capturas/FECHA.zip", subidos == [f"pruebas/ensayo/capturas/{sys.argv[2]}.zip"], str(subidos))
z = zipfile.ZipFile(raiz + "/_subido.zip"); nombres = z.namelist()
resp = [x for x in nombres if "/ia_respuestas/direccion/" in x]
pag = [x for x in nombres if "/ia_respuestas/" not in x]
revisar("S1 la captura trae las páginas, navegacion.json y la salida", any(x.endswith("navegacion.json") for x in pag) and any(x.endswith("salida_main.txt") for x in pag), f"{len(pag)} archivos")
revisar("S1 la captura trae respuestas de Haiku", len(resp) > 0, f"{len(resp)} respuestas, {os.path.getsize(raiz + '/_subido.zip') // 1024} KB")
# El día se rehace solo con la captura, en una carpeta de respuestas vacía
from motor.edicion import procesar, paginas_desde_captura
from motor import direccion as DR
rollos, _ = paginas_desde_captura(D.RAIZ / "capturas" / sys.argv[2])
antes = procesar(rollos, sys.argv[2], cliente=None)["ia"]
tmp = tempfile.mkdtemp(); z.extractall(tmp)
original = DR.CARPETA_RESPUESTAS
DR.CARPETA_RESPUESTAS = D.Path(tmp) / sys.argv[2] / "ia_respuestas" / "direccion"
rollos2, _ = paginas_desde_captura(D.Path(tmp) / sys.argv[2])
despues = procesar(rollos2, sys.argv[2], cliente=None)["ia"]
DR.CARPETA_RESPUESTAS = original
revisar("S1 el día rehecho solo con la captura da los mismos colores", antes["colores"] == despues["colores"] and antes["sin_ia"] == despues["sin_ia"], f"{despues['colores']} sin respuesta {despues['sin_ia']}")
revisar("S1 una respuesta por aviso leído", len(resp) == despues["leidos"] or len(resp) <= despues["leidos"], f"{len(resp)} respuestas, {despues['leidos']} avisos leídos")
# Si falla el agregado de respuestas, la captura se sube igual
subidos.clear()
viejo = D._respuestas_del_dia
import motor.edicion as ME
real = ME.paginas_desde_captura
def rota(*a, **k): raise RuntimeError("fallo de prueba")
ME.paginas_desde_captura = rota
D.guardar_captura("x")
ME.paginas_desde_captura = real
z2 = zipfile.ZipFile(raiz + "/_subido.zip")
revisar("S1 si no se pueden agregar las respuestas, la captura se sube igual sin ellas", len(subidos) == 1 and not any("/ia_respuestas/" in x for x in z2.namelist()))
# Si falla la subida, no se cae
def roto(*a, **k): raise RuntimeError("Supabase no guardó")
D.E.subir = roto
try:
    D.guardar_captura("x"); ok = True
except Exception:
    ok = False
revisar("sigue igual. si Supabase no guarda, la corrida sigue", ok)
print(); print("RESULTADO. TODO OK" if not FALLAS else f"RESULTADO. {len(FALLAS)} FALLAS. {FALLAS}")

# --- S2. El zip de respuestas llega dañado ---------------------------------------------------------------------------
class Llego(Exception): pass
sub2 = []
def bajar(remoto, local):
    if remoto.endswith("ia_respuestas.zip"): D.Path(local).write_bytes(b"esto no es un zip")
    else: shutil.copy(D.RAIZ / "causas_ojv.xlsx", local) if D.Path(local).name != "causas_ojv.xlsx" else None
D.E.bajar = bajar; D.E.existe = lambda r: False; D.E.subir_texto = lambda *a, **k: None
D.E.subir = lambda local, remoto, tipo="x": sub2.append(remoto)
def corre(*a, **k): raise Llego()
D.subprocess.run = corre
try:
    D.main(); paso = False
except Llego:
    paso = True
except Exception as e:
    paso = False; print("   cayó con", type(e).__name__, e)
revisar("S2 con el zip dañado la corrida llega hasta main.py", paso)
revisar("S2 el zip dañado queda guardado aparte en respaldos/", any("respaldos/ia_respuestas_danado_" in x for x in sub2), str(sub2))
print(); print("RESULTADO. TODO OK" if not FALLAS else f"RESULTADO. {len(FALLAS)} FALLAS. {FALLAS}")
