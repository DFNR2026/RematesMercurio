# Columna "Valor comercial" con inciti. Estado al 24 de Noviembre de 2026, 16:45

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

## 3. Costo y plan de inciti

### Lo que dice el contrato (verificado en los documentos que mandó el abogado el 24 de Noviembre)

Hay dos documentos y no dicen lo mismo. Vale el de Términos y Condiciones, que es el plan aceptado.

| | Propuesta comercial (10 de marzo de 2026) | Términos y Condiciones (12 de marzo de 2026), el que vale |
|---|---|---|
| Wallet para búsquedas e informes | UF 2 | **UF 1** |
| Insights | Insights Lite incluido. PRO+, Mercado Extra y Harry IA marcados "NO" | "Insights" UF 1 al mes (no dice Lite ni PRO+) |
| Total plan base mensual | UF 2 + IVA | UF 2 + IVA |
| Duración | 12 meses, después mes a mes | 6 meses desde el 1 de marzo de 2026, después mes a mes |

Precio por consulta en los dos. Búsqueda de Inmuebles UF 0,02, Búsqueda de Personas UF 0,02, Informe de Valorización UF 0,0371 e Informe Comercial UF 0,0371. Los precios no incluyen IVA. La integración API está incluida en todos los planes. Se factura el último día del mes con la UF del primer día del mes siguiente. Un cambio de plan pedido antes del día 26 rige desde el mes siguiente. Para terminar hay que pedir la baja por ticket con 10 días de anticipación.

Facturación de la cuenta (pantallazos de Diego) calza con los Términos y Condiciones. Facturación mínima UF 1 (el wallet), adicionales UF 1 (el módulo Insights) y sobreconsumo igual al consumo menos UF 1.

Las "27 valorizaciones" del plan son UF 1 dividido por UF 0,0371 (26,95). No son 27 valorizaciones gratis aparte. Es el mismo wallet de UF 1 que también gastan las búsquedas de personas y de inmuebles de la oficina. La oficina consumió más de UF 1 en cada uno de los últimos 6 meses (de UF 1,062 a UF 2,622), así que **el wallet ya se agota con el uso de la oficina y cada tasación del robot sería sobreconsumo a UF 0,0371 más IVA**.

Búsqueda de la API. Las 281 búsquedas de la API del 24 de Noviembre (26 de las pruebas y 255 de la cobertura) no movieron el contador, que siguió en 81 (verificado por Diego). No se cobran.

### Costo estimado del robot

Semana del 16 al 22 de Noviembre, 35 causas (contadas por Diego), unas 150 al mes. La cobertura dice que se tasaría un 85% fuera de Las Condes, Vitacura y Lo Barnechea. 150 × 0,85 = 128 tasaciones. 128 × 0,0371 = 4,7 UF al mes, con IVA 5,6 UF, unos $234.000 (UF a $41.399). Es un techo, porque la muestra de la cobertura son avisos de todas las tablas y no solo de la principal. De diciembre a febrero bajan los remates (dicho por los abogados).

### Costo con el wallet (corrección de Diego, 16:38, y ajuste de 16:42)

Diego aclara que las búsquedas de personas son uso propio del abogado y no entran en la cuenta del robot, y que abrir una cuenta aparte solo para propiedades no conviene (sumaría otro plan base). Se acepta. La forma limpia de medir es cuánto agrega el robot a la factura.
- La cuenta ya pasó la UF 1 del wallet todos los meses de los últimos seis (1.062 a 2.622, pantalla de Facturación). Por eso las unas 27 valorizaciones del wallet ya se gastan hoy y cada tasación del robot se cobra aparte.
- Costo que agrega el robot = (tasaciones del robot − valorizaciones que la oficina deja de hacer a mano) × 0,0371 UF + IVA. Cada tasación sale a unos $1.830 con IVA.
- Techo, si la oficina no hacía ninguna a mano, 128 × 0,0371 = 4,7 UF, con IVA 5,6 UF, unos $234.000 al mes. Baja con cada valorización a mano que se deja de hacer y con las tasaciones guardadas que se reutilizan.
- Diego (16:54) aclara que no hay un número claro de valorizaciones a mano, porque dependen de si la propiedad calza con el mandamiento. Se trabaja con el techo.
- Pregunta a inciti por el precio de PRO+, pendiente por decisión de Diego.

### Otros módulos

- Insights PRO+, Mercado Extra y Harry IA no están contratados (marcados "NO" en la propuesta, ausentes en los Términos y Condiciones). Su "ilimitado" vale solo si se contratan.
- Insights (incluido, UF 1 al mes). En la plataforma es ilimitado. En la API solo existe /get_insights_pro, que pide el módulo PRO+. Con el plan actual probablemente responde 403 (supuesto). Según el manual, una respuesta rechazada no se cobra y Insights PRO+ no cobra por consulta.
- Informe Comercial y Búsqueda de Personas son por RUT y no sirven para este tema (dicho por Diego).

### Confidencialidad (cláusula 7 de los Términos y Condiciones)

