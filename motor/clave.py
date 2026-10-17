"""Llave de deduplicación de causas (rol-año|tribunal) y la limpieza del nombre del tribunal que usa.

Movidas sin cambios de lógica desde modulo1_mercurio.py el 17 de Octubre de 2026 (etapa B del traspaso), para que el
motor nuevo las use sin cargar el navegador. modulo1_mercurio.py las importa con los mismos nombres, así
modulo5_reporte.py sigue haciendo "from modulo1_mercurio import _clave_causa" y la llave tiene UNA sola fuente.
Regla inamovible. La llave es siempre rol-año más tribunal (commit 2fabb84, choque real 7030-2024 entre el 6° y el 29°).
"""
from __future__ import annotations

import logging
import re

log = logging.getLogger("modulo1_mercurio")    # mismo logger que antes, los mensajes van al mismo log


def _limpiar_tribunal(nombre: str | None) -> str | None:
    """
    Normaliza el nombre de un tribunal:
    - Une guiones silábicos (ej: "Juzga-\ndo" → "Juzgado")
    - Elimina fragmentos de dirección física
    - Normaliza mayúsculas/minúsculas
    """
    if not nombre:
        return None
    # Unir palabras partidas por guion al final de línea
    texto = re.sub(r"-\s*\n\s*", "", nombre)
    # Limpiar saltos de línea y espacios múltiples
    texto = re.sub(r"\s+", " ", texto).strip()
    # Eliminar texto entre paréntesis (a veces contiene dirección)
    texto = re.sub(r"\(.*?\)", "", texto).strip()
    # Capitalización básica: primera letra mayúscula en cada token relevante
    # (No alterar ordinales: 1°, 2°, etc.)
    texto = re.sub(r"\s{2,}", " ", texto)
    return texto


