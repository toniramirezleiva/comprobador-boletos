# Comprovador de butlletes

App web gratuïta per comprovar butlletes d'Euromilions, La Primitiva, Bonoloto, El Gordo de la Primitiva, Loteria Nacional i cupons de l'ONCE a partir d'una foto. L'aplicació és en català.

- **Usarla:** https://toniramirezleiva.github.io/comprobador-boletos/
- Las fotos se leen en el propio dispositivo (reconocimiento de texto gratuito, Tesseract.js). Revisa siempre los números propuestos.
- Los boletos se guardan solo en el navegador de cada persona. No se envían a ningún servidor.
- `resultados.json` contiene los resultados oficiales de los sorteos y se actualiza automáticamente después de cada sorteo.

Los datos son orientativos. Para cobrar, la única lista válida es la oficial de Loterías y Apuestas del Estado o de la ONCE.

## Cómo se actualizan los resultados

Un proceso automático de GitHub Actions (`.github/workflows/resultados.yml`) consulta las fuentes oficiales (Loterías y Apuestas del Estado y ONCE) cada 5 minutos por la noche, después de los sorteos, y cada 15-20 minutos de madrugada y por la mañana. Cuando hay datos nuevos, actualiza `resultados.json`. No tiene ningún coste.
