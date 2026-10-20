"""Corrida diaria del robot del Mercurio en GitHub Actions (19 de Octubre de 2026).

Pasos.
1. Si la edición de hoy ya se envió (marca en Supabase), no hace nada. Si quedó procesada pero
   el correo no salió, reenvía el Excel guardado.
2. Baja de Supabase el historial (estado/causas_ojv.xlsx) y las respuestas de Haiku (estado/ia_respuestas.zip).
3. Corre main.py --fecha HOY, el mismo programa del PC.
4. Según el código de salida de main.py guarda la memoria nueva y manda el correo.
   0 o 4 con Excel  respaldo del historial viejo, historial nuevo, respuestas y Excel a Supabase. Correo con el Excel.
   0 sin Excel      no hubo causas nuevas. Guarda las respuestas, y el historial si cambió (regla de los 4 días).
                    Correo que lo dice.
   otro caso        no se sube el historial. Si no es el último intento, sale para que el siguiente reintente.
                    Desde las 6:00, una sola vez, avisa que todavía no hay informe y que el último intento es a las 7:05.
                    En el último intento (desde las 7:00) avisa cuántos intentos se hicieron y que no se intenta más.

Variables de entorno.
    MODO            real (por defecto) o ensayo. En ensayo el correo va solo a CORREO_DIEGO,
                    lo que se guarda va a pruebas/ensayo/ y no se mira la marca de enviado.
    FECHA           AAAA-MM-DD. Por defecto hoy en hora de Chile (TZ=America/Santiago).
    INTENTO_FINAL   1 fuerza el último intento (corridas a mano). Si no viene, es último desde las 7:00 de Chile.
    SUPABASE_URL, SUPABASE_KEY, GMAIL_USER, GMAIL_APP_PASSWORD, CORREO_ABOGADO, CORREO_DIEGO.
"""
from __future__ import annotations
import os, re, shutil, subprocess, sys, time, traceback, zipfile
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.chdir(RAIZ)

from servidor import estado as E  # noqa: E402
from servidor.correo import enviar  # noqa: E402

MODO = os.environ.get("MODO", "real").strip() or "real"
FECHA = (os.environ.get("FECHA") or "").strip() or date.today().isoformat()
AHORA = datetime.now()  # hora de Chile, porque el flujo fija TZ=America/Santiago
_forzado = os.environ.get("INTENTO_FINAL", "").strip()
FINAL = _forzado == "1" or (not _forzado and AHORA.hour >= 7)
HORA_AVISO = 6        # desde esta hora, un aviso de que todavía no hay informe
ULTIMO_INTENTO = "7:05"
P = "" if MODO == "real" else "pruebas/ensayo/"
MARCA = f"{P}enviados/{FECHA}.txt"
MARCA_6AM = f"{P}avisos/{FECHA}_todavia_no.txt"
MARCA_FINAL = f"{P}avisos/{FECHA}_sin_informe.txt"
CONTADOR = f"{P}intentos/{FECHA}.txt"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
INFORMES = RAIZ / "Informe final"
CARPETA_IA = RAIZ / "ia_respuestas"
PIE = ("Este correo lo envía un programa automático cada mañana. No es necesario responderlo.\n"
       "Ante cualquier duda, hable con Diego.")


def log(msg: str) -> None:
    print(f"[diario] {msg}", flush=True)


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_texto() -> str:
    """'2026-10-19' da 'lunes 19 de octubre del 2026'. Mismo formato que motor.filtros.fecha_palabras,
    copiado aquí para que los avisos de falla no dependan de importar el programa."""
    d = date.fromisoformat(FECHA)
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} del {d.year}"


def para_todos() -> list[str]:
    diego = os.environ.get("CORREO_DIEGO", "").strip()
    if MODO != "real":
        return [diego]
    abogado = os.environ.get("CORREO_ABOGADO", "").strip()
    return list(dict.fromkeys(x for x in (abogado, diego) if x))


