"""Tasación comercial con la API de inciti (paso 3 del diseño de la columna Valor comercial, 24 de Noviembre de 2026).

Diseño y decisiones de Diego en Exploracion_tasacion/DISENO_VALOR_COMERCIAL.md (secciones 7 y 7b). Resumen.
- Solo la tabla principal. Por cada causa con UNA casa o departamento de dirección comprobada en la RM, busca la propiedad
  en inciti (gratis) con la regla fijada el 24 de Noviembre (versión 2) y la tasa (/get_appraisal, 0,0371 UF por respuesta
  200). Las Condes, Vitacura y Lo Barnechea no se tasan (decisión del abogado).
- Cuando no hay valor, un texto corto va en la celda del valor ("Tasación no encontrada", etc.).
- Memoria tasaciones.csv (en Supabase estado/tasaciones.csv), solo agrega filas. Una tasación de la misma causa o de la misma
  propiedad no se vuelve a pagar. Con más de 6 meses se muestra en amarillo con su antigüedad y NO se vuelve a tasar.
- Tope de 20 tasaciones por corrida (TASACION_TOPE) y 15 minutos. Nunca detiene la corrida, el Excel sale igual.
- Sin la key (INCITI_API_KEY) no hace nada y el Excel queda exactamente como antes.
- Nunca guarda datos de propietarios. De inciti solo se guarda rol, dirección del SII, coordenadas, metros, valores y el
  enlace al PDF.
"""
from __future__ import annotations

import csv
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "tasaciones.csv"              # memoria local. servidor/diario.py la baja y la sube a Supabase
RESUMEN_HOY = RAIZ / "_tasaciones_hoy.json"    # lo lee servidor/diario.py para el correo de Diego
BASE = "https://api.inciti.com/api/"
COSTO_UF = 0.0371                              # por tasación (verificado en Facturación el 24 de Noviembre de 2026)
BASE_PLAN = 27                                 # tasaciones del mes que Diego cuenta como incluidas en la base del plan
VIGENCIA_MESES = 6
TIEMPO_MAX = 15 * 60
ESPERA_BUSQUEDA = 0.7                          # límite de inciti, 100 consultas por minuto
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

# Códigos del SII de las comunas de la RM, del manual de inciti (verificado el 24 de Noviembre de 2026).
# Santiago tiene tres (13101, 13134 Santiago Oeste y 13135 Santiago Sur). La búsqueda por rol da lo mismo con cualquiera.
COMUNAS = {
    "santiago": "13101", "cerrillos": "14166", "cerro navia": "14156", "colina": "14201", "conchali": "14127",
    "estacion central": "14157", "huechuraba": "14158", "independencia": "13167", "la florida": "15128",
    "la reina": "15132", "lampa": "14202", "las condes": "15108", "lo barnechea": "15161", "lo prado": "14155",
    "macul": "15151", "maipu": "14109", "nunoa": "15105", "penalolen": "15152", "providencia": "15103",
    "pudahuel": "14111", "quilicura": "14114", "quinta normal": "14107", "recoleta": "13159", "renca": "14113",
    "tiltil": "14203", "til til": "14203", "til-til": "14203", "vitacura": "15160", "pirque": "16302",
    "san jose de maipo": "16303", "san miguel": "16106", "la cisterna": "16110", "la granja": "16131",
    "san ramon": "16153", "la pintana": "16154", "pedro aguirre cerda": "16162", "san joaquin": "16163",
    "lo espejo": "16164", "el bosque": "16165", "puente alto": "16301", "san bernardo": "16401",
    "calera de tango": "16402", "buin": "16403", "paine": "16404", "talagante": "14501", "isla de maipo": "14502",
    "el monte": "14503", "penaflor": "14504", "padre hurtado": "14505", "melipilla": "14601", "maria pinto": "14602",
    "curacavi": "14603", "san pedro": "14604", "alhue": "14605",
}
SANTIAGO = {"13101", "13134", "13135"}
NO_TASAR = {"15108", "15160", "15161"}          # Las Condes, Vitacura y Lo Barnechea (decisión del abogado)

