"""Tasación comercial con inciti (motor/tasacion.py, 24 de Noviembre de 2026). Sin internet y sin cobro. inciti se reemplaza
por respuestas grabadas. Incluye la repetición de la regla v2 sobre las 160 búsquedas reales del 24 de Noviembre.
Uso python pruebas/test_tasacion.py desde la raíz del proyecto."""
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.pop("INCITI_API_KEY", None)
os.environ.pop("TASACION_TOPE", None)
os.environ.pop("TASACION_APAGADA", None)

from motor import tasacion as T  # noqa: E402

T.ESPERA_BUSQUEDA = 0
fallas = 0


def revisar(nombre, condicion, detalle=""):
    global fallas
    if not condicion:
        fallas += 1
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)


class Falsa:
    """inciti de mentira. busquedas[(servicio, calle o rol)] = (estado, resultados). tasaciones = lista de (estado, datos)."""

    def __init__(self, busquedas=None, tasaciones=None):
        self.b = busquedas or {}
        self.t = list(tasaciones or [])
        self.busquedas = 0
        self.llamadas_tasar = []

    def buscar(self, servicio, cuerpo):
        self.busquedas += 1
        k = (servicio, cuerpo.get("rol") or cuerpo.get("street"))
        return self.b.get(k, (404, []))

    def tasar(self, cuerpo):
        self.llamadas_tasar.append(cuerpo)
        return self.t.pop(0) if self.t else (500, {})


def respuesta(uf, clp, pdf="https://ejemplo/informe.pdf"):
    return (200, {"ufValue": 41399.0, "pdfUrl": pdf, "valuation": {"sale": {"propertyValueUF": uf, "propertyValueCLP": clp}}})


def causa(rol, direccion, calle, comuna="Santiago", dir_ok=True, n=1, textos=None):
    props = [{"direccion": direccion, "calle": calle, "comuna": comuna, "dir_ok": dir_ok, "tipo": "calle"}] * n
    return {"rol": rol, "año": "2025", "tribunal": "1° Juzgado Civil de Santiago", "observaciones": "",
            "n_propiedades": n, "_tasar": props, "_textos": textos or ["REMATE ..."]}


DEP = {"rol": "490-279", "address": "NATANIEL COX 223 DP 2007", "useType": "HABITACIONAL", "util": 29, "total": 0,
       "comunaCode": "13101"}
tmp = Path(tempfile.mkdtemp())
MEM, RES = tmp / "tasaciones.csv", tmp / "hoy.json"
HOY = date(2026, 11, 25)

# --- Sin key no hace nada --------------------------------------------------------------------------------------------
c0 = causa("1", "calle Nataniel Cox 223, departamento 2007", "calle Nataniel Cox")
revisar("Sin key no tasa ni agrega columnas", T.tasar_causas([c0], archivo=MEM, resumen=RES) is None and "tas_uf" not in c0)
revisar("Sin key no crea la memoria", not MEM.exists())

# --- Lectura de la dirección del robot y del rol de avalúo -------------------------------------------------------------
p = T.partes_direccion({"direccion": "Avenida Vicuña Mackenna 4927, departamento 2605", "calle": "Avenida Vicuña Mackenna"})
revisar("Dirección con unidad", p == {"calle": "Avenida Vicuña Mackenna", "numero": "4927", "unidad": "departamento 2605"}, str(p))
p = T.partes_direccion({"direccion": "calle Las Acacias 02927", "calle": "calle Las Acacias"})
revisar("Dirección con cero inicial y sin unidad", p == {"calle": "calle Las Acacias", "numero": "02927", "unidad": None}, str(p))
p = T.partes_direccion({"direccion": "Edificio. calle Agustinas 1888, departamento 302 D, block D. Bodega 1",
                        "dir_base": "calle Agustinas 1888, departamento 302 D, block D", "calle": "calle Agustinas"})
revisar("Usa la dirección antes del formato de condominio y corta la unidad en la coma",
        p == {"calle": "calle Agustinas", "numero": "1888", "unidad": "departamento 302 D"}, str(p))
