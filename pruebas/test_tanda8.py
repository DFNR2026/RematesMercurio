"""Ciclo 2 de mejora de la lectura, tanda 8 (16 de Noviembre de 2026). Juzgados no civiles eliminados (NC1) y avisos
pegados con todas sus propiedades fuera de la RM a Descartadas (PG1). Sin internet y sin IA.
Uso python pruebas/test_tanda8.py desde la raíz del proyecto."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.edicion import procesar, paginas_desde_captura
from motor import filtros as F
from motor.clave import _clave_causa

fallas = 0


def revisar(nombre, condicion, detalle=""):
    global fallas
    if not condicion:
        fallas += 1
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)


# --- NC1. Juzgados no civiles ---------------------------------------------------------------------------------------
_raiz = Path(__file__).resolve().parent.parent
_r = procesar(paginas_desde_captura(_raiz / "banco_pruebas" / "2026-10-09")[0], "2026-10-09", cliente=None)
_tr = [c.get("tribunal") or "" for c in _r["causas"]]
revisar("NC1 Cobranza Laboral de Temuco y 3° de Familia eliminados (banco del 9 de Octubre)", len(_r.get("no_civiles") or []) == 2, str(_r.get("no_civiles")))
revisar("NC1 ninguna causa que queda es de Cobranza, Familia o Trabajo",
        not any(("Cobranza" in t or "Familia" in t or "Trabajo" in t) for t in _tr))
revisar("NC1 los Juzgados de Letras con competencia civil siguen", any("Juzgado de Letras" in t and "Trabajo" not in t for t in _tr), str(sorted(set(_tr))[:5]))
revisar("PL1 sigue eliminando Policía Local", len(_r.get("policia_local") or []) == 1)

# --- PG1. Aviso pegado con todas sus comunas fuera de la RM ---------------------------------------------------------
_n = [0]


def _pegado(rol, comunas):
    _n[0] += 1
    av = {"edicion": "2026-11-15", "orden": _n[0], "paginas": ["F10"], "n_remates": len(comunas), "dir_color": "verde",
          "texto": f"REMATE 1° Juzgado Civil. ROL C-{rol}-2023 ... otro aviso rol 504-2018. Aviso {_n[0]}",
          "direcciones": [{"direccion": f"Avenida Uno {i}", "comuna": c, "tipo": "calle", "cita": "Avenida Uno"} for i, c in enumerate(comunas)],
          "inscripciones": [{"fojas": "1", "numero": "1", "anio": "2010"} for _ in comunas],
          "alertas": ["Corte del aviso dudoso. Dos roles distintos en un mismo trozo y no se encontró dónde partir."]}
    return {"clave": _clave_causa(rol, "2023", "1° Juzgado Civil de Valdivia"), "rol": rol, "año": "2023",
            "tribunal": "1° Juzgado Civil de Valdivia", "caratula": "", "avisos": [av], "n_propiedades": len(comunas),
            "alertas": list(av["alertas"])}


_t = F.aplicar([{"fecha": "2026-11-15", "sin_rol": [], "causas": [
    _pegado("1296", ["Valdivia"]), _pegado("1297", ["Valdivia", "Maipú"]), _pegado("1298", [None])]}],
    {}, lambda t: "C.A. de Valdivia")
_d = [x for x in _t["descartados"] if x["rol"] == "1296"]
revisar("PG1 pegado con la comuna fuera de la RM va a Descartadas (1296-2023 de Valdivia)",
        len(_d) == 1 and _d[0]["motivo"].startswith("Propiedad fuera de RM: Valdivia") and "pegado" in _d[0]["motivo"], str(_d))
revisar("PG1 pegado con una propiedad en la RM sigue en la principal", any(x["rol"] == "1297" for x in _t["principal"]))
revisar("PG1 pegado sin comuna sigue en la principal", any(x["rol"] == "1298" for x in _t["principal"]))

print()
print("RESULTADO.", "TODO OK" if not fallas else f"{fallas} FALLAS")
sys.exit(1 if fallas else 0)
