# Bitácora de la exploración del PJUD (Oficina Judicial Virtual)

Documento único de la fase exploratoria para volver a llegar al mandamiento o a las bases de remate de cada causa del Excel del Mercurio. Abierta por decisión explícita de Diego el 25 de Noviembre de 2026. Esta bitácora solo crece. Una corrección se anota abajo con su fecha y nunca se borra lo anterior. Cada afirmación lleva si está verificada (con su fuente) o es un supuesto, y su n cuando es una medición.

Objetivo de Diego. Una columna en el Excel del Mercurio con la deuda del mandamiento (o el dato que corresponda según el procedimiento). Hoy el Mercurio corre solo en GitHub a las 5 sin nadie mirando, y ahí el WAF lo frenaría. La fase debe responder si existe una forma realista de llegar a esa columna y cuál.

Reglas de Diego para esta fase. Nada de Playwright, Selenium ni ningún navegador automatizado propio. Nada de navegadores "stealth", cambiar la huella del navegador o parecidos. Todo en el Chrome real de Diego, a paso de persona, con Diego frente al PC. Un CAPTCHA lo resuelve Diego, nunca un medio automático. Pocas consultas y con pausas. No se guardan RUT, teléfonos ni correos de personas salvo decisión de Diego. Todo lo que cobre se avisa en negrita antes. No se toca el código del robot sin decisión aparte. Agendar_Remates y Matriz_Causas_Activas solo se leen.

## 1. Fuentes leídas el 25 de Noviembre

| Fuente | Dónde | Qué aporta |
|---|---|---|
| El_backend_proyecto_RM_PJUD.md | git show 53d757c (3 de Julio de 2026) | Flujo completo del motor viejo, selectores, fuzzy de Corte y tribunal, descarga |
| AVISO_WAF_PJUD_para_otros_proyectos.md | git show 7fb6474 | WAF F5 con Shape, CAPTCHA de imagen, cookies TS, bloqueo intermitente |
| ADDENDUM_MERCURIO_2026-06-12.md | git show 7fb6474 | Contexto de Junio, nada nuevo del PJUD |
| ojv_remates.py v10.2, modulo2_ojv.py, modulo3_extractor.py | git show 8edd5ee^ | El código que corría. Nació el 15 de Marzo de 2026 (135df5e) y se borró el 3 de Julio (8edd5ee) |
| CORRETAJE_PROPIEDADES.md | D:\Agendar_Remates (solo lectura) | Prueba del 12 de Noviembre con C-15362-2025 del 11° Civil |
| ENTRAMPADOS.md | D:\Matriz_Causas_Activas (solo lectura, acceso dado por Diego) | Historia del muro del WAF de Junio y Julio |
| Condiciones de uso de la OJV | oficinajudicialvirtual.pjud.cl/home/condicionesdeuso.php, leídas en el Chrome de Diego | Ver sección 4 |

## 2. Cómo se hacía entre Marzo y Julio de 2026 (verificado en el código de 8edd5ee^)

Playwright con su propio Chromium, ventana visible, slow_mo 100, sin login. Todas las causas del día seguidas con 2 segundos de pausa. Por causa, indexN.php, Consulta causas, competencia Civil (value 3), Corte y tribunal por parecido de texto (rapidfuzz token_set_ratio, umbral 80), libro C, rol y año, Buscar, abrir solo la fila con el rol y el año exactos, leer demandante y demandado en Litigantes, leer el procedimiento en el detalle.

Ruteo por procedimiento.

| Procedimiento en el detalle | Cuaderno | Documento | Cómo se elige la fila |
|---|---|---|---|
| Ejecutivo obligación de dar | Apremio | Mandamiento | Etapa "Mandamiento" y trámite "Mandamiento", recorriendo desde los folios bajos. Respaldo, etapa Mandamiento sin "requerimiento" |
| Desposeimiento | Apremio (el texto "Apremio de desposeimiento" contiene "Apremio") | Mandamiento | Igual que el ejecutivo |
| Ley de Bancos | Principal | Bases de remate | Filas con "propone bases" o "bases de remate", sin "aprueba", "aprobada" ni "aprobado". Si hay varias, la de folio más alto |
| Liquidación simplificada o concursal, ordinarios, partición, arbitral, ejecutivo de mínima cuantía | Ninguno | Ninguno | Se descartaban |

