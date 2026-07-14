# Gumli test suite

Testerna är grupperade efter ansvar så att ett fel blir lätt att lokalisera:

- `unit/` – modeller, JSON-repository, migreringar och historikretention.
- `components/` – Flet-komponenter och vylogik utan browser.
- `e2e/` – verkliga användarflöden i Chromium, inklusive persistens och responsivitet.
- `pwa/` – manifest, mallar, byggartefakter och kontraktet mellan de två repona.
- `support/` – delade fixtures, sökvägar och den MIME-korrekta lokala PWA-servern.

## Installera testberoenden

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m playwright install chromium
```

## Snabb svit

E2E-testerna upptäcks men hoppas över. Alla unit-, component- och PWA-tester körs:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

## Full svit med headless Chromium

```powershell
$env:GUMLI_RUN_E2E = "1"
$env:GUMLI_HEADLESS = "1"
.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

## Synliga GUI-tester

```powershell
$env:GUMLI_RUN_E2E = "1"
$env:GUMLI_HEADLESS = "0"
.venv\Scripts\python.exe -m unittest discover -s tests\e2e -t .
```

Sätt `GUMLI_DEPLOY_REPOSITORY` om deploy-repot inte ligger bredvid källkodsrepot.

## Tidtagen full svit

Kör varje logisk del en gång och skriv ut testantal och tid per grupp:

```powershell
.venv\Scripts\python.exe tests\run_timed.py
```
