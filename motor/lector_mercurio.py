"""Lectura de una edición de El Mercurio Digital (parte con internet).

Recorre TODOS los cuerpos del día, lee el texto de cada página con el visor del propio diario
(PDFViewerApplication del visor, igual que lo vería una persona) y entrega las páginas a
navegacion_logica.ordenar(), que decide qué páginas tienen remates y en qué orden se pegan.

Uso, desde D:\\Agendar_Remates con el entorno activado.
    python -m motor.lector_mercurio --fecha 2026-10-14
    python -m motor.lector_mercurio --fecha 2026-10-14 --visible      (muestra el navegador)
    python -m motor.lector_mercurio --fecha 2026-10-14 --union espacio (formas alternativas de unir el texto, solo para pruebas)
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, sys
from datetime import date, datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import config  # noqa: E402  (config.py está fuera de git)
from motor.navegacion_logica import Pagina, analizar_pagina, ordenar  # noqa: E402
# Mercurio (17 de Octubre de 2026). Su config.py no trae estas dos rutas y se edita a mano en el PC del abogado.
# Se usan las del config si existen, si no el perfil de navegador que ya usa el Mercurio y la carpeta capturas.
PERFIL_NAVEGADOR = Path(getattr(config, "PERFIL_NAVEGADOR", RAIZ / "playwright_profile"))
CAPTURAS = Path(getattr(config, "CAPTURAS", RAIZ / "capturas"))

_T0 = datetime.now()
_LOG = None
def avance(msg: str) -> None:
    """Registro de avance con hora, en pantalla y en logs/lectura_AAAA-MM-DD.log. Sirve para saber dónde se detiene."""
    linea = f"[{datetime.now():%H:%M:%S} +{(datetime.now() - _T0).total_seconds():6.1f}s] {msg}"
    print(linea, flush=True)
    if _LOG:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(linea + "\n")

LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Funciones que corren DENTRO de la página del visor. Mismo método probado en Chrome el 2026-10-14.
JS_LISTAR_CUERPOS = r"""
async ([d, letras]) => {
  const out = {};
  for (const s of letras) {
    let html = '';
    try { html = await (await fetch(`/${d}/${s}`)).text(); } catch (e) { continue; }
    const fe = (html.match(/fechaEdicion\s*=\s*['"]([\d\/]+)['"]/) || [])[1] || '';
    const ids = [...new Map([...html.matchAll(/gotoPage\s*\(\s*'(\w)'\s*,\s*'([^']+)'\s*,\s*(\d+)/g)]
                 .filter(m => m[1] === s).map(m => [m[2], +m[3]])).entries()].sort((a, b) => a[1] - b[1]);
    if (ids.length) out[s] = { fe, ids };
  }
  return out;
}
"""

JS_LEER_PAGINAS = r"""
async ([rutas, paralelo, union, timeout]) => {
  const leer = (ruta) => new Promise(res => {
    const f = document.createElement('iframe');
    f.style.cssText = 'position:fixed;left:-3000px;top:0;width:900px;height:1200px';
    f.src = ruta; const t0 = Date.now(); let ocupado = false;
    const tick = async () => {
      if (ocupado) return;
      let app = null; try { app = f.contentWindow.PDFViewerApplication; } catch (e) {}
      if (app && app.pdfDocument) {
        ocupado = true;
        try {
          const pg = await app.pdfDocument.getPage(1); const tc = await pg.getTextContent();
          // union 'salto' = renglones unidos por salto de línea, igual que el texto del visor (verificado contra el banco el 2026-10-14)
          const txt = union === 'salto' ? tc.items.map(it => it.str).join('\n')
                    : tc.items.map(it => it.str + (it.hasEOL ? '\n' : union)).join('');
          // Posición de cada renglón en la página (x, y, ancho, alto). Sirve para ordenar columnas por cómo están impresas.
          const geo = tc.items.map(it => [it.str, +it.transform[4].toFixed(1), +it.transform[5].toFixed(1), +(it.width || 0).toFixed(1), +(it.height || 0).toFixed(1)]);
          const vista = pg.getViewport({ scale: 1 });
          f.remove(); return res({ ruta, ok: true, txt, items: tc.items.length, geo, ancho: vista.width, alto: vista.height });
        } catch (e) { f.remove(); return res({ ruta, ok: false, err: String(e) }); }
      }
      if (Date.now() - t0 > timeout) { f.remove(); return res({ ruta, ok: false, err: 'tiempo agotado' }); }
      setTimeout(tick, 400);
    };
    f.onload = () => setTimeout(tick, 300); document.body.appendChild(f);
  });
  const resultados = new Array(rutas.length); let i = 0;
  async function trabajador() { while (i < rutas.length) { const k = i++; resultados[k] = await leer(rutas[k]); } }
  await Promise.all(Array.from({ length: paralelo }, trabajador));
  return resultados;
}
"""


async def _esta_logueado(page: Page) -> bool:
    try:
        btn = page.locator("#openPram")
        if not await btn.is_visible():
            return True
        return "iniciar" not in (await btn.inner_text()).strip().lower()
    except Exception:
        return False


async def _login(page: Page) -> None:
    if not config.MERCURIO_USER or not config.MERCURIO_PASS:
        raise RuntimeError("Faltan MERCURIO_USER y MERCURIO_PASS en config.py")
    await page.locator("#openPram > span").click()
    await page.wait_for_timeout(1000)
    await page.locator("#txtUsername").fill(config.MERCURIO_USER)
    await page.locator("#txtPassword").fill(config.MERCURIO_PASS)
    async with page.expect_navigation(timeout=30_000):
        await page.locator("#gopram").click()
    await page.wait_for_timeout(1500)
    for _ in range(2):
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
    if not await _esta_logueado(page):
        raise RuntimeError("Login fallido. Revisa MERCURIO_USER y MERCURIO_PASS en config.py")


async def _activar_hd(page: Page, url_pagina: str) -> None:
    """El visor muestra imágenes en modo normal. Solo en modo HD carga el documento con texto.
    Mismos selectores que usa el Mercurio (modulo1_mercurio._click_hd_btn). El modo HD queda activo para la sesión."""
    avance(f"Abriendo {url_pagina} para activar HD")
    await page.goto(url_pagina, wait_until="domcontentloaded", timeout=60_000)
    await page.wait_for_timeout(3000)
    listo = "() => !!(window.PDFViewerApplication && window.PDFViewerApplication.pdfDocument)"
    if await page.evaluate(listo):
        avance("HD ya estaba activo")
        return
    for intento in (1, 2):
        for selector in ("div.toolbar div.cont_activar_pdf > span:nth-of-type(1) img", "#inactive_pdf img"):
            boton = page.locator(selector).first
            try:
                if await boton.is_visible(timeout=4000):
                    await boton.click()
                    avance(f"Botón HD presionado (intento {intento}, selector {selector})")
                    break
            except Exception:
                continue
        for _ in range(40):
            await page.wait_for_timeout(500)
            if await page.evaluate(listo):
                avance("HD activo. El visor cargó el documento")
                return
    raise RuntimeError("No se pudo activar el modo HD del visor. Sin HD el diario solo entrega imágenes y no hay texto que leer")


async def leer_edicion(fecha: date, visible: bool = False, union: str = "salto", paralelo: int = 4) -> dict:
    global _LOG
    d = f"{fecha.year}/{fecha.month:02d}/{fecha.day:02d}"
    inicio = datetime.now()
    (RAIZ / "logs").mkdir(exist_ok=True)
    _LOG = RAIZ / "logs" / f"lectura_{fecha.isoformat()}.log"
    avance(f"Inicio lectura {d}. visible={visible} union={ {'salto': 'salto', ' ': 'espacio', '': 'sin_separador'}[union] } paralelo={paralelo}")
    avance("Iniciando Playwright")
    async with async_playwright() as pw:
        avance(f"Abriendo navegador con perfil {PERFIL_NAVEGADOR}")
        ctx = await pw.chromium.launch_persistent_context(str(PERFIL_NAVEGADOR), headless=not visible)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        avance(f"Navegador abierto. Cargando {config.MERCURIO_BASE_URL}/{d}/A")
        await page.goto(f"{config.MERCURIO_BASE_URL}/{d}/A", wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(2500)
        avance(f"Portada cargada. Título '{await page.title()}'")
        if not await _esta_logueado(page):
            avance("Sin sesión. Haciendo login")
            await _login(page)
            avance("Login hecho. Recargando portada")
            await page.goto(f"{config.MERCURIO_BASE_URL}/{d}/A", wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_timeout(2500)
        else:
            avance("Sesión ya activa")

        avance("Listando cuerpos del día")
        cuerpos = await page.evaluate(JS_LISTAR_CUERPOS, [d, LETRAS])
        avance("Cuerpos encontrados. " + (", ".join(f"{s}({v['fe']}, {len(v['ids'])} págs)" for s, v in sorted(cuerpos.items())) or "ninguno"))
        notas, alarmas, paginas = [], [], []
        if not cuerpos:
            alarmas.append("El sitio no devolvió ningún cuerpo para esta fecha")
        else:
            s0, info0 = sorted(cuerpos.items())[0]
            await _activar_hd(page, f"{config.MERCURIO_BASE_URL}/{d}/{s0}/{info0['ids'][0][0]}#zoom=page-width")
        for s, info in sorted(cuerpos.items()):
            if info["fe"].replace("/", "") != d.replace("/", ""):
                notas.append(f"Cuerpo {s} trae la edición {info['fe'] or 'sin fecha'}, no la del {d}. No se lee")
                continue
            rutas = [f"/{d}/{s}/{pid}" for pid, _ in info["ids"]]
            res = []
            for k in range(0, len(rutas), paralelo):
                tanda = rutas[k:k + paralelo]
                avance(f"Cuerpo {s}. Leyendo páginas {k + 1} a {k + len(tanda)} de {len(rutas)}")
                r_tanda = await page.evaluate(JS_LEER_PAGINAS, [tanda, paralelo, union, 45_000])
                avance(f"Cuerpo {s}. Tanda lista. " + ", ".join(
                    (f"{x['ruta'].split('/')[-1]} ok {len(x['txt'])} car" if x["ok"] else f"{x['ruta'].split('/')[-1]} FALLA {x.get('err')}") for x in r_tanda))
                res.extend(r_tanda)
            # Reintento uno a uno de las que fallaron
            for k, r in enumerate(res):
                if not r["ok"]:
                    avance(f"Reintentando {r['ruta']}")
                    r2 = (await page.evaluate(JS_LEER_PAGINAS, [[r["ruta"]], 1, union, 90_000]))[0]
                    res[k] = r2
            for (pid, num), r in zip(info["ids"], res):
                if not r["ok"]:
                    alarmas.append(f"No se pudo leer {s}{num} ({pid}). {r.get('err')}")
                    continue
                pg = analizar_pagina(Pagina(s, num, pid, r["txt"]))
                pg.geo = {"ancho": r.get("ancho"), "alto": r.get("alto"), "items": r.get("geo")}
                paginas.append(pg)
        await ctx.close()

    avance(f"Navegador cerrado. {len(paginas)} páginas leídas. Ordenando")
    resultado = ordenar(paginas)
    carpeta = CAPTURAS / fecha.isoformat()
    carpeta.mkdir(parents=True, exist_ok=True)
    resumen_paginas = []
    for p in paginas:
        if p.cornisas or p.salidas or p.entradas:
            nombre = f"{p.cuerpo}{p.numero:02d}_{p.id_pagina}.txt"
            (carpeta / nombre).write_text(p.texto, encoding="utf-8", newline="")
            (carpeta / nombre.replace(".txt", ".geo.json")).write_text(json.dumps(getattr(p, "geo", None), ensure_ascii=False), encoding="utf-8")
            resumen_paginas.append({"pagina": p.nombre, "id": p.id_pagina, "archivo": nombre,
                                    "cornisas": p.cornisas, "salidas": p.salidas, "entradas": p.entradas,
                                    "caracteres": len(p.texto),
                                    "sha256": hashlib.sha256(p.texto.encode("utf-8")).hexdigest()})
    informe = {
        "fecha": fecha.isoformat(), "leida_en": inicio.isoformat(timespec="seconds"),
        "segundos": round((datetime.now() - inicio).total_seconds()),
        "union_texto": {"salto": "salto", " ": "espacio", "": "sin_separador"}[union],
        "cuerpos": {s: f"{v['fe']} n={len(v['ids'])}" for s, v in sorted(cuerpos.items())},
        "paginas_leidas": len(paginas),
        "paginas_con_remates": resumen_paginas,
        "rollos": [[p.nombre for p in r] for r in resultado.rollos],
        "alarmas": alarmas + resultado.alarmas, "notas": notas + resultado.notas,
    }
    avance("Guardando capturas y navegacion.json")
    (carpeta / "navegacion.json").write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
    return informe


def main():
    ap = argparse.ArgumentParser(description="Lee una edición de El Mercurio y arma el orden de las páginas de remates")
    ap.add_argument("--fecha", required=True, help="AAAA-MM-DD")
    ap.add_argument("--visible", action="store_true")
    ap.add_argument("--union", choices=["salto", "sin_separador", "espacio"], default="salto")
    a = ap.parse_args()
    inf = asyncio.run(leer_edicion(date.fromisoformat(a.fecha), a.visible, {"salto": "salto", "espacio": " ", "sin_separador": ""}[a.union]))
    print(f"Edición {inf['fecha']} leída en {inf['segundos']} s. Cuerpos {inf['cuerpos']}. Páginas leídas {inf['paginas_leidas']}")
    print("Rollos.", " | ".join("-".join(r) for r in inf["rollos"]) or "ninguno")
    for n in inf["notas"]: print("Nota.", n)
    for al in inf["alarmas"]: print("ALARMA.", al)
    print("Detalle en", CAPTURAS / inf["fecha"] / "navegacion.json")


if __name__ == "__main__":
    main()
