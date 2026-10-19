# El backend del Proyecto RM — Capa PJUD / OJV

**Documento técnico de referencia y evaluación de replicación**
**Proyecto:** `D:\Mercurio\` (RM) — repo `DFNR2026/RematesMercurio`
**Fecha de levantamiento:** 2026-06-13
**Método:** lectura verbatim del código en disco. No es paráfrasis de documentación previa; cada función, selector y comportamiento aquí descrito se leyó directamente de los archivos fuente.

**Archivos cubiertos:**
- `ojv_remates.py` — motor base OJV (cabecera interna "Versión 10.2")
- `modulo2_ojv.py` — Módulo 2 (M2), adaptador del motor para el pipeline
- `main.py` — orquestador (solo para confirmar cómo y cuándo se invoca M2)
- `config.py` — constantes que consume la capa OJV

> **Aclaración de nombre.** En este proyecto le llamamos "backend" o "módulo" a la capa que entra al Poder Judicial. Técnicamente es la **capa de consulta a la OJV (Oficina Judicial Virtual del PJUD)** más la **descarga de documentos**. No hay login al PJUD: la consulta es **anónima** (no existe credencial PJUD en el sistema). La única autenticación del proyecto es contra El Mercurio, y vive en otra capa (M1).

---

## 1. Qué es esta capa y qué NO es

**Qué hace:** recibe una lista de causas civiles (ROL, año, corte, tribunal) y, para cada una, entra a la OJV del PJUD, busca la causa exacta, abre su detalle, lee los litigantes reales (demandante y demandado), detecta el tipo de procedimiento y descarga el documento que corresponde (mandamiento o bases de remate) como PDF a disco.

**Qué NO hace (límites de la capa):**
- No hace login al PJUD (consulta anónima, sujeta a los límites públicos de la OJV).
- No extrae montos de deuda — eso es M3 (`modulo3_extractor.py`), que lee los PDF que esta capa descarga.
- No scrapea El Mercurio — eso es M1 (`modulo1_mercurio.py`).
- No hace tasación (M4 no existe).

**Frontera de entrada/salida:** esta capa es el puente entre M1 (que produce causas con datos parciales del diario) y M3 (que necesita los PDF descargados).

---

## 2. Cómo está dividido el código (dualidad importante)

La capa vive en **dos archivos** con una relación clara:

| Archivo | Rol | Punto de entrada | Fuente de causas |
|---|---|---|---|
| `ojv_remates.py` | Motor base. Contiene TODA la lógica de navegación, búsqueda, lectura de tabla y descarga de PDF. | `main()` propio (script standalone, `python ojv_remates.py`) | Lee `causas_ojv.xlsx` (hoja CAUSAS) directamente con pandas |
| `modulo2_ojv.py` | Adaptador para el pipeline. Importa los helpers del motor y agrega lógica específica (filtrado de procedimientos, enriquecimiento del dict, manejo de fallos). | `procesar_causas_ojv(causas)` (función pública, la llama `main.py`) | Recibe la lista de causas en memoria desde M1 |

Es decir: **el motor (`ojv_remates.py`) puede correr solo** (modo de prueba, leyendo Excel) **o como biblioteca** (cuando M2 importa sus funciones). En el pipeline real, el camino que se ejecuta es `main.py → procesar_causas_ojv() → _procesar_una_causa() → helpers de ojv_remates`.

**Qué importa M2 del motor:**
```
cerrar_popups, cerrar_modal_aviso, seleccionar_por_texto, navegar_a_consulta,
limpiar_formulario, buscar_causa, abrir_detalle, seleccionar_cuaderno,
filas_del_modal, descargar_pdf_de_fila, buscar_mandamiento, buscar_bases_remate
```

**Qué reimplementa M2 (no usa la versión del motor):**
- Extracción de litigantes: M2 define `_extraer_litigantes_ojv()` (agrega retorno garantizado a la pestaña Historia). La versión del motor, `_extraer_litigantes()`, solo se usa en el modo standalone del motor.
- Selección de cuaderno: M2 define `_seleccionar_cuaderno_dinamico()` (busca por texto + espera recarga de tabla). El `seleccionar_cuaderno()` importado queda como remanente no usado en el camino de M2.

Esta duplicación es deuda menor, pero conviene tenerla presente al replicar: **la lógica "buena" para el pipeline está en M2; la del motor es la base histórica.**

---

## 3. Flujo end-to-end de una causa en la OJV

Secuencia real, en orden, con la función responsable de cada paso (camino del pipeline, vía `procesar_causas_ojv`):

### 3.1 Apertura del navegador y del formulario (una sola vez por corrida)
`navegar_a_consulta(page)`:
1. `page.goto("https://oficinajudicialvirtual.pjud.cl/indexN.php", wait_until="domcontentloaded", timeout=30000)`. Se usa `indexN.php` (no `index.php`) para evitar el modal de avisos del home.
2. Si el `goto` expira mientras la OJV redirige `indexN → home/index.php`, espera la navegación pendiente (`wait_for_load_state`).
3. Presiona `Escape` para cerrar el pop-up/aviso semanal del PJUD (tolerante: si no hay pop-up, no falla).
4. Si terminó en `home/index.php`: cierra modal de aviso (`cerrar_modal_aviso`) y hace click en `text=Consulta causas`.
5. Espera el selector `#competencia` (formulario listo).