modulo3_extractor.py leía el PDF con PyMuPDF (OCR con Tesseract solo si el PDF traía menos de 100 caracteres), buscaba el monto con frases ("pague la suma de", "capital adeudado" en el mandamiento, "mínimo para las posturas", "precio mínimo" en las bases), pasaba la UF a pesos con mindicador.cl y main.py descartaba deudas sobre $300.000.000.

Qué se rompió. El 3 de Julio el commit 8edd5ee borró la capa del PJUD con el mensaje "WAF F5/Shape bloquea OJV 24/7".

## 3. Lo que dicen los registros anteriores del WAF (verificado en los documentos, no repetido hoy salvo donde se indica)

Pila de protección de la OJV según ENTRAMPADOS.md sección 2. F5 BIG-IP ASM (la página "The requested URL was rejected... Your support ID is"), Shape Security (JavaScript que puntúa el navegador, cookies TS) y Google reCAPTCHA invisible que puntúa en silencio.

Hallazgos de Julio que importan para esta fase.

| Fecha | Hallazgo | Fuente |
|---|---|---|
| Antes del 9 de Julio | La extensión de Claude en un Chrome real también caía en la segunda búsqueda de la sesión. El problema no era Playwright | ENTRAMPADOS.md sección 4 |
| 9 de Julio | La causa era la cookie de Shape TS03f870c8029, de unos 30 segundos de vida, que solo se renueva cuando la página recibe respuesta del servidor. Recargar la página antes de cada causa la renueva y el bloqueo desapareció (4 de 4 búsquedas, n=4) | ENTRAMPADOS.md sección 3 |
| 10 de Julio | Un cuaderno que no carga deja envejecer la cookie y debilita la causa siguiente | ENTRAMPADOS.md sección 9 |
| 11 de Julio | Diego navegó a mano unas 7 búsquedas seguidas sin bloqueo (n=7) | ENTRAMPADOS.md sección 10.3 |
| 12 de Julio | Con el bot de Matriz (Playwright) el bloqueo llegó cerca de la tercera causa con la cookie sana. Se atribuyó al análisis de comportamiento de Shape sobre la sesión automatizada | ENTRAMPADOS.md sección 11 |
| 27 de Julio | El botón Buscar lleva un token de reCAPTCHA v3 que genera el navegador (action validate_captcha_rit) | ENTRAMPADOS.md sección 15.6 |
| 12 de Noviembre | Claude en el Chrome de Diego, como Invitado, llegó a C-15362-2025 del 11° Civil. Diego hizo el clic al cuaderno de apremio. Mandamiento en el folio 1 (24 de Diciembre de 2025), 805,1377 UF. Sin CAPTCHA anotado (n=1) | CORRETAJE_PROPIEDADES.md de Agendar_Remates |

ENTRAMPADOS.md sigue con Bright Data y Zyte (navegadores e IP de terceros). Quedan fuera de esta fase por las reglas de Diego y no se consideran como opción.

## 4. Condiciones de uso de la OJV (verificado, leídas el 25 de Noviembre)

Cinco cláusulas, pensadas para la tramitación con Clave Única. Ninguna prohíbe de forma expresa la consulta como Invitado ni el uso asistido. La cuarta obliga a no usar el servicio de forma que pueda dañar, inutilizar o sobrecargar el portal o impedir su uso normal. La tercera remite a las condiciones generales de poderjudicial.cl, que no se leyeron. Lectura de Claude, pocas causas a paso de persona calzan con la cuarta y un recorrido masivo no. Claude no es abogado, conviene que lo mire uno de los abogados si pasa a ser diario.

