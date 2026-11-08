"""Ciclo 2 de mejora de la lectura (8 de Noviembre de 2026). Pruebas de los arreglos de la tanda 1, sin internet y sin Haiku.
Correr desde la raíz del proyecto con. python -m pruebas.test_mejora_ciclo2

Cada prueba usa el caso real que motivó el arreglo (banco en Storage_supabase/Banco_ciclo2) y un caso que debe seguir igual.
"""
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor import direccion as D
from motor.ia_comun import buscar_frase
from motor.numeros_texto import palabras_a_cifras
from motor.extraccion import minimo_y_costas
from motor.orden_columnas import texto_por_posicion

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

def L(**k):
    base = {"tipo": "calle", "calle": "calle Carmen", "numero": "660", "unidad": None, "comuna": "Santiago",
            "frase_direccion": "con acceso peatonal por calle Carmen 660", "frase_unidad": None, "frase_comuna": "Comuna de Santiago"}
    base.update(k)
    return {"inmuebles": [base]}

# --- D8. Orden de columnas. Solo corta la página si el MISMO número de sección está en 3 columnas o más ---------------
def pagina(secundarias):
    items = [["VIERNES", 700, 1572, 50, 7]]
    for c in range(4):
        items.append(["1616", 10 + 100 * c, 1547, 19, 14.9])
    for c in range(4):
        items.append([f"col{c} arriba", 10 + 100 * c, 900, 90, 5.5])
        items.append([f"col{c} abajo", 10 + 100 * c, 200, 90, 5.5])
    for c, cod in secundarias:
        items.append([cod, 12 + 100 * c, 312, 26, 13.9])
    return {"items": items}

t = texto_por_posicion(pagina([(1, "1612"), (2, "1616")]))
revisar("D8 dos secciones distintas en dos columnas no cortan la página (B09 del 5 de Noviembre)",
        t.index("col3 arriba") < t.index("col3 abajo") and t.index("col2 abajo") < t.index("col3 arriba"), repr(t))
t = texto_por_posicion(pagina([(1, "1309"), (2, "1309"), (3, "1309")]))
revisar("D8 el mismo número en 3 columnas sigue siendo franja (1309 Empleos)",
        t.index("col3 arriba") < t.index("col1 abajo"), repr(t))

# --- D3. Comillas rectas y curvas iguales. Mayúsculas no ------------------------------------------------------------
revisar("D3 comilla recta contra curva (12688-2023)",
        buscar_frase("predio denominado 'sector b. Potrero El Maitén'", "del predio denominado ‘sector b. Potrero El Maitén’, prov") is not None)
revisar("D3 devuelve el tramo tal como está en el aviso",
        buscar_frase("'Plaza'", "Condominio ‘Plaza’ x") == "‘Plaza’")
revisar("D3 una mayúscula distinta sigue sin pasar", buscar_frase("El Sitio", "el Sitio") is None)

# --- D9 y D10. Número de la unidad --------------------------------------------------------------------------------
revisar("D9 departamento 2.708 es el 2708 (14652-2025)", D.unidad_clave("departamento 2.708") == ("departamento", ("2708",)))
revisar("D10 vivienda cuatro-A es la 4 (4294-2025)", palabras_a_cifras("vivienda número cuatro-A") == "vivienda número 4-A")
revisar("D10 un guion entre palabras no se toca", palabras_a_cifras("Pasaje Santa-Rosa") == "Pasaje Santa-Rosa")

# --- D1b. La "y" solo une decena y unidad en palabras_a_cifras -------------------------------------------------------
revisar("D1b cuatro y un no suma (6004-2023)", palabras_a_cifras("Parcela número cuatro y un 6,25%") == "Parcela número 4 y 1 6,25%")
revisar("D1b dos números unidos por y", palabras_a_cifras("doscientos treinta y dos y doscientos treinta y cuatro") == "232 y 234")
revisar("D1b treinta y dos sigue siendo 32", palabras_a_cifras("departamento trescientos treinta y dos") == "departamento 332")

# --- D6. Unidad con letra sin número ---------------------------------------------------------------------------------
TH = ("la propiedad correspondiente a Casa H, del ‘Condominio Montevista’, con acceso por calle Nicanor Plaza número dos mil "
      "cuatrocientos setenta y cinco, Comuna de La Reina, Región Metropolitana")
lh = L(calle="calle Nicanor Plaza", numero="2475", unidad="Casa H", comuna="La Reina",
       frase_direccion="con acceso por calle Nicanor Plaza número dos mil cuatrocientos setenta y cinco",
       frase_unidad="Casa H, del ‘Condominio Montevista’", frase_comuna="Comuna de La Reina")
rh = D.resolver([lh, lh], TH, 1)
revisar("D6 Casa H en verde (4485-2024)", rh["color"] == "verde" and rh["inmuebles"][0]["direccion"] == "calle Nicanor Plaza 2475, Casa H", rh)
revisar("D6 una a suelta no es letra de unidad", not D._unidad_con_letra("casa A", "la casa a la que"))

