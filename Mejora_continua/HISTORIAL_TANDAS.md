# Historial de tandas de mejora de la lectura

Creado el 11 de Noviembre de 2026 a pedido de Diego. Una ficha por tanda, en orden, con el problema que buscaba arreglar, cada cambio en palabras simples, el resultado medido y cómo salió su corrida real. Es el índice para acordarse de qué se hizo. El detalle fino de cada tanda está en su carpeta (Mejora_continua/ciclo2_tandaN), el catálogo de fallos en la sección 5 de GUIA_MEJORA_LECTURA.md y los commits en git. Al publicar una tanda nueva se le agrega su ficha aquí, y al revisar su corrida real se completa la línea "Corrida real". Lo anterior no se borra.

Cómo leer cada cambio. El código entre paréntesis es el tipo de fallo del catálogo de la guía. "Antes" es lo que hacía el programa y "Ahora" lo que hace desde la tanda.

---

## Ciclo 1 (30 de Octubre al 1 de Noviembre de 2026)

**Qué buscaba arreglar.** Los primeros fallos de dirección y carátula vistos en los Excel del 19 al 30 de Octubre, más la falta de evidencia para diagnosticar.

**Cambios.**
- (D1) Antes, dos números en palabras unidos por "y" se sumaban ("doscientos treinta y dos y doscientos treinta y cuatro" daba 466). Ahora se leen como dos números. Caso 20862-2024. Commit b652f2f.
- (C1 a C5) Antes, el código no reconocía cinco formas de escribir la carátula ("autos X con Y Rol", "Rol N, X con Y.", comilla de un solo lado, "Caratulado X/ Y" sin puntuación, "caratulada,,X/ Y"). Ahora las lee. Commit 03a77dd.
- (Captura diaria) Antes, el texto de los avisos se perdía al terminar cada corrida. Ahora se guarda cada día en Supabase, capturas/FECHA.zip. Commit 4c00652.

**Resultado medido.** En 1.145 avisos de 12 ediciones, 10 carátulas y 2 direcciones recuperadas y cero pérdidas.

**Corrida real.** 31 de Octubre con rojos 4 de 100 y 1 de Noviembre con rojos 5 de 94. Pasaron.

---

## Ciclo 2, tanda 1. Direcciones en rojo (8 de Noviembre de 2026)

**Qué buscaba arreglar.** Direcciones correctas que quedaban en rojo por reglas del programa demasiado estrictas, y una página del diario que se leía revuelta. La semana del 2 al 8 de Noviembre había 67 rojos en 709 avisos (9,4%).

**Cambios.**
- (D8) Antes, cuando dos secciones del diario empezaban a la misma altura, la página se cortaba mal y se revolvían los avisos (el 5 de Noviembre entraron al Excel 7 avisos que no eran remates). Ahora el orden de columnas no corta la página en ese caso.
- (D3) Antes, una frase copiada por la IA con comillas rectas en vez de curvas no se encontraba en el aviso. Ahora las comillas rectas y curvas cuentan como iguales. Las mayúsculas siguen sin perdonarse.
- (D4a) Antes, si una lectura traía el número del acceso vehicular de más ("Carmen 660" contra "Carmen 660 y 650"), las dos lecturas no coincidían. Ahora queda el número común.
- (D4b) Antes, si una lectura traía la unidad y la otra no, quedaba en rojo. Ahora queda la unidad si su frase se comprueba en el aviso, y si no, la dirección sin unidad.
- (D6) Antes, una unidad con letra y sin número ("Casa H") se rechazaba. Ahora se acepta.
- (D5a) Antes, una calle sin número ("s/n") se rechazaba. Ahora se acepta si la frase no trae ninguna marca de número.
- (D9) Antes, "departamento 2.708" se leía como 2. Ahora se lee el número con punto de miles.
- (D10) Antes, "vivienda número cuatro-A" no se leía. Ahora sí.
- (D1b) Antes, "cuatro y un" sumaba 5. Ahora no suma.
- (D5c) Antes, una sola palabra "mínimo" seguida de una lista a) b) hacía contar mal los remates. Ahora se cuentan bien.

**Resultado medido.** En 1.849 avisos de 19 ediciones, 21 direcciones de rojo a verde, cero de verde a rojo y cero carátulas perdidas.

**Corrida real.** 9 de Noviembre, rojos 5 de 109 (4,6%, antes 9,4%). Pasó.

