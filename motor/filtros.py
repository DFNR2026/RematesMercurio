"""Filtros de negocio del Mercurio sobre las causas del motor nuevo (etapa C del traspaso, 17 de Octubre de 2026).

Primera parte. Funciones movidas SIN cambios de lógica desde modulo1_mercurio.py (corte del tribunal con RapidFuzz 80 y la
hoja REFERENCIA, comunas de la RM con umbral 88, año de dominio con el corte 2020 de filtro_cbr.py).
Segunda parte. aplicar(), con las reglas de Diego del 17 de Octubre.
- Una hilera por causa (rol-año más tribunal). Mismo tribunal y roles distintos son hileras distintas.
- Más de 5 propiedades en el rol. No se aplica el filtro de dominio. El rol entra si al menos una propiedad está en la RM.
- 5 o menos. Cada propiedad pasa si su comuna está en la RM (y no es Estación Central) y su dominio es anterior a 2020.
  El rol se descarta solo si TODAS fallan. Si algunas pasan, entran solo esas y las otras se anotan en Observaciones.
- Salvaguarda. Un dato que no se pudo leer nunca descarta. La causa queda en la tabla principal con su observación, marcada
  para revisar, y no se escribe en el historial CAUSAS (así vuelve a salir hasta quedar completa).
- Observaciones en palabras simples, para que el abogado entienda qué pasó sin tecnicismos.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

import openpyxl
from rapidfuzz import fuzz

from filtro_cbr import _CBR_ANIO_CORTE
from motor.clave import _limpiar_tribunal

log = logging.getLogger("modulo1_mercurio")
try:
    from config import CAUSAS_XLSX
except Exception:                                     # pruebas sin config.py
    CAUSAS_XLSX = str(Path(__file__).resolve().parent.parent / "causas_ojv.xlsx")


# =====================================================================================================================
# PRIMERA PARTE. Movido sin cambios desde modulo1_mercurio.py
# =====================================================================================================================
_UMBRAL_FUZZY_TRIBUNAL: int = 80          # RapidFuzz token_set_ratio threshold
_CORTES_RM = {"C.A. de Santiago", "C.A. de San Miguel"}
_BANCOS_ESTADO = {"banco estado", "banco del estado"}
_COMUNAS_EXCLUIDAS = {"estación central", "estacion central"}

_CBR_ANIO_MIN = 1900
_CBR_ANIO_MAX = 2027

def _extraer_ordinal(texto: str) -> int | None:
    """
    Extrae el número ordinal de un nombre de tribunal.
    Ej: "1° Juzgado Civil de Santiago" → 1
    Ej: "Decimocuarto Juzgado Civil" → 14
    """
    numerales = {
        "primer": 1, "primero": 1, "primera": 1,
        "segundo": 2, "segunda": 2,
        "tercero": 3, "tercera": 3, "tercer": 3,
        "cuarto": 4, "cuarta": 4,
        "quinto": 5, "quinta": 5,
        "sexto": 6, "sexta": 6,
        "séptimo": 7, "septimo": 7, "séptima": 7,
        "octavo": 8, "octava": 8,
        "noveno": 9, "novena": 9,
        "décimo": 10, "decimo": 10, "décima": 10,
        "decimoprimero": 11, "decimoprimer": 11, "undécimo": 11,
        "decimosegundo": 12, "duodécimo": 12,
        "decimotercero": 13, "decimotercer": 13,
        "decimocuarto": 14,
        "decimoquinto": 15,
        "decimosexto": 16,
        "decimoséptimo": 17, "decimoseptimo": 17,
        "decimoctavo": 18,
        "decimonoveno": 19,
        "vigésimo": 20, "vigesimo": 20,
    }
    texto_lower = texto.lower()
    # Número arábigo con símbolo ordinal
    m = re.search(r"(\d+)\s*[°ºª]", texto)
    if m:
        return int(m.group(1))
    # Número arábigo solo al inicio
    m = re.search(r"^(\d+)\s+", texto)
    if m:
        return int(m.group(1))
    # Numeral escrito
    for palabra, num in numerales.items():
        if palabra in texto_lower:
            return num
    return None

def _cargar_referencia_tribunales() -> list[dict[str, str]]:
    """
    Lee la hoja REFERENCIA de causas_ojv.xlsx.
    Retorna lista de dicts con claves: nombre_tribunal, corte.
    """
    try:
        wb = openpyxl.load_workbook(CAUSAS_XLSX, read_only=True, data_only=True)
    except FileNotFoundError:
        log.warning("causas_ojv.xlsx no encontrado en %s — buscar_corte deshabilitado", CAUSAS_XLSX)
        return []

    if "REFERENCIA" not in wb.sheetnames:
        log.warning("Hoja REFERENCIA no encontrada en %s", CAUSAS_XLSX)
        wb.close()
        return []

    ws = wb["REFERENCIA"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return []

    # Detectar encabezado: buscar columnas que contengan "tribunal" y "corte"
    header = [str(c).lower().strip() if c else "" for c in rows[0]]
    col_tribunal = next((i for i, h in enumerate(header) if "tribunal" in h), None)
    col_corte = next((i for i, h in enumerate(header) if "corte" in h), None)
    if col_tribunal is None or col_corte is None:
        log.warning(
            "Columnas tribunal/corte no encontradas en REFERENCIA (header=%s). "
            "Usando col_tribunal=%s, col_corte=%s",
            header, col_tribunal, col_corte,
        )
        col_tribunal = col_tribunal if col_tribunal is not None else 1
        col_corte = col_corte if col_corte is not None else 0
    log.debug("REFERENCIA columnas: tribunal=%d, corte=%d (header=%s)", col_tribunal, col_corte, header)

    resultado = []
    for fila in rows[1:]:
        nombre = fila[col_tribunal] if len(fila) > col_tribunal else None
        corte = fila[col_corte] if len(fila) > col_corte else None
        if nombre and corte:
            resultado.append({
                "nombre_tribunal": str(nombre).strip(),
                "corte": str(corte).strip(),
            })
    log.debug("REFERENCIA cargada: %d tribunales", len(resultado))
    return resultado

_referencia_cache: list[dict[str, str]] | None = None

def buscar_corte(nombre_tribunal: str) -> str | None:
    """
    Busca la corte de apelaciones correspondiente a un tribunal usando RapidFuzz.
    Umbral: token_set_ratio >= 80, con validación ordinal post-matching.
    Retorna nombre de corte, o None si no se encuentra.
    """
    global _referencia_cache
    if _referencia_cache is None:
        _referencia_cache = _cargar_referencia_tribunales()

    if not _referencia_cache or not nombre_tribunal:
        return None

    nombre_limpio = _limpiar_tribunal(nombre_tribunal) or nombre_tribunal
    ordinal_query = _extraer_ordinal(nombre_limpio)

    mejor_score = 0
    mejor_corte = None
    mejor_tribunal = None

    for entry in _referencia_cache:
        score = fuzz.token_set_ratio(nombre_limpio.lower(), entry["nombre_tribunal"].lower())
        if score > mejor_score:
            mejor_score = score
            mejor_corte = entry["corte"]
            mejor_tribunal = entry["nombre_tribunal"]

    fuzzy_ok = True
    if mejor_score < _UMBRAL_FUZZY_TRIBUNAL:
        log.debug("Tribunal no encontrado (score=%d): %s", mejor_score, nombre_limpio)
        fuzzy_ok = False

    # Validación ordinal: si ambos tienen ordinal, deben coincidir
    if fuzzy_ok and ordinal_query is not None and mejor_tribunal is not None:
        ordinal_match = _extraer_ordinal(mejor_tribunal)
        if ordinal_match is not None and ordinal_query != ordinal_match:
            log.debug(
                "Ordinal mismatch (query=%d, match=%d) para: %s",
                ordinal_query, ordinal_match, nombre_limpio,
            )
            fuzzy_ok = False

    # Mercurio (17 de Octubre de 2026). Si el tribunal nombra una localidad de la RM y el elegido por el fuzzy no la nombra,
    # manda la localidad. La hoja REFERENCIA no tiene Colina y "Juzgado de Letras de Colina" calzaba 95,8 con "Juzgado de
    # Letras de Molina" (Corte de Talca). El rol 1962-2023 del 14 de Octubre se descartaba como "Solo RM".
    if fuzzy_ok and mejor_tribunal is not None:
        for kw in ("san miguel", "san bernardo", "puente alto", "buin", "talagante", "colina", "melipilla", "peñaflor"):
            if kw in nombre_limpio.lower() and kw not in mejor_tribunal.lower():
                log.debug("Localidad '%s' no calza con '%s'. Se usa la lista de localidades", kw, mejor_tribunal)
                fuzzy_ok = False
                break

    if fuzzy_ok:
        log.debug("Tribunal '%s' → corte '%s' (score=%d)", nombre_limpio, mejor_corte, mejor_score)
        return mejor_corte

    # Fallback: asignación directa por nombre de localidad
    nombre_lower = nombre_limpio.lower()
    _SAN_MIGUEL_KEYWORDS = (
        "san miguel", "san bernardo", "puente alto", "buin",
        "talagante", "colina", "melipilla", "peñaflor",
    )
    for kw in _SAN_MIGUEL_KEYWORDS:
        if kw in nombre_lower:
            log.debug("Fallback corte por nombre: '%s' → 'C.A. de San Miguel'", nombre_limpio)
            return "C.A. de San Miguel"
    if "santiago" in nombre_lower:
        log.debug("Fallback corte por nombre: '%s' → 'C.A. de Santiago'", nombre_limpio)
        return "C.A. de Santiago"

    log.debug("Tribunal sin corte (fuzzy ni fallback): %s", nombre_limpio)
    return None

# ---------------------------------------------------------------------------
# Clasificación de comunas de la Región Metropolitana
# ---------------------------------------------------------------------------

# Las 52 comunas de la RM, agrupadas por provincia.
_COMUNAS_RM = [
    # Provincia de Santiago (32)
    "Cerrillos", "Cerro Navia", "Conchalí", "El Bosque", "Estación Central",
    "Huechuraba", "Independencia", "La Cisterna", "La Florida", "La Granja",
    "La Pintana", "La Reina", "Las Condes", "Lo Barnechea", "Lo Espejo",
    "Lo Prado", "Macul", "Maipú", "Ñuñoa", "Pedro Aguirre Cerda",
    "Peñalolén", "Providencia", "Pudahuel", "Quilicura", "Quinta Normal",
    "Recoleta", "Renca", "San Joaquín", "San Miguel", "San Ramón",
    "Santiago", "Vitacura",
    # Provincia de Chacabuco (3)
    "Colina", "Lampa", "Tiltil",
    # Provincia de Cordillera (3)
    "Puente Alto", "Pirque", "San José de Maipo",
    # Provincia de Maipo (4)
    "San Bernardo", "Buin", "Calera de Tango", "Paine",
    # Provincia de Melipilla (5)
    "Melipilla", "Alhué", "Curacaví", "María Pinto", "San Pedro",
    # Provincia de Talagante (5)
    "Talagante", "El Monte", "Isla de Maipo", "Padre Hurtado", "Peñaflor",
]

# Umbral de coincidencia difusa. Alto a propósito: a 80 se confunden pares
# como "San Rafael" (Maule) con "San Ramón" (RM).
_UMBRAL_COMUNA = 88


def _normalizar_comuna(texto: str) -> str:
    """Minúsculas, sin tildes, sin espacios sobrantes."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFD", str(texto))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(t.lower().split())


