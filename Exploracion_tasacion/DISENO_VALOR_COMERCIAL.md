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

## 7. Lo que falta decidir (Diego)

1. "Tasación no encontrada" en Observaciones o en la columna del valor.
2. Vigencia de una tasación guardada (propuesta 6 meses).
3. Archivo CSV o tabla de base de datos para las tasaciones.
4. Qué hacer con una causa que remata varias propiedades. Propuesta, tasar cada casa o departamento hasta 3 y mostrar la suma, con la Observación "Suma de N propiedades".
5. Si el costo de cada día (tasaciones hechas, 0,0371 UF cada una) va solo en el correo a Diego.
6. Si se publica todo junto o en dos noches (primero la tasación y las columnas, después el conteo del mes).

## 8. Paso 3 (después de aprobar)

Escribir motor/tasacion.py y los cambios de main.py, modulo5_reporte.py y servidor/diario.py en una copia fuera de D:\Mercurio. Pruebas con respuestas de inciti grabadas (sin cobro). Una corrida de ensayo en GitHub (el correo va solo a Diego) con unas pocas tasaciones reales. Cifras esperadas fijadas por escrito antes de publicar. Commit y push con Claude Code, un cambio por noche, después de que la anterior pase su corrida real.