revisar("Calle sin número no se busca", T.partes_direccion({"direccion": "Pasaje Uno s/n", "calle": "Pasaje Uno"}) is None)
revisar("Rol de avalúo impreso", T.rol_avaluo(["... rol de avalúo N° 533-358 de la comuna ..."]) == "533-358")
revisar("Dos roles de avalúo distintos no se usan", T.rol_avaluo(["rol de avalúo 1-2", "rol de avaluo 3-4"]) is None)
revisar("Sin rol de avalúo", T.rol_avaluo(["ROL C-1234-2024"]) is None)
revisar("Códigos de comuna (Santiago, Ñuñoa, Tiltil, Buin)",
        [T.codigo_comuna(x) for x in ("Santiago", "Ñuñoa", "Til Til", "Buín")] == ["13101", "15105", "14203", "16403"])

# --- Con inciti de mentira -------------------------------------------------------------------------------------------
api = Falsa({("get_results_by_address", "Nataniel Cox"): (200, [DEP])}, [respuesta(7160.45, 296432383)])
c1 = causa("10", "calle Nataniel Cox 223, departamento 2007", "calle Nataniel Cox")
r = T.tasar_causas([c1], api=api, hoy=HOY, archivo=MEM, resumen=RES)
revisar("Departamento tasado con valor en UF, pesos e informe",
        c1["tas_uf"] == 7160.45 and c1["tas_clp"] == 296432383 and c1["tas_link"] == "https://ejemplo/informe.pdf", str(c1))
revisar("Pide la tasación con rol, comuna, tipo y metros", api.llamadas_tasar == [
    {"rol": "490-279", "comunaCode": "13101", "propertyType": "departamento", "usefulSquareMeters": 29}], str(api.llamadas_tasar))
mem = T.leer_memoria(MEM)
revisar("La memoria guarda una fila tasada y cobrada", len(mem) == 1 and mem[0]["resultado"] == "tasada" and mem[0]["cobrada"] == "si", str(mem))
revisar("La memoria solo trae los campos del diseño (sin datos de personas)", list(mem[0].keys()) == T.CAMPOS)
revisar("Resumen del día con 1 pagada", r["pagadas_hoy"] == 1 and json.loads(RES.read_text(encoding="utf-8"))["mes_total"] == 1)

api = Falsa({("get_results_by_address", "Nataniel Cox"): (200, [DEP])}, [respuesta(1, 1)])
c2 = causa("10", "calle Nataniel Cox 223, departamento 2007", "calle Nataniel Cox")
T.tasar_causas([c2], api=api, hoy=date(2026, 12, 2), archivo=MEM, resumen=RES)
revisar("La misma causa no se paga dos veces", not api.llamadas_tasar and c2["tas_uf"] == 7160.45 and not c2["tas_amarilla"])
revisar("Observación de tasación reutilizada", c2["observaciones"] == "Tasada el 25 de noviembre del 2026 (ver informe).", c2["observaciones"])

api = Falsa({("get_results_by_address", "Nataniel Cox"): (200, [DEP])}, [respuesta(1, 1)])
c3 = causa("99", "calle Nataniel Cox 223, departamento 2007", "calle Nataniel Cox")
T.tasar_causas([c3], api=api, hoy=date(2026, 12, 2), archivo=MEM, resumen=RES)
revisar("Otra causa con la misma propiedad (mismo rol de avalúo) tampoco se paga", not api.llamadas_tasar and c3["tas_uf"] == 7160.45)

api = Falsa({("get_results_by_address", "Nataniel Cox"): (200, [DEP])}, [respuesta(1, 1)])
c4 = causa("10", "calle Nataniel Cox 223, departamento 2007", "calle Nataniel Cox")
T.tasar_causas([c4], api=api, hoy=date(2027, 6, 26), archivo=MEM, resumen=RES)
revisar("Con más de 6 meses no se vuelve a tasar, va en amarillo", not api.llamadas_tasar and c4["tas_amarilla"] and c4["tas_uf"] == 7160.45)
revisar("Observación con la antigüedad", c4["observaciones"] ==
        "Esta propiedad se tasó el 25 de noviembre del 2026, hace 7 meses. Se recomienda volver a valorizarla.", c4["observaciones"])

