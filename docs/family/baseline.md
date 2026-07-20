# Familj – teknisk baslinje

Datum: 2026-07-20
Gren: `codex/family-tab`
Kodbas: `18d4d24 – Improve startup time`

## Fullständig testsvit

Kommando:

```powershell
.venv\Scripts\python.exe -u tests\run_timed.py
```

Godkänd baslinjekörning:

- Enhetstester: 62/62.
- Komponenttester: 86/86.
- PWA- och distributionstester: 62/62.
- GUI/E2E-tester: 70/70.
- Totalt: 280/280 på 468,996 sekunder.

Den första fullständiga körningen avbröts av en enstaka E2E-timeout när Python-arbetaren inte initierades inom 45 sekunder. Den berörda Checklistan-gruppen gick därefter 12/12 på 68,893 sekunder. En ny fullständig körning gick sedan 280/280 och utgör den godkända baslinjen.

## Uppstart

Mätverktyg:

```powershell
.venv\Scripts\python.exe -u -m tests.measure_startup --samples 3
```

Varje kall mätning använder en ny isolerad Chromium-kontext. Den varma mätningen är en omladdning i samma kontext. Medianen används som jämförelsevärde.

| Milstolpe | Kall median | Varm median |
|---|---:|---:|
| Flutter redo | 358,7 ms | 1 197,6 ms |
| Python startad | 3 981,0 ms | 4 157,5 ms |
| Tidigt appskal synligt | 3 995,6 ms | 4 176,8 ms |
| Lagring redo | 3 997,1 ms | 4 176,9 ms |
| Checklista synlig | 4 067,5 ms | 4 233,2 ms |

Kravet för Privat/Jobb efter Familj-ändringen är högst fem procents eller 200 ms försämring, beroende på vilket som är störst. För `checklist-visible` innebär det i denna miljö högst:

- Kall start: 4 270,9 ms.
- Varm omladdning: 4 444,9 ms.

Mätvärdena är miljöberoende. Eftermätningen ska därför använda samma verktyg, antal stickprov och lokala byggmiljö.

## Eftermätning efter tekniskt familjetest

Datum: 2026-07-20

Fullständig regressionskörning:

- Enhetstester: 67/67.
- Komponenttester: 93/93.
- PWA- och distributionstester: 79/79.
- GUI/E2E-tester: 70/70.
- Totalt: 309/309 på 491,734 sekunder.

| Milstolpe | Kall median | Förändring | Varm median | Förändring |
|---|---:|---:|---:|---:|
| Checklista synlig | 3 936,7 ms | −130,8 ms (−3,2 %) | 4 054,5 ms | −178,7 ms (−4,2 %) |

Både kall och varm Privat-start är snabbare än baslinjen i denna mätning. Kravet om högst fem procent eller 200 ms försämring är därmed uppfyllt.
