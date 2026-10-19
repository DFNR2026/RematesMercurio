# Cierre de ciclo — Modernización Extractor El Mercurio Digital (RM)

**Fecha de cierre:** 2026-05-31
**Proyecto:** `D:\Mercurio\` — repo `DFNR2026/RematesMercurio`
**Proyecto hermano:** `D:\Remates\` (Regiones) — repo `DFNR2026/RemateRegiones`
**Alcance:** este documento resume los cambios aplicados en el ciclo de mayo 2026, para (a) entender cómo opera el sistema hoy y (b) servir de referencia a proyectos hermanos.

> Nota de método: los nombres de función y comportamientos descritos aquí se
> verificaron durante el ciclo mediante minería de Cline y corridas reales. Donde
> aparece "(verificar con Cline)" es porque el número de línea exacto puede haber
> cambiado tras las ediciones; el símbolo es real pero su ubicación conviene
> reconfirmarla antes de citarla como autoridad.

---

## 1. Qué cambió en este ciclo (resumen ejecutivo)

| # | Cambio | Estado |
|---|--------|--------|
| 1 | Motor de extracción: **Sonnet 4.6 → DeepSeek V4-Flash** | Aplicado y validado |
| 2 | **Filtro de dominio vigente (CBR)** + campos `fojas` y `año_inscripcion_dominio` | Aplicado y validado |
| 3 | **Deuda extirpada**: M3 descolgado, filtro >$300M eliminado, columna deuda fuera de M5, descarga de mandamiento cortada en M2 | Aplicado y validado |
| 4 | **Resiliencia de red**: reintentos ante JSON truncado + timeout explícito | Aplicado |
| 5 | **Paralelización de M1**: ThreadPoolExecutor (3 workers) | Aplicado y validado |
| 6 | **Pulido**: normalización ordinal de tribunales, dedup de excluidos CBR, consola sincronizada, métricas de tokens/costo | Aplicado y validado |
| — | **Workers concurrentes en M2 (OJV)** | APLAZADO INDEFINIDAMENTE por decisión del abogado |

Costo de operación resultante: **~USD 0.02 por corrida** (antes ~USD 12/mes con Sonnet).

---

## 2. El parámetro de filtración por DOMINIO VIGENTE (CBR) — sección destacada

Este es el cambio de negocio más importante del ciclo. El cliente (abogado) exige que
**no aparezcan en el Excel causas cuyo dominio fue inscrito en el Conservador de
Bienes Raíces el año 2020 o posterior**. La lógica de "propiedad nueva" se traduce en:

- **dominio inscrito ≥ 2020 → EXCLUIR** (no llega al Excel de causas)
- **dominio inscrito < 2020 → MANTENER**
- **año no detectado / no parseable / fuera de rango → REVISAR** (se conserva y se marca, nunca se descarta en silencio)

### 2.1 Dónde vive cada pieza

**Archivo `filtro_cbr.py`** (en `D:\Mercurio\`, copia autocontenida del proyecto Regiones):
- Contiene la heurística histórica `evaluar_antiguedad_cbr(bloque_texto)` y la constante `_CBR_ANIO_CORTE = 2020`.
- **Importante:** en Mercurio esta función heurística (que busca el año por regex sobre texto crudo) **ya NO se usa para decidir**. Se conserva el archivo solo por la constante `_CBR_ANIO_CORTE`. Razón: en Mercurio la decisión se toma sobre el año que extrae la IA, no sobre texto crudo (ver abajo).

**Archivo `modulo1_mercurio.py`** — aquí está la lógica activa del filtro:
- **`PROMPT_EXTRACCION`**: se le pide a la IA (DeepSeek) que devuelva por cada aviso, además del contrato base, los campos:
  - `año_inscripcion_dominio` (año del dominio en el CBR, formato "YYYY" o null)
  - `fojas` (número de fojas de la inscripción, ej "1234" o "1234 vta.", o null)
  - **Nota histórica:** existió un tercer campo `texto_dominio` (cláusula verbatim) que se ELIMINÓ porque inflaba la salida de DeepSeek y causaba truncamiento por timeout de pasarela. No reintroducir sin manejar el truncamiento.
- **`_evaluar_cbr_por_anio(anio_raw)`**: función determinista (NO heurística) que decide sobre `año_inscripcion_dominio`. Cuatro ramas:
  - ≥ 2020 (y ≤ 2027) → EXCLUIR
  - 1900 ≤ año < 2020 → MANTENER
  - null / vacío / no parseable a 4 dígitos → REVISAR ("Año CBR no detectado")
  - fuera de rango 1900–2027 → REVISAR ("Año CBR fuera de rango") — atrapa alucinaciones de la IA
- **Inyección en el loop de página (Fase B / post-proceso secuencial)**: tras `_normalizar_aviso`, se llama `_evaluar_cbr_por_anio(aviso.get("año_inscripcion_dominio"))`. Si EXCLUIR → `continue` (no entra al pipeline) + se acumula en `st.excluidos_cbr`. Si no → se asignan `cbr_anio`, `cbr_flag_revision`, `cbr_motivo` al dict.
- **Salvaguarda anti-borrado-silencioso**: si la IA no extrae el año, el resultado es REVISAR (se conserva), nunca EXCLUIR. Un fallo de extracción jamás elimina una causa.

**Archivo `modulo5_reporte.py`** — la salida visible:
- Columnas nuevas en `_COLUMNAS`: **`Fs.`** (campo `fojas`) y **`CBR Motivo`** (campo `cbr_motivo`).
- **Tabla de transparencia** debajo de la tabla principal de causas: "PROPIEDADES NUEVAS EXCLUIDAS (dominio >= 2020)", con columnas Tribunal / ROL / Año / Año Dominio. Permite al abogado ver qué propiedades nuevas se filtraron (evita que un Excel corto parezca un fallo del bot). La lista llega deduplicada por ROL.

### 2.2 Diferencia clave vs Regiones (no confundir)

| Aspecto | Regiones | Mercurio |
|---|---|---|
| Sobre qué decide CBR | regex sobre texto crudo del aviso (`evaluar_antiguedad_cbr`) | año extraído por la IA (`_evaluar_cbr_por_anio`) |
| Por qué | arquitectura regex-primero, llamada IA por aviso | arquitectura IA-primero, llamada por página completa |
| Destino de REVISAR | `PENDIENTE_REVISION_MANUAL` en `filtrador_saldos.py` | columna `CBR Motivo` en el Excel (Mercurio no tiene filtrador de saldos) |

### 2.3 Comando Cline para extraer info del filtro de dominio vigente

Para que un proyecto hermano (o una sesión futura) recupere los internos reales del
filtro CBR de Mercurio, usar Cline en **modo PLAN (solo lectura)** con este prompt:

```
Modo: PLAN. Solo lectura, no editar nada. Workspace: D:\Mercurio\

