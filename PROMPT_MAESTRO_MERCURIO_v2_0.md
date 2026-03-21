# Prompt Maestro: Extractor El Mercurio Digital (M1)
# Versión 2.2 — 2026-03-21

---

## CONTEXTO Y OBJETIVO

Este proyecto extrae avisos de remates judiciales de propiedades desde El Mercurio Digital (sección Clasificados, código 1616) usando Playwright + Claude Text API (Sonnet 4.6).

El módulo central es `modulo1_mercurio.py`, que scrapea el diario digital, extrae el texto de las páginas relevantes via textLayer del visor PDF, y usa Claude para parsear los avisos en datos estructurados. Su output alimenta los módulos M2 (OJV), M3 (montos) y M5 (reporte Excel) del pipeline existente.

**Foco de negocio: EXCLUSIVAMENTE Región Metropolitana** (Corte de Santiago y Corte de San Miguel).

---

## ARQUITECTURA

```
D:\Mercurio\
├── main.py                    ← orquestador (--fecha YYYY-MM-DD)
├── modulo1_mercurio.py        ← scraper Mercurio Digital + Claude Text API
├── modulo2_ojv.py             ← consulta OJV via Playwright (REUTILIZADO)
├── modulo3_extractor.py       ← extrae montos de deuda (REUTILIZADO)
├── modulo5_reporte.py         ← reporte Excel (REUTILIZADO, hoja RESUMEN al final)
├── ojv_remates.py             ← motor OJV base (REUTILIZADO, NO reescribir)
├── config.py                  ← constantes centralizadas (rutas, credenciales, API keys)
├── causas_ojv.xlsx            ← BD interna: hoja REFERENCIA (233 tribunales) + hoja CAUSAS (historial)
├── limpiar_cache.py           ← limpieza de caché
├── ejecutar_mercurio.bat      ← ejecución manual con doble click (fecha de hoy o específica)
├── cronometro_mercurio.bat    ← ejecución programada a las 5am con reintentos
├── logs/                      ← un .log por ejecución (mercurio_YYYY-MM-DD_HHMMSS.log)
├── Descargas/                 ← mandamientos/bases descargados por M2
└── Informe final/             ← reportes Excel finales (ordenados por tribunal)
```

**Todas las rutas están centralizadas en `config.py` usando `BASE_DIR` relativo.** Ningún módulo tiene rutas hardcodeadas. El proyecto es 100% independiente de `D:\Remates\` (proyecto base P&L) y portable a cualquier carpeta/PC.

---

## CONTRATO DE DATOS (OBLIGATORIO)

`extraer_mercurio(fecha)` retorna una lista de dicts con exactamente estas 9 claves:

```python
{
    "rol": "32342",              # str — número del ROL (sin "C-")
    "año": "2015",               # str — año del ROL (del formato C-XXXXX-YYYY)
    "corte": "C.A. de Santiago",  # str — corte de apelaciones
    "tribunal": "1º Juzgado Civil de Santiago",  # str — nombre oficial
    "demandante": "Banco Itaú",  # str — nombre parcial (M2 lo sobrescribe)
    "demandado": "Pérez",         # str — nombre parcial (M2 lo sobrescribe)
    "direccion": "Av. Matta 1234, depto 501",    # str o None
    "comuna": "Santiago",         # str o None
    "region_rm": True             # bool — SIEMPRE True
}
```

Si esta estructura cambia, M2/M3/M5 se rompen.

---

## FLUJO DE modulo1_mercurio.py

### Paso 1: Navegar al cuerpo A
```
URL = https://digital.elmercurio.com/YYYY/MM/DD/A
```
Fecha por defecto: `date.today()`. Manual: `--fecha YYYY-MM-DD`.

### Paso 2: Login
- Credenciales desde `config.py`: `MERCURIO_USER`, `MERCURIO_PASS`
- Secuencia post-login: `#gopram` → Escape ×2 → click fuera de `#modal_mer_promoLS` → click Clasificados → click fuera de `#modal_mer_selectHome`
- Si sesión activa: saltar login, pero cerrar modales igualmente
- Cierre de modales: primero genérico vía jQuery (`$('.modal.in, .modal.show').modal('hide')`), luego Escape ×2, luego modales específicos por ID (`#modal_mer_promoLS`, `#modal_mer_promoINV`, `#modal_mer_selectHome`)
- **Timeout:** 30s

### Paso 3: Navegar a sección de clasificados (F → D/B fallback)