## 5. Ley General de Bancos (verificado en la web el 25 de Noviembre)

El procedimiento especial hipotecario de la Ley General de Bancos (DFL 3 de 1997) está en el Título XIII, artículos 103 y siguientes. El 104 trata el mínimo de la subasta. Los artículos 60 y 64 que mencionó Diego tratan de otros temas (gestión y solvencia, encaje) y no regulan este juicio. Fuentes, iura.cl (artículo 103 del DFL 3) y fallos citados por diarioconstitucional.cl.

## 6. Mediciones en el Chrome de Diego (bitácora acumulativa)

Método. Extensión Claude in Chrome, pestaña nueva, Diego presente. Pausas de 1 a 3 segundos entre acciones. Sin abrir la pestaña Litigantes (trae RUT). Sin descargar al disco. Ante CAPTCHA o página de F5, detenerse y avisar.

### Causa 1. C-610-2025 del 30° Juzgado Civil de Santiago (Excel del 25 de Noviembre, tabla principal)

Elegida por Claude con el supuesto de que una aseguradora (Bice Vida) sería juicio ejecutivo. El supuesto resultó falso, es Ley de Bancos.

| Paso | Hora (aprox.) | Duración (aprox.) | Resultado |
|---|---|---|---|
| Abrir home/index.php | 11.31 | 5 s | Cargó con el aviso semanal y el sello de reCAPTCHA. Sin desafío |
| Cerrar aviso y clic en Consulta causas | | 3 s | Entró a indexN.php como Invitado. Sin desafío |
| Competencia Civil, C.A. de Santiago (value 90), 30º Juzgado Civil (value 288), libro C, rol 610, año 2025 | | 25 s | Menús cargaron bien |
| Buscar | | 9 s | 1 fila, C-610-2025, 15/01/2025, BICE VIDA COMPAÑÍA DE SEGUROS S.A/GODOY. Sin CAPTCHA |
| Abrir detalle con la lupa | 11.33 | 18 s | "Cargando..." y luego el detalle completo |
| Total hasta el expediente | 11.31 a 11.33 | 2 min 17 s | Sin CAPTCHA, sin F5, sin clic de Diego (n=1) |
| Abrir el PDF del folio 30 con la pestaña quieta unos 10 minutos | 11.43 | 5 s | Abrió en otra pestaña (docuN.php). Sin CAPTCHA |

Lo que muestra el detalle (verificado, capturas). Proc. Ley de Bancos. Etapa 6 Recursos y/o ejecución. Cuadernos "1 - Principal" y "2 - Medida precautoria", sin Apremio. 50 folios en el Principal, ninguno llamado Mandamiento. Folios útiles. 1 Ingreso demanda (15/01/2025). 13 Requerimiento de pago (21/04/2025). 27 Solicita liquidación (28/08/2025). 30 Propone bases de remate (25/09/2025). 50 Aprueba bases de remate.

Bases del folio 30 (verificado, leídas en pantalla, PDF con texto de 8 páginas). Departamento 210 del Block 43, Avenida Salvador Sur 1339, Ñuñoa. Dominio a fojas 61985 número 98698 del año 2007 del CBR de Santiago. Cláusula TERCERO, "El precio mínimo para comenzar las posturas será la suma de 587,724811 Unidades de Fomento", más $450.000 de costas personales y $16.000 de costas procesales. Remate por videoconferencia (Zoom).

Prueba del lector viejo (verificado en la nube de Claude, con el texto copiado de la pantalla, no con el PDF). Los patrones _CTX_BASES de modulo3_extractor.py sacan 587,724811 UF por el patrón "precio mínimo" (el sexto de la lista). Los tres primeros no calzan porque el texto dice "mínimo para comenzar las posturas".

Cambios del PJUD respecto de Julio (verificado hoy).

