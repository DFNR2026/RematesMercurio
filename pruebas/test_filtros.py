"""Prueba de motor/filtros.py (etapa C del traspaso). Casos armados con las reglas de Diego del 17 de Octubre y cuadre sobre
el banco del 14 de Octubre. Cifras fijadas antes del código en MD_Vivos/ETAPA_C_CIFRAS_ESPERADAS.md. Sin internet.
Correr desde D:\\Mercurio con. python -m pruebas.test_filtros"""
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor import filtros as F
from motor.clave import _clave_causa
from motor.edicion import procesar
from motor.orden_columnas import leer_pagina

fallas = []
def revisar(nombre, ok, detalle=""):
    print(("OK    " if ok else "FALLA ") + nombre + (f" | {detalle}" if detalle and not ok else ""))
    if not ok:
        fallas.append(nombre)

CORTES = {"Juzgado de Letras de Antofagasta": "C.A. de Antofagasta"}
corte_de = lambda t: CORTES.get(t, "C.A. de Santiago")
_n = [0]

def aviso(props, texto=None, fecha="2026-10-14"):
    """props = [(direccion, comuna, año)]. Un aviso con un remate por propiedad y una inscripción por remate."""
    _n[0] += 1
    return {"edicion": fecha, "orden": _n[0], "paginas": ["B11"], "texto": texto or f"aviso numero {_n[0]}",
            "n_remates": len(props), "dir_color": "verde",
            "direcciones": [{"direccion": d, "comuna": c} for d, c, _ in props],
            "inscripciones": [{"fojas": str(1000 + i), "numero": "1", "anio": str(a) if a else None} for i, (_, _, a) in enumerate(props)],
            "alertas": []}

def causa(rol, anio, tribunal, avisos, caratula="Banco de Chile con Pérez", alertas=None):
    return {"clave": _clave_causa(rol, anio, tribunal), "rol": rol, "año": anio, "tribunal": tribunal, "caratula": caratula,
            "avisos": avisos, "n_propiedades": sum(a["n_remates"] for a in avisos), "alertas": alertas or []}

def correr(causas, historico=frozenset(), sin_rol=()):
    return F.aplicar([{"fecha": "2026-10-14", "causas": causas, "sin_rol": list(sin_rol)}], set(historico), corte_de)

def donde(r, rol):
    for tabla in ("principal", "excluidas_cbr", "descartados"):
        for x in r[tabla]:
            if x["rol"] == rol:
                return tabla, x
    return None, None

T = "1° Juzgado Civil de Santiago"
casos = [
    causa("1", "2020", T, [aviso([(f"Calle A {i}", "Maipú", 2021 if i % 2 else 2010)]) for i in range(26)]),
    causa("2", "2020", T, [aviso([("Calle B 1", "Maipú", 2022), ("Calle B 2", "Maipú", 2010), ("Calle B 3", "Maipú", 2010), ("Calle B 4", "Maipú", 2010)])]),
    causa("3", "2020", T, [aviso([(f"Calle C {i}", "Maipú", 2021) for i in range(4)])]),
    causa("4", "2020", T, [aviso([("Calle D 1", "Ovalle", 2010), ("Calle D 2", "Ovalle", 2010), ("Calle D 3", "Maipú", 2010)])]),
    causa("5", "2020", T, [aviso([("Calle E 1", "Ovalle", 2010), ("Calle E 2", "Ovalle", 2010)])]),
    causa("6", "2020", T, [aviso([("Calle F 1", "Maipú", None)])]),
    causa("7", "2020", "", [aviso([("Calle G 1", "Maipú", 2010)])]),
    causa("8", "2020", "Juzgado de Letras de Antofagasta", [aviso([("Calle H 1", "Antofagasta", 2010)])]),
    causa("9", "2020", T, [aviso([("Calle I 1", "Maipú", 2010)])], caratula="Banco del Estado de Chile con Soto"),
    causa("10", "2015", T, [aviso([("Calle J 1", "Maipú", 2010)])]),
    causa("11", "2020", T, [aviso([("Calle K 1", "Maipú", 2010)])]),
    causa("12", "2020", T, [aviso([(f"Calle L {i}", "Ovalle" if i else "Maipú", 2010) for i in range(6)])]),
    causa("13", "2020", T, [aviso([(f"Calle M {i}", "Ovalle", 2010) for i in range(6)])]),
    causa("14", "2020", T, [aviso([("Calle N 1", "Estación Central", 2010)])]),
]
txt = "texto republicado del rol dieciseis"
casos.append(causa("16", "2020", T, [aviso([("Calle P 1", "Maipú", 2010)], texto=txt), aviso([("Calle P 1", "Maipú", 2010)], texto=txt, fecha="2026-10-15")]))
casos.append(causa("17", "2020", T, [aviso([("Calle Q 1", "Maipú", 2010)])]))
casos.append(causa("18", "2020", T, [aviso([("Calle R 1", "Maipú", 2010)])]))
r = correr(casos, historico={_clave_causa("11", "2020", T)})

