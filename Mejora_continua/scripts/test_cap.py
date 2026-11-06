import os,sys,zipfile,shutil
raiz=sys.argv[1]; os.environ["FECHA"]=sys.argv[2]; os.environ["MODO"]=sys.argv[3]
sys.path.insert(0,raiz)
from servidor import diario as D
subidos=[]
def falso(local,remoto,tipo="x"): shutil.copy(local,raiz+"/_subido.zip"); subidos.append((remoto,tipo))
D.E.subir=falso
D.guardar_captura("línea de prueba de main.py")
print("subidos",subidos)
if subidos:
    z=zipfile.ZipFile(raiz+"/_subido.zip"); n=z.namelist(); print(len(n),"archivos", [x for x in n if "navegacion" in x or "salida" in x], os.path.getsize(raiz+"/_subido.zip"),"bytes")
    print(z.read(f"{sys.argv[2]}/salida_main.txt").decode())
# caso de error de subida
def roto(*a,**k): raise RuntimeError("Supabase no guardó")
D.E.subir=roto; D.guardar_captura("x")
