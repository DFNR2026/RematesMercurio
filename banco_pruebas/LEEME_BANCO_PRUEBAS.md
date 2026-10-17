# Banco de pruebas de la lectura del Mercurio

Creado el 2026-10-14. Sirve para medir el motor de lectura nuevo contra respuestas correctas ya comprobadas.

## Contenido

Carpeta 2026-08-06. Seis trozos de texto de las páginas B 011, 012 y 013, copiados desde D:\Mercurio\payloads_diag_v2. Cada página se reconstruye uniendo el trozo .0 con el trozo .1 sin sus primeros 2.000 caracteres (el solape se comprobó idéntico en las tres páginas). Incluye inventario_correcto_2026-08-06.json con 95 avisos.

Carpeta 2026-10-14. Texto completo de las páginas B 11 y C 8, descargado desde el visor en Chrome. Las huellas SHA-256 de HUELLAS_ESPERADAS.txt se comprobaron contra los archivos. Incluye inventario_correcto_2026-10-14.json con 58 avisos. CORRECCIÓN 2026-10-15. Son 59 avisos. El inventario manual había dejado pegado un remate de juez partidor en Villarrica (sin rol) al aviso de Cobranza de Concepción. Lo detectó el cortador y se confirmó leyendo el texto. Queda anotado dentro del json. SEGUNDA CORRECCIÓN 2026-10-15 (tarde). Son 61 avisos. Dos remates de juez partidor (Díaz Loayza en Calera de Tango y Lescot en Maipú) iban pegados al aviso anterior, en el inventario manual y en el cortador. Diego confirmó en el diario que están impresos aparte.

Reporte_2026-08-06.xlsx y Reporte_2026-10-14.xlsx son los Excel que entregó el programa viejo esos días, para comparar.

## Cómo se armó cada inventario

Se unió el texto de todas las páginas de la sección 1616 en orden de lectura, se quitaron las cornisas "1616 Remates de propiedades" que el diario repite en cada columna, y se cortó por inicio de aviso con reglas de código. Después se revisó cada trozo a mano y se corrigieron los cortes que las reglas no vieron. Cada rol del inventario se comprobó presente en el texto.

## Qué mide hoy

Nivel 1. Que el motor encuentre todos los avisos, con su rol y su tribunal, y que no invente ninguno. Los demás datos (fecha del remate, modalidad, vale vista, mínimo, garantía, comuna, fojas, año de dominio) quedan para un nivel 2 que se agrega cuando el motor ya extraiga esos campos.

## Comparación con el programa viejo

06-08. El programa vio 92 de los 93 avisos con rol (solo se le escapó un RIT laboral) y botó en silencio los 2 avisos sin rol.
14-10. El programa vio 19 de los 57 avisos con rol. Los 38 restantes estaban en la página C 8, que no leyó.

## Trampas del diario que el motor debe resistir (todas vistas en estos textos)

Avisos que siguen en otra página o en otro cuerpo del diario ("MÁS AVISOS ECONÓMICOS CLASIFICADOS EN PÁGINA C 8", "VIENEN DE PÁGINA B 11").
Cornisas "1616 Remates de propiedades" en mitad de una palabra ("video confe1616 Remates de propiedades rencia").
Roles sin guion (C-39902025, CORRECCIÓN del 16 de Octubre, ejemplo falso, el diario imprime "C-3990-" al final del renglón), sin la palabra Rol (expediente C-5915-2025), con punto de miles (C-1.301-2026), con barra (2087/2024), con errata (CC-936-2026), sin prefijo C, o repetidos al inicio y al final del aviso.
Avisos sin rol impreso (Iturra Saldías, partidores) y RIT de juzgados laborales.
Avisos que empiezan sin la palabra REMATE, con el tribunal en palabras (VIGÉSIMO SEXTO, TRIGÉSIMO, DÉCIMO QUINTO (15°)) o pegados al final del aviso anterior (SecretarioREMATE).
Avisos de hasta 7.900 caracteres.

## Posiciones impresas (agregado el 2026-10-15)

