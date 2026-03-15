"""
modulo1_mercurio.py  —  Extractor El Mercurio Digital
======================================================
Scraper de avisos de remates judiciales de propiedades (sección 1616) desde
El Mercurio Digital, usando Playwright + Claude Vision API.

CONTRATO DE DATOS  (interfaz con M2/M3/M5 — NO modificar)
----------------------------------------------------------
extraer_mercurio() retorna:
    list[ dict[str, Any] ] con claves exactas:
        rol, año, corte, tribunal, demandante, demandado,
        direccion, comuna, region_rm (siempre True)

Autor: generado automáticamente (Claude Sonnet 4.6)
Versión: 1.0  (2026-03-09)
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import anthropic
import openpyxl
from playwright.async_api import Page, async_playwright
from rapidfuzz import fuzz

# ---------------------------------------------------------------------------
# Importar config (credenciales / rutas / constantes)
# ---------------------------------------------------------------------------
try:
    from config import (
        ANTHROPIC_API_KEY,
        MERCURIO_USER,
        MERCURIO_PASS,
        MERCURIO_BASE_URL,
        CAPTURAS_DIR,
        PROCESADAS_DIR,
        CAUSAS_XLSX,          # ruta a causas_ojv.xlsx
    )
except ImportError as exc:
    raise SystemExit(
        "ERROR: config.py no encontrado o le faltan constantes requeridas.\n"
        "Asegúrate de definir: ANTHROPIC_API_KEY, MERCURIO_USER, MERCURIO_PASS, "
        "MERCURIO_BASE_URL, CAPTURAS_DIR, PROCESADAS_DIR, CAUSAS_XLSX\n"
        f"Detalle: {exc}"
    ) from exc

# ---------------------------------------------------------------------------
# Logger  (se configura con dual-logging en _setup_logging)
# ---------------------------------------------------------------------------
log = logging.getLogger("modulo1_mercurio")

_LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


class _LogFmt(logging.Formatter):
    """Formato: [HH:MM:SS] NIVEL — mensaje"""

    def format(self, record: logging.LogRecord) -> str:
        ts = time.strftime("%H:%M:%S", time.localtime(record.created))
        return f"[{ts}] {record.levelname} — {record.getMessage()}"


def _setup_logging() -> Path:
    """
    Configura dual-logging (consola + archivo) para modulo1_mercurio.
    Crea logs/ si no existe.
    Retorna la ruta del archivo de log creado.
    """
    os.makedirs(_LOGS_DIR, exist_ok=True)
    log_file = Path(_LOGS_DIR) / f"mercurio_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.log"

    # Limpiar handlers previos del logger de este módulo
    for h in log.handlers[:]:
        log.removeHandler(h)

    fmt = _LogFmt()

    console_h = logging.StreamHandler(
        open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
    )
    console_h.setFormatter(fmt)

    file_h = logging.FileHandler(str(log_file), encoding="utf-8")
    file_h.setFormatter(fmt)

    log.addHandler(console_h)
    log.addHandler(file_h)
    log.setLevel(logging.DEBUG)

    return log_file


# ---------------------------------------------------------------------------
# Estadísticas de ejecución
# ---------------------------------------------------------------------------
@dataclass
class _Stats:
    paginas_revisadas: int = 0
    paginas_con_1616: int = 0
    paginas_descartadas: int = 0
    pagina_parada: str = ""
    jpgs_capturados: int = 0
    avisos_vision: int = 0
    avisos_post_filtro: int = 0
    causas_nuevas: int = 0


def _log_resumen(stats: _Stats, *, dry_run: bool = False) -> None:
    """Imprime el bloque de resumen al final de la ejecución."""
    dr = " (dry run)" if dry_run else ""

    log.info("=" * 60)
    log.info("  RESUMEN EXTRACCIÓN MERCURIO DIGITAL%s", dr)
    log.info("=" * 60)
    log.info("  Páginas revisadas       : %d", stats.paginas_revisadas)
    log.info("  Descartadas (sin 1616)  : %d", stats.paginas_descartadas)
    log.info("  Conservadas (con 1616)  : %d", stats.paginas_con_1616)
    log.info("  Página de parada        : %s", stats.pagina_parada or "N/A")
    log.info("  JPGs capturados         : %d", stats.jpgs_capturados)
    if dry_run:
        log.info("  Avisos Vision           : — (dry run)")
        log.info("  Post-filtro             : — (dry run)")
        log.info("  Nuevos (no dup)         : — (dry run)")
    else:
        log.info("  Avisos Vision           : %d", stats.avisos_vision)
        log.info("  Post-filtro             : %d", stats.avisos_post_filtro)
        log.info("  Nuevos (no dup)         : %d", stats.causas_nuevas)
    log.info("=" * 60)


# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------
_UMBRAL_FUZZY_TRIBUNAL: int = 80          # RapidFuzz token_set_ratio threshold
_MAX_PAGINAS: int = 15                    # Tope de seguridad: máximas páginas a revisar
_CANVAS_HD_UMBRAL: int = 1800            # canvas.width > este valor → HD activo
_SECCIONES_MENORES = {"1611", "1612", "1613", "1614", "1615"}
_CORTES_RM = {"C.A. de Santiago", "C.A. de San Miguel"}
_BANCOS_ESTADO = {"banco estado", "banco del estado"}

# ---------------------------------------------------------------------------
# Prompt para Claude Vision API
# ---------------------------------------------------------------------------
PROMPT_EXTRACCION = """Analiza este texto extraído de la sección "1616 — Remates de propiedades" del diario El Mercurio.

El texto viene del visor PDF y puede tener palabras cortadas por guiones de salto de línea (ej: "Juzga-\ndo" = "Juzgado", "San-\ntiago" = "Santiago"). Reconstrúyelas.

