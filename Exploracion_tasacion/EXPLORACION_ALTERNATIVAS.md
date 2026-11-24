# Exploración de fuentes para la columna "Valor comercial"

Fase exploratoria pedida por Diego el 24 de Noviembre de 2026, mientras inciti responde el ticket (enviado el 24 de Noviembre a las 00:50). Sin cambios en el robot. Complementa EXPLORACION_INCITI.md.

Marcas. (verificado) quiere decir que lo vi en la fuente o lo medí. (supuesto) quiere decir que lo deduzco y falta comprobarlo.

## 1. Lo que traen los avisos (medido)

Medido el 24 de Noviembre en la nube con el código de ea0f43a, sin IA, sobre las 12 ediciones que quedan en el disco (banco_pruebas del 1 de Septiembre y del 6 al 14 de Octubre, Capturas del 14 al 18 de Octubre). Son 533 avisos distintos con rol, de todas las tablas y no solo de la principal.

| Dato en el aviso | Avisos | % |
|---|---:|---:|
| Inscripción del Conservador leída por el robot | 527 | 98,9 |
| Mínimo de la subasta leído por el robot | 533 | 100 |
| Rol de avalúo del SII | 49 | 9,2 |
| El aviso dice que el mínimo es el avalúo fiscal | 38 | 7,1 |
| Nombra una tasación cerca del mínimo (varias son "tasación fiscal") | 26 | 4,9 |
| Tasación pericial o perito | 3 | 0,6 |
| Metros cuadrados | 7 | 1,3 |
| Dice departamento | 255 | 47,8 |

El 9,2% calza con el 12% medido el 14 de Noviembre solo en la principal (n=225). Que el mínimo sea casi siempre el avalúo fiscal o una fracción de él es (supuesto, por cómo se fijan los mínimos en los juicios). El aviso lo dice solo en 7 de cada 100 (n=533). Sin rol ni metros, ninguna fuente que pida esos datos sirve sola. Hace falta un puente desde la dirección.

## 2. Los cinco sitios que encontró Diego

| Sitio | Qué es | ¿Sirve? |
|---|---|---|
| propiv.com | No cargó (no respondió a la lectura automática) | Sin evaluar |
| lookdata.cl | Integra ventas de ecommerce (Mercado Libre, Falabella, Paris) con el ERP de una tienda | No, no es inmobiliario |
| chilepropiedades.cl | Portal de avisos. Sin API, sin tasación, sin precios por m² | No |
| propiedades.emol.com | Portal de avisos. Su robots.txt prohíbe la lectura automática | No |
| aguilainmobiliaria.cl | Portal de avisos con un "índice Aguila" mensual de mediana UF/m² por tipo y comuna, sin cifras públicas ni API | No como fuente automática. Son precios pedidos y sacarlos sería scraping |

Los portales de avisos quedan fuera por la regla del prompt maestro (no se tasa con scraping de portales) y porque muestran precios pedidos y no pagados.

## 3. El hallazgo principal, el SII publica el puente

El sitio de Transparencia del SII ofrece dos descargas (verificado, sii.cl/destacados/transparencia).

**Detalle Catastral por comuna.** Se baja con RUT y Clave Tributaria, por comuna o nacional, con información vigente e histórica. Trae un registro por rol de avalúo con dirección o nombre del predio, avalúo fiscal, contribución, destino y superficie de terreno, y otro archivo con cada línea de construcción con su superficie en m², año, material, calidad y destino. **No trae RUT ni nombre del propietario** (verificado, estructura_detalle_catastral.pdf). Que sea gratis hoy es (supuesto). Resoluciones de 1999 y 2005 le ponían tarifa, y la página actual solo dice "Descarga".

Con este archivo se puede pasar de la dirección que el robot ya lee al rol de avalúo, sin scraping y sin la API de nadie, y además sale la superficie construida y el avalúo fiscal. Que la búsqueda por dirección calce bien es (supuesto). Las direcciones del SII vienen abreviadas (por ejemplo "PJ", "AV", "DP") y hay que medirlo.

**Transferencias de bienes raíces (F2890).** Archivo público sin clave (F2890_30-10-2026.zip). Es lo que notarios y conservadores informan de cada compraventa. Según CIPER, el F2890 trae rol, precio y fecha. Grupo Colibrí y LucasFinanzas dicen usar las compraventas del SII hasta septiembre de 2026. Qué columnas trae el zip público es (supuesto). No lo pude bajar desde la nube de Claude porque la red lo bloquea.

Si el zip trae rol y monto, para cada causa se vería **el último precio pagado por esa misma propiedad**, y también se podría calcular la mediana UF/m² de cada comuna de la RM, sin depender de terceros.

## 4. Fuentes de UF/m² por comuna (vía analítica)

