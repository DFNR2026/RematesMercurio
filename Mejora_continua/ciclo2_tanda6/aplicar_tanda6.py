"""Ciclo 2, tanda 6 (tanda de los sueltos). Aplica los arreglos sobre una copia del proyecto.
Cada arreglo exige encontrar el texto original exacto una sola vez. Respeta el fin de línea de cada archivo.
Uso python3 -I aplicar_tanda6.py RAIZ [ARREGLO ...] (sin arreglos, aplica todos)."""
import sys
from pathlib import Path

ED, M1, EX = "motor/edicion.py", "modulo1_mercurio.py", "motor/extraccion.py"
A = {}
# V1. Causas voluntarias (rol con letra V). Decisión de Diego del 10 y del 12 de Noviembre de 2026, son irrelevantes y se
# eliminan del todo, como los partidores. No aparecen en ninguna tabla, no se anotan en la memoria y no pasan por la IA.
A["V1"] = [
 (ED, 'def procesar(rollos: list, fecha: str, cliente=None, usar_ia: bool = True) -> dict:\n',
  '_VOL_ROL = re.compile(r"\\bV\\s*-?\\s*\\d")\n'
  '_VOL_TEXTO = re.compile(r"(?<![A-Za-z\\d-])V\\s*-\\s*\\d{1,6}\\s*-\\s*(?:19|20)\\d\\d(?!\\d)")\n\n\n'
  'def es_voluntaria(rol, rol_impreso, texto: str) -> bool:\n'
  '    """Ciclo 2, tanda 6, arreglo V1. Causa voluntaria (rol con letra V, como V-238-2025). Es voluntaria si el rol leído\n'
  '    trae la V (\\"Rol V-188-2025\\"), o si el aviso no tiene rol leído y su texto trae un V-número-año (\\"causa V-50-2026\\").\n'
  '    Un aviso con rol C que trae pegado el extracto de otra causa V (C-12153-2025 del 6 de Octubre) no cuenta."""\n'
  '    if rol:\n'
  '        return bool(_VOL_ROL.search(rol_impreso or ""))\n'
  '    return bool(_VOL_TEXTO.search(texto))\n\n\n'
  'def procesar(rollos: list, fecha: str, cliente=None, usar_ia: bool = True) -> dict:\n'),
 (ED, '    partidores, sin_rol, con_rol = [], [], []\n',
  '    partidores, voluntarias, sin_rol, con_rol = [], [], [], []\n'),
 (ED, '            partidores.append(a.orden)\n            continue\n',
  '            partidores.append(a.orden)\n            continue\n'
  '        if es_voluntaria(a.rol, a.rol_impreso, a.texto):\n'
  '            voluntarias.append(a.orden)\n            continue\n'),
 (ED, '            "partidores": partidores, "sin_rol": sin_rol,',
  '            "partidores": partidores, "voluntarias": voluntarias, "sin_rol": sin_rol,'),
 (M1, '        log.info("Edición %s. %d avisos cortados, %d partidores eliminados, %d sin rol, %d causas. IA %s",\n'
      '                 f.isoformat(), res["avisos_cortados"], len(res["partidores"]), len(res["sin_rol"]), len(res["causas"]),\n',
  '        log.info("Edición %s. %d avisos cortados, %d partidores eliminados, %d voluntarias eliminadas, %d sin rol, %d causas. IA %s",\n'
  '                 f.isoformat(), res["avisos_cortados"], len(res["partidores"]), len(res.get("voluntarias") or []), len(res["sin_rol"]), len(res["causas"]),\n'),
]
# F10. "Fojas 49651. Número 69670" no se leía por el punto entre el número de fojas y "Número" (2334-2025, 11 de Noviembre).
A["F10"] = [
 (EX, r'f(?![a-záéíóúñ]))?\s*,?\s*(?:y\s+)?', r'f(?![a-záéíóúñ]))?\s*[,.]?\s*(?:y\s+)?'),
]
# K1. Corte de los juzgados de Antofagasta. La hoja REFERENCIA escribe "1º", "2º" y "3º Juzgado de Letras Civil de
# Antofagasta" (o volada) y "4° ..." (grado). Los cuatro empatan en el puntaje, buscar_corte se quedaba con el primero (1°)
# y lo rechazaba por número distinto, así que el 2° y el 3° no tenían Corte (548-2025 y 2087-2024). Ahora, en un empate,
# gana el que tiene el mismo número que el tribunal leído. No se toca la hoja REFERENCIA (regla inamovible).
FI = "motor/filtros.py"
A["K1"] = [
 (FI, '        score = fuzz.token_set_ratio(nombre_limpio.lower(), entry["nombre_tribunal"].lower())\n        if score > mejor_score:\n',
  '        score = fuzz.token_set_ratio(nombre_limpio.lower(), entry["nombre_tribunal"].lower())\n'
  '        # Ciclo 2, tanda 6, arreglo K1. En un empate gana el tribunal con el mismo número (Antofagasta, 548-2025).\n'
  '        empate_mejor = (score == mejor_score and ordinal_query is not None and mejor_tribunal is not None\n'
  '                        and _extraer_ordinal(mejor_tribunal) != ordinal_query\n'
  '                        and _extraer_ordinal(entry["nombre_tribunal"]) == ordinal_query)\n'
  '        if score > mejor_score or empate_mejor:\n'),
]
# RM1. Decisión de Diego del 12 de Noviembre de 2026. Un remate de un juzgado de otra región entra si la propiedad está en
# la RM. aplicar() descartaba por "Solo RM" según la Corte del tribunal antes de mirar la comuna, y el prompt maestro dice
# "Solo RM por comuna de la propiedad". En 23 ediciones, 9 de 20 causas descartadas así tenían la propiedad en la RM
# (956-2024 de Punta Arenas con un departamento en Providencia, 2244-2019 de Concepción con una casa en Lo Barnechea).
# La Corte sigue decidiendo cuando ninguna propiedad trae una comuna de la RM escrita igual que en la lista de 52.
A["RM1"] = [
 (FI, 'def propiedades(causa: dict) -> list:\n',
  'def _alguna_comuna_rm(causa: dict) -> bool:\n'
  '    """Ciclo 2, tanda 6, arreglo RM1. True si alguna propiedad de la causa trae una comuna de la RM, igual a una de las 52\n'
  '    (sin coincidencia difusa). Sirve para que un remate de un juzgado de otra región con la propiedad en la RM no se\n'
  '    descarte por Solo RM (decisión de Diego del 12 de Noviembre de 2026)."""\n'
  '    for p in propiedades(causa):\n'
  '        c = (p.get("comuna") or "").strip()\n'
  '        if c and _normalizar_comuna(c) in _COMUNAS_RM_NORM:\n'
  '            return True\n'
  '    return False\n\n\n'
  'def propiedades(causa: dict) -> list:\n'),
 (FI, '            elif corte not in _CORTES_RM:\n                descartados.append({**base, "motivo": "Solo RM", "monto": None}); continue\n',
  '            elif corte not in _CORTES_RM:\n'
  '                if not _alguna_comuna_rm(c):\n'
  '                    descartados.append({**base, "motivo": "Solo RM", "monto": None}); continue\n'
  '                obs.append(OBS_OTRA_REGION)\n'),
 (FI, 'OBS_COMUNA = "El aviso no indica la comuna de la propiedad. Revisar."\n',
  'OBS_COMUNA = "El aviso no indica la comuna de la propiedad. Revisar."\n'
  'OBS_OTRA_REGION = "El remate es en un juzgado de otra región, pero la propiedad está en la Región Metropolitana."\n'),
]
# B1 y B2. Hallazgo del 13 de Noviembre de 2026 (viernes con tres bloques de remates, B10-B11, C8 y G9 a G14). La sección
# siguió de B11 a C8 sin flecha "MÁS AVISOS", así que el lector armó dos bloques y el aviso 1445-2024 quedó partido en
# dos (la cabeza sin rol en B y la cola sin tribunal en C). Además cada bloque se unía solo contra el primero (B), y los
# 37 avisos de C que G reimprime entraron dos veces. B1 lee como un solo bloque dos bloques seguidos cuando el primero
# termina con una palabra cortada y el segundo empieza en minúscula, solo si al unirlos sale exactamente un aviso menos.
# B2 busca el gemelo de cada aviso en todo lo ya cargado y no solo en el primer bloque.
A["B1"] = [
 (ED, 'def _n_remates(ex: dict) -> int:\n',
  'def unir_continuaciones(rollos: list) -> tuple:\n'
  '    """Ciclo 2, tanda 6, arreglo B1. Si un bloque termina con una palabra cortada y el siguiente empieza en minúscula, el\n'
  '    diario siguió la sección en otro cuerpo sin la flecha \"MÁS AVISOS\" (13 de Noviembre de 2026, B11 sigue en C8 y el\n'
  '    aviso 1445-2024 quedó partido en dos). Los dos bloques se leen como uno, solo si al unirlos sale exactamente un aviso\n'
  '    menos. Devuelve (rollos, notas)."""\n'
  '    out, notas = [], []\n'
  '    for paginas in rollos:\n'
  '        if not paginas:\n'
  '            continue\n'
  '        if out:\n'
  '            ant, este = cortar(*construir_rollo(out[-1])), cortar(*construir_rollo(paginas))\n'
  '            if (ant and este and "termina con una palabra cortada" in ant[-1].revisar\n'
  '                    and "empieza en minúscula" in este[0].revisar):\n'
  '                juntos = list(out[-1]) + list(paginas)\n'
  '                if len(cortar(*construir_rollo(juntos))) == len(ant) + len(este) - 1:\n'
  '                    notas.append(f"El bloque que empieza en {paginas[0][0]} continúa al que empieza en {out[-1][0][0]} "\n'
  '                                 "(un aviso quedó cortado entre los dos). Se leen como un solo bloque.")\n'
  '                    out[-1] = juntos\n'
  '                    continue\n'
  '        out.append(list(paginas))\n'
  '    return out, notas\n\n\n'
  'def _n_remates(ex: dict) -> int:\n'),
 (ED, '    cortados, roles_texto = [], set()\n',
  '    rollos, continuaciones = unir_continuaciones(rollos)\n'
  '    cortados, roles_texto = [], set()\n'),
 (ED, '    alarmas = list(alarmas)\n', '    alarmas = continuaciones + list(alarmas)\n'),
]
A["B2"] = [
 (ED, '        for a in avisos[:len(cortados[0])]:\n',
  '        for a in avisos:                # Tanda 6, B2. El gemelo se busca en todo lo ya cargado, no solo en el primer bloque\n'),
]
# P1. Un terreno sin calle (parcela, lote, hijuela) se guardaba con los primeros 200 caracteres de su frase y quedaba a
# media palabra (8121-2024, y 11 causas más en las 13 ediciones medidas el 13 de Noviembre). Ahora la frase va completa
# hasta 350 caracteres. Si es más larga se corta en el último espacio antes de 350 y lleva puntos suspensivos.
DI = "motor/direccion.py"
A["P1"] = [
 (DI, '        direccion = frase[:200] + (f", {unidad.strip()}"',
  '        direccion = _frase_terreno(frase) + (f", {unidad.strip()}"'),
 (DI, 'def _comuna_comprobada(x: dict, texto: str):\n',
  'def _frase_terreno(frase: str, tope: int = 350) -> str:\n'
  '    """Ciclo 2, tanda 6, arreglo P1. La frase de un terreno sin calle va completa hasta el tope. Si es más larga se corta\n'
  '    en el último espacio y lleva puntos suspensivos, para que nunca quede a media palabra (antes frase[:200])."""\n'
  '    if len(frase) <= tope:\n'
  '        return frase\n'
  '    return frase[:tope].rsplit(" ", 1)[0].rstrip(" ,;.") + " ..."\n\n\n'
  'def _comuna_comprobada(x: dict, texto: str):\n'),
]
# G3. Decisión de Diego del 13 de Noviembre de 2026 (sale de la espera por el reclamo de los abogados). El aviso de
# 6458-2022 del 13 de Noviembre empieza "REMATE. SE ORDENA REMATAR" y nombra al tribunal recién al final ("causa digital
# C-6458-2022 seguida ante el 13° Juzgado Civil de Santiago"). El código lo buscaba solo en los primeros 400 caracteres,
# la causa llegó a la principal sin tribunal ni Corte y los abogados no la encontraron en la OJV. Ahora, si el comienzo no
# trae tribunal, se lee el que va justo después del rol ("causa C-N-AÑO seguida ante el", "del", "en el"). Se usa solo si
# esa frase aparece una vez o todas sus apariciones dan el mismo tribunal. Nunca mira el vale vista ni las frases de pago.
A["G3"] = [
 (EX, 'def tribunal(texto: str) -> dict:\n',
  '_ROL_ANTE = re.compile(r"(?:causa|rol|expediente|autos)\\b[^.\\n]{0,40}?\\b[A-Z]{1,2}\\s*-\\s*\\d{1,6}\\s*-\\s*(?:19|20)\\d\\d"\n'
  '                       r"\\s*,?\\s+(?:seguid[ao]s?\\s+|tramitad[ao]s?\\s+)?(?:ante\\s+(?:el\\s+)?|del\\s+|en\\s+el\\s+)", re.I)\n\n\n'
  'def _tribunal_tras_rol(texto: str):\n'
  '    """Ciclo 2, tanda 6, arreglo G3. Tribunal nombrado justo después del rol, al final del aviso (6458-2022 del 13 de\n'
  '    Noviembre de 2026, \\"causa digital C-6458-2022 seguida ante el 13° Juzgado Civil de Santiago\\"). Devuelve el match\n'
  '    de _TRIBUNAL solo si todas las frases así nombran el mismo tribunal. Si no hay ninguna o no coinciden, None."""\n'
  '    hallados = []\n'
  '    for a in _ROL_ANTE.finditer(texto):\n'
  '        m = _TRIBUNAL.match(texto, a.end())\n'
  '        if m:\n'
  '            hallados.append(m)\n'
  '    if not hallados or len({re.sub(r"\\s+", " ", h.group(0)).lower() for h in hallados}) != 1:\n'
  '        return None\n'
  '    return hallados[0]\n\n\n'
  'def tribunal(texto: str) -> dict:\n'),
 (EX, '    m = _TRIBUNAL.search(texto[:400])\n    if not m:\n',
  '    m = _TRIBUNAL.search(texto[:400]) or _tribunal_tras_rol(texto)     # tanda 6, G3\n    if not m:\n'),
]
# TP, T1 y T2. Decisiones de Diego del 13 de Noviembre de 2026 (20:49 y 21:16). Los terrenos sin calle desaparecen del todo,
# como los partidores (T1). Las oficinas, los sitios sin casa y los terrenos con calle no van a la principal y quedan al
# final del mismo Excel en una tabla aparte, solo por si acaso (T2). "Lote" no se usa para filtrar, porque una casa de
# condominio puede ser "lote 17". Un sitio con casa ("el sitio y casa Parcela número 4", 6996-2023) no se aparta. Se mira
# por causa (rol, año y tribunal). Si todas sus propiedades son de ese tipo, la causa sale. Si una causa trae además una
# casa o un departamento, sigue con esa propiedad y una Observación (n=0 en 13 ediciones, el 13 de Noviembre). Solo se
# miran las direcciones comprobadas (en verde). Una dirección en rojo no se puede clasificar y la causa sigue como antes.
# TP lleva el tipo que da Haiku (calle o sin_calle) y la frase comprobada hasta el filtro. No cambia nada por sí solo.
A["TP"] = [
 (DI, '"citas_extra": citas_extra,\n            "calle"', '"citas_extra": citas_extra, "tipo": tipo,\n            "calle"'),
 (DI, 'for k2 in ("direccion", "comuna", "cita", "citas_extra", "calle")', 'for k2 in ("direccion", "comuna", "cita", "citas_extra", "calle", "tipo")'),
 (ED, '"comuna": i["comuna"]} for i in res["inmuebles"]], "verde", []',
      '"comuna": i["comuna"], "tipo": i.get("tipo"), "cita": i.get("cita")} for i in res["inmuebles"]], "verde", []'),
 (FI, '"fojas": [x["fojas"] for x in mia if x.get("fojas")], "aviso": av})',
      '"fojas": [x["fojas"] for x in mia if x.get("fojas")], "aviso": av,\n'
      '                        "tipo": (d or {}).get("tipo"), "cita": (d or {}).get("cita")})'),
]
A["T1"] = [
 (FI, 'def _cbr(p: dict) -> tuple[str, int | None]:\n',
  '''# Ciclo 2, tanda 6, arreglos T1 y T2 (decisiones de Diego del 13 de Noviembre de 2026).
_CASA = re.compile(r"(?i)\\b(?:casas?|viviendas?|edificad[ao]s?|edificaci[oó]n(?:es)?|construcci[oó]n(?:es)?|construid[ao]s?)\\b")
_OFICINA = re.compile(r"(?i)\\boficinas?\\b")
_TERRENO = re.compile(r"(?i)\\bterrenos?\\b")
_SITIO = re.compile(r"(?i)\\bsitios?\\b")
_NOMBRE_CLASE = {"oficina": "oficina", "terreno": "terreno", "sitio": "sitio sin casa"}


def clase_inmueble(direccion, tipo, cita, texto="", n_remates=1):
    """Ciclo 2, tanda 6. None si la propiedad va como siempre. "terreno_sin_calle" si Haiku la dio sin calle y su frase no
    dice casa (T1, desaparece). "oficina", "terreno" o "sitio" si la dirección comprobada trae esa palabra (T2, tabla
    aparte). El sitio no se aparta si su frase, o el aviso de un solo remate, dice casa o vivienda. Lote no cuenta."""
    if not direccion:
        return None
    cita = cita or ""
    if tipo == "sin_calle":
        return None if _CASA.search(cita) else "terreno_sin_calle"
    if _OFICINA.search(direccion):
        return "oficina"
    if _TERRENO.search(direccion):
        return "terreno"
    if _SITIO.search(direccion):
        return None if (_CASA.search(cita) or (n_remates == 1 and _CASA.search(texto or ""))) else "sitio"
    return None


def _clase(p: dict):
    if not p.get("dir_ok"):
        return None
    av = p.get("aviso") or {}
    return clase_inmueble(p.get("direccion"), p.get("tipo"), p.get("cita"), av.get("texto"), av.get("n_remates") or 1)


def _cbr(p: dict) -> tuple[str, int | None]:
'''),
 (FI, '    principal, excluidas, descartados, ya_informadas = [], [], [], []\n',
      '    principal, excluidas, descartados, ya_informadas = [], [], [], []\n'
      '    terrenos_eliminados, apartadas = [], []         # tanda 6, T1 y T2\n'),
 (FI, '        memoria = historico.get(c["clave"]) or []\n',
  '''        # Ciclo 2, tanda 6, T1. Los terrenos sin calle desaparecen del todo, como los partidores (decisión de Diego del
        # 13 de Noviembre de 2026). No van a ninguna tabla ni a la memoria.
        _todas = propiedades(c)
        _cl = [_clase(p) for p in _todas]
        if _cl and all(x == "terreno_sin_calle" for x in _cl):
            terrenos_eliminados.append(c["clave"]); continue
        _fuera = [p for p, x in zip(_todas, _cl) if x == "terreno_sin_calle"]
        memoria = historico.get(c["clave"]) or []
'''),
 (FI, '            props = propiedades(c)\n            dias = racha(list(memoria) + eds)\n',
      '            props = [p for p in _todas if not any(p is q for q in _fuera)] or _todas\n'
      '            dias = racha(list(memoria) + eds)\n'),
 (FI, '        props = propiedades(c)\n        n = len(props)\n',
      '        props = [p for p in _todas if not any(p is q for q in _fuera)]\n'
      '        if _fuera:\n'
      '            obs.append(f"{len(_fuera)} propiedad{\'es\' if len(_fuera) > 1 else \'\'} de este rol no se informa{\'n\' if len(_fuera) > 1 else \'\'} "\n'
      '                       "por ser terreno, sitio u oficina.")\n'
      '        n = len(props)\n'),
 (FI, '            d = av.get("direcciones") or []\n',
      '            d = av.get("direcciones") or []\n'
      '            _cs = [clase_inmueble(x.get("direccion"), x.get("tipo"), x.get("cita"), av.get("texto"), av.get("n_remates") or 1)\n'
      '                   for x in d] if av.get("dir_color") == "verde" else []\n'
      '            if _cs and all(x == "terreno_sin_calle" for x in _cs):\n'
      '                terrenos_eliminados.append("sin rol"); continue          # tanda 6, T1\n'),
 (FI, '            "ya_informadas": ya_informadas, "en_historial": len(ya_informadas)}',
      '            "ya_informadas": ya_informadas, "en_historial": len(ya_informadas),\n'
      '            "terrenos_eliminados": terrenos_eliminados, "apartadas": apartadas}'),
]
A["T2"] = [
 (FI, '''        _fuera = [p for p, x in zip(_todas, _cl) if x == "terreno_sin_calle"]
''',
  '''        # T2. Si todas sus propiedades son oficina, sitio sin casa o terreno (o terreno sin calle), la causa va a la tabla
        # aparte del final del Excel, solo por si acaso. No pasa por los demás filtros ni se anota en la memoria.
        if _cl and all(_cl):
            _ps = [p for p, x in zip(_todas, _cl) if x != "terreno_sin_calle"]
            _tipos = sorted({_NOMBRE_CLASE[x] for x in _cl if x != "terreno_sin_calle"})
            apartadas.append({"rol": c["rol"], "año": c["año"], "tribunal": c["tribunal"],
                              "direccion": _unir(p["direccion"] for p in _ps), "comuna": _unir(p["comuna"] for p in _ps),
                              "motivo": "Es " + " y ".join(_tipos),
                              "ediciones": eds})
            continue
        _fuera = [p for p, x in zip(_todas, _cl) if x]
'''),
 (FI, '                terrenos_eliminados.append("sin rol"); continue          # tanda 6, T1\n',
      '                terrenos_eliminados.append("sin rol"); continue          # tanda 6, T1\n'
      '            if _cs and all(_cs):                                          # tanda 6, T2\n'
      '                _ds = [x for x, k in zip(d, _cs) if k != "terreno_sin_calle"]\n'
      '                apartadas.append({"rol": "", "año": "", "tribunal": av.get("tribunal") or "",\n'
      '                                  "direccion": _unir(x.get("direccion") for x in _ds), "comuna": _unir(x.get("comuna") for x in _ds),\n'
      '                                  "motivo": "Es " + " y ".join(sorted({_NOMBRE_CLASE[k] for k in _cs if k != "terreno_sin_calle"}))\n'
      '                                            + ". El aviso no trae número de rol", "ediciones": [res["fecha"]]})\n'
      '                continue\n'),
 (M1, '        "excluidos_cbr": tabla["excluidas_cbr"], "descartados": tabla["descartados"], "sin_rol": tabla["sin_rol"],\n',
      '        "excluidos_cbr": tabla["excluidas_cbr"], "descartados": tabla["descartados"], "sin_rol": tabla["sin_rol"],\n'
      '        "apartadas": tabla.get("apartadas") or [], "terrenos_eliminados": len(tabla.get("terrenos_eliminados") or []),\n'),
 (M1, '    log.info("  Ya informadas (4 días)  : %d", len(tabla["ya_informadas"]))\n',
      '    log.info("  Ya informadas (4 días)  : %d", len(tabla["ya_informadas"]))\n'
      '    log.info("  Oficinas, sitios y terrenos aparte : %d. Terrenos sin calle eliminados %d",\n'
      '             len(tabla.get("apartadas") or []), len(tabla.get("terrenos_eliminados") or []))\n'),
]
M5 = "modulo5_reporte.py"
A["T2"] += [
 (M5, 'sin_rol: list | None = None, ya_informadas: list | None = None) -> None:\n',
      'sin_rol: list | None = None, ya_informadas: list | None = None, apartadas: list | None = None) -> None:\n'),
 (M5, '''value="Sin causas descartadas por parámetros en esta edición")
        cell.font = _FONT_BODY
        ws.merge_cells(start_row=r_d, start_column=1, end_row=r_d, end_column=5)
        ws.row_dimensions[r_d].height = 16
''',
  '''value="Sin causas descartadas por parámetros en esta edición")
        cell.font = _FONT_BODY
        ws.merge_cells(start_row=r_d, start_column=1, end_row=r_d, end_column=5)
        ws.row_dimensions[r_d].height = 16

    # ── Tanda 6, T2. Oficinas, sitios sin casa y terrenos, al final y aparte, solo por si acaso (Diego, 13 de Noviembre) ──
    apartadas = apartadas or []
    if apartadas:
        inicio_ap = inicio_desc + 2 + max(len(descartados), 1) + 2
        cell_ap = ws.cell(row=inicio_ap, column=1, value="OFICINAS, SITIOS Y TERRENOS (APARTE, SOLO POR SI ACASO)")
        cell_ap.font = Font(bold=True, color="FFFFFF", size=11)
        cell_ap.fill = PatternFill("solid", fgColor="595959")
        ws.merge_cells(start_row=inicio_ap, start_column=1, end_row=inicio_ap, end_column=6)
        ws.row_dimensions[inicio_ap].height = 20
        for ci, h in enumerate(["Tribunal", "ROL", "Año", "Dirección", "Comuna", "Motivo"], 1):
            cell = ws.cell(row=inicio_ap + 1, column=ci, value=h)
            cell.font = Font(bold=True, color="FFFFFF", size=10)
            cell.fill = PatternFill("solid", fgColor="1F4E79")
            cell.alignment = _ALIGN_CENTER
            cell.border = _BORDER_THIN
        for fi, d in enumerate(apartadas):
            r_a = inicio_ap + 2 + fi
            for ci, k in enumerate(["tribunal", "rol", "año", "direccion", "comuna", "motivo"], 1):
                cell = ws.cell(row=r_a, column=ci, value=d.get(k, "") or "")
                cell.font = _FONT_BODY
                cell.border = _BORDER_THIN
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=(k == "direccion"))
            ws.row_dimensions[r_a].height = 30
'''),
 (M5, '    r += 1; fila(r, "Ya informadas en los últimos 4 días", len(metricas.get("ya_informadas") or []))\n',
      '    r += 1; fila(r, "Ya informadas en los últimos 4 días", len(metricas.get("ya_informadas") or []))\n'
      '    r += 1; fila(r, "Oficinas, sitios y terrenos (tabla aparte al final)", len(metricas.get("apartadas") or []))\n'),
 (M5, 'sin_rol=metricas.get("sin_rol", []), ya_informadas=metricas.get("ya_informadas", []))',
      'sin_rol=metricas.get("sin_rol", []), ya_informadas=metricas.get("ya_informadas", []), apartadas=metricas.get("apartadas", []))'),
]

