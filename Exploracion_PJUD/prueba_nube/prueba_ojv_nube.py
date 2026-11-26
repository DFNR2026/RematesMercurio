"""Prueba exploratoria del PJUD (OJV) desde un servidor de GitHub Actions, sin PC.

Decisión de Diego del 26 de Noviembre de 2026. Una sola causa, Chrome común
manejado por Playwright, sin ninguna opción para ocultar la automatización y
sin resolver CAPTCHA. Si aparece un desafío, se detiene y lo anota.

No abre la pestaña Litigantes ni ningún PDF. Guarda capturas y un resumen en
la carpeta resultado/. No usa claves ni secretos.
"""
import json
import os
import re
import time
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

ROL = os.environ.get("ROL", "610")
ANIO = os.environ.get("ANIO", "2025")
CORTE = os.environ.get("CORTE", "90")        # C.A. de Santiago
TRIBUNAL = os.environ.get("TRIBUNAL", "288")  # 30º Juzgado Civil de Santiago
SALIDA = os.environ.get("SALIDA", "resultado")
PORTADA = "https://oficinajudicialvirtual.pjud.cl/home/index.php"

# Huellas de bloqueo del WAF F5/Shape (AVISO_WAF de Julio y ENTRAMPADOS.md).
FIRMAS_BLOQUEO = [
    "requested url was rejected",
    "your support id",
    "human visitor",
    "automated spam",
    "what code is in the image",
]
RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b")

pasos = []
t0 = time.time()


def ahora():
    return round(time.time() - t0, 1)


def texto_body(page):
    try:
        return page.inner_text("body", timeout=5000)
    except Exception:
        return ""


def captcha_visible(page):
    """reCAPTCHA con desafío visible (el invisible v3 no cuenta)."""
    try:
        for fr in page.query_selector_all("iframe[src*='recaptcha/api2/bframe']"):
            if fr.is_visible():
                return True
    except Exception:
        pass
    return False


def registrar(page, nombre, nota=""):
    os.makedirs(SALIDA, exist_ok=True)
    try:
        page.screenshot(path=os.path.join(SALIDA, f"{nombre}.png"), full_page=False)
    except Exception as e:
        nota += f" (sin captura, {type(e).__name__})"
    cuerpo = texto_body(page)
    bajo = cuerpo.lower()
    bloqueo = [f for f in FIRMAS_BLOQUEO if f in bajo]
    captcha = captcha_visible(page)
    try:
        cookies = sorted({c["name"] for c in page.context.cookies()})
    except Exception:
        cookies = []
    paso = {
        "paso": nombre,
        "segundos": ahora(),
        "url": page.url,
        "titulo": page.title() if page else "",
        "largo_texto": len(cuerpo),
        "firmas_bloqueo": bloqueo,
        "captcha_visible": captcha,
        "cookies_nombres": cookies,
        "nota": nota.strip(),
    }
    pasos.append(paso)
    print(json.dumps(paso, ensure_ascii=False))
    return bool(bloqueo) or captcha


