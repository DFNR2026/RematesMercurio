# Exploración de la tasación comercial con la API de inciti

Fase exploratoria pedida por Diego el 14 de Noviembre de 2026. Sin cambios en el robot. Objetivo, saber si se puede agregar una columna "Tasación comercial" a las causas que ya quedan en el Excel.

## Qué se revisó

El manual completo de https://api.inciti.com/ (abierto en el navegador, porque la página se arma con JavaScript), el código de la página (un solo archivo, assets/index-Dc5YcyO5.js, 303 KB) y las respuestas de ejemplo completas de cada servicio. Además las capturas de la plataforma que mandó Diego (Informe Valorización, pasos 1 y 2) y las 10 causas de la tabla principal del Excel del 14 de Noviembre.

## Lo verificado en la API

- URL base https://api.inciti.com/api. Todo es POST con cuerpo JSON y el header X-API-Key. Hay una key de producción y otra de staging. Staging responde siempre el ejemplo del manual y no cobra.
- Hay exactamente 5 servicios. /get_property_data, /get_owner_data, /get_appraisal, /get_tenant_report y /get_insights_pro. El código de la página no nombra ningún otro, ni de búsqueda por dirección, ni de geocodificación, ni de autocompletar.
- Ningún servicio recibe una dirección. /get_property_data y /get_appraisal piden el rol de avalúo del SII (manzana-predio) y el código de comuna del SII. /get_insights_pro recibe polígonos de coordenadas, pero entrega un estudio de mercado de la zona y no la tasación de una propiedad.
- /get_appraisal es el mismo "Informe Valorización" de la plataforma. Pide rol, comunaCode, propertyType (casa, departamento, oficina o local) y usefulSquareMeters, más totalSquareMeters obligatorio en casas. Opcionales dormitorios, baños, estacionamientos y bodegas. Entrega valor de venta en UF y en pesos (sale.propertyValueUF y sale.propertyValueCLP), valor por metro, estacionamientos y bodegas aparte, arriendo, comparables del Conservador y de avisos, y un PDF público. Responde 404 si hay menos de 3 ventas comparables.
- /get_property_data, con rol y comuna, trae los datos del SII. Entre ellos utilSurface (metros útiles), totalSurface, constructions con constructionSurface y año, grounds (terreno), useType, avalúo fiscal, coordenadas, si es condominio, y el historial de ventas del Conservador con fojas, número y año de cada inscripción. Trae también propietarios con RUT, teléfonos y correos.
- Cobro por consulta en /get_property_data y /get_appraisal según el plan, solo las respuestas 200. Hasta 100 consultas por minuto.

## Lo que muestra la plataforma (capturas de Diego)

El Informe Valorización tiene 5 pasos. Tipo, Dirección, Verificación, Datos adicionales (metrajes y comodidades) y Resultado. El paso 2 busca "por dirección o por su rol de avalúo". O sea, inciti sí convierte una dirección en una propiedad del SII, pero lo hace dentro de su plataforma y no lo publica en la API.

## Emulación con el Excel del 14 de Noviembre (10 causas de la principal)

| Causa | Dirección | Comuna | Rol de avalúo en el aviso | Metros en el aviso |
|---|---|---|---|---|
| 15634-2022 | Pasaje Tambillo 3629 | Puente Alto | No | No |
| 3029-2026 | calle Los Ciruelos Oriente 9266 | La Florida | No | No |
| 13136-2022 | Santo Domingo 1161, departamento 808 | Santiago | 210-636 | No |
| 14911-2024 | calle Las Tinajas 5421 | La Florida | No | No |
| 4920-2023 | Rojas Magallanes 2437, departamento 401 | La Florida | No | No |
| 12754-2024 | Avenida Irarrázaval 2401, oficina 520 | Ñuñoa | No | No |
| 6266-2024 | Presidente Riesco 6161, departamento 23 | Las Condes | No | No |
| 9057-2025 | calle Club Santa Filomena 2085 | Buin | No | No |
| 8225-2025 | Avenida Circunvalación 3073 | Melipilla | No | No |
| 22356-2024 | Arturo Prat 324, departamento 1809 | Santiago | 533-358 | No |

Con la API publicada hoy se podrían tasar 2 de 10. Para esas 2 el camino sería /get_property_data para sacar los metros y el tipo, y después /get_appraisal, dos consultas cobradas por propiedad. 13136-2022 además es de Policía Local y desde la tanda 7 se elimina. En las 14 ediciones guardadas, 27 de 225 avisos distintos de la principal traen el rol de avalúo (12%) y 1 trae metros.

## Conclusión

La tasación de inciti sirve para lo que se busca, y los metros cuadrados no son problema, porque /get_property_data los entrega desde el SII. Lo que falta es una sola pieza, pasar de la dirección que el robot ya lee al rol de avalúo. La plataforma lo hace y la API no lo ofrece. Sin esa pieza la columna quedaría vacía en cerca de 9 de cada 10 filas.

## Preguntas para inciti

1. Si la API tiene, o puede tener, una búsqueda por dirección y comuna que devuelva el rol de avalúo, como el paso 2 del Informe Valorización.
2. Si pueden buscar la propiedad por su inscripción del Conservador (fojas, número y año), que el robot lee en la mayoría de los avisos.
3. Cuánto cuestan /get_property_data y /get_appraisal por consulta en el plan de la cuenta.

## Reglas si se avanza

No guardar ni mostrar los datos de propietarios (RUT, teléfonos, correos). La key vive solo en config.py y en los secretos de GitHub. Probar todo primero con la key de staging. La tasación es un paso nuevo para las causas que ya quedaron en el Excel, con decisión de Diego antes de publicarla.
