"""Ciclo 2 de mejora, tanda 1 (8 de Noviembre de 2026). Aplica los arreglos D8, D3, D10, D1b, D9, D6, D5a, D4a, D4b y D5c
sobre una COPIA del proyecto. Uso. python aplicar_tanda1.py RAIZ_DE_LA_COPIA
Cada reemplazo exige encontrar el texto original exactamente una vez. Si el código cambió, se detiene sin escribir nada."""
import sys, os
RAIZ = sys.argv[1]
pendientes = {}
def rep(p, pares):
    ruta = os.path.join(RAIZ, *p.split("/"))
    s = pendientes.get(ruta) or open(ruta, encoding="utf-8").read()
    for a, b in pares:
        assert s.count(a) == 1, (p, a[:80]); s = s.replace(a, b, 1)
    pendientes[ruta] = s

# D8
rep("motor/orden_columnas.py",[("""        fila = [b for b in secundarias if abs(b[2] - a[2]) <= 3]
        if len({min(bordes, key=lambda x: abs(x - b[1])) for b in fila}) >= 2:""",
"""        # Ciclo 2 de mejora, tipo D8 (8 de Noviembre de 2026). Una franja verdadera repite el MISMO número de sección en 3
        # columnas o más (las 3 reales guardadas, "1309" en 5 y 6 columnas). Dos secciones distintas que empiezan a la misma
        # altura en dos columnas ("1612" y "1616", B09 del 5 de Noviembre) son el flujo normal del diario y no se cortan.
        fila = [b for b in secundarias if abs(b[2] - a[2]) <= 3 and str(b[0]).strip() == str(a[0]).strip()]
        if len({min(bordes, key=lambda x: abs(x - b[1])) for b in fila}) >= 3:""")])

# D3
rep("motor/ia_comun.py",[('''    sin = re.sub(r"\\s+", "", frase)
    if not sin:
        return None
    pos = [i for i, c in enumerate(texto) if not c.isspace()]
    compacto = "".join(texto[i] for i in pos)''',
'''    # Ciclo 2 de mejora, tipo D3 (decisión de Diego del 8 de Noviembre de 2026). Además de los espacios se aceptan como
    # iguales las comillas rectas y curvas (la IA copia ' donde el diario imprime ‘ ’). Mayúsculas y palabras siguen exactas.
    sin = re.sub(r"\\s+", "", frase).translate(_COMILLAS)
    if not sin:
        return None
    pos = [i for i, c in enumerate(texto) if not c.isspace()]
    compacto = "".join(texto[i] for i in pos).translate(_COMILLAS)'''),
("def buscar_frase(", '_COMILLAS = str.maketrans({c: "\'" for c in "‘’‚‛′`´"} | {c: \'"\' for c in "“”„‟″«»"})\n\n\ndef buscar_frase(')])

# D10 y D1b
rep("motor/numeros_texto.py",[('    partes = re.split(r"(\\s+)", texto)',
'''    # Ciclo 2 de mejora, tipo D10 (8 de Noviembre de 2026). "cuatro-A" es "4-A". El guion pegado a una letra sola separa el
    # número de la letra (rol 4294-2025, "la vivienda número cuatro-A").
    partes = re.split(r"(\\s+|-(?=[A-Za-z]\\b))", texto)'''),
('''            while j + 2 < len(partes) and _sin_tildes(partes[j + 2]) in PALABRAS:
                j += 2''',
'''            while j + 2 < len(partes) and _sin_tildes(partes[j + 2]) in PALABRAS:
                # Ciclo 2 de mejora, tipo D1b (8 de Noviembre de 2026). La misma regla de D1. La "y" solo une una decena con
                # una unidad. "Parcela número cuatro y un 6,25%" daba "Parcela número 5" (rol 6004-2023).
                if _sin_tildes(partes[j + 2]) == "y" and not (_sin_tildes(partes[j]) in _DECENAS_Y and j + 4 < len(partes)
                                                             and _sin_tildes(partes[j + 4]) in _UNO_A_NUEVE):
                    break
                j += 2''')])