_COMUNAS_RM_NORM = {_normalizar_comuna(c): c for c in _COMUNAS_RM}


def _evaluar_comuna_rm(comuna: str | None) -> tuple[bool, str]:
    """Decide si la propiedad está en la Región Metropolitana.

    Retorna (es_rm, observacion). La observación se muestra en el Excel y
    explica por qué una causa dudosa se mantuvo en la tabla principal.

    Salvaguarda: si la comuna no viene en el aviso, la causa NO se descarta.
    Perder una causa buena es peor que mostrar una de más.
    """
    if not comuna or not str(comuna).strip():
        return (True, "Sin comuna en el aviso — se mantiene para revisión manual")

    original = str(comuna).strip()
    norm = _normalizar_comuna(original)

    # Coincidencia exacta
    if norm in _COMUNAS_RM_NORM:
        return (True, "")

    # Campo con varias comunas separadas por coma o barra
    if "," in original or "/" in original:
        partes = [p.strip() for p in original.replace("/", ",").split(",") if p.strip()]
        for p in partes:
            if _normalizar_comuna(p) in _COMUNAS_RM_NORM:
                return (True, f"Comuna múltiple '{original}': contiene '{p}', de la RM — se mantiene")

    # Coincidencia difusa contra las 52
    mejor, mejor_score = None, 0
    for cn, cd in _COMUNAS_RM_NORM.items():
        score = fuzz.ratio(norm, cn)
        if score > mejor_score:
            mejor, mejor_score = cd, score
    if mejor_score >= _UMBRAL_COMUNA:
        return (True, f"Comuna '{original}' asimilada a '{mejor}' (coincidencia {mejor_score:.0f}%)")

    return (False, "")

