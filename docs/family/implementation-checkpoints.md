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

## 5. Senare och statuslivscykel – Godkänd

Flytt, radering och automatisk aktivering sju dagar före deadline.

- [x] Versionsskyddad flytt mellan Aktuell och Senare.
- [x] Radering sätter status Raderad och behåller raden i Sheet.
- [x] Radering kräver en separat bekräftelse i appen.
- [x] Senare med deadline inom sju kalenderdagar, inklusive försenade uppgifter,
      flyttas till Aktuell med Automatik som senaste ändrare.
- [x] Samma automatregel körs före bootstrap och direkt efter redigering/statusbyte.
- [x] Repository-, komponent-, Apps Script- och GUI-tester täcker livscykeln.
- [x] Full regression: 386/386 tester godkända.
- [x] Produktionsprov verifierade flytt till Senare, radering med bekräftelse och
      bevarad Sheet-rad med status Raderad, rätt ändrare och ökande version.
- [x] Sjudagarsautomatiken verifierades live genom att sätta deadline 2026-07-29
      på en Senare-uppgift; nästa bootstrap flyttade den till Aktuell och visade
      Automatik som senaste ändrare.
- [x] Båda produktionsprovens rader rensades efter verifieringen; endast rubrikraden
      återstår i Uppgifter.
- [x] Apps Script version 9 använder samma produktionsadress och implementerings-id
      som tidigare.
- [x] GitHub Pages commit `bf751e0`, build `c13d41c5cb27621f`, är verifierad live.

Kontrollpunkt 5 är publicerad och produktionsverifierad 2026-07-22.

## 6. Slutförande och historik – lokalt godkänd

Faktisk utförare, serverstämplad sluttid och lat 14-dagars historik utan återställning.

- [x] Aktuell och Senare har en direkt, tillgänglig knapp för att markera en uppgift
      som klar.
- [x] Klienten skickar endast ID, Version och målet Klar; Apps Script härleder
      Slutförd av från enhetsnyckeln och sätter Slutförd från serverns klocka.
- [x] Slutförandet är låst och versionsskyddat och uppdaterar Senast ändrad av,
      Uppdaterad och Version.
- [x] Slutförd uppgift tas bort lokalt från Aktuell eller Senare efter lyckat svar.
- [x] Historik hämtas fortfarande först när Historik öppnas och ingår aldrig i bootstrap.
- [x] Endast poster från exakt de senaste 14 dygnen returneras; äldre Sheet-rader
      bevaras och skrivs inte om eller rensas.
- [x] Historik sorteras nyast slutförd först, visar faktisk utförare och sluttid och
      saknar återställningsåtgärd.
- [x] GUI-test verifierar skapa, direkt slutförande, tom Aktuell, Historikrad,
      utföraraudit och avsaknad av återställningsknapp.
- [x] Lokal GitHub Pages-build `4d278d6183e2fba8` används av GUI-regressionen.
- [x] Full regression: 394/394 tester godkända.

Kontrollpunkten är färdig lokalt men ännu inte publicerad till Apps Script eller
GitHub Pages.

## 7. Snabblistan – Väntar

Aktiva favoriter från Sheet och skapande av uppgift från favorit.

## 8. Slutpolish och pilot – Väntar

Offline, konflikter, säkerhet, prestanda, full regression och pilot på en andra telefon.