| Pieza | Julio (código viejo) | 25 de Noviembre |
|---|---|---|
| Descarga del documento | /civil/documentos/doculs.php con dtaDoc | /ADIR_871/civil/documentos/docuN.php con dtaDoc |
| Clave del cuaderno y del documento | JWT | JWT que vence a la hora de emitida (iat y exp separados por 3.600 s en la clave del selector de cuadernos) |
| Opciones del tribunal | "30° Juzgado Civil de Santiago" | "30º Juzgado Civil de Santiago" (o volada) |

### Pestaña quieta desde la mañana (25 de Noviembre, 17.50)

No se pudo medir. Diego dio el visto bueno al Paso 2c a las 17.50 y la pestaña de las 11.33 ya no estaba al alcance de la extensión (la sesión de Claude in Chrome se renovó y el grupo de pestañas viejo quedó fuera de su control). Queda pendiente medir cuánto dura una sesión quieta.

### Causa 2. C-1118-2026 del 3° Juzgado Civil de Santiago (Excel del 25 de Noviembre, tabla principal, sin carátula leída por el Mercurio)

| Paso | Hora (aprox.) | Duración (aprox.) | Resultado |
|---|---|---|---|
| Pestaña nueva, home/index.php | 17.50 | 5 s | Cargó con el aviso semanal. Sin desafío |
| Cerrar aviso y Consulta causas | | 5 s | indexN.php como Invitado. Sin desafío |
| Civil, C.A. de Santiago, 3º Civil (value 261), C, 1118, 2026 | | 20 s | Menús cargaron bien |
| Buscar | 17.51 | 9 s | 1 fila, C-1118-2026. Sin CAPTCHA |
| Abrir detalle | 17.52 | 10 s | Detalle abierto (F. Ing. 23/01/2026). Sin CAPTCHA |

Lo que muestra el detalle (verificado leyendo la página, sin captura). Proc. Ley de Bancos. Etapa 6 Recursos y/o ejecución. Un solo cuaderno, "1 - Principal". En la historia hay "Propone bases de remate", "Aprueba bases de remate" y "Fija día y hora remate bienes raíces".

Problema de la herramienta, no del PJUD. Desde el Buscar de esta causa las capturas de pantalla de la extensión fallaron (3 de 3, "Page.captureScreenshot timed out", renderer sin respuesta), mientras la lectura de la página siguió funcionando. Supuesto, la ventana de Chrome quedó en segundo plano o minimizada y Chrome dejó de dibujar la pestaña. Se detuvo la prueba para pedirle a Diego que deje la ventana visible.

### Retomada a las 19.55 (Diego tenía Chrome minimizado y luego apagó el PC por la tarde, dicho por Diego)

Lección de la herramienta. Con la ventana de Chrome minimizada la extensión no puede sacar capturas. Para estas pruebas la ventana tiene que quedar visible.

Pestaña quieta 2 horas (verificado). La pestaña con el detalle de C-1118-2026 quedó abierta de 17.52 a 19.56. Al hacer clic en el PDF del folio 31 se abrió una pestaña en blanco, sin PDF, sin CAPTCHA y sin página de F5. Supuesto, la clave del documento venció (dura una hora). Al recargar desde la portada todo volvió a funcionar sin desafío. Conclusión de n=1, una sesión quieta no se bloquea pero sus enlaces a documentos mueren, así que hay que recargar antes de cada causa.

### Causa 2 (continuación). C-1118-2026 del 3° Civil, recargada desde la portada a las 19.56

| Paso | Hora (aprox.) | Resultado |
|---|---|---|
| Portada, aviso, Consulta causas, Civil, Santiago, 3º Civil, 1118, 2026, Buscar, detalle | 19.56 a 19.57 | Sin CAPTCHA |
| PDF folio 31 "Propone bases de remate" (15/06/2026) | 19.57 | Abrió (docuN.php). 4 páginas con texto. Carátula "BICE VIDA CON ZUÑIGA PEÑA" (el Mercurio no la había leído). Inmueble en calle Antumalal 548, Quilicura, dominio fojas 30369 de 2006. Cláusula 4, mínimo 906,337383 UF más $250.000 y $91.600 de costas |
| PDF folio 36 "Presenta bases corregidas" (09/11/2026) | 19.57 | Abrió. El documento se titula "Propone nueva liquidación del crédito y su aprobación... segundo otrosí modifica bases". Liquidación actualizada del crédito al 9 de Octubre de 2026 por 923,774602 UF, y el mínimo pasa a 923,774602 UF más las mismas costas. El nombre del archivo PDF dice otra carátula (plantilla del abogado), el contenido es de esta causa |

