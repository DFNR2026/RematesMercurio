# Ciclo 2, tanda 4. Direcciones y corte de dominio 2019. Medición en copia (10 de noviembre del 2026)

Sin tocar D:\Mercurio\motor. Medido en una copia en la nube de Claude (Python 3.13, RapidFuzz 3.14.5) con el código de HEAD e4a320b (tanda 3 publicada), sobre 21 ediciones guardadas (Capturas del 14 al 18 de octubre y del 2 al 10 de noviembre, más banco_pruebas) y 2.054 avisos, con las 1.054 respuestas de Haiku del 10 de noviembre. 497 avisos de banco_pruebas no tienen respuesta guardada y quedan sin lectura antes y después, igual en las dos corridas.

Se aplica con python3 -I aplicar_tanda4.py RAIZ [ARREGLO ...], que exige encontrar cada texto original exacto una sola vez y respeta el fin de línea de cada archivo (filtro_cbr.py está con CRLF en el disco). Pruebas nuevas en test_tanda4.py (va a pruebas/), 45 líneas OK. Las tablas se miden con tablas.py (cada edición sola y sin memoria) y se comparan con cmp.py.

## Cada arreglo por separado

| Arreglo | Archivo | Qué hace | Avisos que cambian | Filas que cambian de tabla | Rojo a verde |
|---|---|---|---|---|---|
| T4a | direccion.py y edicion.py | Con la dirección en rojo conserva la comuna si las dos lecturas dan la misma y cada una se comprueba en el aviso | 45 (solo ganan la comuna, sin dirección) | 8 a Descartadas por fuera de la RM | 0 |
| D4e | direccion.py | Una lectura agrega la esquina a la calle y la otra no. Queda la calle común | 2 (1267-2019) | 2 a Descartadas | 2 |
| D12 | numeros_texto.py | Un número en palabras pegado a una coma o un punto se lee completo ("Ciento Seis, del Primer Piso" daba 100) | 2 (12090-2024) | 2 de Excluidas a Descartadas | 2 |
| E1 | conjunto.py | Un nombre de edificio de 3 o 4 letras ya no se toma como subdivisión | 17 (solo texto) | 0 | 0 |
| E2 | conjunto.py | El nombre del edificio puede empezar con "de", "del", "la" | 4 (solo texto, 14456-2025) | 0 | 0 |
| R1 | filtro_cbr.py, filtros.py y modulo5_reporte.py | Corte del dominio en 2019. Pasa solo el dominio anterior a 2019 | 0 | 117 de la principal a Excluidas (48 causas) | 0 |

## T4a, detalle

19 avisos distintos en rojo en las 21 ediciones (20 con el republicado). En 17 las dos lecturas dan la misma comuna y se comprueba. No cumplen 4079-2023 (cada lectura dio otra comuna) y 29434-2019 (la comuna no está en su frase).

Cambian de tabla 4 causas, todas a Descartadas por fuera de la RM. 1267-2019 (Talca, principal, 9 y 10 de noviembre), 10750-2022 (Las Cabras, principal, 16 al 18 de octubre), 12090-2024 (Los Ángeles, de Excluidas, 9 y 10 de noviembre) y 8206-2024 (Puerto Varas, de Excluidas, 6 de octubre). La frase de la comuna de las 4 leída en las respuestas guardadas, es la del inmueble.

Se quedan en la principal y solo ganan la columna Comuna, con la dirección vacía y la misma Observación, 15341-2025 (Puente Alto), 3251-2021 (El Bosque), 19929-2024 (La Florida) y 11266-2023 (Pudahuel). Ninguna causa pasa de Descartadas o Excluidas a la principal.

El 9836-2023 de los derechos de agua queda fuera del alcance por decisión de Diego del 10 de noviembre (irrelevante para el proyecto). No está en rojo, así que T4a no lo toca.

## D4e y D12, detalle

D4e tiene un solo caso (n=1), 1267-2019. Queda en verde con "calle 6 Oriente 1600", comuna Talca, y sale de la principal por su comuna. Exige mismo número, unidad y comuna, y que la calle más larga sea la otra seguida de "esquina" o "esq".

D12 es un fallo del programa que no estaba en la lista. Apareció al mirar por qué el 12090-2024 seguía en rojo. palabras_a_cifras no reconocía "Seis," por la coma pegada y daba "100 Seis", así que las dos lecturas parecían unidades distintas (106 y 100). Un solo caso en los datos (n=1). Queda en verde con "Condominio de departamentos Las Orquídeas. Calle Comandante Luis Soto 759, Departamento Número 106", comuna Los Ángeles.