1. Cerrar modales genéricos (jQuery `$('.modal.in, .modal.show').modal('hide')`) + Escape ×2 + modales conocidos por ID
2. Click en Clasificados (`#uctHeader_ctl02_rptBodyPart_ctl07_aBody`) → intenta cargar sección F
   - `_navegar_a_sección_f()` retorna `bool` (no crashea si falla por modal bloqueante u otro error)
3. Verificar `fechaEdicion` (variable JS) contra la fecha solicitada
4. Si F funciona y fecha coincide → continuar con F
5. Si F falla o fecha no coincide:
   - **Fin de semana (sábado/domingo):** navegar directo a `https://digital.elmercurio.com/YYYY/MM/DD/D` → verificar `fechaEdicion` → si coincide, usar D. Si D falla → intentar B como último recurso.
   - **Día de semana (L-V):** navegar directo a `https://digital.elmercurio.com/YYYY/MM/DD/B` → verificar `fechaEdicion` → si coincide, usar B.
6. Si ninguna sección tiene la fecha → `raise EdicionNoDisponible` → `sys.exit(2)` (cronometro reintenta en 30 min)

**¿Por qué D?** Los fines de semana, El Mercurio publica los clasificados en una sección D independiente (no visible en el menú del header), accesible solo por URL directa. La sección F queda stale con la fecha del último día hábil.

**¿Por qué B (L-V)?** De lunes a viernes, cuando F no se actualiza, los clasificados aparecen al final de la sección B (Economía y Negocios).

### Paso 4: Obtener mapa de páginas
- Extraer lista de page IDs de la sección activa (F, D o B)
- Iniciar desde la última página

### Paso 5: Activar HD (una sola vez)
- Esperar canvas base (width > 0) antes de clickear
- Click botón HD + retry si no responde
- Verificar `canvas.width > 1800` (esperado: 1950px)
- HD queda activo para toda la sesión — NO reactivar por página
- Buffer 2s post-renderizado
- HD es necesario porque mejora la calidad del textLayer

### Paso 6: Recorrido de páginas

La numeración de secciones es **CRECIENTE** (1611 → 1612 → 1616 → 1635...).

```
LOOP (desde última hacia atrás, tope 15 páginas):
  1. Esperar 2s buffer
  2. Leer textLayer COMPLETO
  3. DECISIÓN:
     - Sin "1616"                              → descartar, seguir
     - Con "1616" solo                         → conservar texto, seguir
     - Con "1616" + sección menor (1611-1615)  → conservar texto, PARAR
```

La condición de parada detecta el borde superior de la sección 1616. No se capturan imágenes — solo se lee el texto del textLayer.

### Paso 6b: Cachito de 1616 en sección B

Siempre que la sección primaria NO sea B (es decir, cuando se usa F o D), puede haber avisos 1616 sueltos al final de la sección B. Estos son avisos que deberían estar en F/D pero El Mercurio los publica en B.

```
Si seccion_activa != "B":
  1. Navegar directo a sección B
  2. Obtener mapa de páginas de B
  3. Revisar las 3 últimas páginas de B (de atrás hacia adelante)
  4. Si alguna contiene "1616" → conservar texto
  5. El dedup de Paso 8 elimina duplicados entre sección primaria y cachito B
```

HD persiste en la sesión, no necesita reactivarse para el cachito B.

### Paso 7: Enviar texto a Claude Text API

Para cada página conservada, enviar el **texto del textLayer** a Sonnet 4.6:

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16384,
    messages=[{
        "role": "user",
        "content": PROMPT_EXTRACCION + "\n\n---\nTEXTO DE LA PÁGINA:\n" + texto
    }]
)
```

**`max_tokens=16384`** porque la sección B puede tener textos de ~78K caracteres que generan respuestas JSON largas. Con 4096 el JSON se truncaba.

**¿Por qué texto y no imagen?** El textLayer del visor PDF contiene el texto original perfecto. Enviar texto en vez de imagen es 10-15x más barato, elimina errores de lectura, y duplica la cantidad de avisos extraídos (88 vs 49 en tests comparativos).

### Paso 8: Post-procesamiento y filtros

1. **Parsear ROL:** extraer número y año del formato `C-XXXXX-YYYY`
2. **Limpiar tribunal:** `_limpiar_tribunal()` — reconstruye guiones silábicos
3. **Mapear tribunal → corte:** `buscar_corte()` con RapidFuzz (umbral 80) + validación ordinal
4. **Fallback corte por nombre:** si fuzzy match falla, asignar corte por keywords ("Santiago" → C.A. de Santiago; "San Miguel"/"Buin"/"Puente Alto"/"Talagante"/"Colina"/"Melipilla"/"Peñaflor"/"San Bernardo" → C.A. de San Miguel)
5. **Filtro RM:** solo C.A. de Santiago y C.A. de San Miguel
6. **Filtro Banco Estado:** descartar "Banco Estado" / "Banco del Estado"
7. **Filtro Estación Central:** descartar causas con comuna "Estación Central"
8. **Filtro año:** descartar año < 2018 o año no parseable
9. **Deduplicación historial:** contra hoja CAUSAS de `causas_ojv.xlsx`
10. **Deduplicación ejecución:** entre páginas de la misma ejecución
11. **Asignar `region_rm = True`**

### Filtros post-M3 (en main.py)

- **Filtro monto máximo:** descartar causas con deuda > $300.000.000 CLP (solo cuando hay monto confirmado; sin monto pasan)

---

## PROMPT PARA CLAUDE TEXT API

```
Analiza este texto extraído de la sección "1616 — Remates de propiedades" del diario El Mercurio.

