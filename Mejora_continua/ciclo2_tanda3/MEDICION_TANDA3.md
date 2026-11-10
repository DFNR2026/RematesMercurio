# Ciclo 2, tanda 3. Carátulas y fojas. Medición en copia (9 de noviembre del 2026)

Sin tocar D:\Mercurio\motor. Medido en una copia fuera de D:\Mercurio (contenedor de Claude, Python 3.13) con el código de HEAD 981673f, sobre 20 ediciones guardadas (Capturas del 14 al 18 de octubre y del 2 al 9 de noviembre, más banco_pruebas), 1.958 avisos. Decisiones de Diego del 9 de noviembre. Entran los arreglos del programa y los tres de error de tipeo del diario (C5b, C13, C14). El texto distinto para la carátula incompleta (C6) no entra. BancoEstado se busca en el aviso solo si la carátula quedó vacía y fuera de las frases de pago.

Se aplica con python3 -I aplicar_tanda3.py RAIZ [ARREGLO ...], que exige encontrar cada texto original exacto una sola vez. Pruebas nuevas en test_tanda3.py (va a pruebas/), 29 casos. Corrección del 10 de noviembre, la primera versión decía 30 por un error de conteo. Antes de los arreglos fallan los 18 de arreglo y pasan los 7 que deben seguir igual. Después pasan todos.

## Cada arreglo por separado (avisos que cambian sobre 1.958)

| Arreglo | Qué hace | Carátulas ganadas | Inscripciones ganadas | Pérdidas o cambios | Otros cambios (color, dirección, remates) |
|---|---|---|---|---|---|
| F1 | Acepta "Fs.", "fs", "fs." y "fjs" en lugar de fojas | 0 | 304 | 0 | 0 |
| F2 | Acepta "f." | 0 | 5 | 0 | 0 |
| F3 | Acepta "números" | 0 | 4 | 0 | 0 |
| F4 | Acepta la letra F junto a las fojas y "N.°" | 0 | 14 | 0 | 0 |
| F7 | "Reg." y "Prop." no cortan la frase antes del año (solo se ve junto a F1, 188-2025) | 0 | 0 | 0 | 0 |
| C8 | Rol sin guion antes de la carátula | 1 | 0 | 0 | 0 |
| C9 | Espacio antes del año del rol y carátula cerrada por ", remata" | 1 | 0 | 0 | 0 |
| C10 | "expediente" igual que "autos" | 4 | 0 | 0 | 0 |
| C3b | Comilla de apertura sin cierre, termina en ", remátese" o ", Rol" | 4 | 0 | 0 | 0 |
| C11 | Busca la carátula desde cada comilla | 4 | 0 | 0 | 0 |
| C12 | Carátula con barra sola antes de "Rol C-" | 12 | 0 | 0 | 0 |
| C5b | Punto y coma en vez de comilla | 6 | 0 | 0 | 0 |
| C14 | "expediente cat. X/Y, Rol" | 4 | 0 | 0 | 0 |
| C13 | Minúscula al inicio justo después de "caratulado" | 3 | 0 | 0 | 0 |

Corrección durante la medición. La primera versión de C3b cambiaba el arreglo de _CAR_SIN y cortaba la carátula de 17802-2023 en "S.A." (3 avisos). Se rehízo como patrón aparte (_CAR_ABIERTA) que no acepta ninguna comilla adentro. Con eso cero cambios. Se agregó "fjs" a F1 al ver 12304-2024 entre los que quedaban.

## Todos juntos

39 avisos ganan carátula (11 roles, entre ellos 19158-2023 de BancoEstado que se veía en Excluidas), 0 pierden, 0 cambian. 327 avisos ganan inscripción, 0 pierden, 0 cambian, todas con año. 0 cambios de color, dirección o remates. Avisos sin inscripción 355 a 31, los 31 revisados (aviso sin inscripción, usufructo en Hipotecas, número roto "N 3 22232", sin la palabra fojas, interdicción, partición y otros que no son remates).

Tablas, cada edición sola y sin memoria (1.879 causas).
- 63 pasan de la principal a Excluidas por dominio 2020 o posterior, todas con su año leído del aviso (por ejemplo 1650-2024 de 2021 y 15460-2025 de 2025).
- 6 pasan de la principal a Descartadas por BancoEstado (11209-2023 cuatro días, 3543-2026 dos días). 3 de Excluidas a Descartadas (19158-2023) y 1 cambia de motivo dentro de Descartadas (14152-2014, de Pre-2018 a BancoEstado). Revisadas en el texto, las tres son de verdad del Banco del Estado de Chile como demandante.
- Ninguna causa pasa de Excluidas o Descartadas a la principal.
- Principal 823 a 754. Con Observación del año de inscripción 184 a 29. Con Observación de carátula 28 a 14. Sin fojas 173 a 18.

BancoEstado en el aviso. De 51 avisos con carátula vacía, la regla marca 7 (3 causas) y las 3 son de BancoEstado. Cero equivocadas en 1.958 avisos. Los 39 avisos del 2 al 9 de noviembre que nombran el banco solo para pagar no se marcan.

Pruebas del proyecto en la copia con los arreglos. test_caratula, test_conjunto, test_cortador, test_direccion, test_edicion, test_extraccion, test_filtros, test_mejora_ciclo2, test_navegacion_logica y test_tanda3, todas TODO OK.

## Qué queda sin arreglo

C2a (1558-2025, decisión del ciclo 1), C16 (7314-2015, aviso de partición pegado, es del corte del aviso), C6, C15 sin "con" que no es de BancoEstado, y las fojas del aviso (F5, F6, F8, F9).
