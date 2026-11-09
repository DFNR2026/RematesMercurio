"""Ciclo 2 de mejora, tanda 2 (8 de Noviembre de 2026). Pruebas del formato de condominios y edificios (motor/conjunto.py),
sin internet y sin Haiku. Correr desde la raíz del proyecto con. python -m pruebas.test_conjunto

Los textos son fragmentos reales de avisos guardados (rol entre paréntesis) y casos que deben quedar igual que antes.
"""
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.conjunto import describir, conjunto, piezas, accesos
from motor import direccion as D

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

# 5633-2024. Calle interior. La calle que dio la IA es la entrada del condominio (decisión de Diego del 8 de Noviembre).
T1 = ("el inmueble que consiste en la unidad número 47- 59, ubicada en la calle interior Canal Baker número 47- 59 del "
      "denominado ‘Condominio Barrio Patagonia’, así como el derecho de uso y goce exclusivo del estacionamiento número 59, con "
      "acceso principal por Avenida Alcalde José Infante Larraín s/n Lote Uno-Ocho A, comuna de Maipú, Región Metropolitana")
r = describir(T1, "Avenida Alcalde José Infante Larraín s/n, unidad 47-59", "Avenida Alcalde José Infante Larraín")
revisar("calle interior, estacionamiento y entrada (5633-2024)",
        r == "Condominio Barrio Patagonia. calle interior Canal Baker 47-59, unidad 47-59. Estacionamiento 59. "
             "Acceso por Avenida Alcalde José Infante Larraín s/n", r)

# 13112-2023. La entrada es otra calle.
T2 = ("inmueble que consiste en Unidad N° 112, ubicada calle Piedemonte N° 18551, Condominio Los Álamos, acceso común por "
      "Avenida del Manantial Oriente N° 18516, comuna San Bernardo, y derechos proporcionales en bienes comunes")
r = describir(T2, "calle Piedemonte 18551, unidad 112", "calle Piedemonte")
revisar("entrada por otra calle (13112-2023)",
        r == "Condominio Los Álamos. calle Piedemonte 18551, unidad 112. Acceso común por Avenida del Manantial Oriente N° 18516", r)

# 3182-2026. Departamento, Edificio B es parte del condominio y no su nombre, estacionamiento.
T3 = ("inmueble correspondiente al Departamento N° 407, 4° piso, Edificio B, ‘Condominio Mistral Oriente V’, calle Balada N° 2813, "
      "comuna de La Serena, el Derecho de Uso y Goce Exclusivo el Estacionamiento N° 63, 1° piso del mismo Condominio")
r = describir(T3, "calle Balada 2813, departamento 407", "calle Balada")
revisar("condominio de departamentos con estacionamiento (3182-2026)",
        r == "Condominio de departamentos Mistral Oriente V. calle Balada 2813, departamento 407. Estacionamiento 63", r)

# 20992-2023. Sin nombre, estacionamiento en palabras, bodega.
T4 = ("consistente en el Departamento N° 504 del quinto piso y la bodega N° 504 del piso subterráneo, todos del Condominio don "
      "Arturo, con acceso por Avenida Circunvalación N° 193, comuna de Ovalle. Se incluyen el derecho de uso y goce exclusivo del "
      "estacionamiento Número quinientos cuatro del piso primero del mismo Edificio")
r = describir(T4, "Avenida Circunvalación 193, departamento 504", "Avenida Circunvalación")
revisar("estacionamiento escrito en palabras y bodega, entrada por la misma calle (20992-2023)",
        r == "Condominio de departamentos. Avenida Circunvalación 193, departamento 504. Estacionamiento 504. Bodega 504", r)

# 2093-2024. Edificio. La entrada de estacionamientos es la misma calle y no se repite.
T5 = ("departamento 2406 del piso 24 y la bodega 135 del tercer subterráneo, ambos del ‘Edificio Eco Santiago’, con acceso principal "
      "por calle Apóstol Santiago N° 32, y con acceso a estacionamientos por calle Apóstol Santiago N° 18, comuna de Estación Central")
r = describir(T5, "calle Apóstol Santiago 32, departamento 2406", "calle Apóstol Santiago")
revisar("edificio con bodega y entradas por la misma calle (2093-2024)",
        r == "Edificio Eco Santiago. calle Apóstol Santiago 32, departamento 2406. Bodega 135", r)

# 4294-2025. Condominio de casas.
T6 = ("la vivienda número cuatro-A ubicada en Av. La Montaña N° 3.650, emplazada en el lote N° 4, del denominado “Condominio "
      "Laguna Norte Tres“, Comuna de Lampa, Región Metropolitana")