**Commits.** cc8f5c1 (código) y a856eff (documentos). Carpeta ciclo2_tanda1.

---

## Ciclo 2, tanda 2. Formato de condominios y edificios (8 y 9 de Noviembre de 2026)

**Qué buscaba arreglar.** El programa trataba todo inmueble como calle, número y unidad. En un condominio la calle de la unidad, la entrada y el estacionamiento pueden ser distintos, y el abogado no veía eso.

**Cambios.**
- (F1 de formato) Antes, la celda Dirección traía solo calle, número y unidad. Ahora, cuando la dirección está comprobada, el aviso trae un remate y dice condominio o edificio, la celda dice el tipo (condominio de departamentos, de casas, solo condominio, o edificio), su nombre, la dirección, la calle interior, los estacionamientos y bodegas, y la entrada si es otra calle. Todo por código, sin IA, en el archivo nuevo motor/conjunto.py. "Conjunto habitacional" no cuenta como condominio.
- Cuatro correcciones al formato encontradas al revisar las 289 celdas una por una. Listas de estacionamientos con "y", un piso que no es estacionamiento, no repetir la unidad y no repetir "Edificio".

**Resultado medido.** En 1.849 avisos, 289 direcciones cambian solo de texto, cero colores, carátulas o remates movidos.

**Corrida real.** 10 de Noviembre, 19 de 19 filas con condominio o edificio salieron con el formato nuevo. Pasó. Quedaron dos nombres de edificio sin leer (ONIX y "de La Recoleta Urbano"), arreglados en la tanda 4.

**Commits.** 2b83a2d (código) y 981673f (documentos). Carpeta ciclo2_tanda2.

---

## Ciclo 2, tanda 3. Carátulas y fojas (9 y 10 de Noviembre de 2026)

**Qué buscaba arreglar.** La inscripción del dominio escrita de formas que el código no leía, con lo que la causa quedaba sin año y entraba a la principal con la Observación "No se encontró el año" (21 de 87 filas del 2 al 9 de Noviembre). También carátulas sin leer y causas de BancoEstado que se colaban a la principal.

**Cambios.**
- (Fojas F1 a F4 y F7) Antes, la inscripción solo se leía con la palabra "fojas". Ahora se lee también con "Fs.", "fs", "fjs", "f.", "números" en plural, la letra F junto a las fojas y "N.°", y "Reg." y "Prop." ya no cortan la frase antes del año.
- (C8 a C14, C3b y C5b) Antes, varias formas de carátula no se leían. Ahora se leen después de "expediente", con barra antes del rol, con la comilla sin cerrar, con el rol sin guion y con tres errores de tipeo del diario (punto y coma en vez de comilla, minúscula al inicio, "expediente cat.").
- (BE) Antes, una causa de BancoEstado entraba a la principal si su carátula quedaba vacía o decía "Banco de Estado". Ahora se reconocen esas formas, y con la carátula vacía se busca el banco en el aviso fuera de las frases de pago.

**Resultado medido.** En 1.958 avisos de 20 ediciones, 39 avisos ganan carátula y 327 ganan inscripción, cero pérdidas y cero cambios de color o dirección. 63 causas pasan de la principal a Excluidas por dominio reciente y 3 de BancoEstado a Descartadas. La Observación del año en la principal baja de 184 a 29.

**Corrida real.** 11 de Noviembre, rojos 4 de 78, y 2 de 12 filas de la principal con la columna Fs. vacía (antes 21 de 87). Pasó. Una de esas dos filas mostró un fallo nuevo, la fojas con punto (F10), pendiente.

**Commits.** a7ca807 (código) y e4a320b (documentos). Carpeta ciclo2_tanda3.

---

## Ciclo 2, tanda 4. Direcciones y corte de dominio 2019 (10 y 11 de Noviembre de 2026)

**Qué buscaba arreglar.** Inmuebles de otras regiones que entraban a la principal porque su dirección quedaba en rojo y se perdía también la comuna (1267-2019 de Talca). Dos direcciones en rojo por fallos puntuales y nombres de edificio que no se leían. Aparte, el pedido de los abogados de subir el corte del dominio.

