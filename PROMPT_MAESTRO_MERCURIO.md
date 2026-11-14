# Prompt Maestro. Extractor El Mercurio Digital (RM)
# Versión 4.7 (14 de Noviembre de 2026). Versión 4.0 aprobada por Diego el 21 de Octubre de 2026

> Uno de los dos documentos base del proyecto. Este dice cómo funciona el programa y sus reglas, y cambia poco. ESTADO_PROYECTO.md (en D:\Mercurio, fuera de git) dice en qué estamos, las decisiones y los pendientes. Reemplaza a PROMPT_MAESTRO_MERCURIO_v3_1.md (de Julio, borrado el 6 de Noviembre de 2026 con el resto de documentos/historia, queda en el historial de git). La experiencia para mejorar la lectura de dirección y carátula está en Mejora_continua/GUIA_MEJORA_LECTURA.md. Todo proceso de mejora continua (Kaizen) se anota tanda por tanda en Mejora_continua/HISTORIAL_TANDAS.md, al publicar y al revisar su corrida real. Ante cualquier diferencia con el código, el árbitro es el código.

## Qué es

Programa que lee los avisos de remates judiciales de propiedades de El Mercurio Digital (Clasificados, sección 1616) y entrega un Excel al abogado. Lee el texto del visor PDF del diario (textLayer en modo HD), sin imágenes. La IA es Claude Haiku y solo lee la dirección y la comuna, con la frase exacta comprobada por código. DeepSeek salió del programa el 17 de Octubre.

Desde el 19 de Octubre corre solo en un servidor de GitHub Actions todos los días y le manda el Excel por correo al abogado. Su PC (E:\Mercurio) ya no corre el programa.

## Dónde vive cada cosa

| Pieza | Dónde | Notas |
|---|---|---|
| Código | GitHub DFNR2026/RematesMercurio (público), rama main | Copia de trabajo en D:\Mercurio |
| Servidor | GitHub Actions, flujo .github/workflows/diario.yml | ubuntu-24.04, Python 3.14 |
| Historial causas_ojv.xlsx | Supabase, proyecto mercurio-robot, bucket privado mercurio, estado/causas_ojv.xlsx | La copia viva. La de D: quedó como respaldo del 18 de Octubre y no se debe correr el programa en el PC |
| Respuestas guardadas de Haiku | Supabase, estado/ia_respuestas.zip | Caché por huella. Si se pierde, solo cuesta un poco más. Si llega dañado, la corrida lo guarda en respaldos/ia_respuestas_danado_FECHA.zip y sigue sin él (desde el 13 de Noviembre) |
| Respaldos diarios del historial | Supabase, respaldos/causas_ojv_antes_FECHA.xlsx | Uno por día con Excel |
| Excel de cada día | Supabase, informes/ | Copia por si se pierde un correo |
| Captura de cada día | Supabase, capturas/FECHA.zip | Texto de las páginas de remates que leyó el lector, su navegacion.json y la salida de main.py. Permite rehacer cualquier día en el PC sin el diario (desde el 1 de Noviembre de 2026). Desde el 13 de Noviembre trae también las respuestas de Haiku de los avisos de ese día, así el día se rehace solo con este archivo |
| Marcas del día | Supabase, enviados/, intentos/, avisos/ | Evitan correos repetidos y llevan el número de intentos |
| Claves | Secretos de GitHub (9) | MERCURIO_USER, MERCURIO_PASS, ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, GMAIL_USER, GMAIL_APP_PASSWORD, CORREO_ABOGADO, CORREO_DIEGO |
| Correo | Gmail personal nueva del robot, con contraseña de aplicación | CORREO_DIEGO es la misma cuenta del robot (decisión de Diego) |

config.py sigue fuera de git. En el servidor se arma en cada corrida desde config_template.py, con líneas que leen las claves de los secretos.

## Corrida diaria (servidor/diario.py)