El navegador se lanza con `chromium.launch(headless=False, slow_mo=100)` y `accept_downloads=True`. **No es headless** — corre con ventana visible y 100 ms de ralentización por acción. `page.set_default_timeout(15000)`.

### 3.2 Limpieza entre causas
`limpiar_formulario(page)`: cierra modal si quedó abierto, intenta botón "Limpiar"; si no existe, resetea `#competencia` (el AJAX limpia los dependientes). Se llama desde la causa 2 en adelante.

### 3.3 Búsqueda exacta de la causa
`buscar_causa(page, rol, año, corte, tribunal)`:
1. **Competencia = Civil:** `select_option("#competencia", value="3")`.
2. **Corte:** `seleccionar_por_texto(page, "conCorte", corte, timeout_seg=10)` — fuzzy match.
3. **Tribunal:** `seleccionar_por_texto(page, "conTribunal", tribunal, timeout_seg=15)` — fuzzy match.
4. **Libro = C:** `select_option("#conTipoCausa", value="C")`.
5. **ROL + año:** rellena `#conRolCausa` y `#conEraCausa`. **Verifica que el AJAX no los haya borrado** y reintenta el `fill` si quedaron vacíos (problema real de la OJV: el cambio de tribunal dispara AJAX que limpia los campos).
6. **Buscar:** click en `#btnConConsulta`, espera `domcontentloaded` (20 s), cierra modales/pop-ups.
7. **Detección de "sin resultados":** si el body contiene `"No se han encontrado resultados"` → retorna False (aunque la página tenga filas de layout).
8. **Conteo de filas reales:** `table#veDetalle tbody tr`; si no, fallback genérico filtrando filas vacías, `"No se han encontrado"` y `"VALOR RECUSACIÓN"`.

### 3.4 Apertura del detalle (con salvaguarda anti-causa-equivocada)
`abrir_detalle(page, rol, año)`:
- Busca la fila que contenga **el ROL exacto + el año** (acepta año en 4 dígitos `"2023"` o 2 dígitos `"23"`).
- **NO usa la primera fila como fallback cuando se pasó rol/año** — si no encuentra la fila exacta, retorna False e imprime las primeras 3 filas para diagnóstico. Esto evita abrir la causa equivocada (bug histórico de "primera fila").
- Localiza la lupa dentro de la fila: `a.toggle-modal` / `td:first-child a` / `a[href='#modalDetalleCivil']` / `a`. Si encuentra el `<i>`, sube al `<a>` padre.
- `scroll_into_view_if_needed()` antes del click (evita "element is not visible").
- Espera `#modalDetalleCivil, .modal.in, .modal.show` (7 s).

### 3.5 Extracción de litigantes reales
`_extraer_litigantes_ojv(page, etiqueta)` (versión M2):
- Click en pestaña Litigantes: `a[href="#litigantesCiv"]`.
- Lee SOLO `#litigantesCiv tbody tr`. Columnas reales OJV: `celdas[0]`=Participante (`"DTE."`, `"DDO."`), `celdas[1]`=RUT, `celdas[2]`=tipo persona, `celdas[3]`=Nombre.
- Toma el **primer** DTE y el **primer** DDO. Limpia el nombre quitando paréntesis tipo `"(Poder Amplio)"` y espacios.
- **Siempre vuelve a la pestaña Historia** (`_volver_a_historia`, click `a[href="#702"]` o por texto "Historia"), porque la pestaña Historia es la que tiene el cuaderno y la descarga.
- Los nombres obtenidos **sobrescriben** `causa['demandante']` y `causa['demandado']` (los parciales del diario quedan reemplazados por los oficiales de la OJV).

