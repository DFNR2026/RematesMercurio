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
# La IA es Claude Haiku (motor/ia_comun.py). DeepSeek se retiró del programa el 17 de Octubre de 2026.

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
