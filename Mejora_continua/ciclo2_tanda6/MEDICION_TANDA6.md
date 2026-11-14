# Ciclo 2, tanda 6 (tanda de los sueltos). Medición en copia (12 de noviembre del 2026)

Sin tocar D:\Mercurio. Medido en la nube de Claude (Python 3.13, RapidFuzz 3.14.5) con el código de HEAD 17572c2 (tandas 4 y 5 publicadas), sobre 23 ediciones guardadas (Capturas del 14 al 18 de octubre y del 2 al 12 de noviembre, más banco_pruebas) y 2.211 avisos, con la hoja REFERENCIA de causas_ojv.xlsx (respaldo del 18 de octubre) y las 1.054 respuestas de Haiku del 10 de noviembre. Los avisos del 11 y 12 de noviembre y los de banco_pruebas sin respuesta guardada quedan sin lectura de dirección, igual antes y después.

Se aplica con python3 -I aplicar_tanda6.py RAIZ [ARREGLO ...], que exige encontrar cada texto original exacto una sola vez y respeta el fin de línea de cada archivo. Las tablas se miden con tablas.py y cmp.py de ciclo2_tanda4 (cada edición sola y sin memoria). Pruebas nuevas en test_tanda6.py (va a pruebas/), 15 líneas OK.

Estado. V1, F10, RM1 y K1 medidos y aprobados por Diego el 12 de noviembre. Actualización del 13 de noviembre. Se agregan B1 y B2 (bloques de remates) y P1 (parcela cortada a 200 caracteres), medidos y a la espera del visto bueno de Diego, ver la sección del 13 de noviembre al final. El script los trae en ORDEN, así que los sha1 finales de la tanda son los de esa sección. F11 (inscripción en palabras) queda en espera por decisión de Diego (n=1 en 23 ediciones).

## Conteo previo (pedido por Diego antes de proponer el arreglo)

Causas voluntarias, 6 causas distintas en 12 avisos. Con rol leído porque el aviso dice "Rol V-...", 188-2025 del 23° Civil (18 de octubre y 8 de noviembre, iba a la principal con la carátula "/O’Brien"), 285-2024 del 17° Civil (12 de noviembre, iba a Descartadas por BancoEstado) y 310-2025 del 7° Civil (banco_pruebas del 1 de septiembre, iba a Excluidas). Sin rol leído porque el aviso dice "causa V-..." o "V-..." sin la palabra Rol, 439-2026 del 1° Civil de Puente Alto (15 al 17 de octubre), 238-2025 del 1° Civil (4 y 12 de noviembre) y 50-2026 del 21° Civil, interdicción (4 al 6 de noviembre). Falso positivo a evitar, el aviso C-12153-2025 del 6 de octubre trae pegado el extracto de otra causa V-101-2025.

Fojas. F10 (punto entre el número de fojas y "Número", sin "vta.") solo en 2334-2025 (11 y 12 de noviembre). F11 (inscripción en palabras sin ningún dato leído) solo en 7170-2026 (12 de noviembre).

## Cada arreglo por separado

| Arreglo | Archivo | Qué hace | Avisos que cambian | Filas que cambian de tabla |
|---|---|---|---|---|
| V1 | motor/edicion.py y modulo1_mercurio.py | La causa voluntaria se elimina del todo, como los partidores. Es voluntaria si el rol leído trae la V, o si el aviso no tiene rol leído y su texto trae un V-número-año. No pasa por la IA, no aparece en ninguna tabla y no se anota en la memoria. El log cuenta "N voluntarias eliminadas" junto a los partidores | 12 avisos salen (los 12 del conteo, ninguno más) | 188-2025 sale de la principal (2 ediciones), 285-2024 de Descartadas, 310-2025 de Excluidas, y los avisos sin rol bajan en 7 (15 al 17 de octubre, 4 al 6 de noviembre y 12 de noviembre) |
| F10 | motor/extraccion.py | El patrón de fojas acepta un punto, igual que la coma, entre el número de fojas y "Número" o "N°" | 2 (2334-2025 gana su inscripción de 2024, 11 y 12 de noviembre) | 2334-2025 de la principal a Excluidas (2 ediciones) |

