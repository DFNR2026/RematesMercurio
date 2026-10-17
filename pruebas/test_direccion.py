"""Parte 3.7b. Prueba de la dirección leída por la IA (motor/direccion.py), sin internet. No llama a Haiku.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_direccion

1. El 14 de Octubre (banco de AJUSTE) con las respuestas guardadas da 60 aciertos, 1 no leído y 0 equivocados.
2. Casos hechos a mano para cada control del verificador.
3. Números en palabras.
4. Candado. La prueba no escribe ninguna respuesta nueva en ia_respuestas.
"""
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor import direccion as D
from motor.numeros_texto import palabras_a_numero, palabras_a_cifras, numeros_en
from pruebas.medir_direccion import cargar, n_remates, comparar

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

antes = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))

# 1. Banco del 14 de Octubre con lo guardado
d, ed, av, banco = cargar("14")
cuenta, verdes = {}, 0
for n, e in sorted(banco.items()):
    t = av[n].texto; nr = n_remates(t, ed)
    g = D.leer_guardada(t, nr)
    if not g:
        cuenta["sin_respuesta"] = cuenta.get("sin_respuesta", 0) + 1; continue
    res = D.resolver(g["lecturas"], t, nr)
    if res["color"] == "verde":
        verdes += 1
        for x, ee in zip(g["lecturas"][0]["inmuebles"], e["remates"]):
            c = comparar(x, ee); cuenta[c] = cuenta.get(c, 0) + 1
        for i in res["inmuebles"]:
            if i["cita"] not in t or any(c not in t for c in i["citas_extra"]):
                FALLAS.append(f"cita que no está en el aviso {n}")
    else:
        cuenta["no_leido"] = cuenta.get("no_leido", 0) + len(e["remates"])
revisar("14-10. 60 aciertos, 1 no leído, 0 equivocados (ajuste dir-2 con los arreglos 1 a 4)", cuenta == {"acierto": 60, "no_leido": 1}, str(cuenta))
revisar("14-10. las citas de la dirección están en su aviso", not any(f.startswith("cita") for f in FALLAS))

# 2. Casos hechos a mano
T = ("REMATE 1° JUZGADO CIVIL DE Santiago, Huérfanos 1409. Se rematará el departamento número trescientos dos D del edificio con "
     "acceso por calle Agustinas número mil ochocientos ochenta y ocho, Comuna de Santiago. Mínimo $ 10.000.000.")
def L(**k):
    base = {"tipo": "calle", "calle": "calle Agustinas", "numero": "1888", "unidad": "departamento 302 D", "comuna": "Santiago",
            "frase_direccion": "acceso por calle Agustinas número mil ochocientos ochenta y ocho", "frase_unidad": "departamento número trescientos dos D",
            "frase_comuna": "Comuna de Santiago"}
    base.update(k); return {"inmuebles": [base]}
r = D.resolver([L(), L()], T, 1)
revisar("verde con número y unidad en palabras, guarda las cifras", r["color"] == "verde" and r["inmuebles"][0]["direccion"] == "calle Agustinas 1888, departamento 302 D"
        and r["inmuebles"][0]["comuna"] == "Santiago", str(r["inmuebles"]))
revisar("rojo si la frase no está en el aviso", D.resolver([L(frase_direccion="calle Agustinas 1888"), L(frase_direccion="calle Agustinas 1888")], T, 1)["color"] == "rojo")
revisar("rojo si el número no está en la frase", D.resolver([L(numero="1889"), L(numero="1889")], T, 1)["color"] == "rojo")
revisar("rojo si la calle no está en la frase", D.resolver([L(calle="calle Huérfanos"), L(calle="calle Huérfanos")], T, 1)["color"] == "rojo")
revisar("rojo si la comuna no está en su frase", D.resolver([L(comuna="Providencia"), L(comuna="Providencia")], T, 1)["color"] == "rojo")
revisar("rojo si el número de la unidad no está en su frase", D.resolver([L(unidad="departamento 303 D"), L(unidad="departamento 303 D")], T, 1)["color"] == "rojo")
rd = D.resolver([L(), L(numero="1889")], T, 1)
revisar("rojo si las dos lecturas no coinciden, y el texto trae las dos lecturas y la frase del aviso",
        rd["color"] == "rojo" and "calle Agustinas 1888" in D.texto_rojo(rd) and "calle Agustinas 1889" in D.texto_rojo(rd)
        and "En el aviso aparece así 'acceso por calle Agustinas número mil ochocientos ochenta y ocho'" in D.texto_rojo(rd)
        and D.texto_rojo(rd).startswith("Falla de la IA. Las dos lecturas de la IA dieron direcciones distintas."), D.texto_rojo(rd))
