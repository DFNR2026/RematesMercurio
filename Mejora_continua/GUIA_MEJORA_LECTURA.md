# Guía de mejora continua de la lectura de avisos de remates (dirección y carátula)

Creada el 6 de Noviembre de 2026 a pedido de Diego. Guarda la experiencia y el método para mejorar la lectura de la dirección y de la carátula de los avisos de remates de El Mercurio, para que no se pierda en los chats y sirva también para D:\Agendar_Remates. Se actualiza al cerrar cada ciclo (sección 7). Está en git desde el 6 de Noviembre, para que quede respaldada y con historial. Corrección del 6 de Noviembre. La primera versión decía que quedaba fuera de git por traer roles de causas. Eso estaba mal. Los avisos de remates salen en un diario público y sus datos (roles, carátulas, partes, direcciones) son públicos siempre (decisión de Diego). No se deben tratar como confidenciales.

Advertencia para Agendar_Remates. El motor del Mercurio vino de Agendar el 17 de Octubre, pero desde entonces cada proyecto cambió por su lado. Antes de aplicar cualquier cosa de esta guía allá, comparar archivo por archivo (motor/direccion.py, motor/extraccion.py, motor/numeros_texto.py, motor/ia_comun.py y sus pruebas). Nunca asumir que son iguales.

## 1. Cómo funciona la lectura (Mercurio, al 6 de Noviembre)

La carátula (demandante con demandado) la lee SOLO el código, con expresiones regulares, en motor/extraccion.py caratula(). Nunca pasa por la IA. Si no encuentra ninguna deja el dato vacío, y si encuentra dos distintas no elige ninguna.

La dirección la lee Claude Haiku dos veces por aviso (motor/direccion.py). Cada lectura trae la calle, el número, la unidad, la comuna y la frase exacta del aviso de donde sacó cada dato. Después el código comprueba todo contra el texto. La frase debe estar en el aviso (motor/ia_comun.py buscar_frase, que solo perdona diferencias de espacios), el número debe estar en su frase en cifras o en palabras (motor/numeros_texto.py), y las dos lecturas deben coincidir. Si todo calza queda en verde. Si algo no calza queda en rojo, sin dirección.

Las respuestas de Haiku se guardan por huella (modelo, versión de las instrucciones, cantidad de remates y texto del aviso). Si el mismo aviso vuelve otro día no se le pregunta de nuevo. Cambiar INSTRUCCIONES o VERSION_INSTRUCCIONES invalida todas las respuestas guardadas y obliga a pagar de nuevo.

En el Excel el abogado no ve el motivo del rojo. motor/filtros.py traduce cualquier rojo a "No se pudo comprobar la dirección" y cualquier falla de carátula a "No se pudo leer la carátula". El motivo de fondo solo se ve reproduciendo el aviso (sección 3).

## 2. Principios que no se negocian

1. Nunca inventar. Un dato vacío con su Observación es mejor que uno equivocado.
2. La IA nunca tiene la última palabra. Todo lo que dice se comprueba contra el texto del aviso.
3. La Observación no va a desaparecer nunca del todo. Es la red de seguridad. Lo que se arregla son los fallos del programa. Los fallos de la IA y los avisos mal escritos van a seguir llegando a esa red, y está bien.
4. Concluir del total y nunca del último caso. Cada tipo de fallo lleva su n y se suma a la bitácora sin borrar lo anterior. Si un registro estaba mal, se anota la corrección.
5. Separar lo verificado de lo supuesto en cada afirmación.
6. Una variable por prueba, y un cambio de código por noche después de que el anterior pasó su corrida real.

## 3. El ciclo, paso a paso