def _evaluar_cbr_por_anio(anio_raw) -> dict:
    """
    Decide CBR a partir del año de inscripción del dominio que devolvió la IA.
    No usa regex sobre texto; opera sobre el año ya extraído.
    """
    if anio_raw is None or str(anio_raw).strip() == "":
        return {"decision": "REVISAR", "cbr_anio": None,
                "cbr_flag_revision": True, "cbr_motivo": "Año CBR no detectado"}
    m = re.search(r"\b(\d{4})\b", str(anio_raw))
    if not m:
        return {"decision": "REVISAR", "cbr_anio": None,
                "cbr_flag_revision": True, "cbr_motivo": "Año CBR no detectado"}
    anio = int(m.group(1))
    if not (_CBR_ANIO_MIN <= anio <= _CBR_ANIO_MAX):
        return {"decision": "REVISAR", "cbr_anio": None,
                "cbr_flag_revision": True, "cbr_motivo": "Año CBR fuera de rango"}
    if anio >= _CBR_ANIO_CORTE:
        return {"decision": "EXCLUIR", "cbr_anio": anio,
                "cbr_flag_revision": False, "cbr_motivo": ""}
    return {"decision": "MANTENER", "cbr_anio": anio,
            "cbr_flag_revision": False, "cbr_motivo": ""}


