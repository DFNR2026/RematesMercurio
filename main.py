"""
main.py — Orquestador del Extractor El Mercurio Digital (M1 lectura, M5 Excel)

Uso (lo normal es ejecutar_mercurio.bat, que llama a esto):
    python main.py --fecha 2026-10-17                          # una edición
    python main.py --fecha 2026-10-14 --fecha-fin 2026-10-17   # varias ediciones en UN solo Excel
    python main.py --fecha 2026-10-14 --usar-captura           # usa la lectura ya guardada en capturas\\ (sin internet al diario)
    python main.py --demo                                      # 25 causas sintéticas, solo para probar el Excel
    python main.py --fecha 2026-10-17 --hasta 1                # se detiene después de la lectura (sin Excel)

Códigos de salida (los lee ejecutar_mercurio.bat para mostrar el aviso correcto al abogado):
    0  terminó bien (con o sin causas nuevas)
    2  la edición no está publicada todavía
    3  no se pudo leer el diario (no hay informe)
    4  hay informe, pero puede estar incompleto (dice qué pasó y qué hacer)
    1  error inesperado del programa

Traspaso del 17 de Octubre de 2026. Se retiró el lector viejo de PDFs (modulo1_parser, carpeta Diarios), que ya no existía.
"""

import os
import sys
import time
import shutil
import argparse
import logging
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# Dual-log: consola + archivo en logs/
# ─────────────────────────────────────────────────────────────────
_LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_LOGS_DIR, exist_ok=True)
_LOG_FILE = os.path.join(
    _LOGS_DIR,
    f"ejecucion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
)

_root = logging.getLogger()
for _h in _root.handlers[:]:
    _root.removeHandler(_h)
_root.setLevel(logging.INFO)

_FMT = logging.Formatter("%(asctime)s %(message)s")

_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(_FMT)
_root.addHandler(_console_handler)

_file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(_FMT)
_root.addHandler(_file_handler)

log = logging.getLogger("main")


class _TeeWriter:
    """Redirige print() a consola + archivo de log simultáneamente."""

    def __init__(self, original_stream, log_file_handle):
        self._orig = original_stream
        self._log = log_file_handle

    def write(self, text):
        # El log (UTF-8) va primero y siempre: un fallo de consola no debe impedir el registro.
        try:
            self._log.write(text)
            self._log.flush()
        except Exception:
            pass
        # La consola puede usar un codec limitado (p. ej. cp1252 en salida redirigida).
        # Si el texto no es codificable, se degrada con reemplazo en vez de crashear.
        try:
            self._orig.write(text)
        except UnicodeEncodeError:
            enc = getattr(self._orig, "encoding", None) or "ascii"
            self._orig.write(text.encode(enc, errors="replace").decode(enc))
        self._orig.flush()

    def flush(self):
        self._orig.flush()
        self._log.flush()

    # Necesario para que logging no falle al verificar el stream
    def fileno(self):
        return self._orig.fileno()


_log_fh = open(_LOG_FILE, "a", encoding="utf-8")
sys.stdout = _TeeWriter(sys.__stdout__, _log_fh)
sys.stderr = _TeeWriter(sys.__stderr__, _log_fh)

# ─────────────────────────────────────────────────────────────────
# Imports de módulos del proyecto
# ─────────────────────────────────────────────────────────────────
from modulo1_mercurio import extraer_mercurio, obtener_metricas, EdicionNoDisponible
from modulo5_reporte import generar_reporte, actualizar_historial, PASOS_SI_FALLA

_W = 60


def _sep(titulo: str = "") -> None:
    print()
    if titulo:
        print("=" * _W)
        print(f"  {titulo}")
    print("=" * _W)


def _fechas(desde: str | None, hasta: str | None) -> list[str]:
    from datetime import date, timedelta
    if not desde:
        return [date.today().isoformat()]
    a = date.fromisoformat(desde)
    b = date.fromisoformat(hasta) if hasta else a
    if b < a:
        a, b = b, a
    return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


def _causas_demo() -> list[dict]:
    """25 causas sintéticas para probar el Excel sin red ni IA. Escriben en el historial: respaldar causas_ojv.xlsx antes."""
    import random
    random.seed(42)
    comunas = ["Maipú", "La Florida", "Santiago", "Puente Alto", "San Bernardo", "Peñalolén", "Las Condes", "Ñuñoa"]
    return [{"rol": str(30000 + i), "año": str(random.randint(2018, 2024)), "corte": "C.A. de Santiago",
             "tribunal": f"{i}° Juzgado Civil de Santiago", "demandante": "Banco Demo", "demandado": f"Deudor Demo {i}",
             "direccion": f"Calle Demo {i * 100}", "comuna": random.choice(comunas), "fojas": str(1000 + i),
             "observaciones": "", "revisar": False, "region_rm": True} for i in range(1, 26)]


