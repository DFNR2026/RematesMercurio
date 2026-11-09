"""Ciclo 2 de mejora, tanda 2 (8 de Noviembre de 2026). Formato de condominios y edificios en la columna Dirección.

Decisión de Diego. El programa trataba todo inmueble como calle, número y unidad. En un condominio o edificio la calle de
la unidad, la entrada y el estacionamiento pueden ser distintos. Cuando el aviso habla de un condominio o un edificio, la
dirección dice, en una sola celda.
1. Si es condominio de departamentos o de casas (solo "Condominio" si no se puede saber), o edificio, con su nombre.
2. La dirección que comprobó la IA (calle, número y unidad). Si el aviso trae una calle interior, esa es la de la unidad.
3. Los estacionamientos y bodegas que se rematan con la unidad.
4. La entrada si es por otra calle.

Todo sale del texto del aviso por código, sin IA. El nombre y la entrada se copian tal como están en el aviso. Solo se
usa con un remate por aviso, porque con varios no se sabe a cuál pertenece cada pieza. Si el aviso no habla de condominio
ni de edificio, la dirección queda igual que antes.
"""
from __future__ import annotations
import re
from motor.numeros_texto import palabras_a_cifras
from motor.direccion import calle_clave, norm

_Q = "‘’“”\"'#«»"
_CONECTOR = r"(?:del|de|las|la|los|el|y)"
_PALABRA = r"(?:[A-ZÁÉÍÓÚÑ0-9][\wÁÉÍÓÚÑáéíóúñ\.\-]*)"
_CONJ = re.compile(r"\b(condominio|edificio)s?\b", re.I)
_NO_NOMBRE = re.compile(r"^(?:ubicad|denominad|singulariz|consistente|correspondiente|respectiv|en|con|que|N[°º]|n[uú]mero)", re.I)


def _nombre(texto: str, desde: int) -> str | None:
    """El nombre que sigue a 'Condominio' o 'Edificio', entre comillas o con mayúscula inicial. None si no hay."""
    s = texto[desde:desde + 100]
    s = re.sub(r"^\s*(?:denominad[oa]s?|llamad[oa]|de\s+nombre)\s+", " ", s, flags=re.I)
    m = re.match(rf"\s*[{_Q}]([^{_Q}]{{2,60}})[{_Q}]", s)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.match(rf"\s+({_PALABRA}(?:\s+(?:{_CONECTOR}\b|{_PALABRA})){{0,6}})", s)
    if not m:
        return None
    n = re.split(r"\s+(?:N[°º.]?|n[uú]mero|N[uú]mero)(?:\s|$)", m.group(1))[0]   # el nombre termina donde empieza el número de la calle
    n = re.sub(rf"(?:\s+{_CONECTOR})+$", "", n).strip(" .-")
    if not n or _NO_NOMBRE.match(n):
        return None
    return n


_NUMERO_PALABRA = r"(?:uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)"


def _es_subdivision(nombre: str | None) -> bool:
    """'Edificio B', 'Edificio 5', 'Edificio Cuatro', 'Edificio Sur', 'Edificio B del Conjunto Habitacional' son partes
    del condominio, no su nombre."""
    if not nombre:
        return False
    return (re.fullmatch(rf"[A-Z0-9\-]{{1,4}}(?:\s+(?:[A-Z0-9]{{1,2}}|{_NUMERO_PALABRA}))?|[IVXL]+|{_NUMERO_PALABRA}|norte|sur|oriente|poniente", nombre, re.I) is not None
            or re.search(r"\bdel?\s+(?:condominio|conjunto|proyecto)\b", nombre, re.I) is not None
            or re.match(r"(?:primera|segunda|tercera|cuarta)\s+etapa\b", nombre, re.I) is not None)


def conjunto(texto: str) -> dict | None:
    """{'condominio': bool, 'nombre_condominio', 'edificio': bool, 'nombre_edificio'} o None si el aviso no habla de
    condominio ni de edificio."""
    r = {"condominio": False, "nombre_condominio": None, "edificio": False, "nombre_edificio": None}
    for m in _CONJ.finditer(texto):
        k = m.group(1).lower()
        n = _nombre(texto, m.end())
        if _es_subdivision(n):
            n = None
        r[k] = True
        if n and not r[f"nombre_{k}"]:
            r[f"nombre_{k}"] = n
    return r if (r["condominio"] or r["edificio"]) else None


_NUM = r"(?:n[uú]meros?\s+|N[°º.]\s*)?((?:\d[\w\-]*(?:(?:\s*,\s*|\s+y\s+)(?:N[°º.]\s*)?\d[\w\-]*(?![°º\w]))*)|(?:[a-záéíóú]+(?:\s+y\s+[a-záéíóú]+|\s+[a-záéíóú]+){0,4}))"


