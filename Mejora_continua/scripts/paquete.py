import sys,json
sys.path.insert(0,".")
from motor.extraccion import caratula
from motor.numeros_texto import numeros_en
from motor import direccion as DR
B=json.load(open("Excels_Supabase/Banco_fallos/avisos_con_fallo_14_al_18.json"))
extra={r:json.load(open(f"{sys.argv[1]}/{r}.json"))["texto"][0] for r in ["6108","7898","4567","188","20862"]}
def txt(rol, ultimo=True):
    if rol.split("-")[0] in extra: return extra[rol.split("-")[0]]
    xs=[r for r in B if r["rol"]==rol]; return xs[-1 if ultimo else 0]
def aviso(rol,i=-1):
    xs=[r for r in B if r["rol"]==rol]; return xs[i]
casos=[]
def car(id_,tipo,rol,esperado,nota=""):
    t=txt(rol) if rol.split("-")[0] in extra else aviso(rol)["texto"]
    r=caratula(t)
    casos.append({"id":id_,"tipo":tipo,"funcion":"motor/extraccion.py caratula()","rol":rol,
      "resultado_actual":{"valor":r["caratula"]["valor"],"alertas":[a[1] for a in r["alertas"]]},
      "esperado":esperado,"nota":nota,"texto_aviso":t})
car("C1a","C1","4567-2026","Banco Santander-Chile S.A. Con Unanue")
car("C1b","C1","13731-2025","Banco Santander-Chile S.A con Rivas Contreras")
car("C1c","C1","8167-2024","Banco De Chile Con Covarrubias","viene como 'autos rol c-8167-2024 Banco De Chile Con Covarrubias. Juicio'")
car("C2a","C2","1177-2025","Banco de Chile con Hinojosa","la carátula va pegada al tribunal, sin palabra que la anuncie")
car("C2b","C2","4079-2023","Bravo con Bravo","juicio de partición, va después de 'Rol N° C-4079-2023,'")
car("C3a","C3","26036-2016","Aval Chile S.A.G.R./ Torres","solo comilla de cierre")
car("C3b","C3","18954-2024","Avla Seguros de Crédito y Garantía S.A./ Pozo","solo comilla de apertura")
car("C4","C4","6108-2025","Banco Itaú Chile SA./ Bosque Petreles S.A","'Caratulado:' seguido de texto sin punto ('decretó la subasta')")
car("C5","C5","7898-2024","Cooperativa De Ahorro Y Crédito Coopeuch/ Castillo","'caratulada,,' con doble coma")
# negativos
car("N1","negativo","188-2025",None,"carátula incompleta impresa en el aviso ('“/O’Brien“'). Debe seguir sin valor y con su alerta")
for r in B:
    if r["rol"]=="SIN ROL":
        t=r["texto"]; x=caratula(t)
        casos.append({"id":"N2" if "PUENTE" in t[:40] else "N3","tipo":"negativo","funcion":"motor/extraccion.py caratula()","rol":"sin rol",
          "resultado_actual":{"valor":x["caratula"]["valor"],"alertas":[a[1] for a in x["alertas"]]},"esperado":None,
          "nota":"aviso que no es juicio (interdicción o remate privado). No debe inventar carátula","texto_aviso":t})
# direccion
def dirc(id_,tipo,rol,esperado,nota,i=-1,funcion="motor/direccion.py verificar_inmueble() y motor/numeros_texto.py"):
    r=aviso(rol,i); res=DR.resolver(r["lecturas"],r["texto"],r["n"])
    casos.append({"id":id_,"tipo":tipo,"funcion":funcion,"rol":rol,"n_remates":r["n"],
      "lecturas_ia":r["lecturas"],"resultado_actual":{"color":res["color"],"motivos":res["motivos"]},
      "esperado":esperado,"nota":nota,"texto_aviso":r["texto"]})
dirc("D1","D1","20862-2024",{"color":"verde","direccion":"calle Santa Lucía 232 y 234, departamento 71","comuna":"Santiago"},
     "numeros_en('números doscientos treinta y dos y doscientos treinta y cuatro') da {'466'}. Igual con 'quinientos setenta y cinco y quinientos setenta y siete', que da {'1152'}",
     funcion="motor/numeros_texto.py numeros_en()")
dirc("D5a","D5","5633-2024","A decidir. Propuesta, verde con 'Avenida Alcalde José Infante Larraín s/n' si la frase trae s/n",
     "la IA da numero 's/n' y el programa exige cifras")
dirc("D5b","D5","28-2025","A decidir. La instrucción a la IA dice sin_calle para un sitio de loteo sin número, la IA dio tipo calle sin número",
     "cambiar las instrucciones cambia VERSION_INSTRUCCIONES y la huella, y obliga a pagar de nuevo todas las lecturas")
casos.append({"id":"D6","tipo":"D6","funcion":"motor/direccion.py verificar_inmueble() líneas 172-174","rol":"4485-2024 (16° Civil, edición del 30 de Octubre)",
  "lecturas_ia":"no guardadas en el disco. Según ESTADO_PROYECTO.md la IA leyó 'Nicanor Plaza 2475, Casa H, La Reina'",
  "resultado_actual":{"color":"rojo","motivos":["La unidad que dio la IA no trae número."]},
  "esperado":"A decidir. Propuesta, aceptar una unidad con letra si la letra está en su frase",
  "nota":"SIN TEXTO DEL AVISO. Además pruebas/test_direccion.py línea 77 exige hoy el rojo para 'departamento D'. Cambiarlo es cambiar una regla probada","texto_aviso":None})
json.dump(casos,open(sys.argv[2]+"/casos.json","w"),ensure_ascii=False,indent=1)
for c in casos: print(c["id"],c["rol"],"| actual:",json.dumps(c["resultado_actual"],ensure_ascii=False)[:150])
