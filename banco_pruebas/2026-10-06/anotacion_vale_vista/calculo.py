"""Cálculo de anotación (solo para armar el banco). Reglas del proyecto al 2026-10-16."""
import csv, datetime as dt
RAIZ = __import__("os").path.expanduser("~/mnt/Agendar_Remates")
FER = {r["fecha"] for r in csv.DictReader(open(RAIZ + "/db/feriados_2026.csv", encoding="utf-8"))}
EDICION = dt.date(2026, 10, 6)
DESDE_EST = (EDICION + dt.timedelta(days=1)).isoformat()
HORA_CIERRE_SUPUESTA = "14:00"   # pregunta 3 al abogado

def habil(d): return d.weekday() < 5 and d.isoformat() not in FER
def habil_antes(d):
    d -= dt.timedelta(days=1)
    while not habil(d): d -= dt.timedelta(days=1)
    return d
def habiles_antes(d, n):
    for _ in range(n): d = habil_antes(d)
    return d

def calcular(a, fecha, hora):
    """a = anotación. Devuelve vv_desde, vv_desde_origen, vv_hasta, vv_estado, preguntas."""
    r = a["regla"]; preg = list(a.get("preguntas_abogado", []))
    if r == "sin_dato":
        return None, None, None, "sin_dato", preg
    d0 = dt.date.fromisoformat(fecha)
    hd, hh = a.get("hora_desde"), a.get("hora_hasta")
    if r == "en_el_remate":
        x = f"{fecha} {hora}"; return x, "texto", x, "calculado", preg
    if r == "horas_antes":
        t = dt.datetime.fromisoformat(f"{fecha} {hora}") - dt.timedelta(hours=a["horas"])
        if habil(t.date()):
            hasta = t.strftime("%Y-%m-%d %H:%M")
        else:
            hasta = f"{habil_antes(t.date() + dt.timedelta(days=1)).isoformat()} {HORA_CIERRE_SUPUESTA}"
            preg.append(3)
        return DESDE_EST, "estimado_dia_siguiente_edicion", hasta, ("revisar" if preg else "calculado"), sorted(set(preg))
    if r == "dias_habiles_antes":
        d = habiles_antes(d0, a["dias"])
    elif r in ("dia_anterior", "dia_anterior_sabado_a_viernes", "dia_anterior_sabado_a_habil"):
        d = d0 - dt.timedelta(days=1)
        if not habil(d):
            cubre = (r != "dia_anterior" and d.weekday() == 5)
            d = habil_antes(d + dt.timedelta(days=1))
            if not cubre: preg.append(2)
    elif r == "dias_semana_anterior":
        # el día de la semana nombrado más cercano antes del remate (0 lunes ... 4 viernes)
        d = d0 - dt.timedelta(days=1)
        while d.weekday() not in a["dias_semana"]: d -= dt.timedelta(days=1)
        if len(a["dias_semana"]) > 1: preg.append(5)
        if not habil(d): preg.append(2)
    elif r == "fecha_fija":
        d = dt.date.fromisoformat(a["fecha"])
    else:
        raise ValueError(r)
    hasta = f"{d.isoformat()} {hh}" if hh else d.isoformat()
    if hd: desde, origen = f"{d.isoformat()} {hd}", "texto"
    else: desde, origen = DESDE_EST, "estimado_dia_siguiente_edicion"
    return desde, origen, hasta, ("revisar" if preg else "calculado"), sorted(set(preg))
