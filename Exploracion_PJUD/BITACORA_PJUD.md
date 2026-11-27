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

## 9f. Decisiones y preguntas de Diego (26 de Noviembre, 11.04)

1. La columna se llama Deuda (término más amplio, porque en Ley de Bancos no hay mandamiento). Va en UF y al lado en CLP. Corrige el nombre "deuda/mandamiento" anotado en 9d, que queda como registro.
2. Si el documento trae una sola moneda, la otra celda queda en blanco. No se convierte.
3. Diego pregunta si existe un Chrome en la nube que una IA maneje sin ningún PC encendido, como GitHub Actions, y propone intentarlo igual porque no está probado.

## 9g. Chrome en la nube, lo que se sabe (26 de Noviembre)

Verificado en la documentación de Anthropic leída el 26 de Noviembre. Las tareas programadas de Claude corren en la nube sin ningún dispositivo encendido, pero cuando una tarea maneja Chrome necesita la app de escritorio abierta y conectada. Los navegadores documentados para Claude son el que trae la app de escritorio y el Chrome del usuario con la extensión, los dos en un PC. No se encontró en la documentación un Chrome de Anthropic en la nube que Claude pueda manejar sin PC. En esta sesión de chat tampoco hay una herramienta de navegador en la nube.

Corrección de lo dicho en 9e. Ahí se escribió que un navegador en un servidor es "justo lo que el WAF bloqueaba en Julio". Es impreciso. Lo verificado en ENTRAMPADOS.md es que el bot con Playwright en el PC de Diego (IP de casa) pasaba la primera búsqueda y caía en la segunda por la cookie, que recargando pasó 3 o 4 búsquedas y que cerca de la tercera causa cayó por el análisis de comportamiento. Bright Data y Zyte, que son navegadores en la nube, sí pasaron el WAF, pero esos servicios lo logran ocultando la automatización y resolviendo el CAPTCHA solos (sección 12.5 de ENTRAMPADOS, "CAPTCHA se resuelve solo"), que es lo que Diego prohibió. Un navegador común en un servidor, sin esos trucos, nunca se probó contra la OJV. Que se bloquee es un supuesto.

Forma honesta de probarlo, sin PC y sin trucos (propuesta de Claude, sin decidir). Un flujo de prueba aparte en GitHub Actions, en una rama propia y a mano, con un Chrome normal manejado por un script, sin opciones para esconder la automatización y sin resolver CAPTCHA. Una sola causa del Excel, recargando la portada, y guardando capturas y el texto de lo que vio en cada paso (formulario, CAPTCHA, página de F5 o resultado). Si aparece cualquier desafío se detiene y lo anota. No toca el robot y no cobra. Requiere que Diego levante para esta prueba su regla de no usar Playwright ni un navegador automatizado propio, porque sin PC no hay otra forma de que alguien haga los clics.

## 9h. Prueba en la nube con GitHub Actions (26 de Noviembre, preparada antes de correr)

Decisión de Diego del 26 de Noviembre, 11.14. Levanta para esta prueba la regla de no usar un navegador automatizado propio. Aclaración de Claude, lo que se prueba sí es Playwright manejando un Chrome común, porque sin PC alguien tiene que dar los clics y ese alguien es un script.

Archivos en Exploracion_PJUD/prueba_nube. prueba_ojv_nube.py (el script) y prueba_ojv_nube.yml (el flujo, que va a .github/workflows solo en la rama prueba-ojv-nube y corre al subir esa rama). No toca el robot (ningún flujo del robot se dispara con un push, verificado en los cinco .yml), no usa secretos, no cobra.

