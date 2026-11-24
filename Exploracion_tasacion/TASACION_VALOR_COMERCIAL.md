# Columna "Valor comercial" con inciti. Estado al 24 de Noviembre de 2026, 12:30

Documento único de este tema. Reúne lo probado, lo decidido y lo pendiente. Los anteriores (EXPLORACION_INCITI.md del 14 de Noviembre, EXPLORACION_ALTERNATIVAS.md y RESPUESTA_INCITI_24NOV.md del 24 de Noviembre) quedan como registro. Fase de diseño, sin cambios en el robot.

Marcas. (verificado) lo vi en la fuente o lo medí. (supuesto) falta comprobarlo. n es el número de casos.

## 1. Cómo funciona (verificado)

1. El robot ya lee de cada aviso la calle, el número, la unidad y la comuna (respuesta de Haiku, motor/direccion.py).
2. Búsqueda en inciti, POST https://api.inciti.com/api/searchengine/get_results_by_address con street, streetNumber, comunaCode (código del SII) y unitNumber. Devuelve el rol de avalúo, la dirección como la escribe el SII, el destino (HABITACIONAL, BODEGA, OFICINA y otros), los m² útiles, los m² de terreno en casas y las coordenadas. No trae valor ni datos de propietarios. **No se cobra** (no está en la lista de cobro del manual, y 26 consultas no movieron el contador de la cuenta, que siguió en 79 búsquedas y UF 1.939).
3. Si el aviso trae el rol de avalúo, sirve también get_results_by_rol con comunaCode y rol. Con 13101, 13134 o 13135 devolvió la misma propiedad de Santiago (n=1).
4. Tasación, POST https://api.inciti.com/api/get_appraisal con rol, comunaCode, propertyType (casa o departamento), usefulSquareMeters y, en casas, totalSquareMeters. Los m² salen de la búsqueda, nunca del aviso (los avisos traen m² en 1,3%, n=533). Devuelve valor de venta en UF y pesos, arriendo estimado, comparables del Conservador, avalúo fiscal en el PDF y un pdfUrl público. **Cuesta 0,0371 UF** por respuesta 200 (verificado en el log de la cuenta y en Facturación, el consumo subió de UF 1.939 a UF 2.013 con 2 tasaciones). Un 404 no se cobra. Tarda de 27 a 41 segundos (n=2).
5. Los servicios de búsqueda no están en el manual público y la key de staging responde 404 para ellos ("no tiene una respuesta de prueba para este endpoint"). Solo se pueden probar con la key de producción.

## 2. Resultados de las pruebas (verificado, archivos en INFORMES_REPORTES\inciti_*)

Búsqueda por dirección con 18 causas de la RM que imprimen su rol de avalúo, para saber la respuesta correcta.

| Resultado | Causas |
|---|---:|
| Rol exacto | 15 |
| No encontrada | 2 |
| Rol equivocado | 1 |

