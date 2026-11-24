# Diseño de la columna "Valor comercial" (paso 2). Borrador del 24 de Noviembre de 2026

Propuesta para que Diego la apruebe o la corrija. No toca el robot. Las decisiones ya tomadas por Diego y el abogado están en TASACION_VALOR_COMERCIAL.md (secciones 4 y 4b). Lo marcado **(por decidir)** necesita la respuesta de Diego.

## 1. Dónde entra en la corrida

Hoy main.py lee el diario, filtra, anota la memoria y arma el Excel (verificado, main.py líneas 204 y 205, actualizar_historial y generar_reporte). La tasación entraría **entre el filtro y el Excel**, solo para las causas de la tabla principal. Un módulo nuevo, por ejemplo motor/tasacion.py, sin cambiar la lectura ni los filtros.

Para cada causa de la principal, en este orden.
1. Si la comuna es Las Condes, Vitacura o Lo Barnechea, no se tasa (decisión del abogado).
2. Si la dirección no quedó comprobada (en rojo o sin dato), no se tasa.
3. Si la propiedad ya tiene una tasación guardada y vigente, se reutiliza sin pagar.
4. Si el aviso trae el rol de avalúo, búsqueda por rol (gratis).
5. Si no lo trae, o no lo encuentra, búsqueda por dirección (gratis), primero la calle sin "calle", "Pasaje" ni "Avenida" y después tal como la lee el robot. Si devuelve varios resultados, el que calce con el número del aviso.
6. Si lo encontrado no es habitacional (bodega, estacionamiento, oficina, local), no se tasa.
7. Tasación /get_appraisal (0,0371 UF) con el rol, la comuna, casa o departamento, los m² útiles y, en casas, los m² de terreno que dio la búsqueda. Sin estacionamientos ni bodegas.
8. **Cada tasación se guarda en Supabase apenas llega**, antes del Excel. Así, si la corrida falla después y se repite a los 20 minutos, no se paga dos veces.

Protecciones.
- Si inciti no responde o da error, el Excel sale igual, sin valores y con su Observación. La tasación nunca detiene el correo.
- Un tope por corrida (por ejemplo 20 tasaciones) por si un día viene algo raro.
- La key va en un secreto nuevo de GitHub, INCITI_API_KEY, y en config.py. Nunca se imprime.
- No se guarda ni se muestra ningún dato de propietarios. La búsqueda y la tasación no los traen (verificado), y se guardan solo los campos de la lista de la sección 4.

Tiempo. Cada tasación tarda de 27 a 41 segundos (n=2). Con unas 5 causas al día serían de 2 a 4 minutos más por corrida (supuesto).

## 2. Cómo se ve en el Excel (hoja Remates, tabla principal)

Tres columnas nuevas entre "Fs." y "Observaciones".

| ... | Comuna | Fs. | Valor venta UF | Valor venta $ | Informe | Observaciones |
|---|---|---|---:|---:|---|---|
| ... | Huechuraba | ... | 7.160,45 | 296.432.383 | Ver informe | |
| ... | Las Condes | ... | | | | Sin tasación en Las Condes, Vitacura y Lo Barnechea, por decisión de la oficina. |
| ... | Santiago | ... | | | | Tasación no encontrada. |

- Los valores van como números, así se pueden ordenar de mayor a menor.
- "Ver informe" es un enlace al PDF de inciti.
- Las tablas de abajo (sin rol, ya informadas, excluidas, descartadas, oficinas y sitios) no llevan tasación.

## 3. Observaciones cuando no hay valor (textos para el abogado)

| Caso | Texto en Observaciones |
|---|---|
| No se encontró la propiedad | Tasación no encontrada. |
| Las Condes, Vitacura o Lo Barnechea | Sin tasación en Las Condes, Vitacura y Lo Barnechea, por decisión de la oficina. |
| Dirección no comprobada | Sin tasación, porque no se pudo leer bien la dirección del aviso. |
| No es casa ni departamento | Sin tasación, en los registros figura como bodega, estacionamiento u oficina. |
| inciti no tiene 3 ventas parecidas (404 que no se cobra) | Sin tasación, no hay suficientes ventas parecidas en la zona para calcularla. |
| inciti o internet fallaron | Sin tasación hoy, el servicio de tasación no respondió. Revise el informe de mañana. |
| Tasación reutilizada | Tasada el 24 de noviembre del 2026 (ver informe). |
| Remate republicado con tasación guardada | Este remate ya salió antes. Tasado el 24 de noviembre del 2026 (ver informe). |