**Cambios.**
- (T4a) Antes, con la dirección en rojo se perdía también la comuna, y la causa entraba a la principal como si fuera de la RM. Ahora se conserva la comuna si las dos lecturas dan la misma y se comprueba en el aviso, sin dar nunca la dirección. Así un inmueble de Talca va a Descartadas.
- (D4e) Antes, si una lectura agregaba "esquina 5 Norte" a la calle y la otra no, quedaba en rojo. Ahora queda la calle común.
- (D12) Antes, un número en palabras pegado a una coma ("Ciento Seis,") se leía como 100. Ahora se lee completo.
- (E1) Antes, un nombre de edificio de 3 o 4 letras (ONIX, Fam, Open, Novo) se tomaba como subdivisión y la celda decía solo "Edificio.". Ahora sale el nombre.
- (E2) Antes, un nombre de edificio que empieza con "de" ("de La Recoleta Urbano") no se leía. Ahora sí, salvo que después venga un número o una calle.
- (R1) Antes, pasaba a la principal el dominio anterior a 2020. Ahora pasa solo el anterior a 2019, porque con dominio de 2019 la deuda queda muy cerca del valor comercial (pedido de los abogados). La Observación del año y los títulos del Excel dicen 2019.

**Resultado medido.** En 2.054 avisos de 21 ediciones, 4 avisos de rojo a verde y cero de verde a rojo, cero carátulas o remates movidos. 117 filas de la principal pasan a Excluidas por el corte 2019 (48 causas), y 8 filas pasan a Descartadas por estar fuera de la RM.

**Corrida real.** 12 de Noviembre, log 116927650288. Rojos 4 de 79 (5,1%), sin errores. El corte 2019 funciona (títulos, Observación y dos causas con dominio 2019 en Excluidas) y 755-2023 sale "Edificio ONIX". Pasó. Corrección de lo esperado. 1267-2019 republicado cayó en Ya informadas por la regla de los 4 días, no en Descartadas. La revisión encontró un fallo nuevo, la inscripción toda en palabras (F11, 7170-2026), pendiente.

**Commits.** eb1d7d7 (direcciones), a990722 (corte 2019) y 6817729 (documentos). Carpeta ciclo2_tanda4.

---

## Ciclo 2, tanda 5. El ° impreso como un 3 (10 y 12 de Noviembre de 2026)

**Qué buscaba arreglar.** El 9 de Noviembre el diario imprimió "REMATE 2 3 JUZGADO", con el signo ° como un 3 suelto. El programa leyó el 3° Juzgado Civil cuando era el 2°, el abogado recibió el tribunal equivocado y la memoria quedó con una llave falsa. El mismo error rompió la inscripción "Fojas 15422 N 3 22232".

**Cambios.**
- (G1) Antes, "2 3 JUZGADO" se leía como el 3° Juzgado. Ahora, si el número es un 3 suelto y justo antes hay otro número de una o dos cifras, el tribunal es ese número anterior. No se confunde con un número de calle ("1409 3 Juzgado" sigue siendo el 3°) ni con una fecha.
- (G2) Antes, la inscripción "N 3 22232" no se leía. Ahora "N 3" vale como "N°" solo si después viene otro número.

**Resultado medido.** En 904 avisos distintos de 21 ediciones cambia 1 aviso y 1 causa (21355-2023 pasa al 2° Civil y gana su dominio de 2022, que lo manda a Excluidas). Cero colores, direcciones, carátulas o remates movidos. En la edición del 12 de Noviembre no cambia ninguno de los 79 avisos.

**Qué no arregla.** El 3 suelto dentro de la dirección ("Avenida Ecuador N 3 3866"), donde lee Haiku y el programa comprueba contra el aviso. La fila vieja de la memoria con el 3° se deja como está (decisión de Diego).

**Corrida real.** 13 de Noviembre a las 5:03, pendiente de revisar.

**Commits.** Pendientes. Carpeta ciclo2_tanda5.

---

## Listas para publicar, todavía sin publicar

**Respaldo de las respuestas de Haiku.** (S1) Ahora capturas/FECHA.zip guarda también las respuestas de Haiku de los avisos del día, así cada día se puede rehacer solo con su captura. (S2) Si estado/ia_respuestas.zip llega dañado, la corrida sigue en vez de caerse. Solo servidor/diario.py. Se publica después de la tanda 5. Carpeta respaldo_respuestas.

## Por medir (tanda de los sueltos)

Corte de los juzgados de Antofagasta (empate de nombres en buscar_corte), dirección de parcela cortada a 200 caracteres (8121-2024), causas voluntarias con rol con letra V (se descartan del todo, decisión de Diego), fojas con punto entre el número y "Número" (F10, 2334-2025), e inscripción toda en palabras (F11, 7170-2026). Después los dos mínimos de 28-2025.
