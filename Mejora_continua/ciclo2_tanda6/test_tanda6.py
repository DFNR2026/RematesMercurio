"""Ciclo 2 de mejora de la lectura, tanda 6 (12 de Noviembre de 2026). Causas voluntarias, fojas con punto, juzgado de otra región con la propiedad en la RM, Corte de Antofagasta, bloques de remates que continúan en otro cuerpo, tribunal nombrado al final y terrenos, oficinas y sitios (13 de Noviembre). Sin internet
y sin IA. Uso python pruebas/test_tanda6.py desde la raíz del proyecto."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.edicion import es_voluntaria
from motor.extraccion import inscripcion

fallas = 0


def revisar(nombre, condicion, detalle=""):
    global fallas
    if not condicion:
        fallas += 1
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)


# --- V1. Causas voluntarias --------------------------------------------------------------------------------------
revisar("V1 rol leído con V y guion (188-2025)", es_voluntaria("188", "Rol V-188-2025", "23° JUZGADO CIVIL SANtiago, V-188-2025 “/O’Brien“."))
revisar("V1 rol leído con V y espacio (310-2025)", es_voluntaria("310", "Rol V 310-2025", "Bases y antecedentes Rol V 310-2025, caratulado ’Núñez’"))
revisar("V1 sin rol, causa V (V-50-2026)", es_voluntaria(None, None, "REMATE: 21° JUZGADO CIVIL DE Santiago en causa V-50-2026 sobre interdicción por demencia"))
revisar("V1 sin rol, V sin la palabra causa (V-238-2025)", es_voluntaria(None, None, "Autos causa “Hirmas/“, V-238-2025, Secretaría."))
revisar("V1 sin rol, Puente Alto (V-439-2026)", es_voluntaria(None, None, "1° JUZGADO CIVIL DE PUENTE Alto, causa V-439-2026. Por resolución"))
revisar("V1 rol C con un extracto V pegado no es voluntaria (C-12153-2025)",
        not es_voluntaria("12153", "Rol C-12.153-2025", "‘Banco Santander-Chile con Gatica’ Rol C-12.153-2025. Secretaría. EXTRACTO ... en causa V-101-2025, ’Charad/ Charad’"))
revisar("V1 rol C normal no es voluntaria", not es_voluntaria("2334", "Rol C-2334-2025", "Rol C-2334-2025. La Secretaría."))
revisar("V1 sin rol y sin V no es voluntaria", not es_voluntaria(None, None, "JUEZ PARTIDOR rematará el inmueble de calle Los Aromos 123"))
revisar("V1 una V dentro de una palabra no cuenta", not es_voluntaria(None, None, "Ley N° 21.389, artículo IV-12-2020 y TV-15-2021"))
revisar("V1 una V sin año no cuenta", not es_voluntaria(None, None, "departamento V-12, bodega V-3"))

# --- F10. Punto entre el número de fojas y "Número" -----------------------------------------------------------------
t = "El dominio se encuentra inscrito a Fojas 49651. Número 69670, correspondiente al Registro de Propiedad del año 2024, del Conservador de Bienes Raíces de Santiago."
r = inscripcion(t, "2026-11-11")["inscripcion"]
revisar("F10 fojas con punto antes de Número (2334-2025)", len(r) == 1 and r[0]["fojas"] == "49651" and r[0]["numero"] == "69670" and r[0]["anio"] == "2024", str(r))
r = inscripcion("inscrito a fojas 1234. N° 5678 del Registro de Propiedad del año 2015 del Conservador de Bienes Raíces de Santiago", "2026-11-11")["inscripcion"]
revisar("F10 fojas con punto antes de N°", len(r) == 1 and r[0]["numero"] == "5678" and r[0]["anio"] == "2015", str(r))
r = inscripcion("Fojas 49651, Número 69670, del Registro de Propiedad del año 2024", "2026-11-11")["inscripcion"]
revisar("F10 la coma sigue igual", len(r) == 1 and r[0]["anio"] == "2024", str(r))
r = inscripcion("fojas 4683 vta. Número 4293 del Registro de Propiedad del año 2020", "2026-11-11")["inscripcion"]
revisar("F10 vta. sigue igual", len(r) == 1 and r[0]["fojas"] == "4683" and r[0]["numero"] == "4293", str(r))
r = inscripcion("inscrito a fojas 1234. Mínimo para la subasta 2.500 UF", "2026-11-11")["inscripcion"]
revisar("F10 punto seguido de otra frase sin número no inventa inscripción", r == [], str(r))

# --- RM1. Juzgado de otra región con la propiedad en la RM (decisión de Diego del 12 de Noviembre de 2026) -------------
from motor import filtros as F
from motor.clave import _clave_causa
_n = [0]


def _aviso(props):
    _n[0] += 1
    return {"edicion": "2026-11-12", "orden": _n[0], "paginas": ["B10"], "texto": f"aviso de prueba {_n[0]}",
            "n_remates": len(props), "dir_color": "verde", "direcciones": [{"direccion": d, "comuna": c} for d, c, _ in props],
            "inscripciones": [{"fojas": str(100 + i), "numero": "1", "anio": str(a)} for i, (_, _, a) in enumerate(props)],
            "alertas": []}


def _causa(rol, tribunal, props):
    av = _aviso(props)
    return {"clave": _clave_causa(rol, "2025", tribunal), "rol": rol, "año": "2025", "tribunal": tribunal,
            "caratula": "Banco de Chile con Pérez", "avisos": [av], "n_propiedades": av["n_remates"], "alertas": []}


_CORTES = {"1° Juzgado de Letras de Punta Arenas": "C.A. de Punta Arenas", "1° Juzgado Civil de Viña del Mar": "C.A. de Valparaíso"}
r = F.aplicar([{"fecha": "2026-11-12", "sin_rol": [], "causas": [
    _causa("956", "1° Juzgado de Letras de Punta Arenas", [("calle Ricardo Lyon 505", "Providencia", 2010)]),
    _causa("1558", "1° Juzgado Civil de Viña del Mar", [("calle Uno 1", "Estación Central", 2010)]),
    _causa("6206", "1° Juzgado Civil de Viña del Mar", [("calle Dos 2", "Viña del Mar", 2010)]),
    _causa("7000", "1° Juzgado Civil de Viña del Mar", [(None, None, 2010)]),
    _causa("7001", "1° Juzgado Civil de Viña del Mar", [("calle Tres 3", "Providencia", 2021)]),
]}], {}, lambda t: _CORTES.get(t, "C.A. de Santiago"))


def _donde(rol):
    for tabla in ("principal", "excluidas_cbr", "descartados"):
        for x in r[tabla]:
            if x.get("rol") == rol:
                return tabla, x
    return None, None


t, x = _donde("956")
revisar("RM1 Punta Arenas con la propiedad en Providencia entra a la principal", t == "principal", str((t, x and x.get("motivo"))))
revisar("RM1 lleva la Observación de otra región", t == "principal" and F.OBS_OTRA_REGION in (x.get("observaciones") or ""), str(x and x.get("observaciones")))
t, x = _donde("1558")
revisar("RM1 Viña con Estación Central sigue descartada por Estación Central", t == "descartados" and x.get("motivo") == "Estación Central", str((t, x and x.get("motivo"))))
t, x = _donde("6206")
revisar("RM1 Viña con la propiedad en Viña sigue en Solo RM", t == "descartados" and x.get("motivo") == "Solo RM", str((t, x and x.get("motivo"))))
t, x = _donde("7000")
revisar("RM1 sin comuna la Corte sigue decidiendo (Solo RM)", t == "descartados" and x.get("motivo") == "Solo RM", str((t, x and x.get("motivo"))))
t, x = _donde("7001")
revisar("RM1 con la propiedad en la RM pasa igual por el dominio (2021 a Excluidas)", t == "excluidas_cbr", str((t, x and x.get("motivo"))))
revisar("RM1 una comuna parecida no basta (sin coincidencia difusa)", not F._alguna_comuna_rm(_causa("1", "x", [("c", "Providenciaa", 2010)])))

# --- K1. Empate de nombres en buscar_corte (Antofagasta) ---------------------------------------------------------
_viejo = F._referencia_cache
F._referencia_cache = [{"nombre_tribunal": f"{n}º Juzgado de Letras Civil de Antofagasta", "corte": "C.A. de Antofagasta"} for n in (1, 2, 3)] + \
                      [{"nombre_tribunal": "4° Juzgado de Letras Civil de Antofagasta", "corte": "C.A. de Antofagasta"},
                       {"nombre_tribunal": "2° Juzgado Civil de Santiago", "corte": "C.A. de Santiago"}]
for n in (1, 2, 3, 4):
    revisar(f"K1 {n}° Juzgado de Letras de Antofagasta encuentra su Corte", F.buscar_corte(f"{n}° Juzgado de Letras de Antofagasta") == "C.A. de Antofagasta")
revisar("K1 un número que no está en la hoja no se inventa (5°)", F.buscar_corte("5° Juzgado de Letras de Antofagasta") is None)
revisar("K1 Santiago sigue igual", F.buscar_corte("2° Juzgado Civil de Santiago") == "C.A. de Santiago")
F._referencia_cache = _viejo

# --- B1 y B2. Bloques de remates que continúan en otro cuerpo sin flecha (13 de Noviembre de 2026) --------------------
from motor.edicion import unir_continuaciones, procesar
_CAB = "1616\nRemates de\npropiedades\n"
_P1 = _CAB + ("REMATE: 1° JUZGADO CIVIL DE Santiago, Huérfanos 1409, rematará el 3 de diciembre de 2026 la propiedad de calle Uno 100, comuna de Maipú. "
              "Bases y antecedentes Rol C-100-2024, caratulado Banco con Pérez. La Secretaria.\n"
              "REMATE: 22° JUZGADO CIVIL DE Santiago, Huérfanos 1409, piso 17, el 7 de diciembre de 2026 se subastará el departamento 97 de "
              "Avenida Cerro Paranal 515, comuna de Antofagasta. Para la garantía todo postor de-")
_P2 = _CAB + ("berá acompañar vale vista a la orden del tribunal. Demás antecedentes en expediente C-1445-2024, Scotiabank Chile con Ojeda. Secretario.\n"
              "REMATE: 2° JUZGADO CIVIL DE Santiago, Huérfanos 1409, rematará el 9 de diciembre de 2026 la propiedad de calle Dos 200, comuna de Ñuñoa. "
              "Bases y antecedentes Rol C-200-2024, caratulado Banco con Soto. La Secretaria.")
_P2b = _CAB + _P2[len(_CAB):].replace("berá acompañar", "Deberá acompañar", 1)
_r, _n = unir_continuaciones([[("B11", _P1)], [("C8", _P2)]])
revisar("B1 un aviso cortado entre dos bloques los une en uno", len(_r) == 1 and len(_n) == 1, str(_n))
_r, _n = unir_continuaciones([[("B11", _P1)], [("C8", _P2b)]])
revisar("B1 si el segundo bloque empieza con mayúscula no se unen", len(_r) == 2 and not _n)
_r, _n = unir_continuaciones([[("B10", _P2b)], [("G9", _P2b)]])
revisar("B1 un cuerpo reimpreso (B y G de los viernes) no se une", len(_r) == 2 and not _n)
_res = procesar([[("B11", _P1)], [("C8", _P2)], [("G12", _P1[:-1] + _P2[len(_CAB):])]], "2026-11-13", usar_ia=False)
_c = {c["rol"]: c for c in _res["causas"]}
revisar("B1 el aviso partido sale una vez, con su rol y su tribunal (1445-2024)",
        _res["avisos_cortados"] == 3 and not _res["sin_rol"] and len(_res["causas"]) == 3
        and _c["1445"]["tribunal"] == "22° Juzgado Civil de Santiago" and len(_c["1445"]["avisos"]) == 1, str(_res["alarmas"]))
_res = procesar([[("B11", _P1)], [("C8", _P2b)], [("G12", _P1 + " " + _P2b[len(_CAB):])]], "2026-11-13", usar_ia=False)
_c200 = [c for c in _res["causas"] if c["rol"] == "200"]
revisar("B2 un aviso del segundo bloque que el tercero reimprime entra una sola vez",
        len(_c200) == 1 and len(_c200[0]["avisos"]) == 1 and any("2 de 3 avisos unidos" in a for a in _res["alarmas"]), str(_res["alarmas"]))

# --- G3. Tribunal nombrado solo al final, después del rol (6458-2022, 13 de Noviembre de 2026) -----------------------
from motor.extraccion import tribunal
_t6458 = ("REMATE. SE ORDENA REMATAR en pública subasta el día 3 de diciembre del 2026, a las 13:30 horas, mediante videoconferencia. "
          "La propiedad de Víctor Hugo Montoya Escobar, casa N° 135, calle El Guanaco Norte N° 1.942, comuna de Huechuraba. " + "x " * 200 +
          "garantía mediante vale vista tomado a nombre del Décimo Tercer Juzgado Civil de Santiago, Rut N° 60.306.013-k. "
          "Bases y demás antecedentes en la causa digital C-6458-2022 seguida ante el 13° Juzgado Civil de Santiago, Secretario.")
revisar("G3 tribunal al final, después del rol (6458-2022)", tribunal(_t6458)["tribunal"]["valor"] == "13° Juzgado Civil de Santiago", str(tribunal(_t6458)))
revisar("G3 el vale vista solo no da tribunal", tribunal(_t6458.split("Bases y")[0])["tribunal"]["valor"] is None)
_tdos = _t6458 + " Antecedentes en causa C-1-2020 seguida ante el 2° Juzgado Civil de Santiago."
revisar("G3 dos frases con tribunales distintos no eligen ninguno", tribunal(_tdos)["tribunal"]["valor"] is None, str(tribunal(_tdos)))
_tcab = "REMATE: 5° JUZGADO CIVIL DE Santiago, Huérfanos 1409, rematará. " + "x " * 220 + "antecedentes en causa C-9-2024 seguida ante el 13° Juzgado Civil de Santiago."
revisar("G3 si el comienzo trae tribunal, manda el comienzo", tribunal(_tcab)["tribunal"]["valor"] == "5° Juzgado Civil de Santiago")

# --- T1 y T2. Terrenos sin calle, oficinas, sitios y terrenos (decisiones de Diego del 13 de Noviembre de 2026) -------
ci = F.clase_inmueble
revisar("T1 terreno sin calle", ci("Lote B del plano de subdivisión de la Parcela Diez", "sin_calle", "Lote B del plano de subdivisión") == "terreno_sin_calle")
revisar("T1 sin calle con casa en su frase no se elimina (6996-2023)", ci("el sitio y casa Parcela número 4", "sin_calle", "el sitio y casa Parcela número 4 del Loteo Los Tilos") is None)
revisar("T1 Casablanca no cuenta como casa", ci("Parcela 43", "sin_calle", "Parcela 43, Conservador de Casablanca") == "terreno_sin_calle")
revisar("T2 oficina", ci("Edificio. Avenida Holanda 067, oficina 101", "calle", "Avenida Holanda N° 067") == "oficina")
revisar("T2 sitio sin casa", ci("calle Los Aromos 12, sitio 5", "calle", "calle Los Aromos N° 12, sitio 5", "remata el sitio 5 de calle Los Aromos 12") == "sitio")
revisar("T2 casa y sitio no se aparta", ci("calle Los Aromos 12, sitio 5", "calle", "calle Los Aromos N° 12", "remata la casa y sitio de calle Los Aromos 12") is None)
revisar("T2 lote de condominio no se aparta (4590-2026)", ci("Condominio Alto Casa Grande Doce-B. calle Las Perdices 2970, lote 17", "calle", "calle Las Perdices N° 2970") is None)
revisar("T2 departamento normal no se aparta", ci("Edificio ONIX. Primera Avenida 1336, Departamento 1809. Bodega 163", "calle", "Primera Avenida 1336") is None)
revisar("T2 terreno con calle", ci("calle Uno 100, terreno", "calle", "terreno de calle Uno N° 100") == "terreno")


_k2 = [0]


def _av2(dirs, texto="aviso de prueba"):
    _k2[0] += 1
    return {"edicion": "2026-11-13", "orden": _k2[0], "paginas": ["B10"], "texto": f"{texto} {_k2[0]}", "n_remates": len(dirs),
            "dir_color": "verde", "direcciones": [{"direccion": d, "comuna": "Maipú", "tipo": t, "cita": d} for d, t in dirs],
            "inscripciones": [{"fojas": "1", "numero": "1", "anio": "2010"} for _ in dirs], "alertas": []}


def _c2(rol, dirs):
    av = _av2(dirs)
    return {"clave": _clave_causa(rol, "2025", "1° Juzgado Civil de Santiago"), "rol": rol, "año": "2025",
            "tribunal": "1° Juzgado Civil de Santiago", "caratula": "Banco de Chile con Pérez", "avisos": [av],
            "n_propiedades": av["n_remates"], "alertas": []}


r2 = F.aplicar([{"fecha": "2026-11-13", "causas": [
    _c2("100", [("Lote 4 de la Parcela 9", "sin_calle")]),
    _c2("101", [("Avenida Pajaritos 3195, oficina 602", "calle"), ("Avenida Pajaritos 3195, oficina 603", "calle")]),
    _c2("102", [("calle Uno 100, departamento 5", "calle")]),
    _c2("103", [("calle Uno 100, departamento 5", "calle"), ("Lote 4 de la Parcela 9", "sin_calle")]),
    _c2("104", [("Avenida Holanda 067, oficina 101", "calle"), ("Lote 4 de la Parcela 9", "sin_calle")]),
], "sin_rol": [_av2([("Parcela 7 del Fundo X", "sin_calle")]), _av2([("calle Dos 2, oficina 3", "calle")])]}],
    {"x": []}, lambda t: "C.A. de Santiago")
_en = lambda rol, tabla: [x for x in r2[tabla] if x.get("rol") == rol]
_todas = lambda rol: [t for t in ("principal", "excluidas_cbr", "descartados", "ya_informadas", "apartadas") if _en(rol, t)]
revisar("T1 una causa de solo terreno sin calle no aparece en ninguna tabla", _todas("100") == [], str(_todas("100")))
revisar("T1 queda contada como terreno eliminado", any("100-2025" in str(k) for k in r2["terrenos_eliminados"]), str(r2["terrenos_eliminados"]))
revisar("T2 una causa de dos oficinas va a la tabla aparte", _todas("101") == ["apartadas"] and _en("101", "apartadas")[0]["motivo"] == "Es oficina", str(_todas("101")))
revisar("T2 un departamento sigue en la principal", _todas("102") == ["principal"])
_p103 = _en("103", "principal")
revisar("T2 departamento con un terreno sin calle en la misma causa sigue con el departamento y su Observación",
        len(_p103) == 1 and _p103[0]["direccion"] == "calle Uno 100, departamento 5" and "no se informa" in _p103[0]["observaciones"], str(_p103))
revisar("T2 oficina con terreno sin calle va aparte solo con la oficina", _todas("104") == ["apartadas"] and _en("104", "apartadas")[0]["direccion"] == "Avenida Holanda 067, oficina 101")
revisar("T1 y T2 sin rol. El terreno desaparece y la oficina va aparte", r2["sin_rol"] == [] and any(x["rol"] == "" for x in r2["apartadas"]), str(r2["sin_rol"]))

r3 = F.aplicar([{"fecha": "2026-11-13", "sin_rol": [], "causas": [
    _c2("105", [("calle Uno 100, departamento 5", "calle"), ("Avenida Holanda 067, oficina 101", "calle")])]}],
    {_clave_causa("105", "2025", "1° Juzgado Civil de Santiago"): ["2026-11-12"]}, lambda t: "C.A. de Santiago")
revisar("T2 en Ya informadas la oficina de una causa mixta no se muestra",
        len(r3["ya_informadas"]) == 1 and r3["ya_informadas"][0]["direccion"] == "calle Uno 100, departamento 5", str(r3["ya_informadas"]))

print()
print("RESULTADO.", "TODO OK" if fallas == 0 else f"{fallas} FALLA(S)")
sys.exit(1 if fallas else 0)