# --- D5a. Calle sin número ------------------------------------------------------------------------------------------
TS = ("el inmueble ubicado en pasaje Los Olmos s/n, comuna de Maipú, Región Metropolitana")
ls = L(calle="pasaje Los Olmos", numero=None, comuna="Maipú", frase_direccion="ubicado en pasaje Los Olmos s/n", frase_comuna="comuna de Maipú")
rs = D.resolver([ls, ls], TS, 1)
revisar("D5a calle s/n en verde", rs["color"] == "verde" and rs["inmuebles"][0]["direccion"] == "pasaje Los Olmos s/n", rs)
TN = "el inmueble ubicado en pasaje Los Olmos número veinte, comuna de Maipú"
ln = L(calle="pasaje Los Olmos", numero=None, comuna="Maipú", frase_direccion="ubicado en pasaje Los Olmos número veinte", frase_comuna="comuna de Maipú")
revisar("D5a rojo si la frase dice número y la IA no lo dio", D.resolver([ln, ln], TN, 1)["color"] == "rojo")

# --- D4a. Número de acceso de más -------------------------------------------------------------------------------------
TA = "Departamento 504 del piso 5, con acceso peatonal por calle Carmen 660, y con acceso vehicular por calle Carmen 650, Comuna de Santiago"
a1 = L()
a2 = L(numero="660 y 650", frase_direccion="con acceso peatonal por calle Carmen 660, y con acceso vehicular por calle Carmen 650, Comuna de Santiago")
ra = D.resolver([a1, a2], TA, 1)
revisar("D4a queda el número común (9124-2023)", ra["color"] == "verde" and ra["inmuebles"][0]["direccion"] == "calle Carmen 660", ra)
revisar("D4a funciona en cualquier orden", D.resolver([a2, a1], TA, 1)["inmuebles"][0]["direccion"] == "calle Carmen 660")
a3 = L(numero="650 y 660", frase_direccion=a2["inmuebles"][0]["frase_direccion"])
revisar("D4a rojo si el primer número no es el mismo", D.resolver([a1, a3], TA, 1)["color"] == "rojo")
a4 = L(calle="calle Huérfanos", numero="660 y 650")
revisar("D4a rojo si la calle es otra", D.resolver([a1, a4], TA, 1)["color"] == "rojo")

# --- D4b. Unidad en una lectura sí y en la otra no ------------------------------------------------------------------
TB = ("la propiedad ubicado en Calle Parque Cordillera N° 02886, que corresponde al sitio número 54, del Conjunto, comuna de Puente Alto")
b1 = L(calle="Calle Parque Cordillera", numero="02886", comuna="Puente Alto", frase_direccion="Calle Parque Cordillera N° 02886", frase_comuna="comuna de Puente Alto")
b2 = L(calle="Calle Parque Cordillera", numero="02886", comuna="Puente Alto", unidad="sitio 54", frase_unidad="sitio número 54",
       frase_direccion="Calle Parque Cordillera N° 02886", frase_comuna="comuna de Puente Alto")
rb = D.resolver([b1, b2], TB, 1)
revisar("D4b queda la que trae unidad comprobada (11560-2013)", rb["color"] == "verde" and rb["inmuebles"][0]["direccion"] == "Calle Parque Cordillera 02886, sitio 54", rb)
b3 = L(calle="Calle Parque Cordillera", numero="02886", comuna="Puente Alto", unidad="sitio 99", frase_unidad="sitio número 99",
       frase_direccion="Calle Parque Cordillera N° 02886", frase_comuna="comuna de Puente Alto")
rb3 = D.resolver([b1, b3], TB, 1)
revisar("D4b si la unidad no se comprueba, queda la dirección sin unidad", rb3["color"] == "verde" and rb3["inmuebles"][0]["direccion"] == "Calle Parque Cordillera 02886", rb3)
b4 = L(calle="Calle Parque Cordillera", numero="02887", comuna="Puente Alto", unidad="sitio 54", frase_unidad="sitio número 54",
       frase_direccion="Calle Parque Cordillera N° 02886", frase_comuna="comuna de Puente Alto")
revisar("D4b rojo si además cambia el número", D.resolver([b1, b4], TB, 1)["color"] == "rojo")

# --- D5c. Lista de mínimos con letras --------------------------------------------------------------------------------
TM = ("Mínimo posturas a) departamento N° 205C $46.847.342, b) Propiedad ubicada en Pasaje Goya Sur N° 1530 $95. 286.918. "
      "Para participar todo postor deberá rendir garantía equivalente al 10% del mínimo fijado.")
mm = minimo_y_costas(TM)["minimo"]
revisar("D5c una palabra mínimo con lista a) b) son 2 remates (8467-2025)",
        len(mm.get("lista") or []) == 2 and mm["lista"][1]["monto"] == 95286918.0, mm)
m1 = minimo_y_costas("Mínimo para las posturas $59.512.071.- pago 5° día hábil.")["minimo"]
revisar("D5c un mínimo simple sigue siendo uno", m1.get("monto") == 59512071.0 and "lista" not in m1, m1)

print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} FALLAS {FALLAS}")
sys.exit(1 if FALLAS else 0)