F10 revisado aparte en la inscripción de los 2.211 avisos, cambian solo esos 2.

## Juntos

2.211 avisos a 2.199. 13 filas de tabla cambian (las 11 de V1 y las 2 de F10, sin cruces). Ninguna fila entra a la principal. Cero colores, carátulas, remates o direcciones cambiados en los avisos que quedan. En la edición del 12 de noviembre el log diría 86 cortados, 7 partidores, 2 voluntarias, 1 sin rol y 76 causas.

Pruebas del proyecto en la copia con todo aplicado. Las 13 (las 12 de antes y test_tanda6) con TODO OK. modulo1_mercurio.py compila.

sha1 de partida (HEAD 17572c2). motor/edicion.py 4e1690a0047421e1914cd06a42792b46d04758a7, motor/extraccion.py cc89e94b8786d92647b8edb4843adb58ce6c2aff, modulo1_mercurio.py 4dc3cc04597708781e4ef2c116eaad7d4c892a4c.

sha1 con V1 y F10 aplicados. motor/edicion.py 37d42f54bdbbf599ba6e43aeb2853d3c839044cb, motor/extraccion.py 6ed95198127c078a89ecd4f9c623782968ac7383, modulo1_mercurio.py cbd4ed098d197df94fb4fb0d4278af3cc0d6e0d7.

## K1, Corte de los juzgados de Antofagasta (medido solo, primero quedó en espera)

Causa raíz, comprobada corriendo buscar_corte. La hoja REFERENCIA escribe "1º", "2º" y "3º Juzgado de Letras Civil de Antofagasta" con o volada y "4° ..." con el signo de grado. Los cuatro empatan en el puntaje, buscar_corte se queda con el primero (1°) y lo rechaza por número distinto. Por eso el 1° y el 4° encuentran su Corte y el 2° y el 3° no. K1 hace que en un empate gane el tribunal con el mismo número. En los 67 tribunales distintos de las 23 ediciones cambian solo esos dos, que pasan a C.A. de Antofagasta. Siguen sin Corte "2° Juzgado de Policía Local de Pudahuel", "3° Juzgado Civil de Talca" y "Juzgado de Cobranza Laboral de Temuco".

Efecto en las tablas. 5 filas de la principal a Descartadas por Solo RM, 548-2025 del 2° de Antofagasta (9 y 10 de noviembre) y 2087-2024 del 3° de Antofagasta (banco_pruebas, 9 al 11 de octubre).

Por qué queda en espera. Las dos tienen la propiedad en la RM, 548-2025 un departamento en calle Compañía 2633, comuna de Santiago, y 2087-2024 una casa en Avenida Primo de Rivera 727, comuna de Maipú (leído en el texto de cada aviso). Hoy entran a la principal con la Observación de la Corte. Con K1 se perderían.

Hallazgo mayor. En motor/filtros.py aplicar() descarta por Solo RM según la Corte del tribunal antes de mirar la comuna de la propiedad, y el prompt maestro dice "Solo RM por comuna de la propiedad". En las 23 ediciones hay 20 causas en Descartadas por Solo RM y 9 tienen la propiedad en una comuna de la RM según la dirección comprobada (1069 Casablanca con Curacaví, 1177 Viña con Cerrillos, 207 San Felipe con Santiago, 2237 Chillán con Santiago, 2244 Concepción con Lo Barnechea, 2357 Viña con Peñalolén, 28 San Fernando con Conchalí, 548 Viña con Providencia y 956 Punta Arenas con Providencia). 5 de esas comprobadas en el texto del aviso. Otras 8 no tienen comuna leída en la copia (sin respuesta guardada de Haiku), y 3 son de fuera de la RM (Temuco, Puerto Montt, Ovalle). Estación Central de Viña (1558) se descarta igual por su propia regla. Falta la decisión de Diego sobre si un remate de un juzgado de otra región con la propiedad en la RM debe entrar.

## RM1, juzgado de otra región con la propiedad en la RM (decisión de Diego del 12 de noviembre)

