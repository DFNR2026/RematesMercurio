"""Ciclo 2 de mejora de la lectura, tanda 3 (9 de Noviembre de 2026). Carátulas y fojas. Sin internet y sin Haiku.
Correr desde la raíz del proyecto con. python -m pruebas.test_tanda3

Cada prueba usa el texto real que motivó el arreglo (banco en Storage_supabase/Banco_ciclo2/BANCO_CICLO2_CARATULA_FOJAS.md)
y hay casos que deben seguir igual.
"""
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.extraccion import inscripcion, caratula
from motor import filtros as F

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

def ins(t):
    return [(x["fojas"], x["numero"], x["anio"]) for x in inscripcion(t, "2026-11-09")["inscripcion"]]

def car(t):
    return caratula(t)["caratula"]["valor"]

# --- Fojas -----------------------------------------------------------------------------------------------------------
revisar("F1 Fs. con punto (4031-2021)", ins("inscrito a Fs. 73223 N° 104980 del Registro de Propiedad del año 2016 del Conservador de Bienes Raíces de Santiago.") == [("73223", "104980", "2016")])
revisar("F1 fs sin punto y el año al final (2170-2009)", ins("Inscrita a fs 2899 N° 2278 del Registro de Propiedad del Conservador de Bienes Raíces de Santiago, correspondiente al año 1998. Mínimo") == [("2899", "2278", "1998")])
revisar("F1 fs. pegado al número (4375-2024)", ins("a fs.78621 N° 119575 Registro Propiedad año 2012 Conservador Bienes Raíces Santiago.") == [("78621", "119575", "2012")])
revisar("F1 fjs (12304-2024)", ins("Inscrito a nombre del demandado a fjs 287 N° 100 año 2015 Registro Propiedad CBR Curanilahue año 2015. Mínimo") == [("287", "100", "2015")])
revisar("F2 f. (5337-2022)", ins("Conservador de Bienes Raíces de Yungay a f. 1.470 N° 1.415 del año 2011, cuyo rol") == [("1470", "1415", "2011")])
revisar("F3 números en plural (21712-2024)", ins("Conservador de Bienes Raíces de Santiago fojas 41.203 números 59.200 Registro de Propiedad del año 2017. Mínimo") == [("41203", "59200", "2017")])
revisar("F4 letra F pegada y N.° (9252-2022)", ins("inscrito a fojas 3334F N.° 2652 Registro Propiedad año 2018 Conservador Bienes Raíces de Villarrica. Mínimo") == [("3334", "2652", "2018")])
revisar("F4 letra F separada (4205-2026)", ins("inscrito a fojas 2504 F N° 2221, Registro Propiedad año 2010, Conservador Bienes Raíces Temuco. Mínimo") == [("2504", "2221", "2010")])
revisar("F7 Reg. Prop. no corta antes del año (188-2025)", ins("inscrito a fs. 63381 N° 61142 Reg. Prop. CBR Santiago año 2001. Mín. Posturas") == [("63381", "61142", "2001")])
revisar("sigue igual. fojas de siempre", ins("inscrito a fojas 57.106 N81.820 del Registro de Propiedad del año 2009") == [("57106", "81820", "2009")])
revisar("sigue igual. Hipotecas no cuenta como dominio (3227-2023)", ins("El derecho de usufructo se encuentra inscrito a Fs. 28164 N° 32312 del año 2021, del Registro de Hipotecas y Gravámenes del Conservador de Bienes Raíces de Santiago.") == [])
revisar("sigue igual. sin la palabra fojas no se adivina (2929-2025)", ins("inscrito a 49414 número 70690 correspondiente al Registro de Propiedad del año 2016") == [])
revisar("sigue igual. Fs. sin número de inscripción", ins("superficie de 120 m2 según Fs. 12 del expediente, rol de avalúo 123-4") == [])