# =====================================================================================================================
# SEGUNDA PARTE. Reglas de Diego del 17 de Octubre de 2026
# =====================================================================================================================
MAX_PROPIEDADES_CON_FILTRO = 5          # más de 5 propiedades en el rol, sin filtro de dominio
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_palabras(f: str) -> str:
    """'2026-10-17' da '17 de octubre del 2026' (formato pedido por Diego el 17 de Octubre)."""
    a, m, d = f[:10].split("-")
    return f"{int(d)} de {_MESES[int(m) - 1]} del {a}"


def _huella(t: str) -> str:
    return re.sub(r"[\W_]+", "", (t or "").lower())


# --- Carátula partida en demandante y demandado ---------------------------------------------------------------------
_SEP_CARATULA = re.compile(r"\s+con\s+|\s*/\s*|\s+contra\s+", re.I)


def partir_caratula(caratula: str | None) -> tuple[str, str]:
    """'Banco de Chile con Aguilera' da ('Banco de Chile', 'Aguilera'). Sin separador va completa en demandante."""
    if not caratula:
        return "", ""
    partes = _SEP_CARATULA.split(caratula.strip(), maxsplit=1)
    if len(partes) == 2 and partes[0].strip() and partes[1].strip():
        return partes[0].strip(), partes[1].strip()
    return caratula.strip(), ""


