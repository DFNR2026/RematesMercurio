# Ciclo 2, tanda 5. El ° impreso como un 3 suelto. Medición en copia (10 de noviembre del 2026)

Sin tocar D:\Mercurio\motor. Medido en la nube de Claude sobre la copia que ya trae la tanda 4, con 21 ediciones, 2.054 avisos y 904 avisos distintos. Solo cambia motor/extraccion.py, que la tanda 4 no toca. Se aplica con python3 -I aplicar_tanda5.py RAIZ [G1] [G2]. Pruebas en test_tanda5.py (va a pruebas/), 15 líneas OK. Antes de los arreglos fallan 4.

## Qué pasa

El texto del diario trae a veces el signo ° como un 3 suelto. Es del diario y no del programa (el mismo aviso de 21355-2023 salió con "2 3 JUZGADO" el 9 de noviembre y con "2° JUZGADO" el 10). En las 21 ediciones aparece en 8 avisos distintos de las ediciones del 10 de octubre y del 9 y 10 de noviembre, en frases como "N 3 950", "7 3 piso" o "Ley N 3 21.389".

Banco. Corrección de lo anotado el 10 de noviembre en ESTADO_PROYECTO.md ("falló 1 de 4 veces en un tribunal"). Contado en los datos, el 3 suelto cae justo antes de la palabra Juzgado en 1 solo aviso de 904 (21355-2023 del 9 de noviembre), y en ese falló (n=1 de 1). En la inscripción rompe 1 aviso, el mismo ("Fojas 15422 N 3 22232").

## Arreglos

| Arreglo | Qué hace | Avisos que cambian | Otros cambios |
|---|---|---|---|
| G1 | Si el número del tribunal es un 3 suelto y justo antes hay otro número de una o dos cifras, el tribunal es el número anterior ("2 3 JUZGADO" es el 2°) | 1 (21355-2023 pasa de 3° a 2° Juzgado Civil de Santiago) | 0 |
| G2 | La inscripción acepta "N 3" como "N°" solo si después viene otro número | 0 avisos, 1 fila (21355-2023 gana su dominio de 2022 y pasa de la principal a Excluidas) | 0 |

Juntos, 1 aviso y 1 causa cambian. Cero colores, direcciones, carátulas o remates movidos. Las 12 pruebas del proyecto (con test_tanda4 y test_tanda5) dan TODO OK.

No se confunde con un número de calle ("1409 3 Juzgado" sigue siendo el 3°), con una fecha ("12/11 3 Juzgado") ni con "N 3 del Registro" (sin otro número después no se adivina). Todos con su prueba.

sha1 de motor/extraccion.py con la tanda 5 aplicada sobre e4a320b. cc89e94b8786d92647b8edb4843adb58ce6c2aff

## La llave equivocada en la memoria

El 9 de noviembre la causa quedó anotada en la memoria como 21355-2023 del 3° Juzgado Civil de Santiago. Esa fila no se borra (la memoria solo agrega). Con G1 la causa se anota desde ahora con el 2°. Efecto que queda, si vuelve a publicarse dentro de los 4 días siguientes al 9 de noviembre no se reconoce como ya informada. Ya pasó el 10 de noviembre sin daño (fue a Excluidas por su dominio de 2022).

## Qué no arregla

El 3 suelto en la dirección ("Avenida Ecuador N 3 3866", "departamento N 3 401-S"). Ahí lee Haiku y el programa comprueba contra el aviso, sin casos de dirección equivocada vistos.
