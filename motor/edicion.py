"""Motor nuevo del Mercurio (etapa B del traspaso, 17 de Octubre de 2026). De las páginas de una edición a las causas
agrupadas por rol. Sin filtros de negocio (eso es la etapa C) y sin Excel (etapa D).

Pasos.
1. Cada rollo de páginas (lo que entrega el lector, en orden de lectura) se une en un solo texto y se corta por aviso,
   con código y sin IA (motor.cortador). Si hay dos rollos (B y G los viernes) se unen sin duplicar por la huella del texto.
2. Cuadre. Cada rol que el código encuentra en el texto debe quedar dentro de algún aviso. Si no, la edición lleva alarma.
3. Cada aviso pasa por la extracción por código (tribunal, inscripción con su año, carátula, cantidad de remates).
4. Los avisos de juez partidor, juez árbitro o partición se eliminan (decisión de Diego). Solo se cuentan.
5. La dirección y la comuna las lee Haiku (motor.direccion), con doble lectura y la frase comprobada por código.
   Primero las respuestas guardadas en ia_respuestas. Si Haiku no responde, el aviso queda sin dirección y con alerta.
   Nunca se cae la corrida por la IA.
6. Los avisos con rol se agrupan en causas con la llave _clave_causa (rol-año más tribunal). Los sin rol van aparte.

Piezas copiadas sin cambios de lógica desde D:\\Agendar_Remates. huella y unir_rollos (motor\\procesar_edicion.py),
roles_del_aviso y alarma_cuadre (motor\\republicaciones.py), _n_remates (motor\\procesar_edicion.py).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from motor.cortador import construir_rollo, cortar, roles_en
from motor.orden_columnas import leer_pagina
from motor.extraccion import tribunal as leer_tribunal, inscripcion, caratula, minimo_y_costas
from motor.partidor import es_partidor
from motor.clave import _clave_causa
from motor import direccion as DR

# Dólares por millón de tokens de Claude Haiku 5.5, verificados por Agendar_Remates el 16 de Octubre de 2026
# (pruebas\\medir_direccion.py). Solo para la hoja Resumen.
PRECIO_HAIKU = {"entrada": 0.10, "salida": 0.50, "cache_lectura": 0.01, "cache_escritura": 0.125}
DIR_NO_LEIDA = "Dirección no leída. La IA no respondió para este aviso. Revisa el aviso."
CUADRE_ALARMA = "Cuadre. "


# --- Copiado de Agendar_Remates (procesar_edicion.py) -------------------------------------------------------------
def huella(texto: str) -> str:
    """Solo letras y números en minúscula. Ignora espacios, guiones y signos, que cambian entre la lectura de B y la de G
    (2026-10-09. 7 de 127 avisos con diferencias de espacios, 127 de 127 iguales con esta huella)."""
    return re.sub(r"[\W_]+", "", texto.lower())


def unir_rollos(cortados: list) -> tuple:
    """cortados = [avisos del cortador por rollo], en el orden de la navegación. El primero es el principal.
    Un aviso de otro rollo con gemelo (misma huella) en el principal no se carga, solo se cuenta. Las repeticiones se
    cuentan, así dos avisos iguales de verdad no se funden en uno. Un aviso sin gemelo se carga después de los del
    principal, con alerta. Si los gemelos imprimen el rol distinto, el aviso del principal lleva una alerta.
    Devuelve (avisos, alertas_extra {orden: [(tipo, texto)]}, resumen)."""
    avisos = list(cortados[0])
    alertas, resumen = {}, []
    for k, otro in enumerate(cortados[1:], start=2):
        libres = {}
        for a in avisos[:len(cortados[0])]:
            libres.setdefault(huella(a.texto), []).append(a)
        unidos = espacios = 0
        solos = []
        for b in otro:
            gem = libres.get(huella(b.texto))
            if gem:
                a = gem.pop(0)
                unidos += 1
                espacios += a.texto != b.texto
                if (a.rol_impreso or "") != (b.rol_impreso or ""):
                    alertas.setdefault(a.orden, []).append(("revisar_lectura",
                        f"El cuerpo {b.paginas[0][0]} imprime este rol distinto ({b.rol_impreso}, aquí {a.rol_impreso}). Revisa el aviso en la página."))
            else:
                solos.append(b)
        for b in solos:
            b.orden = len(avisos) + 1
            avisos.append(b)
            alertas.setdefault(b.orden, []).append(("revisar_lectura",
                f"Aviso que solo aparece en el cuerpo {b.paginas[0][0]}. No tiene gemelo en el cuerpo {cortados[0][0].paginas[0][0]}."))
        c1, c2 = cortados[0][0].paginas[0][0], otro[0].paginas[0][0] if otro else "?"
        resumen.append(f"Cuerpo {c2} repite al {c1}. {unidos} de {len(otro)} avisos unidos por huella del texto. "
                       f"{espacios} con diferencias de espacios. {len(solos)} solo en {c2}.")
    return avisos, alertas, resumen


def _n_remates(ex: dict) -> int:
    mi = ex.get("minimo") or {}
    return len(mi["lista"]) if mi.get("lista") else 1


# --- Copiado de Agendar_Remates (republicaciones.py) --------------------------------------------------------------
def roles_del_aviso(texto: str) -> list:
    """Roles distintos que imprime el aviso, en orden, como (numero, anio, impreso)."""
    vistos, out = set(), []
    for r in roles_en(texto):
        if (r[1], r[2]) not in vistos:
            vistos.add((r[1], r[2])); out.append((r[1], r[2], r[4].strip()))
    return out


def alarma_cuadre(roles_texto: set, avisos: list) -> str | None:
    """Roles del texto de la sección que no quedaron dentro de ningún aviso (texto que se perdió al cortar)."""
    dentro = set()
    for a in avisos:
        dentro |= {(r[0], r[1]) for r in roles_del_aviso(a.texto)}
    faltan = sorted(roles_texto - dentro)
    if not faltan:
        return None
    return (f"{CUADRE_ALARMA}{len(faltan)} rol{'es' if len(faltan) > 1 else ''} del texto no quedaron dentro de ningún aviso "
            f"({', '.join(f'{n}-{a}' for n, a in faltan[:5])}). Revisa la página.")


# --- Entrada desde capturas ----------------------------------------------------------------------------------------
def paginas_desde_captura(carpeta: Path) -> tuple[list, list]:
    """Lee la carpeta que guarda el lector (navegacion.json y el texto de cada página). Devuelve (rollos, alarmas del
    lector). Cada rollo es [(nombre, texto ordenado por la posición impresa)]."""
    carpeta = Path(carpeta)
    nav = json.loads((carpeta / "navegacion.json").read_text(encoding="utf-8"))
    por_nombre = {p["pagina"]: p for p in nav["paginas_con_remates"]}
    rollos = [[(n, leer_pagina(carpeta / por_nombre[n]["archivo"])) for n in r] for r in nav["rollos"]]
    return rollos, list(nav.get("alarmas") or [])


# --- Proceso de una edición ------------------------------------------------------------------------------------------
def _extraer(texto: str, fecha: str) -> dict:
    """Solo lo que usa el Mercurio, sacado por código. NO se usa extraccion.extraer(), porque su regla de "dos fechas,
    avisos pegados" es de la agenda y borra el tribunal cuando el aviso trae una segunda fecha (6 de Agosto, 3 de 3 falsas
    alarmas, 17 de Octubre). El Mercurio no usa fechas. Los avisos pegados de verdad los vigila la revisión de dos roles."""
    tr, ins, ca, mi = leer_tribunal(texto), inscripcion(texto, fecha), caratula(texto), minimo_y_costas(texto)
    return {"tribunal": tr["tribunal"], "inscripcion": {"lista": ins["inscripcion"], "clave": ins["clave"]},
            "caratula": ca["caratula"], "minimo": mi["minimo"], "alertas": tr["alertas"] + ins["alertas"] + ca["alertas"]}


def _direccion(texto: str, n: int, cliente, ia: dict) -> tuple:
    """(direcciones o None, color, alertas). Primero lo guardado. Sin respuesta y sin Haiku, el aviso queda sin
    dirección con su alerta."""
    guardada = DR.leer_guardada(texto, n) is not None
    try:
        g = DR.leer_con_ia(texto, n, cliente)
    except Exception as e:
        g = {"lecturas": [], "errores": [f"{type(e).__name__}. {str(e)[:120]}"]}
    if len(g.get("lecturas") or []) < 2:
        ia["sin_ia"] += 1
        ia["errores"].append(" ".join(g.get("errores") or ["Faltan lecturas de la IA."])[:200])
        if any("AuthenticationError" in e or "invalid x-api-key" in e for e in g.get("errores") or []):
            ia["clave_invalida"] = True
        return None, None, [DIR_NO_LEIDA]
    if not guardada:                                 # llamada nueva a Haiku (lo guardado no se cobra de nuevo)
        ia["llamadas"] += 1
        for u in g.get("uso") or []:
            ia["tokens_entrada"] += (u.get("entrada") or 0) + (u.get("cache_escritura") or 0) + (u.get("cache_lectura") or 0)
            ia["tokens_salida"] += u.get("salida") or 0
            ia["costo_usd"] += sum((u.get(k) or 0) * v / 1e6 for k, v in PRECIO_HAIKU.items())
    res = DR.resolver(g["lecturas"], texto, n)
    ia["leidos"] += 1
    ia["colores"][res["color"]] = ia["colores"].get(res["color"], 0) + 1
    if res["color"] == "verde":
        return [{"direccion": i["direccion"], "comuna": i["comuna"]} for i in res["inmuebles"]], "verde", []
    if res["color"] == "sin_dato":
        return [], "sin_dato", [DR.NO_ENCONTRADA]
    return None, "rojo", [DR.texto_rojo(res)]


def procesar(rollos: list, fecha: str, cliente=None, usar_ia: bool = True) -> dict:
    """rollos = [[(nombre, texto)]] en el orden de la navegación. fecha = AAAA-MM-DD de la edición.
    cliente = cliente de Haiku o None (solo respuestas guardadas). usar_ia=False no lee la dirección."""
    cortados, roles_texto = [], set()
    for paginas in rollos:
        if not paginas:
            continue
        rollo, marcas = construir_rollo(paginas)
        cortados.append(cortar(rollo, marcas))
        roles_texto |= {(r[1], r[2]) for r in roles_en(rollo)}
    cortados = [c for c in cortados if c]
    avisos, alertas_union, alarmas = unir_rollos(cortados) if cortados else ([], {}, [])
    alarmas = list(alarmas)
    if not avisos:
        alarmas.append("La edición no trae avisos de remates de propiedades.")
    linea = alarma_cuadre(roles_texto, avisos)
    if linea:
        alarmas.append(linea)

    ia = {"leidos": 0, "sin_ia": 0, "llamadas": 0, "tokens_entrada": 0, "tokens_salida": 0, "costo_usd": 0.0,
          "colores": {}, "errores": []}
    partidores, sin_rol, con_rol = [], [], []
    for a in avisos:
        ex = _extraer(a.texto, fecha)
        tribunal = (ex.get("tribunal") or {}).get("valor")
        if es_partidor(tribunal, a.texto):
            partidores.append(a.orden)
            continue
        alertas = [t for _, t in ex.get("alertas") or []]
        alertas += [t for _, t in alertas_union.get(a.orden, [])]
        if a.revisar:
            alertas.append(f"Corte del aviso dudoso. {a.revisar[:1].upper()}{a.revisar[1:]}.")
        rs = roles_del_aviso(a.texto)
        if len(rs) > 1:
            alertas.append(f"El aviso imprime {len(rs)} roles distintos ({' y '.join(r[2] for r in rs)}). Revisa cuál es el correcto.")
        n = _n_remates(ex)
        direcciones, color, alertas_dir = (None, None, [])
        if usar_ia:
            direcciones, color, alertas_dir = _direccion(a.texto, n, cliente, ia)
        av = {"edicion": fecha, "orden": a.orden, "paginas": a.paginas, "rol": a.rol, "anio": a.anio, "rol_impreso": a.rol_impreso,
              "tribunal": tribunal, "caratula": (ex.get("caratula") or {}).get("valor"), "n_remates": n,
              "direcciones": direcciones, "dir_color": color,
              "inscripciones": list((ex.get("inscripcion") or {}).get("lista") or []),
              "alertas": alertas + alertas_dir, "texto": a.texto}
        (con_rol if a.rol else sin_rol).append(av)

    causas = {}
    for av in con_rol:
        clave = _clave_causa(av["rol"], av["anio"], av["tribunal"])
        c = causas.get(clave)
        if c is None:
            c = causas[clave] = {"clave": clave, "rol": av["rol"], "año": av["anio"], "tribunal": av["tribunal"] or "",
                                 "caratula": None, "avisos": [], "n_propiedades": 0, "alertas": []}
        c["avisos"].append(av)
        c["n_propiedades"] += av["n_remates"]
        c["caratula"] = c["caratula"] or av["caratula"]
        c["alertas"] += [x for x in av["alertas"] if x not in c["alertas"]]
    return {"fecha": fecha, "avisos_cortados": len(avisos), "roles_en_texto": len(roles_texto),
            "partidores": partidores, "sin_rol": sin_rol, "causas": list(causas.values()), "alarmas": alarmas, "ia": ia}
