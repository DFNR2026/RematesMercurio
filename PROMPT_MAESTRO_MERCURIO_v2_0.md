# Prompt Maestro: Extractor El Mercurio Digital (M1)
# Versión 2.0 — 2026-03-14

---

## CONTEXTO Y OBJETIVO

Este proyecto extrae avisos de remates judiciales de propiedades desde El Mercurio Digital (sección Clasificados, código 1616) usando Playwright + Claude Text API (Sonnet 4.6).

El módulo central es `modulo1_mercurio.py`, que scrapea el diario digital, extrae el texto de las páginas relevantes, y usa Claude para parsear los avisos en datos estructurados. Su output alimenta los módulos M2 (OJV), M3 (montos) y M5 (reporte Excel) del pipeline existente.

**Foco de negocio: EXCLUSIVAMENTE Región Metropolitana** (Corte de Santiago y Corte de San Miguel).

---

## ARQUITECTURA

```
D:\Mercurio\
├── main.py                    ← orquestador (--fecha YYYY-MM-DD activa Mercurio Digital)
├── modulo1_mercurio.py        ← scraper Mercurio Digital + Claude Text API
├── modulo2_ojv.py             ← consulta OJV via Playwright (REUTILIZADO)
├── modulo3_extractor.py       ← extrae montos de deuda (REUTILIZADO)
├── modulo5_reporte.py         ← reporte Excel (REUTILIZADO, hoja RESUMEN al final)
├── ojv_remates.py             ← motor OJV base (REUTILIZADO, NO reescribir)
├── config.py                  ← constantes centralizadas (rutas, credenciales, API keys)
├── causas_ojv.xlsx            ← BD interna: hoja REFERENCIA (233 tribunales) + hoja CAUSAS (historial)
├── limpiar_cache.py           ← limpieza de caché
├── logs/                      ← un .log por ejecución (mercurio_YYYY-MM-DD_HHMMSS.log)
├── Capturas/                  ← JPGs HD como respaldo visual (no se envían a API)
├── Procesadas/                ← JPGs movidos tras procesamiento exitoso
├── Descargas/                 ← mandamientos/bases descargados por M2
└── Informe final/             ← reportes Excel finales
```

**Todas las rutas están centralizadas en `config.py`.** Ningún módulo tiene rutas hardcodeadas. El proyecto es 100% independiente de `D:\Remates\` (proyecto base P&L).

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
- **Timeout:** 30s

### Paso 3: Navegar A → Clasificados (F)
- Click en `#uctHeader_ctl02_rptBodyPart_ctl07_aBody`
- **Timeout:** 15s

### Paso 4: Obtener mapa de páginas
- Extraer lista de page IDs de la sección F
- Iniciar desde la penúltima página

### Paso 5: Activar HD (una sola vez)
- Esperar canvas base (width > 0) antes de clickear
- Click botón HD + retry si no responde
- Verificar `canvas.width > 1800` (esperado: 1950px)
- HD queda activo para toda la sesión — NO reactivar por página
- Buffer 2s post-renderizado

### Paso 6: Recorrido de páginas (lógica actual)

La numeración de secciones es **CRECIENTE** (1611 → 1612 → 1616 → 1635...).

```
LOOP (desde penúltima hacia atrás, tope 15 páginas):
  1. Esperar 2s buffer
  2. Capturar canvas como JPG (quality 0.80) → guardar en Capturas/
  3. Leer textLayer COMPLETO
  4. DECISIÓN:
     - Sin "1616"        → borrar JPG, seguir
     - Con "1616" solo   → conservar JPG + texto, seguir
     - Con "1616" + sección menor (1611-1615) → conservar, PARAR
```

La condición de parada detecta el borde superior de la sección 1616.

### Paso 7: Enviar texto a Claude Text API