r = describir(T6, "Av. La Montaña 3650, vivienda 4-A", "Av. La Montaña")
revisar("condominio de casas (4294-2025)", r == "Condominio de casas Laguna Norte Tres. Av. La Montaña 3650, vivienda 4-A", r)

# 22035-2024. Condominio sin nombre y edificio con nombre.
T7 = "inmueble que corresponde al Departamento N° 311 del ‘Edificio Dolce II’, del Condominio ubicado con acceso por calle Amunátegui número 630- 646"
r = describir(T7, "calle Amunátegui 630- 646, Departamento N° 311", "calle Amunátegui")
revisar("condominio sin nombre con edificio con nombre (22035-2024)",
        r == "Condominio de departamentos, Edificio Dolce II. calle Amunátegui 630- 646, Departamento N° 311", r)

# Casos que deben quedar igual
T8 = "inmueble ubicado en calle La Viña N° 1544, de la comuna de Puente Alto, que corresponde al sitio 6 de la manzana c del plano de loteo"
revisar("sin condominio ni edificio queda igual", describir(T8, "calle La Viña 1544", "calle La Viña") == "calle La Viña 1544")
revisar("conjunto habitacional solo no cambia la dirección",
        describir("lote o sitio treinta y siete del Conjunto Habitacional Maestranza San Bernardo", "calle Ángel Mella 0246", "calle Ángel Mella") == "calle Ángel Mella 0246")
revisar("sin dirección no inventa nada", describir(T3, None, None) is None)

# Piezas sueltas
revisar("nombre que termina donde empieza el número", conjunto("Edificio Suárez Mujica N° 55, comuna")["nombre_edificio"] == "Suárez Mujica")
revisar("Edificio Cuatro es una parte, no un nombre", conjunto("del Edificio Cuatro, del conjunto")["nombre_edificio"] is None)
revisar("un año no es un estacionamiento", piezas("estacionamientos 2019 del registro", "estacionamiento") == [])
revisar("estacionamiento sin número no cuenta", piezas("con acceso a estacionamientos por calle X", "estacionamiento") == [])

# Revisión de los 289 cambios medidos en el PC (8 de Noviembre)
revisar("lista de estacionamientos con y (5010-2025)",
        piezas("estacionamientos 1 y 2 del primer subterráneo y estacionamiento 60 del segundo subterráneo", "estacionamiento") == ["1", "2", "60"])
revisar("un piso no es otro estacionamiento (3182-2026)", piezas("el Estacionamiento N° 63, 1° piso del mismo Condominio", "estacionamiento") == ["63"])
r = describir("estacionamiento 1 del piso 1, del ’Condominio Apóstol Santiago’, con acceso por Avenida José Manuel Balmaceda número 3751",
              "Avenida José Manuel Balmaceda 3751, estacionamiento 1", "Avenida José Manuel Balmaceda")
revisar("lo que ya es la unidad no se repite (7898-2024)", r == "Condominio Apóstol Santiago. Avenida José Manuel Balmaceda 3751, estacionamiento 1", r)
r = describir("departamento 807 del ‘Edificio Plaza Ceppi’, calle Uno 6590", "calle Uno 6590 y 6594, departamento 807", "calle Uno")
revisar("sin Edificio repetido (14985-2025)", conjunto("del Edificio ‘Edificio Plaza Ceppi’, calle")["nombre_edificio"] == "Edificio Plaza Ceppi"
        and describir("del Edificio ‘Edificio Plaza Ceppi’, calle Uno 6590", "calle Uno 6590, departamento 807", "calle Uno").startswith("Edificio Plaza Ceppi."), r)

# Unión con direccion.resolver. La calle comprobada viaja hasta edicion.
TT = "Departamento 504 del piso 5, con acceso peatonal por calle Carmen 660, Comuna de Santiago"
L = {"inmuebles": [{"tipo": "calle", "calle": "calle Carmen", "numero": "660", "unidad": None, "comuna": "Santiago",
                    "frase_direccion": "con acceso peatonal por calle Carmen 660", "frase_unidad": None, "frase_comuna": "Comuna de Santiago"}]}
rr = D.resolver([L, L], TT, 1)
revisar("resolver entrega la calle comprobada", rr["color"] == "verde" and rr["inmuebles"][0].get("calle") == "calle Carmen", rr)

print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} FALLAS {FALLAS}")
sys.exit(1 if FALLAS else 0)