def _imprimir_fallos(fallos: list) -> None:
    print()
    print("  " + "!" * 58)
    print("  ATENCIÓN. EL INFORME PUEDE ESTAR INCOMPLETO")
    print("  " + "!" * 58)
    for f in fallos:
        print(f"  - {f}")
    print()
    print("  QUÉ HACER")
    for p in PASOS_SI_FALLA:
        print(f"  {p}")
    print("  " + "!" * 58)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extractor El Mercurio Digital — remates de propiedades (sección 1616)")
    parser.add_argument("--fecha", type=str, default=None, metavar="AAAA-MM-DD", help="Edición a leer (por defecto hoy)")
    parser.add_argument("--fecha-fin", type=str, default=None, metavar="AAAA-MM-DD",
                        help="Última edición de un lote. Todas las ediciones entre --fecha y esta van en un solo Excel")
    parser.add_argument("--usar-captura", action="store_true", help="Usa la lectura ya guardada en capturas\\ si existe")
    parser.add_argument("--demo", action="store_true", help="25 causas sintéticas (sin lectura)")
    parser.add_argument("--hasta", type=int, default=5, metavar="N", help="1 a 4 se detiene tras la lectura. 5 completo")
    parser.add_argument("--silencio", action="store_true", help="Solo resúmenes")
    args = parser.parse_args()
    if args.silencio:
        logging.root.setLevel(logging.WARNING)

    t0 = time.time()
    _sep("EXTRACTOR EL MERCURIO DIGITAL")
    print(f"  Log: {_LOG_FILE}")
    metricas: dict = {}
    try:
        if args.demo:
            causas = _causas_demo()
            metricas = {"ediciones": [], "fallos": []}
            print(f"  [DEMO] {len(causas)} causas sintéticas")
        else:
            fechas = _fechas(args.fecha, args.fecha_fin)
            _sep("LECTURA DEL DIARIO")
            print(f"  Ediciones: {', '.join(fechas)}")
            print("  Log detallado: logs/mercurio_*.log")
            try:
                causas = extraer_mercurio(fechas, usar_captura=args.usar_captura)
            except EdicionNoDisponible as e:
                print()
                print(f"  La edición del {e} todavía no está publicada en El Mercurio Digital.")
                print("  Pruebe de nuevo más tarde.")
                sys.exit(2)
            metricas = obtener_metricas()
            sin_rol = metricas.get("sin_rol") or []
            print(f"  Causas nuevas {len(causas)}. Avisos sin rol {len(sin_rol)}. "
                  f"Excluidas por dominio {len(metricas.get('excluidos_cbr') or [])}. Descartadas {len(metricas.get('descartados') or [])}.")
            fallos = metricas.get("fallos") or []
            if fallos:
                _imprimir_fallos(fallos)
            if not metricas.get("ediciones"):
                print()
                print("  NO se generó informe. No se pudo leer ninguna edición.")
                print("  OJO. Esto NO significa que no haya remates. Significa que el programa no pudo leerlos.")
                sys.exit(3)
            if not causas and not sin_rol:
                print()
                print("  Sin causas nuevas. La lectura funcionó bien y no hay remates nuevos que cumplan los criterios.")
                sys.exit(4 if fallos else 0)
        if args.hasta < 5:
            print(f"  Detenido después de la lectura (--hasta {args.hasta}). No se generó Excel.")
            return
        _sep("INFORME EXCEL")
        actualizar_historial(causas)
        ruta = generar_reporte(causas, metricas=metricas)
        print(f"  Informe: {ruta}")
        print(f"  Tiempo total: {int(time.time() - t0)} s")
        _sep()
        if metricas.get("fallos"):
            sys.exit(4)
    except KeyboardInterrupt:
        print("\n  Detenido por el usuario (Ctrl+C).")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print()
        print(f"  ERROR INESPERADO DEL PROGRAMA. {e}")
        import traceback
        traceback.print_exc()
        print("  Avise a Diego y envíele el archivo más nuevo de la carpeta logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
