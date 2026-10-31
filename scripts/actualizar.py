"""Actualiza resultados.json con los resultados oficiales de los últimos días.

Fuentes:
- Loterías y Apuestas del Estado: /servicios/buscadorSorteos (Euromillones, Primitiva,
  Bonoloto, El Gordo y Lotería Nacional).
- ONCE: páginas de resultados de Cupón Diario, Cuponazo y Sueldazo Fin de Semana.

Uso: python3 scripts/actualizar.py [--offline DIR]
Con --offline lee las respuestas guardadas en DIR (pruebas) en lugar de descargarlas.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
TZ = dt.timezone(dt.timedelta(hours=1))
ARCHIVO = "resultados.json"
DIAS_ATRAS = 7
DIAS_GUARDADOS = 60

CAT_EM = ["5+2", "5+1", "5", "4+2", "4+1", "3+2", "4", "2+2", "3+1", "3", "1+2", "2+1", "2"]
CAT_PRI = ["especial", "1", "2", "3", "4", "5", "R"]
CAT_BON = ["1", "2", "3", "4", "5", "R"]
CAT_GOR = ["5+C", "5", "4+C", "4", "3+C", "3", "2+C", "2", "R"]
SELAE = {"EMIL": "euromillones", "LAPR": "primitiva", "BONO": "bonoloto", "ELGR": "elgordo", "LNAC": "loteria_nacional"}
# Jocs que es comproven (per ara, només Euromilions i Primitiva). Per afegir-ne: JOCS="EMIL,LAPR,BONO,ELGR,LNAC,ONCE"
JOCS = [j.strip() for j in os.environ.get("JOCS", "EMIL,LAPR").split(",") if j.strip()]
ONCE_PAGINAS = {
    "Cupón Diario": "https://www.juegosonce.es/resultados-cupon-diario",
    "Cuponazo": "https://www.juegosonce.es/resultados-cuponazo",
    "Sueldazo Fin de Semana": "https://www.juegosonce.es/resultados-sueldazo-fin-de-semana",
}
MESES = {m: i + 1 for i, m in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"])}
OFFLINE = sys.argv[sys.argv.index("--offline") + 1] if "--offline" in sys.argv else None
avisos = []


def descargar(url, clave):
    if OFFLINE:
        for ext in ("json", "html"):
            p = os.path.join(OFFLINE, f"{clave}.{ext}")
            if os.path.exists(p):
                return open(p, "rb").read().decode("utf-8", "replace")
        raise FileNotFoundError(clave)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
                                               "Accept-Language": "es-ES,es;q=0.9", "Referer": "https://www.loteriasyapuestas.es/es/resultados"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def euros(x):
    if x is None:
        return None
    s = str(x).strip().replace(".", "").replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return v


def nums(texto):
    return [int(n) for n in re.findall(r"\d+", texto or "")]


def premios_por_categoria(escrutinio, claves):
    out = {k: None for k in claves}
    for e in escrutinio or []:
        c = e.get("categoria")
        if not isinstance(c, int) or not 1 <= c <= len(claves):
            continue
        v = euros(e.get("premio"))
        out[claves[c - 1]] = v if v else None  # 0 = sin acertantes o bote
    return out


def base(juego, fecha, fuente):
    return {"id": f"{juego}_{fecha}", "juego": juego, "fecha": fecha, "titulo": "", "numeros": [], "estrellas": [],
            "complementario": None, "reintegro": None, "joker": None, "millon": None, "premios": {}, "premiosNumericos": [],
            "acumulables": True, "precioDecimo": None, "completo": False, "notas": "", "fuente": fuente,
            "actualizado": dt.datetime.now(TZ).isoformat(timespec="seconds")}


def convertir_selae(game, d):
    juego = SELAE[game]
    fecha = str(d.get("fecha_sorteo", ""))[:10]
    s = base(juego, fecha, "https://www.loteriasyapuestas.es/es/resultados")
    comb = d.get("combinacion") or ""
    esc = d.get("escrutinio") or []
    if game == "EMIL":
        n = nums(comb)
        if len(n) < 7:
            return None
        s["numeros"], s["estrellas"] = n[:5], n[5:7]
        s["premios"] = premios_por_categoria(esc, CAT_EM)
        s["millon"] = ((d.get("millon") or {}).get("combinacion") or "").replace(" ", "") or None
        s["completo"] = len(esc) >= 13
        s["titulo"] = f"Sorteo {d.get('numero', '')}"
        s["notas"] = "Importes por acertante en España." + ("" if s["premios"].get("5+2") else " 5+2: bote o sin acertantes.")
    elif game in ("LAPR", "BONO"):
        principal = re.split(r"[CR]\(", comb)[0]
        n = nums(principal)
        if len(n) < 6:
            return None
        s["numeros"] = n[:6]
        m = re.search(r"C\((\d+)\)", comb)
        s["complementario"] = int(m.group(1)) if m else None
        m = re.search(r"R\((\d+)\)", comb)
        s["reintegro"] = int(m.group(1)) if m else None
        claves = CAT_PRI if game == "LAPR" else CAT_BON
        s["premios"] = premios_por_categoria(esc, claves)
        if game == "LAPR":
            s["joker"] = ((d.get("joker") or {}).get("combinacion") or "").replace(" ", "") or None
        s["completo"] = len(esc) >= len(claves)
    elif game == "ELGR":
        principal = re.split(r"[CR]\(|CLAVE|Clave", comb)[0]
        n = nums(principal)
        if len(n) < 5:
            return None
        s["numeros"] = n[:5]
        m = re.search(r"(?:R|C|CLAVE|Clave)\s*\(?\s*(\d)", comb[len(principal) - 1:]) or re.search(r"[RC]\((\d)\)", comb)
        s["reintegro"] = int(m.group(1)) if m else None
        s["premios"] = premios_por_categoria(esc, CAT_GOR)
        s["completo"] = len(esc) >= 9
    elif game == "LNAC":
        return convertir_lnac(d, s)
    return s


def convertir_lnac(d, s):
    precio = float(d.get("precioDecimo") or 0) or None
    s["precioDecimo"] = precio
    s["titulo"] = str(d.get("nombre") or "").title()
    pn = []
    rein = [str(x.get("decimo")) for x in d.get("reintegros") or [] if x.get("decimo") is not None]
    term = []
    for campo, cifras in (("extraccionesDeCincoCifras", 5), ("extraccionesDeCuatroCifras", 4), ("extraccionesDeTresCifras", 3), ("extraccionesDeDosCifras", 2)):
        for x in d.get(campo) or []:
            v = str(x.get("decimo") or "")
            if v:
                term.append((f"Extracción de {cifras} cifras", v, (x.get("prize") or 0) / 100))

    def extra_de(num):
        # lo que ese número cobra además por terminaciones y reintegro
        t = sum(imp for _, v, imp in term if num.endswith(v) and len(v) < 5)
        if num[-1:] in rein and precio:
            t += precio
        return t

    for campo, nombre in (("premioEspecial", "Premio especial"), ("primerPremio", "Primer premio"), ("segundoPremio", "Segundo premio")):
        x = d.get(campo) or {}
        num = str(x.get("decimo") or x.get("numero") or "")
        if len(num) == 5 and x.get("prize"):
            total = x["prize"] / 100
            # el importe oficial ya incluye lo que el número cobra por otras vías: se descuenta para no sumarlo dos veces
            pn.append({"concepto": nombre, "tipo": "exacto", "valor": num, "serie": None, "importe": round(max(0, total - extra_de(num)), 2)})
    for campo, nombre in (("tercerosPremios", "Tercer premio"), ("cuartosPremios", "Cuarto premio"), ("quintosPremios", "Quinto premio")):
        for x in d.get(campo) or []:
            num = str(x.get("decimo") or "")
            if len(num) == 5 and x.get("prize"):
                pn.append({"concepto": nombre, "tipo": "exacto", "valor": num, "serie": None, "importe": round(max(0, x["prize"] / 100 - extra_de(num)), 2)})
    for concepto, v, imp in term:
        pn.append({"concepto": concepto, "tipo": "exacto" if len(v) == 5 else "terminacion", "valor": v, "serie": None, "importe": imp})
    for r in rein:
        pn.append({"concepto": "Reintegro", "tipo": "terminacion", "valor": r, "serie": None, "importe": precio})
    s["premiosNumericos"] = pn
    s["acumulables"] = True
    jueves = (d.get("tipoSorteo") or "") == "J"
    s["completo"] = bool(pn) and jueves
    url = d.get("urlListadoOficial")
    if url:
        s["fuente"] = "https://www.loteriasyapuestas.es" + url.replace(" ", "%20")
    if not jueves:
        s["notas"] = "Puede haber premios (aproximaciones, centenas, terminaciones) que no figuran aquí: consulta la lista oficial."
    return s


def convertir_once(producto, texto_html):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", texto_html, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    m = re.search(r"[ÚU]ltimo sorteo celebrado el \w+, (\d{1,2}) de (\w+) de (\d{4})", t)
    if not m:
        return None
    fecha = dt.date(int(m.group(3)), MESES[m.group(2).lower()], int(m.group(1))).isoformat()
    m2 = re.search(r"N[úu]mero: (\d{5}), serie: (\d{1,3})", t)
    if not m2:
        return None
    numero, serie = m2.group(1), int(m2.group(2))
    s = base("once", fecha, ONCE_PAGINAS[producto])
    s["titulo"] = producto
    s["acumulables"] = False
    i = t.find("Premios de")
    j = t.find("no son acumulables", i)
    bloque = re.sub(r"\s+", " ", t[i:j if j > 0 else i + 6000])
    # números adicionales (Sueldazo): pares "NNNNN ... Serie NNN" entre el resultado y la tabla
    cab = re.sub(r"\s+", " ", t[m.start():i if i > 0 else m.start() + 3000])
    adicionales = [(n, int(se)) for n, se in re.findall(r"\b(\d{5})\b\D{0,40}?[Ss]erie:?\s*(\d{3})\b", cab) if n != numero]
    adicionales = list(dict.fromkeys(adicionales))
    pn, raros = [], []
    for trozo in re.split(r"(?=\b[\d.]+ premios? de )", bloque):
        mm = re.match(r"([\d.]+) premios? de (.+?) a (?:las|la) (.+?)\.(?:\s|$)", trozo.strip() + " ")
        if not mm:
            continue
        imp, desc = mm.group(2).strip(), mm.group(3).strip().lower()
        mi = re.search(r"([\d.]+(?:,\d+)?) ?€", imp)
        importe = euros(mi.group(1)) if mi else None
        extra = "" if re.fullmatch(r"[\d.,]+ ?€", imp) else f" ({imp})"
        if re.search(r"adicional|extracci[oó]n", desc):
            for (n2, se2) in adicionales:
                pn.append({"concepto": ("5 cifras y serie" if "serie" in desc else "5 cifras") + " (número adicional)" + extra, "tipo": "exacto", "valor": n2, "serie": se2 if "serie" in desc else None, "importe": importe})
            if not adicionales:
                raros.append(f"{desc}: {imp}")
            continue
        m3 = re.match(r"(\d) (primeras|últimas) cifras", desc) or re.match(r"(primera|última) cifra", desc)
        if desc.startswith("5 cifras y serie"):
            pn.append({"concepto": "5 cifras y serie" + extra, "tipo": "exacto", "valor": numero, "serie": serie, "importe": importe})
        elif desc.startswith("5 cifras"):
            pn.append({"concepto": "5 cifras" + extra, "tipo": "exacto", "valor": numero, "serie": None, "importe": importe})
        elif m3 and m3.group(1).isdigit():
            k = int(m3.group(1))
            ini = m3.group(2) == "primeras"
            pn.append({"concepto": f"{k} {m3.group(2)} cifras", "tipo": "inicio" if ini else "terminacion", "valor": numero[:k] if ini else numero[-k:], "serie": None, "importe": importe})
        elif m3:
            ini = m3.group(1) == "primera"
            pn.append({"concepto": f"{m3.group(1).capitalize()} cifra", "tipo": "inicio" if ini else "terminacion", "valor": numero[:1] if ini else numero[-1:], "serie": None, "importe": importe})
        else:
            raros.append(f"{desc}: {imp}")
    s["premiosNumericos"] = pn
    s["completo"] = bool(pn) and not raros
    ad = ", ".join(f"{n} serie {se:03d}" for n, se in adicionales)
    s["notas"] = f"Número {numero}, serie {serie:03d}." + (f" Números adicionales: {ad}." if ad else "") + " En un mismo cupón no se acumulan premios." + (" Premios no incluidos: " + "; ".join(raros) if raros else "")
    return s


def fusionar(viejo, nuevo):
    """Nunca sustituye un importe conocido por null."""
    if not viejo:
        return nuevo
    for k, v in (viejo.get("premios") or {}).items():
        if v is not None and nuevo["premios"].get(k) is None:
            nuevo["premios"][k] = v
    if viejo.get("completo") and not nuevo.get("completo") and not nuevo.get("premiosNumericos") and not nuevo.get("numeros"):
        return viejo
    return nuevo


def igual(a, b):
    quita = lambda x: {k: v for k, v in (x or {}).items() if k != "actualizado"}
    return quita(a) == quita(b)


def main():
    hoy = dt.datetime.now(TZ).date()
    ini = (hoy - dt.timedelta(days=DIAS_ATRAS)).strftime("%Y%m%d")
    fin = hoy.strftime("%Y%m%d")
    nuevos = []
    for game in [g for g in SELAE if g in JOCS]:
        url = f"https://www.loteriasyapuestas.es/servicios/buscadorSorteos?game_id={game}&celebrados=true&fechaInicioInclusiva={ini}&fechaFinInclusiva={fin}"
        try:
            datos = json.loads(descargar(url, game))
        except Exception as e:
            avisos.append(f"{game}: {e!r}"[:200]); continue
        if not isinstance(datos, list):
            continue  # sin sorteos en el intervalo
        for d in datos:
            try:
                s = convertir_selae(game, d)
                if s and re.match(r"\d{4}-\d{2}-\d{2}$", s["fecha"]):
                    nuevos.append(s)
            except Exception as e:
                avisos.append(f"{game} {d.get('fecha_sorteo')}: {e!r}"[:200])
    for prod, url in (ONCE_PAGINAS.items() if "ONCE" in JOCS else []):
        clave = {"Cupón Diario": "ONCE_html", "Cuponazo": "ONCE_cuponazo_html", "Sueldazo Fin de Semana": "ONCE_sueldazo_html"}[prod]
        try:
            s = convertir_once(prod, descargar(url, clave))
            if s:
                nuevos.append(s)
        except Exception as e:
            avisos.append(f"ONCE {prod}: {e!r}"[:200])

    actual = json.load(open(ARCHIVO, encoding="utf-8")) if os.path.exists(ARCHIVO) else {"sorteos": []}
    por_id = {s["id"]: s for s in actual.get("sorteos", []) if s.get("id")}
    cambios = []
    for s in nuevos:
        viejo = por_id.get(s["id"])
        s = fusionar(viejo, s)
        if not igual(viejo, s):
            por_id[s["id"]] = s
            cambios.append(s["id"])
    limite = (hoy - dt.timedelta(days=DIAS_GUARDADOS)).isoformat()
    lista = sorted((s for s in por_id.values() if s.get("fecha", "") >= limite), key=lambda s: (s["fecha"], s["id"]), reverse=True)
    for a in avisos:
        print("AVISO:", a)
    print("Sorteos leídos:", len(nuevos), "| cambios:", cambios or "ninguno")
    if cambios:
        json.dump({"actualizado": dt.datetime.now(TZ).isoformat(timespec="seconds"), "sorteos": lista}, open(ARCHIVO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"cambios={' '.join(cambios)}\n")


if __name__ == "__main__":
    main()
