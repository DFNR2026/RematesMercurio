"""Parte 3.7c. Prueba de la carátula leída por código (motor/extraccion.py, caratula), sin internet.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_caratula
1. El 14 de Octubre (banco de AJUSTE) da 57 aciertos de 57.
2. Casos hechos a mano, uno por regla.
"""
import io, contextlib, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.extraccion import caratula, clave_caratula
import pruebas.medir_caratula as M

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

buf = io.StringIO(); sys.argv = ["x", "14"]
with contextlib.redirect_stdout(buf): M.main()
primera = buf.getvalue().splitlines()[0]
revisar("14-10. 57 aciertos de 57 (ajuste con 3 arreglos)", primera.endswith("Por aviso. acierto 57."), primera)

v = lambda t: caratula(t)["caratula"]["valor"]
tipo = lambda t: (caratula(t)["alertas"] or [("", "")])[0][0]
revisar("entre comillas tras caratulado", v("antecedentes juicio caratulado ‘Banco de Chile con Aguilera’, Rol C-1-2020.") == "Banco de Chile con Aguilera")
revisar("comilla de cierre como apertura (’Barrera con López’)", v("Rit C-3908-2025, Ruc 25-4-0645112-K, ’Barrera con López’, 12/11/2026") == "Barrera con López")
revisar("sin comillas, Caratulado con mayúscula y punto final",
        v("ver autos Causa Rol: C-2462-2022 Caratulado: Banco de Crédito e Inversiones/Pérez. El Secretario.") == "Banco de Crédito e Inversiones/Pérez")
revisar("sin comillas, termina en ', Juicio'", v("Rol C-9314-2025, Caratulados CAT Administradora de Tarjetas S.A./ Moreno, Juicio Ejecutivo.") == "CAT Administradora de Tarjetas S.A./ Moreno")
revisar("forma 'causa X/ Y, juicio' con S.A.", v("468-2025, causa Banco Itaú Chile S.A./ Rubilar, juicio ejecutivo, se rematará") == "Banco Itaú Chile S.A./ Rubilar")
revisar("S.A. Con dentro de las comillas", v("antecedentes causa “Bice Vida Compañía de Seguros S.A. Con Quiroga Brant“, Rol") == "Bice Vida Compañía de Seguros S.A. Con Quiroga Brant")
T_FALSO = ("en el módulo ‘Audiencia de remates’ dispuesto para tal efecto. Una vez que el postor ha sido aceptado, con su clave única, en el módulo "
           "‘Mis Remates’ deberá entregar. Antecedentes juicio caratulado ‘Banco Internacional con Ce Inmobiliaria III S.A.’, Rol C-1-2024.")
revisar("no toma el texto entre dos términos entre comillas", v(T_FALSO) == "Banco Internacional con Ce Inmobiliaria III S.A.", str(v(T_FALSO)))
# Caso inventado (17 de Octubre). El primero que se escribió venía del 06-10 aviso 68, que es de la VALIDACIÓN, y se cambió.
revisar("la misma carátula con S.A. y sin S.A., o con Ltda y Limitada, cuenta como una (decisión de Diego)",
        v("Causa Rol 1-2016, ‘Banco Uno S.A. con Inversiones Dos Ltda’, el 11 de noviembre. Antecedentes en autos ‘Banco Uno con Inversiones Dos Limitada’.")
        == "Banco Uno S.A. con Inversiones Dos Ltda")
T2 = "juicio ejecutivo ‘Banco Santander-Chile con Gatica’ Rol C-1-2025. Secretaría. EXTRACTO. en causa V-101-2025, ’Charad/ Charad’ por resolución"
revisar("'Cía. Ltda' dentro de la carátula no corta (06-10 aviso 68, arreglo aprobado por Diego)",
        v("Causa Rol N° 25.063-2016, ‘Banco de Chile con Comercial Tapia y Cía. Ltda’, el 11 de noviembre") == "Banco de Chile con Comercial Tapia y Cía. Ltda")
revisar("dos carátulas distintas, duda de lectura sin elegir (decisión de Diego)", v(T2) is None and tipo(T2) == "revisar_lectura", str(caratula(T2)["alertas"])[:150])
revisar("sin carátula, dato faltante", v("REMATE. Demás bases y antecedentes en Tribunal. El secretario.") is None and tipo("Demás bases y antecedentes en Tribunal.") == "dato_faltante")
revisar("clave sin tildes, puntuación ni sufijos", clave_caratula("Scotiabank Chile S.A./Gil") == clave_caratula("scotiabank chile con gil"))
revisar("el texto de las alertas no usa dos puntos ni punto y coma", not any(c in caratula(T2)["alertas"][0][1].split("(")[0] for c in ":;"))
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)
