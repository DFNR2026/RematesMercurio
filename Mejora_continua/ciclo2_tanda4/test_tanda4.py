"""Ciclo 2 de mejora de la lectura, tanda 4 (10 de Noviembre de 2026). Direcciones y corte de dominio 2019. Sin internet y
sin Haiku. Correr desde la raíz del proyecto con. python -m pruebas.test_tanda4

Cada prueba usa el texto real que motivó el arreglo y hay casos que deben seguir igual.
"""
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor import direccion as DR
from motor import conjunto as CJ
from motor import filtros as F
from motor.numeros_texto import palabras_a_cifras

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

def inm(calle, numero, comuna, fd, fc, unidad=None, fu=None, tipo="calle"):
    return {"tipo": tipo, "calle": calle, "numero": numero, "unidad": unidad, "comuna": comuna,
            "frase_direccion": fd, "frase_unidad": fu, "frase_comuna": fc}

def lect(*xs):
    return [{"inmuebles": [x]} for x in xs]

# --- T4a. Comuna comprobada con la dirección en rojo -----------------------------------------------------------------
TALCA = ("se rematará inmueble ubicado en calle 6 Oriente esquina 5 Norte N°1600, de la comuna y provincia de Talca, Región del "
         "Maule. Inscrita Fojas 27560 Número 10429 Registro Propiedad 2014 Conservador de Bienes Raíces de Talca. Mínimo posturas $ 69.922.681.")
FD, FC = "calle 6 Oriente esquina 5 Norte N°1600", "de la comuna y provincia de Talca"
a = inm("calle 6 Oriente", "1600", "Talca", FD, FC)
b = inm("calle 6 Oriente esquina 5 Norte", "1600", "Talca", FD, FC)
revisar("T4a las dos lecturas dan Talca y se comprueba (1267-2019)", DR.comunas_del_rojo(lect(a, b), TALCA, 1) == ["Talca"])
revisar("T4a comunas distintas no se conserva", DR.comunas_del_rojo(lect(a, dict(b, comuna="Maule", frase_comuna="Región del Maule")), TALCA, 1) == [None])
revisar("T4a una lectura sin comuna no se conserva", DR.comunas_del_rojo(lect(a, dict(b, comuna=None, frase_comuna=None)), TALCA, 1) == [None])
revisar("T4a frase de comuna que no está en el aviso no se conserva", DR.comunas_del_rojo(lect(dict(a, frase_comuna="comuna de Talca, Chile"), b), TALCA, 1) == [None])
revisar("T4a comuna que no está en su frase no se conserva", DR.comunas_del_rojo(lect(dict(a, comuna="Curicó"), dict(b, comuna="Curicó")), TALCA, 1) == [None])
revisar("T4a comuna sacada del Conservador no se conserva",
        DR.comunas_del_rojo(lect(dict(a, frase_comuna="Conservador de Bienes Raíces de Talca"), dict(b, frase_comuna="Conservador de Bienes Raíces de Talca")), TALCA, 1) == [None])
revisar("T4a cantidad de direcciones distinta a los remates no entrega nada", DR.comunas_del_rojo(lect(a, b), TALCA, 2) == [])
revisar("T4a una sola lectura no entrega nada", DR.comunas_del_rojo(lect(a), TALCA, 1) == [])
r = DR.resolver(lect(a, dict(b, calle="calle 5 Norte")), TALCA, 1)
revisar("T4a el rojo sigue sin dirección (calles distintas)", r["color"] == "rojo" and r["inmuebles"] == [])

# --- D4e. Una lectura agrega la esquina -----------------------------------------------------------------------------
r = DR.resolver(lect(a, b), TALCA, 1)
revisar("D4e queda la calle común (1267-2019)", r["color"] == "verde" and r["inmuebles"][0]["direccion"] == "calle 6 Oriente 1600" and r["inmuebles"][0]["comuna"] == "Talca", str(r["inmuebles"]))
r = DR.resolver(lect(b, a), TALCA, 1)
revisar("D4e en el otro orden da lo mismo", r["color"] == "verde" and r["inmuebles"][0]["direccion"] == "calle 6 Oriente 1600")
r = DR.resolver(lect(a, dict(b, numero="1601")), TALCA, 1)
revisar("sigue igual. esquina con otro número queda en rojo", r["color"] == "rojo")
r = DR.resolver(lect(a, dict(b, calle="calle 6 Oriente Sur")), TALCA, 1)
revisar("sigue igual. calle más larga sin la palabra esquina queda en rojo", r["color"] == "rojo")
r = DR.resolver(lect(a, dict(b, comuna="Maule", frase_comuna="Región del Maule")), TALCA, 1)
revisar("sigue igual. esquina con otra comuna queda en rojo", r["color"] == "rojo")

