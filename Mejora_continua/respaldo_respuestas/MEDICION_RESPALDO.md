# Respaldo de las respuestas de Haiku en la captura del día. Medición en copia (10 de noviembre del 2026)

Decisión de Diego del 10 de noviembre. capturas/FECHA.zip trae también las respuestas de Haiku de los avisos de ese día, para rehacer cualquier día solo con su captura y no tener que bajar estado/ia_respuestas.zip. Sin tocar D:\Mercurio\servidor. Solo cambia servidor/diario.py. Se aplica con python3 -I aplicar_respaldo.py RAIZ [S1] [S2]. Prueba en test_respaldo.py (uso python3 test_respaldo.py RAIZ_COPIA FECHA, la copia debe traer capturas/FECHA e ia_respuestas/direccion).

| Cambio | Qué hace | Medido con la edición del 10 de noviembre |
|---|---|---|
| S1 | guardar_captura rearma los avisos desde la captura (sin internet y sin Haiku) y agrega al zip la respuesta guardada de cada uno, en FECHA/ia_respuestas/direccion | 96 respuestas para 96 avisos leídos. El zip pasa de 196 a 254 KB. El día rehecho solo con el zip da los mismos colores y 0 avisos sin respuesta. Si falla el agregado, la captura se sube igual sin respuestas. Si falla la subida, la corrida sigue |
| S2 | Si estado/ia_respuestas.zip llega dañado, guarda el archivo dañado en respaldos/ia_respuestas_danado_FECHA.zip y la corrida sigue sin respuestas guardadas | Sin S2 la corrida se cae con BadZipFile antes de main.py, en cada intento (comprobado). Con S2 llega hasta main.py. Si lo que falla es la bajada, se reintenta como siempre |

La línea del log cambia a "Captura del día guardada en Supabase (N archivos, R respuestas de Haiku, K KB)".

S2 no fue pedido por Diego. Salió de revisar qué pasa si el archivo grande se daña. Se puede publicar S1 solo.

sha1 de servidor/diario.py con S1 y S2 aplicados sobre e4a320b. 87d8dd35ed10e3e68e0ba6a42ade80141525b1c1

Repetido el 13 de noviembre del 2026 antes de publicar. servidor/diario.py sin cambios desde 4c00652 (sha1 bef769fbc859f8bf3f397da8ce85c7f653d3cfa4). El script da el mismo sha1 de arriba sobre una copia y sobre D:\Mercurio. Con la edición del 13 de noviembre (tres bloques de remates, 132 avisos leídos con 37 repetidos), 99 respuestas, el zip pasa de 392 a 452 KB, el día rehecho solo con el zip da 126 verde, 5 rojo y 1 sin dato, y las pruebas de S2 pasan. Las respuestas pueden ser menos que los avisos leídos cuando el diario repite avisos entre bloques.