Diego decidió que esas causas entran. RM1 (motor/filtros.py) hace que una causa cuya Corte no es de la RM no se descarte por Solo RM si alguna de sus propiedades trae una comuna de la RM escrita igual que una de las 52 (sin coincidencia difusa). La causa sigue por los demás filtros (BancoEstado, año del rol, Estación Central, dominio) y lleva la Observación "El remate es en un juzgado de otra región, pero la propiedad está en la Región Metropolitana." Sin comuna, la Corte sigue decidiendo como antes.

Medido solo, 35 filas cambian y ninguna otra cosa. 4 causas entran a la principal (28-2025 de San Fernando con Conchalí, 2244-2019 de Concepción con Lo Barnechea, 548-2025 de Viña con Providencia y 2357-2022 de Viña con Peñalolén, 15 filas). 5 causas pasan a Excluidas por su dominio de 2019 o posterior (2237-2025 de Chillán, 1177-2025 de Viña, 956-2024 de Punta Arenas, 1069-2025 de Casablanca y 207-2026 de San Felipe). 1558-2025 de Viña sigue en Descartadas, ahora por Estación Central.

K1 con RM1 puesto. 548-2025 del 2° de Antofagasta (Santiago) se queda en la principal y cambia la Observación de la Corte por la de otra región. 2087-2024 del 3° de Antofagasta pasa a Descartadas por Solo RM solo en la copia, porque banco_pruebas no tiene la lectura de Haiku. Su aviso dice "Comuna de Maipú, Región Metropolitana", así que en una corrida real tendría comuna y entraría (supuesto, depende de que Haiku la lea y se compruebe).

## Todos juntos (V1, F10, RM1 y K1)

2.211 avisos a 2.199. 53 filas de tabla cambian (11 de V1, 2 de F10, 35 de RM1 y 5 de K1, sin cruces). Cero colores, carátulas, remates o direcciones cambiados en los avisos que quedan. Las 13 pruebas con TODO OK, test_tanda6 con 28 OK, y las 2 de K1 para el 2° y el 3° de Antofagasta fallan sin K1. Los cuatro archivos compilan.

sha1 de partida de motor/filtros.py (HEAD 17572c2) 885c0d515d90800dfb22334ff77f67e3627296e3.

sha1 con V1, F10, RM1 y K1 aplicados. motor/edicion.py 37d42f54bdbbf599ba6e43aeb2853d3c839044cb, motor/extraccion.py 6ed95198127c078a89ecd4f9c623782968ac7383, modulo1_mercurio.py cbd4ed098d197df94fb4fb0d4278af3cc0d6e0d7, motor/filtros.py 7aca71aeb67bf53ebff622f60c2381061b1ddbf7.

## Agregado el 13 de noviembre del 2026. B1 y B2 (bloques de remates) y P1 (parcela cortada)

Medido en la nube de Claude (Python 3.13, RapidFuzz 3.14.5) con el código de HEAD 17572c2, sobre las 13 ediciones que quedan en el disco (Capturas del 14 al 18 de octubre, banco_pruebas y la captura del 13 de noviembre) y 1.244 avisos, con las 1.156 respuestas de Haiku del 13 de noviembre y la hoja REFERENCIA del 18 de octubre. Las capturas del 2 al 12 de noviembre ya no están en el disco (Diego las borró el 13 de noviembre), así que V1, F10, RM1 y K1 conservan su medición del 12 de noviembre sobre 23 ediciones y aquí solo se comprobó que siguen dando lo mismo en las 13.

### Causa raíz del hallazgo del 13 de noviembre (viernes con tres bloques, B10-B11, C8 y G9 a G14)

Comprobado rehaciendo el día con su captura. La copia da lo mismo que el servidor (140 avisos, 8 partidores, 132 leídos, 126 verde, 5 rojo y 1 sin dato, 97 causas y 2 sin rol).