Extrae TODOS los avisos de remates de propiedades. Para cada aviso, devuelve:

- "rol": número del ROL de la causa (solo el número, sin "C-"). Formato: "XXXXX"
- "año": año del ROL (los últimos 4 dígitos después del último guión en el formato C-XXXXX-YYYY). Formato: "YYYY"
- "tribunal": nombre completo del tribunal (ej: "1° Juzgado Civil de Santiago")
- "demandante": nombre del demandante/ejecutante (banco o persona)
- "demandado": nombre del demandado/ejecutado
- "direccion": dirección completa del inmueble rematado
- "comuna": comuna donde se ubica el inmueble
- "fecha_remate": fecha del remate si aparece (formato DD/MM/YYYY)

REGLAS:
1. NO inventar datos. Si un campo no es identificable en el texto, devolver null.
2. El ROL siempre aparece como "Rol C-XXXXX-YYYY" o "Rol: C-XXXXX-YYYY" o "rol C-XXXXX-YYYY". El número es XXXXX y el año es YYYY.
3. El tribunal es el JUZGADO que ordena el remate, NO la dirección del tribunal.
4. SOLO extraer avisos de la sección 1616 (Remates de propiedades). Ignorar secciones 1611, 1612, 1615 u otras.
5. Si un aviso está cortado (al inicio o final del texto), extraer lo visible con campos faltantes como null.