### 3.6 Detección y filtrado del tipo de procedimiento
Lee el texto del modal (`#modalDetalleCivil`) en minúsculas y clasifica:

| Marcador en el modal | `tipo_procedimiento` | Cuaderno objetivo |
|---|---|---|
| `"ley de bancos"` | `ley_bancos` | `Principal` |
| `"ejecutivo"` + `"obligaci"` | `ejecutivo` | `Apremio` |
| `"desposeimiento"` | `desposeimiento` | `Apremio` |

**Procedimientos que se descartan** (lista `PROCEDIMIENTOS_DESCARTADOS`, con `motivo_fallo` poblado): `liquidación simplificada`, `liquidación concursal`, `ordinario mayor/menor/mínima cuantía`, `partición`, `arbitral`. Además se descarta explícitamente `Ejecutivo Mínima Cuantía`. Si el modal se pudo leer pero no calza con ninguno de los tres tipos válidos → se descarta como "procedimiento no aplicable".

### 3.7 Selección de cuaderno
`_seleccionar_cuaderno_dinamico(page, texto_cuaderno)`:
- Espera `#selCuaderno` (15 s), loguea los cuadernos disponibles (diagnóstico), busca la opción cuyo texto **contenga** `texto_cuaderno` (case-insensitive), la selecciona y **espera la recarga** de la tabla de historia (`#loadHistCuadernoCivil` / `#historiaClv` / `#modalDetalleCivil .table-responsive`).
- Nota: para desposeimiento el objetivo es `"Apremio"`, y "Apremio de desposeimiento" lo contiene — por eso el match por substring funciona.

### 3.8 Descarga del documento
Según el tipo:

**Mandamiento** — `buscar_mandamiento(page, context, etiqueta)`:
- Obtiene filas del modal (`filas_del_modal`).
- **La tabla viene ordenada por folio DESCENDENTE** (ej. 68, 67, … 1). El mandamiento está en folios bajos (1–5), así que **recorre la lista invertida** (`reversed`).
- Estructura de columnas: `txts[0]`=Folio, `txts[3]`=Etapa, `txts[5]`=Desc. Trámite.
- Match exacto: `Etapa == "mandamiento"` **y** `Desc == "mandamiento"`.
- Fallback: `Etapa == "mandamiento"` y la fila no contiene `"requerimiento"`.
- Guarda `Descargas\{etiqueta}_MANDAMIENTO.pdf`.

**Bases de remate** — `buscar_bases_remate(page, context, etiqueta)`:
- Filtra filas con `"propone bases"` o `"bases de remate"`, **excluyendo** `"aprueba"/"aprobada"/"aprobado"` (esas son resoluciones del juez, no la propuesta).
- Si hay varias versiones, usa la **última** (folio más alto = más reciente).
- Guarda `Descargas\{etiqueta}_BASES_REMATE.pdf`.

**Descarga física** — `descargar_pdf_de_fila(page, context, fila, nombre_archivo)`:
- HTML real del PJUD: un `<form action="/civil/documentos/doculs.php" method="get" target="p3">` con `<input hidden name="dtaDoc" value="JWT">` y un `<a>` que hace `closest(form).submit()`. El botón visible es `i.fa-file-pdf-o`.
- Busca el enlace (`a[title='Descargar Documento']` / `form a` / `a[onclick*='submit']` / `i.fa-file-pdf-o`).
- Como el form usa `target="p3"`, **abre una pestaña nueva**: `context.expect_page(timeout=15000)`. Toma la URL del popup y descarga con `popup.request.get(url_pdf, timeout=20000)`; guarda si la respuesta es OK y pesa > 500 bytes.
- Fallback: `page.expect_download(timeout=20000)` + `save_as`.

### 3.9 Cierre y siguiente causa
`_cerrar_modal(page)`: intenta `"Cerrar"` / `.modal .close` / `button.close`, luego `Escape`. `time.sleep(2)` entre causas.

---

## 4. Selectores DOM del PJUD (referencia de replicación)

Este es el activo más valioso para replicar. Son los selectores reales que la OJV expone hoy:

