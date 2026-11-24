"""Prueba de la tasación de inciti (/get_appraisal) con la key de PRODUCCIÓN. COBRA cada respuesta 200.

Objetivo. Ver qué entrega la tasación y cuánto cobra. Solo 2 consultas, un departamento y una casa de la prueba de aciertos
del 24 de Noviembre, con el rol y los metros que devolvió la búsqueda. Sin estacionamientos ni bodegas (decisión de Diego).
Una sola llamada por caso, sin reintentos, porque cada respuesta exitosa se cobra.

Reglas. Lee solo INCITI_API_KEY_PRODUCCION de D:\\Mercurio\\config.py y nunca la imprime. Borra de lo que guarda todo dato de
propietarios (RUT, teléfonos, correos, nombres de personas) y anota solo en qué campo venían. No toca el robot.
Guarda en D:\\Mercurio\\INFORMES_REPORTES\\inciti_tasacion.

Uso, en PowerShell.  cd D:\\Mercurio\\Exploracion_tasacion   y luego   python prueba_inciti_tasacion.py
"""
import json, re, sys, time, urllib.request, urllib.error
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent          # D:\Mercurio
sys.path.insert(0, str(RAIZ))
try:
    import config
    KEY = getattr(config, "INCITI_API_KEY_PRODUCCION", None)
except Exception as e:
    print("No se pudo leer config.py:", type(e).__name__)
    sys.exit(1)
if not KEY or not str(KEY).strip():
    print("Falta INCITI_API_KEY_PRODUCCION en config.py. Agrégala y vuelve a correr.")
    sys.exit(1)
KEY = str(KEY).strip()

BASE = "https://api.inciti.com/api/"
SALIDA = RAIZ / "INFORMES_REPORTES" / "inciti_tasacion"
SALIDA.mkdir(parents=True, exist_ok=True)

CLAVE_SENSIBLE = re.compile(r"(?i)rut|dni|phone|tel[eé]fono|celular|email|e_mail|correo|mail|owner|propietari|contact|persona|apellido")
VALOR_RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b")
VALOR_MAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
VALOR_FONO = re.compile(r"(?:\+?56)?\s?9\s?\d{4}\s?\d{4}\b")


def limpiar(x, ruta, quitados):
    """Copia sin datos de personas. Devuelve la copia y anota en quitados la ruta de cada campo borrado."""
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            r = f"{ruta}.{k}"
            if CLAVE_SENSIBLE.search(str(k)):
                quitados.append(r)
                out[k] = "[BORRADO]"
            else:
                out[k] = limpiar(v, r, quitados)
        return out
    if isinstance(x, list):
        return [limpiar(v, f"{ruta}[{i}]", quitados) for i, v in enumerate(x)]
    if isinstance(x, str) and (VALOR_RUT.search(x) or VALOR_MAIL.search(x) or VALOR_FONO.search(x)):
        quitados.append(ruta)
        return "[BORRADO]"
    return x


def forma(x, ruta="", out=None):
    """Lista de rutas con su tipo, para ver la estructura sin leer los valores."""
    out = [] if out is None else out
    if isinstance(x, dict):
        for k, v in x.items():
            forma(v, f"{ruta}.{k}" if ruta else k, out)
    elif isinstance(x, list):
        out.append(f"{ruta}  (lista de {len(x)})")
        if x:
            forma(x[0], f"{ruta}[0]", out)
    else:
        out.append(f"{ruta}  ({type(x).__name__})")
    return out


CASOS = [
    ("1_depto_nataniel_cox_223_dp2007", {"rol": "490-279", "comunaCode": "13101", "propertyType": "departamento",
                                         "usefulSquareMeters": 29}),
    ("2_casa_pje_asturcon_1588", {"rol": "89-39", "comunaCode": "14158", "propertyType": "casa",
                                  "usefulSquareMeters": 131, "totalSquareMeters": 234}),
]

BUSCAR = ("propertyValueUF", "propertyValueCLP", "pdfUrl", "pdfError", "noData", "defaultValueUsed", "appraisalDate", "modelVersion")


def recoger(x, ruta="", out=None):
    out = [] if out is None else out
    if isinstance(x, dict):
        for k, v in x.items():
            r = f"{ruta}.{k}" if ruta else k
            if k in BUSCAR or ("uf" in k.lower() and not isinstance(v, (dict, list))):
                out.append(f"{r} = {v}")
            recoger(v, r, out)
    elif isinstance(x, list):
        out.append(f"{ruta}  (lista de {len(x)})") if ruta.endswith(("comparables", "sales", "listings", "cbrSales")) else None
        for i, v in enumerate(x[:1]):
            recoger(v, f"{ruta}[{i}]", out)
    return out


resumen = []
for nombre, cuerpo in CASOS:
    req = urllib.request.Request(BASE + "get_appraisal", data=json.dumps(cuerpo).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "X-API-Key": KEY})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            estado, texto = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        estado, texto = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        estado, texto = None, f"{type(e).__name__}: {str(e)[:200]}"
    seg = round(time.time() - t0, 1)
    try:
        datos = json.loads(texto)
    except Exception:
        datos = {"texto_no_json": texto[:2000]}
    quitados = []
    limpio = limpiar(datos, "$", quitados)
    (SALIDA / f"{nombre}.json").write_text(json.dumps({"enviado": cuerpo, "http": estado, "segundos": seg,
                                                      "campos_borrados": quitados, "respuesta": limpio},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
    resumen.append(f"== {nombre} | HTTP {estado} | {seg} s | campos de personas borrados {len(quitados)}")
    if isinstance(limpio, dict) and limpio.get("error"):
        resumen.append(f"   error {limpio.get('error')} {limpio.get('errorCode') or ''}")
    resumen += ["   " + f for f in recoger(limpio)[:40]]

(SALIDA / "RESUMEN.txt").write_text("\n".join(resumen), encoding="utf-8")
print("\n".join(resumen))
print(f"\nListo. Archivos en {SALIDA}")
