# Apply Fix 1, 2, 3
# Fix 1 & 2 in modulo1_mercurio.py, Fix 3 in main.py

# ===================== FIX 1 & 2 in modulo1_mercurio.py =====================
with open('modulo1_mercurio.py', 'r', encoding='utf-8') as f:
    c = f.read()

# --- FIX 1: Insert _normalizar_ordinal_tribunal after _limpiar_tribunal ---
normalizador_func = '''
def _normalizar_ordinal_tribunal(nombre: str | None) -> str | None:
    """
    Normaliza el ordinal escrito de un nombre de tribunal a formato "N°".
    Ej: "Primer Juzgado Civil de Santiago" → "1° Juzgado Civil de Santiago".
    Si ya es numérico o no tiene ordinal reconocible, deja intacto.
    """
    if not nombre:
        return nombre

    # Si ya tiene formato numérico con °, no tocar
    if re.search(r'\\b\\d+\\s*[°°]', nombre):
        return nombre

    # Diccionario completo 1-30: ordinal escrito → número + °
    # Ordenado por longitud descendente de clave para que "Décimo Tercer" se
    # procese antes que "Tercer" o "Décimo".
    ORDINALES_ESCRITOS = [
        ("vigésimo noveno",  "29°"), ("vigesimo noveno",  "29°"),
        ("vigésimo octavo",  "28°"), ("vigesimo octavo",  "28°"),
        ("vigésimo séptimo", "27°"), ("vigesimo septimo", "27°"),
        ("vigésimo sexto",   "26°"), ("vigesimo sexto",   "26°"),
        ("vigésimo quinto",  "25°"), ("vigesimo quinto",  "25°"),
        ("vigésimo cuarto",  "24°"), ("vigesimo cuarto",  "24°"),
        ("vigésimo tercero", "23°"), ("vigesimo tercero", "23°"),
        ("vigésimo tercer",  "23°"), ("vigesimo tercer",  "23°"),
        ("vigésimo segundo", "22°"), ("vigesimo segundo", "22°"),
        ("vigésimo primero", "21°"), ("vigesimo primero", "21°"),
        ("vigésimo primer",  "21°"), ("vigesimo primer",  "21°"),
        ("décimo noveno",    "19°"), ("decimo noveno",    "19°"),
        ("décimo octavo",    "18°"), ("decimo octavo",    "18°"),
        ("décimo séptimo",   "17°"), ("decimo septimo",   "17°"),
        ("décimo sexto",     "16°"), ("decimo sexto",     "16°"),
        ("décimo quinto",    "15°"), ("decimo quinto",    "15°"),
        ("décimo cuarto",    "14°"), ("decimo cuarto",    "14°"),
        ("décimo tercero",   "13°"), ("decimo tercero",   "13°"),
        ("décimo tercer",    "13°"), ("decimo tercer",    "13°"),
        ("décimo segundo",   "12°"), ("decimo segundo",   "12°"),
        ("décimo primero",   "11°"), ("decimo primero",   "11°"),
        ("décimo primer",    "11°"), ("decimo primer",    "11°"),
        ("trigésimo",        "30°"), ("trigesimo",        "30°"),
        ("duodécimo",        "12°"), ("duodecimo",        "12°"),
        ("undécimo",         "11°"), ("undecimo",         "11°"),
        ("decimonoveno",     "19°"),
        ("decimoctavo",      "18°"),
        ("decimoséptimo",    "17°"), ("decimoseptimo",    "17°"),
        ("decimosexto",      "16°"),
        ("decimoquinto",     "15°"),
        ("decimocuarto",     "14°"),
        ("decimotercero",    "13°"),
        ("decimotercer",     "13°"),
        ("decimosegundo",    "12°"),
        ("decimoprimero",    "11°"),
        ("decimoprimer",     "11°"),
        ("décimo",           "10°"), ("decimo",           "10°"),
        ("noveno",           "9°"),  ("novena",           "9°"),
        ("octavo",           "8°"),  ("octava",           "8°"),
        ("séptimo",          "7°"),  ("septimo",          "7°"),
        ("sexto",            "6°"),  ("sexta",            "6°"),
        ("quinto",           "5°"),  ("quinta",           "5°"),
        ("cuarto",           "4°"),  ("cuarta",           "4°"),
        ("tercero",          "3°"),  ("tercer",           "3°"),
        ("tercera",          "3°"),
        ("segundo",          "2°"),  ("segunda",          "2°"),
        ("primero",          "1°"),  ("primer",           "1°"),
        ("primera",          "1°"),
    ]

    resultado = nombre
    for escrito, reemplazo in ORDINALES_ESCRITOS:
        # Escape para regex: \\b para límite de palabra
        patron = r'\\b' + re.escape(escrito) + r'\\b'
        resultado, n = re.subn(patron, reemplazo, resultado, flags=re.IGNORECASE)
        if n > 0:
            # Solo reemplazamos la primera coincidencia
            break

    return resultado
'''

# Insert after _limpiar_tribunal function (after the 'return texto' line of that function)
c = c.replace(
    '    texto = re.sub(r"\\s{2,}", " ", texto)\n    return texto\n\n\ndef _extraer_ordinal',
    '    texto = re.sub(r"\\s{2,}", " ", texto)\n    return texto\n\n\n# ── Normalizador de ordinal de tribunal ──' + normalizador_func + '\n\ndef _extraer_ordinal'
)

