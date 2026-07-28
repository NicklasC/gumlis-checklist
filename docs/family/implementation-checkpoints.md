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

## 6. Slutförande och historik – Godkänd

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
- [x] Produktionsprov skapades och slutfördes via PWA:n. Sheet-raden verifierades
      med status Klar, Slutförd av Nicklas, serverstämplad sluttid, Senast ändrad
      av Nicklas och Version 2.
- [x] Samma produktionsprov visades i Historik med faktisk utförare och utan
      slutförande- eller återställningsåtgärd; testraden rensades därefter.
- [x] Apps Script version 10 använder samma produktionsadress och implementerings-id
      som tidigare.
- [x] GitHub Pages commit `eb228ba`, build `4d278d6183e2fba8`, är verifierad live.
- [x] Full regression: 394/394 tester godkända.

Kontrollpunkt 6 är publicerad och produktionsverifierad 2026-07-22.

## 7. Snabblistan – Godkänd

Aktiva favoriter från Sheet och skapande av uppgift från favorit.

- [x] Endast aktiva favoriter visas och sorteras enligt Sortering i Favoriter-bladet.
- [x] Favoritraderna är kompakta, mobilanpassade och har tydliga tillgänglighetsnamn.
- [x] Ett tryck skapar direkt en Aktuell-uppgift med Ansvarig Alla och utan deadline.
- [x] Skapad av, Tilldelad av och Senast ändrad av härleds fortfarande av servern
      från enhetsnyckeln genom den befintliga `createTask`-operationen.
- [x] Dubbeltryck blockeras medan skrivningen pågår och ett misslyckat återförsök
      återanvänder samma klientgenererade ID.
- [x] Lyckat skapande uppdaterar Aktuell och familjens bootstrap-cache direkt.
- [x] Bekräftelsen Tillagd för Alla har åtgärden Redigera som öppnar samma editor
      som en vanlig familjeuppgift.
- [x] Komponent-, Apps Script-kontrakts- och GUI-tester täcker favoritflödet.
- [x] GitHub Pages commit `f697585`, build `29eeee038ba4b267`, är verifierad live.
- [x] Full regression: 399/399 tester godkända.
- [x] Produktionsprovet skapade favoritens uppgift som Aktuell för Alla utan deadline.
- [x] Bekräftelsen och Redigera-flödet verifierades i den publicerade PWA:n.
- [x] Produktionsarket registrerade Skapad av, Tilldelad av och Senast ändrad av
      som Nicklas samt Version 1; den exakta testraden rensades efter kontrollen.
- [x] Efter ny synkning var både arket och appens Aktuell-lista åter tomma.
- [x] Webbläsarens fellogg var tom under produktionsprovet.

Kontrollpunkt 7 är publicerad och produktionsverifierad 2026-07-22. Ingen ny
Apps Script-operation eller distribution krävdes; befintlig version 10 och
`createTask`-operation användes.

## 8. Slutpolish och pilot – Tekniskt implementerad, slutverifiering väntar

### Implementerat

- [x] Sparad bootstrap visas vid nätverksfel med texten `Offline – visar sparad data`.
- [x] Skapa, redigera, slutföra, flytta, radera och skapa från Snabblistan
      blockeras offline; inga skrivningar köas.
- [x] `Försök igen` synkar om vyn och återaktiverar skrivning efter lyckat svar.
- [x] Spärrad enhetsnyckel rensar familjecachen och visar inget gammalt familjeinnehåll.
- [x] `Koppla från Familj` rensar både anslutning och familjecache på enheten.
- [x] Redigeringsdialogen kan avbrytas efter ett offlinefel men kan inte skicka fler
      skrivningar förrän vyn har synkats igen.
- [x] Raderingsbekräftelsen ligger kvar tills den asynkrona serveråtgärden är klar.
- [x] Aktuell-listan hanterar 50 uppgifter vid 320, 390 och 412 pixlars bredd utan
      horisontell sidöverskridning.
- [x] Privat/Jobb-starten skapar fortfarande inget familjerepository och gör inget
      familjeanrop.
- [x] Bygget rensar Python-bytecode och `__pycache__` före paketering. Slutarkivet
      är 37 092 byte och innehåller 32 filer utan cache- eller bytecodefiler.
- [x] Samtida A/B-mätning mot föregående publicerade build gav 5,93 s mot 6,09 s
      för varm start, en skillnad på 158 ms (2,7 procent), vilket är inom kravet.
      Kallstarten blev samtidigt tydligt snabbare genom det mindre apparkivet.
- [x] Spårade filer i käll- och Pages-repository samt det byggda apparkivet har
      kontrollerats efter privata nycklar, vanliga API-tokenformat och känsliga filnamn.
      Enda textträffen är ett test som uttryckligen kontrollerar att
      `BEGIN PRIVATE KEY` saknas.
- [x] Säkerhetsgranskningen identifierade och den lokala koden stängde de publika
      editorfunktionerna samt band PWA-bryggan med en 256-bitars engångs-nonce,
      strikt Google-sandbox-origin och exakt kommunikationsfönster.
- [x] Timeoutad handshake återställs; ett sent ready-svar kan inte längre skicka
      ett anrop efter att användaren har fått `TIMEOUT`.
- [x] Fem isolerade Chromium-angrepp verifierar fel nonce, fel fönster, tidigare
      för bred Google-origin, inbäddad Gumli, samtidiga väntande anrop och sent
      ready-svar med säkert återförsök.
- [ ] Produktionsversion 10 behålls endast tills ett samordnat säkerhetssläpp med
      nytt Apps Script deployment-ID och motsvarande PWA-adress kan verifieras.

### Verifieringsläge

- [x] Berörda enhets- och komponenttester är godkända.
- [x] Riktade GUI-tester för skapa/redigera/slutföra samt offline/cache/återförsök
      är godkända mot den rena byggnaden före den avgränsade raderingsfixen.
- [x] Navigationsgruppen gav 15 av 16 godkända tester och identifierade den
      intermittenta dialoglivscykeln vid radering; den bakomliggande ordningen är korrigerad.
- [ ] Kör raderingsflödet upprepat mot slutbyggnaden.
- [x] Hela sviten är godkänd med 424 av 424 tester.
- [ ] Publicera och verifiera lokal slutbuild `23591048ffaf3d08` live tillsammans
      med den nya Apps Script-deploymenten.
- [ ] Verifiera den verkliga Google-sandbox-originen och att en avsiktligt felaktig
      testnyckel ger `UNAUTHORIZED` genom den nya produktionsbryggan.
- [ ] Bekräfta att anslutna telefoner har hämtat den nya PWA:n och stäng därefter
      den gamla sårbara Apps Script-deploymenten.

### Nicklas mobilpilot

- [ ] Uppdatera Gumli på Nicklas telefon och kontrollera normal Privat/Jobb-start.
- [ ] Installera Gumli på en andra Androidtelefon i Chrome.
- [ ] Anslut med just den telefonens personliga enhetsnyckel och kontrollera rätt medlem.
- [ ] Stäng appen, starta om Chrome/PWA och kontrollera att anslutningen ligger kvar.
- [ ] Kontrollera sparad familjelista offline och lyckad `Försök igen` online.
- [ ] Skapa, redigera, slutför och radera en provuppgift på den andra telefonen.
- [ ] Rulla därefter ut till alla fyra telefonerna och godkänn slutpiloten.

Kontrollpunkt 8 får inte markeras Godkänd förrän den automatiska
slutverifieringen, livekontrollen och minst en andra verklig Androidtelefon är godkända.
