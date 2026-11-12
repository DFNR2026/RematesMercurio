"""Ciclo 2, tanda 5. El diario imprime a veces el signo ° como un 3 suelto ("REMATE 2 3 JUZGADO", "N 3 22232").
Aplica los arreglos sobre motor/extraccion.py de una copia. Cada arreglo exige encontrar el texto original exacto una sola vez.
Uso python3 -I aplicar_tanda5.py RAIZ [ARREGLO ...] (sin arreglos, aplica todos)."""
import sys
from pathlib import Path

EX = "motor/extraccion.py"
A = {}
# G1. Tribunal. "REMATE 2 3 JUZGADO CIVIL" es el 2° Juzgado Civil y no el 3° (rol 21355-2023 del 9 de Noviembre de 2026).
A["G1"] = [
 (EX, '    num = _ordinal_a_numero(m.group(1), m.group(2)) if (m.group(1) or m.group(2)) else None\n',
  '    num = _ordinal_a_numero(m.group(1), m.group(2)) if (m.group(1) or m.group(2)) else None\n'
  '    cita = m.group(0)\n'
  '    # Ciclo 2, tanda 5, arreglo G1. El diario imprime a veces el ° como un 3 suelto. "REMATE 2 3 JUZGADO CIVIL" es el\n'
  '    # 2° Juzgado y el programa leía el 3° (rol 21355-2023 del 9 de Noviembre de 2026). Si el número leído es un 3 suelto\n'
  '    # y justo antes hay otro número de una o dos cifras, el número del tribunal es el anterior.\n'
  '    if m.group(1) == "3":\n'
  '        previo = re.search(r"(?<![\\d.,/-])(\\d{1,2})\\s$", texto[:m.start()])\n'
  '        if previo and 1 <= int(previo.group(1)) <= 40:\n'
  '            num, cita = int(previo.group(1)), texto[previo.start():m.end()]\n'),
 (EX, '        return {"tribunal": {"valor": None, "cita": m.group(0)}, "alertas": alertas}\n    ciudad = _titulo(ciudad)\n',
  '        return {"tribunal": {"valor": None, "cita": cita}, "alertas": alertas}\n    ciudad = _titulo(ciudad)\n'),
 (EX, '    return {"tribunal": {"valor": valor, "cita": m.group(0)}, "alertas": alertas}\n',
  '    return {"tribunal": {"valor": valor, "cita": cita}, "alertas": alertas}\n'),
]
# G2. Inscripción. "Fojas 15422 N 3 22232" es el número 22232 (rol 21355-2023). Solo si después del 3 viene otro número.
A["G2"] = [
 (EX, r'|no\.?(?=\s*\d)|N(?=\d))\s*{_NUM_INS}", re.I)', r'|no\.?(?=\s*\d)|N\s3(?=\s+\d)|N(?=\d))\s*{_NUM_INS}", re.I)'),
]
ORDEN = ["G1", "G2"]


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