El texto viene del visor PDF y puede tener palabras cortadas por guiones de salto de línea
(ej: "Juzga-\ndo" = "Juzgado", "San-\ntiago" = "Santiago"). Reconstrúyelas.

Extrae TODOS los avisos de remates de propiedades. Para cada aviso, devuelve:

- "rol": número del ROL de la causa (solo el número, sin "C-"). Formato: "XXXXX"
- "año": año del ROL (los últimos 4 dígitos después del último guión en C-XXXXX-YYYY). Formato: "YYYY"
- "tribunal": nombre completo del tribunal (ej: "1° Juzgado Civil de Santiago")
- "demandante": nombre del demandante/ejecutante (banco o persona)
- "demandado": nombre del demandado/ejecutado
- "direccion": dirección completa del inmueble rematado
- "comuna": comuna donde se ubica el inmueble
- "fecha_remate": fecha del remate si aparece (formato DD/MM/YYYY)

REGLAS:
1. NO inventar datos. Si un campo no es identificable en el texto, devolver null.
2. El ROL siempre aparece como "Rol C-XXXXX-YYYY" o "Rol: C-XXXXX-YYYY". XXXXX es el número, YYYY es el año.
3. El tribunal es el JUZGADO que ordena el remate, NO la dirección del tribunal.
4. SOLO extraer avisos de la sección 1616 (Remates de propiedades). Ignorar secciones 1611, 1612, 1615 u otras.
5. Si un aviso está cortado, extraer lo visible con campos faltantes como null.

Responde ÚNICAMENTE con un JSON array válido. Sin texto explicativo, sin markdown, sin comentarios. Solo JSON puro.
```

---

## REPORTE EXCEL (modulo5_reporte.py)

- Primera hoja: detalle de causas (REGIONES), ordenado por corte (Santiago primero, San Miguel segundo) y después por tribunal ascendente
- Segunda hoja: RESUMEN (no es la primera pestaña al abrir)

---

## MANEJO DE ERRORES

| Operación | Timeout | Acción si falla |
|-----------|---------|-----------------|
| Login El Mercurio | 30s | Abort total |
| Click botón Clasificados (→F) | 15s | Retorna False, continúa a fallback D/B |
| Verificación fecha F | — | Fallback a D (finde) o B (L-V) |
| Verificación fecha D | — | Fallback a B, luego EdicionNoDisponible |
| Verificación fecha B | — | raise EdicionNoDisponible → sys.exit(2) |
| Cachito B (Paso 6b) | — | Warning, continúa sin cachito |
| Navegación entre páginas | 10s | Saltar página, continuar |
| Renderizado HD (canvas.width > 1800) | 20s | Retry click |
| Buffer post-renderizado | 2s | Fijo |
| Claude Text API por página | 60s | Retry 1 vez, luego skip con warning |
| Respuesta no es JSON válido | — | Log response raw, skip página |

Login falla → abort total. Una página falla → se salta, se procesan las demás. Edición no disponible → sys.exit(2) para que cronometro reintente.

---

## COSTOS API ESTIMADOS

- **Claude Text API (Sonnet 4.6):** ~$0.01-0.02 por página de texto (~40-78K caracteres)
- **~2-5 páginas diarias:** ~$0.05-0.10 por ejecución (fines de semana pueden ser 5-7 con cachito B)
- **Costo mensual estimado:** ~$2-3 USD (ejecución diaria L-S)
- Historial CAUSAS evita reprocesar días anteriores

---

## EJECUCIÓN

```bash
# Doble click (fecha de hoy)
ejecutar_mercurio.bat

# Fecha específica desde CMD
ejecutar_mercurio.bat 2026-03-08