CASA = {"rol": "89-39", "address": "PJ ASTURCON 1588", "useType": "HABITACIONAL", "util": 131, "total": 234, "comunaCode": "14158"}
api = Falsa({("get_results_by_address", "Asturcon"): (200, [CASA])}, [(404, {"error": "sin comparables"})])
c5 = causa("20", "Pasaje Asturcon 1588", "Pasaje Asturcon", comuna="Huechuraba")
T.tasar_causas([c5], api=api, hoy=HOY, archivo=MEM, resumen=RES)
revisar("Casa sin ventas parecidas (404, no se cobra)", c5["tas_uf"] == T.T_SIN_COMPARABLES and c5["tas_clp"] is None)
revisar("La casa pide también los metros de terreno", api.llamadas_tasar[0].get("totalSquareMeters") == 234 and
        api.llamadas_tasar[0]["propertyType"] == "casa", str(api.llamadas_tasar))
revisar("El 404 queda en la memoria como no cobrado", T.leer_memoria(MEM)[-1]["cobrada"] == "no")

api = Falsa({("get_results_by_address", "Asturcon"): (200, [dict(CASA, rol="89-40")])}, [(500, {})])
c6 = causa("21", "Pasaje Asturcon 1588", "Pasaje Asturcon", comuna="Huechuraba")
T.tasar_causas([c6], api=api, hoy=HOY, archivo=MEM, resumen=RES)
revisar("Falla de inciti en la tasación", c6["tas_uf"] == T.T_FALLA)

api = Falsa()
c7 = causa("30", "calle Apoquindo 3000", "calle Apoquindo", comuna="Las Condes")
c8 = causa("31", "calle Uno 1", "calle Uno", n=2)
c9 = causa("32", "calle Uno 1", "calle Uno", dir_ok=False)
T.tasar_causas([c7, c8, c9], api=api, hoy=HOY, archivo=MEM, resumen=RES)
revisar("Las Condes no se tasa", c7["tas_uf"] == T.T_COMUNA)
revisar("Más de 1 propiedad", c8["tas_uf"] == T.T_VARIAS)
revisar("Dirección no comprobada", c9["tas_uf"] == T.T_DIRECCION)
revisar("Esos tres casos no buscan ni tasan", api.busquedas == 0 and not api.llamadas_tasar)

LOCAL = {"rol": "5-5", "address": "CALLE DOS 10", "useType": "COMERCIO", "util": 50, "total": 80, "comunaCode": "13101"}
api = Falsa({("get_results_by_address", "Dos"): (200, [LOCAL])})
c10 = causa("40", "calle Dos 10", "calle Dos")
T.tasar_causas([c10], api=api, hoy=HOY, archivo=MEM, resumen=RES)
revisar("Lo que calza es comercio, no es casa ni departamento", c10["tas_uf"] == T.T_NO_HAB and not api.llamadas_tasar)

api = Falsa({("get_results_by_rol", "533-358"): (200, [dict(DEP, rol="533-358", address="ARTURO PRAT 318 338 DP 1809")])},
            [respuesta(3000, 124000000)])
c11 = causa("50", "calle Arturo Prat 324, departamento 1809", "calle Arturo Prat",
            textos=["... rol de avalúo N° 533-358 ..."])
T.tasar_causas([c11], api=api, hoy=HOY, archivo=MEM, resumen=RES)
revisar("Con rol de avalúo impreso busca por rol (Arturo Prat 324)", c11["tas_uf"] == 3000 and api.llamadas_tasar[0]["rol"] == "533-358")

api = Falsa({("get_results_by_address", "Tres"): (None, [])})
c12 = causa("60", "calle Tres 5", "calle Tres")
T.tasar_causas([c12], api=api, hoy=HOY, archivo=MEM, resumen=RES)
revisar("Si inciti no responde la búsqueda, falla del servicio", c12["tas_uf"] == T.T_FALLA)

os.environ["TASACION_TOPE"] = "1"
api = Falsa({("get_results_by_address", "Cuatro"): (200, [dict(DEP, rol="7-1", address="CUATRO 1")]),
             ("get_results_by_address", "Cinco"): (200, [dict(DEP, rol="7-2", address="CINCO 2")])},
            [respuesta(10, 10), respuesta(20, 20)])
