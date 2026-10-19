"""Envío de correos del robot del Mercurio por Gmail (19 de Octubre de 2026).

La cuenta y la clave vienen de las variables de entorno GMAIL_USER y GMAIL_APP_PASSWORD,
que en GitHub salen de los secretos del repositorio. Nunca se escriben en un archivo.
La clave de aplicación de Gmail son 16 letras. Se le quitan los espacios por si se pegó con ellos.

Uso desde la línea de comandos (sirve para la prueba).
    python -m servidor.correo --para CORREO --asunto "..." --cuerpo-archivo cuerpo.txt --adjunto archivo.xlsx
"""
from __future__ import annotations
import argparse, mimetypes, os, smtplib, ssl, sys
from email.message import EmailMessage
from pathlib import Path

SERVIDOR = "smtp.gmail.com"
PUERTO = 465  # SSL directo


def enviar(para: list[str], asunto: str, cuerpo: str, adjuntos: list[Path] | None = None) -> None:
    usuario = os.environ.get("GMAIL_USER", "").strip()
    clave = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    if not usuario or not clave:
        raise RuntimeError("Faltan GMAIL_USER o GMAIL_APP_PASSWORD en el entorno")
    para = [p.strip() for p in para if p and p.strip()]
    if not para:
        raise RuntimeError("No hay destinatarios")
    msg = EmailMessage()
    msg["From"] = f"Robot Remates Mercurio <{usuario}>"
    msg["To"] = ", ".join(para)
    msg["Subject"] = asunto
    msg.set_content(cuerpo)
    for ruta in adjuntos or []:
        ruta = Path(ruta)
        tipo = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
        principal, sub = tipo.split("/", 1)
        msg.add_attachment(ruta.read_bytes(), maintype=principal, subtype=sub, filename=ruta.name)
    with smtplib.SMTP_SSL(SERVIDOR, PUERTO, context=ssl.create_default_context(), timeout=60) as s:
        s.login(usuario, clave)
        s.send_message(msg)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Envía un correo con Gmail")
    ap.add_argument("--para", action="append", required=True, help="Destinatario (se puede repetir)")
    ap.add_argument("--asunto", required=True)
    ap.add_argument("--cuerpo-archivo", required=True, help="Archivo de texto con el cuerpo del correo")
    ap.add_argument("--adjunto", action="append", default=[], help="Archivo adjunto (se puede repetir)")
    a = ap.parse_args()
    adj = [Path(x) for x in a.adjunto]
    for x in adj:
        if not x.is_file():
            sys.exit(f"No existe el adjunto {x}")
    enviar(a.para, a.asunto, Path(a.cuerpo_archivo).read_text(encoding="utf-8"), adj)
    print(f"Correo enviado a {len(a.para)} destinatario(s) con {len(adj)} adjunto(s)")