- Tolera abreviaturas, tildes y orden distinto ("Alcalde Pedro Alarcón" encontró "ALCALDE P ALARCON", "departamento A trescientos nueve" encontró "DP A 309").
- Arturo Prat 324 (22356-2024) no se encontró porque el SII inscribe el edificio como "ARTURO PRAT 318 338". Número dentro de un rango.
  Aviso revisado el 24 de Noviembre en El Mercurio del 14 de Noviembre, cuerpo D, página D15 (https://digital.elmercurio.com/2026/11/14/D/TB4MOSJR). Departamento 1809 del Edificio Concepto People "con acceso principal por calle Arturo Prat N° 324". El terreno del edificio da 32,90 metros de frente a Arturo Prat, por eso el SII lo inscribe con el rango 318 a 338. El aviso trae impreso el rol de avalúo 533-358, así que buscando primero por rol se habría encontrado.
- Elías Fernández Albano 492 depto 1011 A (2272-2025) no se encontró, sin causa identificada (supuesto, otro rango).
- Lo Errázuriz 1701 depto 107-A (12085-2024) devolvió la bodega 107 A, con otro rol y 3 m².
- La calle "Calle Uno" (14985-2025) solo se encontró al mandar "calle Uno" en el segundo intento.
- Almirante Latorre 125 (sin unidad) devolvió 5 resultados, el correcto primero.

Medición previa. De 271 inmuebles con calle en la RM y dos lecturas iguales de Haiku, 257 (95%) arman la consulta tal cual. 47 de los 271 (17%) son de Santiago, que tiene 3 códigos del SII (13101, 13134 y 13135).

Tasación (n=2)

| Propiedad | Valor | UF por m² útil | Referencia de LucasFinanzas |
|---|---|---:|---|
| Depto 29 m², Nataniel Cox 223 DP 2007, Santiago, rol 490-279 | 1.696,67 UF, $70.239.524 | 58,5 | Mediana de deptos en Santiago 55,7 |
| Casa 131 m² con 234 m² de terreno, Pje Asturcón 1588, Huechuraba, rol 89-39 | 7.160,45 UF, $296.432.383 | 54,7 | Mediana de casas en Huechuraba 47,5 |

Los dos PDF oficiales (13 páginas cada uno) no traen RUT, teléfonos, correos ni propietarios. El único nombre de persona es el del tasador, que es el de la cuenta. La página web muestra además un rango conservador y optimista (casa 6.588 a 7.733 UF), que el PDF no trae (supuesto que la API lo trae en algún campo, sin revisar).

## 3. Costo

Semana del 16 al 22 de Noviembre, 35 causas (contadas por Diego). 35 / 7 = 5 al día. 5 × 30 = 150 tasaciones al mes. 150 × 0,0371 = 5,6 UF al mes, unos $230.000 con la UF a $41.399. Es un techo, porque no se tasan las causas sin dirección comprobada, las que no son casa o departamento ni los 404. Según los abogados, de diciembre a febrero bajan los remates y las publicaciones, porque los jueces suelen tomarse vacaciones (dicho por Diego).

La cuenta JFNA la usa también la oficina (búsquedas de personas a 0,0200 UF y valorizaciones a 0,0371 UF). El plan es 1 UF mínima más 1 UF de adicionales, con sobreconsumo permitido.

## 4. Decisiones de Diego (24 de Noviembre)

- Bodegas y estacionamientos no van en la tasación (se mandan en 0, que es el valor por defecto según el manual).
- Las dos formas de entregar el PDF le gustan (adjunto en el correo o enlace en el Excel). Lo consulta con el abogado que revisa los correos.
- Los edificios con rango de números los consulta con el abogado que revisa las tasaciones.
- Cada tasación se guarda en una base de datos para acumular información y agruparla por comuna y sector.
- Cuando se detecte que un remate se republicó, avisar y dar el enlace de la tasación ya hecha, sin pagar otra.
- Quiere un conteo mensual en el Excel, "causas filtradas en lo que va del mes", solo de la principal.
- No hace falta revisar el contrato de inciti para guardar las tasaciones.

## 4b. Decisiones del abogado (transmitidas por Diego el 24 de Noviembre a las 12:23)

- Las causas de Las Condes (15108), Vitacura (15160) y Lo Barnechea (15161) **no se tasan**, pero siguen apareciendo en el Excel como hoy.
- **Sin PDF en el correo.** El enlace al informe va en el Excel.
- **Lo más importante.** Una columna "Resultado Valorización" con el valor de venta en UF y en pesos, por ejemplo "Venta UF 7.160,45 $296.432.383", para no tener que abrir el PDF.
- Decisión de Diego (12:26). El valor va en **dos columnas separadas**, una en UF y otra en pesos, para poder ordenar por valor. El enlace al PDF va en otra columna.
- Los edificios inscritos con un rango de números siguen sin respuesta.

## 5. Propuestas de Claude que siguen abiertas

- Protección. Si la búsqueda devuelve algo que no es habitacional (bodega, estacionamiento, oficina), no se tasa y la causa sale sin valor con una Observación. Con eso el caso de la bodega 107 A queda sin valor y no con un valor equivocado.
- Si la búsqueda devuelve varios resultados, aceptar solo el que calce con el número.
- Dos intentos de búsqueda, primero la calle sin "calle", "Pasaje" ni "Avenida" y después tal como la lee el robot.
- Vigencia de una tasación guardada antes de pagar otra (ejemplo, 6 meses). Sin decidir.
- La tabla de tasaciones en Supabase, solo agrega filas, con rol, comuna, dirección del SII, coordenadas, fecha, valor UF y pesos, m², destino y pdfUrl. Nunca datos de propietarios.

## 6. Pendientes, en orden

1. Respuesta del abogado sobre los edificios con rango de números (lo del PDF ya está respondido, va el enlace en el Excel).
2. Medir la búsqueda con más causas. Como es gratis, se puede correr sobre todas las causas de la principal de los Excel recientes para medir cuántas se encuentran y cuántas son habitacionales, sin costo. Diego baja los Excel a INFORMES_REPORTES.
3. Paso 2, diseño. Columnas (valor en UF y en pesos, enlace al informe), Observaciones para el abogado cuando no hay valor (no encontrada, no habitacional, sin comparables, sin dirección comprobada), conteo mensual, tabla de tasaciones, vigencia y aviso de republicado. Dónde va en la corrida, porque cada tasación tarda unos 30 segundos.
4. Key de producción como secreto nuevo de GitHub (INCITI_API_KEY) y en config.py. Hoy está en config.py como INCITI_API_KEY_PRODUCCION y INCITI_API_KEY_STAGING.
5. Paso 3. Escribir en copia, probar, fijar cifras esperadas y publicar con Claude Code, con decisión de Diego.
6. Commit de Exploracion_tasacion (los .md y los scripts de prueba) con Claude Code.
7. Borrar INFORMES_REPORTES\inciti_staging, inciti_produccion, inciti_aciertos, inciti_tasacion y _paq_aciertos.tgz cuando ya no se necesiten (lo importante está en este archivo).

## 7. Archivos de esta fase (D:\Mercurio\Exploracion_tasacion)

- prueba_inciti_staging.py, prueba_inciti_produccion.py, diag_inciti_rol.py, prueba_inciti_aciertos.py y prueba_inciti_tasacion.py. Leen la key de config.py sin imprimirla y borran datos de personas antes de guardar. Su filtro de datos de personas da falsos positivos ("pricePerSquareMeterUtil" y enlaces), sin datos reales borrados.
- medir_valor.py, medición de lo que traen los avisos.
- EXPLORACION_INCITI.md, EXPLORACION_ALTERNATIVAS.md y RESPUESTA_INCITI_24NOV.md, registro.