Para cada página conservada, enviar el **texto del textLayer** (no la imagen) a Sonnet 4.6:

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": PROMPT_EXTRACCION + "\n\n---\nTEXTO DE LA PÁGINA:\n" + texto
    }]
)
```

**¿Por qué texto y no imagen?** El textLayer del visor PDF contiene el texto original perfecto. Enviar texto en vez de imagen es 10-15x más barato, elimina errores de lectura (OCR), y duplica la cantidad de avisos extraídos (88 vs 49 en tests comparativos).

Los JPGs se capturan igualmente como **respaldo visual** y se mueven a `Procesadas/` tras éxito.

### Paso 8: Post-procesamiento y filtros

1. **Parsear ROL:** extraer número y año del formato `C-XXXXX-YYYY`
2. **Limpiar tribunal:** `_limpiar_tribunal()` — reconstruye guiones silábicos
3. **Mapear tribunal → corte:** `buscar_corte()` con RapidFuzz (umbral 80) + validación ordinal
4. **Fallback corte por nombre:** si fuzzy match falla, asignar corte por keywords en el nombre del tribunal ("Santiago" → C.A. de Santiago; "San Miguel"/"Buin"/"Puente Alto"/etc. → C.A. de San Miguel)
5. **Filtro RM:** solo C.A. de Santiago y C.A. de San Miguel
6. **Filtro Banco Estado:** descartar "Banco Estado" / "Banco del Estado"
7. **Filtro año:** descartar año < 2018 o año no parseable
8. **Deduplicación historial:** contra hoja CAUSAS de `causas_ojv.xlsx`
9. **Deduplicación ejecución:** entre páginas de la misma ejecución
10. **Asignar `region_rm = True`**

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

## MANEJO DE ERRORES

| Operación | Timeout | Acción si falla |
|-----------|---------|-----------------|
| Login El Mercurio | 30s | Abort total |
| Carga cuerpo A → F | 15s | Retry 1 vez, luego abort |
| Navegación entre páginas | 10s | Saltar página, continuar |
| Renderizado HD (canvas.width > 1800) | 20s | Retry click, capturar en resolución disponible |
| Buffer post-renderizado | 2s | Fijo |
| Claude Text API por página | 60s | Retry 1 vez, luego skip con warning |
| Respuesta no es JSON válido | — | Log response raw, skip página |

Login falla → abort total. Una página falla → se salta, se procesan las demás.

---

## GESTIÓN DE IMÁGENES

```
Capturas/                          ← JPGs HD recién capturados (respaldo visual)
Procesadas/                        ← JPGs movidos tras procesamiento exitoso
```

- Captura: `canvas.toDataURL('image/jpeg', 0.80)` → ~1.8MB por imagen (1950x2083px)
- Los JPGs NO se envían a la API — solo sirven como evidencia
- `limpiar_cache.py` limpia `Capturas/` (no `Procesadas/`)
- Formato nombre: `mercurio_YYYY-MM-DD_pN.jpg`

---

## COSTOS API ESTIMADOS

- **Claude Text API (Sonnet 4.6):** ~$0.01-0.02 por página de texto (~40K caracteres)
- **~5 páginas diarias:** ~$0.05-0.10 por ejecución
- **Costo mensual estimado:** ~$2-3 USD (ejecución diaria L-S)
- Historial CAUSAS evita reprocesar días anteriores

---

## LOGGING

Cada ejecución genera `logs/mercurio_YYYY-MM-DD_HHMMSS.log` con:
- Dual output: CMD + archivo
- Formato: `[HH:MM:SS] NIVEL — mensaje`
- textLayer (300 chars) y secciones detectadas por página
- Decisiones por página (conservar/descartar/parar)
- Resumen final: páginas revisadas, conservadas, descartadas, avisos, post-filtro, nuevos

---

## EJECUCIÓN

```bash
# Edición específica (completa con Vision + OJV + montos + reporte)
python main.py --fecha 2026-03-08

# Solo M1 standalone (extracción sin OJV/montos/reporte)
python modulo1_mercurio.py --fecha 2026-03-08

# Dry run (navegación sin API, sin costo)
python modulo1_mercurio.py --fecha 2026-03-08 --dry-run
```

---

## REGLAS INAMOVIBLES

- NO reescribir ojv_remates.py, modulo2_ojv.py, modulo3_extractor.py, modulo5_reporte.py
- NO modificar la hoja REFERENCIA de causas_ojv.xlsx
- NO implementar tasación automatizada (M4 no existe)
- Credenciales siempre en config.py, nunca hardcodeadas
- Todas las rutas centralizadas en config.py, ninguna hardcodeada en módulos
- Canvas HD obligatorio (umbral canvas.width > 1800)
- Montos siempre en pesos chilenos (CLP)
- RapidFuzz para fuzzy matching (umbral 80 en M1, 85 en OJV)
- region_rm = True siempre

---

## DOM REFERENCE (selectores clave)

- Canvas: `id=page1`, HD width > 1800px
- HD activar: `#inactive_pdf` / fallback toolbar button
- HD desactivar: `#active_pdf`
- Text layer: `div.textLayer`
- Login: `#openPram > span` → `#txtUsername` → `#txtPassword` → `#gopram`
- Modal promo: `#modal_mer_promoLS`
- Modal home: `#modal_mer_selectHome`
- Clasificados: `#uctHeader_ctl02_rptBodyPart_ctl07_aBody`
- Navegación páginas: `onclick gotoPage('F','ID',N)`
- URL pattern: `/YYYY/MM/DD/F/PAGE_ID#zoom=page-width`

---

## INSUMOS TÉCNICOS

1. **Scraper_Mercurio.json** — Grabación Playwright del flujo completo
2. **A.html** — DOM del cuerpo A
3. **F.html** — DOM del cuerpo F / Clasificados
4. **paghd.html** — DOM del visor HD (textLayer + canvas)
5. **pagina_mercurio_HD.png** — Ejemplo de captura HD (1950x2083px)

---

## HISTORIAL DE VERSIONES

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-03-08 | Diseño inicial con Vision API |
| 1.1 | 2026-03-08 | Ajustes de selectores y timeouts |
| 2.0 | 2026-03-14 | Reemplazo Vision → textLayer + Text API, nueva lógica de recorrido por secciones crecientes, fallback corte por nombre, HD una sola vez, rutas 100% independientes en D:\Mercurio\, hoja RESUMEN al final del Excel |
