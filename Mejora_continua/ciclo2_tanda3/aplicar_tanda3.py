"""Ciclo 2, tanda 3 (carátulas y fojas). Aplica los arreglos sobre motor/extraccion.py y motor/filtros.py de una copia.
Cada arreglo exige encontrar el texto original exacto una sola vez. Uso python3 -I aplicar_tanda3.py RAIZ [ARREGLO ...]
(sin arreglos, aplica todos)."""
import sys
from pathlib import Path

EX, FI = "motor/extraccion.py", "motor/filtros.py"
A = {}
# F1 a F4 y F7, inscripción en el Conservador
A["F1"] = [(EX, r'_FOJAS = re.compile(rf"\bfojas?\.?\s+(?:fs\.?\s*)?{_NUM_INS}',
               r'_FOJAS = re.compile(rf"\b(?:fojas?\.?\s+(?:fs\.?\s*)?|fj?s\.?\s*){_NUM_INS}')]
A["F2"] = [(EX, r'_FOJAS = re.compile(rf"\b', r'_FOJAS = re.compile(rf"\b(?:f\.\s*|'),
           (EX, r'{_NUM_INS}\s*(?:vuelta', r'){_NUM_INS}\s*(?:vuelta')]
A["F3"] = [(EX, r'rf"(?:n[uú]mero|nro', r'rf"(?:n[uú]meros?|nro')]
A["F4"] = [(EX, r'v(?![a-záéíóúñ]))?\s*,?', r'v(?![a-záéíóúñ])|f(?![a-záéíóúñ]))?\s*,?'),
           (EX, r'|nro\.?|n\s*[°º]|', r'|nro\.?|n\.?\s*[°º]|')]
A["F7"] = [(EX, r'corte = re.search(r"M[íi]nimo|\.\s+[A-ZÁÉÍÓÚ]", resto)',
               r'corte = re.search(r"M[íi]nimo|(?<!\bReg)(?<!\bProp)\.\s+[A-ZÁÉÍÓÚ]", resto)')]
# Carátulas
A["C8"] = [(EX, r'_CAR_TRAS_ROL = re.compile(rf"\b(?i:rol)\s+(?:N[°º]\s*)?[A-Za-z]{{1,2}}-[\d.]+',
               r'_CAR_TRAS_ROL = re.compile(rf"\b(?i:rol)\s+(?:N[°º]\s*)?[A-Za-z]{{1,2}}-?[\d.]+')]
A["C9"] = [(EX, r'[\d.]+-\d{{4}},\s+"' + "\n", r'[\d.]+-\s?\d{{4}},\s+"' + "\n"),
           (EX, r'{_TRAMO}{{1,80}}?)(?=\.\s+[A-ZÁÉÍÓÚ]|\.?\s*$)")' + "\n_SUFIJOS",
                r'{_TRAMO}{{1,80}}?)(?=\.\s+[A-ZÁÉÍÓÚ]|\.?\s*$|,\s+(?:se\s+)?rem[aá]t\w*\b)")' + "\n_SUFIJOS")]
A["C10"] = [(EX, r'_CAR_AUTOS = re.compile(rf"\b(?i:autos)\s+', r'_CAR_AUTOS = re.compile(rf"\b(?i:autos|expediente)\s+')]
A["C3b"] = [(EX, "_SUFIJOS = {",
                 "# Ciclo 2, tanda 3, tipo C3b. Comilla de apertura sin cierre y la carátula termina en coma. \"caratulados ‘Banco de Chile\n"
                 "# con Guzmán, remátese\" (5567-2024). El contenido no puede traer ninguna comilla.\n"
                 "_CAR_ABIERTA = re.compile(rf\"[Cc][Aa][Rr][Aa][Tt][Uu][Ll][Aa][Dd]\\w*\\s*[{_COMILLA_A}]\\s*([A-Z0-9ÁÉÍÓÚÑ][^{_COMILLA_A}{_COMILLA_C};\\n]{{2,150}}?{_SEP}[^{_COMILLA_A}{_COMILLA_C};,\\n]{{1,150}}?),\\s*(?:rem[aá]t\\w*|[Rr]ol)\\b\")\n"
                 "_SUFIJOS = {"),
            (EX, "_CAR_ANTECEDENTES, _CAR_AUTOS", "_CAR_ANTECEDENTES, _CAR_AUTOS, _CAR_ABIERTA")]
A["C11"] = [(EX, "    for m in _CAR_COMILLAS.finditer(texto):\n",
                 "    # Ciclo 2, tanda 3, tipo C11. Se prueba desde cada comilla, así una comilla anterior del aviso no se come la de\n"
                 "    # apertura de la carátula (11560-2013).\n"
                 "    for m in (x for x in (_CAR_COMILLAS.match(texto, i) for i, ch in enumerate(texto) if ch in _COMILLA_A) if x):\n")]
