# TEMPLATE — Copiar como config.py y completar credenciales
# NO subir config.py a GitHub (está en .gitignore)
"""
Configuración global del sistema de análisis de remates judiciales.
"""
import os

# === RUTAS (auto-detectadas, no cambiar) ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIARIOS_DIR            = os.path.join(BASE_DIR, "Diarios")
DIARIOS_PROCESADOS_DIR = os.path.join(BASE_DIR, "Diarios_Procesados")
DESCARGAS_DIR          = os.path.join(BASE_DIR, "Descargas")
REPORTES_DIR           = os.path.join(BASE_DIR, "Informe final")
CAUSAS_XLSX   = os.path.join(BASE_DIR, "causas_ojv.xlsx")

# === CLAVES API ===
ANTHROPIC_API_KEY = "sk-ant-XXXXXXXXXX"  # <-- PEGAR TU API KEY DE ANTHROPIC AQUÍ
DEEPSEEK_API_KEY = ""                    # <-- PEGAR TU API KEY DE DEEPSEEK AQUÍ

# === MOTOR DE EXTRACCIÓN ===
MODELO_EXTRACCION = "sonnet"   # valores: "sonnet" | "deepseek"

# === TARIFAS DEEPSEEK (USD por 1M tokens) ===
# Verificar periódicamente en https://api-docs.deepseek.com/quick_start/pricing
# — los precios cambian; estos son referenciales a 2026-05.
DEEPSEEK_PRECIO_INPUT_USD_POR_1M  = 0.14
DEEPSEEK_PRECIO_OUTPUT_USD_POR_1M = 0.28

# === EXCEL SHEETS ===
SHEET_REFERENCIA = "REFERENCIA"
SHEET_CAUSAS = "CAUSAS"

# === FILTROS ===
DEMANDANTES_EXCLUIDOS = ["banco estado", "banco del estado", "banco del estado de chile"]

# === REGIÓN METROPOLITANA ===
CORTES_RM = {"C.A. de Santiago", "C.A. de San Miguel"}

# === EL MERCURIO DIGITAL ===
MERCURIO_USER     = ""   # <-- RUT sin puntos ni guión
MERCURIO_PASS     = ""   # <-- Contraseña El Mercurio Digital
MERCURIO_BASE_URL = "https://digital.elmercurio.com"
CAPTURAS_DIR      = os.path.join(BASE_DIR, "Capturas")
PROCESADAS_DIR    = os.path.join(BASE_DIR, "Procesadas")