Historia del Principal (verificado en pantalla). Folio 31 Propone bases (15/06/2026), 33 Aprueba bases (18/06/2026), 35 Fija día y hora remate (01/07/2026), 36 Presenta bases corregidas (09/11/2026), 37 Mero trámite con marca [Nulo] (13/11/2026), 38 Nulidad de lo Obrado (19/11/2026), 39 Certificado (20/11/2026).

Hallazgo sobre la regla vieja (verificado en el código de 8edd5ee^ y en esta causa). buscar_bases_remate solo toma filas con "propone bases" o "bases de remate". "Presenta bases corregidas" no tiene ninguna de las dos frases, así que la regla vieja habría tomado el folio 31 (906,337383 UF) y no el 36 (923,774602 UF, el más reciente). n=1 causa con bases corregidas de 2 Ley de Bancos.

Hallazgo de negocio (verificado en esta causa, n=1). En Ley de Bancos el escrito de bases corregidas trae la liquidación del crédito, o sea la deuda actualizada, y el mínimo se fija igual a esa deuda. En C-610-2025 existe un folio 27 "Solicita liquidación" (28/08/2025) que no se abrió.

### Causa 3. C-8703-2020 del 30° Civil (Excel del 25 de Noviembre, tabla principal, demandante Itaú Corpbanca)

| Paso | Hora (aprox.) | Duración (aprox.) | Resultado |
|---|---|---|---|
| Portada, aviso, Consulta causas | 19.58 | 8 s | Sin desafío |
| Civil, Santiago, 30º Civil, C, 8703, 2020, Buscar | 19.58 | 30 s | 1 fila. Sin CAPTCHA |
| Detalle | 19.59 | 10 s | Proc. Ejecutivo Obligación de Dar. Estado Proc. Concluido. Etapa 8 Terminada. Ubicación Corte de Apelaciones (remisión del 13/11/2026). Cuadernos 1 Principal y 2 Apremio Ejecutivo Obligación de Dar |
| Cambio al cuaderno 2 Apremio, hecho por Claude con el selector, sin clic de Diego | 19.59 | 8 s | Tabla recargada, 65 folios |
| PDF folio 1 Mandamiento (Etapa Mandamiento, trámite Mandamiento, 12/06/2020) | 19.59 | 6 s | Abrió (docuS.php, no docuN.php). 1 página con texto. "Pague... la suma de U.F.1393,8395 equivalentes al día 05 de Junio del año 2020 a la suma de $40.026.219, más intereses y costas" |

Otros folios del Apremio vistos. 2 Resolución Mandamiento (23/02/2024), 8 Requerimiento de pago (08/05/2024), 9 y 14 Fija mínimo Art. 488 CPC, 10 Propone bases (21/06/2024), 13 Presenta bases corregidas (27/08/2024), 17 Aprueba bases (23/10/2024), 35 y 41 Actualiza el mínimo (20/11/2025 y 06/03/2026).

Prueba del lector viejo (verificado con el texto copiado de la pantalla). modulo3 saca $40.026.219 (patrón genérico "la suma de", en pesos) y pierde las 1.393,8395 UF, porque el mandamiento escribe "U.F." antes del número y el patrón busca la UF después.

### Causa 4. C-652-2026 del 1° Civil de Viña del Mar (Excel del 25 de Noviembre, tabla principal, Corte de Valparaíso, demandante una cooperativa)