**(por decidir)** Si "Tasación no encontrada" va en Observaciones, como se propone, o dentro de la columna del valor. En la columna impide ordenar por valor.

## 4. Tabla de tasaciones (memoria de tasaciones)

En Supabase, como la memoria de causas. Solo agrega filas, nunca borra ni cambia. Propuesta, un archivo estado/tasaciones.csv con su respaldo diario en respaldos/, igual que causas_ojv.xlsx.

Campos. Fecha de la tasación, causa (rol, año y tribunal con la llave de siempre), rol de avalúo, código y nombre de comuna, dirección del SII, coordenadas, casa o departamento, m² útiles y de terreno, valor de venta en UF y en pesos, valor de la UF usada, arriendo estimado en UF, avalúo fiscal si viene, enlace al PDF, cómo se encontró (por rol o por dirección) y el resultado (tasada, no encontrada, no habitacional, sin comparables, falla).

Usos.
- No pagar dos veces la misma propiedad (vigencia **(por decidir)**, propuesta 6 meses).
- Aviso de remate republicado con el enlace a la tasación ya hecha.
- Con el tiempo, promedios por comuna y sector (usando las coordenadas).

**(por decidir)** Si, en vez del archivo, va en una tabla de la base de datos de Supabase. El archivo sigue la forma en que el robot guarda todo hoy. La tabla sería más cómoda para consultas y promedios.

## 5. Conteo del mes

En la hoja Resumen, una línea "Causas nuevas en la tabla principal en lo que va de noviembre: X". Solo de la principal, sin descartadas, excluidas ni BancoEstado. La memoria de causas hoy no distingue la principal de las ya informadas, así que se propone un archivo pequeño, estado/principal_mes.csv, con la fecha y la llave de cada causa que entra a la principal. Para Noviembre se rellena una sola vez con los Excel ya enviados.

## 6. Lo que no cambia

La lectura, los filtros, la regla de los 4 días, la memoria de causas, el correo y sus horarios. Si se quita la key, el robot funciona exactamente como hoy.

## 7. Decisiones de Diego (24 de Noviembre de 2026, 17:22)

Lo de esta sección manda sobre lo escrito arriba en las secciones 2, 3, 4 y 5.

1. Cuando no hay valor, el texto va dentro de la celda del valor ("Valor venta UF") y no en Observaciones. Ejemplo, "Tasación no encontrada". La celda en pesos queda vacía. Decisión de Diego (17:34), todos los casos sin valor van con un texto corto en la misma celda.
   | Motivo | Texto en la celda del valor |
   |---|---|
   | No se encontró la propiedad | Tasación no encontrada |
   | Las Condes, Vitacura o Lo Barnechea | No se tasa en esta comuna |
   | Bodega, estacionamiento u oficina | No es casa ni departamento |
   | Más de una propiedad en la causa | Más de 1 propiedad en la causa, valorizar manualmente |
   | inciti sin ventas parecidas (404 que no se cobra) | Sin ventas parecidas para tasar |
   | Falla de inciti o de internet | Sin tasación hoy, falla del servicio |
   | Dirección del aviso no comprobada | Dirección no comprobada |
2. Vigencia de 6 meses. Decisión de Diego (17:34), si la tasación guardada tiene más de 6 meses el robot NO vuelve a tasar. Muestra la tasación antigua y dice qué tan antigua es. Muestra los valores de esa tasación con las celdas en amarillo, y en Observaciones dice "Esta propiedad se tasó el 3 de mayo del 2026, hace 7 meses. Se recomienda volver a valorizarla."
3. Las tasaciones se guardan en un archivo, estado/tasaciones.csv en Supabase, con respaldo diario. Solo agrega filas.
4. Causa con más de una casa o departamento. No se tasa. La celda del valor dice "Más de 1 propiedad en la causa, valorizar manualmente". Cómo detecta el robot esos casos se revisa en los datos guardados al empezar el paso 3.
5. El costo del día va solo en el correo de Diego, en negrita. Ojo, el robot no puede saber cuántas de las unas 27 valorizaciones del wallet usó la oficina, y la cuenta ya pasa la UF 1 todos los meses. Por eso el texto cuenta cada tasación del robot como cobro aparte (ver TASACION_VALOR_COMERCIAL.md).
   Decisión de Diego (17:26). El robot lleva su propio contador del mes y supone que nadie más usa las 27 valorizaciones de la base. Las primeras 27 del mes se informan como incluidas en el plan y desde la 28 como cobro aparte.