Qué hace. Google Chrome del servidor, ventana visible con xvfb, sin argumentos extra, sin cambiar el agente de usuario ni navigator.webdriver, sin resolver CAPTCHA. Una causa, C-610-2025 del 30° Civil (la del 25 de Noviembre, ya conocida). Portada, Escape para el aviso, Consulta causas, Civil, Corte 90, tribunal 288, C, rol, año, Buscar y detalle, con pausas fijas de 1 a 3 segundos y 10 a 15 segundos de espera tras Buscar y tras el detalle. En cada paso guarda captura, largo del texto, firmas de bloqueo de F5, si hay un reCAPTCHA con desafío visible y los nombres de las cookies (sin valores). No abre Litigantes ni PDF. Tapa cualquier RUT en el resumen. Si ve un bloqueo, se detiene.

Probado en la nube de Claude el 26 de Noviembre sobre páginas falsas (Python 3.12, Playwright 1.63.0, Google Chrome y xvfb). Con una OJV falsa llega al detalle (LLEGA_AL_DETALLE en 46,6 s) y tapa el RUT. Con una página de bloqueo de F5 se detiene en la portada (BLOQUEO_EN_PORTADA). No se pudo probar contra la OJV real desde ahí.

Resultados posibles, fijados antes de correr. LLEGA_AL_DETALLE con "Ley de Bancos" y los cuadernos 1 Principal y 2 Medida precautoria (lo mismo que se vio el 25 de Noviembre en el Chrome de Diego). BLOQUEO_EN_PORTADA, BLOQUEO_EN_FORMULARIO, BLOQUEO_AL_LLENAR, BLOQUEO_AL_BUSCAR o BLOQUEO_EN_DETALLE (página de F5 o CAPTCHA visible). SIN_RESULTADOS (posible rechazo callado del reCAPTCHA v3 del botón Buscar, porque la causa sí existe). NO_LLEGA_AL_FORMULARIO, FALLA_AL_LLENAR o RESULTADO_NO_RECONOCIDO (cambio de la página o falla del script, se revisa con las capturas). Apuesta de Claude, unos 65% de que termine en un BLOQUEO o en SIN_RESULTADOS, basada en Julio (el bot caía incluso desde la IP de casa) y en que aquí la IP es de un centro de datos. Si llega al detalle, es una sola causa (n=1) y no prueba que se sostenga con 10.

## 9i. ¿Existe un reemplazo de Claude que maneje un Chrome en la nube? (26 de Noviembre)

Sí existen, verificado en la web el 26 de Noviembre. ChatGPT Work tiene un navegador en la nube que sigue trabajando con el PC apagado. Browserbase y servicios parecidos venden navegadores en la nube para agentes de IA. Pero los planes que pasan sitios protegidos incluyen modo sigiloso, proxies residenciales y resolución automática de CAPTCHA, que es lo que Diego prohibió (el plan gratis de Browserbase no trae nada de eso). Y la IA no hace falta para navegar, porque los pasos son siempre los mismos, un script basta. Por eso la prueba de GitHub Actions responde también esta pregunta. Si un Chrome común en un servidor pasa, un agente en la nube también podría. Si se bloquea, los únicos que pasarían son los que esconden la automatización.

## 9j. Resultado de la prueba en la nube (26 de Noviembre, corrida 45837987347, verificado por Claude en el disco)

Fuentes. Reportes_Claude_Code/REPORTE_PRUEBA_OJV_NUBE_2026-11-26.md, INFORMES_REPORTES/prueba_ojv_nube (resumen.json, resumen.md, 01_portada.png, 02_formulario.png y log.txt) y git. Rama prueba-ojv-nube en 1f7f084 con solo los dos archivos (281 inserciones). main sigue en 0cf5aa7, igual a origin/main.

| Paso | Segundos | URL | Qué pasó |
|---|---|---|---|
| 01_portada | 17,3 | home/index.php | Cargó la portada completa con el sello de reCAPTCHA. No apareció el aviso semanal que sí sale en el Chrome de Diego. Cookies BIGipServer, PHPSESSID, TS01262d1d, TS3ee74f51027 y _GRECAPTCHA |
| 02_formulario | 44,4 | loginN.php | Tras el clic en Consulta causas la página pasó a loginN.php con el título "La URL solicitada ha sido rechazada", el texto ". (2) ." y "Su numero de soporte es". Aparecieron las cookies de desafío de Shape TSPD_101, TS9fb3b593029 y TS9fb3b593078. El script esperó el formulario 25 s y cortó |

