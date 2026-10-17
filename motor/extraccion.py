"""Extracción por código de los datos de formato fijo de un aviso (parte 3.6).
Cada valor sale con la frase exacta del aviso de donde se sacó (cita). Si el código no está seguro, deja el valor
vacío y agrega una alerta. Nunca adivina.

Etapa 1. Fecha y hora del remate.
"""
import datetime as dt
import re

_NOMBRE_MES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def fecha_palabras(f: str) -> str:
    """'2026-05-26' da '26 de Mayo de 2026'. Los meses nunca en número en lo que ve Diego (pedido del 15 de Octubre)."""
    a, m, d = f[:10].split("-")
    return f"{int(d)} de {_NOMBRE_MES[int(m) - 1]} de {a}"


MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
         "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
_MES = "|".join(MESES)
_DIA_SEM = r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+"
# "6 de noviembre de 2026", "3 noviembre 2026", "05 de noviembre del año 2026", "29 de Octubre 2026"
FECHA_TEXTO = re.compile(rf"\b(\d{{1,2}})\s+(?:de\s+)?({_MES})\s*,?\s+(?:de\s+|del\s+)?(?:a[ñn]o\s+)?(\d{{4}})\b", re.I)
# "11/11/2026", "27/10/ 2026"
FECHA_NUM = re.compile(r"\b(\d{1,2})/(\d{1,2})/\s?(\d{4})\b")
# "a las 13:15 horas", "13:45 hrs.", "a las 11.30 horas", "a las 11:00,", "A Las 15:05 Horas", "10:30 HRS"
HORA = re.compile(r"(?:\ba(?:\s+las)?\s+)?\b(\d{1,2})[:.]\s?(\d{2})\b(?:\s*(?:horas|hrs?)\b\.?)?", re.I)
# Palabras que anuncian el remate
VERBO = re.compile(r"\b(?:se\s+)?(?:rematar[áa]n?|remata|subastar[áa]n?|se\s+subasta|remate|subasta|llamado\s+con\s+fecha)\b", re.I)


