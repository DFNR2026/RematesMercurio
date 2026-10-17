import json, sys, importlib, os
sys.path.insert(0, os.path.expanduser("~/vvtrabajo"))
from calculo import calcular, RAIZ
tanda = importlib.import_module(sys.argv[1]).T
D = RAIZ + "/banco_pruebas/2026-10-06/"
textos = json.load(open(os.path.expanduser("~/vvtrabajo/textos06.json"), encoding="utf-8"))
val = {x["n"]: x for x in json.load(open(D + "banco_validacion_2026-10-06.json", encoding="utf-8"))["avisos"]}
SALIDA = D + "banco_vale_vista_2026-10-06.json"
if os.path.exists(SALIDA):
    banco = json.load(open(SALIDA, encoding="utf-8"))
else:
    banco = {"edicion": "2026-10-06",
             "uso": "VALIDACIÓN de la parte 3.7a (regla del vale vista). Anotado por Claude el 2026-10-16 ANTES de escribir las instrucciones de la IA y el verificador. No se usa para ajustar nada.",
             "muestra": "Los 62 registros de banco_validacion_2026-10-06.json (muestra sorteada con semilla 20261015, numeración después de la parte 3.6b). Fecha y hora del remate tomadas de ese banco.",
             "reglas": {"dia_habil": "Provisorio lunes a viernes sin feriados (db/feriados_2026.csv). Pregunta 1.",
                        "horas_antes": "Horas de reloj desde la fecha y hora del remate. Si cae en fin de semana o feriado se adelanta al último día hábil, a las 14:00 supuestas (pregunta 3).",
                        "dia_anterior": "Si el día anterior no es hábil y el aviso no dice qué hacer, se usa el hábil anterior (pregunta 2).",
                        "vv_desde": "Si el aviso solo dice hasta cuándo, el desde es el día siguiente a la edición (pregunta 9).",
                        "vv_estado": "calculado (verde), revisar (ámbar, depende de las preguntas al abogado anotadas) o sin_dato.",
                        "ambiguo": "Redacción que admite dos lecturas. Se anota la más literal. La medición cuenta equivocado si el programa da la otra lectura en verde o ámbar.",
                        "trampa": "Frases del aviso que parecen plazo del vale vista pero son otra cosa (correo, devolución, firma del acta, pago)."},
             "avisos": []}
por_n = {a["n"]: a for a in banco["avisos"]}
fallas = []
for a in tanda:
    n = a["n"]; t = textos[str(n)]
    for c in [a.get("cita")] + a.get("citas_extra", []):
        if c and c not in t: fallas.append(f"{n} cita no encontrada: {c}")
    f, h = val[n]["fecha_remate"]["valor"], val[n]["hora_remate"]["valor"]
    if a.get("estado_esperado") in ("rojo", "no_se_mide"):
        desde = origen = hasta = None; estado = a["estado_esperado"]; preg = []
    else:
        desde, origen, hasta, estado, preg = calcular(a, f, h)
    reg = {"n": n, "fecha_remate": f, "hora_remate": h, **a,
           "vv_desde": desde, "vv_desde_origen": origen, "vv_hasta": hasta, "vv_estado": estado}
    if preg: reg["preguntas_abogado"] = preg
    por_n[n] = reg
if fallas:
    print("\n".join(fallas)); raise SystemExit("NO SE GUARDÓ NADA")
banco["avisos"] = [por_n[k] for k in sorted(por_n)]
json.dump(banco, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in banco["avisos"]:
    if r["n"] in {a["n"] for a in tanda}:
        print(r["n"], r["fecha_remate"], r["hora_remate"], r["regla"], "| desde", r["vv_desde"], "| hasta", r["vv_hasta"], "|", r["vv_estado"], r.get("preguntas_abogado", ""))
print("Registros en el banco", len(banco["avisos"]))