Conclusión (n=1). Desde un servidor de GitHub, con un Chrome común manejado por Playwright y sin trucos, el WAF F5 rechazó la entrada al formulario como Invitado. La portada carga, la consulta no. Cae dentro de la apuesta fijada antes de correr (bloqueo o sin resultados, 65%). Coincide con ENTRAMPADOS.md sección 14.3, donde un navegador sin la sesión de invitado rebota a loginN.php.

Corrección de Claude sobre su propio script. El resultado salió como NO_LLEGA_AL_FORMULARIO y no como BLOQUEO_EN_FORMULARIO porque las firmas de bloqueo del script estaban solo en inglés ("requested url was rejected", "your support id") y la OJV mostró la página en español ("La URL solicitada ha sido rechazada", "Su numero de soporte es"). El bloqueo sí ocurrió, lo prueban el título y la captura. Para una próxima prueba hay que agregar las firmas en español.

Peso de lo que hizo Claude Code. Siguió después de encontrar dos veces "secret" en la búsqueda de claves, aunque el texto decía detenerse. Las dos son la palabra "secretos" en comentarios (línea 8 del .py y línea 2 del .yml, verificado por Claude), sin ningún valor, así que el riesgo fue nulo. La lista de patrones la escribió Claude y estaba mal elegida, porque "secret" calza con "secretos". Agregó la línea Co-Authored-By de su sesión. Dejó el worktree D:\Mercurio_prueba_ojv sin borrar, como se pidió. Avisó que upload-artifact@v4 usa Node 20.

Lo que queda abierto, sin decidir. Repetir la prueba para tener n mayor que 1 (con las firmas en español). Probar un agente de IA con navegador en la nube de otro proveedor (Diego, 26 de Noviembre, "toca testear esto si llega a fallar lo demás"). Borrar o conservar la rama prueba-ojv-nube y el worktree.

## 9k. ¿Sirve el plan gratis de ChatGPT para la prueba? (26 de Noviembre, verificado en help.openai.com)

No. El navegador en la nube de ChatGPT Work está en los planes de pago, excepto Free y Go. En la app de escritorio el plan gratis sí trae ChatGPT Work, pero sin ese navegador en la nube, así que no prueba lo que se quiere (trabajar sin PC). La misma ayuda de OpenAI reconoce que algunos sitios bloquean las tareas del navegador en la nube y que esas restricciones las pone el sitio. Probarlo exige pagar un plan (por ejemplo Plus). Decisión pendiente de Diego.

## 9l. Decisiones de Diego y cuentas de Claude para el abogado (26 de Noviembre, 14.25)

Decisión de Diego. Se descarta probar ChatGPT (la tarjeta fue rechazada al activar el mes gratis de Plus). Se sigue con lo que ya funciona, Claude en un Chrome real.

Pregunta de Diego. Si el abogado usará la app de Claude en su PC, ¿se puede crear un perfil secundario en la misma cuenta de Diego para que el abogado no vea sus chats y proyectos?

Respuesta de Claude (verificado en support.claude.com el 26 de Noviembre). En la documentación no aparece una función de perfiles dentro de una cuenta personal (supuesto que no existe, no se encontró). La ayuda dice que los planes de suscripción solo los pueden usar sus suscriptores, y en el plan Team cada asiento es solo de la persona asignada, sin compartir la clave ni dejar que otro use la cuenta. Por eso no corresponde que el abogado use la cuenta de Diego con otro perfil. Caminos que sí calzan. Que el abogado (o la oficina) tenga su propia cuenta pagada, porque Claude in Chrome pide plan pagado. O un plan Team con dos asientos, uno para Diego y otro para el abogado, cada uno con su cuenta separada. Team pide mínimo dos miembros, y quien ya tiene cuenta personal puede tener las dos y cambiar entre ellas.

