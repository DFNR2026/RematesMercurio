"""Parte 3.7b. Dirección del inmueble leída por la IA (Claude Haiku 5.5). La IA nunca tiene la última palabra.

Decisiones de Diego del 17 de Octubre.
- La dirección es para mostrarla en la ficha del remate, con su comuna. No se usa para la clave del bien (esa la da el
  código con la lista de mínimos o la inscripción en el Conservador) ni para filtrar.
- Un terreno sin calle guarda su descripción, tal como está escrita en el aviso.
- Si la dirección queda en rojo, el campo queda vacío y la alerta trae el detalle (las dos lecturas y la frase del aviso).

1. La IA entrega una dirección por remate (calle, número, unidad, comuna) y la frase exacta de cada dato.
2. El código revisa (verificar). La frase debe estar en el aviso (solo diferencias de espacios, igual que el vale vista),
   la calle dentro de su frase, el número dentro de su frase (en cifras o en palabras, motor/numeros_texto.py), la unidad
   y la comuna dentro de las suyas. El número que se guarda es el que está escrito en el aviso, no el que copió la IA.
3. Dos lecturas por aviso. Si no coinciden, rojo. Respuestas guardadas en ia_respuestas\\direccion por huella (modelo,
   versión de las instrucciones, cantidad de remates y texto del aviso).

Colores. verde (verificado), rojo (no verificado, sin dirección), sin_dato (la IA dice que el aviso no da dirección y el
detector no encuentra señales de una).
"""
import hashlib, json, re
from pathlib import Path
from motor.numeros_texto import numeros_en, palabras_a_cifras, _sin_tildes
from motor.ia_comun import buscar_frase, MODELO

RAIZ = Path(__file__).resolve().parent.parent
VERSION_INSTRUCCIONES = "dir-2"     # dir-1 dejaba la comuna vacía cuando el aviso nombra la ciudad sin la palabra comuna (14-10 aviso 50)
CARPETA_RESPUESTAS = RAIZ / "ia_respuestas" / "direccion"
NO_ENCONTRADA = "La IA no encontró la dirección del inmueble en el aviso. Revísala en el aviso."
TIPOS = ["calle", "sin_calle", "sin_dato"]

INSTRUCCIONES = """Eres un lector de avisos de remates judiciales de Chile publicados en El Mercurio. Tu única tarea es encontrar DÓNDE está el inmueble que se remata. No inventas nada. Copias frases exactas del aviso.

Te digo cuántos remates trae el aviso. Devuelve exactamente esa cantidad de inmuebles, en el mismo orden en que el aviso da sus mínimos. Si el aviso remata varias piezas juntas con un solo mínimo (un departamento con su bodega y su estacionamiento), es un solo inmueble.

Campos de cada inmueble.
- tipo. calle si el inmueble tiene calle y número. sin_calle si es un terreno, parcela, lote, hijuela o sitio que el aviso no ubica en una calle con número. sin_dato si el aviso no dice dónde está.
- calle. El nombre de la calle como lo escribe el aviso, con su tipo si lo trae (calle, Avenida, Pasaje, Camino). Sin el número. null si el tipo no es calle.
- numero. El número de la calle EN CIFRAS. Si el aviso lo escribe en palabras, pásalo a cifras ("número mil ochocientos ochenta y ocho" es 1888, "cero novecientos veintiséis" es 0926). Conserva el cero inicial. Si trae dos números, escríbelos como el aviso ("N° 575 y N° 577" es "575 y 577").
- unidad. Solo si lo que se vende es una pieza dentro de un edificio o condominio. La pieza principal con su número, por ejemplo "departamento 1504", "casa 67", "oficina 602", "vivienda 77", "unidad 112". Si se venden un departamento, una bodega y un estacionamiento juntos, va el departamento. El lote o sitio del plano de una casa que tiene calle y número NO es unidad. null si no hay.
- comuna. La comuna donde está el INMUEBLE, no la del tribunal. Si el aviso dice "comuna San Miguel, hoy comuna San Joaquín", va la de hoy. Si el aviso nombra la ciudad junto a la dirección sin la palabra comuna ("calle Camino Nuevo 2065, Chillán"), esa ciudad es la comuna. null si el aviso no la nombra (no la deduzcas del Conservador).
- frase_direccion. La frase EXACTA del aviso, copiada letra por letra, que trae la calle y el número (o, si el tipo es sin_calle, la que describe el terreno). null si el tipo es sin_dato.
- frase_unidad. La frase EXACTA del aviso que trae la unidad con su número. null si no hay unidad.
- frase_comuna. La frase EXACTA del aviso que trae la comuna del inmueble. null si no hay comuna.

Cuidado con estas trampas.
- La dirección del tribunal (Huérfanos 1409 y otras) no es la del inmueble.
- El plano archivado, el rol de avalúo, las fojas y los deslindes no son la dirección.
- Copia las frases tal como están, con sus errores de escritura y sus palabras pegadas. No las corrijas.

Ejemplos (de avisos reales).
1. "inmueble ubicado en calle Santiago Bueras n° 3951, comuna de Peñaflor" da tipo calle, calle "calle Santiago Bueras", numero "3951", unidad null, comuna "Peñaflor".
2. "la propiedad ubicada en calle Álvarez de Toledo número ochocientos sesenta y uno" da calle "calle Álvarez de Toledo", numero "861".
3. "el departamento N° 1504 ... con acceso por Avenida Vicuña Mackenna Oriente número 7320, Comuna de La Florida" da calle "Avenida Vicuña Mackenna Oriente", numero "7320", unidad "departamento 1504", comuna "La Florida", con frase_unidad y frase_direccion distintas.
4. Un aviso con dos remates, oficinas 602 y 603 del edificio "con acceso general por Avenida Pajaritos N° 3195, comuna de Maipú", da dos inmuebles con la misma calle y número y unidades "oficina 602" y "oficina 603".
5. "Lote Dos, Hijuela Segunda, del Antiguo Fundo Cuesta Vieja, ubicado en la comuna de Curacaví" da tipo sin_calle, calle null, numero null, comuna "Curacaví", y en frase_direccion la frase que describe el lote.
6. "con acceso por Avenida Lo Ovalle cero novecientos veintiséis, Comuna de La Cisterna" da numero "0926".
7. "propiedad ubicada en calle Sotomayor N° 575 y N° 577" da numero "575 y 577".
8. "sitio número 5 de la manzana 1, del plano de loteo del predio denominado El Manzano" sin calle ni comuna da tipo sin_calle y comuna null.
9. "con acceso general por calle Camino Nuevo 2065, Chillán" da calle "calle Camino Nuevo", numero "2065", comuna "Chillán", y la misma frase en frase_direccion y frase_comuna.
"""

