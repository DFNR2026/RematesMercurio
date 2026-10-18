"""
modulo1_mercurio.py  —  Lectura de El Mercurio Digital (M1), motor nuevo
=========================================================================
Traspaso del 17 de Octubre de 2026. El motor de lectura construido y probado en D:\\Agendar_Remates reemplaza a la lectura
vieja (una página a la vez enviada a DeepSeek). DeepSeek sale entero del programa (decisión de Diego). La IA es Claude Haiku
y solo lee la dirección y la comuna, con la frase exacta comprobada por código.

Flujo por edición.
1. motor.lector_mercurio. Entra al diario en modo HD, revisa TODOS los cuerpos del día y toma toda página con la cornisa
   "1616 Remates de propiedades", siguiendo las flechas "MÁS AVISOS... EN PÁG./PÁGINA". Guarda el texto en capturas\\FECHA.
2. motor.edicion. Une las páginas en un solo rollo, corta por aviso con código, elimina los partidores, extrae tribunal,
   inscripción y carátula por código, pide la dirección a Haiku y agrupa por causa (rol-año más tribunal).
3. motor.filtros. Une las ediciones del lote y reparte en las tablas del Excel con las reglas de negocio.

API pública (la usan main.py y modulo5_reporte.py, no cambiar los nombres).
    extraer_mercurio(fecha | [fechas], dry_run=False, usar_captura=False) -> list[dict]   causas de la tabla principal
    obtener_metricas() -> dict        tablas extra, tokens, costo y fallos de la última corrida
    EdicionNoDisponible               ninguna edición pedida está publicada
    _clave_causa                      llave de dedup (definida en motor/clave.py, M5 la importa desde aquí)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl

from motor.clave import _clave_causa, _limpiar_tribunal, _normalizar_ordinal_tribunal  # llave de dedup, una sola fuente
from motor import filtros as F
from motor.edicion import procesar, paginas_desde_captura

try:
    from config import CAUSAS_XLSX
except ImportError as exc:
    raise SystemExit(
        "ERROR: config.py no encontrado o le faltan constantes requeridas.\n"
        "Asegúrate de definir: ANTHROPIC_API_KEY, MERCURIO_USER, MERCURIO_PASS, MERCURIO_BASE_URL, CAUSAS_XLSX\n"
        f"Detalle: {exc}"
    ) from exc


class EdicionNoDisponible(Exception):
    """La edición solicitada no está publicada en El Mercurio Digital."""


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


def _cargar_causas_historico() -> set[str]:
    """
    Lee la hoja CAUSAS de causas_ojv.xlsx.
    Retorna set de llaves ya procesadas (formato "ROL-AÑO|tribunal").
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
    col_rol = col_anio = col_trib = None
    for i, h in enumerate(header):
        if "rol" in h and col_rol is None:
            col_rol = i
        if ("año" in h or "anio" in h or "year" in h) and col_anio is None:
            col_anio = i
        if "tribunal" in h and col_trib is None:
            col_trib = i

    if col_rol is None:
        col_rol = 0
    if col_anio is None:
        col_anio = 1

    historico: set[str] = set()
    for fila in rows[1:]:
        rol = fila[col_rol] if len(fila) > col_rol else None
        anio = fila[col_anio] if len(fila) > col_anio else None
        tribunal = fila[col_trib] if col_trib is not None and len(fila) > col_trib else None
        if rol:
            historico.add(_clave_causa(rol, anio, tribunal))

    log.debug("Histórico CAUSAS: %d entradas", len(historico))
    return historico


def _cliente_haiku():
    """Cliente de Haiku con la clave de config.py, o (None, motivo) si no se puede crear. Nunca imprime la clave."""
    try:
        from motor.ia_comun import cliente_desde_config
        return cliente_desde_config(), None
    except Exception as e:
        return None, f"No se pudo preparar la inteligencia artificial ({type(e).__name__})."


def _como_fecha(f) -> date:
    if isinstance(f, date):
        return f
    return datetime.strptime(str(f), "%Y-%m-%d").date()


def _leer(fecha: date, usar_captura: bool) -> dict:
    """Lee la edición con el lector (o usa la captura ya guardada si se pide). Devuelve el informe del lector."""
    from motor.lector_mercurio import CAPTURAS
    nav = CAPTURAS / fecha.isoformat() / "navegacion.json"
    if usar_captura and nav.exists():
        log.info("Usando la captura guardada de %s (no se vuelve a leer el diario)", fecha.isoformat())
        return json.loads(nav.read_text(encoding="utf-8"))
    from motor.lector_mercurio import leer_edicion
    return asyncio.run(leer_edicion(fecha))