Responde ÚNICAMENTE con un JSON array válido. Sin texto explicativo, sin markdown, sin comentarios. Solo JSON puro."""


# ===========================================================================
# FUNCIONES DE POST-PROCESAMIENTO (adaptadas del proyecto base)
# ===========================================================================

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


def _cargar_causas_historico() -> set[str]:
    """
    Lee la hoja CAUSAS de causas_ojv.xlsx.
    Retorna set de ROLes ya procesados (formato "ROL-AÑO").
    """
    try:
        wb = openpyxl.load_workbook(CAUSAS_XLSX, read_only=True, data_only=True)
    except FileNotFoundError:
        return set()

    if "CAUSAS" not in wb.sheetnames:
        wb.close()
        return set()

    ws = wb["CAUSAS"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return set()

    header = [str(c).lower().strip() if c else "" for c in rows[0]]
    col_rol = col_anio = None
    for i, h in enumerate(header):
        if "rol" in h and col_rol is None:
            col_rol = i
        if ("año" in h or "anio" in h or "year" in h) and col_anio is None:
            col_anio = i

    if col_rol is None:
        col_rol = 0
    if col_anio is None:
        col_anio = 1

    historico: set[str] = set()
    for fila in rows[1:]:
        rol = fila[col_rol] if len(fila) > col_rol else None
        anio = fila[col_anio] if len(fila) > col_anio else None
        if rol:
            key = f"{str(rol).strip()}-{str(anio).strip()}" if anio else str(rol).strip()
            historico.add(key)

    log.debug("Histórico CAUSAS: %d entradas", len(historico))
    return historico


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


# ===========================================================================
# LÓGICA DE PLAYWRIGHT
# ===========================================================================

def _construir_url_cuerpo_a(fecha: date) -> str:
    return f"{MERCURIO_BASE_URL}/{fecha.year}/{fecha.month:02d}/{fecha.day:02d}/A"


async def _esta_logueado(page: Page) -> bool:
    """Verifica si ya hay una sesión activa (el botón de login no es visible)."""
    try:
        btn = page.locator("#openPram")
        visible = await btn.is_visible()
        if not visible:
            return True
        # También puede estar visible pero con texto distinto post-login
        texto = (await btn.inner_text()).strip()
        return "iniciar" not in texto.lower()
    except Exception:
        return False


async def _hacer_login(page: Page) -> None:
    """Realiza el flujo de login con las credenciales de config.py."""
    log.info("Iniciando login en El Mercurio Digital…")

    # Abrir modal de login
    await page.locator("#openPram > span").click()
    await page.wait_for_timeout(1000)

    # Rellenar usuario
    await page.locator("#txtUsername").fill(MERCURIO_USER)
    await page.wait_for_timeout(300)

    # Rellenar contraseña
    await page.locator("#txtPassword").fill(MERCURIO_PASS)
    await page.wait_for_timeout(300)

    # Click en "Ingrese acá"
    async with page.expect_navigation(timeout=30_000):
        await page.locator("#gopram").click()

    await page.wait_for_timeout(1500)

    # Secuencia post-login completa (Scraper_Mercurio.json):
    # Escape ×2 → click fuera de #modal_mer_promoLS → (click CLASIFICADOS viene después)
    log.debug("Cerrando modales post-login: Escape ×2")
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)

    # Click fuera de #modal_mer_promoLS (click en el overlay, fuera del contenido)
    try:
        promo = page.locator("#modal_mer_promoLS")
        if await promo.is_visible(timeout=3000):
            # Click en la esquina derecha del overlay (fuera del contenido del modal)
            box = await promo.bounding_box()
            if box:
                await page.mouse.click(box["x"] + box["width"] - 10, box["y"] + 10)
                log.debug("Click fuera de #modal_mer_promoLS para cerrarlo")
            else:
                await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)
    except Exception:
        pass

    # Verificar login exitoso
    if not await _esta_logueado(page):
        raise RuntimeError(
            "Login fallido: el botón de login sigue visible. "
            "Verifica MERCURIO_USER y MERCURIO_PASS en config.py."
        )
    log.info("Login exitoso.")


async def _cerrar_modales(page: Page) -> None:
    """
    Cierra modales que puedan aparecer al navegar por la edición.
    Para #modal_mer_promoLS y #modal_mer_selectHome, hace click fuera del modal
    (en el overlay) como en la secuencia grabada del Scraper_Mercurio.json.
    """
    # Escape ×2 primero (cierra modales genéricos)
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)

    # Modales específicos de El Mercurio — click fuera (en overlay)
    for modal_id in ["#modal_mer_promoLS", "#modal_mer_selectHome"]:
        try:
            modal = page.locator(modal_id)
            if await modal.is_visible(timeout=2000):
                box = await modal.bounding_box()
                if box:
                    # Click en la esquina derecha del overlay
                    await page.mouse.click(box["x"] + box["width"] - 10, box["y"] + 10)
                    log.debug("Cerrado modal %s (click fuera)", modal_id)
                else:
                    await page.keyboard.press("Escape")
                await page.wait_for_timeout(500)
        except Exception:
            pass

    # Fallback: cerrar cualquier modal Bootstrap restante
    for selector in [".modal.in .close", ".modal.show .close"]:
        try:
            elem = page.locator(selector).first
            if await elem.is_visible(timeout=1000):
                await elem.click()
                await page.wait_for_timeout(500)
        except Exception:
            pass


async def _navegar_a_sección_f(page: Page, fecha: date) -> None:
    """Desde cuerpo A, navega a la sección F (Clasificados)."""
    log.info("Navegando a sección F (Clasificados)…")

    # Hacer clic en botón CLASIFICADOS del header
    clasificados_btn = page.locator("#uctHeader_ctl02_rptBodyPart_ctl07_aBody")
    try:
        await clasificados_btn.wait_for(state="visible", timeout=15_000)
    except Exception:
        # Fallback: buscar por texto
        clasificados_btn = page.locator("text=CLASIFICADOS")

    async with page.expect_navigation(
        url=lambda u: "/F" in u or "/f" in u,
        timeout=15_000,
    ):
        await clasificados_btn.click()

    await page.wait_for_timeout(1500)
    await _cerrar_modales(page)
    log.debug("Sección F cargada: %s", page.url)


async def _obtener_ids_paginas_f(page: Page, fecha: date) -> list[str]:
    """
    Extrae la lista ordenada de IDs de página de la sección F desde el DOM.
    Retorna una lista de strings con los IDs en orden de página.
    """
    ids = await page.evaluate("""
    () => {
        // Buscar todos los enlaces con onclick="gotoPage('F', 'ID', NUM)"
        const pattern = /gotoPage\\s*\\(\\s*'F'\\s*,\\s*'([^']+)'\\s*,\\s*(\\d+)\\s*\\)/;
        const seen = new Map();
        const allElems = document.querySelectorAll('[onclick*="gotoPage"]');
        for (const el of allElems) {
            const oc = el.getAttribute('onclick') || '';
            const m = pattern.exec(oc);
            if (m) {
                const pageId = m[1];
                const pageNum = parseInt(m[2], 10);
                if (!seen.has(pageId)) {
                    seen.set(pageId, pageNum);
                }
            }
        }
        // Convertir a array y ordenar por número de página
        const arr = Array.from(seen.entries())
                         .map(([id, num]) => ({ id, num }))
                         .sort((a, b) => a.num - b.num)
                         .map(x => x.id);
        return arr;
    }
    """)
    log.debug("IDs de páginas F encontrados: %s", ids)
    return ids or []


async def _navegar_a_pagina(page: Page, fecha: date, page_id: str) -> None:
    """Navega directamente al visor de una página específica del cuerpo F."""
    url = (
        f"{MERCURIO_BASE_URL}/{fecha.year}/{fecha.month:02d}/{fecha.day:02d}"
        f"/F/{page_id}#zoom=page-width"
    )
    log.debug("Navegando a página F/%s  →  %s", page_id, url)
    await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
    await page.wait_for_timeout(2000)
    await _cerrar_modales(page)


async def _leer_texto_layer(page: Page, max_wait_ms: int = 10_000) -> str:
    """
    Lee el contenido de texto del .textLayer de la página actual.
    Espera hasta max_wait_ms a que el textLayer tenga contenido.
    """
    inicio = time.time()
    while (time.time() - inicio) < (max_wait_ms / 1000):
        try:
            texto = await page.evaluate("""
            () => {
                const tl = document.querySelector('.textLayer');
                return tl ? tl.innerText : '';
            }
            """)
            if texto and texto.strip():
                return texto
        except Exception as e:
            log.debug("Error leyendo textLayer: %s", e)
        await page.wait_for_timeout(500)
    log.debug("textLayer vacío tras esperar %d ms", max_wait_ms)
    return ""


def _detectar_secciones(texto: str) -> list[str]:
    """Detecta las secciones numéricas presentes en el textLayer."""
    buscar = ["1611", "1612", "1613", "1614", "1615", "1616"]
    return [s for s in buscar if s in texto]


async def _esperar_canvas_base(page: Page, timeout_ms: int = 15_000) -> bool:
    """Espera a que el canvas exista y tenga width > 0 (renderizado base)."""
    try:
        await page.wait_for_function(
            "document.querySelector('canvas#page1')?.width > 0"
            " || document.querySelector('#viewer canvas')?.width > 0",
            timeout=timeout_ms,
        )
        ancho = await page.evaluate("""
        () => {
            const c = document.querySelector('canvas#page1') ||
                      document.querySelector('#viewer canvas');
            return c ? c.width : 0;
        }
        """)
        log.debug("Canvas base renderizado: width=%d", ancho)
        return True
    except Exception as e:
        log.warning("Timeout esperando canvas base (width>0): %s", e)
        return False


async def _click_hd_btn(page: Page) -> bool:
    """Intenta clickear el botón HD. Retorna True si se hizo click."""
    try:
        hd_btn = page.locator("div.toolbar div.cont_activar_pdf > span:nth-of-type(1) img").first
        if await hd_btn.is_visible(timeout=5000):
            await hd_btn.click()
            log.debug("Botón HD clickeado (selector toolbar).")
            return True
        hd_btn2 = page.locator("#inactive_pdf img").first
        if await hd_btn2.is_visible(timeout=3000):
            await hd_btn2.click()
            log.debug("Botón HD clickeado (fallback #inactive_pdf).")
            return True
        log.warning("Botón HD no visible con ningún selector.")
        return False
    except Exception as e:
        log.warning("No se pudo clickear botón HD: %s", e)
        return False


async def _activar_hd(page: Page) -> None:
    """
    Activa el modo HD del visor:
    1. Espera a que canvas base renderice (width > 0)
    2. Toma screenshot de diagnóstico
    3. Clickea botón HD
    4. Si canvas sigue en 0 tras 5s, reintenta click
    """
    # 1. Esperar canvas base
    log.debug("Esperando a que canvas base renderice (width > 0)…")
    canvas_ok = await _esperar_canvas_base(page)
    if not canvas_ok:
        log.warning("Canvas base no renderizó; intentando HD de todas formas.")

    # 2. Screenshot de diagnóstico
    diag_path = os.path.join(_LOGS_DIR, "pre_hd_click.png")
    try:
        await page.screenshot(path=diag_path)
        log.info("Screenshot pre-HD guardado: %s", diag_path)
    except Exception as e:
        log.warning("No se pudo tomar screenshot pre-HD: %s", e)

    # 3. Primer click HD
    clicked = await _click_hd_btn(page)
    if not clicked:
        return

    # 4. Verificar si canvas reacciona; si sigue en 0, reintentar
    await page.wait_for_timeout(5000)
    try:
        ancho = await page.evaluate("""
        () => {
            const c = document.querySelector('canvas#page1') ||
                      document.querySelector('#viewer canvas');
            return c ? c.width : 0;
        }
        """)
        if ancho == 0:
            log.warning("Canvas sigue en width=0 tras primer click HD; reintentando click…")
            await _click_hd_btn(page)
        else:
            log.debug("Canvas post-HD click: width=%d", ancho)
    except Exception:
        pass


async def _esperar_canvas_hd(page: Page, timeout_ms: int = 20_000) -> bool:
    """
    Espera a que el canvas renderice en HD (width > 1800).
    Loguea el estado del canvas cada 2 segundos.
    Retorna True si se alcanzó HD, False si se agotó el timeout.
    """
    inicio = time.time()
    timeout_s = timeout_ms / 1000
    ultimo_log = 0.0

    while True:
        elapsed = time.time() - inicio
        if elapsed >= timeout_s:
            break

        try:
            ancho = await page.evaluate("""
            () => {
                const canvas = document.querySelector('canvas#page1') ||
                               document.querySelector('#viewer canvas');
                return canvas ? canvas.width : 0;
            }
            """)
            if ancho and int(ancho) > _CANVAS_HD_UMBRAL:
                log.debug("Canvas HD detectado: width=%d (%.0fs/%.0fs)", ancho, elapsed, timeout_s)
                return True

            # Log cada 2 segundos
            if elapsed - ultimo_log >= 2.0:
                log.debug("Esperando HD: canvas.width=%d (%.0fs/%.0fs)", ancho or 0, elapsed, timeout_s)
                ultimo_log = elapsed
        except Exception:
            pass
        await page.wait_for_timeout(500)

    # Log final
    try:
        ancho_final = await page.evaluate("""
        () => {
            const canvas = document.querySelector('canvas#page1') ||
                           document.querySelector('#viewer canvas');
            return canvas ? canvas.width : 0;
        }
        """)
        log.warning(
            "Timeout esperando HD (canvas.width=%d, umbral=%d). "
            "Capturando en resolución disponible.",
            ancho_final, _CANVAS_HD_UMBRAL,
        )
    except Exception:
        pass
    return False


async def _capturar_canvas(page: Page) -> bytes | None:
    """
    Captura el canvas del visor como JPEG (calidad 0.80).
    Si el resultado base64 supera 5MB, redimensiona al 80% y reintenta.
    Retorna bytes del JPG, o None si falla.
    """
    _MAX_B64 = 5 * 1024 * 1024  # 5 MB límite Vision API

    try:
        # Primer intento: calidad 0.80
        data_url = await page.evaluate("""
        () => {
            const canvas = document.querySelector('canvas#page1') ||
                           document.querySelector('#viewer canvas');
            if (!canvas) return null;
            return canvas.toDataURL('image/jpeg', 0.80);
        }
        """)
        if not data_url or not data_url.startswith("data:image"):
            return None

        _, encoded = data_url.split(",", 1)
        b64_size = len(encoded)
        log.debug(
            "Imagen base64: %d bytes (%.1f MB), límite 5MB",
            b64_size, b64_size / 1024 / 1024,
        )

        if b64_size <= _MAX_B64:
            return base64.b64decode(encoded)

        # Fallback: redimensionar canvas al 80% y exportar
        log.warning(
            "Imagen supera 5MB (%.1f MB), redimensionando canvas al 80%%…",
            b64_size / 1024 / 1024,
        )
        data_url = await page.evaluate("""
        () => {
            const canvas = document.querySelector('canvas#page1') ||
                           document.querySelector('#viewer canvas');
            if (!canvas) return null;
            const scale = 0.80;
            const w = Math.round(canvas.width * scale);
            const h = Math.round(canvas.height * scale);
            const tmp = document.createElement('canvas');
            tmp.width = w;
            tmp.height = h;
            const ctx = tmp.getContext('2d');
            ctx.drawImage(canvas, 0, 0, w, h);
            return tmp.toDataURL('image/jpeg', 0.80);
        }
        """)
        if not data_url or not data_url.startswith("data:image"):
            return None
        _, encoded = data_url.split(",", 1)
        log.debug(
            "Imagen redimensionada base64: %d bytes (%.1f MB)",
            len(encoded), len(encoded) / 1024 / 1024,
        )
        return base64.b64decode(encoded)
    except Exception as e:
        log.warning("Error capturando canvas: %s", e)
        return None


def _guardar_captura(imagen_bytes: bytes, fecha: date, numero: int) -> Path:
    """Guarda la imagen en Capturas/ con el nombre estándar."""
    directorio = Path(CAPTURAS_DIR)
    directorio.mkdir(parents=True, exist_ok=True)
    nombre = f"mercurio_{fecha.isoformat()}_p{numero}.jpg"
    ruta = directorio / nombre
    ruta.write_bytes(imagen_bytes)
    log.info("Imagen guardada: %s (%d KB)", ruta, len(imagen_bytes) // 1024)
    return ruta


def _mover_a_procesadas(ruta_captura: Path) -> None:
    """Mueve una imagen de Capturas/ a Procesadas/."""
    directorio = Path(PROCESADAS_DIR)
    directorio.mkdir(parents=True, exist_ok=True)
    destino = directorio / ruta_captura.name
    shutil.move(str(ruta_captura), str(destino))
    log.debug("Imagen movida a Procesadas/: %s", destino)


# ===========================================================================
# VISION API
# ===========================================================================

def _enviar_texto_a_claude(page_id: str, texto: str, reintentos: int = 1) -> list[dict[str, Any]]:
    """
    Envía texto del textLayer a Claude Text API (Sonnet) y retorna avisos extraídos.
    Reintenta una vez en caso de fallo. Retorna [] si no se puede parsear.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    log.info(
        "Enviando texto pág %s a Claude API (%d caracteres)",
        page_id, len(texto),
    )

    contenido = PROMPT_EXTRACCION + "\n\n---\nTEXTO DE LA PÁGINA:\n" + texto

    for intento in range(reintentos + 1):
        try:
            log.info(
                "Claude API pág %s (intento %d/%d)",
                page_id, intento + 1, reintentos + 1,
            )
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": contenido,
                }],
            )
            texto_respuesta = "".join(
                bloque.text for bloque in response.content if hasattr(bloque, "text")
            )
            log.debug("Respuesta Claude (primeros 200 chars): %s", texto_respuesta[:200])
            return _parsear_json_vision(texto_respuesta)

        except Exception as e:
            log.warning("Error en Claude API (intento %d): %s", intento + 1, e)
            if intento < reintentos:
                time.sleep(5)

    log.error("Claude API falló tras %d intentos para pág %s", reintentos + 1, page_id)
    return []


