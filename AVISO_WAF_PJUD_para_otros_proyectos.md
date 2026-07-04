# AVISO TÉCNICO — El PJUD desplegó un WAF anti-bot (F5/Shape) en la OJV

> Informe independiente y autocontenido. Aplica a cualquier proyecto que acceda de forma automatizada a la Oficina Judicial Virtual (OJV) del Poder Judicial de Chile (`https://oficinajudicialvirtual.pjud.cl`).
> Fecha de verificación: julio de 2026. Basado en evidencia forense capturada de la respuesta cruda del servidor.

---

## Qué está pasando

La OJV del PJUD está protegida por un **WAF (Web Application Firewall) de F5 BIG-IP con el módulo anti-bot Shape Security ("Distributed Cloud Bot Defense")**. Es un sistema comercial de nivel bancario, especializado en detectar y bloquear tráfico automatizado (bots, scrapers, navegadores controlados por Playwright/Selenium/Puppeteer).

Cuando el WAF sospecha que quien accede es un bot, **NO devuelve el contenido normal del sitio**: en su lugar sirve una página de desafío con un **CAPTCHA visual** ("¿Qué código está en la imagen?") que solo un ser humano puede resolver. Hasta que no se resuelve, no hay acceso al formulario ni a los datos.

Este comportamiento parece haberse **endurecido / desplegado de forma más agresiva en fecha reciente** (a comienzos de 2026 el CAPTCHA aparecía de forma anecdótica; ahora se dispara con frecuencia).

## Cómo identificarlo (firma técnica)

Si tu bot deja de recibir el contenido esperado, revisa estas señales — son la huella inequívoca de F5/Shape:

1. **Cookies con prefijo `TS`:** el servidor planta cookies llamadas `TSPD_101`, `TS<hash>`, etc. (todas empiezan con `TS`).
2. **Recursos servidos desde rutas `/TSPD/<hash>?type=5` y `?type=10`:** es el JavaScript de detección del WAF.
3. **La página de bloqueo (status HTTP 200, pero NO es el sitio real) contiene:**
   - El texto: *"This question is for testing whether you are a human visitor and to prevent automated spam submission."*
   - Una imagen CAPTCHA con la pregunta *"What code is in the image?"*, una casilla de texto y un botón "submit".
   - Un control de audio CAPTCHA (para accesibilidad).
   - La etiqueta `<noscript>Please enable JavaScript to view the page content.</noscript>`.
   - Un identificador: `Your support ID is: <número largo>`.
   - JavaScript ofuscado con variables como `window["bobcmn"]` y `window["failureConfig"]`.

**Recomendación práctica:** implementa en tu bot una detección explícita de este bloqueo, buscando en el texto de la página cadenas como `"your support id"`, `"human visitor"`, `"automated spam"` o `"requested url was rejected"`. Sin esa detección, un bloqueo se manifiesta silenciosamente como "el sitio no cargó" o "el resultado salió incompleto", sin causa visible — lo que lleva a diagnósticos equivocados.

## Cómo decide el WAF si te bloquea

El JavaScript de F5/Shape se ejecuta en el navegador **antes** de mostrar contenido e inspecciona el entorno buscando señales de automatización: la propiedad `navigator.webdriver`, inconsistencias del user-agent, propiedades que las herramientas de automatización inyectan en `window`/`document`, el timing de ejecución, etc. Con eso calcula un **puntaje de sospecha**. Si supera un umbral, sirve el CAPTCHA.

Consecuencia importante: **el bloqueo es probabilístico e intermitente**, no determinista. El mismo bot, desde la misma máquina e IP, puede entrar una vez y ser bloqueado la siguiente, según el puntaje momentáneo. Dos bots con código casi idéntico pueden tener tasas de éxito distintas por diferencias sutiles de timing o huella.

## Qué NO es la causa (verificado, para evitar diagnósticos equivocados)

- **NO es la IP de datacenter ni la falta de proxy:** el bloqueo ocurre incluso desde una IP residencial con conexión directa. (La reputación de IP es una señal secundaria del WAF, pero no la dominante.)
- **NO es el modo headless:** el bloqueo ocurre incluso con navegador visible (`headless=False`).
- **NO es solo la frecuencia de acceso:** el bloqueo puede ocurrir en el PRIMER intento de una sesión completamente limpia.
- El factor **dominante** es la **huella de automatización del navegador**, detectada por el JavaScript del WAF.

## Implicancias para el diseño de un bot

1. **No existe un ajuste de código que garantice el acceso permanente.** F5/Shape es un producto dedicado a impedir exactamente esto. La meta realista es *convivir* con el WAF (entrar la mayoría de las veces) y *recuperarse* cuando bloquee, no "vencerlo" de forma estable.
2. **El CAPTCHA requiere un humano.** Cualquier arquitectura de monitoreo 100% automático y desatendido (por ejemplo, en un servidor o Raspberry Pi sin pantalla) choca con esta barrera: no hay ojos humanos para resolver el CAPTCHA cuando aparece.
3. **Las cookies `TS*` son el mecanismo de memoria del WAF.** Una vez que un humano resuelve el CAPTCHA en una sesión, esas cookies marcan la sesión como "validada" por un tiempo. Esto abre una vía legítima de diseño: que un humano resuelva el CAPTCHA una vez y el bot reutilice esa ventana de sesión validada.
4. **Reducir la huella de automatización** (usar un navegador real del sistema en vez del Chromium de automatización, perfiles persistentes, etc.) puede bajar la frecuencia de bloqueo, pero es una carrera armamentística frágil: F5 actualiza sus detecciones. No confíes en ello como única defensa.

## Línea ética

Resolver el CAPTCHA por medios automáticos (servicios de resolución de terceros, OCR, burlar el desafío) es frágil y de dudosa legitimidad. La aproximación sostenible es la **resiliencia honesta**: minimizar la probabilidad de bloqueo con higiene de navegador legítima, detectar el bloqueo de forma robusta, reintentar con criterio, y — cuando haga falta — involucrar a un humano para resolver el CAPTCHA una sola vez.