| Fuente | Qué da | Cobertura RM | Actualización | Costo | Notas |
|---|---|---|---|---|---|
| LucasFinanzas, herramientas de precio del m² | Mediana UF/m² **construido** de lo pagado, con rango P25 a P75 y ventas por comuna y barrio. Deptos (56.068 ventas) y casas (37.132), abril 2025 a marzo 2026 | 33 comunas en deptos y 34 en casas, solo Gran Santiago con 30 o más ventas. Faltan Buin, Melipilla, Colina, Lampa, Talagante y otras | Una vez al año | Gratis, con tabla en Markdown | Sin licencia escrita. Para usarla en un producto hay que pedir permiso |
| Cálculo propio con el F2890 del SII | Lo mismo, pero hecho por nosotros con la fuente oficial | Las 52 comunas, si el zip trae comuna, monto y superficie | Cada vez que el SII publica | Gratis | Depende de las columnas del zip |
| inciti /get_insights_pro | Estudio de mercado de un polígono | Toda | Sin dato | Sin dato | Requiere coordenadas. No probado |

La mediana de la comuna mezcla todo. El rango típico en Santiago va de 41,2 a 82,5 UF/m² y en Ñuñoa de 67,0 a 94,8 (verificado, LucasFinanzas). Multiplicar por los m² da un valor de referencia con un margen de cerca de 25% hacia arriba o hacia abajo, no una tasación (supuesto, sale del ancho del rango).

## 5. Otras APIs o servicios encontrados

| Servicio | Qué ofrece | Entrada | Costo | Riesgo |
|---|---|---|---|---|
| Data Inmobiliaria (datainmobiliaria.cl) | 9,6 millones de roles, compraventas desde 1998, avalúo, precios por m² y "tasación simple" en el plan Profesional Plus. REST API | Rol. No dice si busca por dirección | Plan Oficina $99.990 al mes más IVA con 600 créditos de API | Entrega nombre y RUT del dueño en planes pagados, habría que no pedirlos ni guardarlos |
| Propiteq | Mapa con valor comercial estimado de casas y deptos, AVM con datos del SII y del CBR. Un directorio dice "SaaS + API" | Sin documentación pública | Unos $10.000 por informe detallado según LucasFinanzas | API sin ver |
| HomeSpotter | Plataforma "API-first" con valorizaciones e historial del CBR | Roles | Sin dato | Sin documentación pública |
| HousePricing | AVM para bancos (revalorizó la cartera de Banco Falabella) | Sin dato | SaaS por volumen | Orientado a empresas grandes |
| RolIA (Grupo Colibrí) | Conecta Claude o ChatGPT a 9,1 millones de compraventas del SII y al catastro | Preguntas en lenguaje natural | 15 consultas gratis al mes | Hecho para chat, no para el robot |
| TOCTOC tasación online | Tasación web por propiedad | Web | Cerca de $5.000 (dato de 2022) | Sin API, solo uso manual |
| API de Mercado Libre (Portal Inmobiliario) | API oficial de inmuebles | Orientada a vendedores que publican | Sin dato | Precios pedidos. No sirve para tasar |
| inmodata (subastafacil) | API por dirección, código postal y referencia catastral | Formato español | Sin dato | No es de Chile, se descarta |

## 6. Avalúo fiscal multiplicado por un factor (vía más simple)

El avalúo sale del Detalle Catastral (o del aviso, en el 7% que lo dice). Según HousePricing, en la mitad de las casas el avalúo es entre 36% y 58% del precio de venta, cerca de 70% en un depto de Santiago centro y cerca de 47% en Providencia o Las Condes. El SII usó un factor 0,6 en el reavalúo de 2022 para dejar el avalúo bajo el valor comercial. Dividir por un factor fijo puede errar por el doble entre dos propiedades parecidas. Sirve como piso, no como valor comercial.

## 7. Cómo se combinan

| Ruta | Pasos | Datos | Cobertura esperada | Costo por causa | Precisión |
|---|---|---|---|---|---|
| A. SII más inciti | Dirección a rol con el Detalle Catastral, luego /get_appraisal con rol y m² | Dirección, comuna, tipo | Lo que calce la dirección (supuesto alto en verdes) menos los 404 de inciti | 1 consulta cobrada | La mejor, con comparables |
| B. SII más F2890 | Dirección a rol, último precio pagado por ese rol | Igual | Solo las propiedades vendidas en los años que cubra el zip (supuesto, menos de la mitad) | Gratis | Buena si la venta es reciente |
| C. SII más UF/m² | Dirección a rol, m² construidos por mediana de la comuna | Igual | Lo que calce la dirección | Gratis | Referencia con un margen de cerca de 25% |
| D. Avalúo por factor | Avalúo dividido por 0,5 a 0,6 | Avalúo | Igual que C | Gratis | Piso, con mucho error |
| E. Data Inmobiliaria | Su API con el rol | Rol | Depende de si busca por dirección | Desde $99.990 al mes | Sin probar |

