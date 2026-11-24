"""Mide en los avisos guardados qué datos útiles para el valor comercial trae cada aviso.
Sin IA. Corre desde la carpeta datos (motor, Capturas, banco_pruebas)."""
import sys, re, json, hashlib, collections
sys.path.insert(0, ".")
from motor.edicion import procesar, paginas_desde_captura
from motor.extraccion import minimo_y_costas

EDICIONES = [("banco_pruebas", d) for d in ["2026-09-01", "2026-10-06", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-13", "2026-10-14"]] + \
            [("Capturas", d) for d in ["2026-10-14", "2026-10-15", "2026-10-16", "2026-10-17", "2026-10-18"]]

P = {
    "rol_avaluo": re.compile(r"(?i)rol\s+(?:de\s+)?aval[uú]o|rol\s+(?:del\s+)?s\.?\s?i\.?\s?i\b|rol\s+(?:de\s+)?avaluo|aval[uú]o\s+fiscal\s+(?:n[°ºo]\.?|rol)|rol\s+(?:de\s+)?contribuciones|rol\s+de\s+impuesto\s+territorial"),
    "avaluo_fiscal": re.compile(r"(?i)aval[uú]o\s+fiscal"),
    "tasacion": re.compile(r"(?i)tasaci[oó]n"),
    "pericial": re.compile(r"(?i)tasaci[oó]n\s+pericial|perito|peritaje"),
    "metros": re.compile(r"(?i)\d[\d\.,]*\s*(?:m2|m²|mts2|mts\.?\s?2|metros\s+cuadrados|m\.\s?2)"),
    "departamento": re.compile(r"(?i)\bdepartamento|\bdepto\b|\bdpto\b"),
    "casa": re.compile(r"(?i)\bcasa\b|vivienda"),
}
# mínimo atado al avalúo fiscal o a una tasación (ventana corta alrededor de la palabra mínimo)
MIN_VENTANA = re.compile(r"(?i)m[ií]nimo")

def minimo_ligado(texto, pat):
    for m in MIN_VENTANA.finditer(texto):
        if pat.search(texto[max(0, m.start() - 150): m.end() + 250]):
            return True
    return False

vistos = {}
for base, fecha in EDICIONES:
    rollos, _ = paginas_desde_captura(f"{base}/{fecha}")
    res = procesar(rollos, fecha, cliente=None, usar_ia=False)
    for c in res["causas"]:
        for av in c["avisos"]:
            h = hashlib.sha1(av["texto"].encode()).hexdigest()
            if h in vistos:
                continue
            t = av["texto"]
            r = {k: bool(p.search(t)) for k, p in P.items()}
            mi = minimo_y_costas(t)["minimo"]
            r["minimo_leido"] = bool(mi)
            r["min_avaluo"] = minimo_ligado(t, P["avaluo_fiscal"])
            r["min_tasacion"] = minimo_ligado(t, P["tasacion"])
            r["rol"] = f"{c['rol']}-{c['año']}"
            r["fecha"] = fecha
            r["n_remates"] = av["n_remates"]
            r["inscripcion"] = bool(av.get("inscripciones"))
            vistos[h] = (r, t)

n = len(vistos)
print("Ediciones", len(EDICIONES), "avisos distintos con rol", n)
cnt = collections.Counter()
for r, t in vistos.values():
    for k, v in r.items():
        if v is True:
            cnt[k] += 1
for k in ["inscripcion", "minimo_leido", "rol_avaluo", "avaluo_fiscal", "min_avaluo", "tasacion", "min_tasacion", "pericial", "metros", "departamento", "casa"]:
    print(f"{k:15s} {cnt[k]:4d} de {n}  {100*cnt[k]/n:5.1f}%")
# Muestras de frases para revisar a mano
def muestra(clave, pat, k=6):
    print(f"\n--- muestras {clave}")
    i = 0
    for r, t in vistos.values():
        if r[clave]:
            m = pat.search(t)
            print(" ", r["rol"], "|", re.sub(r"\s+", " ", t[max(0, m.start()-120): m.end()+160]))
            i += 1
            if i >= k: break
muestra("min_avaluo", P["avaluo_fiscal"], 10)
muestra("min_tasacion", P["tasacion"], 6)
muestra("rol_avaluo", P["rol_avaluo"], 6)
muestra("metros", P["metros"], 6)
json.dump([dict(r) for r, t in vistos.values()], open("/home/claude/valor/medicion.json", "w"), ensure_ascii=False, indent=0)
