# Prompt Maestro: Extractor El Mercurio Digital (RM)
# Versión 3.0 — 2026-07-03

> **Reemplaza íntegramente** a `PROMPT_MAESTRO_MERCURIO_v2_0.md` (última versión interna: 2.3, 2026-03-23), eliminado del repositorio junto con la publicación de este documento.
>
> Cambios mayores acumulados desde la 2.3: migración del motor de extracción a **DeepSeek V4-Flash** (ciclo mayo 2026), **filtro de dominio vigente (CBR)**, **paralelización de M1**, y **eliminación completa de la capa PJUD/OJV** (julio 2026).
>
> **Principio rector de este documento:** ante cualquier discrepancia entre lo aquí descrito y el código en disco, **el árbitro es el código**. Este maestro se audita contra `main.py`, `modulo1_mercurio.py` y `modulo5_reporte.py`, no al revés.

---

## ⚠️ ESTADO MAYOR (julio 2026) — LA CAPA PJUD YA NO EXISTE

El PJUD desplegó un **WAF F5 BIG-IP con módulo anti-bot Shape Security** en la Oficina Judicial Virtual, operando 24/7, que bloquea el acceso automatizado con CAPTCHA visual. El bloqueo es probabilístico, ocurre incluso con navegador visible e IP residencial, y no existe ajuste de código que garantice acceso permanente.

En consecuencia, el 2026-07-03 se eliminó por completo la capa PJUD del pipeline:

- **Commits:** `53d757c` (documentación previa del motor OJV) + `8edd5ee` (cirugía).
- **Eliminados del repo:** `modulo2_ojv.py`, `ojv_remates.py`, `modulo3_extractor.py`.
- **Eliminados del flujo:** consulta OJV, sobrescritura de litigantes, descarga de mandamientos/bases, extracción de montos (M3) y el filtro de deuda > $300.000.000 CLP.

**PROHIBIDO reintroducir cualquier acceso automatizado al PJUD sin decisión explícita de Diego.**

Referencias permanentes:
- `El_backend_proyecto_RM_PJUD.md` — el motor OJV documentado función por función, con selectores DOM reales, para replicación futura si las condiciones cambian.
- `AVISO_WAF_PJUD_para_otros_proyectos.md` — firma técnica del WAF (cookies `TS*`, rutas `/TSPD/`, página de desafío) y cómo detectar el bloqueo.

---

## CONTEXTO Y OBJETIVO

Este proyecto extrae avisos de remates judiciales de propiedades desde **El Mercurio Digital** (sección Clasificados, código **1616**) usando **Playwright + DeepSeek V4-Flash**, leyendo el **textLayer** del visor PDF (NO Vision API, NO imágenes).

El módulo central es `modulo1_mercurio.py`: scrapea el diario digital, extrae el texto de las páginas relevantes vía textLayer, y usa la API de extracción para parsear los avisos en datos estructurados. Su output alimenta directamente a M5 (reporte Excel).

**Pipeline actual: M1 (extracción Mercurio) → M5 (reporte Excel). Nada más.**

**Foco de negocio: EXCLUSIVAMENTE Región Metropolitana** (Corte de Santiago y Corte de San Miguel).

---

## ARQUITECTURA

```
D:\Mercurio\
├── main.py                    ← orquestador (--fecha YYYY-MM-DD, --demo, --hasta, etc.)
├── modulo1_mercurio.py        ← M1: scraper Mercurio Digital + API extracción + filtros
├── modulo5_reporte.py         ← M5: reporte Excel + actualización de historial
├── filtro_cbr.py              ← solo aporta la constante _CBR_ANIO_CORTE = 2020
│                                (su heurística evaluar_antiguedad_cbr NO se usa en RM)
├── extrae_texto.py            ← auxiliar de extracción de texto
├── config.py                  ← GITIGNORED: credenciales Mercurio + claves API (Anthropic, DeepSeek)
├── config_template.py         ← semilla trackeada de config.py (sin secretos)
├── causas_ojv.xlsx            ← BD interna (ver nota abajo)
├── limpiar_cache.py           ← limpieza de caché y descargas
├── requirements.txt           ← playwright, anthropic, openai, openpyxl, rapidfuzz
├── ejecutar_mercurio.bat      ← ejecución manual (doble click = hoy)
├── cronometro_mercurio.bat    ← ejecución programada 5am con reintentos
├── instalar_mercurio.bat      ← instalación de entorno
├── logs\                      ← un .log por ejecución (UTF-8)
├── Descargas\                 ← HISTÓRICA: PDFs de la era OJV (la gestiona limpiar_cache.py)
├── Informe final\             ← reportes Excel finales
├── El_backend_proyecto_RM_PJUD.md
└── AVISO_WAF_PJUD_para_otros_proyectos.md
```