## E1 y E2, detalle

E1 cambia 5 causas, las 5 leídas en el texto del aviso. 755-2023 "Edificio ONIX", 3613-2024 "Edificio Fam", 16109-2023 "Edificio Open", 8963-2024 y 1556-2025 "Edificio Novo". Subdivisión queda como una o dos letras, o un código con algún número ("B", "AB", "5", "B2", "A-1"), más lo de antes (números en palabras, puntos cardinales, romanos, "B Dos").

E2 cambia 1 causa, 14456-2025 "Edificio de La Recoleta Urbano". Corrección durante la medición. La primera versión también cambiaba el 207-2026, donde el aviso dice "edificio de Moneda tres mil setenta y cuatro" y eso es una dirección. Se agregó que no vale si después del nombre viene un número. Tampoco vale si lo que sigue es Calle, Avenida, Pasaje, Comuna, Condominio y similares.

"Edificio B Dos" del 2929-2025 sigue como subdivisión, con su prueba.

## R1, detalle

Pedido de los abogados que usan el Excel, transmitido por Diego el 10 de noviembre. Con dominio inscrito en 2019 la deuda queda muy cerca del valor comercial, así que también se descarta. El corte _CBR_ANIO_CORTE de filtro_cbr.py pasa de 2020 a 2019. Pasa a la principal solo el dominio anterior a 2019. Cambian también los textos "anterior a 2020" de la Observación del año y los dos títulos del Excel ("dominio >= 2019" y "Excluidas por dominio 2019 o posterior").

2019 era el año más frecuente de la principal. 117 filas de 784 (48 causas distintas) pasan a Excluidas. En las ediciones del 2 al 10 de noviembre la principal baja así, cada edición sola y sin memoria, con todos los arreglos. 29 a 23, 23 a 20, 21 a 20, 37 a 35, 43 a 37, 52 a 45, 48 a 41, 34 a 23 y 30 a 22. Un rol con más de 5 propiedades sigue sin filtro de dominio. Una causa con dos inscripciones pasa si alguna es anterior a 2019.

## Todos juntos

Colores. 4 avisos de rojo a verde (1267-2019 y 12090-2024, dos ediciones cada uno), 0 de verde a rojo. Rojos 47 a 43. 0 carátulas y 0 conteos de remates cambiados. 24 direcciones verdes cambian solo de texto (los nombres de edificio de 6 causas, más las 2 que pasan a verde).

Tablas. 117 filas de la principal a Excluidas (R1), 5 de la principal a Descartadas por fuera de la RM (Las Cabras 3 y Talca 2) y 3 de Excluidas a Descartadas (Los Ángeles 2 y Puerto Varas 1). Principal 784 a 662, Excluidas 526 a 640, Descartadas 663 a 671, sin rol 21 igual. Ninguna fila entra a la principal.

Pruebas del proyecto en la copia con todo aplicado. test_caratula, test_conjunto, test_cortador, test_direccion, test_edicion, test_extraccion, test_filtros, test_mejora_ciclo2, test_navegacion_logica, test_tanda3 y test_tanda4, las 11 con TODO OK. Antes de los arreglos test_tanda4 no corre (falta comunas_del_rojo).

sha1 de los archivos con todo aplicado sobre HEAD e4a320b.
- motor/direccion.py 6945d1ba962a73f20ec5fab3985a7376a4a9b9fe
- motor/edicion.py 4e1690a0047421e1914cd06a42792b46d04758a7
- motor/numeros_texto.py 6f97a3600ce40c889212463c0af143fd7ab6d5a1
- motor/conjunto.py f8db0f8f9aadf6e08fba4f867a1c2297b5f15c5b
- motor/filtros.py 885c0d515d90800dfb22334ff77f67e3627296e3
- filtro_cbr.py 6d8c31723295911ee04a4ff5456b5fdd41d83fdd (con CRLF, como está en el disco)
- modulo5_reporte.py d119e66b74f7f6691ae913fad2490f39acb5807c

## Qué queda sin arreglo

Las lecturas de la IA que se contradicen (D4c, D4d y D11, decisión ya tomada). 755-2023 sigue sin comuna (el aviso no la trae junto a la dirección, sin revisar más). Los derechos de agua (fuera del alcance).