1. La sección de remates siguió de B11 a C8 sin la flecha "MÁS AVISOS" (navegacion.json trae salidas y entradas vacías en las 9 páginas). Por eso el lector armó tres bloques y no dos.
2. G reimprime todo. B corta 64 avisos, C 38 y G 101. B y C leídos como un solo bloque dan 101 avisos, iguales uno por uno a los 101 de G por huella del texto.
3. unir_rollos busca el gemelo de cada aviso solo en el primer bloque (avisos[:len(cortados[0])]). Los 38 de C no tienen gemelo en B y se cargan. De los 101 de G, 63 tienen gemelo en B y los otros 38 se cargan otra vez. 37 de esos son los mismos de C. Corrección del supuesto del 13 de noviembre, eran 37 avisos repetidos y no 38.
4. Los 37 repetidos no cambian ninguna fila del Excel, porque caen en la misma causa y propiedades() no repite un aviso con la misma huella (medido, B2 solo cambia 0 filas). Lo que inflan es el log (140 avisos en vez de 101, 8 partidores en vez de 4, 132 leídos en vez de 97, 5 rojos en vez de 3).
5. El daño real fue un solo aviso, 1445-2024 del 22° Civil (departamento en Antofagasta). Quedó partido entre B11 y C8. La cabeza (con el tribunal y la dirección, sin rol) salió como aviso sin rol. La cola (con el rol, sin tribunal) salió en la principal sin tribunal ni dirección. El aviso entero de G salió en Descartadas por Antofagasta. Al abogado le llegaron una fila de más en la principal y un aviso sin rol de más.
6. Las otras dos causas sin tribunal del día no vienen de los bloques. 6458-2022 empieza "REMATE. SE ORDENA REMATAR" y nombra al tribunal en palabras al final ("Décimo Tercer Juzgado Civil de Santiago" y "13° Juzgado Civil de Santiago"). 3127-2024 imprime "18° JUZGADO DE CIVIL DE Santiago". Son formas nuevas del tribunal, n=1 cada una, sin arreglo en esta tanda.

### Cada arreglo por separado

| Arreglo | Archivo | Qué hace | Avisos que cambian | Filas que cambian de tabla |
|---|---|---|---|---|
| B1 | motor/edicion.py | unir_continuaciones(). Dos bloques seguidos se leen como uno si el primero termina con una palabra cortada y el segundo empieza en minúscula, y solo si al unirlos sale exactamente un aviso menos. Deja una línea en el log | Solo el 13 de noviembre. Salen la cabeza y la cola de 1445-2024 y entra el aviso entero leído desde B y C | 3, todas del 13 de noviembre. Sale la fila de 1445-2024 sin tribunal de la principal, los avisos sin rol bajan de 2 a 1 y 1445-2024 queda una sola vez con el 22° Civil |
| B2 | motor/edicion.py | unir_rollos busca el gemelo en todo lo ya cargado y no solo en el primer bloque | Solo el 13 de noviembre, dejan de cargarse dos veces los 37 avisos de C | 0 |
| P1 | motor/direccion.py | _frase_terreno(). La frase de un terreno sin calle va completa hasta 350 caracteres. Si es más larga se corta en el último espacio y lleva puntos suspensivos. Antes frase[:200], que cortaba a media palabra | 11 causas distintas cambian solo el texto de la dirección (frases de 202 a 529 caracteres, 10 quedan completas y 1 cortada en 349) | 16 filas cambian solo el texto de la dirección, ninguna cambia de tabla |

Nota de B1. En la copia, 1445-2024 unido queda en la principal con "No se pudo comprobar la dirección", porque el texto leído desde B y C difiere en espacios del de G y no tiene respuesta guardada de Haiku. En una corrida real Haiku lo lee de nuevo (supuesto, lo esperable es que salga en Descartadas por Antofagasta, como salió el aviso entero de G).

Nota de P1. 8121-2024 no está en las 13 ediciones que quedan en el disco. El mecanismo es el mismo (frase[:200] en verificar_inmueble) y se midió con las 11 causas que sí están.

### El 13 de noviembre rehecho con toda la tanda