1. Juntar evidencia. Desde el 2 de Noviembre el robot sube cada día capturas/FECHA.zip a Supabase (texto de las páginas de remates, navegacion.json y salida de main.py). Las respuestas de Haiku están en estado/ia_respuestas.zip y los Excel en informes/. Diego los baja desde el panel (Storage, bucket mercurio), porque el PC no tiene la clave de Supabase y el conector de Claude solo ve la lista de archivos. Esperar a tener una semana o más antes de arreglar.
2. Contar las Observaciones de los Excel, por tipo, filas y causas distintas.
3. Reproducir sin internet ni Haiku. Se descomprimen las capturas y ia_respuestas en una copia de prueba del proyecto (nunca en D:\Mercurio) y se corre motor.edicion.procesar() con cliente=None. Da exactamente lo mismo que dio el servidor, y además muestra el motivo de cada rojo y de cada carátula vacía, en todos los avisos y no solo en los de la tabla principal. Scripts en scripts/ (todo.py junta los avisos con fallo y sus motivos).
4. Clasificar cada caso por origen. Programa (el código rechaza algo correcto o calcula mal), IA (Haiku copió mal, se contradijo entre lecturas o eligió mal el tipo) o aviso (el diario lo imprimió incompleto o raro). Comprobar contra el código antes de concluir. Ejemplo de error propio, el 30 de Octubre se clasificó D2 como fallo del programa y era de la IA (sección 6).
5. Elegir qué arreglar por frecuencia. Primero lo del programa que más se repite. Lo de la IA se decide aparte, porque casi siempre significa aflojar una comprobación.
6. Auditoría independiente. Se arma un paquete con un encargo .md, los casos en JSON (texto completo del aviso, lecturas de la IA, lo que da hoy y lo que debería dar, más casos negativos que deben seguir vacíos) y una copia del código. Lo revisa un agente que no vio el trabajo previo. Sus hallazgos no se aceptan a ciegas.
7. Pesar contra datos reales. Correr las pruebas completas del proyecto con el código arreglado y hacer la regresión con todas las capturas guardadas, antes y después (scripts/regre.py y scripts/comparar.py). Criterio de aceptación, cero carátulas perdidas o cambiadas y cero direcciones que empeoren, salvo las que el arreglo busca.
8. Publicar. Aplicar en D:\Mercurio, agregar pruebas en pruebas/, fijar por escrito las cifras esperadas en ESTADO_PROYECTO.md y pasar el texto cerrado a Claude Code (commit y push, con reporte .md). Un cambio por noche.
9. Comprobar la corrida real del día siguiente. En Supabase (marcas, Excel, captura) y en el log que baja Diego. Los colores de la IA deben sumar los avisos leídos, las causas deben cuadrar con las tablas y las filas agregadas a la memoria con principal más ya informadas.
10. Anotar el ciclo en la sección 7 de esta guía y en BANCO_FALLOS.md.

## 4. Herramientas

| Archivo | Para qué |
|---|---|
| scripts/regre.py | Corre procesar() sobre todas las capturas de una copia del proyecto y guarda por aviso la carátula, el color, las direcciones y la cantidad de remates. Uso python3 -I regre.py RAIZ_COPIA salida.json |
| scripts/comparar.py | Compara dos salidas de regre.py y lista lo que cambió |
| scripts/todo.py | Junta los avisos con dirección en rojo o carátula vacía, con sus motivos y las lecturas de la IA |
| scripts/paquete.py | Ejemplo de cómo se armó casos.json para la auditoría del 30 de Octubre |
| scripts/test_cap.py | Prueba de guardar_captura() de servidor/diario.py sin conectarse a Supabase |
| pruebas/test_caratula.py, test_direccion.py, test_extraccion.py | Pruebas del proyecto. Incluyen el banco real del 14 de Octubre (57 de 57 en carátula, 60 aciertos y 1 no leído en dirección) |
| Excels_Supabase/Banco_fallos | Ciclo 1 completo. Banco, auditoría, respuesta del auditor y sus diffs |

## 5. Catálogo de tipos de fallo