def piezas(texto: str, clave: str) -> list:
    """Números de los estacionamientos o bodegas que nombra el aviso ('estacionamiento N° 63', 'estacionamiento número
    quinientos cuatro'). Solo los que traen número."""
    out = []
    for m in re.finditer(rf"\b{clave}s?\s+{_NUM}", texto, re.I):
        v = palabras_a_cifras(m.group(1)) or ""
        k = re.match(r"\d[\w\-]*(?:(?:\s*,\s*|\s+y\s+)(?:N[°º.]\s*)?\d[\w\-]*(?![°º\w]))*", v)   # "1° piso" no es otro estacionamiento
        if not k:
            continue
        for x in re.findall(r"\d[\w\-]*", k.group(0)):        # "estacionamientos 1 y 2" son dos (rol 5010-2025)
            if not re.fullmatch(r"\d{4}", x) and x not in out:    # un año no es un estacionamiento
                out.append(x)
    return out


_ACC = re.compile(r"acceso\s+(?:(principal|com[uú]n|peatonal|vehicular|particular)\s+)?(?:a\s+(?:los\s+)?estacionamientos?\s+)?"
                  r"por\s+((?:la\s+)?(?:calle|avenida|av\.|avda\.?|pasaje)?\s*[^,;]{3,70}?)"
                  r"(?=,|;|\.\s|\.$|\s+y\s+con|\s+(?:de\s+la\s+)?comuna|$)", re.I)


def accesos(texto: str) -> list:
    """[(tipo de acceso, calle tal como está en el aviso)]."""
    return [((m.group(1) or "").lower(), re.sub(r"\s+", " ", m.group(2)).strip()) for m in _ACC.finditer(texto)]


_INTERIOR = re.compile(r"\b((?:calle|pasaje)\s+interior\s+[A-ZÁÉÍÓÚÑ][^,;]{1,40}?)\s+(?:N[°º]\s*|n[uú]mero\s+)(\d[\d\s\-]*\d|\d)")


def _lista(nombre: str, xs: list) -> str:
    return f"{nombre}{'s' if len(xs) > 1 else ''} {' y '.join(xs) if len(xs) < 3 else ', '.join(xs[:-1]) + ' y ' + xs[-1]}"


def describir(texto: str, direccion: str, calle_ia: str | None) -> str:
    """La dirección en el formato de condominio. Si el aviso no habla de condominio ni de edificio, devuelve la misma."""
    c = conjunto(texto)
    if not c or not direccion:
        return direccion
    unidad = norm(direccion.split(",", 1)[1]) if "," in direccion else ""
    if c["condominio"]:
        tipo = " de departamentos" if re.search(r"\b(departamento|depto|dpto)\b", unidad) else (
               " de casas" if re.search(r"\b(casa|vivienda)\b", unidad) else "")
        cabeza = f"Condominio{tipo}"
        if c["nombre_condominio"]:
            cabeza += f" {c['nombre_condominio']}"
        elif c["nombre_edificio"]:
            cabeza += f", Edificio {c['nombre_edificio']}"
    else:
        nombre = re.sub(r"^edificios?\s+", "", c["nombre_edificio"] or "", flags=re.I)   # sin "Edificio Edificio" (rol 14985-2025)
        cabeza = "Edificio" + (f" {nombre}" if nombre else "")
    calle = calle_clave(calle_ia) if calle_ia else ""
    partes, entradas = [cabeza], []
    i = _INTERIOR.search(texto)
    if i and calle and calle_clave(i.group(1).split(" interior ", 1)[-1]) not in calle:
        # La unidad está en una calle interior. La calle que dio la IA es la entrada del condominio.
        partes.append(f"{i.group(1)} {re.sub(r'\s+', '', i.group(2))}" + (f", {direccion.split(',', 1)[1].strip()}" if "," in direccion else ""))
        entradas.append(("", direccion.split(",", 1)[0].strip()))
    else:
        partes.append(direccion)
    # Lo que ya va en la dirección como unidad no se repite ("estacionamiento 1" rematado solo, rol 7898-2024)
    ya = lambda tipo: {k for k in re.findall(rf"\b{tipo}s?\s+(?:N[°º.]?\s*|n[uú]mero\s+)?(\d[\w\-]*)", direccion.split(",", 1)[1] if "," in direccion else "", re.I)}
    est = [x for x in piezas(texto, "estacionamiento") if x not in ya("estacionamiento")]
    bod = [x for x in piezas(texto, "bodega") if x not in ya("bodega")]
    if est:
        partes.append(_lista("Estacionamiento", est))
    if bod:
        partes.append(_lista("Bodega", bod))
    for tipo, a in accesos(texto):
        if calle and calle in calle_clave(a) or calle and calle in norm(a):
            continue                                          # la entrada es la misma calle de la dirección
        if all(norm(a) != norm(b) for _, b in entradas):
            entradas.append((tipo, a))
    for tipo, a in entradas:
        partes.append(f"Acceso {tipo + ' ' if tipo else ''}por {a}")
    return ". ".join(p.strip().rstrip(".") for p in partes)
