"""Prueba de la regla estricta para elegir la propiedad, VERSIÓN 2, con la key de PRODUCCIÓN. Solo búsquedas, que NO se cobran.

Cambios de la versión 2 (después de la corrida del 24 de Noviembre de 2026, 17:20). Revisa que el nombre de la calle
calce (el SII abrevia, por ejemplo C CARTAGENA P), acepta el número sin el cero inicial solo si no hay uno exacto,
entiende rangos (CARVAJAL 0344 0358), lotes y sitios de casas (LT, ST), la D de departamento, varias unidades iguales
en el mismo edificio, y reintenta una vez cuando inciti responde con error o vacío. Guarda cada respuesta de inciti.

Objetivo. Con los mismos inmuebles de la prueba de cobertura (24 de Noviembre de 2026), probar una regla más estricta
para elegir entre varios resultados del SII y nuevas formas de buscar los que no se encontraron. Compara cada caso con
la decisión de la prueba anterior (cobertura.json).

Regla estricta.
1. El número de la calle debe calzar exacto, con el cero inicial si el aviso lo trae (0320 y 320 son direcciones distintas).
   Solo si el SII no trae ese número exacto se acepta sin el cero (el SII a veces lo omite, como LO OVALLE 320).
   El nombre de la calle también debe calzar, y entre varias se queda con la que más se parece.
2. Solo cuenta lo HABITACIONAL. Bodegas, estacionamientos, oficinas y bienes comunes nunca se eligen.
3. Si el aviso trae unidad (departamento, casa, etc.), la unidad del SII debe calzar exacta, letras incluidas.
4. Si el aviso no trae unidad, se elige solo la propiedad del SII que no trae unidad (o solo lote o sitio). Si no hay una sola, queda dudosa
   o "tasación no encontrada". Nunca se elige la primera de la lista.

Uso, en PowerShell.  cd D:\\Mercurio\\Exploracion_tasacion   y luego   python prueba_inciti_regla_estricta.py
Lee solo INCITI_API_KEY_PRODUCCION de D:\\Mercurio\\config.py y nunca la imprime. No llama a /get_appraisal ni a
/get_property_data. Guarda solo rol, dirección, uso y metros, sin datos de propietarios. No toca el robot.
Guarda en D:\\Mercurio\\INFORMES_REPORTES\\inciti_regla_estricta_v2.
"""
import ast, json, re, sys, time, unicodedata, urllib.request, urllib.error
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent                                   # D:\Mercurio
sys.path.insert(0, str(RAIZ))
try:
    import config
    KEY = getattr(config, "INCITI_API_KEY_PRODUCCION", None)
except Exception as e:
    print("No se pudo leer config.py:", type(e).__name__)
    sys.exit(1)
if not KEY or not str(KEY).strip():
    print("Falta INCITI_API_KEY_PRODUCCION en config.py.")
    sys.exit(1)
KEY = str(KEY).strip()

BASE = "https://api.inciti.com/api/searchengine/"
SALIDA = RAIZ / "INFORMES_REPORTES" / "inciti_regla_estricta_v2"
SALIDA.mkdir(parents=True, exist_ok=True)
NO_TASAR = {"15108", "15160", "15161"}   # Las Condes, Vitacura y Lo Barnechea (decisión del abogado)

# Mismos casos de la prueba de cobertura, leídos de su script (no se copian a mano).
_txt = (AQUI / "prueba_inciti_cobertura.py").read_text(encoding="utf-8")
_m = re.search(r"^CASOS = json\.loads\((.*)\)\s*$", _txt, re.M)
CASOS = json.loads(ast.literal_eval(_m.group(1)))
ANTES = {}
_cob = RAIZ / "INFORMES_REPORTES" / "inciti_cobertura" / "cobertura.json"
if _cob.exists():
    for f in json.loads(_cob.read_text(encoding="utf-8")):
        ANTES[(f["causa"], f["calle"], f["numero"], f["unidad"])] = f

consultas = 0