# direccion: D9, D6, D5a, D4a, D4b
rep("motor/direccion.py",[
('def unidad_clave(t: str | None) -> tuple | None:\n    if not t:\n        return None\n    t = norm(palabras_a_cifras(t))',
'''# Ciclo 2 de mejora, tipo D9 (8 de Noviembre de 2026). "departamento 2.708" es el 2708 y no el 2 (rol 14652-2025).
_MILES = re.compile(r"(?<=\\d)\\.(?=\\d{3}(?!\\d))")

def unidad_en_cifras(t: str | None) -> str | None:
    """La unidad con los números en cifras y sin puntos de miles."""
    t = palabras_a_cifras(t)
    return _MILES.sub("", t) if t else t

def unidad_clave(t: str | None) -> tuple | None:
    if not t:
        return None
    t = norm(unidad_en_cifras(t))'''),
('    unidad = palabras_a_cifras(x.get("unidad"))          # se guarda en cifras (arreglo 1 del ajuste, 14-10 avisos 16 y 42)',
 '    unidad = unidad_en_cifras(x.get("unidad"))          # se guarda en cifras (arreglo 1 del ajuste, 14-10 avisos 16 y 42) y sin puntos de miles (D9)'),
('''        if not re.search(r"\\d", unidad):
            motivos.append("La unidad que dio la IA no trae número.")
        fu = buscar_frase(x.get("frase_unidad"), texto)''',
'''        fu = buscar_frase(x.get("frase_unidad"), texto)
        if not re.search(r"\\d", unidad) and not _unidad_con_letra(unidad, fu):
            motivos.append("La unidad que dio la IA no trae número.")'''),
('''        if not pedidos:
            motivos.append("La IA no dio el número de la calle.")''',
'''        if not pedidos and _MARCA_NUMERO.search(frase):
            # Ciclo 2, tipo D5a (decisión de Diego del 8 de Noviembre de 2026). Calle sin número solo si la frase no trae
            # ninguna marca de número ("s/n", "pasaje 18 Norte ’C’" de Talca). Si dice "N°" o "número" falta el número.
            motivos.append("La IA no dio el número de la calle.")'''),
('''        if not motivos:
            # el número''','''        if not motivos and pedidos:
            # el número'''),
('''        direccion = f"{x['calle'].strip()} {numero}" + (f", {unidad.strip()}" if unidad else "")''',
'''        sn = " s/n" if not numero and re.search(r"s/n|sin\\s+n[uú]mero", frase, re.I) and "s/n" not in x["calle"].lower() else ""
        direccion = (f"{x['calle'].strip()} {numero}" if numero else f"{x['calle'].strip()}{sn}") + (f", {unidad.strip()}" if unidad else "")'''),
('''        direccion = frase[:200] + (f", {unidad.strip()}" if unidad and norm(unidad) not in norm(frase) else "")''',
'''        direccion = frase[:200] + (f", {unidad.strip()}" if unidad and norm(unidad) not in norm(frase) and unidad_clave(unidad) != unidad_clave(frase) else "")'''),
('''    if [clave_inmueble(x) for x in a] != [clave_inmueble(x) for x in b]:
        base["motivos"].append("Las dos lecturas de la IA no coinciden."); return base''',
'''    pares = [_par(x, y) for x, y in zip(a, b)]
    if any(p is None for p in pares):
        base["motivos"].append("Las dos lecturas de la IA no coinciden."); return base'''),
('''    for k, (x, y) in enumerate(zip(a, b), start=1):
        v, v2 = verificar_inmueble(x, texto), verificar_inmueble(y, texto)
        pre = f"Remate {k}. " if n_remates > 1 else ""
        if not v["ok"]:''',
'''    for k, (x, y, modo) in enumerate(pares, start=1):
        v, v2 = verificar_inmueble(x, texto), verificar_inmueble(y, texto)
        pre = f"Remate {k}. " if n_remates > 1 else ""
        if modo == "unidad" and not v["ok"] and v2["ok"]:
            # D4b. La unidad de la lectura que la trae no se comprobó. Queda la dirección sin unidad de la otra lectura.
            v = v2
        if not v["ok"]:'''),
("def verificar_inmueble(", '''# Ciclo 2 de mejora, tipo D6 (decisión de Diego del 8 de Noviembre de 2026). Una unidad con letra y sin número ("Casa H",
# rol 4485-2024) se acepta si en su frase la letra va pegada al tipo ("Casa H, del Condominio"). Una "a" suelta no cuenta.
_LETRA = re.compile(r"^\\s*(?:el|la)?\\s*(departamento|depto|dpto|casa|oficina|local|vivienda|unidad|bodega|estacionamiento|lote|sitio|parcela)"
                    r"\\s+(?:N[°º.]?\\s*|n[uú]mero\\s+)?([A-Z]{1,2})\\s*$", re.I)
_MARCA_NUMERO = re.compile(r"\\bn[°º]|\\bn[uú]mero\\b|\\bnros?\\b|\\bnum\\.", re.I)


def _unidad_con_letra(unidad: str, fu: str | None) -> bool:
    m = _LETRA.match(unidad or "")
    if not m or not fu or not m.group(2).isupper():
        return False
    # el tipo sin distinguir mayúsculas, la letra exacta y en mayúscula
    return re.search(rf"\\b(?i:{m.group(1)})s?\\s+(?:N[°º.]?\\s*|(?i:n[uú]mero)\\s+)?['‘’]?{m.group(2).upper()}['‘’]?(?![\\wÁÉÍÓÚÑáéíóúñ])", fu) is not None


def verificar_inmueble('''),
("def resolver(", '''def _nums(x: dict) -> list:
    return [(n.lstrip("0") or "0") for n in re.findall(r"\\d+", x.get("numero") or "")]


def _par(x: dict, y: dict):
    """Ciclo 2 de mejora (decisiones de Diego del 8 de Noviembre de 2026). Une dos lecturas de un mismo inmueble.
    Devuelve (principal, otra, modo) o None si no coinciden. La principal es la que se guarda si las dos se comprueban.
    - iguales. Misma clave (lo de siempre).
    - D4a. Misma calle, unidad y comuna, y una lectura trae números de acceso de más ("Carmen 660" y "Carmen 660 y 650").
      Vale solo si los números de una están todos en la otra y el primero es el mismo. Queda la que trae menos.
    - D4b. Todo igual salvo que una lectura trae unidad y la otra no. Queda la que trae unidad si su unidad se comprueba,
      si no, la dirección sin unidad (lo decide resolver)."""
    if clave_inmueble(x) == clave_inmueble(y):
        return (x, y, "iguales")
    kx, ky = clave_inmueble(x), clave_inmueble(y)
    if x.get("tipo") == y.get("tipo") == "calle" and kx[1] == ky[1] and kx[3] == ky[3] and kx[4] == ky[4]:
        nx, ny = _nums(x), _nums(y)
        if nx and ny and nx[0] == ny[0] and set(nx) != set(ny):
            if set(nx) < set(ny):
                return (x, y, "acceso")
            if set(ny) < set(nx):
                return (y, x, "acceso")
    if x.get("tipo") == y.get("tipo") and bool(x.get("unidad")) != bool(y.get("unidad")):
        sin_u = lambda k: k[:3] + k[4:] if k[0] == "calle" else (k[0], k[2])
        if sin_u(kx) == sin_u(ky):
            return (x, y, "unidad") if x.get("unidad") else (y, x, "unidad")
    return None


def resolver('''),
])

