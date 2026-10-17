"""Reordena el texto de una página según la posición impresa de cada renglón.

Motivo (verificado el 2026-10-15). En la página F9 del 2026-10-11 el visor entrega las columnas en el
orden 1, 2, 4, 5, 6, 7, 3. Pegarlas así une el final de un aviso con el comienzo de otro.
Método. Cada columna tiene arriba su cornisa de sección ("1616", "1611", etc.). Esas cornisas marcan el
borde izquierdo de cada columna. Cada renglón se asigna a la columna cuyo borde izquierdo está más cerca
por la izquierda, y se lee columna por columna, de izquierda a derecha y de arriba abajo.
Lo que está por encima de las cornisas (fecha, número de página, nombre de la sección) va primero.
Dentro de cada columna se respeta el orden original del visor. Solo se corrige el orden ENTRE columnas
(ordenar renglones por altura rompía la cornisa, cuyo "Remates de" está más alto que el "1616").
"""
from __future__ import annotations
import re


def texto_por_posicion(geo: dict) -> str | None:
    items = [i + [k] for k, i in enumerate((geo or {}).get("items") or []) if i and str(i[0]).strip() != ""]
    if not items:
        return None
    anclas = [i for i in items if re.fullmatch(r"1[5-9]\d\d", str(i[0]).strip())]
    if not anclas:
        return None
    y_cornisa = max(a[2] for a in anclas)
    # Bordes de columna. Una ancla por columna (se juntan las que están a menos de 15 puntos).
    bordes = []
    for x in sorted(a[1] for a in anclas if a[2] >= y_cornisa - 5):
        if not bordes or x - bordes[-1] > 15:
            bordes.append(x)
    if len(bordes) < 2:
        return None
    # Franjas horizontales. Si en una misma altura (bajo la fila de cornisas superior) aparecen cornisas de
    # sección en dos o más columnas, ahí parte una franja nueva que cruza la página (ej. "1300 EMPLEOS" al pie
    # de F15 del 2026-10-11). Cada franja se lee completa, columna por columna, antes de pasar a la siguiente.
    secundarias = [i for i in items if re.fullmatch(r"1\d\d\d", str(i[0]).strip()) and i[4] >= 12
                   and i[2] < y_cornisa - 5 and min(abs(i[1] - b) for b in bordes) <= 3]
    cortes = []
    for a in sorted(secundarias, key=lambda a: -a[2]):
        fila = [b for b in secundarias if abs(b[2] - a[2]) <= 3]
        if len({min(bordes, key=lambda x: abs(x - b[1])) for b in fila}) >= 2:
            techo = max(b[2] + b[4] for b in fila) + 2
            # Un título ancho (dos columnas o más) justo encima de esa fila pertenece a la franja nueva
            # (ej. "MUNDO LABORAL - CLASIFICADOS EMPLEO Y CAPACITACIÓN", 4 columnas de ancho).
            ancho_col = (bordes[-1] - bordes[0]) / (len(bordes) - 1)
            subio = True
            while subio:
                subio = False
                for w in items:
                    if w[3] >= 2 * ancho_col and techo <= w[2] <= techo + 100 and w[2] + w[4] + 2 > techo:
                        techo, subio = w[2] + w[4] + 2, True
            if not cortes or abs(cortes[-1] - techo) > 3:
                cortes.append(techo)
    franja = lambda y: sum(1 for c in cortes if y < c)   # 0 = franja superior
    # Encabezado = lo que el visor entrega antes de la primera cornisa superior (fecha, número de página, sección).
    primera_ancla = min(a[-1] for a in anclas if a[2] >= y_cornisa - 5)
    encabezado, columnas = [], {}
    for it in items:
        s, x, y = it[0], it[1], it[2]
        if it[-1] < primera_ancla:
            encabezado.append(it)
            continue
        candidatos = [b for b in bordes if b <= x + 3]   # medido: el texto legítimo cae a lo más 2 puntos a la izquierda del borde
        b = max(candidatos) if candidatos else bordes[0]
        columnas.setdefault((franja(y), b), []).append(it)
    orden = lambda it: it[-1]   # posición original dentro del visor
    partes = [i[0] for i in sorted(encabezado, key=orden)]
    for clave in sorted(columnas):
        partes += [i[0] for i in sorted(columnas[clave], key=orden)]
    return "\n".join(partes)


def leer_pagina(ruta_txt) -> str:
    """Texto de una página guardada. Si junto al .txt existe su .geo.json, se usa el orden por posición;
    si no existe o no se puede ordenar, se usa el texto tal como lo entregó el visor."""
    import json
    from pathlib import Path
    ruta_txt = Path(ruta_txt)
    geo = ruta_txt.with_name(ruta_txt.name[:-4] + ".geo.json")
    if geo.exists():
        t = texto_por_posicion(json.loads(geo.read_text(encoding="utf-8")))
        if t:
            return t
    return ruta_txt.read_text(encoding="utf-8")