def link_corrida() -> str:
    s, r, i = (os.environ.get(k, "") for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"))
    return f"{s}/{r}/actions/runs/{i}" if i else "(sin enlace)"


def zip_ia(destino: Path) -> int:
    n = 0
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted((CARPETA_IA / "direccion").glob("*.json")):
            z.write(f, f"direccion/{f.name}")
            n += 1
    return n


def contar_ia() -> int:
    return len(list((CARPETA_IA / "direccion").glob("*.json")))


def guardar_memoria(con_historial: bool) -> None:
    if con_historial:
        E.subir(RAIZ / "_causas_antes.xlsx", f"{P}respaldos/causas_ojv_antes_{FECHA}.xlsx")
        E.subir(RAIZ / "causas_ojv.xlsx", f"{P}estado/causas_ojv.xlsx")
        log("Historial nuevo guardado en Supabase, con respaldo del anterior")
    n = zip_ia(RAIZ / "_ia_respuestas.zip")
    E.subir(RAIZ / "_ia_respuestas.zip", f"{P}estado/ia_respuestas.zip", "application/zip")
    log(f"Respuestas de Haiku guardadas en Supabase ({n} archivos)")


def correo_excel(excel: Path, salida: str, incompleto: bool) -> None:
    m = re.search(r"Causas nuevas (\d+)\. Avisos sin rol (\d+)", salida)
    n, sin_rol = (int(m.group(1)), int(m.group(2))) if m else (None, 0)
    ft = fecha_texto()
    lineas = ["Buenos días.", "", f"Se adjunta el reporte de remates de propiedades de El Mercurio del {ft}."]
    if n is not None:
        lineas.append(f"Trae {n} causa(s) nueva(s)" + (f" y {sin_rol} aviso(s) sin rol para revisar." if sin_rol else "."))
    if incompleto:
        lineas += ["", "ATENCIÓN. Este informe puede estar incompleto. Al programa le faltó leer algo.",
                   "En el Excel, la hoja Resumen explica qué faltó. Diego ya fue avisado.",
                   "Si lo necesita, puede revisar los remates en El Mercurio, Clasificados, sección 1616."]
    lineas += ["", PIE]
    asunto = f"Remates El Mercurio, {ft}" + (". Puede estar incompleto" if incompleto else "")
    if MODO != "real":
        asunto = "ENSAYO. " + asunto
    enviar(para_todos(), asunto, "\n".join(lineas), [excel])
    log(f"Correo con el Excel enviado a {len(para_todos())} destinatario(s)")


def correo_sin_causas(con_fallos: bool) -> None:
    ft = fecha_texto()
    if con_fallos:
        texto = (f"El programa leyó El Mercurio del {ft} y no encontró remates nuevos, pero no pudo leer todo.\n"
                 "Puede que falte algo. Diego ya fue avisado.\n"
                 "Si lo necesita, puede revisar los remates en El Mercurio, Clasificados, sección 1616.")
    else:
        texto = (f"El programa leyó El Mercurio del {ft} sin problemas.\n"
                 "Hoy no hubo remates nuevos que cumplan los criterios. Por eso no se adjunta Excel.")
    asunto = f"Remates El Mercurio, {ft}. Sin causas nuevas"
    if MODO != "real":
        asunto = "ENSAYO. " + asunto
    enviar(para_todos(), asunto, f"Buenos días.\n\n{texto}\n\n{PIE}")
    log("Correo sin causas nuevas enviado")


def motivo_simple(codigo: int) -> str:
    ft = fecha_texto()
    return {
        2: (f"El Mercurio Digital todavía no publica la edición del {ft}.\n"
            "Por eso no hay informe de hoy. No es un problema de su computador."),
        3: (f"El programa no pudo leer El Mercurio del {ft}.\n"
            "Esto NO significa que no haya remates. Significa que el programa no logró entrar al diario.\n"
            "No es un problema de su computador."),
    }.get(codigo, (f"El programa tuvo un error y no generó el informe del {ft}.\n"
                   "No es un problema de su computador ni de su internet."))


def aviso_todavia_no(codigo: int) -> None:
    """Desde las 6:00, una sola vez por día. Va al abogado y a Diego."""
    ft = fecha_texto()
    texto = (f"Todavía no es posible hacer el informe de remates del {ft}.\n"
             f"{motivo_simple(codigo).replace('Por eso no hay informe de hoy. ', '')}\n"
             f"El programa lo seguirá intentando solo. El último intento será a las {ULTIMO_INTENTO} de la mañana.\n"
             "Si sale bien antes, le llegará el informe como siempre.")
    pref = "ENSAYO. " if MODO != "real" else ""
    enviar(para_todos(), f"{pref}Remates El Mercurio, {ft}. Todavía no hay informe", f"Buenos días.\n\n{texto}\n\n{PIE}")
    log("Aviso de las 6 enviado")


def avisos_de_falla(codigo: int, salida: str, solo_diego: bool = False, intentos: int = 0) -> None:
    ft = fecha_texto()
    simple = motivo_simple(codigo)
    if intentos:
        simple = (f"Se hicieron {intentos} intento(s) entre las 5 y las {ULTIMO_INTENTO} de la mañana y el problema sigue. "
                  "No se intentará más por hoy.\n" + simple)
    simple += ("\nDiego ya fue avisado.\n"
               "Mientras tanto puede revisar los remates en El Mercurio, Clasificados, sección 1616.")
    abogado = [x for x in para_todos() if x != os.environ.get("CORREO_DIEGO", "").strip()]
    pref = "ENSAYO. " if MODO != "real" else ""
    if abogado and not solo_diego:
        enviar(abogado, f"{pref}Remates El Mercurio, {ft}. Hoy no hay informe", f"Buenos días.\n\n{simple}\n\n{PIE}")
    cola = "\n".join(salida.strip().splitlines()[-60:])
    enviar([os.environ["CORREO_DIEGO"]], f"{pref}AVISO Mercurio {FECHA}. Código {codigo}",
           f"Falló la corrida del {ft} (modo {MODO}). Código de salida {codigo}.\n"
           f"No se subió el historial a Supabase.\n\nLo que vio el abogado\n{simple}\n\n"
           f"Corrida en GitHub\n{link_corrida()}\n\nÚltimas líneas del programa\n{cola}\n")
    log("Avisos de falla enviados")


def main() -> int:
    log(f"Edición {FECHA}. Modo {MODO}. Hora {AHORA:%H:%M}. Último intento {'sí' if FINAL else 'no'}")
    if MODO == "real" and not os.environ.get("INTENTO_FINAL") and E.existe(MARCA_FINAL):
        log("Hoy ya se avisó que no hubo informe. No se intenta más")
        return 0
    if MODO == "real" and E.existe(MARCA):
        E.bajar(MARCA, RAIZ / "_marca.txt")
        marca = (RAIZ / "_marca.txt").read_text(encoding="utf-8")
        if marca.startswith("enviado"):
            log(f"La edición {FECHA} ya se envió ({marca.strip()}). No se hace nada")
            return 0
        if marca.startswith("pendiente_correo excel="):
            nombre = marca.split("=", 1)[1].strip()
            log(f"El Excel {nombre} quedó guardado pero el correo no salió. Se reenvía")
            INFORMES.mkdir(exist_ok=True)
            E.bajar(f"{P}informes/{nombre}", INFORMES / nombre)
            correo_excel(INFORMES / nombre, "", "INCOMPLETO" in nombre)
            E.subir_texto(f"enviado excel={nombre} (reenviado)", MARCA)
            return 0

    intentos = 1
    if E.existe(CONTADOR):
        E.bajar(CONTADOR, RAIZ / "_intentos.txt")
        intentos = int((RAIZ / "_intentos.txt").read_text(encoding="utf-8").strip() or 0) + 1
    E.subir_texto(str(intentos), CONTADOR)
    log(f"Intento número {intentos} de hoy")

    E.bajar("estado/causas_ojv.xlsx", RAIZ / "causas_ojv.xlsx")
    shutil.copy2(RAIZ / "causas_ojv.xlsx", RAIZ / "_causas_antes.xlsx")
    E.bajar("estado/ia_respuestas.zip", RAIZ / "_ia_bajado.zip")
    with zipfile.ZipFile(RAIZ / "_ia_bajado.zip") as z:
        z.extractall(CARPETA_IA)
    log(f"Memoria bajada de Supabase. Respuestas de Haiku disponibles {contar_ia()}")

    inicio = time.time()
    proc = subprocess.run([sys.executable, "main.py", "--fecha", FECHA],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    salida = proc.stdout or ""
    print(salida, flush=True)
    codigo = proc.returncode
    excels = sorted((p for p in INFORMES.glob("Reporte *.xlsx") if p.stat().st_mtime >= inicio - 1),
                    key=lambda p: p.stat().st_mtime)
    excel = excels[-1] if excels else None
    log(f"main.py terminó con código {codigo}. Excel {excel.name if excel else 'ninguno'}")

    if codigo in (0, 4) and excel:
        guardar_memoria(con_historial=True)
        E.subir(excel, f"{P}informes/{excel.name}",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        E.subir_texto(f"pendiente_correo excel={excel.name}", MARCA)
        correo_excel(excel, salida, incompleto=(codigo == 4))
        E.subir_texto(f"enviado excel={excel.name}", MARCA)
        return 0
    if codigo == 0:
        # Regla de los 4 días. Sin causas nuevas, main.py igual anota las causas repetidas del día. Si el historial cambió,
        # se sube, para que el trencito de 4 días no pierda ese día.
        cambio = (RAIZ / "causas_ojv.xlsx").read_bytes() != (RAIZ / "_causas_antes.xlsx").read_bytes()
        guardar_memoria(con_historial=cambio)
        correo_sin_causas(con_fallos=False)
        E.subir_texto("enviado sin causas nuevas", MARCA)
        return 0
    if not FINAL:
        if AHORA.hour >= HORA_AVISO and not E.existe(MARCA_6AM):
            aviso_todavia_no(codigo)
            E.subir_texto(f"avisado a las {AHORA:%H:%M}, código {codigo}", MARCA_6AM)
        log("No salió bien y no es el último intento. El siguiente intento lo vuelve a probar")
        return 0
    if codigo == 4:
        guardar_memoria(con_historial=False)
        correo_sin_causas(con_fallos=True)
        avisos_de_falla(codigo, salida, solo_diego=True, intentos=intentos)
        E.subir_texto(f"código {codigo}, {intentos} intentos", MARCA_FINAL)
        return 1
    avisos_de_falla(codigo, salida, intentos=intentos)
    E.subir_texto(f"código {codigo}, {intentos} intentos", MARCA_FINAL)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        detalle = traceback.format_exc()
        print(detalle, flush=True)
        if FINAL:
            try:
                avisos_de_falla(1, detalle)
            except Exception:
                traceback.print_exc()
        sys.exit(1)
