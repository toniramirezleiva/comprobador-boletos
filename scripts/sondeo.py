"""Diagnóstico: descarga las respuestas de las fuentes oficiales y las guarda en debug/."""
import json, os, urllib.request, datetime
UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
hoy = datetime.date.today()
ini = (hoy - datetime.timedelta(days=3)).strftime("%Y%m%d"); fin = hoy.strftime("%Y%m%d")
urls = {}
for g in ["EMIL", "LAPR", "BONO", "ELGR", "LNAC"]:
    urls[g] = f"https://www.loteriasyapuestas.es/servicios/buscadorSorteos?game_id={g}&celebrados=true&fechaInicioInclusiva={ini}&fechaFinInclusiva={fin}"
urls["ONCE_html"] = "https://www.juegosonce.es/resultados-cupon-diario"
urls["ONCE_cuponazo_html"] = "https://www.juegosonce.es/resultados-cuponazo"
os.makedirs("debug", exist_ok=True)
estado = {}
for k, u in urls.items():
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "application/json, text/html;q=0.9, */*;q=0.8", "Accept-Language": "es-ES,es;q=0.9", "Referer": "https://www.loteriasyapuestas.es/es/resultados"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            estado[k] = {"url": u, "status": r.status, "bytes": len(body), "type": r.headers.get("content-type")}
            ext = "json" if "json" in (r.headers.get("content-type") or "") else "html"
            open(f"debug/{k}.{ext}", "wb").write(body[:400000])
    except Exception as e:
        estado[k] = {"url": u, "error": repr(e)[:300]}
estado["_hora"] = datetime.datetime.utcnow().isoformat() + "Z"
json.dump(estado, open("debug/estado.json", "w"), indent=1)
print(json.dumps(estado, indent=1))