## 9m. Ideas de Diego para la versión final y plan de validación (26 de Noviembre, 14.35)

Ideas de Diego. 1) Que Claude tome solo el informe desde Gmail, aunque el PC esté apagado, y que al prender el PC el abogado solo dé la orden. El correo que recibe el informe también lo usa Diego. 2) Usar las tareas programadas de Claude, sabiendo que el abogado deja el PC apagado, y resolver cómo se dispara al prenderlo. 3) Antes de comprar el plan Team (Diego vio USD 20 por puesto al mes con pago anual y USD 25 con pago mensual, mínimo dos puestos), dejar todo funcionando y validado al 100% en el PC de Diego.

Lo verificado en la documentación de Anthropic (26 de Noviembre).
Gmail. La página actual de conectores de Google dice que Claude puede abrir adjuntos de hasta unos 12 MB (en el chat necesita la ejecución de código activada). Otra versión de la misma página dice que solo ve los datos del adjunto y no su contenido. Hay contradicción, así que se prueba antes de contar con eso. El conector de Gmail lee y busca, y según claude.com no envía correos.
Tareas programadas. Las de Cowork corren en la nube aunque el PC esté apagado y usan los conectores. Cuando necesitan el navegador o archivos del PC, llegan a él por la app de escritorio, y si la app está desconectada no lo alcanzan. Sobre una tarea que pierde su hora hay versiones distintas. La guía de Claude Academy dice que Cowork la corre apenas se vuelve. La guía vieja de Claude Code Desktop dice que se salta. Se prueba.
Conector de Gmail. Está instalado en la cuenta de Diego pero no conectado (verificado en el registro de conectores).

Diseño propuesto, sin decidir. Una tarea en la nube lee temprano el correo del día con el Excel (PC apagado). Cuando el PC está prendido con Chrome y la app de Claude abiertos, Claude recorre las causas de la tabla principal en Chrome, lee la deuda con las reglas fijadas y deja una copia del Excel con las columnas Deuda UF, Deuda CLP y una observación. El disparo al prender el PC se resuelve con lo que muestre la prueba (corre sola al volver, o el abogado aprieta "ejecutar" o escribe una frase).

Plan de validación en el PC de Diego, propuesto. V1 armar el flujo completo una vez con el Excel del día. V2 probar el disparo con el PC apagado a la hora de la tarea. V3 piloto de 5 días hábiles. Criterios de aprobado propuestos para fijar antes de V3. Los 5 días terminan. Cada causa de la principal tiene Deuda o una observación que dice por qué no. Diego compara a mano 5 causas por día con el PDF y no aparece ningún monto equivocado. Los CAPTCHA se anotan y no pasan de 1 en los 5 días. El trabajo diario no pasa de 30 minutos. No se guardan RUT, teléfonos ni correos.

## 9n. Puente Gmail probado (26 de Noviembre, 14.50, verificado)

Diego conectó la Gmail del robot (la que recibe el informe junto al abogado) al conector Gmail de Claude. Claude buscó el correo "Remates El Mercurio, jueves 26 de noviembre del 2026" (enviado a las 5.07), leyó su texto ("Trae 13 causa(s) nueva(s)") y bajó el adjunto "Reporte 26 de noviembre del 2026.xlsx" con la herramienta download_gmail_attachment. 10.846 bytes, igual que informes/ en Supabase. Abre bien y trae 13 causas en la tabla principal. Copia en INFORMES_REPORTES ("Reporte 26 de noviembre del 2026 (desde Gmail).xlsx", sha256 703134b8...). No hace falta el puente con Supabase.

Corrección de 9m. Ahí se anotó que el conector de Gmail no envía correos (según claude.com). El conector conectado hoy pidió permisos para leer, redactar y enviar, y trae herramientas para crear borradores y enviar. Nota de Claude, en una tarea programada sin nadie mirando, Claude no envía correos a nombre de nadie sin una aprobación en el momento, así que la salida más segura es un borrador en Gmail o un archivo, y el envío lo hace una persona.