Intenta cada 20 minutos de 5:03 a 7:05 de Chile, 7 intentos. El despertador principal es cron-job.org, que llama a la API de GitHub (workflow_dispatch) con modo=real y origen=automatico, con la zona America/Santiago. El horario propio de GitHub queda de respaldo, porque desde Agosto de 2026 GitHub atrasa o no dispara los horarios (comprobado el 19 de Octubre). La llave de GitHub vive solo en cron-job.org. GitHub programa en hora universal, por eso el flujo tiene horarios que cubren las dos horas de Chile y su primer paso salta lo que cae fuera de 5:00 a 7:10.

Último intento. Las corridas de cron-job.org y del horario de GitHub dejan INTENTO_FINAL vacío y diario.py decide por la hora (es el último intento desde las 7:00). Las corridas a mano con el botón son último intento forzado. Hasta el 21 de Octubre las de cron-job.org quedaban como último intento por un error de la expresión de GitHub (a && '' || '1' da '1'), arreglado en 145cd2d.

1. Si hoy ya se envió, no hace nada. Si el Excel quedó guardado pero el correo no salió, lo reenvía.
2. Baja de Supabase el historial y las respuestas de Haiku.
3. Corre main.py --fecha HOY, el mismo programa que corría en el PC.
4. Según el código de salida de main.py.

| Código | Qué pasó | Qué hace el robot |
|---|---|---|
| 0 con Excel | Bien | Respalda el historial viejo, sube el nuevo, las respuestas y el Excel. Correo con el Excel al abogado y a Diego |
| 4 con Excel | Excel que puede estar incompleto | Igual que el 0, con el asunto "Puede estar incompleto" |
| 0 sin Excel | No hubo causas nuevas (puede haber ya informadas) | Sube las respuestas, y el historial si cambió. Correo "Sin causas nuevas" |
| 2 | La edición aún no está publicada | Reintenta |
| 3 | No pudo leer el diario | Reintenta. No sube el historial |
| 1 | Error inesperado | Reintenta. No sube el historial |
| 4 sin Excel | Sin causas nuevas pero faltó leer algo | Reintenta. En el último intento avisa al abogado que puede faltar algo y a Diego con detalle |

Desde las 6:00, una sola vez, avisa al abogado y a Diego que todavía no hay informe y que el último intento es a las 7:05. A las 7:05 avisa cuántos intentos se hicieron y que no se intenta más. A Diego le llega además el detalle con las últimas líneas del programa y el enlace a la corrida.

A mano (Run workflow) corre por defecto en modo ensayo. El correo va solo a CORREO_DIEGO y todo se guarda en pruebas/ensayo/, sin tocar estado/. Con modo real y una fecha, rehace un día.

## Lectura (modulo1_mercurio.py y motor/)

Motor traído de Agendar_Remates el 17 de Octubre (etapas A a F del traspaso).

