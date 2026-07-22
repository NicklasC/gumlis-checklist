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
- Produktionsbladen, Apps Script version 8 och beständig anslutning som Nicklas är verifierade.

## 3. Aktuell-lista och synkning – Godkänd

Cache, synkstatus, Mina/Alla-filter, kompakt mobilrad och deadlineindikering.

### 3A. Aktuell-listans skrivskyddade grund – Godkänd

- [x] Separat Familj-bootstrap-cache i IndexedDB.
- [x] Aktuell-lista visas efter lyckad anslutning.
- [x] Synkstatus visar laddning, synkad data, cache/offline och fel utan cache.
- [x] Alla/Mina-filter med räknare.
- [x] Kompakt rad med ansvarig, deadline och röd förseningsindikering.
- [x] Sortering enligt deadline- och skapandetidsreglerna.
- [x] Giltig cache återställs utan nätverksanrop; trasig cache ignoreras.
- [x] Enhets-, komponent- och GUI-regression godkända lokalt.

Kontrollpunkt 3 är verifiererad både lokalt och mot produktionsarket. Tomma
checkboxrader i Sheet ignoreras och ger inte längre falska radfel.

### 3B. Familjens läs-only-nedernavigation – Godkänd

- [x] `listLater` och `listHistory` har separata autentiserade repositoryanrop.
- [x] Apps Script filtrerar Historik till de senaste 14 dagarna utan att läsa en historikflik.
- [x] Familjens Checklista, Snabblistan, Historik och Senare använder separata vyer.
- [x] Familjens Historik saknar återställningsåtgärd.
- [x] GUI-regressionen verifierar navigation genom alla fyra familjesidorna.

Skrivoperationer och skapande från Snabblistan hör till kontrollpunkt 4 och 7.

## 4. Skapa och redigera – Godkänd

- [x] Uppgift skapas med klientgenererat stabilt ID och serverhärledd medlem.
- [x] Titel, ansvarig och valfri deadline kan anges och ändras.
- [x] Alla är standardansvarig.
- [x] Tilldelad av ändras bara när ansvarig ändras.
- [x] Skapad av, Tilldelad av och Senast ändrad av visas vid redigering.
- [x] Skrivningar är låsta, skapande är idempotent och gammal version ger konflikt.
- [x] Konflikt laddar serverns senaste rad och skriver aldrig över den tyst.
- [x] Aktuell och Senare uppdateras lokalt efter lyckad skrivning.
- [x] GUI-test verifierar skapa, deadline, auditinformation och redigering.
- [x] Sen familjeanslutning kan inte längre skriva över en senare Privat/Jobb-navigation.
- [x] Produktionsprov skapades och redigerades via PWA:n, bekräftades som version 2 i
      Sheet och rensades därefter utan kvarlämnad testdata.
- [x] Apps Script version 8 använder samma produktionsadress som tidigare.
- [x] GitHub Pages commit `ebb693d`, build `1efae37b70aa3571`, är verifierad live.
- [x] Full regression: 380/380 tester godkända.

Kontrollpunkt 4 är publicerad och produktionsverifierad 2026-07-22.

## 5. Senare och statuslivscykel – Väntar

Flytt, radering och automatisk aktivering sju dagar före deadline.

## 6. Slutförande och historik – Väntar

Faktisk utförare, serverstämplad sluttid och lat 14-dagars historik utan återställning.

## 7. Snabblistan – Väntar

Aktiva favoriter från Sheet och skapande av uppgift från favorit.

## 8. Slutpolish och pilot – Väntar

Offline, konflikter, säkerhet, prestanda, full regression och pilot på en andra telefon.