Orden de Diego para la versión final (26 de Noviembre, 14.44). PC apagado, GitHub corre el robot, el informe llega al correo, una tarea de Claude toma el informe y queda en pausa. PC prendido, el abogado entra a la app de Claude, escribe o hace algo y parte todo. Plan de Diego, hoy con su PC prendido y mañana 27 de Noviembre con el PC apagado para ver cómo se procede al prenderlo.

## 10. Correcciones

(Ninguna todavía.)

Al 26 de Noviembre, 15.40, la línea de arriba quedó vieja (se conserva). Correcciones anotadas en su sección. 9d a 9f, el nombre de la columna pasa de "deuda/mandamiento" a "Deuda". 9e a 9g, era impreciso decir que un navegador en un servidor es lo que el WAF bloqueaba en Julio. 9h a 9j, el script de la prueba en la nube clasificó como NO_LLEGA_AL_FORMULARIO un bloqueo real, porque sus firmas de bloqueo estaban solo en inglés. 9m a 9n, el conector de Gmail conectado sí puede redactar y enviar, no solo leer. Sección 6, la elección de C-610-2025 como ejecutivo resultó falsa (era Ley de Bancos).

## 11. Reglas para llegar a la deuda (lo aprendido al 26 de Noviembre, se corrige abajo si cambia)

Navegación (verificado con 4 causas en el Chrome de Diego, n=4).
1. Chrome real de Diego con la extensión Claude in Chrome, ventana visible y sin minimizar (minimizada, la extensión no saca capturas).
2. Antes de cada causa, recargar desde home/index.php. Cerrar el aviso semanal con "Cerrar", entrar a "Consulta causas" como Invitado.
3. Búsqueda por RIT. Competencia Civil, Corte por su value (C.A. de Santiago 90, C.A. de Valparaíso 30, C.A. de San Miguel 91), tribunal por su texto o value (los textos usan º con o volada, por ejemplo "30º Juzgado Civil de Santiago" value 288, "3º" value 261), libro C, rol y año. Pausas de 1 a 3 segundos entre pasos.
4. Abrir solo la fila con el rol y el año exactos. No abrir la pestaña Litigantes (trae RUT).
5. Leer "Proc." en el encabezado del detalle.
6. Los enlaces a documentos vencen. Una sesión quieta 2 horas devuelve una página en blanco al abrir un PDF. Si pasa, recargar desde la portada.
7. Ante cualquier CAPTCHA o la página "La URL solicitada ha sido rechazada" / "The requested URL was rejected", detenerse y avisar. No reintentar.

Documento según el procedimiento (regla vieja de 8edd5ee^ más lo aprendido).
| Procedimiento | Cuaderno | Documento | Qué número va a Deuda |
|---|---|---|---|
| Ejecutivo Obligación de Dar | 2 Apremio Ejecutivo Obligación de Dar (Claude lo cambia solo con el selector) | Folio con etapa Mandamiento y trámite Mandamiento, buscando desde los folios bajos (en las 2 causas fue el folio 1) | La suma que manda pagar el mandamiento, en la moneda en que viene |
| Desposeimiento | Apremio | Mandamiento | Igual que el ejecutivo (sin caso medido todavía) |
| Ley de Bancos | 1 Principal (no hay Apremio ni mandamiento) | El escrito más reciente que traiga la liquidación del crédito ("Presenta bases corregidas", "Propone nueva liquidación", "Solicita liquidación"). Si no hay, "Propone bases de remate" | La liquidación del crédito (es deuda). El mínimo de las bases no es deuda, se anota solo en la observación si sirve |
| Otros (ordinarios, liquidación concursal, partición, arbitral, mínima cuantía) | Ninguno | Ninguno | Celda vacía y la observación dice el procedimiento |

