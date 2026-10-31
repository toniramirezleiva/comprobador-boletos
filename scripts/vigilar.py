"""Vigilància: executa actualizar.py cada pocs minuts fins a l'hora de final i publica els canvis.

GitHub no garanteix les tasques programades freqüents (en salta moltes). Per això n'hi ha prou
que n'arrenqui una: aquesta es queda vigilant tota la franja dels sortejos.
Ús: python3 scripts/vigilar.py   (variables: FINS_UTC="00:30" | MINUTS=180, PAUSA=180)
"""
import datetime as dt, os, subprocess, sys, time

ara = lambda: dt.datetime.now(dt.timezone.utc)
pausa = int(os.environ.get("PAUSA", "180"))
fins = None
if os.environ.get("MINUTS"):
    fins = ara() + dt.timedelta(minutes=int(os.environ["MINUTS"]))
elif os.environ.get("FINS_UTC"):
    h, m = map(int, os.environ["FINS_UTC"].split(":"))
    fins = ara().replace(hour=h, minute=m, second=0, microsecond=0)
    if fins <= ara():
        fins += dt.timedelta(days=1)
    if fins - ara() > dt.timedelta(hours=5, minutes=40):  # límit de durada d'una tasca de GitHub (6 h)
        fins = ara() + dt.timedelta(hours=5, minutes=40)

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True)

def una_passada():
    r = subprocess.run([sys.executable, "scripts/actualizar.py"], capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[-400:], flush=True)
    if not sh("git", "status", "--porcelain", "resultados.json").stdout.strip():
        return
    canvis = [l.split("cambios: ")[1] for l in r.stdout.splitlines() if "cambios: " in l]
    sh("git", "add", "resultados.json")
    sh("git", "commit", "-m", "Resultados: " + (canvis[0] if canvis else "actualización"))
    for _ in range(3):
        sh("git", "pull", "--rebase", "origin", "main")
        if sh("git", "push", "origin", "main").returncode == 0:
            print("Publicat", flush=True); return
        time.sleep(10)
    print("No s'ha pogut publicar", flush=True)

una_passada()
while fins and ara() + dt.timedelta(seconds=pausa) < fins:
    time.sleep(pausa)
    una_passada()
print("Fi de la vigilància", ara().isoformat(), flush=True)