- **Todas las rutas centralizadas en `config.py` con `BASE_DIR` relativo.** Proyecto 100% independiente de `D:\Remates\` y portable.
- **GitHub:** `https://github.com/DFNR2026/RematesMercurio`.
- **Espejo operativo:** `E:\Mercurio` (PC del abogado, corre el cron de las 5am). Su `config.py` está gitignored y **se edita a mano** en cada cambio de constantes: no viaja por git.

**`causas_ojv.xlsx` — advertencia de nombre:** pese al nombre, es insumo de **M1**, no de la extinta capa OJV. Hoja **REFERENCIA** (233 tribunales, para el fuzzy de cortes) + hoja **CAUSAS** (historial para deduplicación). NO borrar, NO renombrar, NO modificar la hoja REFERENCIA.

---

## MOTOR DE EXTRACCIÓN (DeepSeek V4-Flash)

- `config.py`: `MODELO_EXTRACCION = "deepseek"` | `"sonnet"`. **Rollback a Sonnet cambiando la constante, sin tocar código.**
- Modelo `deepseek-v4-flash` vía SDK de OpenAI (`base_url=https://api.deepseek.com`), modo Non-Thinking, `max_tokens=16384`.
- **Resiliencia:** 3 intentos por llamada, timeout 120s. Un JSON truncado lanza `ValueError` que dispara el reintento; un `[]` legítimo NO reintenta. (Lección de mayo: el truncamiento era de RED —timeout de pasarela—, no de tokens; el fix correcto es reintento + timeout, no bajar `max_tokens`.)
- **Paralelización:** `ThreadPoolExecutor` con 3 workers. Las páginas grandes se dividen en fragmentos (`pagina.0`, `pagina.1`, …) enviados en paralelo.
- **Métricas:** `st.tokens_input` / `st.tokens_output` acumulan el `usage` de cada llamada; el canal lateral `obtener_metricas()` las lleva a M5 (hoja Resumen) sin cambiar la firma de `extraer_mercurio`.
- **Costo:** ~USD 0.01–0.02 por corrida (referencia real 2026-07-03: USD 0.0123, 58K tokens). Mensual estimado: < USD 0.5.

---

## CONTRATO DE DATOS (M1 → M5)

`extraer_mercurio(fecha)` retorna una lista de dicts. Campos que produce la API de extracción por aviso:

```python
{
    "rol": "32342",                    # str — número del ROL (sin "C-")
    "año": "2015",                     # str — año del ROL (C-XXXXX-YYYY)
    "tribunal": "1° Juzgado Civil de Santiago",
    "demandante": "Banco Itaú",        # parcial del diario (YA NO se sobrescribe con OJV)
    "demandado": "Pérez",              # parcial del diario (YA NO se sobrescribe con OJV)
    "direccion": "Av. Matta 1234, depto 501",   # str o None
    "comuna": "Santiago",              # str o None
    "fecha_remate": "30/07/2026",      # str o None
    "año_inscripcion_dominio": "2015", # str "YYYY" o None — año del dominio en el CBR
    "fojas": "66273",                  # str (ej. "1234" o "1234 vta.") o None
}
```

Campos que agrega el post-proceso de M1:

```python
{
    "corte": "C.A. de Santiago",       # buscar_corte (RapidFuzz 80) + fallback keywords
    "region_rm": True,                 # SIEMPRE True
    "cbr_anio": 2015,                  # resultado de _evaluar_cbr_por_anio
    "cbr_flag_revision": False,        # True si el caso quedó en REVISAR
    "cbr_motivo": "",                  # motivo cuando flag_revision es True
}
```

Si esta estructura cambia, M5 se rompe.

---

## FLUJO DE modulo1_mercurio.py

### Paso 1: Navegar al cuerpo A
`https://digital.elmercurio.com/YYYY/MM/DD/A` — Playwright con perfil persistente. Fecha por defecto: hoy; manual con `--fecha YYYY-MM-DD`.