Objetivo: extraer la lógica completa del filtro de dominio vigente (CBR).
Lee el contenido real; no inventes líneas ni firmas.

1. filtro_cbr.py: contenido completo. Confirma si evaluar_antiguedad_cbr se
   sigue usando o quedó solo como fuente de la constante _CBR_ANIO_CORTE.
   Corre: grep -rn "evaluar_antiguedad_cbr\|_CBR_ANIO_CORTE\|_evaluar_cbr_por_anio" .
2. En modulo1_mercurio.py, reporta verbatim:
   - La función _evaluar_cbr_por_anio (rango de líneas + cuerpo completo).
   - El bloque de PROMPT_EXTRACCION donde se piden año_inscripcion_dominio y fojas.
   - El punto del loop de página donde se inyecta el filtro CBR (la llamada a
     _evaluar_cbr_por_anio, el continue de EXCLUIR, y la acumulación en
     st.excluidos_cbr).
   - Dónde se deduplica st.excluidos_cbr antes de pasarlo al reporte.
3. En modulo5_reporte.py, reporta:
   - Las columnas Fs. y CBR Motivo en _COLUMNAS.
   - El bloque que escribe la tabla "PROPIEDADES NUEVAS EXCLUIDAS".

Entrega: archivo → símbolo → rango de líneas → código verbatim. Declara ausente
cualquier símbolo que no exista en vez de inventarlo.
```

---

## 3. Arquitectura actual del pipeline (post-ciclo)

```
main.py (orquestador)
  │
  ├─ M1  modulo1_mercurio.py   → extracción (DeepSeek V4-Flash, por página, 3 workers)
  │                              + post-proceso regex (ROL, _limpiar_tribunal,
  │                                _normalizar_ordinal_tribunal, buscar_corte)
  │                              + filtro CBR (_evaluar_cbr_por_anio)
  │                              + filtros RM / BancoEstado / EstaciónCentral / pre-2018
  │                              + dedup (historial + ejecución)
  │
  ├─ M2  modulo2_ojv.py        → consulta OJV: demandado real, tipo_procedimiento
  │                              (descarga de mandamiento ELIMINADA este ciclo)
  │                              [workers concurrentes: APLAZADO]
  │
  ├─ M3  modulo3_extractor.py  → DESCOLGADO (comentado en main.py)
  │
  └─ M5  modulo5_reporte.py    → Excel: tabla de causas + tabla de excluidos CBR
                                 + hoja Resumen (validación OJV + métricas tokens/costo)