TF = "pruebas/test_filtros.py"
# T1 en la prueba 18. Las 57 causas del 14 de Octubre siguen contadas una sola vez, ahora sumando las de terrenos sin calle
# que desaparecen por decisión de Diego (8 de ese día) y las de la tabla aparte (T2).
A["T1"] += [
 (TF, 'tot = len(r["principal"]) + len(r["excluidas_cbr"]) + len(r["descartados"])\n',
      'tot = len(r["principal"]) + len(r["excluidas_cbr"]) + len(r["descartados"]) + len(r.get("apartadas") or []) + len(r.get("terrenos_eliminados") or [])\n'),
 (TF, 'for t in ("principal", "excluidas_cbr", "descartados") for x in r[t]}) == 57,\n',
      'for t in ("principal", "excluidas_cbr", "descartados", "apartadas") for x in r.get(t) or []}) + len(set(r.get("terrenos_eliminados") or [])) == 57,\n'),
 (TF, 'descartadas {len(r[\'descartados\'])}, para revisar',
      'descartadas {len(r[\'descartados\'])}, terrenos sin calle eliminados {len(r.get(\'terrenos_eliminados\') or [])}, para revisar'),
]

# K1 va después de RM1. Medido solo, mandaba a Descartadas a 548-2025 y 2087-2024, que tienen la propiedad en la RM. Con RM1
# (decisión de Diego del 12 de Noviembre) esas causas entran por su comuna y K1 solo cambia la Observación de la Corte.
ORDEN = ["V1", "F10", "RM1", "K1", "B1", "B2", "G3", "TP", "T1", "T2"]
# P1 salió de ORDEN el 13 de Noviembre de 2026. Con T1 los terrenos sin calle desaparecen, así que su frase ya no se muestra.


def aplicar(raiz, nombres):
    for n in nombres:
        for rel, viejo, nuevo in A[n]:
            p = Path(raiz) / rel
            b = p.read_bytes(); crlf = b"\r\n" in b
            s = b.decode("utf-8").replace("\r\n", "\n")
            c = s.count(viejo)
            if c != 1:
                sys.exit(f"{n}. En {rel} el texto original aparece {c} veces, se esperaba 1. No se aplica nada más.")
            s = s.replace(viejo, nuevo)
            p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
        print("aplicado", n)


if __name__ == "__main__":
    aplicar(sys.argv[1], sys.argv[2:] or ORDEN)