### Paso 2: Login
- Credenciales desde `config.py` (`MERCURIO_USER`, `MERCURIO_PASS`). Si hay sesión activa, se omite el login pero se cierran modales igual.
- Cierre de modales: primero genérico vía jQuery (`$('.modal.in, .modal.show').modal('hide')`), luego Escape ×2, luego IDs conocidos (`#modal_mer_promoLS`, `#modal_mer_promoINV`, `#modal_mer_selectHome`).
- Timeout: 30s → si falla, abort total.

### Paso 3: Sección de clasificados (cadena F → D → B)
1. Click en Clasificados → intenta sección **F**. `_navegar_a_sección_f()` retorna `bool` (tolerante a fallos).
2. Verificar `fechaEdicion` (variable JS, formato "YYYY/MM/DD") contra la fecha solicitada.
3. Si F falla o la fecha no coincide:
   - **Fin de semana:** URL directa a sección **D** → verificar fecha → si falla, **B** como último recurso.
   - **Día hábil (L-V):** URL directa a sección **B** (Economía y Negocios) → verificar fecha.
4. Ninguna sección con la fecha → `raise EdicionNoDisponible` → `sys.exit(2)` (el cronometro reintenta).

**¿Por qué D?** Los fines de semana los clasificados salen en una sección D independiente, accesible solo por URL directa; F queda stale. **¿Por qué B?** De lunes a viernes, cuando F no se actualiza, los clasificados aparecen al final de B.

### Paso 4: Mapa de páginas
Extraer los page IDs de la sección activa. El recorrido inicia en la **última** página.

### Paso 5: Activar HD (una sola vez)
Esperar canvas base (width > 0) → click botón HD (+ retry si no responde) → verificar `canvas.width > 1800` (esperado 1950px). HD persiste toda la sesión; buffer 2s post-renderizado. HD mejora la calidad del textLayer.

### Paso 6: Recorrido de páginas
La numeración de secciones es **CRECIENTE** (1611 → 1612 → 1616 → 1635…).

```
LOOP (desde la última hacia atrás, tope 15 páginas):
  1. Buffer 2s
  2. Leer textLayer COMPLETO
  3. DECISIÓN:
     - Sin "1616"                              → descartar, seguir
     - Con "1616" solo                         → conservar texto, seguir
     - Con "1616" + sección menor (1611-1615)  → conservar texto, PARAR
```

La condición de parada detecta el borde superior de la sección 1616. No se capturan imágenes.

**Paso 6b — cachito de 1616 en B:** si la sección primaria NO es B, revisar las 3 últimas páginas de B (avisos 1616 sueltos). El dedup del Paso 8 elimina duplicados. HD persiste.

**Paso 6c — redirección a otra sección:** buscar en TODAS las páginas conservadas el patrón:
```
r"MÁS\s+AVISOS\s+ECON[OÓ]MICOS\s*CLASIFICADOS\s+EN\s+PÁG\.?\s*([A-Z])\s+(\d+)"
```
Si hay match (típicamente hacia sección **C** — Nacional): navegar a la sección/página indicada y leer **hacia adelante** mientras haya 1616. Si la navegación falla → warning, continúa. **No recortar el payload por "1616"**: los avisos se dispersan entre columnas y recortar pierde causas válidas (el costo por página es ~1 centavo, la completitud vale más).

### Paso 7: Envío a la API de extracción
El texto de cada página/fragmento conservado se envía al motor configurado (ver **MOTOR DE EXTRACCIÓN**). El prompt canónico vive en `modulo1_mercurio.py::PROMPT_EXTRACCION` — **el texto exacto se consulta en el código, no aquí**. Su contrato: reconstruir palabras cortadas por guiones, extraer TODOS los avisos de la sección 1616 (ignorar 1611/1612/1615), no inventar datos (campo no identificable → `null`), y devolver ÚNICAMENTE un JSON array con los 10 campos del contrato de datos.

> **Regla histórica:** existió un campo `texto_dominio` (cláusula verbatim del CBR) que se ELIMINÓ porque inflaba la salida y causaba truncamiento por timeout de pasarela. **No reintroducir** sin resolver el truncamiento.