def llamar(servicio, cuerpo):
    global consultas
    time.sleep(0.7)
    consultas += 1
    req = urllib.request.Request(BASE + servicio, data=json.dumps(cuerpo).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "X-API-Key": KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            estado, texto = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        estado, texto = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        estado, texto = None, type(e).__name__
    try:
        datos = json.loads(texto)
    except Exception:
        datos = {}
    res = datos.get("results") if isinstance(datos, dict) else None
    res = [x for x in res if isinstance(x, dict)] if isinstance(res, list) else []
    return estado, [{"rol": x.get("rol"), "address": x.get("address"), "useType": x.get("useType"),
                     "util": x.get("usefulSquareMeters"), "total": x.get("totalSquareMeters")} for x in res]


def sin_tildes(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()

PALABRAS_UNIDAD = r"(?i)\b(departamento|depto|dpto|dp|casa|cs|unidad|vivienda|oficina|of|local|n[°º]|no|numero|número)(?!\w)\.?"
TIPOS_SII = {"DP", "D", "DPA", "DEP", "DTO", "DPTO", "DEPTO", "CS", "CASA", "LT", "LOTE", "ST", "SIT", "SITIO",
             "EDIF", "OF", "LC", "LOC", "PC", "PARC"}
LOTES = {"LT", "LOTE", "ST", "SIT", "SITIO", "PC", "PARC"}
PREFIJOS = {"CALLE", "PASAJE", "PJ", "PJE", "PSJE", "AV", "AVENIDA", "CAM", "CAMINO", "SN", "DIAGONAL", "DIAG", "C"}
VACIAS = {"DE", "DEL", "LA", "LAS", "LOS", "EL", "Y"}


def unidad_aviso(c):
    u = c.get("unidad")
    if not u:
        return []
    u = sin_tildes(re.sub(PALABRAS_UNIDAD, " ", u)).upper()
    u = re.sub(rf"^\s*{re.escape(str(int(c['numero'])))}\s*[-\s]\s*(?=\d)", "", u)
    fichas = re.findall(r"\d+|(?<![A-Z])[A-Z](?![A-Z])", u)
    return fichas if any(t.isdigit() for t in fichas) else ["?"]


def palabras(s, quitar_prefijo):
    t = re.findall(r"[A-Z]+", sin_tildes(s or "").upper())
    if quitar_prefijo:
        while t and t[0] in PREFIJOS and len(t) > 1:
            t = t[1:]
    return [x for x in t if x not in VACIAS]


def puntaje_calle(calle_sii, calle_aviso):
    """Cuánto se parece el nombre de la calle del SII al del aviso. El SII abrevia (C CARTAGENA P, GRL, PTE)."""
    av = palabras(calle_aviso, True)
    p = 0.0
    for t in palabras(calle_sii, True):
        if any(a == t or (len(t) >= 3 and a.startswith(t)) or (len(a) >= 3 and t.startswith(a)) for a in av):
            p += 1
        elif len(t) == 1 and any(a.startswith(t) for a in av):
            p += 0.5
        else:
            p -= 0.5
    return p


def partir(direccion, numero):
    """Separa la dirección del SII en calle, número y lo que viene después. Número exacto o, si no, sin el cero inicial."""
    d = (direccion or "").upper()
    for exacto in (True, False):
        for m in re.finditer(r"(?<![\dA-Z])(\d+)(?!\d)", d):
            n = m.group(1)
            if (n == numero) if exacto else (int(n) == int(numero)):
                resto = re.findall(r"\d+|[A-Z]+", d[m.end():])
                if len(resto) > 1 and resto[0].isdigit() and resto[1] in TIPOS_SII:
                    resto = resto[1:]          # rango de números, como CARVAJAL 0344 0358 DP 1501
                return d[:m.start()], resto, exacto
    return None


def elegir_v2(res, c):
    unidad = unidad_aviso(c)
    cands = []
    for x in res:
        if (x.get("useType") or "").upper() != "HABITACIONAL":
            continue
        p = partir(x.get("address"), c["numero"])
        if not p:
            continue
        calle, resto, exacto = p
        cands.append({"x": x, "resto": resto, "exacto": exacto, "punt": puntaje_calle(calle, c["calle"])})
    if not cands:
        return None, "sin calce de número"
    if any(k["exacto"] for k in cands):
        cands = [k for k in cands if k["exacto"]]
    top = max(k["punt"] for k in cands)
    if top <= 0:
        return None, "sin calce de calle"
    cands = [k for k in cands if k["punt"] == top]
    if unidad:
        def fichas(r):
            return sorted(t for t in r if t not in TIPOS_SII)
        ok = [k for k in cands if fichas(k["resto"]) == sorted(unidad)]
        if not ok:
            num = [k for k in cands if [t for t in fichas(k["resto"]) if t.isdigit()] == [t for t in unidad if t.isdigit()]]
            if len(num) == 1:
                return num[0]["x"], "dudosa (calza el número de la unidad, no la letra)"
            return None, "sin calce de unidad"
    else:
        ok = [k for k in cands if not k["resto"] or k["resto"][0] in LOTES]
        if not ok:
            return (cands[0]["x"], "dudosa (el SII trae algo después del número)") if len(cands) == 1 else (None, "ambigua")
    if len(ok) == 1:
        return ok[0]["x"], "elegida"
    x0 = ok[0]["x"]
    manz = {str(k["x"].get("rol", "")).split("-")[0] for k in ok}
    if len(manz) == 1 and all(k["x"].get("util") == x0.get("util") and k["x"].get("total") == x0.get("total") for k in ok):
        return x0, "elegida (varias iguales en el mismo edificio)"
    return None, "ambigua"


def llamar_con_reintento(cuerpo, estados, nombre):
    """Si inciti no responde bien, o responde vacío buscando con unidad, espera 3 segundos y prueba una vez más."""
    estado, res = llamar("get_results_by_address", cuerpo)
    if (estado != 200 and estado != 404) or (estado == 200 and not res and "unitNumber" in cuerpo):
        estados.append(f"{nombre} {estado} {len(res)}, reintento")
        time.sleep(3)
        estado, res = llamar("get_results_by_address", cuerpo)
    estados.append(f"{nombre} {estado} {len(res)}")
    return estado, res


def buscar(c, estados):
    """Hasta tres formas de buscar. Para apenas haya resultados."""
    calle = re.sub(r"(?i)^(calle|pasaje|avenida|av\.?|pje\.?|psje\.?|camino)\s+", "", c["calle"]).strip()
    unidad = unidad_aviso(c)
    u = "".join(t for t in unidad if t.isdigit())
    intentos = [("A", {"street": calle, "streetNumber": str(int(c["numero"])), "comunaCode": c["comunaCode"]}),
                ("B", {"street": c["calle"], "streetNumber": c["numero"], "comunaCode": c["comunaCode"]}),
                ("C", {"street": sin_tildes(calle), "streetNumber": str(int(c["numero"])), "comunaCode": c["comunaCode"]})]
    if u:
        intentos[0][1]["unitNumber"] = u
    for nombre, cuerpo in intentos:
        estado, res = llamar_con_reintento(cuerpo, estados, nombre)
        if estado == 200 and res:
            return nombre, res
    return "ninguno", []


def tipo(x):
    d = (x.get("address") or "").upper()
    if re.search(r"\b(DP|DPTO|DEPTO)\b", d) or not x.get("total"):
        return "departamento"
    return "casa"


def norm_rol(r):
    m = re.match(r"\s*0*(\d+)\s*-\s*0*(\d+)", str(r or ""))
    return f"{m.group(1)}-{m.group(2)}" if m else None


vistos, filas = set(), []
for c in CASOS:
    k = (c["causa"], c["calle"], c["numero"], c["unidad"])
    if k in vistos:
        continue
    vistos.add(k)
    f = {"causa": c["causa"], "comuna": c["comuna"], "calle": c["calle"], "numero": c["numero"], "unidad": c["unidad"],
         "unidad_leida": unidad_aviso(c)}
    elegido, como = None, None
    if c["rol_impreso"]:
        estado, res = llamar("get_results_by_rol", {"comunaCode": c["comunaCode"], "rol": c["rol_impreso"]})
        hab = [x for x in res if (x.get("useType") or "").upper() == "HABITACIONAL"] if estado == 200 else []
        if hab:
            elegido, como = hab[0], "por rol impreso"
    if not elegido:
        estados = []
        intento, res = buscar(c, estados)
        f["intento"], f["estados"], f["candidatos"] = intento, estados, res
        elegido, como = elegir_v2(res, c) if res else (None, "no encontrada")
    f["como"] = como
    f["sii"] = elegido
    if c["comunaCode"] in NO_TASAR:
        f["decision"] = "no se tasa (comuna)"
    elif not elegido:
        f["decision"] = "tasación no encontrada"
    elif not elegido.get("util"):
        f["decision"] = "sin metros útiles"
    elif como.startswith("dudosa"):
        f["decision"] = "dudosa, no se tasaría"
    else:
        f["decision"] = "se tasaría (" + tipo(elegido) + ")"
    a = ANTES.get(k) or {}
    f["antes_decision"] = a.get("decision")
    f["antes_rol"] = norm_rol((a.get("sii") or {}).get("rol"))
    nuevo = norm_rol(elegido.get("rol")) if elegido else None
    ta, tn = str(f["antes_decision"]).startswith("se tasaría"), f["decision"].startswith("se tasaría")
    if ta and tn:
        f["cambio"] = "igual" if f["antes_rol"] == nuevo else "tasa otro rol"
    elif ta and not tn:
        f["cambio"] = "antes se tasaba, ahora no"
    elif tn and not ta:
        f["cambio"] = "antes no, ahora se tasa"
    else:
        f["cambio"] = "igual (no se tasa)"
    filas.append(f)
    if len(filas) % 20 == 0:
        print(f"  {len(filas)} revisados ({consultas} consultas, gratis)")


def contar(clave):
    d = {}
    for f in filas:
        d[f[clave]] = d.get(f[clave], 0) + 1
    return d


lineas = [f"Inmuebles distintos {len(filas)}. Consultas de búsqueda {consultas} (no se cobran).",
          "Decisión " + json.dumps(contar("decision"), ensure_ascii=False),
          "Cambio contra la prueba anterior " + json.dumps(contar("cambio"), ensure_ascii=False),
          "", "Casos que cambian o quedan dudosos (causa | dirección del aviso | antes | ahora | dirección del SII elegida)"]
for f in filas:
    if f["cambio"] not in ("igual", "igual (no se tasa)") or f["decision"].startswith("dudosa"):
        sii = (f["sii"] or {}).get("address")
        lineas.append(f"{f['causa']} | {f['calle']} {f['numero']} {f['unidad'] or ''} | {f['antes_decision']} "
                      f"({f['antes_rol']}) | {f['decision']}, {f['como']} | {sii}")
(SALIDA / "regla_estricta_v2.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
(SALIDA / "RESUMEN.txt").write_text("\n".join(lineas), encoding="utf-8")
print("\n" + "\n".join(lineas))
print(f"Listo. Archivos en {SALIDA}")
