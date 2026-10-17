"""Remates de partición (juez o jueza partidor, partidora o árbitro). Decisión de Diego del 17 de Octubre de 2026.
En el Mercurio se eliminan del todo y no aparecen en ninguna tabla. Solo se cuentan por dentro para el cuadre de roles.
Copia sin cambios de lógica de D:\\Agendar_Remates\\db\\carga.py (normalizar, PARTICION y es_partidor).
"""
import re, unicodedata


def normalizar(t: str | None) -> str:
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[°º.,;:()]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# Se busca al comienzo del aviso, sin importar mayúsculas (el diario escribe "Juez partidor", "JUEZ PARTIdor", "ANTE ARBITRO").
PARTICION = re.compile(r"\bJUEZA?\s+(?:[ÁA]RBITRO|PARTIDORA?)\b|\bANTE\s+(?:EL\s+|LA\s+)?[ÁA]RBITRO\b|\bPARTICI[OÓ]N\b|\bPARTICIONAL\b", re.I)


def es_partidor(tribunal: str | None, texto: str) -> bool:
    t = normalizar(tribunal)
    return t.startswith(("juez partidor", "jueza partidora", "juez arbitro", "jueza arbitro")) or bool(PARTICION.search(texto[:300]))
