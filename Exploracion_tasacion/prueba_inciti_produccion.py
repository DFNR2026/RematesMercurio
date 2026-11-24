"""Prueba mínima de la búsqueda por dirección de inciti con la key de PRODUCCIÓN (puede cobrar).

Objetivo. Ver qué trae la respuesta de get_results_by_address y si encuentra el rol correcto. Usa dos avisos del Excel del
14 de Noviembre que imprimen su rol de avalúo, así se sabe la respuesta correcta. Solo 2 consultas, solo búsqueda por
dirección. No llama a /get_property_data ni a /get_appraisal.

Reglas. Lee solo INCITI_API_KEY_PRODUCCION de D:\\Mercurio\\config.py y nunca la imprime. Borra de lo que guarda todo dato de
propietarios (RUT, teléfonos, correos, nombres de personas) y anota solo en qué campo venían. No toca el robot.
Guarda en D:\\Mercurio\\INFORMES_REPORTES\\inciti_produccion.

Uso, en PowerShell.  cd D:\\Mercurio\\Exploracion_tasacion   y luego   python prueba_inciti_produccion.py
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

BASE = "https://api.inciti.com/api/searchengine/"
SALIDA = RAIZ / "INFORMES_REPORTES" / "inciti_produccion"
SALIDA.mkdir(parents=True, exist_ok=True)

CASOS = [
    ("1_santo_domingo_1161_d808", "get_results_by_address",
     {"street": "Santo Domingo", "streetNumber": "1161", "comunaCode": "13101", "unitNumber": "808"}, ("210", "636")),
    ("2_arturo_prat_324_d1809", "get_results_by_address",
     {"street": "Arturo Prat", "streetNumber": "324", "comunaCode": "13101", "unitNumber": "1809"}, ("533", "358")),
]

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


resumen = []
crudos_limpios = {}
for nombre, servicio, cuerpo, esperado in CASOS:
    req = urllib.request.Request(BASE + servicio, data=json.dumps(cuerpo).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "X-API-Key": KEY})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
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
    crudos_limpios[nombre] = limpio
    (SALIDA / f"{nombre}.json").write_text(json.dumps({"servicio": servicio, "enviado": cuerpo, "http": estado,
                                                      "segundos": seg, "campos_borrados": quitados,
                                                      "respuesta": limpio}, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    plano = json.dumps(limpio, ensure_ascii=False)
    m, p = esperado
    exacto = f"{m}-{p}" in plano
    partes = bool(re.search(rf"\b0*{m}\b", plano)) and bool(re.search(rf"\b0*{p}\b", plano))
    resumen.append(f"== {nombre} | HTTP {estado} | {seg} s | rol esperado {m}-{p} | aparece tal cual {exacto} | "
                   f"manzana y predio por separado {partes} | campos de personas borrados {len(quitados)}")
    resumen += ["   " + f for f in forma(limpio)[:80]]

(SALIDA / "RESUMEN.txt").write_text("\n".join(resumen), encoding="utf-8")
print("\n".join(resumen))
print(f"\nListo. Archivos en {SALIDA}")