1. motor/lector_mercurio.py. Entra al diario con la cuenta del Mercurio, activa el modo HD (canvas de más de 1800 de ancho) con la primera página del cuerpo A, lista todos los cuerpos del día y lee el texto de cada página. No lee los cuerpos A, E, R y T (decisión de Diego del 18 de Octubre, 0 remates en 11 ediciones guardadas). Los remates han salido en B (días hábiles), C, D (sábados), F (domingos) y G (viernes).
2. motor/navegacion_logica.py. Elige las páginas con la cornisa "1616 Remates de propiedades", las encadena y sigue las flechas "MÁS AVISOS... EN PÁG.". Una flecha hacia un cuerpo que no se lee levanta una alarma clara.
3. motor/edicion.py, cortador.py, orden_columnas.py, extraccion.py, partidor.py, direccion.py. Une las páginas en un solo rollo, ordena las columnas por posición, corta por aviso con código, elimina los remates de partidor, extrae tribunal, inscripción y carátula por código, y pide a Haiku solo la dirección y la comuna, con dos lecturas y cita exacta verificada. La cita perdona solo espacios y la diferencia entre comillas rectas y curvas. Cuando las dos lecturas difieren solo en un número de acceso de más o en una unidad que una no trae, el código se queda con la parte común comprobada (ciclo 2 de mejora, 8 de Noviembre, detalle en Mejora_continua/GUIA_MEJORA_LECTURA.md). Desde la tanda 3 del ciclo 2 (10 de Noviembre) la inscripción se lee también cuando el aviso escribe "Fs.", "fs", "fjs" o "f." en vez de fojas, "números" en plural o la letra F junto a las fojas, y la carátula se lee en más formas (después de "expediente", con barra antes del rol, con la comilla sin cerrar y con tres errores de tipeo del diario). Desde la tanda 4 del ciclo 2 (11 de Noviembre), cuando la dirección queda en rojo se conserva la comuna si las dos lecturas dan la misma y cada una se comprueba en el aviso, sin dar nunca la dirección. Así el filtro de la RM puede descartar un inmueble de otra región que antes entraba a la principal por la comuna vacía. También queda la calle común cuando una lectura agrega la esquina y la otra no, y un número en palabras pegado a una coma o un punto se lee completo. Desde la tanda 5 (12 de Noviembre), cuando el diario imprime el ° como un 3 suelto, "2 3 JUZGADO" se lee como el 2° Juzgado (si justo antes del 3 hay un número de una o dos cifras) y la inscripción "N 3 22232" se lee como el número 22232 (solo si después del 3 viene otro número). Desde la tanda 6 (14 de Noviembre), si el comienzo del aviso no trae tribunal, se lee el que va justo después del rol ("causa C-6458-2022 seguida ante el 13° Juzgado Civil de Santiago"), solo si todas esas frases nombran el mismo. La inscripción se lee también con un punto entre el número de fojas y "Número". Cuando la sección de remates sigue en otro cuerpo sin la flecha y un aviso queda cortado entre los dos, los dos bloques se leen como uno, y un aviso que un tercer bloque reimprime ya no se carga dos veces. La causa voluntaria (rol con letra V) se elimina antes de la IA, como el partidor. El tipo que da Haiku (calle o sin calle) y la frase comprobada llegan hasta el filtro.
4. motor/conjunto.py. Si la dirección quedó comprobada, el aviso trae un remate y dice condominio o edificio, arma la celda Dirección con el tipo y nombre del condominio o edificio, la dirección, la calle interior, los estacionamientos y bodegas, y la entrada si es otra calle. Solo código, sin IA (desde el 9 de Noviembre). Desde la tanda 4 (11 de Noviembre) un nombre de edificio de 3 o 4 letras (ONIX, Fam, Novo) ya no se toma como subdivisión, que queda para una o dos letras o un código con número (B, AB, B2, A-1), y el nombre puede empezar con "de", "del" o "la" (Edificio de La Recoleta Urbano).
5. motor/filtros.py. Reglas de negocio y tablas del Excel.

## Reglas de negocio vigentes

Solo RM por comuna de la propiedad. Desde la tanda 6 (14 de Noviembre) la comuna de la propiedad manda sobre la Corte del tribunal. Un remate de un juzgado de otra región entra si alguna propiedad trae una comuna de la RM, con la Observación de otra región, y la Corte decide solo cuando no hay comuna. Los juzgados 2° y 3° de Antofagasta encuentran su Corte. No BancoEstado (mira la carátula entera, y si la carátula no se pudo leer, busca el nombre del banco en el aviso fuera de las frases de pago, desde el 10 de Noviembre). No Estación Central. Año del rol desde 2018. Dominio CBR anterior a 2019, con el año de la inscripción que lee el código. El corte era 2020 hasta el 11 de Noviembre de 2026 y pasó a 2019 por pedido de los abogados que usan el Excel, porque con dominio inscrito en 2019 la deuda queda muy cerca del valor comercial (filtro_cbr.py, _CBR_ANIO_CORTE). Los títulos del Excel y la Observación del año dicen 2019. Año vacío va a REVISAR. Un rol con más de 5 propiedades no pasa por el filtro CBR y entra si al menos una está en la RM. Con 5 o menos, cada propiedad se filtra y el rol se descarta solo si todas fallan. Una fila por rol. Los avisos sin rol y de año ilegible van en su propia tabla. Los partidores no aparecen en ninguna tabla. Desde la tanda 6 tampoco las causas voluntarias (rol con letra V) ni las causas cuyas propiedades en verde son todas terrenos sin calle (decisión de Diego del 13 de Noviembre), salvo que la frase del terreno diga casa o vivienda. No se anotan en la memoria. Las causas cuyas propiedades en verde son todas oficinas, sitios sin casa o terrenos con calle van a una tabla aparte al final del Excel, solo por si acaso, sin pasar por los demás filtros ni anotarse en la memoria. "Lote" no se usa para filtrar. Una causa que trae además una casa o un departamento sigue con esa propiedad y una Observación. Se juzga por causa (rol, año y tribunal), así que dos causas de un mismo aviso van cada una por su lado.