# Textos en palabras simples para el abogado (decisión de Diego del 17 de Octubre)
def _fallo_pagina(alarma: str, fp: str) -> str:
    pag = alarma.replace("No se pudo leer ", "").split(" (")[0]
    return f"No se pudo leer la página {pag} del diario del {fp}. Puede ser internet lento. Vuelva a ejecutar el programa."


def extraer_mercurio(fecha=None, *, dry_run: bool = False, usar_captura: bool = False) -> list[dict[str, Any]]:
    """fecha = una fecha (date o "AAAA-MM-DD"), una lista de fechas (lote, un solo Excel) o None (hoy)."""
    global _ultimas_metricas
    fechas = [date.today()] if fecha is None else [_como_fecha(x) for x in (fecha if isinstance(fecha, (list, tuple)) else [fecha])]
    log_file = _setup_logging()
    t0 = time.time()
    log.info("=== Inicio lectura El Mercurio Digital (motor nuevo) ===")
    log.info("Ediciones: %s | dry_run: %s | usar_captura: %s", ", ".join(f.isoformat() for f in fechas), dry_run, usar_captura)
    log.info("Log file: %s", log_file)

    from motor.lector_mercurio import CAPTURAS
    cliente, motivo = (None, None) if dry_run else _cliente_haiku()
    if motivo:
        log.error(motivo)
    resultados, fallos, avisos_programa, no_disponibles, leidas = [], [], [], [], []
    for f in fechas:
        fp = F.fecha_palabras(f.isoformat())
        try:
            informe = _leer(f, usar_captura)
        except Exception as e:
            log.error("Error leyendo la edición %s: %s", f.isoformat(), e, exc_info=True)
            fallos.append(f"No se pudo abrir el diario del {fp}. Revise internet y vuelva a ejecutar el programa.")
            continue
        for n in informe.get("notas") or []:
            log.info("Nota de la lectura %s. %s", f.isoformat(), n)
        if not informe.get("rollos"):
            if not informe.get("paginas_leidas"):
                no_disponibles.append(fp)
                log.error("La edición del %s no está disponible o no tiene páginas legibles", f.isoformat())
            else:
                avisos_programa.append(f"El diario del {fp} no trae la sección de remates de propiedades.")
            continue
        leidas.append(f.isoformat())
        for al in informe.get("alarmas") or []:
            log.warning("Alarma de lectura %s. %s", f.isoformat(), al)
            if al.startswith("No se pudo leer "):
                fallos.append(_fallo_pagina(al, fp))
            else:
                avisos_programa.append(f"Diario del {fp}. {al}")
        if dry_run:
            continue
        rollos, _al = paginas_desde_captura(CAPTURAS / f.isoformat())
        res = procesar(rollos, f.isoformat(), cliente=cliente)
        log.info("Edición %s. %d avisos cortados, %d partidores eliminados, %d sin rol, %d causas. IA %s",
                 f.isoformat(), res["avisos_cortados"], len(res["partidores"]), len(res["sin_rol"]), len(res["causas"]),
                 {k: res["ia"][k] for k in ("leidos", "sin_ia", "llamadas", "colores")})
        for e in res["ia"]["errores"][:10]:
            log.warning("IA. %s", e)
        for al in res["alarmas"]:
            log.warning("Alarma del motor %s. %s", f.isoformat(), al)
            if al.startswith("Cuadre."):
                fallos.append(f"Diario del {fp}. Un número de rol impreso no quedó dentro de ningún aviso. Revise la página en el diario.")
        if res["ia"].get("clave_invalida"):
            fallos.append(f"Diario del {fp}. {res['ia']['sin_ia']} aviso(s) quedaron sin dirección porque la clave de la "
                          "inteligencia artificial no es válida. No es problema de internet. Avise a Diego para que la cambie.")
        elif res["ia"]["sin_ia"]:
            fallos.append(f"Diario del {fp}. {res['ia']['sin_ia']} aviso(s) quedaron sin dirección porque el servicio de "
                          "inteligencia artificial no respondió (internet o saldo de la cuenta). Vuelva a ejecutar más tarde. "
                          "Lo que ya se leyó no se cobra de nuevo.")
        resultados.append(res)

    if no_disponibles and not leidas:
        _ultimas_metricas = {"fallos": fallos, "ediciones": [], "no_disponibles": no_disponibles}
        raise EdicionNoDisponible(", ".join(no_disponibles))
    for fp in no_disponibles:
        fallos.append(f"La edición del {fp} no está publicada o no se pudo abrir.")

    if dry_run:
        log.info("DRY RUN completado. Ediciones con remates %s", leidas)
        _ultimas_metricas = {"fallos": fallos, "ediciones": leidas, "avisos_programa": avisos_programa}
        return []

    historico = _cargar_causas_historico()
    log.info("Histórico CAUSAS cargado: %d entradas", len(historico))
    tabla = F.aplicar(resultados, historico)
    for x in tabla["descartados"]:
        log.info("  Descartado: ROL %s-%s — %s — %s", x["rol"], x["año"], x["tribunal"], x["motivo"])
    for x in tabla["excluidas_cbr"]:
        log.info("  Excluido por dominio %s: ROL %s-%s — %s", x["cbr_anio"], x["rol"], x["año"], x["tribunal"])
    ia = {k: sum(r["ia"][k] for r in resultados) for k in ("leidos", "sin_ia", "llamadas", "tokens_entrada", "tokens_salida", "costo_usd")}
    _ultimas_metricas = {
        "ediciones": leidas, "tokens_input": ia["tokens_entrada"], "tokens_output": ia["tokens_salida"],
        "costo_usd": ia["costo_usd"], "ia": ia,
        "excluidos_cbr": tabla["excluidas_cbr"], "descartados": tabla["descartados"], "sin_rol": tabla["sin_rol"],
        "en_historial": tabla["en_historial"], "fallos": fallos, "avisos_programa": avisos_programa,
        "avisos_cortados": sum(r["avisos_cortados"] for r in resultados),
        "partidores": sum(len(r["partidores"]) for r in resultados),
    }
    log.info("=" * 60)
    log.info("  RESUMEN LECTURA MERCURIO (motor nuevo)")
    log.info("  Ediciones leídas        : %s", ", ".join(leidas) or "ninguna")
    log.info("  Avisos cortados         : %d (partidores eliminados %d)", _ultimas_metricas["avisos_cortados"], _ultimas_metricas["partidores"])
    log.info("  Tabla principal         : %d", len(tabla["principal"]))
    log.info("  Sin rol                 : %d", len(tabla["sin_rol"]))
    log.info("  Excluidas por dominio   : %d", len(tabla["excluidas_cbr"]))
    log.info("  Descartadas             : %d", len(tabla["descartados"]))
    log.info("  Ya en historial         : %d", tabla["en_historial"])
    log.info("  IA (Haiku)              : %d leídos, %d llamadas nuevas, %d sin respuesta, USD %.4f", ia["leidos"], ia["llamadas"], ia["sin_ia"], ia["costo_usd"])
    for x in fallos:
        log.error("  FALLO: %s", x)
    log.info("  Tiempo                  : %.0f s", time.time() - t0)
    log.info("=" * 60)
    return tabla["principal"]


# Canal lateral de métricas para M5 (no toca la firma de extraer_mercurio)
_ultimas_metricas: dict[str, Any] = {}


def obtener_metricas():
    """Tablas extra (excluidas, descartadas, sin rol), tokens, costo y fallos de la última ejecución."""
    return _ultimas_metricas


if __name__ == "__main__":
    import argparse, pprint
    parser = argparse.ArgumentParser(description="Lectura de El Mercurio Digital, sección 1616 Remates de propiedades")
    parser.add_argument("--fecha", type=str, default=None, help="Fecha de la edición (AAAA-MM-DD). Por defecto hoy.")
    parser.add_argument("--dry-run", action="store_true", help="Solo lee el diario (sin IA ni filtros).")
    parser.add_argument("--usar-captura", action="store_true", help="Usa la captura guardada si existe.")
    args = parser.parse_args()
    causas = extraer_mercurio(args.fecha, dry_run=args.dry_run, usar_captura=args.usar_captura)
    print(f"\n{'='*60}\nCAUSAS EXTRAÍDAS: {len(causas)}\n{'='*60}")
    pprint.pprint(causas, width=120)