# ── Normalizador de ordinal de tribunal ──
def _normalizar_ordinal_tribunal(nombre: str | None) -> str | None:
    """
    Normaliza el ordinal escrito de un nombre de tribunal a formato "N°".
    Ej: "Primer Juzgado Civil de Santiago" → "1° Juzgado Civil de Santiago".
    Si ya es numérico o no tiene ordinal reconocible, deja intacto.
    """
    if not nombre:
        return nombre

    # Si ya tiene formato numérico con °, no tocar
    if re.search(r'\b\d+\s*[°º]', nombre):
        return nombre

    # Diccionario plano 1-30: clave → reemplazo "N°"
    # Incluye todas las variantes de género, apócope, con/sin tilde.
    ORDINALES_MAP = {
        # ── 30 ──
        "trigésimo": "30°", "trigesimo": "30°",
        "trigésima": "30°", "trigesima": "30°",
        # ── 29 ──
        "vigésimo noveno":  "29°", "vigesimo noveno":  "29°",
        "vigésima novena":  "29°", "vigesima novena":  "29°",
        # ── 28 ──
        "vigésimo octavo":  "28°", "vigesimo octavo":  "28°",
        "vigésima octava":  "28°", "vigesima octava":  "28°",
        # ── 27 ──
        "vigésimo séptimo": "27°", "vigesimo septimo": "27°",
        "vigésima séptima": "27°", "vigesima septima": "27°",
        # ── 26 ──
        "vigésimo sexto":   "26°", "vigesimo sexto":   "26°",
        "vigésima sexta":   "26°", "vigesima sexta":   "26°",
        # ── 25 ──
        "vigésimo quinto":  "25°", "vigesimo quinto":  "25°",
        "vigésima quinta":  "25°", "vigesima quinta":  "25°",
        # ── 24 ──
        "vigésimo cuarto":  "24°", "vigesimo cuarto":  "24°",
        "vigésima cuarta":  "24°", "vigesima cuarta":  "24°",
        # ── 23 ──
        "vigésimo tercero": "23°", "vigesimo tercero": "23°",
        "vigésimo tercer":  "23°", "vigesimo tercer":  "23°",
        "vigésima tercera": "23°", "vigesima tercera": "23°",
        # ── 22 ──
        "vigésimo segundo": "22°", "vigesimo segundo": "22°",
        "vigésima segunda": "22°", "vigesima segunda": "22°",
        # ── 21 ──
        "vigésimo primero": "21°", "vigesimo primero": "21°",
        "vigésimo primer":  "21°", "vigesimo primer":  "21°",
        "vigésima primera": "21°", "vigesima primera": "21°",
        # ── 20 ──
        "vigésimo": "20°", "vigesimo": "20°",
        "vigésima": "20°", "vigesima": "20°",
        # ── 19 ──
        "décimo noveno":    "19°", "decimo noveno":    "19°",
        "décima novena":    "19°", "decima novena":    "19°",
        "decimonoveno":     "19°", "decimonovena":     "19°",
        # ── 18 ──
        "décimo octavo":    "18°", "decimo octavo":    "18°",
        "décima octava":    "18°", "decima octava":    "18°",
        "decimoctavo":      "18°", "decimoctava":      "18°",
        # ── 17 ──
        "décimo séptimo":   "17°", "decimo septimo":   "17°",
        "décima séptima":   "17°", "decima septima":   "17°",
        "decimoséptimo":    "17°", "decimoseptimo":    "17°",
        "decimoséptima":    "17°", "decimoseptima":    "17°",
        # ── 16 ──
        "décimo sexto":     "16°", "decimo sexto":     "16°",
        "décima sexta":     "16°", "decima sexta":     "16°",
        "decimosexto":      "16°", "decimosexta":      "16°",
        # ── 15 ──
        "décimo quinto":    "15°", "decimo quinto":    "15°",
        "décima quinta":    "15°", "decima quinta":    "15°",
        "decimoquinto":     "15°", "decimoquinta":     "15°",
        # ── 14 ──
        "décimo cuarto":    "14°", "decimo cuarto":    "14°",
        "décima cuarta":    "14°", "decima cuarta":    "14°",
        "decimocuarto":     "14°", "decimocuarta":     "14°",
        # ── 13 ──
        "décimo tercero":   "13°", "decimo tercero":   "13°",
        "décimo tercer":    "13°", "decimo tercer":    "13°",
        "décima tercera":   "13°", "decima tercera":   "13°",
        "decimotercero":    "13°", "decimotercer":     "13°",
        "decimotercera":    "13°",
        # ── 12 ──
        "décimo segundo":   "12°", "decimo segundo":   "12°",
        "décima segunda":   "12°", "decima segunda":   "12°",
        "duodécimo":        "12°", "duodecimo":        "12°",
        "duodécima":        "12°", "duodecima":        "12°",
        "decimosegundo":    "12°", "decimosegunda":    "12°",
        # ── 11 ──
        "décimo primero":   "11°", "decimo primero":   "11°",
        "décimo primer":    "11°", "decimo primer":    "11°",
        "décima primera":   "11°", "decima primera":   "11°",
        "undécimo":         "11°", "undecimo":         "11°",
        "undécima":         "11°", "undecima":         "11°",
        "decimoprimero":    "11°", "decimoprimer":     "11°",
        "decimoprimera":    "11°",
        # ── 10 ──
        "décimo": "10°", "decimo": "10°",
        "décima": "10°", "decima": "10°",
        # ── 9 ──
        "noveno": "9°", "novena": "9°",
        # ── 8 ──
        "octavo": "8°", "octava": "8°",
        # ── 7 ──
        "séptimo": "7°", "septimo": "7°",
        "séptima": "7°", "septima": "7°",
        # ── 6 ──
        "sexto": "6°", "sexta": "6°",
        # ── 5 ──
        "quinto": "5°", "quinta": "5°",
        # ── 4 ──
        "cuarto": "4°", "cuarta": "4°",
        # ── 3 ──
        "tercero": "3°", "tercer": "3°",
        "tercera": "3°",
        # ── 2 ──
        "segundo": "2°", "segunda": "2°",
        # ── 1 ──
        "primero": "1°", "primer": "1°",
        "primera": "1°",
    }

    # Recorrer de mayor a menor longitud de clave para evitar colisiones de
    # subcadenas (ej: "décimo tercer" debe procesarse antes que "tercer").
    resultado = nombre
    for escrito in sorted(ORDINALES_MAP.keys(), key=len, reverse=True):
        patron = r'\b' + re.escape(escrito) + r'\b'
        resultado, n = re.subn(patron, ORDINALES_MAP[escrito], resultado, flags=re.IGNORECASE)
        if n > 0:
            break

    return resultado


def _clave_causa(rol, anio, tribunal) -> str:
    """Llave de dedup: rol-año|tribunal canónico. Si no hay tribunal,
    degrada a rol-año (comportamiento legado, con registro en log)."""
    base = f"{str(rol).strip()}-{str(anio).strip()}" if anio else str(rol).strip()
    t = (tribunal or "").strip()
    if not t:
        log.debug("Llave de dedup sin tribunal (degradada a rol-año): %s", base)
        return base
    # Mismo orden del post-proceso de avisos: limpiar → normalizar ordinal
    t = _limpiar_tribunal(t) or ""
    t = _normalizar_ordinal_tribunal(t) or ""
    t = " ".join(t.split()).lower()          # colapsar espacios + minúsculas
    if not t:
        log.debug("Llave de dedup sin tribunal (degradada a rol-año): %s", base)
        return base
    return f"{base}|{t}"