t, x = donde(r, "1"); revisar("1. 26 propiedades a la principal sin filtro de dominio", t == "principal" and x["direccion"].count(" / ") == 25 and "No se aplicó el filtro de dominio" in x["observaciones"], (t, x and x["observaciones"]))
t, x = donde(r, "2"); revisar("2. 4 propiedades, 1 excluida por dominio", t == "principal" and x["direccion"].count(" / ") == 2 and "1 propiedad excluida" in x["observaciones"] and "2022" in x["observaciones"], (t, x))
t, x = donde(r, "3"); revisar("3. 4 propiedades todas 2021 a excluidas", t == "excluidas_cbr", t)
t, x = donde(r, "4"); revisar("4. 2 en Ovalle y 1 en Maipú, entra solo Maipú", t == "principal" and x["direccion"] == "Calle D 3" and "2 propiedades excluidas" in x["observaciones"], (t, x))
t, x = donde(r, "5"); revisar("5. 2 en Ovalle a descartadas", t == "descartados" and "fuera de RM" in x["motivo"], (t, x))
t, x = donde(r, "6"); revisar("6. sin año de dominio a principal, revisar", t == "principal" and x["revisar"] and F.OBS_DOMINIO in x["observaciones"], (t, x))
t, x = donde(r, "7"); revisar("7. sin tribunal a principal, revisar", t == "principal" and x["revisar"] and F.OBS_TRIBUNAL in x["observaciones"], (t, x))
t, x = donde(r, "8"); revisar("8. Antofagasta a descartadas Solo RM", t == "descartados" and x["motivo"] == "Solo RM", (t, x))
t, x = donde(r, "9"); revisar("9. Banco del Estado a descartadas", t == "descartados" and x["motivo"] == "Banco Estado", (t, x))
t, x = donde(r, "10"); revisar("10. rol 2015 a descartadas Pre-2018", t == "descartados" and x["motivo"] == "Pre-2018", (t, x))
t, x = donde(r, "11"); revisar("11. en historial no aparece", t is None and r["en_historial"] == 1, (t, r["en_historial"]))
t, x = donde(r, "12"); revisar("12. 6 propiedades, 1 en RM, entran las 6", t == "principal" and x["direccion"].count(" / ") == 5, (t, x))
t, x = donde(r, "13"); revisar("13. 6 propiedades fuera de la RM a descartadas", t == "descartados", (t, x))
t, x = donde(r, "14"); revisar("14. Estación Central a descartadas", t == "descartados" and x["motivo"] == "Estación Central", (t, x))
revisar("15. carátulas partidas", F.partir_caratula("Banco de Chile con Aguilera") == ("Banco de Chile", "Aguilera")
        and F.partir_caratula("Banco BCI/Pérez") == ("Banco BCI", "Pérez") and F.partir_caratula("Securitizadora Bice") == ("Securitizadora Bice", ""))
t, x = donde(r, "16"); revisar("16. mismo aviso en dos ediciones, una hilera sin repetir", t == "principal" and x["direccion"] == "Calle P 1" and x["ediciones"] == ["2026-10-14", "2026-10-15"], (t, x))
revisar("17. mismo tribunal, roles distintos, hileras distintas", donde(r, "17")[0] == "principal" and donde(r, "18")[0] == "principal")
print("   observación del caso 2.", donde(r, "2")[1]["observaciones"])
# 20 (agregado el 17 de Octubre, noche). Trozo con dos roles que no se pudo separar y que se descartaría por Banco Estado.
pegado = causa("1442", "2024", "2° Juzgado de Letras de Buin", [aviso([("Parcela 49", "Paine", 2020)], texto="Rol C-1442-2024 ... Rol C-1177-2025 Viña del Mar")],
               caratula="Banco del Estado de Chile con Acugas", alertas=["Corte del aviso dudoso. Dos roles distintos en un mismo trozo y no se encontró dónde partir."])
r20 = correr([pegado])
t, x = donde(r20, "1442")
revisar("20. trozo con dos roles sin separar no se descarta y nombra los dos roles", t == "principal" and x["revisar"] and "1177-2025" in x["observaciones"], (t, x and x["observaciones"]))

# Cuadre sobre el banco del 14 de Octubre, historial vacío
B = RAIZ / "banco_pruebas" / "2026-10-14"
res = procesar([[("B11", leer_pagina(B / "mercurio_2026-10-14_B11.txt")), ("C8", leer_pagina(B / "mercurio_2026-10-14_C8.txt"))]], "2026-10-14", cliente=None)
r = F.aplicar([res], set())
tot = len(r["principal"]) + len(r["excluidas_cbr"]) + len(r["descartados"])
revisar("18. las 57 causas del 14 de Octubre en exactamente una tabla", tot == 57 and len({x["rol"] + x["año"] + x["tribunal"] for t in ("principal", "excluidas_cbr", "descartados") for x in r[t]}) == 57,
        f"principal {len(r['principal'])}, excluidas {len(r['excluidas_cbr'])}, descartadas {len(r['descartados'])}")
revisar("19. tabla de sin rol vacía", r["sin_rol"] == [], r["sin_rol"])
print(f"   14 de Octubre. principal {len(r['principal'])}, excluidas por dominio {len(r['excluidas_cbr'])}, descartadas {len(r['descartados'])}, para revisar {sum(x['revisar'] for x in r['principal'])}")
print("\nRESULTADO.", "TODO OK" if not fallas else f"{len(fallas)} FALLAS")
sys.exit(1 if fallas else 0)