101 avisos cortados, 4 partidores, 0 voluntarias, 1 sin rol y 96 causas. Alarmas "El bloque que empieza en C8 continúa al que empieza en B10" y "Cuerpo G repite al B. 101 de 101 avisos unidos". Sin memoria, principal 37 (antes 38), Excluidas 28 (antes 27, entra 2334-2025 por F10), Descartadas 31 (antes 32) y sin rol 1 (antes 2).

### Todos juntos (V1, F10, RM1, K1, B1, B2 y P1) en las 13 ediciones

1.244 avisos a 1.237. 37 filas de tabla cambian (21 de V1, F10, RM1, K1 y B1, y 16 de P1 que solo cambian el texto de la dirección). Las 13 pruebas con TODO OK, test_tanda6 con 36 OK (28 de antes, 5 de B1 y B2 y 3 de P1). Los archivos compilan.

sha1 de partida de motor/direccion.py (HEAD 17572c2) 6945d1ba962a73f20ec5fab3985a7376a4a9b9fe.

sha1 con los siete arreglos aplicados. motor/edicion.py e286d64f1b7d7d6b9f007db9b583f724e406d9d1, motor/extraccion.py 6ed95198127c078a89ecd4f9c623782968ac7383, modulo1_mercurio.py cbd4ed098d197df94fb4fb0d4278af3cc0d6e0d7, motor/filtros.py 7aca71aeb67bf53ebff622f60c2381061b1ddbf7, motor/direccion.py a3583549e031e0047da067e31d47765fb57898ad.

### Dos mínimos de 28-2025, causa raíz (sin arreglo, n=1)

Comprobado corriendo minimo_y_costas sobre el aviso (Capturas del 15 al 18 de octubre). El código sí lee los dos mínimos ($ 159.164.537 y $ 100.285.662). Lo que falla es la asignación. Solo arma la lista de remates si cada mínimo nombra su inmueble con una etiqueta con número en cifras (_ETIQUETA, "lote 4", "oficina N° 5"). Este aviso separa los lotes con "I.-" y "II.-" y escribe los números en palabras ("sitio número cinco", "Oficina número mil uno"), así que ningún mínimo queda con etiqueta, el código deja el mínimo vacío y cuenta 1 remate. Haiku lee entonces una sola propiedad y la dirección queda en rojo. En las 13 ediciones la misma alerta sale en 3 causas. 4079-2023 es la partición de 11 propiedades (no aplica), 770-2014 queda en verde igual, y 28-2025 es el único caso con daño. Arreglo posible, aceptar "I.-", "II.-" como etiqueta del lote cuando cada mínimo tiene la suya. En espera por n=1, igual que F11.

## Agregado el 13 de noviembre del 2026 (noche). Decisiones de Diego, G3, T1 y T2, y P1 fuera

Decisiones de Diego del 13 de noviembre. B1 y B2 aprobados. G3 sale de la espera por el reclamo de los abogados (dijeron que 6458-2022 y 1445-2024 del Excel del 13 no existían). Los terrenos sin calle desaparecen del todo, como los partidores. Las oficinas, los sitios sin casa y los terrenos con calle van al final del mismo Excel en una tabla aparte, solo por si acaso. "Lote" no se usa para filtrar porque una casa de condominio puede ser "lote 17". Se mira por causa (rol, año y tribunal). P1 sale de ORDEN, porque con T1 la frase de un terreno sin calle ya no se muestra. Los dos mínimos de 28-2025 (M1), F11, G4 y G5 siguen en espera.

Reclamo de los abogados, revisado con la captura del 13 de noviembre. Las dos causas están impresas en El Mercurio de ese día. 6458-2022 en G11 y B11 ("causa digital C-6458-2022 seguida ante el 13° Juzgado Civil de Santiago", casa 135 del Condominio La Liguria, Huechuraba). 1445-2024 en G12 y C8 ("expediente C-1445-2024, 'Scotiabank Chile con Ojeda'", 22° Juzgado Civil de Santiago, departamento en Antofagasta). No hubo invento. El rol, el tribunal y la carátula los lee solo el código desde el texto del diario. Las dos filas llegaron sin tribunal ni Corte, y sin tribunal no se pueden buscar en la OJV. 6458-2022 por la forma G3. 1445-2024 por el aviso partido entre B11 y C8 (B1), que además salió también en Descartadas con su tribunal.

