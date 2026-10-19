"""Memoria del robot en Supabase Storage, bucket privado "mercurio" (19 de Octubre de 2026).

La dirección y la clave vienen de las variables de entorno SUPABASE_URL y SUPABASE_KEY
(secretos de GitHub). Nunca se imprimen.
"""
from __future__ import annotations
import os, urllib.error, urllib.parse, urllib.request
from pathlib import Path

BUCKET = "mercurio"


def _url(remoto: str) -> str:
    base = os.environ["SUPABASE_URL"].strip().rstrip("/")
    return f"{base}/storage/v1/object/{BUCKET}/{urllib.parse.quote(remoto)}"


def _cabeceras() -> dict:
    k = os.environ["SUPABASE_KEY"].strip()
    return {"apikey": k, "Authorization": f"Bearer {k}"}


def existe(remoto: str) -> bool:
    req = urllib.request.Request(_url(remoto), headers=_cabeceras(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return False
        raise


def bajar(remoto: str, local: Path) -> None:
    req = urllib.request.Request(_url(remoto), headers=_cabeceras(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            Path(local).write_bytes(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase no entregó {remoto} (respuesta {e.code}). {e.read()[:300]!r}") from None


def subir(local: Path, remoto: str, tipo: str = "application/octet-stream") -> None:
    datos = Path(local).read_bytes()
    cab = _cabeceras() | {"Content-Type": tipo, "x-upsert": "true"}
    req = urllib.request.Request(_url(remoto), data=datos, headers=cab, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            if r.status != 200:
                raise RuntimeError(f"Supabase no guardó {remoto} (respuesta {r.status})")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase no guardó {remoto} (respuesta {e.code}). {e.read()[:300]!r}") from None


def subir_texto(texto: str, remoto: str) -> None:
    tmp = Path("_texto_tmp.txt")
    tmp.write_text(texto, encoding="utf-8")
    subir(tmp, remoto, "text/plain; charset=utf-8")
    tmp.unlink()