La información sobre el funcionamiento de la plataforma que recibe el usuario es confidencial y no se puede divulgar a terceros. Los servicios searchengine los entregó inciti por ticket y no están en su manual público. El repositorio es público y desde el commit dbbe1a9 los trae en los scripts y documentos de esta carpeta. Decisión de Diego (16:38), se deja como está, la cláusula apunta a competidores.

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
- Edificios con rango de números. Se busca primero por rol cuando el aviso lo trae. Si no se encuentra, el Excel dice "Tasación no encontrada" (decisión de Diego, 15:56).
- El abogado considera irrelevante el caso de los edificios con rango ("hilar muy fino"). No se trabaja más. El ticket de inciti se cierra solo con un agradecimiento (16:13).

## 5. Propuestas de Claude que siguen abiertas

- Protección. Si la búsqueda devuelve algo que no es habitacional (bodega, estacionamiento, oficina), no se tasa y la causa sale sin valor con una Observación. Con eso el caso de la bodega 107 A queda sin valor y no con un valor equivocado.
- Si la búsqueda devuelve varios resultados, aceptar solo el que calce con el número.
- Dos intentos de búsqueda, primero la calle sin "calle", "Pasaje" ni "Avenida" y después tal como la lee el robot.
- Vigencia de una tasación guardada antes de pagar otra (ejemplo, 6 meses). Sin decidir.
- La tabla de tasaciones en Supabase, solo agrega filas, con rol, comuna, dirección del SII, coordenadas, fecha, valor UF y pesos, m², destino y pdfUrl. Nunca datos de propietarios.

## 6. Pendientes, en orden (actualizado a las 16:20)

1. Diego corre prueba_inciti_cobertura.py (solo búsquedas, gratis, unas 200 a 400 consultas, de 3 a 5 minutos). Mide con 200 inmuebles de la RM de las ediciones guardadas cuántos se encuentran, cuántos se tasarían y, en los 18 con rol impreso, si la dirección da el mismo rol.
2. Diego revisa DISENO_VALOR_COMERCIAL.md (paso 2) y decide sus 6 puntos abiertos.
3. Paso 3. Escribir en copia, probar, fijar cifras esperadas y publicar con Claude Code, con decisión de Diego.
4. Decidir qué parte de Exploracion_tasacion entra al repositorio público (ver nota en el chat del 24 de Noviembre). Hoy está sin commit.

Hecho el 24 de Noviembre. ESTADO_PROYECTO.md anotado (16:10). Borradas las carpetas de prueba de INFORMES_REPORTES y el paquete temporal (16:20).

## 7. Archivos de esta fase (D:\Mercurio\Exploracion_tasacion)

- prueba_inciti_staging.py, prueba_inciti_produccion.py, diag_inciti_rol.py, prueba_inciti_aciertos.py y prueba_inciti_tasacion.py. Leen la key de config.py sin imprimirla y borran datos de personas antes de guardar. Su filtro de datos de personas da falsos positivos ("pricePerSquareMeterUtil" y enlaces), sin datos reales borrados.
- prueba_inciti_cobertura.py, medición de la búsqueda con 200 inmuebles (lista, sin correr).
- DISENO_VALOR_COMERCIAL.md, diseño del paso 2 para aprobar.
- medir_valor.py, medición de lo que traen los avisos.
- EXPLORACION_INCITI.md, EXPLORACION_ALTERNATIVAS.md y RESPUESTA_INCITI_24NOV.md, registro.

## Cierre del diseño (24 de Noviembre de 2026, 17:45)

- Regla para elegir la propiedad fijada con la corrida v2, sin más calibraciones (decisión de Diego). Detalle y cifras en DISENO_VALOR_COMERCIAL.md, sección 7b. Con esa regla se tasarían 145 de 178 inmuebles fuera de las comunas excluidas (81%). La regla vieja daba 151, pero 10 eran otra calle o una elección al azar.
- Decisiones de Diego del diseño en DISENO_VALOR_COMERCIAL.md, sección 7. Textos cortos en la celda del valor cuando no hay valor, sin volver a tasar pasados 6 meses (se muestra la tasación antigua en amarillo con su antigüedad), archivo estado/tasaciones.csv, sin tasar causas con más de una propiedad, costo del día en negrita en el correo de Diego con contador propio (27 de la base y luego cobro aparte), conteo del mes en el correo de Diego y no en la hoja Resumen, publicación en dos noches.
- F2890 del SII revisado (EXPLORACION_ALTERNATIVAS.md, sección 9). Sirve solo como respaldo por manzana. En pausa.
- Pregunta a inciti por el precio de PRO+, pendiente por decisión de Diego.
- Siguiente paso, el paso 3, solo con la decisión explícita de Diego.
- Paso 3 (24 de Noviembre de 2026, 18:12). Código en la rama tasacion de GitHub (commit 16dce6b), no en main. Ensayo del 24 sin tasaciones (todas las causas ya informadas), costo 0. Pausa hasta Diciembre por decisión de Diego, cuando rige el plan nuevo de inciti. En Diciembre se ajustan COSTO_UF y BASE_PLAN de motor/tasacion.py al plan nuevo.

