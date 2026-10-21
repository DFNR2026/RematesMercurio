# Prompt Maestro. Extractor El Mercurio Digital (RM)
# Versión 4.0, aprobada por Diego el 21 de Octubre de 2026

> Reemplaza a PROMPT_MAESTRO_MERCURIO_v3_1.md (de Julio, ahora en documentos/historia). Ante cualquier diferencia con el código, el árbitro es el código.

## Qué es

Programa que lee los avisos de remates judiciales de propiedades de El Mercurio Digital (Clasificados, sección 1616) y entrega un Excel al abogado. Lee el texto del visor PDF del diario (textLayer en modo HD), sin imágenes. La IA es Claude Haiku y solo lee la dirección y la comuna, con la frase exacta comprobada por código. DeepSeek salió del programa el 17 de Octubre.

Desde el 19 de Octubre corre solo en un servidor de GitHub Actions todos los días y le manda el Excel por correo al abogado. Su PC (E:\Mercurio) ya no corre el programa.

## Dónde vive cada cosa

| Pieza | Dónde | Notas |
|---|---|---|
| Código | GitHub DFNR2026/RematesMercurio (público), rama main | Copia de trabajo en D:\Mercurio |
| Servidor | GitHub Actions, flujo .github/workflows/diario.yml | ubuntu-24.04, Python 3.14 |
| Historial causas_ojv.xlsx | Supabase, proyecto mercurio-robot, bucket privado mercurio, estado/causas_ojv.xlsx | La copia viva. La de D: quedó como respaldo del 18 de Octubre y no se debe correr el programa en el PC |
| Respuestas guardadas de Haiku | Supabase, estado/ia_respuestas.zip | Caché por huella. Si se pierde, solo cuesta un poco más |
| Respaldos diarios del historial | Supabase, respaldos/causas_ojv_antes_FECHA.xlsx | Uno por día con Excel |
| Excel de cada día | Supabase, informes/ | Copia por si se pierde un correo |
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
3. motor/edicion.py, cortador.py, orden_columnas.py, extraccion.py, partidor.py, direccion.py. Une las páginas en un solo rollo, ordena las columnas por posición, corta por aviso con código, elimina los remates de partidor, extrae tribunal, inscripción y carátula por código, y pide a Haiku solo la dirección y la comuna, con dos lecturas y cita exacta verificada.
4. motor/filtros.py. Reglas de negocio y tablas del Excel.

## Reglas de negocio vigentes

Solo RM por comuna de la propiedad. No BancoEstado (mira la carátula entera). No Estación Central. Año del rol desde 2018. Dominio CBR anterior a 2020, con el año de la inscripción que lee el código. Año vacío va a REVISAR. Un rol con más de 5 propiedades no pasa por el filtro CBR y entra si al menos una está en la RM. Con 5 o menos, cada propiedad se filtra y el rol se descarta solo si todas fallan. Una fila por rol. Los avisos sin rol y de año ilegible van en su propia tabla. Los partidores no aparecen en ninguna tabla.

Regla de los 4 días (decisión de Diego del 20 de Octubre). Un remate que no se hace y se vuelve a pedir tarda como mínimo 2 meses en reaparecer en el diario. Una causa que salió en alguno de los 4 días anteriores a la edición (el día anterior y 3 más atrás, como un trencito) es el mismo aviso republicado y va a la tabla "Ya informadas en los últimos 4 días", con la frase "Este aviso ha salido en El Mercurio los días ...". Si salió hace más de 4 días entra como nueva y pasa por los filtros, porque es un nuevo intento de remate. Un día con solo causas repetidas no genera Excel y manda el correo "Sin causas nuevas".

Memoria (hoja CAUSAS). Se anota una fila por causa y por edición en que salió, con la fecha de la edición, tanto para las de la tabla principal como para las ya informadas. Las causas con observaciones (para revisar) también se anotan, porque existen y salieron en el diario (decisión de Diego del 20 de Octubre, reemplaza la regla del 17 de Octubre que no las anotaba). Las excluidas, las descartadas y los avisos sin rol no se anotan. Una fila sin fecha se trata como informada hace más de 4 días, así la causa nunca queda escondida.

## Excel (modulo5_reporte.py)

Nombre "Reporte 19 de octubre del 2026.xlsx", con " INCOMPLETO" si faltó algo. Primera hoja con la tabla principal (ROL, Año, Corte, Tribunal, Demandante, Demandado, Dirección, Comuna, Fs., Observaciones), luego sin rol, ya informadas en los últimos 4 días (Tribunal, ROL, Año, Dirección, Publicado en El Mercurio), excluidas por dominio y descartadas. La hoja se llama todavía "Regiones" por un nombre heredado, pendiente cambiarlo a "Remates". Hoja Resumen al final, con recuadro rojo si está incompleto. Fechas con el mes en palabras.

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
- Todo lo que toque GitHub (commit, push, revisar corridas) lo hace Claude Code en el PC de Diego, con un texto que Claude prepara y que termina en un reporte .md en D:\Mercurio\MD_Cline. Nunca desde el chat ni desde PowerShell.
- Un cambio nuevo por noche. No se publica otro cambio de código hasta que el anterior pasó su primera corrida real de las 5:03.
- git status --short antes de cada commit. Agregar archivo por archivo. Prohibido git add ., git add -A, git commit -am, git reset --hard, git clean y git pull fuera del guion.
- Push solo con el "apruebo push" de Diego. Pegar el texto en Claude Code cuenta como aprobación.
- Un commit es una sola historia. Las cifras esperadas se fijan antes de correr.
- Los logs de cada corrida se descargan a D:\Mercurio\Testeo_GitHub para auditarlos desde el disco.

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
| 4.0 | 19 al 21 de Octubre de 2026 (borrador) | Motor de Agendar_Remates con Haiku (commits 7996493 a bd67a06). Cuerpos A, E, R y T sin lectura (59fd135). Servidor en GitHub Actions con Supabase y Gmail (add4b51 a f8c49eb). cron-job.org como despertador (802fab7). Regla de los 4 días (739e00c) y causas para revisar anotadas en la memoria (2a6100b). Último intento arreglado en las corridas automáticas (145cd2d) |