# Textos cortos de la celda del valor (decisión de Diego del 24 de Noviembre de 2026, 17:34)
T_NO_ENCONTRADA = "Tasación no encontrada"
T_COMUNA = "No se tasa en esta comuna"
T_NO_HAB = "No es casa ni departamento"
T_VARIAS = "Más de 1 propiedad en la causa, valorizar manualmente"
T_SIN_COMPARABLES = "Sin ventas parecidas para tasar"
T_FALLA = "Sin tasación hoy, falla del servicio"
T_DIRECCION = "Dirección no comprobada"
T_TOPE = "Sin tasación hoy, se alcanzó el tope del día"

CAMPOS = ["fecha", "hora", "causa", "rol_avaluo", "comuna_code", "comuna", "direccion_sii", "coordenadas", "tipo",
          "m2_util", "m2_total", "valor_uf", "valor_clp", "uf_usada", "pdf_url", "como", "resultado", "cobrada"]


# ─────────────────────────────────────────────────────────────────
# Regla para elegir la propiedad. Copia de Exploracion_tasacion/prueba_inciti_regla_estricta.py (versión 2), fijada por
# Diego el 24 de Noviembre de 2026 (última calibración). El único agregado es solo_hab=False, que sirve para decir
# "No es casa ni departamento" cuando lo que calza es una bodega, un estacionamiento o una oficina.
# ─────────────────────────────────────────────────────────────────

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


def elegir_v2(res, c, solo_hab=True):
    unidad = unidad_aviso(c)
    cands = []
    for x in res:
        if solo_hab and (x.get("useType") or "").upper() != "HABITACIONAL":
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


def tipo_sii(x):
    d = (x.get("address") or "").upper()
    if re.search(r"\b(DP|DPTO|DEPTO)\b", d) or not x.get("total"):
        return "departamento"
    return "casa"


def norm_rol(r):
    m = re.match(r"\s*0*(\d+)\s*-\s*0*(\d+)", str(r or ""))
    return f"{m.group(1)}-{m.group(2)}" if m else None


# ─────────────────────────────────────────────────────────────────
# Datos del aviso
# ─────────────────────────────────────────────────────────────────

_ROL_AVALUO = re.compile(r"(?i)rol\s+(?:de\s+)?aval[uú]o(?:\s+fiscal)?(?:\s+(?:n[°ºo]\.?|n[uú]mero|nro\.?))?\s*:?\s*(\d{1,5})\s*-\s*(\d{1,5})\b")


def rol_avaluo(textos):
    """El rol de avalúo impreso en el aviso, si hay uno solo. Si no hay o hay varios distintos, None."""
    roles = {f"{int(a)}-{int(b)}" for t in textos or [] for a, b in _ROL_AVALUO.findall(t or "")}
    return roles.pop() if len(roles) == 1 else None


def partes_direccion(p):
    """Calle, número y unidad de una dirección comprobada del robot. Usa dir_base, la que motor/direccion.py arma como
    "calle número, unidad" antes del formato de condominio de motor/conjunto.py. Devuelve None si no trae número."""
    direccion = (p.get("dir_base") or p.get("direccion") or "").strip()
    calle = (p.get("calle") or "").strip()
    if not direccion or not calle or not direccion.lower().startswith(calle.lower()):
        return None
    resto = direccion[len(calle):]
    num_txt, _, unidad = resto.partition(",")
    m = re.match(r"\s*(\d+)", num_txt)
    if not m:
        return None
    unidad = unidad.split(",")[0].strip()         # "departamento 302 D, block D" queda en "departamento 302 D"
    return {"calle": calle, "numero": m.group(1), "unidad": unidad or None}


def codigo_comuna(nombre):
    n = " ".join(sin_tildes(str(nombre or "")).lower().split())
    return COMUNAS.get(n)


# ─────────────────────────────────────────────────────────────────
# inciti
# ─────────────────────────────────────────────────────────────────

def leer_key():
    k = os.environ.get("INCITI_API_KEY", "").strip()
    if not k:
        try:
            import config
            k = str(getattr(config, "INCITI_API_KEY", "") or "").strip()
        except Exception:
            k = ""
    return k


