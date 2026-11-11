"""Ciclo 2, tanda 4 (direcciones) y cambio del corte de dominio a 2019. Aplica los arreglos sobre una copia del proyecto.
Cada arreglo exige encontrar el texto original exacto una sola vez. Respeta el fin de línea de cada archivo.
Uso python3 -I aplicar_tanda4.py RAIZ [ARREGLO ...] (sin arreglos, aplica todos)."""
import sys
from pathlib import Path

DI, ED, NT, CJ, FI, FC, M5 = ("motor/direccion.py", "motor/edicion.py", "motor/numeros_texto.py", "motor/conjunto.py",
                              "motor/filtros.py", "filtro_cbr.py", "modulo5_reporte.py")
A = {}
# T4a. La comuna comprobada se conserva aunque la dirección quede en rojo (1267-2019 de Talca, 10750-2022 de Las Cabras).
A["T4a"] = [
 (DI, 'def _nums(x: dict) -> list:\n',
  'def _comuna_comprobada(x: dict, texto: str):\n'
  '    """La comuna de una lectura si su frase está en el aviso y la trae. Las mismas reglas de verificar_inmueble."""\n'
  '    c, fc0 = x.get("comuna"), x.get("frase_comuna") or ""\n'
  '    if not c or (re.search(r"conservador|\\bCBR\\b|registro", fc0, re.I) and not re.search(r"comuna", fc0, re.I)):\n'
  '        return None\n'
  '    fc = buscar_frase(fc0, texto)\n'
  '    return c.strip() if fc is not None and norm(c) in norm(fc) else None\n\n\n'
  'def comunas_del_rojo(lecturas: list, texto: str, n_remates: int) -> list:\n'
  '    """Ciclo 2, tanda 4, arreglo T4a (decisión de Diego del 10 de Noviembre de 2026). Cuando la dirección queda en rojo, la\n'
  '    comuna de cada remate se conserva si las dos lecturas dan la misma y cada una se comprueba en el aviso. Si no, None\n'
  '    para ese remate. Nunca devuelve una dirección. Sirve para que un inmueble de Talca no pase como RM (1267-2019)."""\n'
  '    if len(lecturas) < 2:\n'
  '        return []\n'
  '    a, b = (l.get("inmuebles") or [] for l in lecturas[:2])\n'
  '    if len(a) != n_remates or len(b) != n_remates:\n'
  '        return []\n'
  '    out = []\n'
  '    for x, y in zip(a, b):\n'
  '        cx, cy = _comuna_comprobada(x, texto), _comuna_comprobada(y, texto)\n'
  '        out.append(cx if cx and cy and norm(cx) == norm(cy) else None)\n'
  '    return out\n\n\n'
  'def _nums(x: dict) -> list:\n'),
 (ED, '    return None, "rojo", [DR.texto_rojo(res)]\n',
  '    # Ciclo 2, tanda 4, arreglo T4a. El rojo no da dirección, pero conserva la comuna si las dos lecturas coinciden y se\n'
  '    # comprueba en el aviso. Así el filtro de la RM puede descartar un inmueble de otra región.\n'
  '    comunas = DR.comunas_del_rojo(g["lecturas"], texto, n)\n'
  '    if any(comunas):\n'
  '        return [{"direccion": None, "comuna": c} for c in comunas], "rojo", [DR.texto_rojo(res)]\n'
  '    return None, "rojo", [DR.texto_rojo(res)]\n'),
]
# D4e. Una lectura agrega la esquina a la calle y la otra no. Queda la parte común (1267-2019).
A["D4e"] = [
 (DI, '    if x.get("tipo") == y.get("tipo") and bool(x.get("unidad")) != bool(y.get("unidad")):\n',
  '    if x.get("tipo") == y.get("tipo") == "calle" and kx[1] and ky[1] and kx[1] != ky[1] and kx[2:] == ky[2:]:\n'
  '        # Ciclo 2, tanda 4, tipo D4e. Mismo número, unidad y comuna, y una lectura agrega la esquina a la calle\n'
  '        # ("calle 6 Oriente" y "calle 6 Oriente esquina 5 Norte", rol 1267-2019). Queda la que trae solo la calle.\n'
  '        if re.match(re.escape(kx[1]) + r"\\s+(?:esquina|esq)\\b", ky[1]):\n'
  '            return (x, y, "esquina")\n'
  '        if re.match(re.escape(ky[1]) + r"\\s+(?:esquina|esq)\\b", kx[1]):\n'
  '            return (y, x, "esquina")\n'
  '    if x.get("tipo") == y.get("tipo") and bool(x.get("unidad")) != bool(y.get("unidad")):\n'),
]
# D12. Un número en palabras pegado a una coma o un punto no se leía completo ("Ciento Seis, del Primer Piso" daba 100).
A["D12"] = [
 (NT, '    partes = re.split(r"(\\s+|-(?=[A-Za-z]\\b))", texto)\n',
  '    # Ciclo 2, tanda 4, tipo D12 (10 de Noviembre de 2026). La coma, el punto o el punto y coma pegados a la palabra se\n'
  '    # separan, para que "Departamento Número Ciento Seis, del Primer Piso" dé 106 y no 100 (rol 12090-2024).\n'
  '    partes = re.split(r"(\\s+|-(?=[A-Za-z]\\b)|(?<=[A-Za-zÁÉÍÓÚÑáéíóúñ])(?=[,;.](?:\\s|$)))", texto)\n'),
]
# E1. Un nombre de edificio de hasta 4 letras se tomaba como subdivisión ("Edificio ONIX", rol 755-2023).
A["E1"] = [
 (CJ, '    return (re.fullmatch(rf"[A-Z0-9\\-]{{1,4}}(?:\\s+',
  '    # Ciclo 2, tanda 4, arreglo E1. Subdivisión es una o dos letras ("B", "AB") o un código con algún número ("5", "B2",\n'
  '    # "A-1"). Una palabra de 3 o 4 letras es un nombre ("Edificio ONIX", rol 755-2023).\n'
  '    return (re.fullmatch(rf"(?:[A-Z]{{1,2}}|(?=[A-Z\\-]*\\d)[A-Z0-9\\-]{{1,4}})(?:\\s+'),
]
# E2. Un nombre de edificio que empieza con "de", "del", "la" ("Edificio de La Recoleta Urbano", rol 14456-2025).
A["E2"] = [
 (CJ, '    if not m:\n        return None\n    n = re.split(',
  '    if not m:\n'
  '        # Ciclo 2, tanda 4, arreglo E2. El nombre puede empezar con "de", "del", "la" si sigue una palabra con mayúscula\n'
  '        # ("Edificio de La Recoleta Urbano", rol 14456-2025). No vale si lo que sigue es una calle u otra cosa, ni si después viene un número.\n'
  '        m = re.match(rf"\\s+((?:(?:del|de|las|la|los|el)\\s+){{1,2}}(?!(?:Calle|Avenida|Av|Avda|Pasaje|Camino|Comuna|Ciudad|Propiedad|Condominio|Conjunto|Proyecto|Edificio|Departamentos?|Oficinas?|Estacionamientos?|Bodegas?|Subterr[aá]neo|Piso|Loteo|Rol)\\b){_PALABRA}(?:\\s+(?:{_CONECTOR}\\b|{_PALABRA})){{0,6}})", s)\n'
  '        if m and re.match(r"\\s*(?:N[°º.]?\\s*|n[uú]mero\\s+)?\\d", palabras_a_cifras(s[m.end():]) or ""):\n'
  '            m = None      # "edificio de Moneda tres mil setenta y cuatro" es una dirección, no un nombre (207-2026)\n'
  '    if not m:\n        return None\n    n = re.split('),
]
# R1. Corte del dominio. Pedido de los abogados del 10 de Noviembre de 2026. Se excluye también el dominio inscrito en 2019,
# porque en esos casos la deuda queda muy cerca del valor comercial. Pasa solo el dominio anterior a 2019.
A["R1"] = [
 (FC, '_CBR_ANIO_CORTE = 2020', '_CBR_ANIO_CORTE = 2019   # hasta el 10 de Noviembre de 2026 era 2020 (pedido de los abogados, deuda muy cerca del valor comercial)'),
 (FC, 'Regla: dominio inscrito >= 2020 -> EXCLUIR', 'Regla: dominio inscrito >= 2019 -> EXCLUIR'),
 (FC, '       dominio inscrito < 2020  -> MANTENER', '       dominio inscrito < 2019  -> MANTENER'),
 (FI, 'año de dominio con el corte 2020 de filtro_cbr.py).', 'año de dominio con el corte de filtro_cbr.py, 2019 desde el 10 de Noviembre de 2026 y antes 2020).'),
 (FI, 'y su dominio es anterior a 2020.\n', 'y su dominio es anterior a 2019.\n'),
 (FI, 'Revisar si es anterior a 2020."', 'Revisar si es anterior a 2019."'),
 (FI, 'Pasa si algún año conocido es anterior a 2020. Falla si todos son 2020 o más."""', 'Pasa si algún año conocido es anterior al corte (2019). Falla si todos son del corte o más."""'),
 (M5, 'value="PROPIEDADES NUEVAS EXCLUIDAS (dominio >= 2020)")', 'value="PROPIEDADES NUEVAS EXCLUIDAS (dominio >= 2019)")'),
 (M5, '"Excluidas por dominio 2020 o posterior"', '"Excluidas por dominio 2019 o posterior"'),
]
ORDEN = ["T4a", "D4e", "D12", "E1", "E2", "R1"]


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