Columnas de salida (decisión de Diego). Deuda UF y Deuda CLP. Si el documento trae una sola moneda, la otra queda en blanco y no se convierte. Una columna de observación con el documento usado (folio, fecha, nombre del trámite) o por qué no hay deuda.

Lectura del monto. El lector viejo de modulo3_extractor.py sirve de base, con dos correcciones conocidas. Aceptar "U.F." antes del número (falló en C-8703-2020). Incluir "precio mínimo para comenzar las posturas" y "liquidación... la suma de ... Unidades de Fomento" para Ley de Bancos. Los PDF vistos traen texto, ninguno escaneado (n=6).

No se guarda. RUT, nombres o domicilios de demandados, teléfonos ni correos que salen en los documentos.

## 12. Plan de V1 y V2 (fijado el 26 de Noviembre, 15.40, para el chat siguiente)

V1, flujo completo con el PC de Diego prendido y Diego presente. Entrada, el Excel del día bajado de la Gmail del robot con el conector Gmail (búsqueda subject:"Remates El Mercurio" has:attachment del día, herramienta download_gmail_attachment). Recorrer en Chrome todas las causas de la tabla principal con las reglas de la sección 11 (o primero 5, a decisión de Diego). Salida, una copia del Excel con las columnas Deuda UF, Deuda CLP y Observación deuda, en D:\Mercurio\INFORMES_REPORTES, y además como borrador en la Gmail del robot si Diego lo aprueba (no se envía nada sin su aprobación en el momento). Medir por causa la hora, el tiempo, si apareció CAPTCHA o F5 y el documento usado. Anotar todo aquí. Es la primera vez con más de 4 causas seguidas, que es el dato que falta.

V2, el disparo con el PC apagado (pedido por Diego para el 27 de Noviembre). Una tarea programada de una sola vez, temprano (propuesta 6.30), que solo haga la parte de Gmail (bajar el Excel del día y armar la lista de causas) y termine con un mensaje que diga cuántas causas hay y que, al prender el PC con Chrome y Claude abiertos, se responda "sigue" en esa misma conversación. Diego prende el PC, entra a esa tarea y responde. Se mide si la tarea corrió con el PC apagado, si al responder la sesión alcanza el Chrome de Diego y qué tuvo que hacer Diego. La tarea no se crea sin el visto bueno de Diego.

Criterios de aprobado propuestos para V3 (piloto de 5 días hábiles), a confirmar por Diego antes de partir. Los 5 días terminan. Cada causa de la principal tiene Deuda o una observación que dice por qué no. Diego compara a mano 5 causas por día con el PDF y no aparece ningún monto equivocado. No más de 1 CAPTCHA en los 5 días. No más de 30 minutos de trabajo diario. Nada de RUT, teléfonos ni correos guardados.

Después de V3. Decidir entre A (PC de Diego) y D (PC del abogado con su propia cuenta, plan Team de dos puestos o cuenta pagada de la oficina) y la forma de entrega (Excel completo, borrador o segundo correo).

## 13. Estado al cierre del chat del 25 y 26 de Noviembre (15.40, verificado)

main y origin/main en 0cf5aa7 (bitácora hasta la sección 9e). Esta bitácora tiene sin commit las secciones 9f a 13. Exploracion_PJUD/prueba_nube (script y flujo de la prueba en la nube) sin seguimiento en main. Rama prueba-ojv-nube en GitHub en 1f7f084 con la prueba. Worktree D:\Mercurio_prueba_ojv en esa rama (desde la terminal Linux aparece como prunable porque no ve D:, desde Windows está bien). Resultados de la prueba en la nube en INFORMES_REPORTES\prueba_ojv_nube. Excel del 25 y del 26 de Noviembre en INFORMES_REPORTES. Conector Gmail conectado a la Gmail del robot en la cuenta de Claude de Diego. Supabase con la corrida del 26 de Noviembre a las 5.07 (informe, captura y enviado). El robot no se tocó en toda la fase.