Medido en la nube de Claude (Python 3.13, RapidFuzz 3.14.5) con el código de HEAD 9f0ae19, las 13 ediciones que quedan en el disco (Capturas del 14 al 18 de octubre, banco_pruebas y la captura del 13 de noviembre), 1.244 avisos, las 1.156 respuestas de Haiku del 13 de noviembre y la hoja REFERENCIA del 18 de octubre. Las tablas se miden con tablas6.py (esta carpeta) y ciclo2_tanda4/cmp.py. Cada arreglo se midió contra la copia con los anteriores puestos.

| Arreglo | Archivo | Qué hace | Avisos que cambian | Filas que cambian de tabla |
|---|---|---|---|---|
| G3 | motor/extraccion.py | Si el comienzo del aviso no trae tribunal, se lee el que va justo después del rol ("causa C-N-AÑO seguida ante el", "del", "en el"), solo si todas esas frases nombran el mismo. El vale vista y las frases de pago no cuentan | 1 (6458-2022 gana el 13° Juzgado Civil de Santiago) | 1. 6458-2022 sigue en la principal, ahora con tribunal y Corte. En los otros 9 avisos de las 13 ediciones que traen esa frase, el tribunal coincide con el del comienzo (0 distintos) |
| TP | motor/direccion.py, motor/edicion.py y motor/filtros.py | Lleva hasta el filtro el tipo que da Haiku (calle o sin calle) y la frase comprobada | 723 avisos en verde ganan esos dos datos, sin cambiar la dirección | 0 |
| T1 | motor/filtros.py y pruebas/test_filtros.py | Una causa cuyas propiedades en verde son todas terrenos sin calle desaparece del todo (ninguna tabla ni memoria). Un terreno sin calle cuya frase dice casa o vivienda no cuenta ("el sitio y casa Parcela número 4", 6996-2023). Si una causa trae además una casa o un departamento, sigue con esa propiedad y una Observación. Lo mismo para los avisos sin rol | 0 | 82 filas salen (34 de la principal, 16 de Excluidas, 36 de Descartadas, 36 causas distintas) y 2 avisos sin rol (predio El Carmen de Calle Larga, 17 y 18 de octubre). Sale también 9836-2023, los derechos de agua del Embalse de Cogotí |
| T2 | motor/filtros.py, modulo1_mercurio.py y modulo5_reporte.py | Una causa cuyas propiedades en verde son todas oficina, sitio sin casa o terreno va a la tabla nueva del final del Excel, "Oficinas, sitios y terrenos (aparte, solo por si acaso)", con tribunal, rol, año, dirección, comuna y motivo. No pasa por los demás filtros ni se anota en la memoria. Una línea nueva en el Resumen y en el log | 0 | 13 filas a la tabla aparte, todas oficinas (8715-2025, 4948-2025, 8527-2024, 16177-2024 y 10880-2022). Ningún sitio ni terreno con calle en las 13 ediciones |

Pruebas del punto 5 de Diego (causa con una casa o departamento y además un terreno, sitio u oficina). n=0 en las 13 ediciones. Se dejó que la causa siga con su propiedad normal y una Observación, para no perder un remate en silencio. Falta que Diego lo confirme.

Error encontrado y corregido antes de cerrar. En la primera versión de T1, la tabla de Ya informadas comparaba la lista de propiedades contra otra lista armada de nuevo y nunca sacaba nada. Ahora usa la misma lista. Con la prueba nueva de test_tanda6 (causa mixta en Ya informadas). No cambió ninguna fila porque n=0.

El 13 de noviembre rehecho con toda la tanda, sin memoria. Principal 31 (antes 38), Excluidas 26, Descartadas 26 (antes 32), tabla aparte 1 (16177-2024, oficina), sin rol 1 (antes 2) y 11 causas de terrenos sin calle eliminadas. 6458-2022 en la principal con el 13° Juzgado Civil de Santiago. 1445-2024 una sola vez, con el 22° Juzgado Civil de Santiago (en la copia queda en la principal con "No se pudo comprobar la dirección" porque el aviso unido no tiene respuesta guardada de Haiku. En una corrida real Haiku lo lee y lo esperable es Descartadas por Antofagasta, supuesto).