# Apply _normalizar_ordinal_tribunal at L1043
c = c.replace(
    '    tribunal_limpio = _limpiar_tribunal(str(tribunal_raw).strip() if tribunal_raw else None)\n\n    # Mapear tribunal → corte',
    '    tribunal_limpio = _limpiar_tribunal(str(tribunal_raw).strip() if tribunal_raw else None)\n    tribunal_limpio = _normalizar_ordinal_tribunal(tribunal_limpio)\n\n    # Mapear tribunal → corte'
)

# --- FIX 2: Dedup excluidos_cbr by ROL ---
c = c.replace(
    '    # Poblar métricas accesibles desde el exterior (canal lateral para M5)\n    global _ultimas_metricas\n    _ultimas_metricas = {\n        "tokens_input": st.tokens_input,\n        "tokens_output": st.tokens_output,\n        "excluidos_cbr": st.excluidos_cbr,\n    }',
    '    # Poblar métricas accesibles desde el exterior (canal lateral para M5)\n    global _ultimas_metricas\n    # Deduplicar excluidos CBR por ROL (primera aparición)\n    _vistos = set()\n    _exc_unicos = []\n    for e in st.excluidos_cbr:\n        if e["rol"] not in _vistos:\n            _vistos.add(e["rol"])\n            _exc_unicos.append(e)\n    _ultimas_metricas = {\n        "tokens_input": st.tokens_input,\n        "tokens_output": st.tokens_output,\n        "excluidos_cbr": _exc_unicos,\n    }'
)

with open('modulo1_mercurio.py', 'w', encoding='utf-8') as f:
    f.write(c)

# Verify FIX 1 & 2
c2 = open('modulo1_mercurio.py', 'r', encoding='utf-8').read()
print('Fix 1 - function exists:', '_normalizar_ordinal_tribunal' in c2)
print('Fix 1 - applied in aviso:', 'tribunal_limpio = _normalizar_ordinal_tribunal(tribunal_limpio)' in c2)
print('Fix 2 - dedup exists:', '_vistos = set()' in c2)

# ===================== FIX 3 in main.py =====================
with open('main.py', 'r', encoding='utf-8') as f:
    m = f.read()

new_resumen = '''def _resumen_final(causas: list[dict], elapsed_s: float, ruta_reporte: str) -> None:
    """Imprime el resumen ejecutivo al terminar el pipeline."""
    total = len(causas)

    # Clasificación OJV (mismo criterio que _clasificar en M5)
    validadas = sum(1 for c in causas
                    if bool(c.get("demandado")) and not c.get("motivo_fallo"))
    sin_coincidencia = total - validadas

    # Métricas de extracción
    try:
        from modulo1_mercurio import obtener_metricas
        met = obtener_metricas()
    except Exception:
        met = {}
    tokens_in = met.get("tokens_input", 0)
    tokens_out = met.get("tokens_output", 0)
    tokens_total = tokens_in + tokens_out

    # Costo estimado
    try:
        from config import MODELO_EXTRACCION, DEEPSEEK_PRECIO_INPUT_USD_POR_1M, DEEPSEEK_PRECIO_OUTPUT_USD_POR_1M
    except ImportError:
        MODELO_EXTRACCION = "desconocido"
    if MODELO_EXTRACCION == "deepseek":
        try:
            costo = (tokens_in / 1e6) * DEEPSEEK_PRECIO_INPUT_USD_POR_1M + (tokens_out / 1e6) * DEEPSEEK_PRECIO_OUTPUT_USD_POR_1M
            costo_str = f"USD {costo:.4f}"
        except Exception:
            costo_str = "no calculado"
    else:
        costo_str = f"no calculado (motor={MODELO_EXTRACCION})"

    _sep("RESUMEN EJECUTIVO")
    mins, segs = divmod(int(elapsed_s), 60)
    print(f"  Tiempo total           : {mins}m {segs}s")
    print(f"  Total causas procesadas: {total}")
    print()
    print("  VALIDACIÓN OJV")
    print(f"    Validadas en OJV     : {validadas}  (demandado poblado, sin fallo)")
    print(f"    Sin coincidencia OJV : {sin_coincidencia}  (fallo OJV o demandado vacío)")
    print()
    print("  MÉTRICAS DE EXTRACCIÓN")
    print(f"    Tokens entrada       : {tokens_in:,}")
    print(f"    Tokens salida        : {tokens_out:,}")
    print(f"    Tokens total         : {tokens_total:,}")
    print(f"    Costo estimado       : {costo_str}")
    print()
    if ruta_reporte:
        print(f"  Reporte: {ruta_reporte}")
    _sep()'''

# Replace the old _resumen_final
old_resumen_start = 'def _resumen_final(causas: list[dict], elapsed_s: float, ruta_reporte: str) -> None:'
old_resumen_end = '    _sep()\n\n\n# ─'

# Find the function and replace it
idx_start = m.find(old_resumen_start)
idx_end = m.find(old_resumen_end, idx_start)
if idx_start >= 0 and idx_end > idx_start:
    m = m[:idx_start] + new_resumen + m[idx_end+len(old_resumen_end)-3:]

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(m)
print('Fix 3 - resumen replaced:', 'VALIDACIÓN OJV' in m)