# D5c
rep("motor/extraccion.py",[('''        hallados.append({"monto": monto, "moneda": moneda, "cita": texto[a.start():m.end()], "fin": m.end(),
                         "inmueble": f"{etiqueta.group(1).lower()} {etiqueta.group(2)}" if etiqueta else None})''',
'''        # Ciclo 2 de mejora, tipo D5c (8 de Noviembre de 2026). Una sola palabra "mínimo" seguida de una lista con letras
        # ("Mínimo posturas a) departamento N° 205C $46.847.342, b) Propiedad ubicada en Pasaje Goya Sur N° 1530 $95.286.918",
        # rol 8467-2025). Cada letra con su monto es un remate. Si la letra no nombra un lote o departamento, la letra es la etiqueta.
        marca = re.search(r"(?<!\\w)([a-hA-H])\\)\\s", texto[a.end():m.start()])
        hallados.append({"monto": monto, "moneda": moneda, "cita": texto[a.start():m.end()], "fin": m.end(),
                         "inmueble": f"{etiqueta.group(1).lower()} {etiqueta.group(2)}" if etiqueta else (f"{marca.group(1).lower()})" if marca else None)})
        if marca:
            letra, pos = marca.group(1), m.end()
            while True:
                letra = chr(ord(letra) + 1)
                mk = re.compile(rf"(?<!\\w){letra}\\)\\s").search(texto, pos, pos + 250)
                if not mk:
                    break
                mm = MONTO.search(texto, mk.end(), mk.end() + 200)
                if not mm or re.search(r"%|garant[ií]a|cauci[oó]n|(?<!\\w)[a-hA-H]\\)\\s", texto[mk.end():mm.start()], re.I):
                    break
                mo, mon, raro = _a_numero(mm)
                et = _ETIQUETA.search(texto, mk.end(), mm.start())
                hallados.append({"monto": mo, "moneda": mon, "cita": texto[mk.start():mm.end()], "fin": mm.end(),
                                 "inmueble": f"{et.group(1).lower()} {et.group(2)}" if et else f"{letra.lower()})"})
                pos = mm.end()''')])
for ruta, s in pendientes.items():
    fin = "\r\n" if b"\r\n" in open(ruta, "rb").read() else "\n"   # se respeta el fin de línea que ya tiene el archivo
    open(ruta, "w", encoding="utf-8", newline=fin).write(s)
print("Tanda 1 aplicada en", len(pendientes), "archivos")
