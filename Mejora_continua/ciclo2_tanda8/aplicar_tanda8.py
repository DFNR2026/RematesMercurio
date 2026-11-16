"""Ciclo 2, tanda 8. Aplica los arreglos sobre una copia del proyecto (sobre la tanda 7 publicada, HEAD 51ac4c2).
Cada arreglo exige encontrar el texto original exacto una sola vez. Respeta el fin de línea de cada archivo.
Uso python3 -I aplicar_tanda8.py RAIZ [ARREGLO ...] (sin arreglos, aplica todos)."""
import sys
from pathlib import Path

ED, M1, FI = "motor/edicion.py", "modulo1_mercurio.py", "motor/filtros.py"
A = {}
# NC1. Decisión de Diego del 16 de Noviembre de 2026. Los remates de juzgados que no son civiles (Cobranza Laboral,
# Familia y Letras del Trabajo) se eliminan del todo, igual que Policía Local (PL1). Se reconocen por el tribunal que lee
# el código, antes de la IA. "Juzgado de Letras" a secas y "Juzgado de Letras y Garantía" siguen, porque tienen
# competencia civil en su territorio.
A["NC1"] = [
 (ED, '    partidores, voluntarias, policia_local, sin_rol, con_rol = [], [], [], [], []\n',
      '    partidores, voluntarias, policia_local, no_civiles, sin_rol, con_rol = [], [], [], [], [], []\n'),
 (ED, '            policia_local.append(a.orden)\n            continue\n',
      '            policia_local.append(a.orden)\n            continue\n'
      '        # Ciclo 2, tanda 8, NC1. Cobranza Laboral, Familia y Letras del Trabajo, se eliminan del todo (Diego, 16 de Noviembre).\n'
      '        if tribunal and re.search(r"(?i)cobranza\\s+laboral|juzgado\\s+de\\s+familia|letras\\s+del\\s+trabajo", tribunal):\n'
      '            no_civiles.append(a.orden)\n            continue\n'),
 (ED, '"policia_local": policia_local, "sin_rol": sin_rol,',
      '"policia_local": policia_local, "no_civiles": no_civiles, "sin_rol": sin_rol,'),
 (M1, '%d de Policía Local eliminados, %d sin rol, %d causas. IA %s",\n',
      '%d de Policía Local eliminados, %d de otros juzgados no civiles eliminados, %d sin rol, %d causas. IA %s",\n'),
 (M1, 'len(res.get("policia_local") or []), len(res["sin_rol"]),',
      'len(res.get("policia_local") or []), len(res.get("no_civiles") or []), len(res["sin_rol"]),'),
]
# PG1. Decisión de Diego del 16 de Noviembre de 2026. Un aviso pegado a otro que el programa no pudo separar iba siempre a
# la principal sin filtros, para no perder el segundo aviso (salvaguarda del 17 de Octubre). Ahora, si todas sus
# propiedades traen una comuna comprobada y ninguna es de la RM, va a Descartadas por fuera de la RM (1296-2023 de
# Valdivia, 15 y 16 de Noviembre). Si alguna no trae comuna o alguna es de la RM, sigue a la principal como antes.
A["PG1"] = [
 (FI, '            props = propiedades(c)\n            dem, ddo = partir_caratula(c.get("caratula") or "")\n',
      '            props = propiedades(c)\n'
      '            # Ciclo 2, tanda 8, PG1. Pegado con todas sus comunas comprobadas fuera de la RM, a Descartadas.\n'
      '            _cs = [(p.get("comuna") or "").strip() for p in props]\n'
      '            if _cs and all(_cs) and not any(_normalizar_comuna(x) in _COMUNAS_RM_NORM for x in _cs):\n'
      '                descartados.append({**base, "motivo": "Propiedad fuera de RM: " + _unir(_cs)\n'
      '                                    + f". Aviso pegado a otro (roles {\' y \'.join(roles)})", "monto": None})\n'
      '                continue\n'
      '            dem, ddo = partir_caratula(c.get("caratula") or "")\n'),
]
TE, TF = "pruebas/test_edicion.py", "pruebas/test_filtros.py"
# NC1 en las pruebas de inventario. Las causas de juzgados no civiles ya no salen de procesar(), así que el inventario
# del 14 de Octubre baja de 57 a 55 (3908-2025 y 770-2014, Cobranza Laboral) y el del 6 de Agosto de 93 a 92 (84-2016).
A["NC1"] += [
 (TE, 'inv = claves_inventario("2026-10-14")\n',
      'inv = {k for k in claves_inventario("2026-10-14") if not any(x in k for x in ("cobranza laboral", "juzgado de familia", "letras del trabajo"))}  # tanda 8, NC1\n'),
 (TE, 'revisar("4. causas 57 y calzan con el inventario", len(r["causas"]) == 57 and got == inv,',
      'revisar("4. causas 55 y calzan con el inventario (sin las 2 de Cobranza Laboral)", len(r["causas"]) == 55 and got == inv,'),
 (TE, 'inv = claves_inventario("2026-08-06")\n',
      'inv = {k for k in claves_inventario("2026-08-06") if not any(x in k for x in ("cobranza laboral", "juzgado de familia", "letras del trabajo"))}  # tanda 8, NC1\n'),
 (TE, 'revisar("10. causas 93 y calzan con el inventario", len(r["causas"]) == 93 and got == inv,',
      'revisar("10. causas 92 y calzan con el inventario (sin la de Cobranza Laboral)", len(r["causas"]) == 92 and got == inv,'),
 (TF, 'revisar("18. las 57 causas del 14 de Octubre en exactamente una tabla", tot == 57 and ',
      'revisar("18. las 55 causas del 14 de Octubre en exactamente una tabla (sin las 2 de Cobranza Laboral, tanda 8)", tot == 55 and '),
 (TF, ' + len(set(r.get("terrenos_eliminados") or [])) == 57,',
      ' + len(set(r.get("terrenos_eliminados") or [])) == 55,'),
]

ORDEN = ["NC1", "PG1"]


def aplicar(raiz, nombres):
    for n in nombres:
        for rel, viejo, nuevo in A[n]:
            p = Path(raiz) / rel
            b = p.read_bytes()
            crlf = b"\r\n" in b
            t = b.decode("utf-8")
            if crlf:
                viejo, nuevo = viejo.replace("\n", "\r\n"), nuevo.replace("\n", "\r\n")
            if t.count(viejo) != 1:
                raise SystemExit(f"{n}. No encontré una sola vez el texto original en {rel} ({t.count(viejo)} veces)")
            p.write_bytes(t.replace(viejo, nuevo).encode("utf-8"))
        print("aplicado", n)


if __name__ == "__main__":
    aplicar(sys.argv[1], sys.argv[2:] or ORDEN)