def terminar(resultado, detalle=""):
    os.makedirs(SALIDA, exist_ok=True)
    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "causa": f"C-{ROL}-{ANIO}",
        "corte_value": CORTE,
        "tribunal_value": TRIBUNAL,
        "resultado": resultado,
        "detalle": RUT.sub("[RUT]", detalle)[:1500],
        "segundos_totales": ahora(),
        "pasos": pasos,
    }
    with open(os.path.join(SALIDA, "resumen.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    lineas = [
        "# Prueba OJV en la nube",
        "",
        f"Causa C-{ROL}-{ANIO}. Resultado **{resultado}** en {ahora()} s.",
        "",
        "| Paso | Segundos | Largo del texto | Firmas de bloqueo | CAPTCHA visible |",
        "|---|---|---|---|---|",
    ]
    for p in pasos:
        lineas.append(
            f"| {p['paso']} | {p['segundos']} | {p['largo_texto']} | "
            f"{', '.join(p['firmas_bloqueo']) or 'ninguna'} | {'sí' if p['captcha_visible'] else 'no'} |"
        )
    if detalle:
        lineas += ["", "Detalle", "", "```", RUT.sub("[RUT]", detalle)[:1500], "```"]
    md = "\n".join(lineas) + "\n"
    with open(os.path.join(SALIDA, "resumen.md"), "w", encoding="utf-8") as f:
        f.write(md)
    destino = os.environ.get("GITHUB_STEP_SUMMARY")
    if destino:
        with open(destino, "a", encoding="utf-8") as f:
            f.write(md)
    print(f"RESULTADO {resultado}")


def main():
    with sync_playwright() as p:
        # Chrome común del servidor. Sin argumentos extra, sin cambiar el agente
        # de usuario, sin tocar navigator.webdriver. Ventana visible con xvfb.
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(20000)

        # 1. Portada
        try:
            page.goto(PORTADA, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            registrar(page, "01_portada", f"goto falló {type(e).__name__}")
            return terminar("NO_CARGA_PORTADA", str(e))
        time.sleep(3)
        if registrar(page, "01_portada"):
            return terminar("BLOQUEO_EN_PORTADA", texto_body(page)[:600])

        # 2. Cerrar el aviso semanal y entrar a Consulta causas
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        time.sleep(2)
        try:
            page.click("text=Consulta causas", timeout=15000)
            page.wait_for_selector("#competencia", timeout=25000)
        except Exception as e:
            registrar(page, "02_formulario", f"no llegó al formulario {type(e).__name__}")
            return terminar("NO_LLEGA_AL_FORMULARIO", texto_body(page)[:600])
        time.sleep(3)
        if registrar(page, "02_formulario"):
            return terminar("BLOQUEO_EN_FORMULARIO", texto_body(page)[:600])

        # 3. Llenar el formulario a paso lento
        try:
            page.select_option("#competencia", label="Civil")
            time.sleep(3)
            page.wait_for_selector(f"#conCorte option[value='{CORTE}']", state="attached", timeout=20000)
            page.select_option("#conCorte", value=CORTE)
            time.sleep(3)
            page.wait_for_selector(f"#conTribunal option[value='{TRIBUNAL}']", state="attached", timeout=20000)
            page.select_option("#conTribunal", value=TRIBUNAL)
            time.sleep(2)
            try:
                page.select_option("#conTipoCausa", value="C", timeout=5000)
            except Exception:
                pass
            page.fill("#conRolCausa", ROL)
            time.sleep(1)
            page.fill("#conEraCausa", ANIO)
            time.sleep(2)
        except Exception as e:
            registrar(page, "03_formulario_lleno", f"falló al llenar {type(e).__name__}")
            return terminar("FALLA_AL_LLENAR", str(e)[:600])
        if registrar(page, "03_formulario_lleno"):
            return terminar("BLOQUEO_AL_LLENAR", texto_body(page)[:600])

        # 4. Buscar
        try:
            page.click("#btnConConsulta")
        except Exception as e:
            registrar(page, "04_buscar", f"no se pudo apretar Buscar {type(e).__name__}")
            return terminar("FALLA_AL_BUSCAR", str(e)[:600])
        time.sleep(10)
        bloqueado = registrar(page, "04_buscar")
        cuerpo = texto_body(page)
        if bloqueado:
            return terminar("BLOQUEO_AL_BUSCAR", cuerpo[:600])
        etiqueta = f"C-{ROL}-{ANIO}"
        if "No se han encontrado resultados" in cuerpo:
            return terminar("SIN_RESULTADOS", "La OJV respondió que no hay resultados")
        if etiqueta not in cuerpo:
            return terminar("RESULTADO_NO_RECONOCIDO", cuerpo[:600])

        # 5. Abrir el detalle de la fila exacta
        try:
            fila = page.locator("tr", has_text=etiqueta).first
            fila.locator("a").first.click()
        except Exception as e:
            registrar(page, "05_detalle", f"no se pudo abrir el detalle {type(e).__name__}")
            return terminar("ENCONTRADA_SIN_DETALLE", str(e)[:600])
        time.sleep(15)
        if registrar(page, "05_detalle"):
            return terminar("BLOQUEO_EN_DETALLE", texto_body(page)[:600])
        try:
            encabezado = page.inner_text("#modalDetalleCivil", timeout=10000)
        except Exception:
            encabezado = ""
        proc = re.search(r"Proc\.?:\s*(.+)", encabezado)
        try:
            cuadernos = [o.inner_text().strip() for o in page.query_selector_all("#modalDetalleCivil select option")]
        except Exception:
            cuadernos = []
        detalle = (
            f"Procedimiento {proc.group(1).strip() if proc else 'no leído'}\n"
            f"Cuadernos {cuadernos}\n"
            f"Encabezado {encabezado[:400]}"
        )
        terminar("LLEGA_AL_DETALLE" if encabezado else "DETALLE_VACIO", detalle)
        browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        terminar("ERROR_INESPERADO", f"{type(e).__name__}: {e}")