class Inciti:
    """Las llamadas a inciti. La key nunca se imprime ni se guarda."""

    def __init__(self, key):
        self._key = key
        self.busquedas = 0

    def _post(self, servicio, cuerpo, timeout):
        req = urllib.request.Request(BASE + servicio, data=json.dumps(cuerpo).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json", "X-API-Key": self._key})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                estado, texto = r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            estado, texto = e.code, e.read().decode("utf-8", "replace")
        except Exception:
            return None, {}
        try:
            return estado, json.loads(texto)
        except Exception:
            return estado, {}

    def buscar(self, servicio, cuerpo):
        time.sleep(ESPERA_BUSQUEDA)
        self.busquedas += 1
        estado, datos = self._post("searchengine/" + servicio, cuerpo, 30)
        res = datos.get("results") if isinstance(datos, dict) else None
        res = [x for x in res if isinstance(x, dict)] if isinstance(res, list) else []
        return estado, [{"rol": x.get("rol"), "address": x.get("address"), "useType": x.get("useType"),
                         "util": x.get("usefulSquareMeters"), "total": x.get("totalSquareMeters"),
                         "comunaCode": x.get("comunaCode"), "coordenadas": x.get("coordinates")} for x in res]

    def tasar(self, cuerpo):
        """Una sola llamada, sin reintentos, porque cada respuesta 200 se cobra."""
        return self._post("get_appraisal", cuerpo, 150)


def _buscar_con_reintento(api, cuerpo, nombre, estados):
    estado, res = api.buscar("get_results_by_address", cuerpo)
    if (estado != 200 and estado != 404) or (estado == 200 and not res and "unitNumber" in cuerpo):
        estados.append(f"{nombre} {estado} {len(res)}, reintento")
        time.sleep(3)
        estado, res = api.buscar("get_results_by_address", cuerpo)
    estados.append(f"{nombre} {estado} {len(res)}")
    return estado, res


def buscar_direccion(api, c, estados):
    """Hasta tres formas de buscar, igual que la versión 2. Para apenas haya resultados."""
    calle = re.sub(r"(?i)^(calle|pasaje|avenida|av\.?|pje\.?|psje\.?|camino)\s+", "", c["calle"]).strip()
    u = "".join(t for t in unidad_aviso(c) if t.isdigit())
    intentos = [("A", {"street": calle, "streetNumber": str(int(c["numero"])), "comunaCode": c["comunaCode"]}),
                ("B", {"street": c["calle"], "streetNumber": c["numero"], "comunaCode": c["comunaCode"]}),
                ("C", {"street": sin_tildes(calle), "streetNumber": str(int(c["numero"])), "comunaCode": c["comunaCode"]})]
    if u:
        intentos[0][1]["unitNumber"] = u
    fallas = 0
    for nombre, cuerpo in intentos:
        estado, res = _buscar_con_reintento(api, cuerpo, nombre, estados)
        if estado == 200 and res:
            return "ok", res
        if estado not in (200, 404):
            fallas += 1
    # Si alguna forma de buscar no tuvo respuesta, no se puede decir que no existe. Queda como falla del servicio.
    return ("falla" if fallas else "nada"), []


# ─────────────────────────────────────────────────────────────────
# Memoria de tasaciones (solo agrega filas)
# ─────────────────────────────────────────────────────────────────

def leer_memoria(archivo=None):
    archivo = Path(archivo or ARCHIVO)
    if not archivo.exists():
        return []
    with open(archivo, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def agregar_memoria(fila, archivo=None):
    archivo = Path(archivo or ARCHIVO)
    nuevo = not archivo.exists()
    with open(archivo, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        if nuevo:
            w.writeheader()
        w.writerow({k: ("" if fila.get(k) is None else fila.get(k)) for k in CAMPOS})


def _mismo_codigo(a, b):
    return a == b or (a in SANTIAGO and b in SANTIAGO)


def buscar_en_memoria(memoria, causa=None, rol=None, codigo=None):
    """La tasación más nueva de esa causa o de esa propiedad (rol de avalúo y comuna)."""
    filas = [f for f in memoria if f.get("resultado") == "tasada"
             and ((causa and f.get("causa") == causa) or (rol and norm_rol(f.get("rol_avaluo")) == rol
                                                          and _mismo_codigo(f.get("comuna_code"), codigo)))]
    return max(filas, key=lambda f: (f.get("fecha", ""), f.get("hora", "")), default=None)


def meses_entre(desde, hasta):
    m = (hasta.year - desde.year) * 12 + hasta.month - desde.month
    return m - 1 if hasta.day < desde.day else m


def fecha_palabras(d):
    return f"{d.day} de {MESES[d.month - 1]} del {d.year}"


# ─────────────────────────────────────────────────────────────────
# Tasación de la tabla principal
# ─────────────────────────────────────────────────────────────────

def _clave(c):
    return f"{c.get('rol', '')}-{c.get('año', '')}|{c.get('tribunal', '')}"


def _poner(c, texto=None, uf=None, clp=None, link=None, amarilla=False, obs=None):
    c["tas_uf"] = uf if uf is not None else texto
    c["tas_clp"] = clp
    c["tas_link"] = link
    c["tas_amarilla"] = amarilla
    if obs:
        prev = (c.get("observaciones") or "").strip()
        c["observaciones"] = f"{prev} {obs}".strip()


def _desde_memoria(c, fila, hoy):
    d = date.fromisoformat(fila["fecha"])
    uf = float(fila["valor_uf"]) if fila.get("valor_uf") else None
    clp = int(float(fila["valor_clp"])) if fila.get("valor_clp") else None
    link = fila.get("pdf_url") or None
    meses = meses_entre(d, hoy)
    if meses >= VIGENCIA_MESES and hoy > d:
        _poner(c, uf=uf, clp=clp, link=link, amarilla=True,
               obs=f"Esta propiedad se tasó el {fecha_palabras(d)}, hace {meses} meses. Se recomienda volver a valorizarla.")
    else:
        _poner(c, uf=uf, clp=clp, link=link, obs=f"Tasada el {fecha_palabras(d)} (ver informe).")


def _datos_inciti(datos):
    """Valor de venta, UF usada y enlace al PDF de la respuesta de /get_appraisal. Nada de personas."""
    if not isinstance(datos, dict):
        return None
    venta = ((datos.get("valuation") or {}).get("sale") or {})
    uf, clp = venta.get("propertyValueUF"), venta.get("propertyValueCLP")
    if not isinstance(uf, (int, float)) or uf <= 0:
        return None
    return {"uf": float(uf), "clp": int(clp) if isinstance(clp, (int, float)) else None,
            "uf_usada": datos.get("ufValue"), "pdf": datos.get("pdfUrl") or None}


def tasar_causas(causas, metricas=None, api=None, hoy=None, archivo=None, resumen=None):
    """Agrega a cada causa de la tabla principal tas_uf, tas_clp, tas_link y tas_amarilla. Sin key no hace nada.
    Nunca levanta un error. Devuelve el resumen del día (o None si no hay key)."""
    key = leer_key() if api is None else "prueba"
    if not key:
        return None
    hoy = hoy or date.today()
    archivo = Path(archivo or ARCHIVO)
    resumen_path = Path(resumen or RESUMEN_HOY)
    api = api or Inciti(key)
    tope = int(os.environ.get("TASACION_TOPE") or 20)
    apagada = os.environ.get("TASACION_APAGADA", "").strip() == "1"
    inicio = time.time()
    r = {"fecha": hoy.isoformat(), "pagadas_hoy": 0, "sin_comparables": 0, "fallas": 0, "reutilizadas": 0,
         "no_encontradas": 0, "tope_alcanzado": False, "uf_usada": None}
    try:
        memoria = leer_memoria(archivo)
    except Exception:
        memoria, apagada = [], True        # sin memoria no se tasa, para no pagar dos veces
    for c in causas:
        try:
            if apagada:
                _poner(c, T_FALLA)
                r["fallas"] += 1
                continue
            _tasar_una(c, api, memoria, hoy, archivo, r, tope, inicio)
        except Exception as e:
            print(f"  Tasación de {c.get('rol')}-{c.get('año')} con error ({type(e).__name__}). Sigue la corrida.")
            if "tas_uf" not in c:
                _poner(c, T_FALLA)
                r["fallas"] += 1
    r["busquedas"] = api.busquedas
    try:
        mes = hoy.isoformat()[:7]
        filas = leer_memoria(archivo)
        r["mes_total"] = sum(1 for f in filas if f.get("cobrada") == "si" and f.get("fecha", "").startswith(mes))
        resumen_path.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    print(f"  Tasaciones. Pagadas hoy {r['pagadas_hoy']}. Reutilizadas {r['reutilizadas']}. "
          f"Sin ventas parecidas {r['sin_comparables']}. No encontradas {r['no_encontradas']}. Fallas {r['fallas']}. "
          f"Búsquedas {api.busquedas} (no se cobran).")
    return r


def _tasar_una(c, api, memoria, hoy, archivo, r, tope, inicio):
    clave = _clave(c)
    props = c.get("_tasar") or []
    if len(props) > 1 or (c.get("n_propiedades") or 0) > 1:
        _poner(c, T_VARIAS)
        return
    if len(props) != 1 or not props[0].get("dir_ok") or not props[0].get("direccion"):
        _poner(c, T_DIRECCION)
        return
    p = props[0]
    codigo = codigo_comuna(p.get("comuna"))
    if not codigo:
        _poner(c, T_DIRECCION)
        return
    if codigo in NO_TASAR:
        _poner(c, T_COMUNA)
        return
    previa = buscar_en_memoria(memoria, causa=clave)
    if previa:
        _desde_memoria(c, previa, hoy)
        r["reutilizadas"] += 1
        return
    # Búsqueda (gratis). Primero por el rol de avalúo impreso, si hay uno solo. Después por dirección.
    elegido, como = None, None
    rol_imp = rol_avaluo(c.get("_textos"))
    if rol_imp:
        estado, res = api.buscar("get_results_by_rol", {"comunaCode": codigo, "rol": rol_imp})
        hab = [x for x in res if (x.get("useType") or "").upper() == "HABITACIONAL"] if estado == 200 else []
        if hab:
            elegido, como = hab[0], "por rol impreso"
    if not elegido:
        partes = partes_direccion(p)
        if not partes:
            _poner(c, T_NO_ENCONTRADA)
            r["no_encontradas"] += 1
            return
        caso = {**partes, "comunaCode": codigo}
        estados = []
        situacion, res = buscar_direccion(api, caso, estados)
        if situacion == "falla":
            _poner(c, T_FALLA)
            r["fallas"] += 1
            return
        x, motivo = elegir_v2(res, caso) if res else (None, "no encontrada")
        if x is None or motivo.startswith("dudosa"):
            otro, m2 = elegir_v2(res, caso, solo_hab=False) if res else (None, "")
            if otro is not None and m2.startswith("elegida") and (otro.get("useType") or "").upper() != "HABITACIONAL":
                _poner(c, T_NO_HAB)
            else:
                _poner(c, T_NO_ENCONTRADA)
                r["no_encontradas"] += 1
            return
        elegido, como = x, "por dirección"
    rol = norm_rol(elegido.get("rol"))
    codigo_sii = str(elegido.get("comunaCode") or codigo)
    util, total = elegido.get("util"), elegido.get("total")
    if not rol or not util:
        _poner(c, T_NO_ENCONTRADA)
        r["no_encontradas"] += 1
        return
    previa = buscar_en_memoria(memoria, rol=rol, codigo=codigo_sii)
    if previa:
        _desde_memoria(c, previa, hoy)
        r["reutilizadas"] += 1
        return
    # Tasación (se cobra cada respuesta 200)
    if r["pagadas_hoy"] >= tope or time.time() - inicio > TIEMPO_MAX:
        _poner(c, T_TOPE)
        r["tope_alcanzado"] = True
        return
    tipo = tipo_sii(elegido)
    cuerpo = {"rol": rol, "comunaCode": codigo_sii, "propertyType": tipo, "usefulSquareMeters": util}
    if tipo == "casa":
        cuerpo["totalSquareMeters"] = total
    estado, datos = api.tasar(cuerpo)
    ahora = datetime.now()
    fila = {"fecha": hoy.isoformat(), "hora": ahora.strftime("%H:%M:%S"), "causa": clave, "rol_avaluo": rol,
            "comuna_code": codigo_sii, "comuna": p.get("comuna"), "direccion_sii": elegido.get("address"),
            "coordenadas": json.dumps(elegido.get("coordenadas"), ensure_ascii=False) if elegido.get("coordenadas") else "",
            "tipo": tipo, "m2_util": util, "m2_total": total, "como": como, "cobrada": "si" if estado == 200 else "no"}
    v = _datos_inciti(datos) if estado == 200 else None
    if estado == 200:
        r["pagadas_hoy"] += 1
    if v:
        fila.update({"valor_uf": round(v["uf"], 2), "valor_clp": v["clp"], "uf_usada": v["uf_usada"],
                     "pdf_url": v["pdf"], "resultado": "tasada"})
        r["uf_usada"] = v["uf_usada"] or r["uf_usada"]
        _poner(c, uf=round(v["uf"], 2), clp=v["clp"], link=v["pdf"])
    elif estado == 404:
        fila["resultado"] = "sin_comparables"
        r["sin_comparables"] += 1
        _poner(c, T_SIN_COMPARABLES)
    else:
        fila["resultado"] = "falla"
        r["fallas"] += 1
        _poner(c, T_FALLA)
    agregar_memoria(fila, archivo)
    memoria.append({k: ("" if fila.get(k) is None else str(fila.get(k))) for k in CAMPOS})


# ─────────────────────────────────────────────────────────────────
# Texto del correo de Diego (contador propio del robot, decisión de Diego del 24 de Noviembre de 2026, 17:26)
# ─────────────────────────────────────────────────────────────────

def _uf(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pesos(x):
    return "$" + f"{int(round(x, -2)):,}".replace(",", ".")


def _n(n, singular, plural):
    return f"{n} {singular if n == 1 else plural}"


def texto_correo(r, uf_valor=None):
    """Las líneas del correo de Diego. Supone que nadie más usa las 27 valorizaciones de la base del plan."""
    hoy = r.get("pagadas_hoy", 0)
    mes_total = r.get("mes_total", hoy)
    antes = max(mes_total - hoy, 0)
    incluidas_hoy = max(0, min(BASE_PLAN, mes_total) - min(BASE_PLAN, antes))
    aparte_hoy = hoy - incluidas_hoy
    aparte_mes = max(0, mes_total - BASE_PLAN)
    mes = MESES[int(r["fecha"][5:7]) - 1]
    uf_valor = uf_valor or r.get("uf_usada")
    lineas = []
    principal = f"Hoy se {'hizo' if hoy == 1 else 'hicieron'} {_n(hoy, 'tasación', 'tasaciones')}. En {mes} van {mes_total}. "
    if aparte_hoy == 0:
        principal += (f"Todas las de hoy entran en la base de {BASE_PLAN} del plan, así que hoy no hay cobro aparte."
                      if hoy else "Hoy no hay cobro aparte.")
    else:
        costo = aparte_hoy * COSTO_UF
        principal += (f"Las primeras {BASE_PLAN} del mes entran en la base del plan y hoy {aparte_hoy} se cobra"
                      f"{'n' if aparte_hoy != 1 else ''} aparte. Costo de hoy {aparte_hoy} × 0,0371 = {_uf(costo)} UF más IVA")
        principal += f", unos {_pesos(costo * 1.19 * uf_valor)}." if uf_valor else "."
    lineas.append(principal)
    if aparte_mes:
        costo_mes = aparte_mes * COSTO_UF
        linea = f"En {mes} se {'cobra' if aparte_mes == 1 else 'cobran'} aparte {_n(aparte_mes, 'tasación', 'tasaciones')}, {_uf(costo_mes)} UF más IVA"
        lineas.append(linea + (f", unos {_pesos(costo_mes * 1.19 * uf_valor)}." if uf_valor else "."))
    otros = []
    if r.get("reutilizadas"):
        otros.append(f"{r['reutilizadas']} ya estaban tasadas y no se pagaron de nuevo")
    if r.get("sin_comparables"):
        otros.append(f"{r['sin_comparables']} sin ventas parecidas (no se cobran)")
    if r.get("fallas"):
        otros.append(f"{r['fallas']} con falla del servicio")
    if r.get("tope_alcanzado"):
        otros.append("se alcanzó el tope de tasaciones del día")
    if otros:
        lineas.append("Además, " + ", ".join(otros) + ".")
    return lineas