| Elemento | Selector |
|---|---|
| URL de entrada | `https://oficinajudicialvirtual.pjud.cl/indexN.php` |
| Modal de aviso semanal | `#close-modal` (se cierra con `Escape`) |
| Link a formulario | `text=Consulta causas` |
| Competencia (Civil=3) | `#competencia` |
| Corte | `#conCorte` |
| Tribunal | `#conTribunal` |
| Libro/Tipo (C) | `#conTipoCausa` |
| ROL | `#conRolCausa` |
| Año | `#conEraCausa` |
| Botón Buscar | `#btnConConsulta` |
| Tabla de resultados | `table#veDetalle tbody tr` |
| Lupa de detalle | `a.toggle-modal` / `a[href='#modalDetalleCivil']` |
| Modal de detalle | `#modalDetalleCivil` (o `.modal.in` / `.modal.show`) |
| Pestaña Litigantes | `a[href="#litigantesCiv"]` → tabla `#litigantesCiv tbody tr` |
| Pestaña Historia | `a[href="#702"]` |
| Selector de cuaderno | `#selCuaderno` |
| Tabla de historia (cuaderno) | `#loadHistCuadernoCivil` / `#historiaClv` |
| Endpoint de descarga | `form[action="/civil/documentos/doculs.php"]` (GET, `target="p3"`, input `dtaDoc`=JWT) |
| Botón PDF en fila | `a[title='Descargar Documento']` / `i.fa-file-pdf-o` |

---

## 5. Fuzzy matching de corte y tribunal

`seleccionar_por_texto(page, selector_id, texto_buscar, timeout_seg)`:
- Normaliza ambos lados con `_normalizar_texto_ojv()`: pasa ordinales a dígitos (`primer/primera/1er → 1`, etc.), quita tildes, elimina `°º.,-`, elimina la palabra `"de"`, `jdo→juzgado`, `garantia→gar`, y colapsa `"letras civil" → "letras"` (el diario a veces agrega "Civil" pero el dropdown OJV no).
- Compara con `rapidfuzz.fuzz.token_set_ratio`.
- **Umbral real en el código: `>= 80`.** Hace polling hasta `timeout_seg * 2` iteraciones (0.5 s c/u) esperando que carguen las opciones del AJAX.

> **Discrepancia documentada para replicación:** el umbral efectivo es **80**, pero el mensaje de error de M2 dice `"score < 85%"` y la documentación maestra también menciona 85. El número que gobierna la decisión es **80** (la constante en `seleccionar_por_texto`). Al replicar, no confíes en el texto del mensaje: el árbitro es la comparación `mejor_score >= 80`.

---

## 6. Contrato de datos (entrada y salida)

**Entrada** (lo que produce M1 / lo que `procesar_causas_ojv` espera): dicts con al menos `rol`, `año`, `corte`, `tribunal` (y opcionalmente `demandante`, `demandado`, `direccion`, `comuna`, `region_rm`).

**Salida** (lo que M2 agrega a cada dict):

| Campo | Valores |
|---|---|
| `tipo_procedimiento` | `"ejecutivo"` / `"ley_bancos"` / `"desposeimiento"` / `""` |
| `tipo_documento` | `"mandamiento"` / `"bases_remate"` / `""` |
| `descargado` | `True` / `False` |
| `ruta_pdf` | ruta absoluta al PDF descargado o `""` |
| `motivo_fallo` | texto del motivo cuando no se pudo procesar (ej. "OJV: causa no encontrada", "procedimiento descartado: …", "OJV: descarga fallida") |

Además **sobrescribe** `demandante` y `demandado` con los nombres oficiales de la pestaña Litigantes (cuando se pudieron leer).

---

## 7. Manejo de errores, anti-bot y resiliencia

- **Modales del PJUD:** `cerrar_modal_aviso` (`#close-modal` + `Escape`) y `cerrar_popups` (varios botones de cierre). El pop-up semanal se intenta cerrar siempre con `Escape` de forma tolerante.
- **Campos borrados por AJAX:** `buscar_causa` verifica y reintenta el `fill` de ROL/año.
- **Causa equivocada:** `abrir_detalle` exige match exacto de ROL+año; sin fallback a primera fila.
- **Blacklist manual:** `CAUSAS_IGNORADAS` en `config.py` (causas que existen pero no se pueden procesar, ej. cuadernos restringidos con timeout). En el ejemplo actual: `C-1838-2024`.
- **Aislamiento de fallos:** un error en una causa puebla `motivo_fallo` y continúa con la siguiente; nunca aborta el lote (salvo que falle la apertura inicial del formulario).
- **WAF / IP única:** el sistema NO paraleliza OJV (workers concurrentes están aplazados). Riesgo conocido: una sola IP contra el WAF del PJUD; correr RM y Regiones en paralelo apunta a la misma IP. La consulta es anónima (sin credencial PJUD).
- **Encoding:** M2 fuerza UTF-8 en stdout/stderr para que los `print()` con `✓ ✗ → ⚠` del motor no rompan en terminales Windows cp1252.