6. El abogado nunca usa la hoja Resumen. El conteo del mes no va en esa hoja. Se propone llevarlo al correo de Diego junto al costo. Si la hoja Resumen se elimina es otro cambio, fuera de este tema.

Publicación en dos noches. Primera, la tasación con sus columnas. Segunda, el conteo del mes en el correo de Diego, después de que la primera pase bien su corrida de la mañana.

## 7b. Regla para elegir la propiedad (fijada el 24 de Noviembre de 2026, 17:45)

Última calibración, por decisión de Diego. Es la regla de Exploracion_tasacion/prueba_inciti_regla_estricta.py (versión 2) y el robot la copia tal cual.
1. Si el aviso trae el rol de avalúo, se busca por rol. Si no, por dirección, con hasta tres formas de escribirla. Si inciti responde con error o vacío buscando con unidad, espera 3 segundos y reintenta una vez.
2. Solo cuenta lo HABITACIONAL. Nunca bodegas, estacionamientos, oficinas ni bienes comunes.
3. El número de la calle calza exacto, con su cero inicial. Solo si el SII no trae ese número exacto se acepta sin el cero.
4. El nombre de la calle tiene que parecerse, aunque el SII lo abrevie. Entre varias calles con el mismo número gana la que más se parece.
5. Si el aviso trae unidad, la del SII calza exacta, letras incluidas. Si solo calza el número y no la letra, queda dudosa y no se tasa.
6. Si el aviso no trae unidad, vale solo la propiedad del SII sin unidad (o con solo lote o sitio). Si hay varias, como en un condominio, no se elige ninguna.
7. Varias unidades iguales en el mismo edificio (mismo número, mismos metros, misma manzana) se tasan con cualquiera, porque dan el mismo valor.
8. Lo que no calza o queda dudoso va como "Tasación no encontrada" y no se cobra.

Resultado de la corrida v2 (verificado, INFORMES_REPORTES/inciti_regla_estricta_v2, 230 búsquedas sin cobro). De 184 inmuebles distintos, 6 son de las comunas excluidas. De los 178 restantes se tasarían 145 (81%), 31 quedan como "Tasación no encontrada" y 2 como dudosas. Contra la regla vieja (151), 142 quedan igual, 3 se arreglan (La Capilla 1415 casa 23 en vez de bienes comunes, Lo Errázuriz 1701 departamento 107 en vez de la bodega, El Bosque 091) y 10 salen. De esos 10, 2 eran otra calle (Calle Central por Padre Alberto de Agostini, Pasaje 17 por Pasaje ocho), 6 eran una elección al azar entre varias casas o edificios (Luciérnagas 5677 A a H, El Portal 6450 casas 71 a 80, Independencia 4599 en 5 edificios, Travesía 8721 en 3 edificios, Camino al Volcán 29016 en 3 lotes, Santa María 571 departamento 501 A o B) y 2 quedan dudosas (Julio Arangua Sur 304 A, Blanco Encalada 1823 C-407). La regla vieja cobraba por esos 10 sin saber si era la propiedad correcta.
Fallas pasajeras de inciti. En 13 búsquedas inciti no respondió (sin código de respuesta). Con el reintento se recuperaron 12 (verificado en el campo estados del .json).

## 8. Paso 3 (después de aprobar)

Escribir motor/tasacion.py y los cambios de main.py, modulo5_reporte.py y servidor/diario.py en una copia fuera de D:\Mercurio. Pruebas con respuestas de inciti grabadas (sin cobro). Una corrida de ensayo en GitHub (el correo va solo a Diego) con unas pocas tasaciones reales. Cifras esperadas fijadas por escrito antes de publicar. Commit y push con Claude Code, un cambio por noche, después de que la anterior pase su corrida real.