# --- Observaciones en palabras simples --------------------------------------------------------------------------------
OBS_TRIBUNAL = "No se pudo leer el tribunal en el aviso. Revisar en el diario."
OBS_CORTE = "No se pudo saber a qué Corte pertenece el tribunal. Revisar."
OBS_DIRECCION = "No se pudo comprobar la dirección. Revisar el aviso en el diario."
OBS_SIN_DIRECCION = "El aviso no indica la dirección de la propiedad."
OBS_CARATULA = "No se pudo leer la carátula (demandante y demandado). Revisar en el diario."
OBS_DOMINIO = "No se encontró el año de inscripción del dominio. Revisar si es anterior a 2020."
OBS_COMUNA = "El aviso no indica la comuna de la propiedad. Revisar."
# (patrón de la alerta técnica, texto para el abogado, ¿obliga a revisar?)
_TRADUCCION = [
    (r"^Dirección no leída|^Falla de la IA", OBS_DIRECCION, True),
    (r"^La IA no encontró la dirección", OBS_SIN_DIRECCION, False),
    (r"tribunal", OBS_TRIBUNAL, True),
    (r"carátula", OBS_CARATULA, True),
    (r"^Corte del aviso dudoso", "El aviso podría estar cortado o mezclado con otro. Revisar en el diario.", True),
    (r"roles distintos", "El aviso trae dos números de rol distintos. Confirmar cuál es el correcto.", True),
    (r"imprime este rol distinto", "El rol aparece escrito distinto en dos partes del diario. Revisar.", True),
    (r"inscripción del inmueble dice año", "El año de inscripción del aviso parece mal escrito. Revisar.", True),
    (r"solo aparece en el cuerpo", None, False),           # aviso que sale en un solo cuerpo del viernes. Normal
]


def traducir_alerta(t: str) -> tuple[str | None, bool]:
    for patron, texto, revisa in _TRADUCCION:
        if re.search(patron, t, re.I):
            return texto, revisa
    return "Hay una duda en la lectura de este aviso. Revisar en el diario.", True


# --- Propiedades de una causa -----------------------------------------------------------------------------------------
def _anios(lista: list) -> list:
    out = []
    for x in lista:
        try:
            out.append(int(str(x.get("anio")).replace(".", "")))
        except (TypeError, ValueError):
            pass
    return out


def propiedades(causa: dict) -> list:
    """Una propiedad por remate de cada aviso, sin repetir las republicaciones (misma huella del texto del aviso).
    Cada una con su dirección y comuna (si Haiku la verificó), los años y las fojas de su inscripción.
    Inscripción. Si el aviso trae un remate, son todas las del aviso (un depto y su bodega pueden tener dos). Si trae
    varios y la cantidad de inscripciones calza, una por remate en orden. Si no calza, todas las del aviso para cada uno."""
    out, vistos = [], set()
    for av in causa["avisos"]:
        h = _huella(av["texto"])
        n = av["n_remates"]
        insc = av.get("inscripciones") or []
        dirs = av.get("direcciones")
        for i in range(n):
            if (h, i) in vistos:
                continue
            vistos.add((h, i))
            mia = [insc[i]] if n > 1 and len(insc) == n else insc
            d = dirs[i] if dirs and i < len(dirs) else None
            out.append({"direccion": (d or {}).get("direccion"), "comuna": (d or {}).get("comuna"),
                        "dir_ok": av.get("dir_color") == "verde", "anios": _anios(mia),
                        "fojas": [x["fojas"] for x in mia if x.get("fojas")], "aviso": av})
    # La misma dirección verificada en dos avisos distintos del mismo rol es la misma propiedad
    unicas, dirs_vistas = [], set()
    for p in out:
        k = (p["direccion"] or "").lower().strip()
        if k and k in dirs_vistas:
            continue
        if k:
            dirs_vistas.add(k)
        unicas.append(p)
    return unicas


def _cbr(p: dict) -> tuple[str, int | None]:
    """('pasa'|'falla'|'sin_dato', año). Pasa si algún año conocido es anterior a 2020. Falla si todos son 2020 o más."""
    validos = [a for a in p["anios"] if _CBR_ANIO_MIN <= a <= _CBR_ANIO_MAX]
    if not validos:
        return "sin_dato", None
    if any(a < _CBR_ANIO_CORTE for a in validos):
        return "pasa", min(validos)
    return "falla", max(validos)


def _comuna(p: dict) -> tuple[bool, str]:
    """(pasa, motivo si no pasa). Salvaguarda. Sin comuna o comuna dudosa, pasa (decisión del 6 de Agosto)."""
    c = (p.get("comuna") or "").strip()
    if c.lower() in _COMUNAS_EXCLUIDAS:
        return False, "Estación Central"
    es_rm, _obs = _evaluar_comuna_rm(c or None)
    return (True, "") if es_rm else (False, f"Propiedad fuera de RM: {c}")