NUEVOS = (
    "# Ciclo 2, tanda 3, tipo C12. Carátula sola antes del rol, con barra, al empezar una frase. \"conexión. Avla S.A.G.R./Inversiones\n"
    "# y Servicios Calafquen S.A. Rol C-9252-2022.\"\n"
    "_CAR_ANTES_ROL = re.compile(rf\"(?<=\\.\\s)([A-ZÁÉÍÓÚÑ]{_TRAMO}{{1,100}}?/\\s?(?=[A-ZÁÉÍÓÚÑ]){_TRAMO}{{1,80}}?)\\.?\\s+[Rr][Oo][Ll]\\s+[A-Za-z]{{1,2}}-\\d\")\n"
    "# Ciclo 2, tanda 3, tipo C5b. Punto y coma en vez de la comilla de apertura. \"expediente; Banco Santander-Chile con Lobos’\".\n"
    "_CAR_PUNTO_COMA = re.compile(rf\"\\b(?i:expediente|caratulad\\w*|autos|causa|juicio)\\s*;\\s*([A-ZÁÉÍÓÚÑ][^{_COMILLA_A};\\n]{{2,150}}?{_SEP}[^{_COMILLA_A};\\n]{{1,150}}?)\\s*[{_COMILLA_C}]\")\n"
    "# Ciclo 2, tanda 3, tipo C14. \"expediente cat. Administradora de Tarjetas S.A./Díaz, Rol C-17716-2024\". Una abreviatura\n"
    "# corta en minúscula antes de la carátula, y la carátula termina en \", Rol\".\n"
    "_CAR_EXP_ABREV = re.compile(rf\"\\b(?i:expediente)\\s+([a-záéíóúñ]{{1,4}}\\.\\s+[A-ZÁÉÍÓÚÑ]{_TRAMO}{{1,100}}?{_SEP}(?=\\s*[A-ZÁÉÍÓÚÑ]){_TRAMO}{{1,80}}?)(?=,\\s*[Rr]ol\\b)\")\n")
A["C12"] = [(EX, "_SUFIJOS = {", NUEVOS.split("# Ciclo 2, tanda 3, tipo C5b")[0] + "_SUFIJOS = {"),
            (EX, "_CAR_ANTECEDENTES, _CAR_AUTOS", "_CAR_ANTECEDENTES, _CAR_AUTOS, _CAR_ANTES_ROL")]
A["C5b"] = [(EX, "_SUFIJOS = {", "# Ciclo 2, tanda 3, tipo C5b" + NUEVOS.split("# Ciclo 2, tanda 3, tipo C5b")[1].split("# Ciclo 2, tanda 3, tipo C14")[0] + "_SUFIJOS = {"),
            (EX, "_CAR_ANTECEDENTES, _CAR_AUTOS", "_CAR_ANTECEDENTES, _CAR_AUTOS, _CAR_PUNTO_COMA")]
A["C14"] = [(EX, "_SUFIJOS = {", "# Ciclo 2, tanda 3, tipo C14" + NUEVOS.split("# Ciclo 2, tanda 3, tipo C14")[1] + "_SUFIJOS = {"),
            (EX, "_CAR_ANTECEDENTES, _CAR_AUTOS", "_CAR_ANTECEDENTES, _CAR_AUTOS, _CAR_EXP_ABREV"),
            (EX, "            hallados.append((m.start(1), m.group(1).strip().rstrip(\",\")))\n",
                 "            v = m.group(1).strip().rstrip(\",\")\n"
                 "            hallados.append((m.start(1), v[:1].upper() + v[1:]))\n")]
A["C13"] = [(EX, '        if not re.match(r"[A-Z0-9ÁÉÍÓÚÑ]", v) or re.search(',
                 '        # Ciclo 2, tanda 3, tipo C13. Minúscula al inicio, solo justo después de "caratulado" (11870-2025).\n'
                 '        if re.match(r"[a-záéíóúñ]", v) and re.search(r"caratulad\\w*\\s*$", texto[max(0, m.start() - 30):m.start()], re.I):\n'
                 '            v = v[:1].upper() + v[1:]\n'
                 '        if not re.match(r"[A-Z0-9ÁÉÍÓÚÑ]", v) or re.search(')]
# BancoEstado. "Banco de Estado" en la carátula, y si la carátula está vacía, el nombre en el aviso fuera de las frases de pago.
A["BE"] = [(FI, '_BANCOS_ESTADO = {"banco estado", "banco del estado"}',
                '_BANCOS_ESTADO = {"banco estado", "banco del estado", "banco de estado", "bancoestado"}\n'
                '# Ciclo 2, tanda 3 (decisión de Diego del 9 de Noviembre). Si la carátula no se leyó, se busca el banco en el aviso, pero\n'
                '# no en las frases de pago, donde casi todos los avisos lo nombran (cupón de pago, cuenta corriente del tribunal).\n'
                '_BE_AVISO = re.compile(r"banco\\s*(?:del?\\s*)?estado", re.I)\n'
                '_BE_PAGO = re.compile(r"pago|cuenta|cup[oó]n|dep[oó]sit|vale|consign|tribunal|transferencia|sucursal|endosable|tomad", re.I)\n\n\n'
                'def _bancoestado_en_aviso(c: dict) -> bool:\n'
                '    for av in c.get("avisos") or []:\n'
                '        t = av.get("texto") or ""\n'
                '        for m in _BE_AVISO.finditer(t):\n'
                '            if not _BE_PAGO.search(t[max(0, m.start() - 60):m.start()] + t[m.end():m.end() + 25]):\n'
                '                return True\n'
                '    return False'),
           (FI, '        if any(b in caratula.lower() for b in _BANCOS_ESTADO):\n',
                '        if any(b in caratula.lower() for b in _BANCOS_ESTADO) or (not caratula and _bancoestado_en_aviso(c)):\n')]
ORDEN = ["F1", "F2", "F3", "F4", "F7", "C8", "C9", "C10", "C3b", "C11", "C12", "C5b", "C14", "C13", "BE"]


def aplicar(raiz, cuales):
    raiz = Path(raiz)
    for k in [x for x in ORDEN if x in cuales]:
        for arch, viejo, nuevo in A[k]:
            p = raiz / arch
            t = p.read_text(encoding="utf-8")
            n = t.count(viejo)
            if n != 1:
                sys.exit(f"{k}: el texto original aparece {n} veces en {arch}")
            p.write_text(t.replace(viejo, nuevo), encoding="utf-8")
        print("aplicado", k)


if __name__ == "__main__":
    aplicar(sys.argv[1], sys.argv[2:] or ORDEN)
