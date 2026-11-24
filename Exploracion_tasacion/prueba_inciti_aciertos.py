"""Prueba de aciertos de la búsqueda por dirección de inciti con la key de PRODUCCIÓN (puede cobrar).

Objetivo. Medir cuántas veces la dirección que lee el robot lleva al rol correcto. 18 causas de la RM cuyo aviso imprime el
rol de avalúo (16 de Octubre y 2 de Noviembre), así se sabe la respuesta correcta. Intento 1 con la calle sin "calle",
"Pasaje" ni "Avenida", el número sin ceros iniciales y la unidad con su letra. Solo si da 404, intento 2 con la calle tal
como la lee el robot y la unidad sin letra. Máximo 36 consultas, solo búsqueda por dirección.

Reglas. Lee solo INCITI_API_KEY_PRODUCCION de D:\\Mercurio\\config.py y nunca la imprime. Borra de lo que guarda todo dato de
propietarios (RUT, teléfonos, correos, nombres de personas) y anota solo en qué campo venían. No toca el robot.
Guarda en D:\\Mercurio\\INFORMES_REPORTES\\inciti_aciertos.

Uso, en PowerShell.  cd D:\\Mercurio\\Exploracion_tasacion   y luego   python prueba_inciti_aciertos.py
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
SALIDA = RAIZ / "INFORMES_REPORTES" / "inciti_aciertos"
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
 {
  "causa": "18569-2023",
  "direccion_robot": "Pasaje Asturcón 1588, Huechuraba",
  "esperado": [
   "0089-00039"
  ],
  "intento1": {
   "street": "Asturcón",
   "streetNumber": "1588",
   "comunaCode": "14158"
  },
  "intento2": {
   "street": "Pasaje Asturcón",
   "streetNumber": "1588",
   "comunaCode": "14158"
  }
 },
 {
  "causa": "14985-2025",
  "direccion_robot": "calle Uno 6590 y 6594, departamento 807, La Cisterna",
  "esperado": [
   "2905-89"
  ],
  "intento1": {
   "street": "Uno",
   "streetNumber": "6590",
   "comunaCode": "16110",
   "unitNumber": "807"
  },
  "intento2": {
   "street": "calle Uno",
   "streetNumber": "6590",
   "comunaCode": "16110",
   "unitNumber": "807"
  }
 },
 {
  "causa": "2237-2025",
  "direccion_robot": "calle Nataniel Cox 223, departamento 2007, Santiago",
  "esperado": [
   "490-279"
  ],
  "intento1": {
   "street": "Nataniel Cox",
   "streetNumber": "223",
   "comunaCode": "13101",
   "unitNumber": "2007"
  },
  "intento2": {
   "street": "calle Nataniel Cox",
   "streetNumber": "223",
   "comunaCode": "13101",
   "unitNumber": "2007"
  }
 },
 {
  "causa": "22041-2024",
  "direccion_robot": "calle Los Alerces 3330, departamento 306-A, Ñuñoa",
  "esperado": [
   "6339-127"
  ],
  "intento1": {
   "street": "Los Alerces",
   "streetNumber": "3330",
   "comunaCode": "15105",
   "unitNumber": "306-A"
  },
  "intento2": {
   "street": "calle Los Alerces",
   "streetNumber": "3330",
   "comunaCode": "15105",
   "unitNumber": "306"
  }
 },
 {
  "causa": "16109-2023",
  "direccion_robot": "Cuarta Avenida 1447, departamento 705, San Miguel",
  "esperado": [
   "5655-119",
   "5655-284"
  ],
  "intento1": {
   "street": "Cuarta Avenida",
   "streetNumber": "1447",
   "comunaCode": "16106",
   "unitNumber": "705"
  },
  "intento2": {
   "street": "Cuarta Avenida",
   "streetNumber": "1447",
   "comunaCode": "16106",
   "unitNumber": "705"
  }
 },
 {
  "causa": "618-2025",
  "direccion_robot": "calle Alcalde Pedro Alarcón 777, departamento 310, San Miguel",
  "esperado": [
   "2156-37"
  ],
  "intento1": {
   "street": "Alcalde Pedro Alarcón",
   "streetNumber": "777",
   "comunaCode": "16106",
   "unitNumber": "310"
  },
  "intento2": {
   "street": "calle Alcalde Pedro Alarcón",
   "streetNumber": "777",
   "comunaCode": "16106",
   "unitNumber": "310"
  }
 },
 {
  "causa": "14133-2024",
  "direccion_robot": "Avenida Lo Ovalle 0926, departamento A trescientos nueve, La Cisterna",
  "esperado": [
   "2901-83"
  ],
  "intento1": {
   "street": "Lo Ovalle",
   "streetNumber": "926",
   "comunaCode": "16110",
   "unitNumber": "309-A"
  },
  "intento2": {
   "street": "Avenida Lo Ovalle",
   "streetNumber": "0926",
   "comunaCode": "16110",
   "unitNumber": "309"
  }
 },
 {
  "causa": "15178-2022",
  "direccion_robot": "Pasaje Seis Emilio Sanfuentes Vergara 509, Pudahuel",
  "esperado": [
   "992-5"
  ],
  "intento1": {
   "street": "Seis Emilio Sanfuentes Vergara",
   "streetNumber": "509",
   "comunaCode": "14111"
  },
  "intento2": {
   "street": "Pasaje Seis Emilio Sanfuentes Vergara",
   "streetNumber": "509",
   "comunaCode": "14111"
  }
 },
 {
  "causa": "15225-2024",
  "direccion_robot": "calle Almirante Latorre 125 al 143, Santiago",
  "esperado": [
   "620-2"
  ],
  "intento1": {
   "street": "Almirante Latorre",
   "streetNumber": "125",
   "comunaCode": "13101"
  },
  "intento2": {
   "street": "calle Almirante Latorre",
   "streetNumber": "125",
   "comunaCode": "13101"
  }
 },
 {
  "causa": "2272-2025",
  "direccion_robot": "Avenida Elías Fernández Albano 492, departamento 1011 A, La Cisterna",
  "esperado": [
   "310-337"
  ],
  "intento1": {
   "street": "Elías Fernández Albano",
   "streetNumber": "492",
   "comunaCode": "16110",
   "unitNumber": "1011-A"
  },
  "intento2": {
   "street": "Avenida Elías Fernández Albano",
   "streetNumber": "492",
   "comunaCode": "16110",
   "unitNumber": "1011"
  }
 },
 {
  "causa": "16650-2023",
  "direccion_robot": "calle Barcelona 12152, El Bosque",
  "esperado": [
   "5616-10"
  ],
  "intento1": {
   "street": "Barcelona",
   "streetNumber": "12152",
   "comunaCode": "16165"
  },
  "intento2": {
   "street": "calle Barcelona",
   "streetNumber": "12152",
   "comunaCode": "16165"
  }
 },
 {
  "causa": "6871-2024",
  "direccion_robot": "calle Rivas 1061, departamento 907, San Miguel",
  "esperado": [
   "648-109",
   "648-310",
   "648-226"
  ],
  "intento1": {
   "street": "Rivas",
   "streetNumber": "1061",
   "comunaCode": "16106",
   "unitNumber": "907"
  },
  "intento2": {
   "street": "calle Rivas",
   "streetNumber": "1061",
   "comunaCode": "16106",
   "unitNumber": "907"
  }
 },
 {
  "causa": "10397-2025",
  "direccion_robot": "calle Santa Ester 923, San Miguel",
  "esperado": [
   "4348-4"
  ],
  "intento1": {
   "street": "Santa Ester",
   "streetNumber": "923",
   "comunaCode": "16106"
  },
  "intento2": {
   "street": "calle Santa Ester",
   "streetNumber": "923",
   "comunaCode": "16106"
  }
 },
 {
  "causa": "8617-2025",
  "direccion_robot": "Pasaje Salvador Sanfuentes 10735, La Pintana",
  "esperado": [
   "6083-5"
  ],
  "intento1": {
   "street": "Salvador Sanfuentes",
   "streetNumber": "10735",
   "comunaCode": "16154"
  },
  "intento2": {
   "street": "Pasaje Salvador Sanfuentes",
   "streetNumber": "10735",
   "comunaCode": "16154"
  }
 },
 {
  "causa": "11474-2025",
  "direccion_robot": "calle Vargas Buston 1082, Departamento número mil ocho, San Miguel",
  "esperado": [
   "5748-136",
   "5748-287"
  ],
  "intento1": {
   "street": "Vargas Buston",
   "streetNumber": "1082",
   "comunaCode": "16106",
   "unitNumber": "1008"
  },
  "intento2": {
   "street": "calle Vargas Buston",
   "streetNumber": "1082",
   "comunaCode": "16106",
   "unitNumber": "1008"
  }
 },
 {
  "causa": "12085-2024",
  "direccion_robot": "Avenida Lo Errázuriz 1701, departamento 107 -A, Cerrillos",
  "esperado": [
   "4-42"
  ],
  "intento1": {
   "street": "Lo Errázuriz",
   "streetNumber": "1701",
   "comunaCode": "14166",
   "unitNumber": "107-A"
  },
  "intento2": {
   "street": "Avenida Lo Errázuriz",
   "streetNumber": "1701",
   "comunaCode": "14166",
   "unitNumber": "107"
  }
 },
 {
  "causa": "13136-2022",
  "direccion_robot": "Santo Domingo 1161, departamento 808, Santiago",
  "esperado": [
   "210-636"
  ],
  "intento1": {
   "street": "Santo Domingo",
   "streetNumber": "1161",
   "comunaCode": "13101",
   "unitNumber": "808"
  },
  "intento2": {
   "street": "Santo Domingo",
   "streetNumber": "1161",
   "comunaCode": "13101",
   "unitNumber": "808"
  }
 },
 {
  "causa": "22356-2024",
  "direccion_robot": "Arturo Prat 324, departamento 1809, Santiago",
  "esperado": [
   "533-358"
  ],
  "intento1": {
   "street": "Arturo Prat",
   "streetNumber": "324",
   "comunaCode": "13101",
   "unitNumber": "1809"
  },
  "intento2": {
   "street": "Arturo Prat",
   "streetNumber": "324",
   "comunaCode": "13101",
   "unitNumber": "1809"
  }
 }
]


def llamar(cuerpo):
    req = urllib.request.Request(BASE + "get_results_by_address", data=json.dumps(cuerpo).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "X-API-Key": KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            estado, texto = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        estado, texto = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        estado, texto = None, f"{type(e).__name__}: {str(e)[:200]}"
    try:
        datos = json.loads(texto)
    except Exception:
        datos = {"texto_no_json": texto[:2000]}
    quitados = []
    return estado, limpiar(datos, "$", quitados), quitados


def norm_rol(r):
    m = re.match(r"\s*0*(\d+)\s*-\s*0*(\d+)", str(r or ""))
    return f"{m.group(1)}-{m.group(2)}" if m else str(r)


filas, consultas = [], 0
for caso in CASOS:
    esperados = {norm_rol(r) for r in caso["esperado"]}
    fila = {"causa": caso["causa"], "direccion_robot": caso["direccion_robot"], "esperado": sorted(esperados)}
    for n in ("intento1", "intento2"):
        estado, resp, quitados = llamar(caso[n])
        consultas += 1
        res = resp.get("results") if isinstance(resp, dict) else None
        res = res if isinstance(res, list) else []
        roles = [norm_rol(x.get("rol")) for x in res if isinstance(x, dict)]
        fila[n] = {"enviado": caso[n], "http": estado, "n_resultados": len(res), "roles": roles,
                   "direcciones_sii": [x.get("address") for x in res if isinstance(x, dict)][:5],
                   "m2_utiles": [x.get("usefulSquareMeters") for x in res if isinstance(x, dict)][:5],
                   "m2_totales": [x.get("totalSquareMeters") for x in res if isinstance(x, dict)][:5],
                   "uso": [x.get("useType") for x in res if isinstance(x, dict)][:5],
                   "campos_de_personas_borrados": quitados, "error": resp.get("error") if isinstance(resp, dict) else None}
        if estado == 200 and res:
            break
    ult = fila.get("intento2") or fila["intento1"]
    roles = ult["roles"]
    if not roles:
        fila["resultado"] = "NO ENCONTRADA"
    elif roles[0] in esperados:
        fila["resultado"] = "ACIERTA" + (" (intento 2)" if "intento2" in fila else "")
    elif esperados & set(roles):
        fila["resultado"] = "ACIERTA EN LA LISTA, NO PRIMERO"
    else:
        fila["resultado"] = "ROL DISTINTO"
    filas.append(fila)
    print(f"{fila['causa']:12s} {fila['resultado']:32s} esperado {','.join(fila['esperado']):22s} devuelto {','.join(roles[:3]) or '-':22s} "
          f"m2 {ult['m2_utiles'][:1]} | {ult['direcciones_sii'][:1]}")

cuenta = {}
for f in filas:
    k = f["resultado"].split(" (")[0]
    cuenta[k] = cuenta.get(k, 0) + 1
lineas = [f"Consultas hechas {consultas}", "Resultados " + ", ".join(f"{k} {v}" for k, v in cuenta.items())]
(SALIDA / "aciertos.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
(SALIDA / "RESUMEN.txt").write_text("\n".join(lineas), encoding="utf-8")
print("\n" + "\n".join(lineas))
print(f"Listo. Archivos en {SALIDA}")