Todos juntos (V1, F10, RM1, K1, B1, B2, G3, TP, T1 y T2) contra HEAD en las 13 ediciones. 1.244 avisos a 1.237. 6 avisos sin rol menos (13 a 7). Cero colores, carátulas o remates cambiados en los avisos que quedan. Las 13 pruebas del proyecto con TODO OK en la copia, test_tanda6 con 54 OK (36 de antes, menos los 3 de P1, más 4 de G3 y 17 de T1 y T2) y test_filtros con su prueba 18 ajustada. Los archivos compilan. El Excel del 14 de octubre armado con modulo5_reporte.py trae la tabla aparte al final con sus 3 oficinas y la línea en el Resumen.

sha1 de partida (HEAD 9f0ae19). motor/edicion.py 4e1690a0047421e1914cd06a42792b46d04758a7, motor/extraccion.py cc89e94b8786d92647b8edb4843adb58ce6c2aff, modulo1_mercurio.py 4dc3cc04597708781e4ef2c116eaad7d4c892a4c, motor/filtros.py 885c0d515d90800dfb22334ff77f67e3627296e3, motor/direccion.py 6945d1ba962a73f20ec5fab3985a7376a4a9b9fe, modulo5_reporte.py d119e66b74f7f6691ae913fad2490f39acb5807c, pruebas/test_filtros.py 92094c603859f7dd46164c2b855871996801121b.

sha1 con la tanda completa (ORDEN de aplicar_tanda6.py). motor/edicion.py 766fa786c8116d3b4f2675f5fec669e7ae5dff25, motor/extraccion.py 163bfe73039ad0eca36689aa3edf4e875620c55b, modulo1_mercurio.py c97e1645f9c98a619514802bf3e029019b306466, motor/filtros.py b11527e4c839ddba2f57faef3bd3456df7f714e4, motor/direccion.py 40847663ab047447e861f72e56988e9d592ea5db, modulo5_reporte.py cd2e36c8e94d20b7bfd6942f500eaff1c26280fe, pruebas/test_filtros.py 1e1834b648e968dfa0fce32638a024a8965da268. Los sha1 de la sección anterior (con P1 y sin G3, TP, T1 y T2) ya no valen.

## Agregado el 14 de noviembre del 2026. Edición del 14 de noviembre y aplicación en D:\Mercurio

La edición del 14 de noviembre (sábado, cuerpo D, 117 avisos) se sumó a la medición, rehecha solo con su captura y las 111 respuestas de Haiku que trae dentro. Sin memoria, HEAD da principal 40, Excluidas 29 y Descartadas 39. Con la tanda da principal 34, Excluidas 30, Descartadas 32, 2 en la tabla aparte (12754-2024 y 16177-2024, oficinas) y 10 causas de terrenos sin calle eliminadas (entre ellas 16669-2023, 22311-2024, 946-2024 y 1707-2026). 6458-2022 republicado gana el 13° Juzgado Civil de Santiago. 6229-2025 del 1° Juzgado Civil de Temuco pasa de Descartadas a la principal por RM1, con la propiedad en "Comuna de Independencia, Región Metropolitana" según el aviso y dominio 2017. 118-2026 de Bulnes pasa de Descartadas a Excluidas por RM1 (La Cisterna, dominio 2026). 2334-2025 pasa de la principal a Excluidas por F10. Las 13 pruebas repetidas en la nube con los siete archivos medidos dan TODO OK.

Aplicado en D:\Mercurio el 14 de noviembre. Antes, los siete archivos sin cambios desde HEAD 9f0ae19 (git diff vacío). El script sobre una copia dio los sha1 de la sección del 13 de noviembre (noche), y aplicado en D:\Mercurio dio los mismos. test_tanda6.py copiado a pruebas/.