### Paso 8: Post-procesamiento y filtros
1. **Parsear ROL** (`C-XXXXX-YYYY` → número + año). Aviso sin ROL parseable → descartado con log del dict completo.
2. **Limpiar tribunal:** `_limpiar_tribunal()` (guiones silábicos) + `_normalizar_ordinal_tribunal()`.
3. **Tribunal → corte:** `buscar_corte()` con RapidFuzz (umbral **80**) contra hoja REFERENCIA + validación ordinal. Fallback por keywords: "Santiago" → C.A. de Santiago; "San Miguel"/"Buin"/"Puente Alto"/"Talagante"/"Colina"/"Melipilla"/"Peñaflor"/"San Bernardo" → C.A. de San Miguel.
4. **Filtro CBR** (ver sección propia): EXCLUIR / MANTENER / REVISAR según `año_inscripcion_dominio`.
5. **Filtro RM:** solo C.A. de Santiago y C.A. de San Miguel.
6. **Filtro Banco Estado:** descartar "Banco Estado" / "Banco del Estado".
7. **Filtro Estación Central:** descartar comuna "Estación Central".
8. **Filtro año:** descartar año de ROL < 2018 o no parseable.
9. **Dedup historial** (hoja CAUSAS) + **dedup ejecución** (entre páginas).
10. `region_rm = True`.

> **El filtro de deuda > $300M ya no existe** (dependía de M3, eliminado).

---

## FILTRO DE DOMINIO VIGENTE (CBR)

Regla de negocio del abogado: **no deben llegar al Excel causas cuyo dominio fue inscrito en el Conservador de Bienes Raíces en 2020 o después.**

La decisión es **determinista** y se toma sobre el año que extrae la IA (`año_inscripcion_dominio`), NO sobre texto crudo. Función `_evaluar_cbr_por_anio(anio_raw)` en `modulo1_mercurio.py`, cuatro ramas:

| Condición | Veredicto |
|---|---|
| 2020 ≤ año ≤ 2027 | **EXCLUIR** (no entra al pipeline; se acumula en `st.excluidos_cbr`) |
| 1900 ≤ año < 2020 | **MANTENER** |
| null / vacío / no parseable a 4 dígitos | **REVISAR** — "Año CBR no detectado" |
| fuera de rango 1900–2027 | **REVISAR** — "Año CBR fuera de rango" (atrapa alucinaciones de la IA) |

**Salvaguarda anti-borrado-silencioso:** un fallo de extracción JAMÁS elimina una causa; el peor caso es REVISAR (se conserva y se marca en la columna `CBR Motivo`).

En el Excel, la **tabla de transparencia** "PROPIEDADES NUEVAS EXCLUIDAS (dominio >= 2020)" (Tribunal / ROL / Año / Año Dominio, deduplicada por ROL) permite al abogado ver qué se filtró — evita que un Excel corto parezca un fallo del bot.

`filtro_cbr.py` se conserva solo por la constante `_CBR_ANIO_CORTE = 2020`; su heurística por regex (`evaluar_antiguedad_cbr`) es la que usa el proyecto **Regiones**, no RM.

---

## REPORTE EXCEL (modulo5_reporte.py)

Estructura verificada (2026-07-03):

- **Hoja de causas** (primera): columnas `ROL, Año, Corte, Tribunal, Demandante, Demandado, Dirección, Comuna, Fs., CBR Motivo, Fechas Public., Fecha Remate`. Ordenada por corte (Santiago primero, San Miguel segundo) y luego tribunal ascendente.
- Debajo de la tabla principal: **"PROPIEDADES NUEVAS EXCLUIDAS (dominio >= 2020)"** y **"CAUSAS DESCARTADAS POR PARÁMETROS"** (esta última la alimenta M1: Solo RM, Banco Estado, Estación Central, Pre-2018; su columna Monto queda vacía por diseño — cabo cosmético conocido).
- **Hoja Resumen (AL FINAL):** totales + MÉTRICAS DE EXTRACCIÓN (tokens entrada/salida, costo USD si el motor es deepseek).
- `actualizar_historial()` hace APPEND de las causas nuevas a la hoja CAUSAS.

Ya NO existen: columnas de deuda/monto, Tipo Proc., Motivo Fallo, sección "VALIDACIÓN OJV", ni el tablero de consola "CON DEUDA / SIN PDF / SIN MONTO".

---

## MANEJO DE ERRORES