def _roles_impresos(texto: str) -> list:
    from motor.cortador import roles_en
    return [(r[1], r[2]) for r in roles_en(texto)]


def _unir(textos):
    vistos, out = set(), []
    for t in textos:
        if t and t.lower() not in vistos:
            vistos.add(t.lower()); out.append(t)
    return " / ".join(out)


# --- Reparto en las tablas del Excel ------------------------------------------------------------------------------------
def aplicar(resultados: list, historico: set, corte_de=None) -> dict:
    """resultados = salidas de motor.edicion.procesar() (una por edición). historico = llaves de la hoja CAUSAS.
    Devuelve {principal, excluidas_cbr, descartados, sin_rol, en_historial} con el formato que espera M5."""
    corte_de = corte_de or buscar_corte
    causas = {}
    for res in resultados:
        for c in res["causas"]:
            u = causas.setdefault(c["clave"], {**c, "avisos": [], "alertas": []})
            u["avisos"] += c["avisos"]
            u["caratula"] = u.get("caratula") or c.get("caratula")
            u["alertas"] += [a for a in c["alertas"] if a not in u["alertas"]]
    principal, excluidas, descartados, en_historial = [], [], [], 0
    for c in causas.values():
        if c["clave"] in historico:
            en_historial += 1
            log.debug("  Ya en historial: ROL %s-%s — %s", c["rol"], c["año"], c["tribunal"])
            continue
        rol, anio, tribunal = c["rol"], c["año"], c["tribunal"]
        base = {"rol": rol, "año": anio, "tribunal": tribunal}
        obs, revisar = [], False
        for a in c["alertas"]:
            t, r = traducir_alerta(a)
            if t and t not in obs:
                obs.append(t)
            revisar = revisar or (r and t is not None)
        # 0. Salvaguarda (17 de Octubre). Un trozo con dos roles que el cortador no pudo separar puede traer DOS avisos
        #    pegados. Nunca se descarta, porque el segundo aviso se perdería en silencio (16-10, el 1442-2024 de Buin
        #    llevaba pegado el 1177-2025 de Viña del Mar). Va a la tabla principal con todas sus direcciones, para revisar.
        if any("roles distintos en un mismo trozo" in a for a in c["alertas"]):
            roles = sorted({f"{r[0]}-{r[1]}" for av in c["avisos"] for r in _roles_impresos(av["texto"])})
            props = propiedades(c)
            dem, ddo = partir_caratula(c.get("caratula") or "")
            principal.append({**base, "corte": (corte_de(tribunal) or "") if tribunal else "", "demandante": dem, "demandado": ddo,
                              "direccion": _unir(p["direccion"] for p in props), "comuna": _unir(p["comuna"] for p in props),
                              "fojas": _unir(f for p in props for f in p["fojas"]),
                              "observaciones": f"Este aviso venía pegado a otro (roles {' y '.join(roles)}) y el programa no pudo "
                                               "separarlos. Revisar ambos en el diario. No se le aplicaron los filtros.",
                              "revisar": True, "region_rm": True, "n_propiedades": len(props), "cbr_anio": None,
                              "ediciones": sorted({av.get("edicion", "") for av in c["avisos"]} - {""})})
            continue
        # 1. Corte (solo RM). Tribunal no leído o corte desconocida, la causa se queda con su observación.
        corte = ""
        if not tribunal:
            if OBS_TRIBUNAL not in obs:
                obs.append(OBS_TRIBUNAL)
            revisar = True
        else:
            corte = corte_de(tribunal) or ""
            if not corte:
                obs.append(OBS_CORTE); revisar = True
            elif corte not in _CORTES_RM:
                descartados.append({**base, "motivo": "Solo RM", "monto": None}); continue
        # 2. Banco Estado, sobre la carátula entera
        caratula = c.get("caratula") or ""
        if any(b in caratula.lower() for b in _BANCOS_ESTADO):
            descartados.append({**base, "motivo": "Banco Estado", "monto": None}); continue
        # 3. Año del rol desde 2018
        try:
            if int(anio) < 2018:
                descartados.append({**base, "motivo": "Pre-2018", "monto": None}); continue
        except (TypeError, ValueError):
            obs.append("No se pudo leer el año del rol. Revisar."); revisar = True
        # 4. Comuna y dominio por propiedad
        props = propiedades(c)
        n = len(props)
        evaluadas = []
        for p in props:
            ok_c, mot_c = _comuna(p)
            est, a_cbr = _cbr(p)
            evaluadas.append((p, ok_c, mot_c, est, a_cbr))
        if n > MAX_PROPIEDADES_CON_FILTRO:
            pasan = [e for e in evaluadas if e[1]]
            if pasan:
                pasan = evaluadas            # el rol entra con todas sus direcciones
                obs.insert(0, f"Rol con {n} propiedades. No se aplicó el filtro de dominio.")
        else:
            pasan = [e for e in evaluadas if e[1] and e[3] != "falla"]
        if not pasan:
            if all(e[1] for e in evaluadas) and n <= MAX_PROPIEDADES_CON_FILTRO:
                excluidas.append({**base, "cbr_anio": max(e[4] for e in evaluadas)})
            else:
                motivos = sorted({e[2] for e in evaluadas if e[2]})
                motivo = motivos[0] if len(motivos) == 1 else "Todas sus propiedades quedan fuera de los filtros"
                descartados.append({**base, "motivo": motivo, "monto": None})
            continue
        fuera = [e for e in evaluadas if e not in pasan]
        if fuera:
            det = [f"dominio {e[4]}" if e[1] else e[2].replace("Propiedad fuera de RM: ", "fuera de la RM, ") for e in fuera]
            obs.append(f"{len(fuera)} propiedad{'es' if len(fuera) > 1 else ''} excluida{'s' if len(fuera) > 1 else ''} de este rol ({'; '.join(det)}).".replace(";", ","))
        if n <= MAX_PROPIEDADES_CON_FILTRO and any(e[3] == "sin_dato" for e in pasan):
            obs.append(OBS_DOMINIO); revisar = True
        if any(e[0]["dir_ok"] and not (e[0]["comuna"] or "").strip() for e in pasan):
            obs.append(OBS_COMUNA); revisar = True
        dem, ddo = partir_caratula(caratula)
        anios_ok = [e[4] for e in pasan if e[4]]
        principal.append({**base, "corte": corte, "demandante": dem, "demandado": ddo,
                          "direccion": _unir(e[0]["direccion"] for e in pasan),
                          "comuna": _unir(e[0]["comuna"] for e in pasan),
                          "fojas": _unir(f for e in pasan for f in e[0]["fojas"]),
                          "observaciones": " ".join(obs), "revisar": revisar, "region_rm": True,
                          "n_propiedades": len(pasan), "cbr_anio": min(anios_ok) if anios_ok else None,
                          "ediciones": sorted({av.get("edicion", "") for av in c["avisos"]} - {""})})
    sin_rol, por_huella = [], {}
    for res in resultados:
        for av in res["sin_rol"]:
            h = _huella(av["texto"])
            if h in por_huella:          # el mismo aviso republicado otro día va una sola vez, con sus otras fechas
                por_huella[h]["_otras"].append(res["fecha"])
                continue
            d = av.get("direcciones") or []
            sin_rol.append({"tribunal": av.get("tribunal") or "", "caratula": av.get("caratula") or "",
                            "direccion": _unir(x.get("direccion") for x in d), "comuna": _unir(x.get("comuna") for x in d),
                            "pagina": f"{', '.join(av.get('paginas') or [])} ({fecha_palabras(res['fecha'])})",
                            "motivo": "El aviso no trae número de rol impreso. Revisar en el diario.", "_otras": []})
            por_huella[h] = sin_rol[-1]
    for s in sin_rol:
        otras = s.pop("_otras")
        if otras:
            s["pagina"] += ". Se repite el " + ", ".join(fecha_palabras(f) for f in otras)
    return {"principal": principal, "excluidas_cbr": excluidas, "descartados": descartados, "sin_rol": sin_rol,
            "en_historial": en_historial}
