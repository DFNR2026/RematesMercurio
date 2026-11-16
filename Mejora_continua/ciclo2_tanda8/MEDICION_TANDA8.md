# Ciclo 2, tanda 8. Medición en copia (16 de noviembre del 2026)

Decisiones de Diego del 16 de noviembre. Los remates de juzgados que no son civiles (Cobranza Laboral, Familia y Letras del Trabajo) se eliminan del todo, como Policía Local. Un aviso pegado a otro con la propiedad fuera de la RM va a Descartadas (1296-2023 del 1° Juzgado Civil de Valdivia entró a la principal el 15 de noviembre).

Medido en la nube de Claude (Python 3.13, RapidFuzz 3.14.5) con el código de HEAD 51ac4c2 (tanda 7 publicada), sobre 16 ediciones (Capturas del 14 al 18 de octubre, banco_pruebas y las capturas del 13 al 16 de noviembre), 1.521 avisos y las respuestas de Haiku guardadas. Tablas con ciclo2_tanda7/tablas7.py y ciclo2_tanda4/cmp.py, cada edición sola y sin memoria. Se aplica con python3 -I aplicar_tanda8.py RAIZ [ARREGLO ...]. Pruebas nuevas en test_tanda8.py (va a pruebas/), 7 líneas OK, y sin los arreglos 3 fallan.

| Arreglo | Archivo | Qué hace | Avisos que cambian | Filas que cambian de tabla |
|---|---|---|---|---|
| NC1 | motor/edicion.py, modulo1_mercurio.py, pruebas/test_edicion.py y pruebas/test_filtros.py | Un aviso cuyo tribunal leído dice "Cobranza Laboral", "Juzgado de Familia" o "Letras del Trabajo" se elimina antes de la IA, como Policía Local. "Juzgado de Letras" a secas y "de Letras y Garantía" siguen, porque tienen competencia civil. El log cuenta "N de otros juzgados no civiles eliminados". Las pruebas de inventario de test_edicion y la 18 de test_filtros bajan su cuenta por las causas de Cobranza Laboral que ya no salen | 19 salen, todos no civiles (Cobranza Laboral de Santiago, Concepción y Temuco, 1° y 3° de Familia de Santiago y Letras del Trabajo de San Bernardo) | 3908-2025 sale de la principal (14 al 16 de octubre y banco), 9854-2025 de Familia sale de la principal, 357-2024 de Excluidas, 770-2014 y 138-2017 de Descartadas, y un aviso sin rol |
| PG1 | motor/filtros.py | En la salvaguarda de avisos pegados, si todas sus propiedades traen una comuna comprobada y ninguna es de la RM, la causa va a Descartadas con el motivo "Propiedad fuera de RM" y los roles pegados. Si alguna no trae comuna o es de la RM, sigue a la principal como antes | 0 | 1296-2023 del 15 de noviembre pasa de la principal a Descartadas. Los otros pegados de las 16 ediciones siguen en la principal (1296-2023 del 16 de noviembre sin comuna leída en la copia y 3673 del 9 de octubre) |

Juntos, 1.521 avisos a 1.502 y 20 filas de tabla cambian, sin cruces. Cero colores, carátulas o direcciones en los avisos que quedan. Las 15 pruebas del proyecto con TODO OK. Los archivos compilan.

sha1 de partida (HEAD 51ac4c2). motor/edicion.py e643d3b3a59ebe5c0c493d01fcb6a84ceb833b3a, motor/filtros.py b11527e4c839ddba2f57faef3bd3456df7f714e4, modulo1_mercurio.py d25defe1f9c8b13ff57b9c080fa913c1f8f28194, pruebas/test_edicion.py ded7fcd1628437d10aaa9000a5179ad7b81cdfa8, pruebas/test_filtros.py 1e1834b648e968dfa0fce32638a024a8965da268.

sha1 con la tanda completa. motor/edicion.py 4b77ee27c7c6fcc48203c9c15803b131db602bea, motor/filtros.py 159bcb982485715ee105f123b947bc779fdf9cf9, modulo1_mercurio.py fd297c85c084ece8a31f3a8a1c0d0c1aa4897630, pruebas/test_edicion.py 5673079def04b7d28a24afd53d4dc2c23a851d0f, pruebas/test_filtros.py 707fcb0a3002f80f6ed9744756f9c112313941a0, pruebas/test_tanda8.py e7454d1291deb3329c9e08ad06a7972be464d021.

Nota. 28-2025 es una cobranza laboral, pero su tribunal es el "2° Juzgado de Letras de San Fernando", así que NC1 no la toca.
