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
- Produktionsbladen, Apps Script version 4 och beständig anslutning som Nicklas är verifierade.

## 3. Aktuell-lista och synkning – Pågår

Cache, synkstatus, Mina/Alla-filter, kompakt mobilrad och deadlineindikering.

## 4. Skapa och redigera – Väntar

Titel, ansvarig, deadline, Tilldelad av, Senast ändrad av och versionskontroll.

## 5. Senare och statuslivscykel – Väntar

Flytt, radering och automatisk aktivering sju dagar före deadline.

## 6. Slutförande och historik – Väntar

Faktisk utförare, serverstämplad sluttid och lat 14-dagars historik utan återställning.

## 7. Snabblistan – Väntar

Aktiva favoriter från Sheet och skapande av uppgift från favorit.

## 8. Slutpolish och pilot – Väntar

Offline, konflikter, säkerhet, prestanda, full regression och pilot på en andra telefon.