---

## 8. Dependencias y acoplamientos

**Necesita para funcionar:**
- `playwright.sync_api` + Chromium (`playwright install chromium`).
- `rapidfuzz` (fuzzy matching).
- `pandas` (solo el motor, para leer el Excel en modo standalone).
- `config.py`: `DESCARGAS_DIR`, `CAUSAS_IGNORADAS`, `CAUSAS_XLSX`, `OJV_URL`.
- La forma del dict de causas (contrato con M1).

**Aguas abajo:** M3 (`modulo3_extractor.py`) consume `ruta_pdf` y `tipo_documento` para extraer montos de los PDF.

> **Credenciales:** `config.py` contiene claves hardcodeadas (no se reproducen aquí). Para cualquier reutilización: mover secretos fuera del código y confirmar `config.py` en `.gitignore`. La capa OJV en sí **no usa credenciales** (consulta anónima); las claves de `config.py` son de El Mercurio y de las APIs de extracción, ajenas a esta capa.

---

## 9. Cómo se invoca desde el orquestador (confirmado en `main.py`)

En el pipeline real, M2 se ejecuta así:
```
causas = procesar_causas_ojv(causas)          # M2: OJV + descarga (ACTIVO)
...
causas = extraer_montos(causas)               # M3: lee los PDF descargados (ACTIVO)
# Filtro post-M3: descarta deuda > $300.000.000 CLP (ACTIVO)
```
Banderas relevantes: `--sin-ojv` omite M2 y reutiliza los PDF ya presentes en `Descargas\` (los indexa por nombre `{ROL}_{MANDAMIENTO|BASES_REMATE}.pdf`); `--demo` salta M1 y M2 con causas sintéticas; `--hasta N` corta el pipeline tras el módulo N.

> **Nota de estado (relevante para el lector que viene de la documentación de cierre):** en el código en disco al 2026-06-13, la **descarga de mandamientos/bases está ACTIVA**, M3 está activo y el filtro de $300M está activo. Esto contradice lo que afirma `CIERRE_CICLO_MERCURIO_2026-05.md` ("deuda extirpada / descarga cortada en M2"). El árbitro es el código. Esta contradicción se detalla y se propone resolución por separado (ver el mensaje que acompaña este documento).

---

## 10. Evaluación de replicación / reutilización

El objetivo de este documento es decidir si esta capa sirve para otro proyecto. Veredicto por capas:

### 10.1 Altamente reutilizable (genérico, NO atado a remates)
Todo el "motor de consulta OJV" es reaprovechable casi tal cual por **cualquier proyecto que necesite consultar la OJV del PJUD por ROL y bajar documentos**:
- `navegar_a_consulta` — entrada robusta al formulario, manejo del modal semanal y del redirect `indexN → home`.
- `seleccionar_por_texto` + `_normalizar_texto_ojv` — selección fuzzy de corte/tribunal en dropdowns que cargan por AJAX. Resuelve un problema real y molesto.
- `buscar_causa` — el patrón competencia → corte → tribunal → libro → ROL/año, con reintento anti-AJAX.
- `abrir_detalle` — apertura segura con match exacto (la salvaguarda anti-primera-fila es oro: evita procesar la causa equivocada).
- `_extraer_litigantes_ojv` — lectura de DTE/DDO desde la pestaña Litigantes.
- `_seleccionar_cuaderno_dinamico` — selección de cuaderno por texto con espera de recarga.
- `descargar_pdf_de_fila` — el patrón de descarga vía form `target="p3"` + popup + `request.get` (con fallback `expect_download`) es exactamente lo que necesita cualquiera que baje documentos del PJUD.
- El stack anti-modal (`cerrar_modal_aviso`, `cerrar_popups`).

**Recomendación:** extraer estas primitivas a un módulo reutilizable (ej. `ojv_core.py`) desacoplado de la lógica de remates. Eso te deja una librería "consulta OJV + descarga genérica" lista para el proyecto que tengas en mente.

### 10.2 Atado al negocio de remates (requiere adaptación)
- El **ruteo por procedimiento** (ejecutivo → mandamiento / cuaderno Apremio; ley de bancos → bases / cuaderno Principal; desposeimiento → Apremio).
- La lista `PROCEDIMIENTOS_DESCARTADOS` y el descarte de "mínima cuantía".
- Las **heurísticas de folio** para identificar "Mandamiento" (Etapa+Desc) y "Propone bases" (excluyendo "aprueba"). Un proyecto nuevo cambiaría estos targets por los documentos que le interesen.

### 10.3 Atado a este pipeline (no transferible directo)
- El contrato exacto del dict de causas.
- Las constantes de `config.py` y la lectura de `causas_ojv.xlsx` del modo standalone.
- La sobrescritura de `demandante`/`demandado`.

### 10.4 Riesgos a considerar antes de replicar
- **El DOM de la OJV es frágil:** todos los selectores están hardcodeados. Si el PJUD cambia el front, se rompe. Antes de reutilizar, **validar cada selector contra la OJV vigente**.
- **WAF / concurrencia:** sin paralelización segura. Una sola IP; cuidado con correr varios procesos contra el PJUD a la vez.
- **Consulta anónima:** sin login, sujeta a los límites públicos de la OJV (rate, captchas eventuales, modales nuevos).
- **`headless=False`:** corre con ventana visible. Para servidor/VPS habría que validar headless o un display virtual.
- **Umbrales tuneados:** el 80 de fuzzy está calibrado para nombres de tribunales chilenos; revisar si el dominio cambia.

### 10.5 Resumen ejecutivo de replicación
La capa **sí sirve para replicar**, con una división limpia: el **70 % es motor OJV genérico** (consulta + descarga) reutilizable casi sin tocar, y el **30 % es lógica de remates** (qué procedimiento, qué documento, qué folio) que se reemplaza por la del nuevo dominio. La ruta recomendada es aislar el motor en su propio módulo y montar encima la lógica específica del proyecto nuevo.

---

## 11. Apéndice — Inventario de funciones

### `ojv_remates.py` (motor base, v10.2)
| Función | Rol |
|---|---|
| `leer_causas()` | Lee causas desde `causas_ojv.xlsx` (modo standalone) |
| `cerrar_popups(page)` | Cierra botones de cierre genéricos |
| `cerrar_modal_aviso(page)` | Cierra `#close-modal` con Escape |
| `_quitar_tildes(s)` | Quita diacríticos |
| `_normalizar_texto_ojv(texto)` | Normalización agresiva para fuzzy de tribunales |
| `seleccionar_por_texto(page, id, texto, timeout)` | Selección fuzzy en `<select>` (umbral 80) |
| `navegar_a_consulta(page)` | Entra a la OJV y abre el formulario |
| `limpiar_formulario(page)` | Resetea el formulario entre causas |
| `buscar_causa(page, rol, año, corte, tribunal)` | Búsqueda exacta de la causa |
| `abrir_detalle(page, rol, año)` | Abre el modal de la causa correcta |
| `seleccionar_cuaderno(page, texto)` | Selección de cuaderno (versión motor) |
| `filas_del_modal(page)` | Devuelve filas de la tabla del modal |
| `descargar_pdf_de_fila(page, context, fila, nombre)` | Descarga física del PDF |
| `buscar_mandamiento(page, context, etiqueta)` | Localiza y descarga el mandamiento |
| `buscar_bases_remate(page, context, etiqueta)` | Localiza y descarga las bases de remate |
| `_extraer_litigantes(page, rol)` | Lee DTE/DDO (versión motor) |
| `procesar_causa(page, context, causa)` | Flujo completo de una causa (standalone) |
| `main()` | Entry point standalone |

### `modulo2_ojv.py` (M2, adaptador del pipeline)
| Función | Rol |
|---|---|
| `_extraer_litigantes_ojv(page, etiqueta)` | Lee DTE/DDO + retorno garantizado a Historia |
| `_volver_a_historia(page)` | Vuelve a la pestaña Historia |
| `_seleccionar_cuaderno_dinamico(page, texto)` | Selección de cuaderno por texto + espera recarga |
| `_procesar_una_causa(page, context, causa)` | Flujo completo de una causa (enriquece el dict) |
| `_cerrar_modal(page)` | Cierra el modal de detalle |
| `procesar_causas_ojv(causas)` | **Interfaz pública.** Recibe causas de M1, las enriquece, devuelve la lista + resumen |

---

*Fin del documento — `El_backend_proyecto_RM_PJUD.md`*
