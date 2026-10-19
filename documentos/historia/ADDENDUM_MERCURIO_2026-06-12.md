# Addendum al Cierre de Ciclo Mercurio — 12 de junio de 2026
**Complementa:** `CIERRE_CICLO_MERCURIO_2026-05.md` (la sección 6 de ese documento queda obsoleta).

---

## 1. MENTORÍA A REGIONES: CERRADA (actualiza la sección 6 del cierre anterior)

El harness CBR se corrió sobre datos reales con cobertura completa (106/106 bloques).
**Veredicto definitivo: la rama de desambiguación ambigua NO muerde** (métrica de oro = 0
en el total y en la población que producción v2 evalúa). El fix asimétrico quedó archivado;
sobrevive solo una vigilancia mensual de una línea por DOCX nuevo.

En el camino, la auditoría destapó y corrigió en Regiones: un punto ciego del 29% en el
propio harness (rama `else` faltante), un bug de pérdida silenciosa en el pre-filtro de
producción (`\d+` vs punto de miles — el pre-filtro era más estricto que el extractor que
gateaba), una red de seguridad CSV para descartes, y la eliminación completa de la ruta
v1 (−1.118 líneas). Detalle completo en `D:\Remates\CIERRE_CICLO_REGIONES_2026-06.md` y
`D:\Remates\TRASPASO_PENDIENTES_2026-06-12.md`. Hashes canónicos del ciclo Regiones:
`aaa8723`, `6efec23`, `3b122af`, `fbecfa1`.

## 2. PENDIENTE DE SEGURIDAD — EL ÚNICO "HAZLO YA" DE MERCURIO

**Rotar `MERCURIO_PASS`** (expuesta en texto plano en historial de chats):
1. Cambiar la contraseña en digital.elmercurio.com.
2. Editar `config.py` a mano en `D:\Mercurio` **y** en `E:\Mercurio` (PC del abogado).
3. La nueva contraseña NO se pega jamás en un chat (ni a Claude ni a Cline).
4. Verificar con una corrida: `ejecutar_mercurio.bat` con fecha del día.

Los demás pendientes siguen APLAZADOS por decisión (sin cambio): informe con 0 causas
(`if causas:` en main.py) y Tanda B de workers M2/OJV (riesgo PDF-en-disco sin resolver).

## 3. NUEVAS REGLAS DE MÉTODO (nacidas en el ciclo Regiones, aplican a AMBOS proyectos)

- **Terminal y git: 100% vía Cline.** Diego no ejecuta comandos; pega reportes o dice
  "listo, lee". ACTs con pasos numerados y condiciones de detención.
- **Git:** `git status --short` antes de todo commit; `git add <archivo>` explícito;
  PROHIBIDO `-am`, `add .`, `add -A`, `reset --hard`, `clean`, y todo `pull`/`rebase`
  fuera de guion (push rechazado = detenerse y reportar). Un commit = una historia.
- **Flujo sin copy-paste:** Cline escribe cada reporte en `MD_Cline\<Tanda>.md`; Claude
  lo lee del disco vía el conector Filesystem (Claude Desktop) y verifica de primera
  mano lo crítico — incluidos los refs de `.git` cuando los hashes no calzan.
  Al retomar trabajo en Mercurio: crear `D:\Mercurio\MD_Cline\` y usar la misma convención.
- **Validación por predicción numérica:** los criterios de éxito se fijan ANTES de
  correr (ej.: "pre-filtro 14→12, BancoEstado 6→7, post-parse 85→86"). Aciertos exactos
  o se detiene y audita.
- **El relato del agente se audita contra el código, siempre.** El ciclo Regiones acumuló
  10 desviaciones entre narrativa de Cline y evidencia verbatim — ninguna maliciosa,
  todas plausibles, varias casi costosas (un KeyError a producción, un borrado del
  --worker-mode). El verbatim es barato; creerle al resumen no.

## 4. APRENDIZAJES TRANSFERIBLES A RM (para tenerlos a mano si aplican)

- **Un pre-filtro debe ser superconjunto del extractor que protege.** Si RM alguna vez
  gatea con regex antes de la API (para ahorrar tokens), validar la equivalencia con
  corpus real antes de desplegar.
- **Un `else` no es cosmético** cuando la función puede retornar lista vacía: la
  equivalencia se demuestra con aritmética (105−46+1=60 vs 105+1=106), no con prosa.
- **Los contadores con nombre engañoso son deuda activa** ("sin_rol" que cuenta
  historial+RM+CBR esconde información). Revisar los contadores de M1 Mercurio con ese
  lente cuando haya tanda de calidad de logs.
- **Conocer la ruta de producción antes de instrumentar.** Preguntar "¿qué corre
  producción?" antes del primer diff.
