"""Ciclo 2 de mejora de la lectura, tanda 7 (14 de Noviembre de 2026). Juzgados de Policía Local eliminados (PL1),
tribunal "JUZGADO DE CIVIL" (G4) y sin la palabra Juzgado (G5), inscripción toda en palabras (F11) y dos mínimos con
lotes "I.-" y "II.-" (M1). Sin internet y sin IA. Uso python pruebas/test_tanda7.py desde la raíz del proyecto."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.extraccion import tribunal, inscripcion, minimo_y_costas
from motor.edicion import procesar

fallas = 0


def revisar(nombre, condicion, detalle=""):
    global fallas
    if not condicion:
        fallas += 1
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)


T = lambda t: tribunal(t)["tribunal"]["valor"]

# --- G4 y G5. Formas del tribunal ----------------------------------------------------------------------------------
revisar("G4 18° JUZGADO DE CIVIL DE Santiago (3127-2024)", T("REMATE: 18° JUZGADO DE CIVIL DE Santiago, ubicado en calle Huérfanos N° 1409, en causa Rol C-3127-2024") == "18° Juzgado Civil de Santiago")
revisar("G4 Juzgado de Letras de Colina sigue igual", T("REMATE. JUZGADO DE LETRAS DE COLINA, causa Rol C-100-2024") == "Juzgado de Letras de Colina", T("REMATE. JUZGADO DE LETRAS DE COLINA, causa Rol C-100-2024"))
revisar("G4 7° Juzgado Civil de Santiago sigue igual", T("REMATE: 7° JUZGADO CIVIL DE Santiago, Huérfanos 1409") == "7° Juzgado Civil de Santiago")
revisar("G5 DÉCIMO SÉPTIMO CIVIL de Santiago (1455-2023)", T("REMATE: DÉCIMO SÉPTIMO CIVIL de Santiago, Huérfanos N° 1409, 4° Piso, en causa Rol C-1455-2023") == "17° Juzgado Civil de Santiago")
revisar("G5 17° CIVIL DE SANTIAGO en cifras", T("REMATE. 17° CIVIL DE Santiago, Huérfanos 1409, causa C-1-2020") == "17° Juzgado Civil de Santiago")
revisar("G5 no lee 'civil' en medio del aviso", T("REMATE. Se rematará el inmueble, juicio ejecutivo y civil de cobro, " + "x " * 220) is None)
revisar("G5 el tribunal normal manda", T("REMATE: 5° JUZGADO CIVIL DE Santiago, rematará") == "5° Juzgado Civil de Santiago")

# --- F11. Inscripción toda en palabras ----------------------------------------------------------------------------
_t7170 = 'REMATE: DÉCIMO TERCER JUZgado Civil De Santiago, Huérfanos 1409 cuarto piso, expediente ‘Metlife Chile Seguros De Vida S.A. Con Bahamonde Klein, Cristian Adolfo’, Rol: C-7170-2026. Juicio Hipotecario Ley de Bancos. Se rematará 03 de diciembre de 2026 a las 13:15 horas, vía plataforma zoom, el departamento número dos mil doscientos seis del vigésimo segundo piso; el estacionamiento número sesenta y nueve del subterráneo y la bodega número treinta y nueve del subterráneo, todos del edificio ‘Parque de Los Reyes’, ubicado en Avenida Presidente Balmaceda número dos mil novecientos catorce y calle esperanza número mil quinientos setenta y seis, comuna de Santiago, Región Metropolitana, y derechos en proporción al valor de lo adquirido en unión de los otros adquirentes en los bienes comunes entre los cuales se encuentra el terreno, inscritos a fojas cinco mil noventa y dos número siete mil cuatrocientos ochenta y cuatro; a fojas cinco mil noventa y cuatro número siete mil cuatrocientos ochenta y seis y a fojas cinco mil noventa y tres número siete mil cuatrocientos ochenta y cinco, todas del registro de propiedad del Conservador de Bienes Raíces de Santiago del año dos mil veintiuno. Mínimo: será la suma equivalente al día del remate a 2.223,1370 unidades de fomento más la suma de $ 477.900.- por concepto de costas personales y procesales. El plazo para consignar el saldo de precio es al quinto día habil de efectuada la subasta. La subasta se realizará por video conferencia, mediante la plataforma zoom. Todo interesado para presenciar y/o participar en el mismo, deberá coordinarse al correo jcsantiago13_remates @pjud.cl. Por lo cual se requiere de un computador o teléfono, en ambos casos con cámara, micrófono y audio del mismo equipo y conexión a internet, siendo carga de las partes y postores el tener los elementos teconológicos y de conexión. Los interesados deben rendir la garantía equivalente al 10% del mínimo fijado, mediante vale vista a nombre del Décimo Tercer Juzgado Civil De Santiago, Rut N° 60.306.013-k, hasta las 12:00 horas del día hábil anterior a la fecha fijada para el remate, garantía que se imputará al precio del remate, o se hará efectiva en la forma legal. Para los efectos de constitución de la garantía suficiente, se deja establecido que los postores deberán comparecer al tribunal el día hábil anterior al día de la subasta, esto es, el día lunes anterior al día del remate y en su caso, el día miércoles anterior al día del remate, ello desde las 11:00 horas y hasta las 14:00 horas, a fin de hacer entrega en secretaría del respectivo vale vista a nombre del Décimo Tercer Juzgado Civil de Santiago, Rut N° 60.306.013-k. Los postores, a más tardar a las 14:00 horas del día hábil anterior a la realización de la subasta, deberán enviar un correo electrónico a jcsantiago13_remates @pjud.cl, indicando en el asunto ‘Remate’, con señalamiento del rol de la causa y la fecha de realización, a fin de coordinar su participación, así como para obtener información respecto al protocolo para la realización de la subasta y recibir el link con la invitación a la misma. Demás bases y antecedentes causa Rol N° C-7170-2026. La Secretaria.'
_i = inscripcion(_t7170, "2026-11-13")["inscripcion"]
revisar("F11 tres inscripciones en palabras con su año (7170-2026)",
        [(x["fojas"], x["numero"], x["anio"]) for x in _i] == [("5092", "7484", "2021"), ("5094", "7486", "2021"), ("5093", "7485", "2021")], str(_i))
_mixto = "inscrito a fojas 1234 número 5678 del año 2010. El otro inmueble a fojas cinco mil número seis mil del año dos mil veinte."
revisar("F11 si ya se leyó una en cifras, no se tocan las de palabras", [(x["fojas"], x["anio"]) for x in inscripcion(_mixto)["inscripcion"]] == [("1234", "2010")])
revisar("F11 un aviso sin inscripción sigue sin inscripción", inscripcion("REMATE. Mínimo $ 10.000.000. La propiedad de calle Uno.")["inscripcion"] == [])

# --- M1. Dos mínimos con lotes I.- y II.- -------------------------------------------------------------------------
_t28 = 'EXTRACTO REMATE. ANTE EL 2° Juzgado de Letras de San Fernando, en causa cobranza laboral Rit C-28-2025, ’Villar con Eco Limp SpA’, se rematará el día 5 de noviembre de 2026 a las 13:00 horas, a través de videoconferencia a realizarse por intermedio de la plataforma Zoom y de acuerdo a las bases aprobadas con fecha 16/12/2025: I.- Propiedades Ubicadas En La Comuna De Conchalí, Región Metropolitana Que Deslindan: A) Propiedad ubicada en calle Pedro Fontova, que corresponde al sitio número cinco del sector número uno del plano de loteo del Fundo La Palmilla; B) Inmueble ubicado en Avenida Pedro Fontova número tres mil setecientos veintiséis, que corresponde al sitio número cuatro, sector número uno del plano de loteo del Fundo La Palmilla. El título de dominio de ambas propiedades se encuentra inscrito a nombre de la ejecutada, Eco Limp Ltda, a fojas 3247 número 4790 correspondiente al Registro de Propiedad del año 2021 del Conservador de Bienes Raíces de Santiago del año dos mil veintiuno, Rol de avalúo número 2319-6, Comuna de Conchalí. Mínimo de las posturas: $ 159.164.537. II.- Oficina número mil uno de la unidad ’La Torre’ del Edificio Condomio YMCA, ubicado en calle Compañía número mil trescientos noventa, comuna de Santiago, Región Metropolitana y derechos en proporción al valor adquirido en unión de los otros adquirentes en los bienes comunes entre los cuales se encuentra el terreno, el título de dominio se encuentra inscrito a fojas 78307 número 118871 correspondiente al Registro de Propiedad del año 2011, del Conservador de Bienes Raíces de Santiago. Mínimo de las posturas: $ 100.285.662. Los interesados en participar en la subasta, deberán tener activa su clave única del estado para efectos de suscribir la correspondiente acta de remate y deberán consignar garantía suficiente para participar de la subasta conforme a las bases de remate, mediante cupón de pago del Banco Estado obtenido desde el portal www.pjud.cl, en la causa correspondiente. Dicho comprobante deberá ser remitido al correo electrónico jl2_sanfernando_remates@pjud.cl junto con la copia digitalizada de la cédula de identidad, señalando el Rol de la causa, nombre completo del postor, correo electrónico y teléfono, todo hasta las 14:00 horas del día anterior a la fecha fijada para el remate, no se aceptará otro modo de consignación o comprobante de garantía a la ya indicada, tales como transferencia electrónica, vale vista, entre otros. Enlace Zoom para remate: https://zoom.us/j/ 2616659749? pwd=MFljK0Zkd2VEQ kp6eUc3NDB4ckFIQT0 ID de reunión: 261 665 9749 Código de acceso: 212121. Bases y demás antecedentes en la causa. Vanessa Olivia Manríquez Maulén.'
_m = minimo_y_costas(_t28)["minimo"]
revisar("M1 dos remates con sus mínimos (28-2025)", [(d["inmueble"], d["monto"]) for d in _m.get("lista") or []] == [("lote I", 159164537.0), ("lote II", 100285662.0)], str(_m))
revisar("M1 un solo mínimo sigue siendo uno", minimo_y_costas("I.- Casa en calle Uno 1. Mínimo $ 50.000.000. Lo demás.")["minimo"].get("monto") == 50000000.0)
revisar("M1 dos mínimos sin lote siguen sin asignarse",
        minimo_y_costas("Mínimo para la subasta $ 10.000.000 y otro mínimo de $ 20.000.000 por el resto.")["minimo"].get("monto") is None)

# --- PL1. Juzgado de Policía Local eliminado ----------------------------------------------------------------------
from motor.edicion import paginas_desde_captura
_raiz = Path(__file__).resolve().parent.parent
_r = procesar(paginas_desde_captura(_raiz / "banco_pruebas" / "2026-10-09")[0], "2026-10-09", cliente=None)
revisar("PL1 el remate del 2° Juzgado de Policía Local de Pudahuel queda eliminado (banco del 9 de Octubre)",
        len(_r.get("policia_local") or []) == 1, str(_r.get("policia_local")))
revisar("PL1 ningún aviso que queda es de Policía Local",
        not any("Policía Local" in (a.get("tribunal") or "") for a in _r["sin_rol"])
        and not any("Policía Local" in (c.get("tribunal") or "") for c in _r["causas"]))
revisar("PL1 las demás causas del día siguen", len(_r["causas"]) > 50, str(len(_r["causas"])))

print()
print("RESULTADO.", "TODO OK" if not fallas else f"{fallas} FALLAS")
sys.exit(1 if fallas else 0)