| Tipo | Origen | Qué pasa | Ejemplo real | Estado |
|---|---|---|---|---|
| D1 | Programa | Dos números en palabras unidos por "y" se sumaban | "doscientos treinta y dos y doscientos treinta y cuatro" daba 466 (rol 20862-2024) | Arreglado, b652f2f |
| D1b | Programa | El mismo error en palabras_a_cifras, que se usa para la unidad | Sin caso real todavía | Pendiente |
| D2 | IA | Haiku se comió un dígito al pasar a cifras | "cero mil cuatrocientos noventa y uno" dio 0491 y es 01491 (rol 936-2024) | Sin arreglo, el programa lo atrapa bien |
| D3 | IA | Haiku copió la frase con otra mayúscula o comilla | "El Sitio" en vez de "el Sitio" (rol 10750-2022) | Decisión de diseño, buscar_frase solo perdona espacios |
| D4 | IA | Las dos lecturas no coinciden | una trae "casa 1" y la otra no (rol 15143-2024) | Decisión de diseño |
| D5a | IA y programa | Calle "s/n" | "Avenida Alcalde José Infante Larraín s/n" (rol 5633-2024) | En espera. El arreglo del auditor da la avenida del acceso y no la calle de la unidad |
| D5b | Programa | El aviso trae dos remates y se contó uno, porque minimo_y_costas no leyó "$159.164. 537" | rol 28-2025 | Pendiente, es un problema del conteo de remates |
| D6 | Programa (regla con prueba) | Unidad con letra y sin número | "Casa H" (rol 4485-2024) | En espera de ver el aviso. test_direccion exige hoy el rojo para "departamento D" |
| D7 | Aviso | Remate de partición con 11 propiedades | rol 4079-2023 | No aplica |
| C1 | Programa | "autos X con Y Rol" | rol 4567-2026 | Arreglado, 03a77dd |
| C2a | Programa | Carátula pegada al tribunal sin palabra que la anuncie | "Viña del Mar Banco de Chile con Hinojosa" (rol 1177-2025) | No se arregla. Anclarla al tribunal es riesgoso porque _TRIBUNAL puede tragarse una palabra con mayúscula |
| C2b | Programa | "Rol N, X con Y." | rol 4079-2023, 9008-2025, 7881-2024 | Arreglado, 03a77dd |
| C3 | Aviso y programa | Comilla de un solo lado | rol 18954-2024, 26036-2016 | Arreglado, 03a77dd |
| C4 | Programa | "Caratulado X/ Y" seguido del verbo sin puntuación | rol 6108-2025 | Arreglado, 03a77dd |
| C5 | Aviso y programa | "caratulada,,X/ Y" | rol 7898-2024 | Arreglado, 03a77dd |
| C6 | Aviso | El aviso imprime la carátula incompleta | "“/O’Brien“" (rol 188-2025) | Correcto que quede vacía. Pendiente un texto distinto para el abogado |
| C7 | No aplica | Avisos que no son juicios (interdicción, remate privado) | 2 sin rol | Correcto que quede vacía |
| D? | Sin clasificar | Dirección en rojo, caso nuevo | rol 12688-2023 del 20° Civil, 1 de Noviembre | Pendiente, ahora se puede ver con ia_respuestas.zip |

## 6. Lecciones aprendidas

1. Sin el texto del aviso no hay diagnóstico. En el ciclo 1 solo 8 de 27 causas con Observación tenían evidencia. Por eso desde el 2 de Noviembre se guarda la captura diaria. En GitHub Actions lo que el programa escribe en disco se pierde al terminar la corrida.
2. Comprobar en el código antes de clasificar. D2 parecía fallo del programa y al correr numeros_en resultó correcto (el error era de la IA).
3. El texto del rojo culpa siempre a la IA ("fue Haiku el que se equivocó"), aunque lo frene una regla del programa. No confiar en ese texto para clasificar.
4. El encargo al auditor también puede estar mal. En D5b el "debería dar" era incorrecto y el auditor lo detectó.
5. El auditor también se equivoca. Llamó a C2b "el más débil" y en datos reales acertó 3 casos sin ningún falso positivo. Por eso todo hallazgo se pesa contra los avisos reales (sección 3, paso 7).
6. Un riesgo teórico se mide en los datos. El riesgo del tribunal con una palabra de más no apareció en los 43 tribunales distintos de 12 días.
7. La regresión con todas las capturas es la prueba más fuerte. En el ciclo 1, 1.145 avisos de 12 ediciones mostraron cero pérdidas, y eso permitió publicar cinco patrones de carátula en una sola noche.
8. Medir la mejora en el total y no solo en la tabla principal. Los rojos de la IA sobre todos los avisos leídos son la cifra comparable entre días (log, línea "colores").
9. Explicar desde el principio que la Observación no desaparece. Al ver todavía Observaciones el 1 de Noviembre parecía que los arreglos no habían servido, cuando habían bajado de 13% a 1 de 6 filas.

## 7. Bitácora de ciclos

| Ciclo | Fechas | Evidencia | Arreglos publicados | Resultado medido |
|---|---|---|---|---|
| 1 | 30 de Octubre al 1 de Noviembre de 2026 | 12 Excel (19 al 30 de Octubre), capturas del 14 al 18 de Octubre, banco del 14 de Octubre | D1 (b652f2f), C1 C2b C3 C4 C5 (03a77dd), captura diaria (4c00652) | En 1.145 avisos, 10 carátulas y 2 direcciones recuperadas y cero pérdidas. Corridas reales del 31 de Octubre (rojos 4 de 100) y del 1 de Noviembre (rojos 5 de 94, Observaciones en la tabla principal 1 de dirección y 1 de carátula de 6 filas) |
| 2 | Desde cerca del 8 de Noviembre | Capturas del 2 al 8 de Noviembre | | |