# Ejecución programada a las 5am con reintentos
cronometro_mercurio.bat

# Solo M1 standalone (sin OJV/montos/reporte)
python modulo1_mercurio.py --fecha 2026-03-08

# Dry run (navegación sin API, sin costo, ~30 segundos)
python modulo1_mercurio.py --fecha 2026-03-08 --dry-run
```

### cronometro_mercurio.bat
- Si lo abres de día, espera hasta medianoche y luego hasta las 5am
- A las 5:00 ejecuta `main.py --fecha` con la fecha del día
- Si la edición no está disponible (ni F, D ni B), reintenta cada 30 min hasta 6 veces
- Detección via exit code 2 (`EdicionNoDisponible`)

---

## LOGGING

Cada ejecución genera `logs/mercurio_YYYY-MM-DD_HHMMSS.log` con:
- Dual output: CMD + archivo
- Formato: `[HH:MM:SS] NIVEL — mensaje`
- textLayer (300 chars) y secciones detectadas por página
- Decisiones por página (conservar/descartar/parar)
- Sección utilizada (F, D fin de semana, o B fallback L-V)
- Cachito B: páginas revisadas y conservadas en Paso 6b
- Resumen final: páginas revisadas, conservadas, descartadas, avisos, post-filtro, nuevos

---

## REGLAS INAMOVIBLES

- NO reescribir ojv_remates.py, modulo2_ojv.py, modulo3_extractor.py, modulo5_reporte.py
- NO modificar la hoja REFERENCIA de causas_ojv.xlsx
- NO implementar tasación automatizada (M4 no existe)
- Credenciales siempre en config.py, nunca hardcodeadas
- Todas las rutas centralizadas en config.py con BASE_DIR relativo
- Canvas HD obligatorio (umbral canvas.width > 1800)
- Montos siempre en pesos chilenos (CLP)
- RapidFuzz para fuzzy matching (umbral 80 en M1, 85 en OJV)
- region_rm = True siempre
- Descartar Banco Estado, Estación Central, deuda > $300M, pre-2018

---

## DOM REFERENCE (selectores clave)

- Canvas: `id=page1`, HD width > 1800px
- HD activar: `#inactive_pdf` / fallback toolbar button
- HD desactivar: `#active_pdf`
- Text layer: `div.textLayer`
- Fecha edición: variable JS `fechaEdicion` (formato "YYYY/MM/DD")
- Login: `#openPram > span` → `#txtUsername` → `#txtPassword` → `#gopram`
- Modal promo LS: `#modal_mer_promoLS`
- Modal promo INV: `#modal_mer_promoINV` (suscripción Mercurio Inversiones)
- Modal home: `#modal_mer_selectHome`
- Cierre genérico modales: `$('.modal.in, .modal.show').modal('hide')` (jQuery Bootstrap)
- Clasificados: `#uctHeader_ctl02_rptBodyPart_ctl07_aBody`
- Economía y Negocios: `#uctHeader_ctl02_rptBodyPart_ctl01_aBody`
- Navegación páginas: `onclick gotoPage('F','ID',N)` o `gotoPage('B','ID',N)` o `gotoPage('D','ID',N)`
- URL pattern: `/YYYY/MM/DD/{F|B|D}/PAGE_ID#zoom=page-width`
- Sección D: no aparece en menú header, accesible solo por URL directa (fines de semana)

---

## HISTORIAL DE VERSIONES

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-03-08 | Diseño inicial con Vision API |
| 1.1 | 2026-03-08 | Ajustes de selectores y timeouts |
| 2.0 | 2026-03-14 | Reemplazo Vision → textLayer + Text API, nueva lógica de recorrido por secciones crecientes, fallback corte por nombre, HD una sola vez, rutas 100% independientes en D:\Mercurio\, hoja RESUMEN al final del Excel |
| 2.1 | 2026-03-16 | Fallback sección F → B cuando F no actualizada, max_tokens 16384, captura JPG eliminada (textLayer es suficiente), filtros Estación Central y deuda > $300M, ordenamiento Excel por tribunal, cronometro_mercurio.bat con reintentos, EdicionNoDisponible + sys.exit(2), portabilidad con BASE_DIR relativo |
| 2.2 | 2026-03-21 | Sección D para fines de semana (sábado→D, domingo→D/F), cachito 1616 en últimas 3 páginas de B, modal `#modal_mer_promoINV` + cierre genérico jQuery de modales Bootstrap, `_navegar_a_sección_f()` retorna bool (no crashea), navegación F tolerante a fallos con fallback encadenado F→D→B, recorrido inicia en última página (no penúltima) para no perder avisos |