def _fechas(texto):
    """Todas las fechas del aviso, en orden. (inicio, fin, AAAA-MM-DD, cita)."""
    out = []
    for m in FECHA_TEXTO.finditer(texto):
        try:
            d = dt.date(int(m.group(3)), MESES[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            continue
        out.append((m.start(), m.end(), d.isoformat(), m.group(0)))
    for m in FECHA_NUM.finditer(texto):
        try:
            d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        out.append((m.start(), m.end(), d.isoformat(), m.group(0)))
    return sorted(out)


def _hora_tras(texto, desde, hasta):
    """Primera hora válida en texto[desde:hasta] que venga con 'a las' delante o 'horas/hrs' detrás."""
    for m in HORA.finditer(texto, desde, hasta):
        h, mi = int(m.group(1)), int(m.group(2))
        tiene_marca = m.group(0).lower().startswith("a") or re.search(r"(?:horas|hrs?)\.?$", m.group(0), re.I)
        if 0 <= h <= 23 and 0 <= mi <= 59 and tiene_marca:
            return f"{h:02d}:{mi:02d}", m.group(0).strip()
    return None, None


def fecha_y_hora(texto: str, fecha_edicion: str | None = None) -> dict:
    """Devuelve {'fecha_remate': {valor, cita}, 'hora_remate': {valor, cita}, 'alertas': [(tipo, texto)]}."""
    alertas = []
    fechas = _fechas(texto)
    # Fecha del remate. La primera fecha que aparece dentro de los 250 caracteres que siguen a un verbo de remate.
    candidatas = []
    for v in VERBO.finditer(texto):
        for ini, fin, valor, cita in fechas:
            if v.start() <= ini <= v.end() + 250:
                candidatas.append((ini, fin, valor, cita))
                break
    # También vale una fecha seguida de cerca (40 caracteres) por el verbo ("12/11/2026, 12:00 horas, se rematará", aviso 61 del 14-10).
    for v in VERBO.finditer(texto):
        for ini, fin, valor, cita in fechas:
            if fin <= v.start() <= fin + 40:
                candidatas.append((ini, fin, valor, cita))
    elegida = min(candidatas) if candidatas else None
    # Red de seguridad. Si hay fechas DISTINTAS que siguen de cerca (100 caracteres) a un verbo de remate,
    # el trozo puede traer dos avisos pegados. No se entrega fecha.
    cercanas = set()
    for v in VERBO.finditer(texto):
        for ini, fin, valor, cita in fechas:
            if v.end() <= ini <= v.end() + 100:
                cercanas.add(valor)
                break
    resultado = {"fecha_remate": {"valor": None, "cita": None}, "hora_remate": {"valor": None, "cita": None}, "alertas": alertas}
    if len(cercanas) > 1:
        # fechas con el mes en palabras (marcha blanca del 17 de Octubre, salían como 2026-10-27)
        alertas.append(("revisar_lectura", f"El trozo trae más de una fecha de remate ({', '.join(fecha_palabras(x) for x in sorted(cercanas))}). Puede tener dos avisos pegados."))
        return resultado
    if not elegida:
        alertas.append(("revisar_lectura", "No se encontró la fecha del remate."))
        return resultado
    ini, fin, valor, cita = elegida
    resultado["fecha_remate"] = {"valor": valor, "cita": cita}
    if fecha_edicion and valor < fecha_edicion:
        alertas.append(("error_escritura", f"La fecha del remate ({fecha_palabras(valor)}) es anterior a la edición del diario ({fecha_palabras(fecha_edicion)})."))
    h, hc = _hora_tras(texto, fin, fin + 80)
    if h is None:
        h, hc = _hora_tras(texto, max(0, ini - 80), ini)
    if h is None:
        alertas.append(("revisar_lectura", "No se encontró la hora del remate junto a la fecha."))
    resultado["hora_remate"] = {"valor": h, "cita": hc}
    return resultado


# --- Etapa 2. Mínimo y costas -----------------------------------------------------------------------------
MINIMO = re.compile(r"m[ií]nimo", re.I)
# Una mención de "mínimo" que pertenece a la garantía o a las alzas no es el mínimo del remate
_NO_ES_MINIMO = re.compile(r"(?:%[^%]{0,15}|sobre\s+el\s+|conforme\s+al\s+|equivalente\s+al\s+)$", re.I)
_PESOS = r"\$\s?(\d{1,3}(?:\.\s?\d{3})+|\d+)"
_NUM_UF = r"(\d{1,3}(?:\.\d{3})+(?:\s?,\d+)?|\d+(?:\s?,\d+)?)"
MONTO = re.compile(
    rf"(\$\s?)?{_NUM_UF}\s*\.?-?\s*(?:UF\b|U\.F\.|unidades\s+de\s+fomento)"     # 355,969402 unidades de fomento / 1.100 UF / "$1.771,0860.- Unidades de Fomento" (signo $ por error)
    rf"|\bUF\s*{_NUM_UF}"                                                         # UF 2.824.-
    rf"|{_PESOS}", re.I)                                                          # $ 17.364.913
_ETIQUETA = re.compile(r"\b(oficina|lote|departamento|depto|casa|local|bodega|estacionamiento|parcela|sitio)\s*(?:N[°º]?\s*)?(\d+[A-Za-z]?)\b", re.I)


def _a_numero(m):
    """(monto, moneda, signo_pesos_en_uf). Grupos. 1 signo $ antes de UF, 2 número UF, 3 número tras 'UF', 4 pesos."""
    if m.group(4):
        return float(re.sub(r"[.\s]", "", m.group(4))), "CLP", False
    txt = m.group(2) or m.group(3)
    return float(re.sub(r"\s", "", txt).replace(".", "").replace(",", ".")), "UF", bool(m.group(1))


def _costas(texto, desde):
    """Costas que siguen al mínimo. Montos en pesos entre el último 'más' y la palabra 'costas' (hasta 250 caracteres),
    más una segunda parte 'y $ X ... costas' pegada a la primera (costas procesales y personales)."""
    fin_busqueda = desde + 250
    c = re.search(r"costas", texto[desde:fin_busqueda], re.I)
    if not c:
        return None, None
    pos_costas = desde + c.start()
    mas = [x for x in re.finditer(r"\bm[aá]s\b", texto[desde:pos_costas], re.I)]
    if not mas:
        return None, None
    ini = desde + mas[-1].start()
    fin = pos_costas + len("costas")
    montos = [float(re.sub(r"[.\s]", "", x.group(1))) for x in re.finditer(_PESOS, texto[ini:pos_costas])]
    if not montos:
        # la palabra costas va antes del monto ("más las costas procesales y personales que corresponden a la suma de $ 1.315.000")
        alreves = re.match(rf"[^.$]{{0,90}}?suma\s+de\s+{_PESOS}", texto[fin:fin + 130], re.I)
        if alreves:
            montos = [float(re.sub(r"[.\s]", "", alreves.group(1)))]
            fin = fin + alreves.end()
            return sum(montos), texto[ini:fin]
    seg = re.match(rf"[^$]{{0,40}}?\by\s+{_PESOS}[^$]{{0,40}}?costas", texto[fin:fin + 120], re.I)
    if seg:
        montos.append(float(re.sub(r"[.\s]", "", seg.group(1))))
        fin = fin + seg.end()
    if not montos:
        return None, None
    return sum(montos), texto[ini:fin]


def _monto_legible(monto, moneda):
    """$ 77.387.528 o 1.771,086 UF, como se escribe en Chile."""
    if moneda == "CLP":
        return "$ " + f"{monto:,.0f}".replace(",", ".")
    entero, _, dec = f"{monto:.6f}".rstrip("0").rstrip(".").partition(".")
    return f"{int(entero):,}".replace(",", ".") + ("," + dec if dec else "") + " UF"


def minimo_y_costas(texto: str) -> dict:
    """Devuelve {'minimo': {monto, moneda, costas_clp, cita, cita_costas} o {'lista': [...]}, 'alertas': [...]}."""
    alertas, hallados = [], []
    for a in MINIMO.finditer(texto):
        if _NO_ES_MINIMO.search(texto[max(0, a.start() - 30):a.start()]):
            continue
        m = MONTO.search(texto, a.end(), a.end() + 200)
        if not m:
            continue
        # el monto no debe pertenecer a otra mención de "mínimo" o a la garantía que esté entre medio
        entre = texto[a.end():m.start()]
        if re.search(r"%|garant[ií]a|cauci[oó]n", entre, re.I):
            continue
        monto, moneda, signo_raro = _a_numero(m)
        if signo_raro:
            alertas.append(("error_escritura", f"El aviso pone el signo $ a un monto en Unidades de Fomento ({m.group(0).strip()})."))
        # El inmueble de este mínimo. Primero el nombrado entre "mínimo" y el monto ("Mínimo para el Lote 1 es $"),
        # si no, el PRIMERO nombrado después del mínimo anterior (o desde el comienzo del aviso). Parte 3.7b, 17 de Octubre.
        # Antes se tomaba el último nombrado en los 300 caracteres anteriores, y fallaba cuando un lote trae varias piezas.
        # 14-10 aviso 30 ("Lote 4. Conformado por el Estacionamiento N° 6 ..., cuyo mínimo") daba "estacionamiento 6" y
        # 06-10 aviso 73 ("1) Departamento N° 41 ..., bodega N° 41 ... y estacionamiento N° 22") daba "estacionamiento 22".
        etiqueta = _ETIQUETA.search(texto, a.start(), m.start())
        if not etiqueta:
            etiqueta = _ETIQUETA.search(texto, hallados[-1]["fin"] if hallados else 0, a.start())
        hallados.append({"monto": monto, "moneda": moneda, "cita": texto[a.start():m.end()], "fin": m.end(),
                         "inmueble": f"{etiqueta.group(1).lower()} {etiqueta.group(2)}" if etiqueta else None})
    vacio = {"monto": None, "moneda": None, "costas_clp": None, "cita": None}
    if not hallados:
        alertas.append(("revisar_lectura", "No se encontró el mínimo del remate."))
        return {"minimo": vacio, "alertas": alertas}
    # Un solo monto repetido es un solo remate. Varios montos, o el mismo monto para inmuebles distintos, son varios.
    if len({(h["monto"], h["moneda"]) for h in hallados}) == 1:
        distintos = hallados[:1]
    else:
        distintos = []
        for h in hallados:
            if (h["monto"], h["moneda"], h["inmueble"]) not in [(d["monto"], d["moneda"], d["inmueble"]) for d in distintos]:
                distintos.append(h)
    if len(distintos) == 1:
        h = distintos[0]
        costas, cita_c = _costas(texto, h["fin"])
        r = {"monto": h["monto"], "moneda": h["moneda"], "costas_clp": costas, "cita": h["cita"]}
        if cita_c:
            r["cita_costas"] = cita_c
        return {"minimo": r, "alertas": alertas}
    # Varios mínimos distintos. Solo es una lista de remates si cada uno nombra su lote, oficina o depto.
    if all(d["inmueble"] for d in distintos) and len({d["inmueble"] for d in distintos}) == len(distintos):
        lista = []
        for d in distintos:
            costas, cita_c = _costas(texto, d["fin"])
            el = {"monto": d["monto"], "moneda": d["moneda"], "costas_clp": costas, "cita": d["cita"], "inmueble": d["inmueble"]}
            lista.append(el)
        return {"minimo": {"lista": lista}, "alertas": alertas}
    alertas.append(("revisar_lectura", "El aviso trae varios montos mínimos y el código no pudo asignar cada uno a su inmueble: "
                    + ", ".join(_monto_legible(d["monto"], d["moneda"]) for d in distintos)))
    return {"minimo": vacio, "alertas": alertas}


# --- Etapa 3. Garantía --------------------------------------------------------------------------------------
_GARANTIA = re.compile(r"garant[ií]a|cauci[oó]n|vale\s+(?:a\s+la\s+)?vista|consignar", re.I)
_PORC = re.compile(r"(?:un\s+)?(\d{1,2}(?:,\d+)?)\s?%", re.I)
_MONTO_FIJO = re.compile(rf"(?:garant[ií]a|cauci[oó]n)[^.$%]{{0,40}}?{_PESOS}|ascendente\s+a\s+{_PESOS}", re.I)


def garantia(texto: str) -> dict:
    """Devuelve {'garantia': {porcentaje, base, base_origen, monto, moneda, cita}, 'alertas': [...]}.
    base_origen. 'texto' si el aviso dice de qué es el porcentaje. 'asumido' si no lo dice (decisión de Diego,
    se asume el mínimo y el HUD lo muestra como ASUMIDO)."""
    alertas = []
    anclas = [a.start() for a in _GARANTIA.finditer(texto)]
    porcentajes = []
    for p in _PORC.finditer(texto):
        # el porcentaje debe estar cerca de una palabra de garantía (hasta 300 caracteres después o 80 antes).
        # 300 por el aviso de Iquique ("garantía suficiente de cualquiera de estas dos formas... 10% del mínimo")
        if any(a - 80 <= p.start() <= a + 300 for a in anclas):
            porcentajes.append(p)
    g = {"porcentaje": None, "base": "sin_dato", "base_origen": None, "monto": None, "moneda": None, "cita": None}
    if porcentajes:
        p = porcentajes[0]
        g["porcentaje"] = float(p.group(1).replace(",", "."))
        if g["porcentaje"].is_integer():
            g["porcentaje"] = int(g["porcentaje"])
        despues = texto[p.end():p.end() + 45]
        fin = p.end()
        b = re.match(r"\s*(?:del?\s+|al\s+)?(?:(?:precio|valor|monto)\s+)?(?:de\s+(?:la\s+)?)?(m[ií]nimo|tasaci[oó]n)", despues, re.I)
        if b:
            g["base"] = "tasacion" if b.group(1).lower().startswith("tasaci") else "minimo"
            g["base_origen"] = "texto"
            fin = p.end() + b.end()
        else:
            g["base"], g["base_origen"] = "minimo", "asumido"
            alertas.append(("condicion_especial", f"{g['porcentaje']}% DEL MÍNIMO ASUMIDO. EL AVISO NO LO DICE."))
        g["cita"] = texto[p.start():fin]
        otros = {float(x.group(1).replace(",", ".")) for x in porcentajes[1:]} - {float(g["porcentaje"])}
        if otros:
            alertas.append(("revisar_lectura", f"El aviso menciona otro porcentaje cerca de la garantía ({', '.join(f'{o:g}%' for o in sorted(otros))})."))
    mf = _MONTO_FIJO.search(texto)
    if mf and not re.search(r"m[ií]nimo", texto[mf.start():mf.end()], re.I):
        g["monto"] = float(re.sub(r"[.\s]", "", mf.group(1) or mf.group(2)))
        g["moneda"] = "CLP"
        if g["cita"] is None:
            g["cita"] = mf.group(0)
    if g["porcentaje"] is None and g["monto"] is None:
        g["base"] = "sin_dato"
        alertas.append(("dato_faltante", "El código no encontró el porcentaje ni el monto de la garantía. Revisa el aviso o las bases."))
    if g["porcentaje"] is not None and g["porcentaje"] != 10:
        alertas.append(("condicion_especial", f"Garantía del {g['porcentaje']}%, no del 10%."))
    if g["base"] == "tasacion":
        alertas.append(("condicion_especial", "Garantía sobre la TASACIÓN, no sobre el mínimo."))
    return {"garantia": g, "alertas": alertas}


# --- Etapa 4. Modalidad -------------------------------------------------------------------------------------
_ZOOM = re.compile(r"\bzoom\b|video[\s-]?conferencia|telem[áa]tic[ao]|en\s+forma\s+virtual", re.I)
_OTRA_PLATAFORMA = re.compile(r"\b(?:google\s+)?meet\b|vendaya", re.I)
# Frases de remate presencial que usan los avisos
_PRESENCIAL = re.compile(
    r"(?:de|en)\s+(?:manera|forma)\s+presencial|\bpresencialmente\b|remate\s+presencial|modalidad\s+presencial|presencia\s+f[ií]sica"
    r"|(?:remat\w*|subast\w*|realizar[áa]|efectuar[áa]|llevar[áa]\s+a\s+cabo)\W+(?:\w+\W+){0,16}?"
    r"(?:en\s+)?(?:las\s+)?(?:dependencias|recinto)(?:\s+f[ií]sicas)?\s+(?:del?\s+)?(?:\w+\s+){0,2}?(?:tribunal|juzgado)", re.I)
# Si cerca de la frase se habla de la entrega o devolución del vale vista, no se refiere al remate
_NO_ES_REMATE = re.compile(r"vale\s+(?:a\s+la\s+)?vista|entreg|secretar|turno|devoluci|devuelt|restitu|retir|acompa[ñn]|garant|\bacta\b|suscrib|firma", re.I)
# Mixta dicha en una sola frase. "vía plataforma Zoom o en forma presencial", "vía www.vendaya.cl y presencialmente"
_MIXTA = re.compile(r"(?:zoom|video[\s-]?conferencia|meet|vendaya)[^.]{0,30}?\b(?:o|y)\s+(?:en\s+forma\s+|de\s+manera\s+)?presencial(?:mente)?"
                    r"|presencial(?:mente)?[^.]{0,30}?\b(?:o|y)\s+(?:v[ií]a\s+)?(?:zoom|video[\s-]?conferencia)", re.I)


def _presencial(texto):
    for m in _PRESENCIAL.finditer(texto):
        alrededor = texto[max(0, m.start() - 120):m.start()] + texto[m.end():m.end() + 30]
        if not _NO_ES_REMATE.search(alrededor) and not _NO_ES_REMATE.search(m.group(0)):
            return m
    return None


def modalidad(texto: str) -> dict:
    """Devuelve {'modalidad': {valor, cita}, 'plataforma': str|None, 'alertas': [...]}.
    valor. zoom, presencial, mixta, en_linea o sin_dato."""
    alertas = []
    z, o, p = _ZOOM.search(texto), _OTRA_PLATAFORMA.search(texto), _presencial(texto)
    mx = _MIXTA.search(texto)
    plataforma = None
    if o:
        plataforma = "Google Meet" if "meet" in o.group(0).lower() else "vendaya.cl"
    elif z and "zoom" in texto.lower():
        plataforma = "Zoom"
    virtual = z or o
    if mx or (virtual and p):
        valor, cita = "mixta", (mx or p).group(0)
        alertas.append(("condicion_especial", "El aviso nombra remate presencial y también en línea. Revisa cuál aplica."))
    elif o:
        valor, cita = "en_linea", o.group(0)
        alertas.append(("condicion_especial", f"Remate en línea por {plataforma}, no por Zoom."))
    elif z:
        valor, cita = "zoom", z.group(0)
    elif p:
        valor, cita = "presencial", p.group(0)
    else:
        valor, cita = "sin_dato", None
        alertas.append(("revisar_lectura", "El aviso no dice si el remate es por Zoom o presencial."))
    return {"modalidad": {"valor": valor, "cita": cita}, "plataforma": plataforma, "alertas": alertas}


# --- Etapa 5. Tribunal en forma única -----------------------------------------------------------------------
_UNIDADES = {"primer": 1, "primero": 1, "segundo": 2, "tercer": 3, "tercero": 3, "cuarto": 4, "quinto": 5, "sexto": 6,
             "septimo": 7, "séptimo": 7, "octavo": 8, "noveno": 9}
_DECENAS = {"decimo": 10, "décimo": 10, "vigesimo": 20, "vigésimo": 20, "trigesimo": 30, "trigésimo": 30}
_ESPECIALES = {"undecimo": 11, "undécimo": 11, "duodecimo": 12, "duodécimo": 12, "decimotercer": 13, "decimotercero": 13}
_PAL_ORD = "|".join(sorted(list(_UNIDADES) + list(_DECENAS) + list(_ESPECIALES), key=len, reverse=True))
_ORDINAL = rf"(?:(\d{{1,2}})\s*(?:°|º|er|ER|o\b)?|((?:{_PAL_ORD})(?:\s+(?:{_PAL_ORD}))?)(?:\s*\(\s*\d{{1,2}}\s*°?\s*\))?)"
_TIPO = (r"(civil|(?:de\s+)?letras\s+(?:en\s+lo\s+)?civil|(?:de\s+letras\s+)?(?:de\s+)?cobranza\s+laboral(?:\s+y\s+previsional)?"
         r"|de\s+letras(?:\s+del\s+trabajo)?|letras|de\s+familia|familia|de\s+polic[ií]a\s+local|polic[ií]a\s+local)")
# Palabras que no son ciudad ("7° JUZGADO CIVIL, EN calle Huérfanos 1409")
_NO_CIUDAD = {"en", "ubicado", "ubicada", "con", "causa", "autos", "rol", "huerfanos", "huérfanos", "calle", "avenida", "juicio", "expediente", "domiciliado"}
_TRIBUNAL = re.compile(rf"(?:{_ORDINAL}\s*)?juz(?:gado)?\.?\s+{_TIPO}\s*,?\s*(?:de\s+|del\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+(?!(?i:huerfanos|huérfanos|ubicado))(?-i:[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+))?)", re.I)
_MINUSC = {"de", "del", "y"}


def _ordinal_a_numero(dig, pal):
    if dig:
        return int(dig)
    partes = pal.lower().split()
    if len(partes) == 1 and partes[0] in _ESPECIALES:
        return _ESPECIALES[partes[0]]
    total = 0
    for p in partes:
        total += _DECENAS.get(p, 0) + _UNIDADES.get(p, 0) + _ESPECIALES.get(p, 0)
    return total or None


def _titulo(txt):
    return " ".join(w if w in _MINUSC else w[:1].upper() + w[1:] for w in txt.lower().split())


def tribunal(texto: str) -> dict:
    """Devuelve {'tribunal': {valor, cita}, 'alertas': [...]}. Forma única. '7° Juzgado Civil de Santiago',
    'Juzgado de Letras de Colina', 'Juzgado de Cobranza Laboral y Previsional de Santiago'."""
    alertas = []
    m = _TRIBUNAL.search(texto[:400])
    if not m:
        alertas.append(("revisar_lectura", "No se encontró el tribunal al comienzo del aviso."))
        return {"tribunal": {"valor": None, "cita": None}, "alertas": alertas}
    num = _ordinal_a_numero(m.group(1), m.group(2)) if (m.group(1) or m.group(2)) else None
    tipo = re.sub(r"\s+", " ", m.group(3).lower())
    tipo = re.sub(r"^de\s+", "", tipo)
    if "civil" in tipo:
        tipo = "civil"                                            # "de Letras en lo Civil" y "de Letras Civil" son juzgados civiles
    elif "cobranza" in tipo:
        tipo = re.sub(r"^letras\s+(?:de\s+)?", "", tipo)          # "de Letras de Cobranza Laboral" es de Cobranza Laboral
    ciudad = m.group(4)
    if ciudad.split()[0].lower() in _NO_CIUDAD:
        ciudad = "Santiago" if re.search(r"hu[ée]rfanos", texto[m.end():m.end() + 150], re.I) else None
    if not ciudad:
        alertas.append(("revisar_lectura", "No se encontró la ciudad del tribunal."))
        return {"tribunal": {"valor": None, "cita": m.group(0)}, "alertas": alertas}
    ciudad = _titulo(ciudad)
    if tipo in ("letras", "de letras") and num and ciudad == "Santiago":
        tipo = "civil"                                            # en Santiago los juzgados de letras numerados son los civiles
    tipo = {"civil": "Civil"}.get(tipo, "de " + _titulo(tipo))
    valor = (f"{num}° " if num else "") + f"Juzgado {tipo} de {ciudad}"
    return {"tribunal": {"valor": valor, "cita": m.group(0)}, "alertas": alertas}


# --- Etapa 6. Inscripción en el Conservador (parte 3.7b, 17 de Octubre) ------------------------------------------
# Decisión de Diego del 17 de Octubre. La inscripción se lee SOLO para saber qué propiedad es cuál (no para filtrar).
# Es el "RUT" de la propiedad. Separa los 26 remates del rol C-5656-2013 del 01-09 (26 de 26 distintas).
# "Inscripción a Fojas 7.694, Número 6.390 del Registro de Propiedad del año 2009 del Conservador de Bienes Raíces de La Serena"
# "inscrito a fojas 57.106 N81.820", "a fojas 5.431 vuelta N° 6.193", "a fojas 44773 bajo el N° 66273", "fojas 44321, número 64342"
# Formas vistas en las 7 ediciones capturadas (17 de Octubre). "5914v N° 6254", "3242V N° 5292", "No. 38.549", "No 4.989",
# "fojas 14. 515 N° 13.762", "fojas. 2412 número 3376", "fojas Fs. 76060 N° 106266".
_NUM_INS = r"(\d{1,3}(?:\.\s?\d{3})+|\d+)"
_FOJAS = re.compile(rf"\bfojas?\.?\s+(?:fs\.?\s*)?{_NUM_INS}\s*(?:vuelta|vta\.?|v(?![a-záéíóúñ]))?\s*,?\s*(?:y\s+)?(?:bajo\s+(?:el\s+)?)?"
                    rf"(?:n[uú]mero|nro\.?|n\s*[°º]|no\.?(?=\s*\d)|N(?=\d))\s*{_NUM_INS}", re.I)
# "del año 2009", "de 2011", "del 2021", "Propiedad 2018", "Santiago, 2005", "año 2.007"
_ANIO_INS = re.compile(r"(?:\ba[ñn]o|\bdel?|\bpropiedad|,)\s+((?:19|20)\d\d|[12]\.\d{3})(?!\d)", re.I)
_CBR = re.compile(r"Conservador\s+(?:de\s+)?Bienes\s+Ra[íi]ces\s+(?:de\s+|del\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de\s+|del\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)")
_HIPOTECA = re.compile(r"hipotecas?|grav[áa]menes|prohibiciones", re.I)


def inscripcion(texto: str, fecha_edicion: str | None = None) -> dict:
    """Devuelve {'inscripcion': [{fojas, numero, anio, conservador, cita}], 'clave': str|None, 'alertas': []}.
    Solo cuenta las inscripciones de dominio. Se salta las del Registro de Hipotecas o de Prohibiciones. El año y el
    conservador se buscan en los 220 caracteres que siguen (a veces van después del conservador, 01-09 aviso 50).
    clave junta todas las inscripciones del aviso (un depto y su bodega pueden tener dos, 09-10 aviso 83)."""
    lista = []
    for m in _FOJAS.finditer(texto):
        resto = texto[m.end():m.end() + 220]
        # el dato termina donde empieza la frase siguiente (punto y mayúscula). Si vienen varias inscripciones seguidas,
        # comparten el año y el conservador que van al final ("fojas 79793, n° 112451, fojas 79794 n° 112452 ... todas del
        # registro de propiedad del año 2020", 06-10 aviso 53).
        corte = re.search(r"M[íi]nimo|\.\s+[A-ZÁÉÍÓÚ]", resto)
        resto = resto[:corte.start()] if corte else resto
        if _HIPOTECA.search(texto[max(0, m.start() - 60):m.start()] + resto[:90]) and not re.search(r"propiedad|dominio", resto[:90], re.I):
            continue
        a, c = _ANIO_INS.search(resto), _CBR.search(resto)
        fin = max([m.end()] + [m.end() + x.end() for x in (a, c) if x])
        el = {"fojas": re.sub(r"[.\s]", "", m.group(1)), "numero": re.sub(r"[.\s]", "", m.group(2)), "anio": a.group(1).replace(".", "") if a else None,
              "conservador": c.group(1) if c else None, "cita": texto[m.start():fin]}
        if (el["fojas"], el["numero"]) not in [(x["fojas"], x["numero"]) for x in lista]:
            lista.append(el)
    clave = " + ".join(f"fojas {x['fojas']} n {x['numero']}" + (f" {x['anio']}" if x["anio"] else "") for x in sorted(lista, key=lambda x: (x["fojas"], x["numero"]))) or None
    alertas = []
    for x in lista:
        # 09-10 aviso 119 (y su republicación del 10 y del 11) imprime "Registro Propiedad año 2033"
        if fecha_edicion and x["anio"] and x["anio"] > fecha_edicion[:4]:
            alertas.append(("error_escritura", f"La inscripción del inmueble dice año {x['anio']}, posterior a la edición del diario. Posible error de escritura del aviso."))
    return {"inscripcion": lista, "clave": clave, "alertas": alertas}


# --- Etapa 7. Carátula de la causa (parte 3.7c, 17 de Octubre) ------------------------------------------------
# Decisión de Diego. Basta la carátula tal como la imprime el aviso, sin separar demandante y demandado. La lee el código.
# Formas vistas en el banco del 14-10. "caratulado ‘Banco de Chile con Aguilera’", "expediente “Securitizadora Security S.A.
# con Tilleria“", "Caratulado. Banco de Crédito e Inversiones/Pérez. El Secretario", "causa Banco Itaú Chile S.A./ Rubilar,
# juicio ejecutivo", "Rit C-3908-2025, Ruc 25-4-0645112-K, ’Barrera con López’".
_COMILLA_A, _COMILLA_C = "‘’'“”\"«", "’'”\"»‘“"
_SEP = r"(?:\s[Cc][Oo][Nn]\s|/|\s[Cc]ontra\s)"
_CAR_COMILLAS = re.compile(rf"[{_COMILLA_A}]\s*([^{_COMILLA_A}»\n]{{2,150}}?{_SEP}[^{_COMILLA_A}»\n]{{1,150}}?)\s*[{_COMILLA_C}]")
_CAR_ANTES = re.compile(r"caratulad\w*|juicio|autos|expediente|causa|\brol\b|\brit\b|\bruc\b|antecedentes|virtual", re.I)
_CAR_SIN = re.compile(rf"[Cc][Aa][Rr][Aa][Tt][Uu][Ll][Aa][Dd]\w*\s*:?\s*([A-Z0-9ÁÉÍÓÚÑ][^{_COMILLA_A};\n]{{2,150}}?{_SEP}[^{_COMILLA_A};\n]{{1,150}}?)"
                      # Arreglo 2 del ajuste (14-10 avisos 6, 28, 39 y 46). El final se busca sin comerse antes el punto o la coma.
                      r"(?=\s*(?:[’'”\"]|,\s*(?:Rol|rol|Juicio|juicio|v[ií]a|Ejecutivo|ejecutivo)\b|\.\s+[A-ZÁÉÍÓÚ]|\.?\s*$))")
# Arreglo 2 (14-10 aviso 49). La primera parte acepta el punto de "S.A." ("causa Banco Itaú Chile S.A./ Rubilar, juicio").
_CAR_CAUSA = re.compile(rf"\bcausa\s+(?!rol\b|n[°º]|sobre\b|hipotecari)([A-ZÁÉÍÓÚÑ][^,;\n]{{2,100}}?{_SEP}[^,;\n]{{1,80}}?),\s+juicio", re.I)
_SUFIJOS = {"s", "a", "sa", "spa", "ltda", "limitada", "cia", "con", "y"}


def clave_caratula(t: str | None) -> str:
    """Para comparar carátulas. Sin tildes ni mayúsculas, sin puntuación, sin 'con' ni sufijos legales (S.A., SpA, Ltda,
    Limitada). Dos impresiones sin diferencias relevantes dan la misma clave (decisión de Diego)."""
    import unicodedata
    t = "".join(c for c in unicodedata.normalize("NFKD", t or "") if not unicodedata.combining(c)).lower()
    return " ".join(w for w in re.findall(r"[a-z0-9ñ]+", t) if w not in _SUFIJOS)


def caratula(texto: str) -> dict:
    """Devuelve {'caratula': {valor, cita}, 'alertas': [...]}. Si hay dos carátulas distintas de verdad, no elige y deja
    duda de lectura. Si no encuentra ninguna, deja el dato faltante."""
    hallados = []
    for m in _CAR_COMILLAS.finditer(texto):
        v = m.group(1).strip()
        # Arreglo 1 del ajuste (14-10 avisos 30, 31, 32 y 39). Entre la comilla de cierre de "‘Audiencia de remates’" y la de
        # apertura de "‘Mis Remates’" quedaba "dispuesto para tal efecto. Una vez que el postor...". Una carátula empieza con
        # mayúscula o número, no trae un punto seguido de mayúscula y no es larga.
        # (salvo "S.A. Con Quiroga", 14-10 aviso 52, donde lo que sigue al punto es el "Con" que separa las partes)
        # El punto cuenta como fin de frase solo si sigue a una palabra de 5 letras o más, así "Cía. Ltda" no corta (06-10
        # aviso 68). Aplicado con la aprobación de Diego del 17 de Octubre, después de la validación.
        if not re.match(r"[A-Z0-9ÁÉÍÓÚÑ]", v) or re.search(r"(?:^|\s)[^\s.]{5,}\.\s+(?![Cc][Oo][Nn]\s)[A-ZÁÉÍÓÚ]", v) or len(v) > 130:
            continue
        if _CAR_ANTES.search(texto[max(0, m.start() - 80):m.start()]):
            hallados.append((m.start(1), v))
    for patron in (_CAR_SIN, _CAR_CAUSA):
        for m in patron.finditer(texto):
            hallados.append((m.start(1), m.group(1).strip().rstrip(",")))
    distintos = []
    for ini, v in sorted(hallados):
        k = clave_caratula(v)
        if not k:
            continue
        if not any(k == d[2] or k in d[2] or d[2] in k for d in distintos):
            distintos.append((ini, v, k))
    if not distintos:
        return {"caratula": {"valor": None, "cita": None},
                "alertas": [("dato_faltante", "El programa no encontró la carátula de la causa. Revísala en el aviso.")]}
    if len(distintos) > 1:
        return {"caratula": {"valor": None, "cita": None},
                "alertas": [("revisar_lectura", "El aviso trae dos carátulas distintas (" + " y ".join(f"'{d[1]}'" for d in distintos[:3])
                             + "). Puede tener otro aviso pegado. Revísalo en la página.")]}
    v = distintos[0][1]
    return {"caratula": {"valor": v, "cita": v}, "alertas": []}


# --- Todo junto ----------------------------------------------------------------------------------------------
def extraer(texto: str, fecha_edicion: str | None = None) -> dict:
    """Corre las cinco extracciones. Si el trozo trae dos avisos pegados (dos fechas de remate distintas),
    NO entrega ningún dato. Solo la alerta, para que Diego lea el aviso en su página."""
    fh, mc, ga, mo, tr = fecha_y_hora(texto, fecha_edicion), minimo_y_costas(texto), garantia(texto), modalidad(texto), tribunal(texto)
    ins = inscripcion(texto, fecha_edicion)
    ca = caratula(texto)
    alertas = fh["alertas"] + mc["alertas"] + ga["alertas"] + mo["alertas"] + tr["alertas"] + ins["alertas"] + ca["alertas"]
    pegado = any("dos avisos pegados" in t for _, t in fh["alertas"])
    if pegado:
        return {"pegado": True, "fecha_remate": {"valor": None, "cita": None}, "hora_remate": {"valor": None, "cita": None},
                "minimo": {"monto": None, "moneda": None, "costas_clp": None, "cita": None},
                "garantia": {"porcentaje": None, "base": "sin_dato", "base_origen": None, "monto": None, "moneda": None, "cita": None},
                "modalidad": {"valor": "sin_dato", "cita": None}, "plataforma": None, "tribunal": {"valor": None, "cita": None},
                "inscripcion": {"lista": [], "clave": None}, "caratula": {"valor": None, "cita": None},
                "alertas": [a for a in fh["alertas"] if "dos avisos pegados" in a[1]]}
    return {"pegado": False, "fecha_remate": fh["fecha_remate"], "hora_remate": fh["hora_remate"], "minimo": mc["minimo"],
            "garantia": ga["garantia"], "modalidad": mo["modalidad"], "plataforma": mo["plataforma"], "tribunal": tr["tribunal"],
            "inscripcion": {"lista": ins["inscripcion"], "clave": ins["clave"]}, "caratula": ca["caratula"], "alertas": alertas}