```

### Cambio de motor (DeepSeek)
- `config.py`: `MODELO_EXTRACCION` ("sonnet" | "deepseek") + `DEEPSEEK_API_KEY` + tarifas
  `DEEPSEEK_PRECIO_INPUT_USD_POR_1M` / `_OUTPUT_`.
- Rollback a Sonnet: cambiar `MODELO_EXTRACCION = "sonnet"` en config (sin tocar código).
- Modelo DeepSeek: `deepseek-v4-flash`, vía SDK OpenAI, `base_url=https://api.deepseek.com`,
  modo Non-Thinking, `max_tokens=16384`.
- Resiliencia: 3 intentos por página, timeout 120s, JSON truncado lanza ValueError que
  dispara el reintento (un "[]" legítimo NO reintenta).

### Métricas
- `st.tokens_input` / `st.tokens_output` acumulan el `usage` de cada llamada.
- Canal lateral `obtener_metricas()` lleva tokens y `excluidos_cbr` a M5 sin cambiar
  la firma pública de `extraer_mercurio`.
- Costo USD se calcula solo si el motor es deepseek (con tarifas de config).

---

## 4. Reglas y aprendizajes del ciclo (para no repetir errores)

1. **El truncamiento de DeepSeek era de RED, no de tokens.** Cortes a ~3K caracteres con
   límite de salida de 384K = timeout de pasarela por generación lenta. Fix correcto:
   reintento + timeout, NO bajar max_tokens ni recortar campos.
2. **No recortar el payload por "1616".** Los avisos 1616 se dispersan entre columnas;
   recortar por esa etiqueta pierde causas válidas. Con DeepSeek el costo por página es
   ~1 centavo: no vale la pena arriesgar completitud.
3. **CBR decide sobre el año de la IA, no sobre texto verbatim.** El campo verbatim
   rompía la salida; el año (4 dígitos) es trivial de extraer y suficiente.
4. **No tocar módulos heredados sin mapearlos primero (PLAN antes que ACT).** M2/M5/OJV
   llevaban 2 meses sin fallar; cada cambio fue precedido de minería de solo lectura.
5. **Validar con datos reales, no asumir.** Cada fix se confirmó en el Excel/log de una
   corrida, no por la descripción del diff.

---

## 5. Pendientes conocidos (no bloquean operación)

- **Seguridad:** rotar `MERCURIO_PASS` (quedó expuesta en historial de chat) y confirmar
  que `config.py` está en `.gitignore`. La credencial está hardcodeada en `config.py`.
- **Cabo cosmético:** la consola del .bat aún imprime un tablero residual de deuda en
  ceros ("CON DEUDA / SIN PDF / SIN MONTO") antes del RESUMEN EJECUTIVO nuevo. No engaña
  (va en ceros) pero conviene localizar el segundo punto de impresión y quitarlo.
- **Fix 4 (workers OJV):** aplazado por el abogado. Si se retoma: PLAN previo sobre el
  M2 REAL de Mercurio (no el de Regiones), riesgo operativo = no correr Mercurio y
  Regiones en paralelo (misma IP contra el WAF del PJUD; no hay credencial PJUD, la OJV
  es consulta anónima).

---

## 6. Entorno y portabilidad

- Python 3.14, entorno virtual local en `D:\Mercurio\.venv\` (NO va a GitHub).
- Dependencias congeladas en `requirements.txt`: playwright, anthropic, openai,
  openpyxl, rapidfuzz, pandas (+ Chromium vía `playwright install chromium`).
- `pandas` lo importa `ojv_remates.py` (heredado); confirmar si es uso real o import
  muerto en una limpieza futura.