| Paso | Hora (aprox.) | Duración (aprox.) | Resultado |
|---|---|---|---|
| Portada, aviso, Consulta causas | 19.59 | 8 s | Sin desafío |
| Civil, C.A. de Valparaíso (value 30), 1º Juzgado Civil de Viña del Mar, C, 652, 2026, Buscar | 20.00 | 35 s | 1 fila. Sin CAPTCHA |
| Detalle | 20.00 | 10 s | Proc. Ejecutivo Obligación de Dar. Etapa 2 Excepciones en el Principal. Cuadernos 1 Principal y 2 Apremio Ejecutivo Obligación de Dar |
| Cambio al cuaderno 2 Apremio, hecho por Claude | 20.00 | 8 s | 23 folios |
| PDF folio 1 Mandamiento (09/03/2026) | 20.01 | 6 s | Abrió (docuS.php). 1 página con texto, firma electrónica de la jueza. "Ordena despachar mandamiento". Pague la suma de $19.541.599, intereses y costas |

Prueba del lector viejo (verificado con el texto copiado). modulo3 saca $19.541.599.

El mandamiento trae nombre y domicilio de la parte demandada. No se anotan aquí (regla de Diego).

### Resumen acumulado de mediciones al 25 de Noviembre, 20.01 (no se reescribe, se agregan filas)

| Causa | Tribunal | Procedimiento | Documento que da el monto | Monto | Lector viejo | CAPTCHA | Clic de Diego |
|---|---|---|---|---|---|---|---|
| C-610-2025 | 30° Civil Santiago | Ley de Bancos | Bases folio 30 | Mínimo 587,724811 UF | 587,724811 UF | No | No |
| C-1118-2026 | 3° Civil Santiago | Ley de Bancos | Bases folio 31 / bases corregidas y liquidación folio 36 | 906,337383 UF / 923,774602 UF (deuda al 09/10/2026) | Tomaría el folio 31 | No | No |
| C-8703-2020 | 30° Civil Santiago | Ejecutivo Obligación de Dar | Mandamiento folio 1 Apremio | 1.393,8395 UF = $40.026.219 al 05/06/2020 | $40.026.219 (pierde la UF) | No | No |
| C-652-2026 | 1° Civil Viña del Mar | Ejecutivo Obligación de Dar | Mandamiento folio 1 Apremio | $19.541.599 al 09/03/2026 | $19.541.599 | No | No |

Totales del día (n). 4 causas distintas, 5 búsquedas (la 1118 dos veces), 7 PDF pedidos (6 abiertos, 1 en blanco por la sesión vieja), 0 CAPTCHA visibles, 0 páginas de F5, 0 clics de Diego. Tiempo por causa desde la portada hasta el documento, entre 1,5 y 2,5 minutos a paso lento. Las búsquedas de la tarde fueron seguidas, de 19.56 a 20.01, recargando la portada antes de cada una. Dos de cuatro son Ley de Bancos y dos son ejecutivos. Todas las del Excel de hoy salieron en la primera búsqueda con el rol, el año y el tribunal que leyó el Mercurio.

Cambios del PJUD vistos hoy (se suman a la tabla de la causa 1). Los escritos se abren con docuN.php y las resoluciones (mandamientos) con docuS.php, los dos bajo /ADIR_871/civil/documentos/.

## 7. Preguntas de Diego y respuestas de Claude

25 de Noviembre. ¿Por qué el Chrome de Diego manejado por Claude funciona y logra ser indetectable? Respuesta en el chat, resumida en la sección 8.

## 8. Por qué el Chrome real pasa y una API no maneja un navegador (respuesta del 25 de Noviembre)

No es indetectable ni está hecho para esconderse. ENTRAMPADOS.md registra que antes del 9 de Julio la extensión también caía en la segunda búsqueda. Pasa hoy porque el Chrome de Diego es un navegador de verdad, con su perfil, historial, cookies e IP de casa, y porque Claude hace una causa a la vez con pausas y recargando la página, que es lo que el WAF espera de una persona. Lo que vigila Shape es el ambiente del navegador y el comportamiento de la sesión, y aquí los dos son de una persona con poco volumen (supuesto con base en ENTRAMPADOS.md, n=1 hoy).