2026-10-14. mercurio_2026-10-14_B11.geo.json y mercurio_2026-10-14_C8.geo.json. Posición de cada trozo de texto en la página, capturada el 2026-10-15. Los .txt de esa recaptura tienen la misma huella SHA-256 que los del banco, así que las posiciones corresponden exactamente a estos textos.
2026-10-11. F9 y F15 (texto y posiciones). No tienen inventario manual. Se usan como casos de prueba del orden por posición: en F9 el visor entrega las columnas en orden 1, 2, 4, 5, 6, 7, 3, y al pie de F15 hay una franja "1300 EMPLEOS" que cruza las columnas.
2026-10-09. B11 (texto y posiciones). Sin inventario manual. Caso de prueba del corte: "entregado materialmente en la secretaría del tribunal" no es un cierre de aviso, y el aviso siguiente empieza en "POR RESOLUCIÓN DEL 1° JUZGADO".

## Nivel 2 (agregado el 2026-10-15)

2026-10-14\banco_nivel2_2026-10-14.json. Los 61 remates del 14 de Octubre con fecha y hora del remate, modalidad, regla y fechas del vale vista, mínimo, garantía y dirección del inmueble. Cada dato lleva la frase exacta del diario (cita). El número n de cada remate es su número de aviso en el cortador. Las reglas usadas (día hábil, horas de reloj, desde estimado) están escritas dentro del archivo.
Lo anotó Claude. Diego revisó a mano 17 avisos sin encontrar errores de lectura, y sus comentarios quedan en el campo revision_diego. Los montos y porcentajes se comprobaron por código contra su cita.
Se comprueba con python -m pruebas.test_banco_nivel2 (citas presentes en el texto, fechas válidas, modalidades, vale vista recalculado desde la regla).
REVISION_DIEGO_nivel2_2026-10-14_v2.xlsx es la planilla con la que Diego revisó. La versión 1 quedó reemplazada y no va a git.
Lo que el banco enseñó. La mayoría de lo marcado "revisar" son fallas de redacción del aviso, no de lectura. Hay avisos con varios remates, garantías del 20% o sobre la tasación, cauciones sin vale vista, vale vista seis días antes o en el mismo remate, y roles mal impresos.

## Parte 3.7b (agregado el 2026-10-17)

2026-09-01. Páginas B15 y C8 copiadas desde capturas con HUELLAS_ESPERADAS.txt (iguales al lector). Caso de prueba de los 26 remates del rol C-5656-2013 que se distinguen por la inscripción.
2026-10-06\banco_direccion_2026-10-06.json. VALIDACIÓN de la dirección. Los 62 avisos de la muestra ya sorteada (59 medibles, 62 remates), anotados por Claude ANTES de escribir las instrucciones. md5 bcea570d3ae0afc84900dd9463625a13. Script en anotacion_direccion. Se corrió una sola vez (MEDICION_DIR_2026-10-06_dir-2.txt).
2026-10-14\banco_direccion_2026-10-14.json. AJUSTE de la dirección (57 medibles, 61 remates), reanotado desde el campo direccion del banco nivel 2, que queda igual. Las reglas de anotación están dentro de cada banco.
Trampas nuevas del diario. Número de calle y de unidad en palabras ("número cero ciento sesenta y uno", "departamento número A trescientos nueve"), comuna nombrada solo como ciudad ("calle Camino Nuevo 2065, Chillán"), comuna "San Miguel, hoy San Joaquín", inscripción con año imposible ("año 2033"), varias inscripciones con el año al final.

## Parte 3.7c (agregado el 2026-10-17)

2026-10-06\banco_caratula_2026-10-06.json. VALIDACIÓN de la carátula (59 medibles, md5 804f5943a33ca52d20701652052655bc), anotada antes del código, script en anotacion_caratula. Se corrió una sola vez (MEDICION_CARATULA_2026-10-06.txt). 2026-10-14\banco_caratula_2026-10-14.json, AJUSTE (57 medibles).
Trampas nuevas del diario. Comillas de cierre usadas como apertura (’Barrera con López’), "Caratulado" con mayúscula y sin comillas, carátula dentro de "causa X/ Y, juicio", "S.A. Con" y "Cía. Ltda" con punto y mayúscula dentro de la carátula, y el texto entre dos términos entrecomillados que no es carátula.