def _parsear_json_vision(texto: str) -> list[dict[str, Any]]:
    """
    Parsea la respuesta de Vision API.
    Usa raw_decode para tolerar texto extra antes/después del JSON.
    """
    texto = texto.strip()
    # Quitar bloques de código markdown si los hay
    texto = re.sub(r"^```(?:json)?\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"```\s*$", "", texto, flags=re.MULTILINE)
    texto = texto.strip()

    decoder = json.JSONDecoder()
    # Buscar primer '[' para arrays
    idx = texto.find("[")
    if idx == -1:
        log.warning("Respuesta Vision no contiene array JSON: %s", texto[:200])
        return []
    try:
        resultado, _ = decoder.raw_decode(texto, idx)
        if isinstance(resultado, list):
            return resultado
    except json.JSONDecodeError as e:
        log.warning("JSON inválido en respuesta Vision: %s — texto: %s", e, texto[:300])

    return []


# ===========================================================================
# POST-PROCESAMIENTO
# ===========================================================================

def _normalizar_aviso(raw: dict[str, Any]) -> dict[str, Any] | None:
    """
    Normaliza y valida un aviso crudo de Vision API.
    Retorna dict con el contrato de datos, o None si el aviso es inválido.
    """
    rol_raw = str(raw.get("rol") or "").strip()
    año = str(raw.get("año") or "").strip()
    tribunal_raw = raw.get("tribunal") or raw.get("juzgado")
    demandante = str(raw.get("demandante") or "").strip() or None
    demandado = str(raw.get("demandado") or "").strip() or None
    direccion = str(raw.get("direccion") or "").strip() or None
    comuna = str(raw.get("comuna") or "").strip() or None

    # Extraer año del ROL si viene en formato C-XXXXX-YYYY o XXXXX-YYYY
    rol = rol_raw.lstrip("Cc-").strip()
    if not año:
        # Intentar separar "12345-2024" → rol=12345, año=2024
        m = re.match(r"^(\d+)-(\d{4})$", rol)
        if m:
            rol, año = m.group(1), m.group(2)
            log.debug("Año extraído del ROL: %s → rol=%s, año=%s", rol_raw, rol, año)
        else:
            # Intentar desde rol_raw: "C-12345-2024"
            m = re.match(r"^[Cc]-?(\d+)-(\d{4})$", rol_raw)
            if m:
                rol, año = m.group(1), m.group(2)
                log.debug("Año extraído del ROL completo: %s → rol=%s, año=%s", rol_raw, rol, año)

    # Validaciones mínimas: ROL es obligatorio
    if not rol:
        log.debug("Aviso descartado por falta de ROL: %s", raw)
        return None
    if not re.match(r"^\d+$", rol):
        log.debug("ROL no numérico, descartando: %s", rol)
        return None

    # Si año sigue vacío, advertir pero dejar pasar para que M2 intente completar
    if not año:
        log.warning("Aviso sin AÑO (se envía a M2 para completar): rol=%s, raw=%s", rol, raw)

    # Limpiar nombre de tribunal
    tribunal_limpio = _limpiar_tribunal(str(tribunal_raw).strip() if tribunal_raw else None)

    # Mapear tribunal → corte
    corte = buscar_corte(tribunal_limpio) if tribunal_limpio else None

    return {
        "rol": rol,
        "año": año,
        "corte": corte or "",
        "tribunal": tribunal_limpio or "",
        "demandante": demandante or "",
        "demandado": demandado or "",
        "direccion": direccion,
        "comuna": comuna,
        "region_rm": True,
    }


def _filtrar_avisos(
    avisos: list[dict[str, Any]],
    historico: set[str],
    vistos_en_ejecucion: set[str],
) -> list[dict[str, Any]]:
    """
    Aplica todos los filtros del negocio a la lista de avisos normalizados.
    Modifica vistos_en_ejecucion in-place para deduplicar entre páginas.
    Loggea conteo antes/después por cada filtro.
    """
    total_entrada = len(avisos)
    desc_rm = desc_banco = desc_anio = desc_hist = desc_dup = 0

    resultado = []
    for aviso in avisos:
        rol = aviso["rol"]
        año = aviso["año"]
        key = f"{rol}-{año}"

        # Filtro 1: Solo RM
        corte = aviso.get("corte", "")
        if corte not in _CORTES_RM:
            desc_rm += 1
            log.debug("  Descartado (no RM): ROL %s, corte='%s'", rol, corte)
            continue

        # Filtro 2: Banco Estado
        demandante_lower = (aviso.get("demandante") or "").lower()
        if any(b in demandante_lower for b in _BANCOS_ESTADO):
            desc_banco += 1
            log.debug("  Descartado (Banco Estado): ROL %s", rol)
            continue

        # Filtro 3: Año >= 2018
        try:
            if int(año) < 2018:
                desc_anio += 1
                log.debug("  Descartado (pre-2018): ROL %s, año %s", rol, año)
                continue
        except ValueError:
            desc_anio += 1
            log.debug("  Año no parseable, descartando: %s", año)
            continue

        # Filtro 4: Dedup contra historial CAUSAS
        if key in historico:
            desc_hist += 1
            log.debug("  Descartado (ya en historial): ROL %s-%s", rol, año)
            continue

        # Filtro 5: Dedup entre páginas de la misma ejecución
        if key in vistos_en_ejecucion:
            desc_dup += 1
            log.debug("  Descartado (duplicado en ejecución): ROL %s-%s", rol, año)
            continue

        vistos_en_ejecucion.add(key)
        resultado.append(aviso)

    # Resumen de filtros
    log.info("Filtro Solo RM        : %d → %d (-%d)",
             total_entrada, total_entrada - desc_rm, desc_rm)
    post_rm = total_entrada - desc_rm
    log.info("Filtro Banco Estado   : %d → %d (-%d)",
             post_rm, post_rm - desc_banco, desc_banco)
    post_banco = post_rm - desc_banco
    log.info("Filtro Año >= 2018    : %d → %d (-%d)",
             post_banco, post_banco - desc_anio, desc_anio)
    post_anio = post_banco - desc_anio
    log.info("Filtro Historial CAUSAS: %d → %d (-%d)",
             post_anio, post_anio - desc_hist, desc_hist)
    post_hist = post_anio - desc_hist
    log.info("Filtro Dup ejecución  : %d → %d (-%d)",
             post_hist, post_hist - desc_dup, desc_dup)
    log.info("Resultado final filtrado: %d de %d avisos pasan", len(resultado), total_entrada)

    return resultado


# ===========================================================================
# FUNCIÓN PRINCIPAL ASYNC
# ===========================================================================

async def _extraer_mercurio_async(
    fecha: date, *, dry_run: bool = False
) -> list[dict[str, Any]]:
    """
    Núcleo async del extractor. Abre Playwright, navega el diario, captura
    páginas 1616 y las envía a Vision API.

    Si dry_run=True, ejecuta solo la navegación (login, sección F, detección de
    páginas 1616 y captura de imágenes) pero NO envía nada a Vision API.
    """
    log_file = _setup_logging()
    st = _Stats()

    log.info("=== Inicio extracción El Mercurio Digital ===")
    log.info("Fecha edición: %s | dry_run: %s", fecha.isoformat(), dry_run)
    log.info("Log file: %s", log_file)

    historico = _cargar_causas_historico()
    log.info("Histórico CAUSAS cargado: %d entradas", len(historico))
    vistos_en_ejecucion: set[str] = set()
    todas_las_causas: list[dict[str, Any]] = []
    capturas_realizadas: list[Path] = []
    paginas_texto: list[tuple[str, str, Path | None]] = []  # [(page_id, texto_completo, ruta_jpg)]

    async with async_playwright() as pw:
        profile_dir = str(Path(CAPTURAS_DIR).parent / "playwright_profile")
        log.info("Lanzando Chromium headless (perfil: %s)", profile_dir)
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            viewport={"width": 1990, "height": 1279},
            java_script_enabled=True,
            accept_downloads=False,
        )
        page = context.pages[0] if context.pages else await context.new_page()

        try:
            # ---------------------------------------------------------------
            # Paso 1: Abrir Cuerpo A
            # ---------------------------------------------------------------
            url_a = _construir_url_cuerpo_a(fecha)
            log.info("[Paso 1/6] Navegando a cuerpo A: %s", url_a)
            await page.goto(url_a, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(2000)
            log.info("[Paso 1/6] Cuerpo A cargado OK")

            # ---------------------------------------------------------------
            # Paso 2: Login si es necesario
            # ---------------------------------------------------------------
            log.info("[Paso 2/6] Verificando sesión…")
            if not await _esta_logueado(page):
                log.info("[Paso 2/6] Sesión no activa — iniciando login")
                await _hacer_login(page)
                log.info("[Paso 2/6] Login completado OK")
            else:
                log.info("[Paso 2/6] Sesión activa detectada, omitiendo login")

            # Siempre cerrar modales antes de navegar (login o no)
            await _cerrar_modales(page)

            # ---------------------------------------------------------------
            # Paso 3: Navegar a sección F
            # ---------------------------------------------------------------
            log.info("[Paso 3/6] Navegando de cuerpo A -> sección F (Clasificados)")
            await _navegar_a_sección_f(page, fecha)
            log.info("[Paso 3/6] Sección F cargada OK: %s", page.url)

            # ---------------------------------------------------------------
            # Paso 4: Obtener lista de IDs de páginas
            # ---------------------------------------------------------------
            log.info("[Paso 4/6] Obteniendo mapa de páginas de sección F")
            ids_paginas = await _obtener_ids_paginas_f(page, fecha)
            if len(ids_paginas) < 2:
                log.error(
                    "[Paso 4/6] Insuficientes IDs de páginas F (encontrados: %d). "
                    "Posible error de carga o edición no disponible. Abortando.",
                    len(ids_paginas),
                )
                _log_resumen(st, dry_run=dry_run)
                return []

            log.info("[Paso 4/6] Páginas F encontradas: %d — inicio en penúltima (índice %d)",
                     len(ids_paginas), len(ids_paginas) - 2)
            indice_inicio = len(ids_paginas) - 2

            # ---------------------------------------------------------------
            # Paso 5: Navegar a penúltima página y activar HD (una sola vez)
            # ---------------------------------------------------------------
            penultima_id = ids_paginas[indice_inicio]
            log.info("[Paso 5/6] Navegando a penúltima página %s para activar HD", penultima_id)
            await _navegar_a_pagina(page, fecha, penultima_id)

            log.info("Activando modo HD (una sola vez para toda la sesión)…")
            await _activar_hd(page)
            hd_ok = await _esperar_canvas_hd(page, timeout_ms=20_000)
            if hd_ok:
                log.info("Canvas HD confirmado (width > %d). HD queda activo para toda la sesión.", _CANVAS_HD_UMBRAL)
            else:
                log.warning("HD no confirmado, continuando con resolución disponible.")
            await page.wait_for_timeout(2000)  # buffer post-renderizado

            # ---------------------------------------------------------------
            # Paso 6: Loop retroceder desde penúltima (tope 15 páginas)
            # ---------------------------------------------------------------
            log.info("[Paso 6/6] Iniciando recorrido hacia atrás (máx %d páginas)", _MAX_PAGINAS)
            numero_captura = 1
            indice_actual = indice_inicio

            while st.paginas_revisadas < _MAX_PAGINAS and indice_actual >= 0:
                page_id = ids_paginas[indice_actual]
                st.paginas_revisadas += 1
                log.info(
                    "--- Página %s (índice %d/%d, revisada #%d) ---",
                    page_id, indice_actual + 1, len(ids_paginas), st.paginas_revisadas,
                )

                # Navegar (salvo la primera iteración, ya estamos en penúltima)
                if indice_actual != indice_inicio:
                    try:
                        await _navegar_a_pagina(page, fecha, page_id)
                    except Exception as e:
                        log.warning("Error navegando a página %s: %s — saltando", page_id, e)
                        indice_actual -= 1
                        continue

                # Buffer de 2s antes de capturar (HD ya está activo)
                await page.wait_for_timeout(2000)

                # Capturar canvas como JPG
                imagen_bytes = await _capturar_canvas(page)
                ruta_captura_tmp: Path | None = None
                if imagen_bytes:
                    ruta_captura_tmp = _guardar_captura(imagen_bytes, fecha, numero_captura)

                # Leer textLayer completo
                texto_layer = await _leer_texto_layer(page)
                log.debug(
                    "textLayer pág %s (300 chars): \"%s\"",
                    page_id, texto_layer[:300].replace("\n", "\\n"),
                )

                # Detectar secciones
                secciones = _detectar_secciones(texto_layer)
                log.debug("Secciones detectadas en pág %s: %s", page_id, secciones)

                contiene_1616 = "1616" in secciones
                tiene_menor = bool(set(secciones) & _SECCIONES_MENORES)

                # Decisión
                if not contiene_1616:
                    # No contiene 1616 → borrar JPG, retroceder, continuar
                    log.info(
                        "Pág %s: contiene 1616=No, sección menor=N/A → acción: descartar",
                        page_id,
                    )
                    st.paginas_descartadas += 1
                    if ruta_captura_tmp and ruta_captura_tmp.exists():
                        ruta_captura_tmp.unlink()
                        log.debug("JPG descartado: %s", ruta_captura_tmp.name)
                elif contiene_1616 and not tiene_menor:
                    # Contiene 1616 sin sección menor → conservar, continuar
                    log.info(
                        "Pág %s: contiene 1616=Sí, sección menor=No → acción: conservar",
                        page_id,
                    )
                    st.paginas_con_1616 += 1
                    if ruta_captura_tmp:
                        capturas_realizadas.append(ruta_captura_tmp)
                        st.jpgs_capturados += 1
                        log.info(
                            "Captura #%d guardada: %s (%d KB)",
                            numero_captura, ruta_captura_tmp.name,
                            len(imagen_bytes) // 1024 if imagen_bytes else 0,
                        )
                        numero_captura += 1
                    paginas_texto.append((page_id, texto_layer, ruta_captura_tmp))
                else:
                    # Contiene 1616 Y sección menor → conservar y PARAR
                    log.info(
                        "Pág %s: contiene 1616=Sí, sección menor=Sí (%s) → acción: PARAR (inicio de 1616)",
                        page_id, [s for s in secciones if s in _SECCIONES_MENORES],
                    )
                    st.paginas_con_1616 += 1
                    st.pagina_parada = page_id
                    if ruta_captura_tmp:
                        capturas_realizadas.append(ruta_captura_tmp)
                        st.jpgs_capturados += 1
                        log.info(
                            "Captura #%d guardada: %s (%d KB)",
                            numero_captura, ruta_captura_tmp.name,
                            len(imagen_bytes) // 1024 if imagen_bytes else 0,
                        )
                        numero_captura += 1
                    paginas_texto.append((page_id, texto_layer, ruta_captura_tmp))
                    break  # PARAR

                indice_actual -= 1

            # Log de condición de parada
            if st.pagina_parada:
                log.info("Parada: inicio de sección 1616 detectado en página %s", st.pagina_parada)
            elif st.paginas_revisadas >= _MAX_PAGINAS:
                log.warning("Tope de seguridad alcanzado: %d páginas revisadas", _MAX_PAGINAS)
            elif indice_actual < 0:
                log.warning("Se llegó al inicio de la sección F sin encontrar inicio de 1616")

        except Exception as e:
            log.error("Error crítico durante la navegación: %s", e, exc_info=True)
        finally:
            await context.close()
            log.info("Navegador cerrado")

    # -----------------------------------------------------------------------
    # Paso 7 & 8: Procesar capturas con Vision API (saltar si dry_run)
    # -----------------------------------------------------------------------
    if dry_run:
        log.info("[Paso 7/8] OMITIDO (dry run) — Claude API no invocada")
        log.info("[Paso 8/8] OMITIDO (dry run) — Filtrado y dedup no aplicados")
        log.info(
            "DRY RUN completado: %d capturas guardadas en %s",
            len(capturas_realizadas), CAPTURAS_DIR,
        )
        _log_resumen(st, dry_run=True)
        return []

    log.info("[Paso 7/8] Procesando %d páginas con Claude Text API", len(paginas_texto))

    avisos_normalizados_total: list[dict[str, Any]] = []

    for i, (page_id, texto, ruta_jpg) in enumerate(paginas_texto, 1):
        log.info("Procesando página %d/%d: %s", i, len(paginas_texto), page_id)
        avisos_raw = _enviar_texto_a_claude(page_id, texto)
        st.avisos_vision += len(avisos_raw)
        log.info(
            "Claude retornó %d avisos para pág %s",
            len(avisos_raw), page_id,
        )

        for raw in avisos_raw:
            aviso_normalizado = _normalizar_aviso(raw)
            if aviso_normalizado is not None:
                avisos_normalizados_total.append(aviso_normalizado)

        # Mover JPG a Procesadas/ (respaldo)
        if ruta_jpg and ruta_jpg.exists():
            _mover_a_procesadas(ruta_jpg)
            log.info("Imagen movida a Procesadas/: %s", ruta_jpg.name)

    log.info("[Paso 8/8] Aplicando filtros a %d avisos normalizados", len(avisos_normalizados_total))
    todas_las_causas = _filtrar_avisos(avisos_normalizados_total, historico, vistos_en_ejecucion)
    st.avisos_post_filtro = len(todas_las_causas)
    st.causas_nuevas = len(todas_las_causas)

    log.info("=== Extracción completada: %d causas nuevas ===", len(todas_las_causas))
    _log_resumen(st)
    return todas_las_causas


# ===========================================================================
# API PÚBLICA
# ===========================================================================

def extraer_mercurio(
    fecha: date | str | None = None,
    *,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """
    Extrae avisos de remates judiciales de propiedades (sección 1616) desde
    El Mercurio Digital para la fecha indicada (por defecto: hoy).

    Parámetros
    ----------
    fecha : date | str | None
        Fecha de la edición a procesar. Acepta:
        - None → hoy (date.today())
        - date object
        - str en formato "YYYY-MM-DD"
    dry_run : bool
        Si True, ejecuta solo navegación y captura (sin Vision API).

    Retorna
    -------
    list[dict]
        Lista de causas con las claves del contrato de datos:
        rol, año, corte, tribunal, demandante, demandado,
        direccion, comuna, region_rm (siempre True)
    """
    if fecha is None:
        fecha_obj = date.today()
    elif isinstance(fecha, str):
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    else:
        fecha_obj = fecha

    return asyncio.run(_extraer_mercurio_async(fecha_obj, dry_run=dry_run))


# ===========================================================================
# CLI: permite ejecutar directamente  python modulo1_mercurio.py [--fecha YYYY-MM-DD]
# ===========================================================================

if __name__ == "__main__":
    import argparse, pprint

    parser = argparse.ArgumentParser(
        description="Extractor El Mercurio Digital — sección 1616 Remates de propiedades"
    )
    parser.add_argument(
        "--fecha",
        type=str,
        default=None,
        help="Fecha de la edición a procesar (YYYY-MM-DD). Por defecto: hoy.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo navegación y captura de imágenes (sin llamar a Vision API).",
    )
    args = parser.parse_args()

    causas = extraer_mercurio(fecha=args.fecha, dry_run=args.dry_run)
    print(f"\n{'='*60}")
    print(f"CAUSAS EXTRAÍDAS: {len(causas)}")
    print("="*60)
    pprint.pprint(causas, width=120)
