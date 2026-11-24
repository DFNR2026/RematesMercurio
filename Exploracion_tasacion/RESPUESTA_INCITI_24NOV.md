# Respuesta de inciti al ticket (24 de Noviembre de 2026) y evaluación

## Lo que respondió inciti

Dos servicios de búsqueda que no aparecen en el manual público de la API (el 14 de Noviembre el código de la página nombraba solo 5 servicios).

- POST https://api.inciti.com/api/searchengine/get_results_by_rol con comunaCode y rol.
- POST https://api.inciti.com/api/searchengine/get_results_by_address con street, streetNumber, comunaCode y unitNumber.

El final del ejemplo llegó roto por los enlaces automáticos de Gmail. Lo más probable es que el cuerpo sea {"street": "Calle Ejemplo", "streetNumber": "1234", "comunaCode": "15160", "unitNumber": "501"} (supuesto).

## Lo verificado

- El código de comuna es el del SII. 15160 es Vitacura en la tabla de comunas del SII (Defontana, Conara SII).
- En la RM hay 54 códigos del SII para 52 comunas. Santiago tiene tres (13101 Santiago, 13134 Santiago Oeste y 13135 Santiago Sur).
- El robot ya separa cada dirección en calle, número, unidad y comuna (motor/direccion.py, respuesta de Haiku). No hace falta leer nada nuevo del aviso.
- Medido en las 341 respuestas de Haiku guardadas en ia_respuestas/direccion (14 al 17 de Octubre). 356 inmuebles. 291 con tipo calle y las dos lecturas iguales, 271 de ellos en la RM. De esos 271, 257 (95%) tienen número simple y, si hay unidad, unidad con número, así que se puede armar la consulta tal cual. Quedan fuera 11 con dos números o rangos ("575 y 577", "125 al 143") y 3 unidades sin cifra. 47 de los 271 (17%) son de Santiago, con el problema de los tres códigos.
- Tipos de unidad en esos 271. 115 departamentos, 18 casas, 9 oficinas, 5 "unidad", 4 estacionamientos y 3 viviendas.

## Lo que falta saber (supuesto o desconocido)

1. Qué devuelve la búsqueda. Si trae el rol y nada más, cada causa necesita además /get_property_data para los metros (cobrado) y /get_appraisal (cobrado). Si trae metros y tipo, basta /get_appraisal.
2. Si las búsquedas se cobran y el precio de las demás consultas.
3. Cómo escribir la calle (con o sin "Avenida", "Pasaje" o "calle", con tildes) y qué tan tolerante es.
4. Qué código usar para Santiago.
5. Si la respuesta trae datos de propietarios. No se guardarían ni se mostrarían.
6. Qué tan seguido acierta. Ninguna prueba hecha. La red de la nube de Claude bloquea api.inciti.com y la terminal del PC no tiene internet.

## Conclusión

Sí sirve en principio. Es exactamente la pieza que faltaba (dirección a rol de avalúo) y calza con lo que el robot ya tiene en 95% de los inmuebles con calle en la RM (n=271). No está comprobado que acierte ni cuánto cuesta. La exploración del SII queda en pausa como respaldo.

## Prueba propuesta (paso 3, necesita aprobación de Diego)

Hay avisos que imprimen el rol de avalúo (9,2% de 533). Esos sirven de prueba con la respuesta conocida. Se manda la dirección que leyó el robot y se compara el rol que devuelve inciti con el impreso en el aviso. Ejemplos del Excel del 14 de Noviembre, Santo Domingo 1161 departamento 808 en Santiago (rol 210-636) y Arturo Prat 324 departamento 1809 en Santiago (rol 533-358), que además prueban los tres códigos de Santiago. La prueba la corre Claude Code en el PC de Diego con la key de config.py, sin imprimirla y sin guardar datos de propietarios, con unas 10 a 20 consultas.