Regla de los 4 días (decisión de Diego del 20 de Octubre). Un remate que no se hace y se vuelve a pedir tarda como mínimo 2 meses en reaparecer en el diario. Una causa que salió en alguno de los 4 días anteriores a la edición (el día anterior y 3 más atrás, como un trencito) es el mismo aviso republicado y va a la tabla "Ya informadas en los últimos 4 días", con la frase "Este aviso ha salido en El Mercurio los días ...". Si salió hace más de 4 días entra como nueva y pasa por los filtros, porque es un nuevo intento de remate. Un día con solo causas repetidas no genera Excel y manda el correo "Sin causas nuevas".

Memoria (hoja CAUSAS). Se anota una fila por causa y por edición en que salió, con la fecha de la edición, tanto para las de la tabla principal como para las ya informadas. Las causas con observaciones (para revisar) también se anotan, porque existen y salieron en el diario (decisión de Diego del 20 de Octubre, reemplaza la regla del 17 de Octubre que no las anotaba). Las excluidas, las descartadas y los avisos sin rol no se anotan. Una fila sin fecha se trata como informada hace más de 4 días, así la causa nunca queda escondida.

## Excel (modulo5_reporte.py)

Nombre "Reporte 19 de octubre del 2026.xlsx", con " INCOMPLETO" si faltó algo. Primera hoja, llamada "Remates", con la tabla principal (ROL, Año, Corte, Tribunal, Demandante, Demandado, Dirección, Comuna, Fs., Observaciones), luego sin rol, ya informadas en los últimos 4 días (Tribunal, ROL, Año, Dirección, Publicado en El Mercurio), excluidas por dominio y descartadas, y al final, solo si hay alguna, la tabla "Oficinas, sitios y terrenos (aparte, solo por si acaso)" con tribunal, rol, año, dirección, comuna y motivo (desde la tanda 6). Hoja Resumen al final, con recuadro rojo si está incompleto y un "QUÉ HACER" para el abogado (PASOS_SI_FALLA) que le dice que no tiene que ejecutar nada y que puede revisar El Mercurio, Clasificados, sección 1616. Fechas con el mes en palabras.

## Reglas inamovibles

- No reintroducir el acceso automatizado al PJUD u OJV sin decisión explícita de Diego (WAF F5/Shape).
- No hay tasación automatizada.
- Claves solo en config.py o en los secretos de GitHub. Nunca en git ni en el chat. Nunca imprimir una clave.
- Canvas HD obligatorio. RapidFuzz con umbral 80. region_rm siempre True.
- Un dato que no se pudo leer va a REVISAR y nunca excluye una causa en silencio. La causa en REVISAR sí se anota en la memoria.
- La memoria solo agrega filas. Nunca se borran ni se cambian filas de la hoja CAUSAS.
- Llave de dedup siempre rol-año más tribunal con _clave_causa() (motor/clave.py). Prohibido volver a rol-año a secas.
- No borrar ni renombrar causas_ojv.xlsx ni modificar su hoja REFERENCIA.
- El repositorio de GitHub queda con permiso de solo lectura para los flujos. La memoria se escribe en Supabase, no en git.

## Git y GitHub