# --- D12. Número en palabras pegado a una coma -----------------------------------------------------------------------
revisar("D12 Ciento Seis con coma (12090-2024)", palabras_a_cifras("Departamento Número Ciento Seis, del Primer Piso, De La Torre A") == "Departamento Número 106, del Primer Piso, De La Torre A",
        palabras_a_cifras("Departamento Número Ciento Seis, del Primer Piso, De La Torre A"))
revisar("D12 las dos lecturas del 12090-2024 dan la misma unidad",
        DR.unidad_clave("Departamento Número Ciento Seis") == DR.unidad_clave("Departamento Número Ciento Seis, del Primer Piso, De La Torre A") == ("departamento", ("106",)))
revisar("D12 con punto al final", palabras_a_cifras("oficina doscientos dos.") == "oficina 202.")
revisar("sigue igual. sin coma", palabras_a_cifras("departamento A trescientos nueve") == "departamento A 309")
revisar("sigue igual. cuatro-A (D10)", palabras_a_cifras("la vivienda número cuatro-A") == "la vivienda número 4-A")
revisar("sigue igual. cuatro y un (D1b)", (palabras_a_cifras("Parcela número cuatro y un 6,25%") or "").startswith("Parcela número 4 y"))
revisar("sigue igual. texto sin números", palabras_a_cifras("casa esquina, de material sólido.") == "casa esquina, de material sólido.")

# --- E1 y E2. Nombres de edificio -----------------------------------------------------------------------------------
def ed(t):
    return (CJ.conjunto(t) or {}).get("nombre_edificio")
revisar("E1 Edificio ONIX (755-2023)", ed("del segundo subterráneo, del Edificio ONIX, de calle Primera Avenida 1336 y derechos") == "ONIX")
revisar("E1 Edificio Fam (3613-2024)", ed("el departamento N° 211 del 2° piso, del Edificio Fam, con acceso por Avenida Ossa N° 480") == "Fam")
revisar("E1 la dirección sale con el nombre", CJ.describir("departamento 1809 del Edificio ONIX, de calle Primera Avenida 1336", "Primera Avenida 1336, Departamento 1809", "Primera Avenida").startswith("Edificio ONIX. Primera Avenida 1336"))
for sub in ("B", "5", "B2", "A-1", "AB", "B Dos", "Cuatro", "Sur", "III"):
    revisar(f"sigue igual. 'Edificio {sub}' es una parte y no un nombre", ed(f"departamento 27 del Edificio {sub}, con ingreso por Avenida Inglaterra 1144") is None)
revisar("sigue igual. Edificio B Dos entre comillas (2929-2025)", ed("del denominado ‘Edificio B Dos’, perteneciente al Conjunto Habitacional ‘Nueva Inglaterra’") is None)
revisar("E2 Edificio de La Recoleta Urbano (14456-2025)", ed("en el subterráneo, ambos del Edificio de La Recoleta Urbano, con acceso peatonal por calle Juárez número seiscientos veintiuno") == "de La Recoleta Urbano")
revisar("E2 una dirección no es un nombre (207-2026)", ed("del noveno piso, del edificio de Moneda tres mil setenta y cuatro, con acceso por calle Moneda número tres mil noventa") is None)
revisar("E2 'Edificio de Avenida' no es un nombre", ed("departamento 12 del Edificio de Avenida Inglaterra 1144, comuna de Independencia") is None)
revisar("E2 'edificio de calle' no es un nombre", ed("departamento 12 del edificio de calle Moneda 3090, comuna de Santiago") is None)
revisar("sigue igual. nombre con mayúscula de siempre", ed("departamento 715 del Edificio Parque Los Reyes, con acceso por calle Juárez 621") == "Parque Los Reyes")

# --- R1. Corte del dominio en 2019 ----------------------------------------------------------------------------------
revisar("R1 dominio de 2019 queda excluido", F._cbr({"anios": [2019]}) == ("falla", 2019))
revisar("R1 dominio de 2018 pasa", F._cbr({"anios": [2018]}) == ("pasa", 2018))
revisar("R1 dos inscripciones, una anterior a 2019, pasa", F._cbr({"anios": [2019, 2015]}) == ("pasa", 2015))
revisar("sigue igual. dominio de 2020 o posterior queda excluido", F._cbr({"anios": [2021]}) == ("falla", 2021))
revisar("sigue igual. sin año va a revisar", F._cbr({"anios": []}) == ("sin_dato", None))
revisar("R1 la Observación dice 2019", "anterior a 2019" in F.OBS_DOMINIO)

print()
print("RESULTADO. TODO OK" if not FALLAS else f"RESULTADO. {len(FALLAS)} FALLAS. {FALLAS}")
sys.exit(1 if FALLAS else 0)
