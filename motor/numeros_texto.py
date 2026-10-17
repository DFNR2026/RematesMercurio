"""Números escritos en palabras, como los imprimen los avisos ("número ochocientos sesenta y uno", "veintiún mil
quinientos", "cero ciento sesenta y uno"). Parte 3.7b, 17 de Octubre. Lo usa el verificador de la dirección para
comprobar que el número que da la IA es el que está escrito en el aviso. Sin IA, solo reglas.
"""
import re, unicodedata

def _sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c)).lower()

_UNIDADES = {"cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
             "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
             "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiun": 21, "veintiuno": 21, "veintiuna": 21,
             "veintidos": 22, "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintisiete": 27,
             "veintiocho": 28, "veintinueve": 29, "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70,
             "ochenta": 80, "noventa": 90}
_CENTENAS = {"cien": 100, "ciento": 100, "doscientos": 200, "doscientas": 200, "trescientos": 300, "trescientas": 300,
             "cuatrocientos": 400, "cuatrocientas": 400, "quinientos": 500, "quinientas": 500, "seiscientos": 600,
             "seiscientas": 600, "setecientos": 700, "setecientas": 700, "ochocientos": 800, "ochocientas": 800,
             "novecientos": 900, "novecientas": 900, "trecientos": 300}      # "trecientos" con error de escritura, 06-10 aviso 92
PALABRAS = set(_UNIDADES) | set(_CENTENAS) | {"mil", "y"}
_TOKEN = re.compile(r"[a-zñ]+")


def palabras_a_numero(texto: str) -> str | None:
    """'ochocientos sesenta y uno' da '861'. 'cero ciento ochenta y uno' da '0181'. Devuelve None si el texto no es
    solo un número en palabras."""
    toks = _TOKEN.findall(_sin_tildes(texto))
    if not toks or any(t not in PALABRAS for t in toks) or toks[-1] in ("y",):
        return None
    ceros = ""
    while len(toks) > 1 and toks[0] == "cero":
        ceros += "0"; toks = toks[1:]
    total = actual = 0
    for t in toks:
        if t == "y":
            continue
        if t == "mil":
            total += (actual or 1) * 1000; actual = 0
        elif t in _CENTENAS:
            actual += _CENTENAS[t]
        else:
            actual += _UNIDADES[t]
    return ceros + str(total + actual)


def numeros_en(frase: str) -> set:
    """Todos los números que aparecen en la frase, en cifras ('N° 3.195', '0337', '575 y 577') o en palabras
    ('número mil ochocientos ochenta y ocho'). Las cifras se devuelven sin puntos de miles."""
    out = {re.sub(r"\.", "", m) for m in re.findall(r"\d{1,3}(?:\.\d{3})+|\d+", frase)}
    base = _sin_tildes(frase)
    toks = list(_TOKEN.finditer(base))
    i = 0
    while i < len(toks):
        if toks[i].group(0) in PALABRAS and toks[i].group(0) != "y":
            j = i
            # el número sigue mientras las palabras vengan separadas solo por espacios ("noventa/ seis mil" son dos números,
            # 06-10 aviso 102)
            while j + 1 < len(toks) and toks[j + 1].group(0) in PALABRAS and not base[toks[j].end():toks[j + 1].start()].strip():
                j += 1
            while j > i and toks[j].group(0) == "y":
                j -= 1
            n = palabras_a_numero(" ".join(t.group(0) for t in toks[i:j + 1]))
            if n:
                out.add(n)
            i = j + 1
        else:
            i += 1
    return out


def palabras_a_cifras(texto: str | None) -> str | None:
    """Reemplaza cada número en palabras por sus cifras. 'departamento A trescientos nueve' da 'departamento A 309'.
    Lo demás queda igual (14-10 avisos 16 y 42, la unidad viene en palabras y la IA la copia unas veces en palabras y
    otras en cifras)."""
    if not texto:
        return texto
    partes = re.split(r"(\s+)", texto)
    out, i = [], 0
    while i < len(partes):
        if partes[i] and _sin_tildes(partes[i]) in PALABRAS and _sin_tildes(partes[i]) != "y":
            j = i
            while j + 2 < len(partes) and _sin_tildes(partes[j + 2]) in PALABRAS:
                j += 2
            while j > i and _sin_tildes(partes[j]) == "y":
                j -= 2
            n = palabras_a_numero(" ".join(partes[i:j + 1:2]))
            if n:
                out.append(n); i = j + 1; continue
        out.append(partes[i]); i += 1
    return "".join(out)
