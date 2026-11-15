"""Ciclo 2, tanda 7. Aplica los arreglos sobre una copia del proyecto (sobre la tanda 6 publicada, HEAD 1759663).
Cada arreglo exige encontrar el texto original exacto una sola vez. Respeta el fin de línea de cada archivo.
Uso python3 -I aplicar_tanda7.py RAIZ [ARREGLO ...] (sin arreglos, aplica todos)."""
import sys
from pathlib import Path

ED, M1, EX = "motor/edicion.py", "modulo1_mercurio.py", "motor/extraccion.py"
A = {}
# PL1. Decisión de Diego del 14 de Noviembre de 2026. Los remates de un Juzgado de Policía Local son totalmente irrelevantes
# y se eliminan del todo, como los partidores y las causas voluntarias. El 14 de Noviembre 13136-2022 del Tercer Juzgado de
# Policía Local de Santiago ("causa por daños en choque") entró a la principal porque ninguna regla miraba el tipo de juzgado.
# Se reconoce por el tribunal que lee el código, antes de la IA. No aparece en ninguna tabla ni se anota en la memoria.
A["PL1"] = [
 (ED, '    partidores, voluntarias, sin_rol, con_rol = [], [], [], []\n',
      '    partidores, voluntarias, policia_local, sin_rol, con_rol = [], [], [], [], []\n'),
 (ED, '        if es_voluntaria(a.rol, a.rol_impreso, a.texto):\n            voluntarias.append(a.orden)\n            continue\n',
      '        if es_voluntaria(a.rol, a.rol_impreso, a.texto):\n            voluntarias.append(a.orden)\n            continue\n'
      '        # Ciclo 2, tanda 7, PL1. Juzgado de Policía Local, se elimina del todo (decisión de Diego del 14 de Noviembre de 2026).\n'
      '        if tribunal and re.search(r"(?i)polic[ií]a\\s+local", tribunal):\n'
      '            policia_local.append(a.orden)\n            continue\n'),
 (ED, '            "partidores": partidores, "voluntarias": voluntarias, "sin_rol": sin_rol,',
      '            "partidores": partidores, "voluntarias": voluntarias, "policia_local": policia_local, "sin_rol": sin_rol,'),
 (M1, '%d voluntarias eliminadas, %d sin rol, %d causas. IA %s",\n',
      '%d voluntarias eliminadas, %d de Policía Local eliminados, %d sin rol, %d causas. IA %s",\n'),
 (M1, 'len(res.get("voluntarias") or []), len(res["sin_rol"]),',
      'len(res.get("voluntarias") or []), len(res.get("policia_local") or []), len(res["sin_rol"]),'),
]
# G4. "18° JUZGADO DE CIVIL DE Santiago" (3127-2024, 13 de Noviembre de 2026), con un "de" que sobra antes de Civil. El
# código no reconocía el tribunal y la causa llegaba sin él. Ahora "de Civil" vale como "Civil".
A["G4"] = [
 (EX, '_TIPO = (r"(civil|(?:de\\s+)?letras\\s+(?:en\\s+lo\\s+)?civil|',
      '_TIPO = (r"((?:de\\s+)?civil|(?:de\\s+)?letras\\s+(?:en\\s+lo\\s+)?civil|'),
]
# G5. "REMATE: DÉCIMO SÉPTIMO CIVIL de Santiago, Huérfanos N° 1409" (1455-2023, 1 de Septiembre de 2026), sin la palabra
# Juzgado. Solo se acepta al comienzo del aviso (después de "REMATE", "EXTRACTO" o "ANTE EL"), con el número del juzgado,
# y solo si el comienzo no trajo otro tribunal ni lo dio la frase del rol (G3).
A["G5"] = [
 (EX, 'def tribunal(texto: str) -> dict:\n',
  '_TRIB_SIN_JUZ = re.compile(rf"^\\W*(?:extracto\\s+(?:de\\s+)?)?(?:remate|subasta)\\W*(?:ante\\s+(?:el\\s+)?|en\\s+el\\s+)?{_ORDINAL}\\s*(civil)\\s*,?\\s*(?:de\\s+|del\\s+)?"\n'
  '                           r"([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+(?:\\s+(?:del?|de\\s+la)\\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)", re.I)\n\n\n'
  'def tribunal(texto: str) -> dict:\n'),
 (EX, '    m = _TRIBUNAL.search(texto[:400]) or _tribunal_tras_rol(texto)     # tanda 6, G3\n',
      '    m = _TRIBUNAL.search(texto[:400]) or _tribunal_tras_rol(texto) or _TRIB_SIN_JUZ.match(texto)     # tanda 6 G3, tanda 7 G5\n'),
]
# F11. Inscripción toda en palabras ("a fojas cinco mil noventa y dos número siete mil cuatrocientos ochenta y cuatro ...
# del año dos mil veintiuno", 7170-2026, 12 de Noviembre de 2026). Si el aviso no dio ninguna inscripción en cifras, se
# vuelve a buscar con los números en palabras pasados a cifras. Si ya se leyó alguna, no se toca.
A["F11"] = [
 (EX, '    clave = " + ".join(f"fojas {x[\'fojas\']} n {x[\'numero\']}"',
      '    # Ciclo 2, tanda 7, F11. Inscripción toda en palabras, solo si no se leyó ninguna en cifras (7170-2026).\n'
      '    if not lista and texto and re.search(r"(?i)\\bfojas?\\s+[a-záéíóúñ]", texto):\n'
      '        from motor.numeros_texto import palabras_a_cifras\n'
      '        cifras = palabras_a_cifras(texto)\n'
      '        if cifras != texto:\n'
      '            return inscripcion(cifras, fecha_edicion)\n'
      '    clave = " + ".join(f"fojas {x[\'fojas\']} n {x[\'numero\']}"'),
]
# M1. Dos mínimos que no se asignaban a su inmueble (28-2025, 15 al 18 de Octubre de 2026). El aviso separa los lotes con
# "I.-" y "II.-" y los nombra en palabras ("sitio número cinco", "Oficina número mil uno"), así que ninguna etiqueta con
# número en cifras los distinguía, el código dejaba el mínimo vacío y contaba 1 remate. Ahora, si un mínimo no tiene
# etiqueta ni letra, se usa el último número romano de lote ("I.-", "II.-", "III)") que va antes de él. Solo arma la lista
# si cada mínimo queda con su propio número, igual que antes.
A["M1"] = [
 (EX, '        marca = re.search(r"(?<!\\w)([a-hA-H])\\)\\s", texto[a.end():m.start()])\n',
      '        marca = re.search(r"(?<!\\w)([a-hA-H])\\)\\s", texto[a.end():m.start()])\n'
      '        # Ciclo 2, tanda 7, M1. Lote con número romano ("I.-", "II.-") cuando no hay etiqueta ni letra (28-2025).\n'
      '        if not etiqueta and not marca:\n'
      '            romanos = list(_ROMANO.finditer(texto, hallados[-1]["fin"] if hallados else 0, a.start()))\n'
      '            if romanos:\n'
      '                etiqueta = _Lote(romanos[-1].group(1))\n'),
 (EX, 'def _a_numero(m):\n',
      '# Ciclo 2, tanda 7, M1. Número romano de lote al comienzo de un bloque ("I.-", "II.-", "III)").\n'
      '_ROMANO = re.compile(r"(?<![\\w.])(I{1,3}|IV|VI{0,3}|IX|X)\\s*(?:\\.\\s*-|\\))\\s+")\n\n\n'
      'class _Lote:\n'
      '    """Hace de etiqueta \\"lote I\\" para el mínimo, con la misma forma que un match de _ETIQUETA."""\n'
      '    def __init__(self, n):\n'
      '        self.n = n\n\n'
      '    def group(self, i):\n'
      '        return "Lote" if i == 1 else self.n\n\n\n'
      'def _a_numero(m):\n'),
]
ORDEN = ["PL1", "G4", "G5", "F11", "M1"]


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
