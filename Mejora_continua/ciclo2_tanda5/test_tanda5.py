"""Ciclo 2 de mejora de la lectura, tanda 5 (10 de Noviembre de 2026). El ° impreso como un 3 suelto en el tribunal y en la
inscripción. Sin internet y sin Haiku. Correr desde la raíz del proyecto con. python -m pruebas.test_tanda5
"""
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.extraccion import tribunal, inscripcion

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

def tr(t):
    return tribunal(t)["tribunal"]["valor"]

def ins(t):
    return [(x["fojas"], x["numero"], x["anio"]) for x in inscripcion(t, "2026-11-09")["inscripcion"]]

# --- G1. Tribunal ---------------------------------------------------------------------------------------------------
A = "REMATE 2 3 JUZGADO CIVIL DE SANtiago, Huérfanos 1409, 7 3 piso, rematará 10 de diciembre 2026, 12:00 hrs."
revisar("G1 '2 3 JUZGADO' es el 2° Civil (21355-2023)", tr(A) == "2° Juzgado Civil de Santiago", str(tr(A)))
revisar("G1 la cita es la del aviso", tribunal(A)["tribunal"]["cita"].startswith("2 3 JUZGADO CIVIL"), tribunal(A)["tribunal"]["cita"])
revisar("G1 '18 3 Juzgado' es el 18° Civil", tr("18 3 Juzgado Civil de Santiago, Huérfanos 1409, 5° piso") == "18° Juzgado Civil de Santiago")
revisar("G1 '3 3 Juzgado' es el 3° Civil", tr("REMATE 3 3 JUZGADO CIVIL DE Santiago, Huérfanos 1409") == "3° Juzgado Civil de Santiago")
revisar("sigue igual. 3° Juzgado bien impreso", tr("REMATE 3° JUZGADO CIVIL DE Santiago, Huérfanos 1409, 7° piso") == "3° Juzgado Civil de Santiago")
revisar("sigue igual. 3 Juzgado sin número antes", tr("REMATE 3 JUZGADO CIVIL DE Santiago, Huérfanos 1409") == "3° Juzgado Civil de Santiago")
revisar("sigue igual. 2° Juzgado bien impreso (21355-2023 del 10 de Noviembre)", tr("REMATE 2° JUZGADO CIVIL DE SANtiago, Huérfanos 1409, 7° piso") == "2° Juzgado Civil de Santiago")
revisar("sigue igual. un número de calle antes no cuenta", tr("Huérfanos 1409 3 Juzgado Civil de Santiago, rematará") == "3° Juzgado Civil de Santiago")
revisar("sigue igual. una fecha antes no cuenta", tr("Remate 12/11 3 Juzgado Civil de Santiago, rematará") == "3° Juzgado Civil de Santiago")
revisar("sigue igual. Tercer Juzgado en palabras", tr("ante el Tercer Juzgado Civil de Viña del Mar, Arlegui 346") == "3° Juzgado Civil de Viña del Mar")
revisar("sigue igual. 23° Juzgado", tr("REMATE 23° JUZGADO CIVIL DE Santiago, Huérfanos 1409") == "23° Juzgado Civil de Santiago")

# --- G2. Inscripción ------------------------------------------------------------------------------------------------
revisar("G2 'N 3 22232' es el número 22232 (21355-2023)", ins("a Fojas 15422 N 3 22232 Registro Propiedad año 2022, Conservador Bienes Raíces Santiago. Mínimo") == [("15422", "22232", "2022")],
        str(ins("a Fojas 15422 N 3 22232 Registro Propiedad año 2022, Conservador Bienes Raíces Santiago. Mínimo")))
revisar("sigue igual. N° bien impreso", ins("inscrito a fojas 15422 N° 22232 del Registro de Propiedad del año 2022 del Conservador de Bienes Raíces de Santiago.") == [("15422", "22232", "2022")])
revisar("sigue igual. 'N 3' sin otro número después no se adivina", ins("inscrito a fojas 120 N 3 del Registro de Propiedad del año 2010 del Conservador de Bienes Raíces de Santiago.") == [])
revisar("sigue igual. N pegada al número", ins("inscrito a fojas 57.106 N81.820 del Registro de Propiedad del año 2009") == [("57106", "81820", "2009")])

print()
print("RESULTADO. TODO OK" if not FALLAS else f"RESULTADO. {len(FALLAS)} FALLAS. {FALLAS}")
sys.exit(1 if FALLAS else 0)