c13, c14 = causa("70", "calle Cuatro 1", "calle Cuatro"), causa("71", "calle Cinco 2", "calle Cinco")
r = T.tasar_causas([c13, c14], api=api, hoy=HOY, archivo=MEM, resumen=RES)
revisar("Tope de tasaciones por corrida", c13["tas_uf"] == 10 and c14["tas_uf"] == T.T_TOPE and r["tope_alcanzado"]
        and len(api.llamadas_tasar) == 1)
os.environ.pop("TASACION_TOPE")

os.environ["TASACION_APAGADA"] = "1"
api = Falsa()
c15 = causa("80", "calle Seis 1", "calle Seis")
T.tasar_causas([c15], api=api, hoy=HOY, archivo=MEM, resumen=RES)
revisar("Sin memoria de tasaciones no se tasa", c15["tas_uf"] == T.T_FALLA and api.busquedas == 0)
os.environ.pop("TASACION_APAGADA")

# --- Texto del correo de Diego ---------------------------------------------------------------------------------------
lin = T.texto_correo({"fecha": "2026-11-25", "pagadas_hoy": 6, "mes_total": 30, "uf_usada": 41399.0})
revisar("Correo con cobro aparte", lin[0] == "Hoy se hicieron 6 tasaciones. En noviembre van 30. Las primeras 27 del mes "
        "entran en la base del plan y hoy 3 se cobran aparte. Costo de hoy 3 × 0,0371 = 0,11 UF más IVA, unos $5.500.", lin[0])
revisar("Correo con el total aparte del mes", lin[1] == "En noviembre se cobran aparte 3 tasaciones, 0,11 UF más IVA, unos $5.500.", lin[1])
lin = T.texto_correo({"fecha": "2026-11-25", "pagadas_hoy": 6, "mes_total": 10, "uf_usada": 41399.0})
revisar("Correo dentro de la base del plan", lin == ["Hoy se hicieron 6 tasaciones. En noviembre van 10. Todas las de hoy entran "
                                                     "en la base de 27 del plan, así que hoy no hay cobro aparte."], str(lin))

# --- La regla v2 sobre las búsquedas reales del 24 de Noviembre de 2026 (sin internet) -------------------------------
datos = json.loads((RAIZ / "pruebas" / "datos_tasacion" / "regla_v2_24nov.json").read_text(encoding="utf-8"))
distintos = []
for f in datos:
    x, como = T.elegir_v2(f["candidatos"], f)
    if como != f["como"] or (x or {}).get("rol") != f["rol"]:
        distintos.append((f["causa"], como, f["como"]))
revisar(f"La regla del robot da lo mismo que la corrida v2 en los {len(datos)} casos con búsqueda", not distintos, str(distintos[:5]))

# --- Excel ------------------------------------------------------------------------------------------------------------
import openpyxl  # noqa: E402
import modulo5_reporte as M5  # noqa: E402

base = {"rol": "1", "año": "2025", "corte": "C.A. de Santiago", "tribunal": "1° Juzgado Civil de Santiago", "demandante": "Banco",
        "demandado": "Pérez", "direccion": "calle Uno 1", "comuna": "Santiago", "fojas": "1", "observaciones": ""}
M5.REPORTES_DIR = str(tmp)
ruta = M5.generar_reporte([dict(base)], metricas={"ediciones": ["2026-11-25"]})
ws = openpyxl.load_workbook(ruta)["Remates"]
cab = [c.value for c in ws[1]]
revisar("Sin tasación el Excel tiene las columnas de siempre",
        cab == ["ROL", "Año", "Corte", "Tribunal", "Demandante", "Demandado", "Dirección", "Comuna", "Fs.", "Observaciones"], str(cab))
con = [dict(base, tas_uf=7160.45, tas_clp=296432383, tas_link="https://ejemplo/informe.pdf", tas_amarilla=False),
       dict(base, rol="2", tas_uf=T.T_NO_ENCONTRADA, tas_clp=None, tas_link=None, tas_amarilla=False),
       dict(base, rol="3", tas_uf=100.5, tas_clp=4000000, tas_link=None, tas_amarilla=True)]
