# Familj – aktuella implementationskontrollpunkter

Detta dokument ersätter den äldre draftens åtta steg. Definition of Ready är fortsatt
produktens sanningskälla; kontrollpunkterna styr endast genomförandeordningen.

## 1. Säker anslutning och beständig identitet – Godkänd

Separat servicekonto, unik enhetsnyckel, lazy Familj-start och beständig Android-PWA-
anslutning är verifierade och publicerade.

## 2. Modeller och skrivskyddat bootstrap-API – Godkänd

- Svenska radvärden valideras i separata familjemodeller.
- `bootstrap` returnerar Aktuell, medlemmar och favoriter men inte historik eller raderat.
- `listLater` hålls separat.
- Felaktiga Sheet-rader isoleras utan att blockera giltiga rader.
- Alla API-svar följer ett stabilt svarskuvert.
- Produktionsbladen, Apps Script version 5 och beständig anslutning som Nicklas är verifierade.

## 3. Aktuell-lista och synkning – lokalt godkänd

Cache, synkstatus, Mina/Alla-filter, kompakt mobilrad och deadlineindikering.

### 3A. Aktuell-listans skrivskyddade grund – lokalt godkänd

- [x] Separat Familj-bootstrap-cache i IndexedDB.
- [x] Aktuell-lista visas efter lyckad anslutning.
- [x] Synkstatus visar laddning, synkad data, cache/offline och fel utan cache.
- [x] Alla/Mina-filter med räknare.
- [x] Kompakt rad med ansvarig, deadline och röd förseningsindikering.
- [x] Sortering enligt deadline- och skapandetidsreglerna.
- [x] Giltig cache återställs utan nätverksanrop; trasig cache ignoreras.
- [x] Enhets-, komponent- och GUI-regression godkända lokalt.

Kontrollpunkt 3 är verifierad lokalt tillsammans med cache- och offline-felstater.

### 3B. Familjens läs-only-nedernavigation – lokalt godkänd

- [x] `listLater` och `listHistory` har separata autentiserade repositoryanrop.
- [x] Apps Script filtrerar Historik till de senaste 14 dagarna utan att läsa en historikflik.
- [x] Familjens Checklista, Snabblistan, Historik och Senare använder separata vyer.
- [x] Familjens Historik saknar återställningsåtgärd.
- [x] GUI-regressionen verifierar navigation genom alla fyra familjesidorna.

Skrivoperationer och skapande från Snabblistan hör till kontrollpunkt 4 och 7.

## 4. Skapa och redigera – lokalt godkänd

- [x] Uppgift skapas med klientgenererat stabilt ID och serverhärledd medlem.
- [x] Titel, ansvarig och valfri deadline kan anges och ändras.
- [x] Alla är standardansvarig.
- [x] Tilldelad av ändras bara när ansvarig ändras.
- [x] Skapad av, Tilldelad av och Senast ändrad av visas vid redigering.
- [x] Skrivningar är låsta, skapande är idempotent och gammal version ger konflikt.
- [x] Konflikt laddar serverns senaste rad och skriver aldrig över den tyst.
- [x] Aktuell och Senare uppdateras lokalt efter lyckad skrivning.
- [x] GUI-test verifierar skapa, deadline, auditinformation och redigering.

Kontrollpunkten är inte publicerad mot produktions-Apps Script eller GitHub Pages än.

## 5. Senare och statuslivscykel – Väntar

Flytt, radering och automatisk aktivering sju dagar före deadline.

## 6. Slutförande och historik – Väntar

Faktisk utförare, serverstämplad sluttid och lat 14-dagars historik utan återställning.

## 7. Snabblistan – Väntar

Aktiva favoriter från Sheet och skapande av uppgift från favorit.

## 8. Slutpolish och pilot – Väntar

Offline, konflikter, säkerhet, prestanda, full regression och pilot på en andra telefon.