| Operación | Timeout | Acción si falla |
|-----------|---------|-----------------|
| Login El Mercurio | 30s | Abort total |
| Click Clasificados (→F) | 15s | Retorna False → fallback D/B |
| Verificación fecha F / D / B | — | Cadena F→D→B → `EdicionNoDisponible` → `sys.exit(2)` |
| Cachito B (6b) / Redirección (6c) | — | Warning, continúa sin cachito |
| Navegación entre páginas | 10s | Saltar página, continuar |
| Renderizado HD (width > 1800) | 20s | Retry click |
| Buffer post-renderizado | 2s | Fijo |
| API por página/fragmento | 120s | 3 intentos; JSON truncado → ValueError → reintento; `[]` legítimo NO reintenta |
| Respuesta no es JSON válido | — | Log del raw, skip fragmento |

Una página falla → se salta y se procesan las demás. Edición no disponible → exit code 2 para que el cronometro reintente.

---

## EJECUCIÓN

```bash
# Manual, fecha de hoy (doble click) o específica
ejecutar_mercurio.bat
ejecutar_mercurio.bat 2026-07-03

# Programada: espera hasta las 5am, ejecuta, reintenta cada 30 min si no hay edición (máx 6, vía exit code 2)
cronometro_mercurio.bat

# Solo M1, sin API ni costo (~30s): navegación de prueba
python modulo1_mercurio.py --fecha 2026-07-03 --dry-run

# Prueba del tramo post-M1 sin red ni API (25 causas sintéticas → M5)
python main.py --demo
```

**⚠️ `--demo` escribe en producción:** agrega 25 roles sintéticos (30001–30025) al historial CAUSAS. Protocolo obligatorio: respaldar `causas_ojv.xlsx` antes, restaurar después, borrar el Excel sintético generado.

**Flags de `main.py`:** `--fecha YYYY-MM-DD` · `--demo` · `--hasta N` (**1..4 = detiene tras M1; 5 = pipeline completo M1→M5, default**) · `--silencio` · `--limpiar-historial` · `--diarios` (semántica exacta de los tres últimos: `python main.py --help`). El flag `--sin-ojv` fue **eliminado** en la cirugía de julio.

---

## LOGGING

Cada ejecución genera `logs/mercurio_YYYY-MM-DD_HHMMSS.log` (UTF-8) con salida dual CMD + archivo, formato `[HH:MM:SS] NIVEL — mensaje`. Registra: textLayer (300 chars) y secciones detectadas por página, decisión por página (conservar/descartar/parar), sección utilizada (F/D/B), cachitos 6b/6c, avisos raw por página, mapeo tribunal→corte con score, descartes CBR y por filtro (uno a uno), tabla de filtros con conteos (X → Y), y resumen final con tokens y costo.

> Cabo cosmético conocido: el resumen aún imprime la etiqueta "Avisos Vision" (herencia de la v1.0); son avisos de la API de texto.

---

## REGLAS INAMOVIBLES

- **NO reintroducir la capa OJV/PJUD** sin decisión explícita de Diego (WAF activo; ver ESTADO MAYOR).
- NO implementar tasación automatizada (M4 no existe).
- NO modificar la hoja REFERENCIA de `causas_ojv.xlsx`; no borrar ni renombrar el archivo.
- NO tocar módulos estables sin mapearlos primero (PLAN/auditoría antes que ACT).
- Credenciales y claves API SOLO en `config.py` (gitignored); nunca hardcodeadas en otros archivos ni pegadas en chats.
- Canvas HD obligatorio (umbral width > 1800).
- RapidFuzz umbral **80** en M1.
- `region_rm = True` siempre.
- **Filtros de negocio vigentes:** solo RM, no-BancoEstado, no-EstaciónCentral, año ROL ≥ 2018, dominio CBR < 2020. (El filtro de deuda > $300M **ya no existe**.)
- Salvaguarda CBR: extracción fallida → REVISAR, nunca EXCLUIR en silencio.
- No reintroducir `texto_dominio` en el prompt de extracción.
- No recortar el payload de página por "1616".

---

## REGLAS DE OPERACIÓN CON AGENTES (Cline / Claude Code)

Resumen operativo (la versión completa vive en las instrucciones del proyecto de Claude.ai):