revisar("el texto del rojo no usa dos puntos ni punto y coma", ":" not in D.texto_rojo(rd).split("aparece así")[0] and ";" not in D.texto_rojo(rd))
revisar("rojo si la IA da menos direcciones que remates", D.resolver([L(), L()], T, 2)["color"] == "rojo")
revisar("rojo si falta la segunda lectura", D.resolver([L()], T, 1)["color"] == "rojo")
SD = {"inmuebles": [{"tipo": "sin_dato", "calle": None, "numero": None, "unidad": None, "comuna": None, "frase_direccion": None, "frase_unidad": None, "frase_comuna": None}]}
revisar("sin_dato que no se acepta si el aviso parece dar la dirección", D.resolver([SD, SD], T, 1)["color"] == "rojo")
revisar("sin_dato aceptado si no hay señales de dirección", D.resolver([SD, SD], "REMATE. Se rematará el inmueble de autos. Mínimo $ 1.000.", 1)["color"] == "sin_dato")
revisar("la unidad cuenta solo su primer número (piso y edificio no)", D.unidad_clave("Departamento Número 403, Torre I, Piso 4°, Edificio 5") == D.unidad_clave("departamento 403"))
TC = T + " Inscrito a fojas 1 número 2 del Registro de Propiedad del Conservador de Bienes Raíces de Casablanca."
rc = D.resolver([L(comuna="Casablanca", frase_comuna="Conservador de Bienes Raíces de Casablanca")] * 2, TC, 1)
revisar("la comuna sacada de la frase del Conservador queda vacía y la dirección sigue en verde (06-10 avisos 66 y 90)",
        rc["color"] == "verde" and rc["inmuebles"][0]["comuna"] is None, str(rc["inmuebles"])[:150])
revisar("rojo si la unidad no trae número", D.resolver([L(unidad="departamento D")] * 2, T, 1)["color"] == "rojo")
revisar("depto y departamento son lo mismo", D.unidad_clave("depto 1504") == D.unidad_clave("departamento 1504"))
revisar("rojo si el tipo de la unidad no es el de su frase (oficina contra departamento)",
        D.resolver([L(unidad="oficina 302 D")] * 2, T, 1)["color"] == "rojo")
T3 = ("se rematarán las oficinas números 602 y 603, ambas del sexto piso, con acceso general por Avenida Pajaritos N° 3195, comuna de Maipú. "
      "Mínimo oficina 602 $ 1.000.000. Mínimo oficina 603 $ 2.000.000.")
O = lambda u: {"tipo": "calle", "calle": "Avenida Pajaritos", "numero": "3195", "unidad": u, "comuna": "Maipú", "frase_direccion": "Avenida Pajaritos N° 3195",
               "frase_unidad": "las oficinas números 602 y 603", "frase_comuna": "comuna de Maipú"}
revisar("la unidad en plural en su frase (14-10 aviso 3)", D.resolver([{"inmuebles": [O("oficina 602"), O("oficina 603")]}] * 2, T3, 2)["color"] == "verde")

# 3. Números en palabras
revisar("números en palabras", [palabras_a_numero(x) for x in ("ochocientos sesenta y uno", "veintiún mil quinientos", "cero ciento ochenta y uno", "trecientos once")]
        == ["861", "21500", "0181", "311"])
revisar("dos números separados por barra", {"6590", "6594"} <= numeros_en("número seis mil quinientos noventa/ seis mil quinientos noventa y cuatro"))
revisar("palabras a cifras dentro de un texto", palabras_a_cifras("departamento A trescientos nueve") == "departamento A 309")

despues = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
revisar("candado. la prueba no escribió ninguna respuesta nueva en ia_respuestas (no llamó a Haiku)", antes == despues, str(sorted(set(despues) - set(antes)))[:200])
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)