# --- Carátulas -------------------------------------------------------------------------------------------------------
revisar("C8 rol sin guion (8102-2024)", car("Demás bases y antecedentes en juicio ejecutivo. Rol C8102-2024, Banco de Chile / Moris. Secretaría.") == "Banco de Chile / Moris")
revisar("C9 espacio antes del año y coma con remata (2357-2022)", car("PRIMER JUZGADO CIVIL DE VIÑA del Mar, Rol C-2357- 2022, Banco Crédito e Inversiones Con Andrades, remata el 02 de diciembre") == "Banco Crédito e Inversiones Con Andrades")
revisar("C10 expediente sin comillas (21824-2023)", car("Demás antecedentes en expediente Empresa Nacional de Energía Enex S.A. con Pizarro, Rol: C-21.824-2023. Juicio") == "Empresa Nacional de Energía Enex S.A. con Pizarro")
revisar("C3b comilla abierta y coma (5567-2024)", car("autos C-5567-2024, caratulados ‘Banco de Chile con Guzmán, remátese el 16 de diciembre de 2026") == "Banco de Chile con Guzmán")
revisar("C11 una comilla anterior no se come la carátula (11560-2013)", car("pdo ‘Mis Remates’ y del postor, a más tardar con 13 horas. Causa Rol C-11560-2013, caratulada ’CCAF Los Héroes/ Pozo’. Juicio") == "CCAF Los Héroes/ Pozo")
revisar("C12 carátula sola antes del rol (9252-2022)", car("por problemas de conexión. Avla S.A.G.R./Inversiones y Servicios Calafquen S.A. Rol C-9252-2022. Secretaria.") == "Avla S.A.G.R./Inversiones y Servicios Calafquen S.A")
revisar("C5b punto y coma en vez de comilla (2929-2025)", car("segundo piso, expediente; Banco Santander-Chile con Lobos’, Rol C-2929-2025. ejecutivo.") == "Banco Santander-Chile con Lobos")
revisar("C14 expediente cat. (17716-2024)", car("Huérfanos 1409 segundo piso, expediente cat. Administradora de Tarjetas S.A./Díaz, Rol C-17716-2024. Ejecutivo.") == "Cat. Administradora de Tarjetas S.A./Díaz")
revisar("C13 minúscula al inicio (11870-2025)", car("juicio caratulado ‘banco Santander Chile S.A/Bobadilla Bianco, Barbara Angelica y otro’. La Secretaria.") == "Banco Santander Chile S.A/Bobadilla Bianco, Barbara Angelica y otro")
revisar("sigue igual. carátula larga con S.A. adentro (17802-2023)", car("Ley Bancos caratulado ‘Fondo de Inversión Larraín Vial Deuda Privada con San Manuel S.A. Inversión y Desarrollo’. Se rematará") == "Fondo de Inversión Larraín Vial Deuda Privada con San Manuel S.A. Inversión y Desarrollo")
revisar("sigue igual. carátula incompleta del aviso queda vacía (188-2025)", car("23° JUZGADO CIVIL SANtiago, V-188-2025 “/O’Brien“. segundo remate 12 noviembre 2026") is None)
revisar("sigue igual. minúscula sin caratulado no se toma", car("con señalamiento ‘el rol de la causa con fecha’ y hora") is None)

# --- BancoEstado -----------------------------------------------------------------------------------------------------
def causa(texto, carat):
    return {"caratula": carat, "avisos": [{"texto": texto}]}
revisar("BE carátula sin con (11209-2023)", F._bancoestado_en_aviso(causa("Demás bases y antecedentes en causa rol C-11209-2023 ‘Banco del Estado de Chile Ramírez Monrroy Luis Antonio’.", None)))
revisar("BE sigue igual. cupón de pago no cuenta (1267-2019)", not F._bancoestado_en_aviso(causa("efectuado a través cupón de pago Banco Estado (no transferencia electrónica)", None)))
revisar("BE sigue igual. cuenta del tribunal no cuenta", not F._bancoestado_en_aviso(causa("mediante consignación en cuenta corriente 9733 Banco Estado del Tribunal.", None)))
revisar("BE Banco de Estado en la carátula", "banco de estado" in F._BANCOS_ESTADO)

print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} FALLAS {FALLAS}")
sys.exit(1 if FALLAS else 0)