_INMUEBLE = {
    "type": "object",
    "properties": {
        "tipo": {"type": "string", "enum": TIPOS},
        "calle": {"type": ["string", "null"]},
        "numero": {"type": ["string", "null"]},
        "unidad": {"type": ["string", "null"]},
        "comuna": {"type": ["string", "null"]},
        "frase_direccion": {"type": ["string", "null"]},
        "frase_unidad": {"type": ["string", "null"]},
        "frase_comuna": {"type": ["string", "null"]},
    },
    "required": ["tipo", "calle", "numero", "unidad", "comuna", "frase_direccion", "frase_unidad", "frase_comuna"],
    "additionalProperties": False,
}
ESQUEMA = {"type": "object", "properties": {"inmuebles": {"type": "array", "items": _INMUEBLE}},
           "required": ["inmuebles"], "additionalProperties": False}


# --- Normalización para comparar ---------------------------------------------------------------------------------
def norm(t: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", _sin_tildes(t or ""))).strip()

_TIPO_CALLE = re.compile(r"^(?:(?:calle|avenida|avda|av|pasaje|psje)\s+)+")

def calle_clave(t: str | None) -> str:
    """'calle Pasaje Estación Casma' y 'Pasaje Estación Casma' dan 'estacion casma'."""
    return _TIPO_CALLE.sub("", norm(t))

def numeros_clave(t: str | None) -> tuple:
    return tuple(sorted((n.lstrip("0") or "0") for n in re.findall(r"\d+", t or "")))

# También en plural (arreglo 2 del ajuste, 14-10 aviso 3, "las oficinas números 602 y 603")
_UNIDAD = re.compile(r"\b(departamento|depto|dpto|casa|oficina|local|vivienda|unidad|bodega|estacionamiento|lote|sitio|parcela)(?:s|es)?\b", re.I)

def unidad_clave(t: str | None) -> tuple | None:
    if not t:
        return None
    t = norm(palabras_a_cifras(t))      # "departamento trescientos dos D" y "departamento 302 D" son la misma unidad
    m = _UNIDAD.search(t)
    tipo = m.group(1) if m else ""
    tipo = {"depto": "departamento", "dpto": "departamento"}.get(tipo, tipo)
    # Solo el primer número después del tipo (arreglo 4 del ajuste, 14-10 avisos 11 y 49). La IA a veces agrega el piso,
    # el edificio o la bodega ("Departamento Número 403, Torre I, Piso 4°, Edificio 5" es el departamento 403).
    k = re.search(r"\d+", t[m.end():] if m else t)
    return (tipo, ((k.group(0).lstrip("0") or "0"),) if k else (t,))


def clave_inmueble(x: dict) -> tuple:
    """Lo que debe coincidir entre las dos lecturas (y con el banco)."""
    if x.get("tipo") == "calle":
        return ("calle", calle_clave(x.get("calle")), numeros_clave(x.get("numero")), unidad_clave(x.get("unidad")), norm(x.get("comuna")))
    return (x.get("tipo"), unidad_clave(x.get("unidad")), norm(x.get("comuna")))


def legible(x: dict) -> str:
    """Cómo se muestra una lectura en el texto del rojo."""
    if x.get("tipo") == "sin_dato":
        return "que el aviso no da la dirección"
    if x.get("tipo") == "sin_calle":
        base = (x.get("frase_direccion") or "un terreno sin calle")[:120]
    else:
        base = f"{x.get('calle') or '(sin calle)'} {x.get('numero') or '(sin número)'}"
    if x.get("unidad"):
        base += f", {x['unidad']}"
    if x.get("comuna"):
        base += f", comuna {x['comuna']}"
    return base


# --- Verificación --------------------------------------------------------------------------------------------------
_SENALES = re.compile(r"ubicad[oa]\s+en|con\s+acceso|acceso\s+(?:principal|general|com[uú]n)?\s*por|con\s+frente\s+a|ingreso\s+(?:principal\s+)?por"
                      r"|\bcalle\s+[A-ZÁÉÍÓÚÑ]|\bavenida\s+[A-ZÁÉÍÓÚÑ]|\bpasaje\s+[A-ZÁÉÍÓÚÑ]|\bcomuna\s+(?:de\s+)?[A-ZÁÉÍÓÚÑ]", re.I)


def verificar_inmueble(x: dict, texto: str) -> dict:
    """Revisa un inmueble de la respuesta. Devuelve {ok, motivos, direccion, comuna, cita, citas_extra} con lo que se
    guardaría (el número tal como está en el aviso y las frases tal como están en el aviso)."""
    motivos, citas_extra = [], []
    # Comuna sacada de la frase del Conservador o del Registro (06-10 avisos 66 y 90, "Conservador Bienes Raíces Casablanca").
    # Las instrucciones lo prohíben y no dice dónde está el inmueble. La comuna queda vacía y el resto sigue igual.
    # Aplicado con la aprobación de Diego del 17 de Octubre, después de la validación (la cifra honesta sigue siendo la cruda).
    fc0 = x.get("frase_comuna") or ""
    if x.get("comuna") and re.search(r"conservador|\bCBR\b|registro", fc0, re.I) and not re.search(r"comuna", fc0, re.I):
        x = dict(x, comuna=None, frase_comuna=None)
    tipo = x.get("tipo")
    if tipo not in TIPOS:
        return {"ok": False, "motivos": [f"Tipo desconocido ({tipo})."]}
    if tipo == "sin_dato":
        return {"ok": True, "motivos": [], "direccion": None, "comuna": None, "cita": None, "citas_extra": []}
    frase = buscar_frase(x.get("frase_direccion"), texto)
    if frase is None:
        motivos.append("La frase de la dirección no está en el aviso." if x.get("frase_direccion") else "La IA no entregó la frase de la dirección.")
        return {"ok": False, "motivos": motivos}
    numero = None
    if tipo == "calle":
        if not x.get("calle") or calle_clave(x["calle"]) not in calle_clave(frase) and calle_clave(x["calle"]) not in norm(frase):
            motivos.append("La calle que dio la IA no está en la frase de la dirección.")
        en_frase = numeros_en(frase)
        pedidos = re.findall(r"\d+", x.get("numero") or "")
        if not pedidos:
            motivos.append("La IA no dio el número de la calle.")
        for n in pedidos:
            iguales = [f for f in en_frase if (f.lstrip("0") or "0") == (n.lstrip("0") or "0")]
            if not iguales:
                motivos.append(f"El número {n} no está en la frase de la dirección.")
        if not motivos:
            # el número que se guarda es el que está en el aviso (con su cero inicial), no el que copió la IA
            partes = re.split(r"(\d+)", x["numero"])
            numero = "".join(next((f for f in en_frase if (f.lstrip("0") or "0") == (p.lstrip("0") or "0")), p) if p.isdigit() else p for p in partes)
    unidad = palabras_a_cifras(x.get("unidad"))          # se guarda en cifras (arreglo 1 del ajuste, 14-10 avisos 16 y 42)
    if unidad:
        if not re.search(r"\d", unidad):
            motivos.append("La unidad que dio la IA no trae número.")
        fu = buscar_frase(x.get("frase_unidad"), texto)
        if fu is None:
            motivos.append("La frase de la unidad no está en el aviso.")
        else:
            tipos_frase = {({"depto": "departamento", "dpto": "departamento"}.get(m.group(1), m.group(1))) for m in _UNIDAD.finditer(norm(fu))}
            if not _UNIDAD.search(norm(unidad)) or (unidad_clave(unidad) or ("",))[0] not in tipos_frase:
                # el tipo de la unidad (departamento, casa, oficina) debe ser el que dice su frase, no otro
                motivos.append("La unidad que dio la IA no trae su tipo (departamento, casa, oficina) en la frase.")
            nums = {f.lstrip("0") or "0" for f in numeros_en(fu)}
            for n in re.findall(r"\d+", unidad):
                if (n.lstrip("0") or "0") not in nums:
                    motivos.append(f"El número de la unidad ({n}) no está en su frase.")
            if fu != frase:
                citas_extra.append(fu)
    comuna = x.get("comuna")
    if comuna:
        fc = buscar_frase(x.get("frase_comuna"), texto)
        if fc is None:
            motivos.append("La frase de la comuna no está en el aviso.")
        elif norm(comuna) not in norm(fc):
            motivos.append("La comuna que dio la IA no está en su frase.")
        elif fc != frase and fc not in citas_extra:
            citas_extra.append(fc)
    if motivos:
        return {"ok": False, "motivos": motivos}
    if tipo == "calle":
        direccion = f"{x['calle'].strip()} {numero}" + (f", {unidad.strip()}" if unidad else "")
    else:
        direccion = frase[:200] + (f", {unidad.strip()}" if unidad and norm(unidad) not in norm(frase) else "")
    return {"ok": True, "motivos": [], "direccion": direccion, "comuna": comuna.strip() if comuna else None, "cita": frase, "citas_extra": citas_extra}


def resolver(lecturas: list, texto: str, n_remates: int) -> dict:
    """Une las dos lecturas y verifica. Devuelve {color, inmuebles [{direccion, comuna, cita, citas_extra}], motivos,
    lecturas_legibles, frase}. En rojo y sin dato nunca hay dirección."""
    base = {"color": "rojo", "inmuebles": [], "motivos": [], "lecturas_legibles": [], "frase": None}
    if len(lecturas) < 2:
        base["motivos"].append("Falta la segunda lectura de la IA."); return base
    a, b = (l.get("inmuebles") or [] for l in lecturas[:2])
    base["lecturas_legibles"] = [" / ".join(legible(x) for x in a) or "nada", " / ".join(legible(x) for x in b) or "nada"]
    primera = next((buscar_frase(x.get("frase_direccion"), texto) for x in a + b if buscar_frase(x.get("frase_direccion"), texto)), None)
    base["frase"] = primera
    if len(a) != n_remates or len(b) != n_remates:
        base["motivos"].append(f"La IA entregó {len(a)} y {len(b)} direcciones y el aviso trae {n_remates} remates."); return base
    if [clave_inmueble(x) for x in a] != [clave_inmueble(x) for x in b]:
        base["motivos"].append("Las dos lecturas de la IA no coinciden."); return base
    if all(x.get("tipo") == "sin_dato" for x in a):
        s = _SENALES.search(texto)
        if s:
            base["motivos"].append(f"La IA no encontró la dirección, pero el aviso parece darla ({texto[s.start():s.start() + 80]})."); return base
        base["color"] = "sin_dato"; return base
    for k, (x, y) in enumerate(zip(a, b), start=1):
        v, v2 = verificar_inmueble(x, texto), verificar_inmueble(y, texto)
        pre = f"Remate {k}. " if n_remates > 1 else ""
        if not v["ok"]:
            base["motivos"] += [pre + m for m in v["motivos"]]
        elif not v2["ok"]:
            base["motivos"] += [pre + "Segunda lectura. " + m for m in v2["motivos"]]
        else:
            base["inmuebles"].append({k2: v[k2] for k2 in ("direccion", "comuna", "cita", "citas_extra")})
    if base["motivos"]:
        base["inmuebles"] = []; return base
    if any(i["direccion"] is None for i in base["inmuebles"]):      # mezcla de sin_dato y con dirección
        base["motivos"].append("La IA dio dirección para unos remates y para otros no."); base["inmuebles"] = []; return base
    base["color"] = "verde"
    return base


# --- Texto del rojo (decisión de Diego del 17 de Octubre, con las dos lecturas y la frase del aviso) -------------------
_FALLA_IA = ("El aviso está bien escrito y fue Haiku el que se equivocó. El programa lo atrapó y por eso no te da la dirección. "
             "Revisa en el aviso cuál es la correcta.")


def texto_rojo(res: dict) -> str:
    m = res.get("motivos") or ["El programa no dejó motivo."]
    l1, l2 = (res.get("lecturas_legibles") or ["", ""])[:2] if len(res.get("lecturas_legibles") or []) >= 2 else ("", "")
    if any(x.startswith("Las dos lecturas de la IA no coinciden") for x in m):
        simple = f"Las dos lecturas de la IA dieron direcciones distintas. Una dice {l1} y la otra {l2}."
    elif any("direcciones y el aviso trae" in x for x in m):
        simple = f"La IA no entregó una dirección por cada remate del aviso. Leyó {l1}."
    elif any(x.startswith("La IA no encontró la dirección, pero") for x in m):
        simple = "La IA dijo que el aviso no da la dirección, pero el aviso parece darla."
    elif any(x.startswith("Falta la segunda lectura") for x in m):
        simple = "La IA entregó una sola lectura de las dos que se piden."
    else:
        detalle = " ".join(dict.fromkeys(re.sub(r"^(?:Remate \d+\. )?(?:Segunda lectura\. )?", "", x) for x in m))
        simple = f"La IA leyó {l1}, pero el programa no pudo comprobarlo en el aviso. {detalle}"
    frase = f" En el aviso aparece así '{res['frase'][:220]}'." if res.get("frase") else ""
    return f"Falla de la IA. {simple}{frase} {_FALLA_IA}"


# --- Llamada a la IA con respuestas guardadas --------------------------------------------------------------------
def huella(texto: str, n_remates: int) -> str:
    return hashlib.sha256(f"{MODELO}|{VERSION_INSTRUCCIONES}|{n_remates}|{texto}".encode("utf-8")).hexdigest()


def leer_guardada(texto: str, n_remates: int):
    p = CARPETA_RESPUESTAS / f"{huella(texto, n_remates)}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def leer_con_ia(texto: str, n_remates: int, cliente=None, lecturas: int = 2) -> dict:
    """Devuelve {'lecturas': [..], 'uso': [..]} desde lo guardado, o llama a la IA y lo guarda. Nunca se le pregunta a la
    IA por un aviso que ya tiene su respuesta guardada."""
    g = leer_guardada(texto, n_remates)
    if g and len(g["lecturas"]) >= lecturas:
        return g
    if cliente is None:
        raise RuntimeError("No hay respuesta guardada de la dirección para este aviso y no se entregó cliente de IA.")
    out = {"modelo": MODELO, "version": VERSION_INSTRUCCIONES, "n_remates": n_remates, "lecturas": [], "uso": [], "errores": []}
    pedido = f"El aviso trae {n_remates} remate{'s' if n_remates != 1 else ''}.\n\nAVISO\n{texto}"
    for _ in range(lecturas):
        try:
            resp = cliente.messages.create(
                model=MODELO, max_tokens=1500, thinking={"type": "disabled"},
                system=[{"type": "text", "text": INSTRUCCIONES, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": pedido}],
                output_config={"format": {"type": "json_schema", "schema": ESQUEMA}})
            out["uso"].append({"entrada": resp.usage.input_tokens, "salida": resp.usage.output_tokens,
                               "cache_lectura": getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
                               "cache_escritura": getattr(resp.usage, "cache_creation_input_tokens", 0) or 0,
                               "stop": resp.stop_reason})
            bloque = next(b for b in resp.content if getattr(b, "type", None) == "text")
            out["lecturas"].append(json.loads(bloque.text))
        except Exception as e:                      # la lectura queda en rojo, nunca se inventa
            out["errores"].append(f"{type(e).__name__}: {str(e)[:300]}")
    if len(out["lecturas"]) == lecturas:
        CARPETA_RESPUESTAS.mkdir(parents=True, exist_ok=True)
        (CARPETA_RESPUESTAS / f"{huella(texto, n_remates)}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out