Haiku por API solo recibe texto y devuelve texto, no tiene manos. Para hacer clics, un programa en el PC tiene que ejecutar sus órdenes dentro de un navegador. Ese programa es justamente Playwright, Selenium o una extensión hecha a medida, que es lo que Diego excluyó. La extensión Claude in Chrome cumple ese papel, pero la maneja la app de Claude y no un script propio. Para esta tarea la navegación es siempre la misma, así que la IA no hace falta para navegar. Solo ayudaría a leer un PDF raro, y el lector viejo con código ya saca el monto de unas bases como las de C-610-2025.

## 9. Opciones a comparar en el Paso 3 (sin decidir)

A. Paso aparte en el PC de Diego con su Chrome, después del correo de las 5 (segundo correo o Excel completo). B. Solo las causas que marque el abogado. C. Tarea programada de Claude que use el Chrome de Diego cada mañana. D (idea de Diego, 25 de Noviembre). Programa en el PC del abogado con una ventana donde adjunta el Excel y desde su PC se completa todo, con la duda de si necesita Claude instalado o si sirve la API con Haiku. Recordatorio, hoy "el programa no se corre en el PC de Diego", así que toda opción en un PC es una excepción que decide Diego.

## 9b. Paso 3. Comparación de opciones (25 de Noviembre, 21.50)

Base medida para comparar. 4 causas, 0 CAPTCHA, entre 1,5 y 2,5 minutos por causa hasta el documento (n=4). El Excel del 25 de Noviembre trajo 10 causas en la principal, así que un día así serían unos 20 a 25 minutos (supuesto, 10 por 2 a 2,5 minutos). Nunca se midieron más de 3 causas seguidas en una sesión.

Verificado en la documentación de Anthropic (code.claude.com/docs/en/chrome y support.claude.com, leído el 25 de Noviembre). Claude Code se puede abrir con Chrome con "claude --chrome", trabaja en una ventana de Chrome visible y, cuando encuentra un CAPTCHA o una página de inicio de sesión, se detiene y le pide a la persona que lo resuelva. Claude in Chrome requiere un plan pagado de Claude. Supuesto sin verificar, que funcione igual en una ejecución no interactiva (claude -p) lanzada desde un archivo.

Un .py solo, sin Claude, no puede navegar la OJV sin un navegador automatizado propio, que Diego excluyó. Por eso la opción D se entiende como un lanzador con ventana que abre Claude con Chrome en el PC del abogado.

| Opción | Cómo funciona | Trabajo para dejarla fija | Riesgo | Costo |
|---|---|---|---|---|
| A. PC de Diego después del correo de las 5 | Diego abre este chat (o uno fijo) con el Excel del día y Claude recorre las causas de la principal en su Chrome. Devuelve un Excel completo o un segundo correo | Bajo. Un procedimiento escrito y un lector de montos corregido | Bajo. Diego presente para el CAPTCHA. Depende de que Diego esté cada mañana y de no usar el PC esos 20 minutos | Sin cobro de API. Gasta uso del plan de Diego |
| B. Solo las causas que marque el abogado | Igual que A o D, pero con 2 o 3 causas elegidas | Muy bajo | El más bajo, menos consultas al PJUD | El menor. Se puede combinar con cualquier otra |
| C. Tarea programada de Claude con el Chrome de Diego | Una tarea fija a una hora, con el PC encendido, Chrome visible y la app de Claude abierta | Medio | Alto si nadie mira. Un CAPTCHA deja la tarea detenida. Choca con la regla de Diego de estar presente y con el freno anotado el 12 de Noviembre ("no dejarlo programado sin nadie mirando"). Aceptable solo si la hora es una en que Diego está frente al PC | Igual que A |
| D. Programa con ventana en el PC del abogado (idea de Diego) | El abogado adjunta el Excel en una ventana simple, esa ventana abre Claude Code con Chrome y un texto fijo, y al final queda el Excel con la columna. Si sale un CAPTCHA, lo resuelve el abogado | Medio a alto. Instalar Claude Code y la extensión en su PC, una cuenta pagada de Claude a nombre del abogado o de la oficina (no la de Diego), el lanzador y el texto fijo, y probarlo con él | Medio. El abogado tiene que estar frente al PC y entender qué hacer si se detiene. Excepción a la regla "el programa no se corre en el PC del abogado", la decide Diego | Una suscripción de Claude para la oficina. Sin cobro de API si el monto lo lee código |

