"""Lógica pura de navegación (sin internet). Decide qué páginas tienen remates y en qué orden se pegan.

Reglas basadas en el reconocimiento de 36 ediciones (RECONOCIMIENTO_EDICIONES_2026-10-14.md).
1. Una página es de remates si trae la cornisa "1616 Remates de propiedades".
2. Las páginas con cornisa de un mismo cuerpo se encadenan por número correlativo.
3. Las flechas "MÁS AVISOS ECONÓMICOS CLASIFICADOS EN PÁG./PÁGINA X N" y "VIENEN DE PÁGINA X N"
   unen páginas de cuerpos distintos y se confirman por los dos lados.
4. Lo que no calza genera una alarma. Nunca se descarta una página con cornisa.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

CORNISA = re.compile(r"1616\s*Remates\s*de\s*propiedades", re.I)
# Se exige "AVISOS ECONÓMICOS CLASIFICADOS" para no confundir con "MÁS AVISOS DE DEFUNCIONES".
FLECHA_SALIDA = re.compile(
    r"M[AÁ]S\s+AVISOS\s+ECON[OÓ]MICOS\s+CLASIFICADOS\s+EN\s+P[AÁ]G(?:INA|\.)?\s*([A-Z])\s*(\d{1,3})(?!\d)", re.I)
FLECHA_ENTRADA = re.compile(
    r"(?:AVISOS\s+ECON[OÓ]MICOS\s+CLASIFICADOS\s+)?VIENEN?\s+DE\s+(?:LA\s+)?P[AÁ]G(?:INA|\.)?\s*([A-Z])\s*(\d{1,3})(?!\d)", re.I)


def normalizar(texto: str) -> str:
    """Une palabras cortadas por guion al final de línea y compacta espacios."""
    texto = re.sub(r"-\s*\n\s*", "", texto)
    return re.sub(r"\s+", " ", texto)


@dataclass
class Pagina:
    cuerpo: str
    numero: int
    id_pagina: str
    texto: str = ""
    cornisas: int = 0
    salidas: list = field(default_factory=list)   # [(cuerpo, numero)]
    entradas: list = field(default_factory=list)  # [(cuerpo, numero)]

    @property
    def clave(self):
        return (self.cuerpo, self.numero)

    @property
    def nombre(self):
        return f"{self.cuerpo}{self.numero}"


def analizar_pagina(p: Pagina) -> Pagina:
    t = normalizar(p.texto)
    p.cornisas = len(CORNISA.findall(t))
    p.salidas = [(c.upper(), int(n)) for c, n in FLECHA_SALIDA.findall(t)]
    p.entradas = [(c.upper(), int(n)) for c, n in FLECHA_ENTRADA.findall(t)]
    return p


@dataclass
class Resultado:
    rollos: list            # lista de listas de Pagina, cada una en orden de lectura
    alarmas: list           # textos
    notas: list             # hechos normales que conviene registrar (ej. cuerpos paralelos)


def ordenar(paginas: list[Pagina], sin_leer: frozenset = frozenset()) -> Resultado:
    """sin_leer son las letras de los cuerpos que el lector no lee a propósito (lector_mercurio.CUERPOS_SIN_LECTURA).
    Una flecha hacia ellos no se pierde en silencio. Levanta una alarma que lo dice con claridad."""
    por_clave = {p.clave: p for p in paginas}
    alarmas, notas = [], []
    con_cornisa = {p.clave for p in paginas if p.cornisas > 0}

    # Enlaces siguiente -> anterior
    siguiente = {}
    # a) flechas de salida
    for p in paginas:
        for destino in p.salidas:
            if destino not in por_clave:
                if destino[0] in sin_leer:
                    alarmas.append(f"{p.nombre} dice que siguen avisos en {destino[0]}{destino[1]}, que está en el cuerpo {destino[0]}. "
                                   f"Ese cuerpo no se lee porque nunca había traído remates. Avise a Diego para volver a leerlo")
                else:
                    alarmas.append(f"{p.nombre} dice que siguen avisos en {destino[0]}{destino[1]}, pero esa página no existe en la edición")
                continue
            d = por_clave[destino]
            if destino not in con_cornisa:
                alarmas.append(f"{p.nombre} dice que siguen avisos en {d.nombre}, pero {d.nombre} no trae la cornisa 1616")
                con_cornisa.add(destino)  # se lee igual, por las dudas
            if p.clave not in d.entradas:
                alarmas.append(f"{p.nombre} apunta a {d.nombre}, pero {d.nombre} no confirma que vienen de {p.nombre}")
            siguiente[p.clave] = destino
    # b) flechas de entrada sin salida que las respalde
    for p in paginas:
        for origen in p.entradas:
            if origen not in por_clave:
                if origen[0] in sin_leer:
                    alarmas.append(f"{p.nombre} dice que vienen avisos de {origen[0]}{origen[1]}, que está en el cuerpo {origen[0]}. "
                                   f"Ese cuerpo no se lee porque nunca había traído remates. Avise a Diego para volver a leerlo")
                else:
                    alarmas.append(f"{p.nombre} dice que vienen avisos de {origen[0]}{origen[1]}, pero esa página no existe en la edición")
                continue
            if siguiente.get(origen) != p.clave:
                alarmas.append(f"{p.nombre} dice que vienen avisos de {por_clave[origen].nombre}, pero esa página no lo anuncia")
                siguiente.setdefault(origen, p.clave)
                con_cornisa.add(p.clave)
                con_cornisa.add(origen)
    # c) páginas correlativas del mismo cuerpo
    for (c, n) in sorted(con_cornisa):
        sig = (c, n + 1)
        if sig in con_cornisa and (c, n) not in siguiente:
            siguiente[(c, n)] = sig

    # Huecos dentro de un cuerpo (ej. B8 y B10 con cornisa pero B9 sin ella)
    cuerpos = sorted({c for c, _ in con_cornisa})
    for c in cuerpos:
        nums = sorted(n for cc, n in con_cornisa if cc == c)
        for a, b in zip(nums, nums[1:]):
            if b - a > 1 and siguiente.get((c, a)) != (c, b):
                faltan = ", ".join(f"{c}{k}" for k in range(a + 1, b))
                alarmas.append(f"Hueco en el cuerpo {c}. {c}{a} y {c}{b} traen remates pero {faltan} no trae la cornisa")

    # Armar cadenas
    previos = {}
    for o, d in siguiente.items():
        if d in previos:
            alarmas.append(f"Dos páginas ({por_clave[previos[d]].nombre} y {por_clave[o].nombre}) dicen continuar en {por_clave[d].nombre}")
        previos[d] = o
    inicios = [k for k in sorted(con_cornisa) if k not in previos]
    rollos, vistos = [], set()
    for k in inicios:
        cadena = []
        while k and k not in vistos:
            vistos.add(k)
            cadena.append(por_clave[k])
            k = siguiente.get(k)
        rollos.append(cadena)
    sueltas = con_cornisa - vistos
    if sueltas:
        alarmas.append("Páginas en un ciclo de flechas imposible. " + ", ".join(por_clave[k].nombre for k in sorted(sueltas)))
        rollos.append([por_clave[k] for k in sorted(sueltas)])

    if not rollos:
        alarmas.append("Ninguna página de la edición trae la cornisa 1616")
    elif len(rollos) > 1:
        notas.append("Hay más de un bloque de remates (" + " | ".join(
            "-".join(p.nombre for p in r) for r in rollos) +
            "). Puede ser un cuerpo reimpreso, como B y G los viernes. Se leen todos y se unen sin duplicar por rol.")
    return Resultado(rollos, alarmas, notas)
