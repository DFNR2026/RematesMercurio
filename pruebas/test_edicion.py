"""Prueba de motor/edicion.py contra el banco (etapa B2 del traspaso). Cifras fijadas antes del código en
MD_Vivos/ETAPA_B_CIFRAS_ESPERADAS.md. Sin internet y sin llamar a Haiku (cliente None, solo respuestas guardadas).
Correr desde D:\\Mercurio con. python -m pruebas.test_edicion"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.edicion import procesar, paginas_desde_captura
from motor.orden_columnas import leer_pagina
from motor.clave import _clave_causa
from motor.partidor import es_partidor
import unicodedata


def sin_tildes(s):
    # Solo para comparar con el inventario, que se escribió a mano sin tildes ("Concepcion"). El diario imprime
    # "Concepción" y el código lo lee bien (auditado el 17 de Octubre). La llave del programa NO se cambia.
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

B = RAIZ / "banco_pruebas"
antes = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
fallas = []


def revisar(nombre, ok, detalle=""):
    print(("OK    " if ok else "FALLA ") + nombre + (f" | {detalle}" if detalle and not ok else ""))
    if not ok:
        fallas.append(nombre)


def claves_inventario(fecha):
    inv = json.loads((B / fecha / f"inventario_correcto_{fecha}.json").read_text(encoding="utf-8"))["avisos"]
    out = set()
    for a in inv:
        if a["rol"] and not es_partidor(a["tribunal"], a["tribunal"] + " " + (a["nota"] or "")):
            r, y = a["rol"].split("-")
            out.add(sin_tildes(_clave_causa(r, y, a["tribunal"])))
    return out


# 14 de Octubre
r = procesar([[("B11", leer_pagina(B / "2026-10-14/mercurio_2026-10-14_B11.txt")),
               ("C8", leer_pagina(B / "2026-10-14/mercurio_2026-10-14_C8.txt"))]], "2026-10-14", cliente=None)
print("\n=== 2026-10-14 ===")
revisar("1. avisos cortados 61", r["avisos_cortados"] == 61, r["avisos_cortados"])
revisar("2. partidores eliminados 4", len(r["partidores"]) == 4, r["partidores"])
revisar("3. avisos sin rol 0", len(r["sin_rol"]) == 0, [a["texto"][:80] for a in r["sin_rol"]])
inv = claves_inventario("2026-10-14")
got = {sin_tildes(c["clave"]) for c in r["causas"]}
revisar("4. causas 57 y calzan con el inventario", len(r["causas"]) == 57 and got == inv,
        f"causas {len(r['causas'])}, faltan {sorted(inv - got)[:5]}, sobran {sorted(got - inv)[:5]}")
revisar("5. 0 avisos sin respuesta guardada de dirección", r["ia"]["sin_ia"] == 0, f"{r['ia']['sin_ia']} {r['ia']['errores'][:2]}")
revisar("6. cuadre sin roles fuera de los avisos", not any(x.startswith("Cuadre.") for x in r["alarmas"]), r["alarmas"])
print("   colores de dirección", r["ia"]["colores"])

# 6 de Agosto
pags = []
for n in (11, 12, 13):
    a = (B / f"2026-08-06/payload_B-20260806-0{n}.0.txt").read_text(encoding="utf-8")
    b = (B / f"2026-08-06/payload_B-20260806-0{n}.1.txt").read_text(encoding="utf-8")
    pags.append((f"B{n}", a + b[2000:]))
r = procesar([pags], "2026-08-06", usar_ia=False)
print("\n=== 2026-08-06 ===")
revisar("7. avisos cortados 95", r["avisos_cortados"] == 95, r["avisos_cortados"])
revisar("8. partidores eliminados 1", len(r["partidores"]) == 1, r["partidores"])
revisar("9. avisos sin rol 1 (Iturra Saldías)", len(r["sin_rol"]) == 1 and "Iturra" in r["sin_rol"][0]["texto"],
        [a["texto"][:80] for a in r["sin_rol"]])
inv = claves_inventario("2026-08-06")
got = {sin_tildes(c["clave"]) for c in r["causas"]}
revisar("10. causas 93 y calzan con el inventario", len(r["causas"]) == 93 and got == inv,
        f"causas {len(r['causas'])}, faltan {sorted(inv - got)[:5]}, sobran {sorted(got - inv)[:5]}")

# 1 de Septiembre
rollos, _ = paginas_desde_captura(B / "2026-09-01")
r = procesar(rollos, "2026-09-01", usar_ia=False)
print("\n=== 2026-09-01 ===")
c5656 = [c for c in r["causas"] if c["rol"] == "5656" and c["año"] == "2013"]
revisar("11. rol 5656-2013 en una sola causa con 26 propiedades", len(c5656) == 1 and c5656[0]["n_propiedades"] == 26,
        [(c["clave"], c["n_propiedades"]) for c in c5656])

despues = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
revisar("candado. ninguna respuesta nueva en ia_respuestas", antes == despues)
print("\nRESULTADO.", "TODO OK" if not fallas else f"{len(fallas)} FALLAS")
sys.exit(1 if fallas else 0)