ruta = M5.generar_reporte(con, metricas={"ediciones": ["2026-11-26"]})
ws = openpyxl.load_workbook(ruta)["Remates"]
cab = [c.value for c in ws[1]]
revisar("Con tasación van las tres columnas entre Fs. y Observaciones",
        cab[8:] == ["Fs.", "Valor venta UF", "Valor venta $", "Informe", "Observaciones"], str(cab))
fila = {ws.cell(row=i, column=1).value: i for i in range(2, 5)}
revisar("El valor va como número con formato", ws.cell(row=fila["1"], column=10).value == 7160.45
        and ws.cell(row=fila["1"], column=10).number_format == "#,##0.00")
revisar("El informe es un enlace que dice Ver informe", ws.cell(row=fila["1"], column=12).value == "Ver informe"
        and ws.cell(row=fila["1"], column=12).hyperlink.target == "https://ejemplo/informe.pdf")
revisar("El texto va en la celda del valor", ws.cell(row=fila["2"], column=10).value == "Tasación no encontrada")
revisar("Más de 6 meses en amarillo", ws.cell(row=fila["3"], column=10).fill.fgColor.rgb.endswith("FFFF00")
        and ws.cell(row=fila["3"], column=11).fill.fgColor.rgb.endswith("FFFF00"))
revisar("El filtro cubre las 13 columnas", ws.auto_filter.ref.startswith("A1:M"), ws.auto_filter.ref)

# --- servidor/diario.py. Memoria de tasaciones en Supabase y correo de Diego (Supabase y Gmail de mentira) -----------
os.environ.setdefault("CORREO_DIEGO", "diego@ejemplo")
from servidor import diario as D  # noqa: E402

nube, subidas, correos = {}, [], []
D.E.existe = lambda remoto: remoto in nube
D.E.bajar = lambda remoto, local: Path(local).write_bytes(nube[remoto])
D.E.subir = lambda local, remoto, tipo="": (subidas.append(remoto), nube.__setitem__(remoto, Path(local).read_bytes()))
D.enviar = lambda para, asunto, cuerpo, adjuntos=None, html=None: correos.append((para, asunto, cuerpo, html))
try:
    nube["estado/tasaciones.csv"] = "fecha,causa\n2026-11-24,1\n".encode("utf-8")
    revisar("Baja la memoria de tasaciones", D.bajar_tasaciones() and D.TASACIONES.read_bytes() == nube["estado/tasaciones.csv"])
    D.subir_tasaciones()
    revisar("Sin cambios no sube nada", subidas == [])
    with open(D.TASACIONES, "a", encoding="utf-8") as f:
        f.write("2026-11-25,2\n")
    D.subir_tasaciones()
    revisar("Con cambios sube la memoria con respaldo de la anterior", len(subidas) == 2 and subidas[0].startswith(f"{D.P}respaldos/tasaciones_antes_")
            and subidas[1] == f"{D.P}estado/tasaciones.csv", str(subidas))
    D.E.existe = lambda remoto: (_ for _ in ()).throw(RuntimeError("caída"))
    revisar("Si no se puede bajar, ese intento no tasa", D.bajar_tasaciones() is False)
    D.TAS_RESUMEN.write_text(json.dumps({"fecha": "2026-11-25", "pagadas_hoy": 6, "mes_total": 30, "uf_usada": 41399.0}), encoding="utf-8")
    D.correo_tasaciones()
    revisar("Correo de tasaciones solo a Diego, con negrita", len(correos) == 1 and correos[0][0] == ["diego@ejemplo"]
            and "<b>Hoy se hicieron 6 tasaciones." in correos[0][3] and "unos $5.500" in correos[0][2], str(correos[:1]))
finally:
    for f in (D.TASACIONES, D.TAS_ANTES, D.TAS_RESUMEN):
        if f.exists():
            f.unlink()

print()
print("RESULTADO.", "TODO OK" if not fallas else f"{fallas} FALLAS")
sys.exit(1 if fallas else 0)