- El código lo escribe Claude directo en D:\Mercurio con el PC de Diego vinculado, primero en una copia de prueba. Cline no se usa.
- Todo lo que toque GitHub (commit, push, revisar corridas) lo hace Claude Code en el PC de Diego, con un texto que Claude prepara y que termina en un reporte .md en D:\Mercurio\Reportes_Claude_Code. Nunca desde el chat ni desde PowerShell.
- Un cambio nuevo por noche. No se publica otro cambio de código hasta que el anterior pasó su primera corrida real de las 5:03. Desde el 8 de Noviembre, por decisión de Diego, los arreglos de la lectura pueden ir en tandas. Cada arreglo se mide por separado en una copia contra todas las capturas guardadas, la tanda se publica junta y no se publica otra hasta que la anterior pasó su primera corrida real.
- git status --short antes de cada commit. Agregar archivo por archivo. Prohibido git add ., git add -A, git commit -am, git reset --hard, git clean y git pull fuera del guion.
- Push solo con el "apruebo push" de Diego. Pegar el texto en Claude Code cuenta como aprobación.
- Un commit es una sola historia. Las cifras esperadas se fijan antes de correr.
- INFORMES_REPORTES es una carpeta de paso, fuera de git (desde el 13 de Noviembre). Para revisar un día, Diego baja ahí su log de GitHub, su Excel y su captura de Supabase, en una carpeta con la fecha, y después lo puede borrar.

## Pruebas manuales en GitHub

| Flujo | Qué hace |
|---|---|
| prueba_entrada.yml | Lectura en modo de prueba, sin Haiku ni historial |
| prueba_supabase.yml | Baja y revisa estado/, sube una copia a pruebas/ |
| prueba_correo.yml | Manda pruebas/Reporte 18 de octubre del 2026.xlsx solo a CORREO_DIEGO |
| diario.yml (a mano) | Corrida completa en modo ensayo o real |

## Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 3.1 | 5 de Julio de 2026 | DeepSeek, lectura vieja, llave de dedup con tribunal, despliegue en E:\Mercurio |
| 4.7 | 14 de Noviembre de 2026 | Ciclo 2 de mejora de la lectura, tanda 6. Causas voluntarias eliminadas, fojas con punto, Solo RM por la comuna de la propiedad, Corte de Antofagasta, bloques de remates que continúan en otro cuerpo, tribunal nombrado después del rol, terrenos sin calle eliminados y tabla aparte de oficinas, sitios y terrenos (motor/edicion.py, extraccion.py, direccion.py, filtros.py, modulo1_mercurio.py y modulo5_reporte.py) |
| 4.6 | 13 de Noviembre de 2026 | Respaldo de las respuestas de Haiku. La captura del día trae las respuestas de sus avisos y la corrida sigue si el archivo de respuestas llega dañado (servidor/diario.py) |
| 4.5 | 12 de Noviembre de 2026 | Ciclo 2 de mejora de la lectura, tanda 5. El ° impreso como un 3 suelto en el tribunal y en la inscripción (motor/extraccion.py) |
| 4.4 | 11 de Noviembre de 2026 | Ciclo 2 de mejora de la lectura, tanda 4. Comuna comprobada con la dirección en rojo, esquina de más en una lectura y número en palabras pegado a una coma (motor/direccion.py, edicion.py y numeros_texto.py), nombres de edificio (motor/conjunto.py). Corte del dominio de 2020 a 2019 por pedido de los abogados (filtro_cbr.py, motor/filtros.py y modulo5_reporte.py) |
| 4.3 | 10 de Noviembre de 2026 | Ciclo 2 de mejora de la lectura, tanda 3. Carátulas y fojas (motor/extraccion.py) y BancoEstado en el aviso cuando la carátula queda vacía (motor/filtros.py). Logs_GitHub y Storage_supabase pasan a D:\Mercurio\INFORMES_REPORTES |
| 4.2 | 9 de Noviembre de 2026 | Ciclo 2 de mejora de la lectura, tanda 2. Formato de condominios y edificios en la columna Dirección (motor/conjunto.py) |
| 4.1 | 8 de Noviembre de 2026 | Ciclo 2 de mejora de la lectura, tanda 1 (orden de columnas, comillas, unión de lecturas, unidad con letra o con punto de miles, calle sin número, lista de mínimos). Publicación por tandas |
| 4.0 | 19 al 21 de Octubre de 2026 (borrador) | Motor de Agendar_Remates con Haiku (commits 7996493 a bd67a06). Cuerpos A, E, R y T sin lectura (59fd135). Servidor en GitHub Actions con Supabase y Gmail (add4b51 a f8c49eb). cron-job.org como despertador (802fab7). Regla de los 4 días (739e00c) y causas para revisar anotadas en la memoria (2a6100b). Último intento arreglado en las corridas automáticas (145cd2d) |