- Diego NO ejecuta terminal ni git: todo lo corre un agente con pasos numerados y **condiciones de detención**; Diego pega los reportes.
- `git status --short` antes de todo commit; staging con `git add <archivo>` explícito. PROHIBIDO `-am`, `add .`, `add -A`, `reset --hard`, `clean`, y `pull`/`rebase`/`fetch+merge` fuera de guion.
- `git push` solo con visto bueno explícito de Diego tras validación. Un commit = una historia.
- Validación por **predicción numérica** fijada ANTES de correr; aciertos exactos o se detiene y audita.
- El relato del agente se audita contra el código: pedir verbatim, no confiar en resúmenes.

---

## DOM REFERENCE (El Mercurio)

- Canvas: `id=page1`, HD width > 1800px (esperado 1950)
- HD activar: `#inactive_pdf` / fallback botón toolbar · HD desactivar: `#active_pdf`
- Text layer: `div.textLayer`
- Fecha edición: variable JS `fechaEdicion` ("YYYY/MM/DD")
- Login: `#openPram > span` → `#txtUsername` → `#txtPassword` → `#gopram`
- Modales: `#modal_mer_promoLS`, `#modal_mer_promoINV`, `#modal_mer_selectHome`; cierre genérico `$('.modal.in, .modal.show').modal('hide')`
- Clasificados: `#uctHeader_ctl02_rptBodyPart_ctl07_aBody` · Economía y Negocios: `#uctHeader_ctl02_rptBodyPart_ctl01_aBody`
- Navegación: `gotoPage('F'|'B'|'D'|'C','ID',N)` · URL: `/YYYY/MM/DD/{F|B|D|C}/PAGE_ID#zoom=page-width`
- Sección C (Nacional): `#TdBody3 > a` o URL directa · Sección D: solo URL directa (fines de semana)
- Redirección: textLayer con `MÁS AVISOS ECONÓMICOS` + `CLASIFICADOS EN PÁG. {X} {N}` (dos nodos div consecutivos)

---

## DOCUMENTOS DEL ECOSISTEMA

| Documento | Rol |
|---|---|
| `CIERRE_CICLO_MERCURIO_2026-05.md` | Cierre histórico del ciclo mayo (DeepSeek, CBR, paralelización). Nota: su afirmación "deuda extirpada" describía la intención; en código, M2/M3 siguieron activos hasta la cirugía de julio. |
| `ADDENDUM_MERCURIO_2026-06-12.md` | Reglas de método (git vía agentes, validación numérica, auditoría verbatim) + cierre de mentoría a Regiones. |
| `El_backend_proyecto_RM_PJUD.md` | Motor OJV documentado verbatim antes de su eliminación (commit `53d757c`). Base de replicación si el WAF cambia. |
| `AVISO_WAF_PJUD_para_otros_proyectos.md` | Firma técnica del WAF F5/Shape y cómo detectar el bloqueo. Aplica también a Regiones. |

---

## HISTORIAL DE VERSIONES

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-03-08 | Diseño inicial con Vision API |
| 1.1 | 2026-03-08 | Ajustes de selectores y timeouts |
| 2.0 | 2026-03-14 | Vision → textLayer + Text API; recorrido por secciones crecientes; fallback corte por nombre; HD una sola vez; rutas independientes en D:\Mercurio\ |
| 2.1 | 2026-03-16 | Fallback F→B; max_tokens 16384; filtros Estación Central y deuda >$300M; cronometro con reintentos; EdicionNoDisponible + exit(2) |
| 2.2 | 2026-03-21 | Sección D fines de semana; cachito 1616 en B; modales adicionales; navegación F tolerante; recorrido desde la última página |
| 2.3 | 2026-03-23 | Redirección a otra sección (Paso 6c) con `_REDIRECT_PATTERN` |
| (2.4)* | 2026-05-31 | *Aplicada al código sin actualizar este documento* — motor DeepSeek V4-Flash, filtro CBR (`_evaluar_cbr_por_anio`, campos `fojas` y `año_inscripcion_dominio`), paralelización 3 workers, resiliencia de red, normalización ordinal, métricas tokens/costo. Detalle en `CIERRE_CICLO_MERCURIO_2026-05.md`. |
| **3.0** | **2026-07-03** | **Eliminación completa de la capa PJUD/OJV** (WAF F5/Shape 24/7): borrados M2/M3/ojv_remates, sin filtro deuda >$300M, `--sin-ojv` eliminado, `--hasta` 1..4 = solo M1, M5 sin columnas OJV/deuda. Commits `53d757c` + `8edd5ee`. Este documento reemplaza al maestro v2.x. |

---

*— Fin del Prompt Maestro v3.0 —*
