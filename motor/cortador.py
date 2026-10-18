"""Motor parte 2. Rollo único y corte por aviso. Solo código, sin IA.

Entrada. Las páginas de un rollo en orden de lectura (lo que entrega navegacion_logica.ordenar).
Salida. Lista de avisos con su texto, su rol sacado por código y las páginas por donde pasa.

Pasos.
1. Recortar cada página a la zona de la sección 1616 (desde su primera cornisa y, en la última
   página, hasta el código de la sección siguiente, por ejemplo 1635 o 1640).
2. Quitar las cornisas "1616 / Remates de / propiedades" que el diario repite en cada columna,
   las flechas "MÁS AVISOS..." y "VIENEN DE...", y unir las palabras cortadas por guion.
3. Cortar por inicio de aviso. Si un trozo queda con dos roles distintos, se parte por el cierre
   del primer aviso. Si no se puede partir, se marca para revisión y nunca se descarta.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

# --- 1 y 2. Limpieza -------------------------------------------------------
CORNISA_LINEAS = re.compile(r"(?m)^\s*1616\s*\n\s*Remates\s+de\s*\n\s*propiedades\s*$\n?")
SECCION_SIGUIENTE = re.compile(r"(?m)^\s*(1(?:6[2-9]\d|[7-9]\d\d))\s*\n\s*[A-ZÁÉÍÓÚ][a-záéíóúñ]+")
FLECHAS = re.compile(r"(?:AVISOS\s+ECON[OÓ]MICOS\s+CLASIFICADOS\s+)?(?:M[AÁ]S\s+AVISOS\s+ECON[OÓ]MICOS\s+CLASIFICADOS\s+EN|VIENEN?\s+DE)\s+P[AÁ]G(?:INA|\.)?\s*[A-Z]\s*\d{1,3}(?!\d)", re.I)


def recortar_pagina(texto: str, es_ultima: bool) -> str:
    m = re.search(r"(?m)^\s*1616\s*\n\s*Remates\s+de\s*\n\s*propiedades\s*$", texto)
    if not m:
        return ""
    t = texto[m.start():]
    if es_ultima:
        s = SECCION_SIGUIENTE.search(t)
        if s:
            t = t[:s.start()]
    return t


def _guion_fin_de_renglon(m):
    """Guion al final de un renglón (2026-10-16). Medido en las 7 ediciones (14.765 casos).
    Letra + minúscula ("Condo-" "minio", "SAN-" "tiago") es palabra cortada. Se une sin guion.
    MAYÚSCULA + MAYÚSCULA se une como antes (solo 2 casos, el "Rol N° C-" "C-936-2026" que el diario imprime mal).
    Todo lo demás es un guion real y se deja. Antes se borraba y fabricaba roles "mal impresos" que el diario no imprimió
    ("Rol: C-2462-" "2022" quedaba "C-24622022", "Rol C-" "2461-2022" quedaba "C2461-2022").
    Después de un punto o de un espacio queda el guion y un espacio ("$ 54.327.614.-" "precio" queda "614.- precio")."""
    a, b = m.group(1), m.group(2)
    if a.isalpha() and (b.islower() or (a.isupper() and b.isupper())):
        return a
    if a == "." or a.isspace():
        return a + "- "
    return a + "-"


def limpiar(texto: str) -> str:
    t = CORNISA_LINEAS.sub("", texto)
    t = FLECHAS.sub("\n", t)   # salto, no espacio: así la palabra cortada por guion antes de la flecha se une
    t = re.sub(r"([\s\S])-\s*\n\s*(?=(\S))", _guion_fin_de_renglon, t)   # guion al final de renglón (si queda al final de la página, se une en construir_rollo)
    return re.sub(r"\s+", " ", t).strip()


# --- Rol por código ----------------------------------------------------------
_NUM = r"(\d{1,2}\.\d{3}|\d{1,6})"
_ANIO = r"((?:19|20)\d\d)(?!\d)"
PATRONES_ROL = [
    # Rol C-1234-2025, Rol N° C-1.301-2026, rol c- 21629-2024, Rol N.° C-21650-2024, Rol: C-5107-2022, Rol N° 2087/2024, CC-936-2026
    ("ROL", re.compile(r"\bRol(?!\s+de\s+aval)\s*(?:N\.?\s*[°º]\.?)?\s*:?\s*(?:C{1,2}\s*-?\s*)?" + _NUM + r"\s*[-/]\s*" + _ANIO, re.I)),
    # Rol C-39902025 (sin guion entre número y año)
    ("ROL", re.compile(r"\bRol(?!\s+de\s+aval)\s*(?:N\.?\s*[°º]\.?)?\s*:?\s*C{1,2}\s*-?\s*(\d{1,5})" + _ANIO, re.I)),
    # Rol V 310-2025 o V-310-2025 (causas voluntarias), visto el 01-09
    ("ROL", re.compile(r"\bRol\s*(?:N\.?\s*[°º]\.?)?\s*:?\s*V\s*-?\s*" + _NUM + r"\s*-\s*" + _ANIO, re.I)),
    # Rol C-1113 7-2023 (espacio dentro del número), visto el 01-09
    ("ROL", re.compile(r"\bRol\s*(?:N\.?\s*[°º]\.?)?\s*:?\s*C{1,2}\s*-\s*(\d{1,4} \d{1,4})\s*-\s*" + _ANIO, re.I)),
    # Rit C-3908-2025 (juzgados laborales)
    ("RIT", re.compile(r"\bRit\s*:?\s*C\s*-\s*" + _NUM + r"\s*-\s*" + _ANIO, re.I)),
    # expediente C-5915-2025, C-8694-2024, C14838-2024 sin la palabra Rol
    ("ROL", re.compile(r"(?<![\w.-])[Cc]{1,2}\s*-?\s*" + _NUM + r"\s*-\s*" + _ANIO)),   # incluye c-26036-2016 en minúscula (10-11)
]


def roles_en(texto: str) -> list[tuple[str, str, str, int, str]]:
    """Devuelve (tipo, numero, anio, posicion, impreso) sin repetir posiciones."""
    hallados, ocupado = [], []
    for tipo, pat in PATRONES_ROL:
        for m in pat.finditer(texto):
            if any(a <= m.start() < b for a, b in ocupado):
                continue
            ocupado.append((m.start(), m.end()))
            hallados.append((tipo, m.group(1).replace(".", "").replace(" ", "").lstrip("0") or "0", m.group(2), m.start(), m.group(0)))
    return sorted(hallados, key=lambda x: x[3])


# --- 3. Corte por aviso --------------------------------------------------------
_ORD_PAL = (r"PRIMER|PRIMERO|SEGUNDO|TERCER|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO|"
            r"D[EÉ]CIMO|UND[EÉ]CIMO|DUOD[EÉ]CIMO|VIG[EÉ]SIMO|TRIG[EÉ]SIMO")
ORDINAL = rf"(?:\d{{1,2}}\s*(?:°|º|er|ER|o)?|(?:{_ORD_PAL})(?:\s+(?:{_ORD_PAL}))?)(?:\s*\(\d{{1,2}}\s*°\))?"
INICIO = re.compile(
    r"(?:EXTRACTO\s+|AVISO\s+)?REMATE\b"                                   # REMATE en mayúsculas, aunque venga pegado (SecretarioREMATE)
    r"|EXTRACTO\.?\s+JUZGADO\b"                                             # EXTRACTO. JUZGADO COBRANZA (visto el 06-08, pegado a un correo)
    r"|EXTRACTO\s+\d{1,2}\s*[°º]\s*(?:JUZGADO|TRIBUNAL)\b"                  # Mercurio, 17 de Octubre. "Ltda.’. EXTRACTO 3°JUZGADO CIVIL DE Viña del Mar" iba pegado al rol 1442-2024 (16-10 y 17-10)
    r"|(?<=[a-záéíóúñ] )\d{1,2}\s*[°º]\s+JUZGADO\s+CIVIL\b(?=.{0,120}?\b(?:[Rr]ematar[áa]|[Rr]emata|[Ss]ubastar[áa])\b)"
                                                                            # "pagarse al contado 15° JUZGADO CIVIL SANTIAGO. ... Rematará" sin punto antes (visto el 2026-10-06)
    r"|(?:(?<=\. )|(?<=\.’ )|(?<=\.” )|(?<=\.\) )|^)(?:"                    # o un encabezado de tribunal al comenzar una oración
    rf"(?:ANTE\s+(?:EL\s+)?)?{ORDINAL}\s+(?:JUZGADO|TRIBUNAL|JUZ)"
    r"|JUZGADO\s+(?:DE\s+)?(?:COBRANZA|LETRAS|FAMILIA)"
    r"|EXTRACTO\s+(?:PARTICI|NOTIFICACI)"
    r"|(?:EXTRACTO\.?\s+)?ANTE\s+(?:(?:EL|LA)\s+)?(?:SEÑORA?\s+)?JUEZ"          # EXTRACTO. ANTE EL SEÑOR JUEZ Árbitro (pegado al 30° Civil, visto el 2026-10-06)
    r"|(?:[A-ZÁÉÍÓÚÑ]+\s+){1,4}REMATA\b"                                  # COMUNA PROVIDENCIA REMATA (partidor sin rol, visto el 2026-10-11)
    r"|JUEZA?\s+[ÁA]RBITR[OA]\b"                                          # JUEZ ÁRBITRO ARTURO GÓMEZ Tomás (pegado a Cobranza, visto el 2026-10-06)
    r"|JUEZ\s+PARTIDOR\b"                                                  # JUEZ PARTIDOR, CRISTIÁN LESCOT Jerez, rematará (sin rol, visto el 2026-10-14)
    r"|(?:PRIMER|SEGUNDO|TERCER)\s+LLAMADO\b"                              # TERCER LLAMADO - AVISO DE REmate (sin rol, visto el 2026-10-14)
    r")")
CIERRE = re.compile(r"(?:(?:El|La)\s+)?Secretar[ií]\w*(?:\s*\(\w+\))?(?:\s*/\s*a)?\.?|Actuario[^.]{0,60}\.|Ministro de Fe\.?", re.I)


@dataclass
class Aviso:
    orden: int
    texto: str
    inicio: int                       # posición en el rollo limpio
    paginas: list = field(default_factory=list)
    roles: list = field(default_factory=list)      # [(tipo, numero, anio)] distintos
    rol_impreso: str | None = None
    tipo_id: str = "SIN_ROL"
    rol: str | None = None
    anio: str | None = None
    revisar: str = ""                 # motivo si el corte quedó dudoso


def _distintos(roles):
    vistos, out = set(), []
    for tipo, n, a, _, _ in roles:
        if (n, a) not in vistos:
            vistos.add((n, a)); out.append((tipo, n, a))
    return out


def construir_rollo(paginas: list[tuple[str, str]]) -> tuple[str, list[tuple[int, str]]]:
    """paginas = [(nombre, texto_crudo)] en orden. Devuelve el rollo limpio y dónde empieza cada página."""
    rollo, marcas = "", []
    for i, (nombre, texto) in enumerate(paginas):
        limpio = limpiar(recortar_pagina(texto, es_ultima=(i == len(paginas) - 1)))
        if re.search(r"[a-záéíóúñ]-$", rollo) and re.match(r"[a-záéíóúñ]", limpio):
            rollo = rollo[:-1]          # palabra cortada por guion entre una página y la siguiente ("Parcela-" | "ción")
        elif rollo:
            rollo += " "
        marcas.append((len(rollo), nombre))
        rollo += limpio
    return rollo, marcas


def _paginas_de(a: int, b: int, marcas) -> list[str]:
    out = []
    for k, (p, nombre) in enumerate(marcas):
        fin = marcas[k + 1][0] if k + 1 < len(marcas) else 10**12
        if p < b and fin > a:
            out.append(nombre)
    return out


TRIBUNAL_MAYUSCULAS = re.compile(r"(?<=\s)(?:JUZGADO|TRIBUNAL)\s+(?:DE\s+)?[A-ZÁÉÍÓÚÑ]{3,}\b")   # sin re.I a propósito


def cortar(rollo: str, marcas) -> list[Aviso]:
    cortes = sorted({0} | {m.start() for m in INICIO.finditer(rollo)})
    trozos = [(a, b) for a, b in zip(cortes, cortes[1:] + [len(rollo)])]
    # Unir fragmentos mínimos ("REMATE." suelto) con el trozo siguiente
    unidos = []
    for a, b in trozos:
        if unidos and len(rollo[unidos[-1][0]:unidos[-1][1]].strip()) < 25 and not roles_en(rollo[unidos[-1][0]:unidos[-1][1]]):
            unidos[-1] = (unidos[-1][0], b)
        else:
            unidos.append((a, b))
    # Segunda pasada. Trozos con dos roles distintos se parten tras el cierre del primer aviso.
    finales = []
    pendientes = list(unidos)
    while pendientes:
        a, b = pendientes.pop(0)
        t = rollo[a:b]
        rs = roles_en(t)
        dist = _distintos(rs)
        if len(dist) >= 2:
            primero = dist[0][1:]
            ult_pos_primero = max(r[3] + len(r[4]) for r in rs if (r[1], r[2]) == primero)
            # El cierre válido va seguido del comienzo de otro aviso (mayúscula o número). Así no se parte en
            # "entregado materialmente en la secretaría del tribunal" (visto el 2026-10-09, rol 1911-2020).
            c = next((c for c in CIERRE.finditer(t, ult_pos_primero)
                      if re.match(r"\s*[A-ZÁÉÍÓÚÑ0-9]", t[c.end():])), None)
            otro = min(r[3] for r in rs if (r[1], r[2]) != primero)
            if c and c.end() < otro and c.end() < len(t) - 20:
                pendientes.insert(0, (a + c.end(), b))
                finales.append((a, a + c.end(), ""))
                continue
            # Sin cierre. Si entre los dos roles hay UN solo nombre de tribunal escrito en mayúsculas, ahí empieza
            # el segundo aviso (visto el 2026-10-09: "...Audiencias de Remate JUZGADO DE LETRAS DE COLINA, ...").
            # Si hay cero o varios, no se adivina y queda para revisión.
            if not c:
                cand = [m.start() for m in TRIBUNAL_MAYUSCULAS.finditer(t, ult_pos_primero, otro)]
                if len(cand) == 1:
                    pendientes.insert(0, (a + cand[0], b))
                    finales.append((a, a + cand[0], ""))
                    continue
            finales.append((a, b, "dos roles distintos en un mismo trozo y no se encontró dónde partir"))
            continue
        finales.append((a, b, ""))
    avisos = []
    for i, (a, b, motivo) in enumerate(finales, 1):
        t = rollo[a:b].strip()
        if not t:
            continue
        rs = roles_en(t)
        dist = _distintos(rs)
        if not motivo and re.search(r"[a-záéíóúñ]-$", t):
            motivo = "el aviso termina con una palabra cortada. Puede faltarle su continuación (columnas desordenadas)"
        if not motivo and re.match(r"[a-záéíóúñ]", t):
            motivo = "el aviso empieza en minúscula. Puede ser la continuación de otro aviso (columnas desordenadas)"
        av = Aviso(orden=len(avisos) + 1, texto=t, inicio=a, paginas=_paginas_de(a, b, marcas), roles=dist, revisar=motivo)
        if dist:
            av.tipo_id, av.rol, av.anio = dist[0]
            av.rol_impreso = next(r[4] for r in rs if (r[1], r[2]) == (av.rol, av.anio))
        avisos.append(av)
    return avisos