Recomendación de Claude. Primero un piloto con la opción A durante unos 5 días hábiles, con todas las causas de la principal (unas 10 por día), Diego presente, midiendo el CAPTCHA con 10 causas seguidas y el tiempo total. Ese es el dato que falta y decide todo lo demás. Si pasa limpio, se arma la D para que el abogado no dependa de Diego, y B queda como modo de respaldo para días con muchas causas. C no se recomienda mientras nadie pueda mirar.

## 9c. Qué falta para que pase a función fija (25 de Noviembre)

1. Decidir con el abogado qué número muestra la columna. En los ejecutivos, la deuda del mandamiento (en UF y en pesos, con su fecha). En Ley de Bancos, la liquidación del crédito más reciente si existe, y si no, el mínimo de las bases.
2. Fijar las reglas de lectura con lo aprendido. Ruteo por procedimiento de la regla vieja, más las bases corregidas y la liquidación, la UF escrita antes del número, y qué se anota cuando no hay documento (causa reservada, sin Apremio, terminada, sin mandamiento).
3. Piloto de 5 días (opción A) midiendo el CAPTCHA con 10 causas seguidas.
4. Elegir A o D, y cómo llega el Excel y cómo vuelve (Excel completo o segundo correo).
5. Escribir el procedimiento fijo y el lector de montos como código aparte del robot. El robot de GitHub no cambia.
6. Que un abogado revise las Condiciones de uso de la OJV si pasa a uso diario.

## 9d. Decisiones de Diego (26 de Noviembre, 10.48)

1. Exploracion_PJUD entra a git. Diego dice que nadie entra a su repositorio. Nota de Claude, el repositorio DFNR2026/RematesMercurio es público y cualquiera puede verlo. Los datos de las causas son públicos por decisión de Diego del 6 de Noviembre y la bitácora no trae nombres ni domicilios de demandados ni claves.
2. La columna se llama deuda/mandamiento y muestra lo que se debe en UF y al lado en pesos (CLP).
3. Diego preguntó si el piloto necesita su PC encendido y si existe una forma automática sin ningún PC encendido. Respuesta de Claude en la sección 9e.

## 9e. ¿Se puede sin ningún PC encendido? (respuesta del 26 de Noviembre)

No dentro de las reglas de esta fase. Todo lo medido funciona porque es un Chrome real, en un PC con IP de casa y con una persona que puede resolver un CAPTCHA. Para hacerlo sin ningún PC encendido habría que usar un navegador en un servidor (GitHub, un VPS o la nube), y eso es un navegador automatizado con IP de centro de datos, justo lo que el WAF bloqueaba en Julio y lo que Diego excluyó. Los servicios de terceros (Bright Data, Zyte) también quedan fuera por sus reglas. Por eso el robot de las 5 vive bien en GitHub, porque El Mercurio no tiene esa protección, y la parte del PJUD necesita un PC encendido (el de Diego o el del abogado). Lo que sí puede cambiar después del piloto es cuánto hay que estar mirando. Si en muchos días no aparece ningún CAPTCHA, Diego puede decidir probar una tarea programada a una hora fija (opción C), que se detiene sola si aparece uno. Igual necesita el PC encendido, con Chrome visible y la app de Claude abierta.

## 10. Correcciones

(Ninguna todavía.)
