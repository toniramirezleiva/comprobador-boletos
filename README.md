# Comprovador de butlletes

App web gratuïta per comprovar butlletes d'Euromilions, La Primitiva, Bonoloto, El Gordo de la Primitiva, Loteria Nacional i cupons de l'ONCE a partir d'una foto. L'aplicació és en català.

- **Usarla:** https://toniramirezleiva.github.io/comprobador-boletos/
- Las fotos se leen en el propio dispositivo (reconocimiento de texto gratuito, Tesseract.js). Revisa siempre los números propuestos.
- Los boletos se guardan solo en el navegador de cada persona. No se envían a ningún servidor.
- `resultados.json` contiene los resultados oficiales de los sorteos y se actualiza automáticamente después de cada sorteo.

Los datos son orientativos. Para cobrar, la única lista válida es la oficial de Loterías y Apuestas del Estado o de la ONCE.

## Com s'actualitzen els resultats

Un procés automàtic de GitHub Actions (`.github/workflows/resultados.yml`) consulta les fonts oficials de Loterías y Apuestas del Estado. Es comproven l'**Euromilions dels divendres**, la **Primitiva dels dissabtes** i els **sortejos extraordinaris de l'ONCE** (11 de l'11, Nadal): aquelles nits el procés vigila fins a la 1:40 i consulta cada 3 minuts, i el matí següent fa unes quantes passades més per als escrutinis endarrerits. Per afegir-hi altres jocs, cal ampliar la variable `JOCS` del flux. No té cap cost.
