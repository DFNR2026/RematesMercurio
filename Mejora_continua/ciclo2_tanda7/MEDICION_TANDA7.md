# Ciclo 2, tanda 7. Medición en copia (14 de noviembre del 2026)

Sin tocar D:\Mercurio. Medido en la nube de Claude (Python 3.13, RapidFuzz 3.14.5) con el código de HEAD 1759663 (tanda 6 publicada), sobre las 14 ediciones que quedan en el disco (Capturas del 14 al 18 de octubre, banco_pruebas y las capturas del 13 y del 14 de noviembre), 1.348 avisos, las respuestas de Haiku del 13 de noviembre más las 111 de la captura del 14, y la hoja REFERENCIA del 18 de octubre. Cada arreglo se midió contra la copia con los anteriores puestos. Las tablas se miden con tablas7.py (esta carpeta) y ciclo2_tanda4/cmp.py, cada edición sola y sin memoria.

Se aplica con python3 -I aplicar_tanda7.py RAIZ [ARREGLO ...], que exige encontrar cada texto original exacto una sola vez y respeta el fin de línea de cada archivo. Pruebas nuevas en test_tanda7.py (va a pruebas/), 16 líneas OK. Sin los arreglos, 7 de ellas fallan.

Decisiones de Diego del 14 de noviembre. Los remates de un Juzgado de Policía Local se eliminan por completo (13136-2022, "causa por daños en choque" del Tercer Juzgado de Policía Local de Santiago, entró a la principal el 14 de noviembre). F11, M1, G4 y G5 salen de la espera y se arreglan.

## Cada arreglo

| Arreglo | Archivo | Qué hace | Avisos que cambian | Filas que cambian de tabla |
|---|---|---|---|---|
| PL1 | motor/edicion.py y modulo1_mercurio.py | Un aviso cuyo tribunal leído dice "Policía Local" se elimina antes de la IA, como el partidor y la causa voluntaria. No va a ninguna tabla ni a la memoria. El log cuenta "N de Policía Local eliminados" | 4 salen, todos de Policía Local (13136-2022 del 3° de Santiago el 14 de noviembre y su aviso sin rol del 10 de octubre, y el 2° de Pudahuel sin rol del 9 y 10 de octubre) | 13136-2022 sale de la principal del 14 de noviembre y bajan los avisos sin rol del 9 y del 10 de octubre |
| G4 | motor/extraccion.py | "JUZGADO DE CIVIL" vale como "JUZGADO CIVIL" | 1 (3127-2024 gana el 18° Juzgado Civil de Santiago) | 3127-2024 es un lote de parcela sin calle en Coihueco, así que T1 lo sigue eliminando, ahora con su tribunal |
| G5 | motor/extraccion.py | Al comienzo del aviso, "DÉCIMO SÉPTIMO CIVIL de Santiago" sin la palabra Juzgado se lee como el 17° Juzgado Civil. Solo si el comienzo no trajo tribunal ni lo dio la frase del rol (G3) | 1 (1455-2023 gana el 17° Juzgado Civil de Santiago) | 1455-2023 sigue en la principal, ahora con tribunal y Corte |
| F11 | motor/extraccion.py | Si el aviso no dio ninguna inscripción en cifras y trae "fojas" seguido de palabras, se busca otra vez con los números en palabras pasados a cifras | 1 de 693 avisos distintos (7170-2026 gana sus tres inscripciones de 2021) | 7170-2026 pasa de la principal a Excluidas por dominio 2021 (13 y 14 de noviembre) |
| M1 | motor/extraccion.py | Si un mínimo no tiene etiqueta con número ni letra, se usa el último número romano de lote ("I.-", "II.-") que va antes de él. La lista se arma solo si cada mínimo queda con su propio lote | 4 (28-2025 del 15 al 18 de octubre pasa de 1 a 2 remates) | 28-2025 pasa de la principal a Descartadas por Solo RM en la copia (ver la nota) |

Nota de M1. 28-2025 es una cobranza laboral del 2° Juzgado de Letras de San Fernando con dos lotes. El lote I son dos sitios en Conchalí (sitio número cinco y sitio número cuatro del Fundo La Palmilla) y el lote II la Oficina número mil uno del Edificio YMCA, en calle Compañía 1390, Santiago. Con 2 remates la huella del aviso cambia y no hay respuesta guardada de Haiku, por eso en la copia queda sin dirección, sin comuna y se descarta por la Corte. En una corrida real Haiku lo lee de nuevo. Lo esperable es que salgan las comunas de la RM y que, por ser sitios sin casa y una oficina, vaya a la tabla aparte del final (supuesto, no se puede comprobar sin Haiku).

## Todos juntos (PL1, G4, G5, F11 y M1) contra la tanda 6

1.348 avisos a 1.344. 12 filas de tabla cambian, las mismas de cada arreglo, sin cruces. Cero colores, carátulas o direcciones cambiados en los otros avisos. En la edición del 14 de noviembre, sin memoria, la principal pasa de 34 a 32 filas (sale 13136-2022 por PL1 y 7170-2026 por F11) y Excluidas de 30 a 31. Las 14 pruebas del proyecto con TODO OK (las 13 de antes y test_tanda7). Los archivos compilan.

sha1 de partida (HEAD 1759663). motor/edicion.py 766fa786c8116d3b4f2675f5fec669e7ae5dff25, motor/extraccion.py 163bfe73039ad0eca36689aa3edf4e875620c55b, modulo1_mercurio.py c97e1645f9c98a619514802bf3e029019b306466.

sha1 con la tanda completa (ORDEN de aplicar_tanda7.py). motor/edicion.py e643d3b3a59ebe5c0c493d01fcb6a84ceb833b3a, motor/extraccion.py a374a67fc8fe092876541f94671034ccc965e74f, modulo1_mercurio.py d25defe1f9c8b13ff57b9c080fa913c1f8f28194.

## Lo que esta tanda no cubre

Otros juzgados que no son civiles siguen entrando como hasta ahora, porque nadie pidió sacarlos. En las 14 ediciones aparecen Cobranza Laboral (770-2014, 3908-2025, 357-2024), Familia (9854-2025, 6692-2024), Letras del Trabajo (138-2017) y "Letras de y Garantía" de Bulnes (118-2026).

## Agregado el 15 de noviembre del 2026. Edición del 15 de noviembre y aplicación en D:\Mercurio

La edición del 15 de noviembre (domingo, cuerpo F, 117 avisos, 99 leídos) se sumó a la medición con las 99 respuestas de Haiku de su captura. Con la tanda cambia solo 7170-2026, que pasa de la principal a Excluidas por F11. En las 15 ediciones, 1.447 avisos a 1.443 y 13 filas de tabla cambian, las de cada arreglo. Las 14 pruebas repetidas en la nube con los tres archivos medidos dan TODO OK.

Aplicado en D:\Mercurio el 15 de noviembre. Antes, los tres archivos sin cambios desde HEAD 1759663. El script sobre una copia dio los sha1 de arriba y aplicado en D:\Mercurio dio los mismos. test_tanda7.py copiado a pruebas/ (sha1 d0cc1e57cbf6308baedd92afb570e13195fd1c4a).