Las rutas A, B y C comparten el primer paso, que no depende de inciti y se puede probar en copia. Si el puente funciona, C y D se pueden usar desde el primer día gratis, y A se suma si inciti responde con un precio razonable.

## 8. Lo que falta para decidir

1. Que Diego baje del sitio de Transparencia del SII el zip F2890 (público) y el Detalle Catastral de 3 a 5 comunas donde salen muchas causas (por ejemplo Santiago, La Florida, Puente Alto, Ñuñoa y Maipú). Lo del SII se baja a mano y de vez en cuando, nunca desde el robot ni con su clave en GitHub.
2. Con eso, medir en copia cuántas direcciones de las causas de la principal guardadas calzan con un rol y si el zip F2890 trae rol, monto y superficie.
3. La respuesta de inciti sobre la búsqueda por dirección y el precio.
4. Si se usa la tabla de LucasFinanzas, pedirle permiso por escrito.

## Fuentes

- SII, sitio de Transparencia, https://www.sii.cl/destacados/transparencia/index.html
- SII, estructura del Detalle Catastral, https://www.sii.cl/bbrr/descargas/estructura_detalle_catastral.pdf
- CIPER, falta de transparencia del SII en el reavalúo, https://www.ciperchile.cl/2022/06/05/la-falta-de-transparencia-del-sii-en-reavaluos-y-contribuciones/
- LucasFinanzas, precio del m² de departamentos, https://www.lucasfinanzas.cl/herramientas/precio-m2-departamentos-santiago/
- LucasFinanzas, precio del m² de casas, https://www.lucasfinanzas.cl/herramientas/precio-m2-casas/
- Data Inmobiliaria, https://datainmobiliaria.cl/
- Grupo Colibrí, avalúo fiscal contra precio real, https://www.grupocolibri.cl/blog/avaluo-fiscal-vs-precio-real-terreno
- Portal Innova, HousePricing sobre avalúos, https://portalinnova.cl/?p=261721
- SII, oficio a la Comisión de Hacienda del Senado (factor 0,6), https://www.sii.cl/destacados/novedades/Oficio_Comision_Hacienda_Senado_300625.pdf
- Medición propia, script medir_valor.py (copia en esta carpeta)

## 9. Revisión del F2890 del SII (24 de Noviembre de 2026, 17:00)

Se leyó desde el Chrome de Diego, en memoria y sin guardar el archivo en el disco, el zip público F2890_30-10-2026.zip del sitio de Transparencia del SII (84,8 MB comprimido, un solo .txt de 416 MB, publicado el 3 de Noviembre de 2026). Todo lo que sigue está verificado contra ese archivo.
- Columnas. COMUNA, MANZANA, PREDIO, FECHA_INSCRIPCION, FECHA_ESCRITURA, MONTO_PESOS, MONTO_UF. El rol es MANZANA-PREDIO. No trae dirección, metros, tipo de propiedad ni datos de personas. El monto viene en pesos o en UF, según la venta.
- Tamaño. 9.219.581 ventas de todo Chile, 347 comunas. Unas 340.000 a 470.000 por año desde 2015, y 201.420 en 2026 hasta octubre. Hay fechas mal escritas (años como 2099 o 9905), pocas.
- Nombres. Santiago viene partida en SANTIAGO CENTRO, SANTIAGO OESTE y SANTIAGO SUR, más SAN JOSE MAIPO y TIL-TIL. Hay que traducir los nombres.
- Cruce con las 152 propiedades tasables de la prueba de cobertura. 126 tienen al menos una venta registrada (las 21 de Santiago, San José de Maipo y Til Til no se cruzaron por el nombre). La última venta de esa misma propiedad es antigua en casi todas. Solo 3 de las 126 se vendieron en 2024 o 2025, y la mayoría entre 2010 y 2022. Calza con que se rematan propiedades compradas hace años.
- Por manzana. De las 130 manzanas de esas propiedades, 114 tienen ventas desde 2024 (la mitad tiene 13 o más). En los edificios la manzana suele ser el mismo edificio.

Conclusión. El último precio de la misma propiedad casi nunca sirve, porque es viejo. Lo que sí sirve es el precio de las ventas recientes de la misma manzana. Sin metros en el F2890, la mediana sería en UF por venta y no en UF/m², salvo que los metros de cada rol se saquen de otra fuente (el Detalle Catastral del SII o la búsqueda gratis de inciti). Queda como posible respaldo o comparación de la tasación de inciti, no como reemplazo.
