"""Respaldo de las respuestas de Haiku dentro de la captura del día (decisión de Diego del 10 de Noviembre de 2026).
Aplica los cambios sobre servidor/diario.py de una copia. Cada cambio exige encontrar el texto original exacto una sola vez.
Uso python3 -I aplicar_respaldo.py RAIZ [CAMBIO ...] (sin cambios, aplica todos)."""
import sys
from pathlib import Path

DI = "servidor/diario.py"
A = {}
# S1. capturas/FECHA.zip trae también las respuestas de Haiku de los avisos de ese día.
A["S1"] = [
 (DI, 'def guardar_captura(salida: str) -> None:\n',
  'def _respuestas_del_dia(z, carpeta: Path) -> int:\n'
  '    """Agrega a la captura las respuestas guardadas de Haiku de los avisos de hoy (decisión de Diego del 10 de Noviembre\n'
  '    de 2026). Así cada día se puede rehacer solo con su captura, sin bajar estado/ia_respuestas.zip. Rearma los avisos\n'
  '    desde la captura, sin internet y sin llamar a Haiku. Nunca detiene la corrida."""\n'
  '    try:\n'
  '        from motor.edicion import procesar, paginas_desde_captura\n'
  '        from motor import direccion as DR\n'
  '        rollos, _ = paginas_desde_captura(carpeta)\n'
  '        res = procesar(rollos, FECHA, cliente=None)\n'
  '        n, vistos = 0, set()\n'
  '        for av in [a for c in res["causas"] for a in c["avisos"]] + res["sin_rol"]:\n'
  '            f = DR.CARPETA_RESPUESTAS / f"{DR.huella(av[\'texto\'], av[\'n_remates\'])}.json"\n'
  '            if f.name not in vistos and f.exists():\n'
  '                vistos.add(f.name)\n'
  '                z.write(f, f"{FECHA}/ia_respuestas/direccion/{f.name}")\n'
  '                n += 1\n'
  '        return n\n'
  '    except Exception as e:\n'
  '        log(f"No se pudieron agregar las respuestas de Haiku a la captura ({type(e).__name__}). La corrida sigue")\n'
  '        return 0\n\n\n'
  'def guardar_captura(salida: str) -> None:\n'),
 (DI, '            z.writestr(f"{FECHA}/salida_main.txt", salida)\n',
  '            z.writestr(f"{FECHA}/salida_main.txt", salida)\n'
  '            n_ia = _respuestas_del_dia(z, carpeta)\n'),
 (DI, 'log(f"Captura del día guardada en Supabase ({n} archivos, {destino.stat().st_size // 1024} KB)")',
  'log(f"Captura del día guardada en Supabase ({n} archivos, {n_ia} respuestas de Haiku, {destino.stat().st_size // 1024} KB)")'),
]
# S2. Si estado/ia_respuestas.zip llega dañado, la corrida sigue (antes se caían los 7 intentos del día).
A["S2"] = [
 (DI, '    with zipfile.ZipFile(RAIZ / "_ia_bajado.zip") as z:\n        z.extractall(CARPETA_IA)\n',
  '    try:\n'
  '        with zipfile.ZipFile(RAIZ / "_ia_bajado.zip") as z:\n'
  '            z.extractall(CARPETA_IA)\n'
  '    except zipfile.BadZipFile:\n'
  '        # El archivo de respuestas llegó dañado (10 de Noviembre de 2026). Antes la corrida se caía aquí en todos los\n'
  '        # intentos y ese día no salía informe. Ahora se guarda el archivo dañado aparte y la corrida sigue. Haiku lee de\n'
  '        # nuevo los avisos de hoy, que cuesta centavos. Si lo que falla es la bajada, se reintenta como siempre.\n'
  '        (CARPETA_IA / "direccion").mkdir(parents=True, exist_ok=True)\n'
  '        try:\n'
  '            E.subir(RAIZ / "_ia_bajado.zip", f"{P}respaldos/ia_respuestas_danado_{FECHA}.zip", "application/zip")\n'
  '        except Exception:\n'
  '            pass\n'
  '        log("El archivo de respuestas de Haiku llegó dañado. Se guardó aparte en respaldos/ y la corrida sigue sin él")\n'),
]
ORDEN = ["S1", "S2"]


def aplicar(raiz, cuales):
    raiz = Path(raiz)
    for k in [x for x in ORDEN if x in cuales]:
        for arch, viejo, nuevo in A[k]:
            p = raiz / arch
            t = p.read_bytes().decode("utf-8")
            if "\r\n" in t:
                viejo, nuevo = viejo.replace("\n", "\r\n"), nuevo.replace("\n", "\r\n")
            n = t.count(viejo)
            if n != 1:
                sys.exit(f"{k}: el texto original aparece {n} veces en {arch}")
            p.write_bytes(t.replace(viejo, nuevo).encode("utf-8"))
        print("aplicado", k)


if __name__ == "__main__":
    aplicar(sys.argv[1], sys.argv[2:] or ORDEN)
