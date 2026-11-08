"""Piezas comunes de la IA (Claude Haiku), traídas de D:\\Agendar_Remates\\motor\\vale_vista.py el 17 de Octubre de 2026.
El vale vista no viaja al Mercurio (decisión de Diego). Solo se copian el modelo, la búsqueda de la frase exacta y el
cliente. Copia sin cambios de lógica.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MODELO = "claude-haiku-5-5"


_COMILLAS = str.maketrans({c: "'" for c in "‘’‚‛′`´"} | {c: '"' for c in "“”„‟″«»"})


def buscar_frase(frase: str | None, texto: str) -> str | None:
    """Busca la frase en el aviso aceptando SOLO diferencias de espacios (decisión de Diego). Devuelve el tramo tal
    como está escrito en el aviso, o None."""
    if not frase:
        return None
    # Ciclo 2 de mejora, tipo D3 (decisión de Diego del 8 de Noviembre de 2026). Además de los espacios se aceptan como
    # iguales las comillas rectas y curvas (la IA copia ' donde el diario imprime ‘ ’). Mayúsculas y palabras siguen exactas.
    sin = re.sub(r"\s+", "", frase).translate(_COMILLAS)
    if not sin:
        return None
    pos = [i for i, c in enumerate(texto) if not c.isspace()]
    compacto = "".join(texto[i] for i in pos).translate(_COMILLAS)
    k = compacto.find(sin)
    if k < 0:
        return None
    return texto[pos[k]:pos[k + len(sin) - 1] + 1]


def cliente_desde_config():
    import importlib.util, anthropic
    spec = importlib.util.spec_from_file_location("config", RAIZ / "config.py")
    c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
    return anthropic.Anthropic(api_key=c.ANTHROPIC_API_KEY)
