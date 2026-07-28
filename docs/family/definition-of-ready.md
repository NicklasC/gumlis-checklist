# Familj i Gumli – Definition of Ready

Status: Godkänd – implementation påbörjad
Planeringsdatum: 2026-07-19
Godkänd av Nicklas: 2026-07-20
Kodbasens baslinje: 18d4d24 – Improve startup time

Detta dokument är den aktuella sanningskällan för Familj version 1. Äldre briefs, planer, uppgiftslistor och mockuper är historiskt underlag och får inte användas som bindande krav om de motsäger detta dokument.

Ingen implementation får påbörjas innan dokumentet är uttryckligen godkänt.

## 1. Mål

Familj ska vara ett tredje huvudläge bredvid Privat och Jobb. Familjemedlemmarna ska kunna hantera en gemensam uppgiftslista från varsin installerad Android-PWA, medan Nicklas kan administrera samma data direkt i ett privat Google Sheet.

Familj får ta längre tid att öppna än Privat och Jobb. Familj får däremot inte försämra normal uppstart för Privat eller Jobb.

## 2. Prioriteringar

Prioriteringsordningen är:

1. Privat och Jobb ska fortsätta starta snabbt och fungera som idag.
2. Familjedata och hemligheter får inte publiceras i GitHub.
3. Familjelistan ska vara enkel att använda från telefon.
4. Google Sheet ska vara begripligt och fullt administrerbart för Nicklas.
5. Ändringar ska kunna kopplas till rätt familjemedlem.
6. Familjehistoriken ska bevaras för framtida analys.
7. Lösningen ska vara robust vid långsam eller saknad uppkoppling.

## 3. Uttryckliga avgränsningar

Följande ingår inte i version 1:

- Bakgrundsnotiser eller pushnotiser.
- Offlinekö för ändringar.
- Flera hushåll.
- Externa användare.
- Fullständig ändringslogg med alla tidigare fältvärden.
- Analysverktyg eller diagram.
- Automatisk rensning av familjehistorik.
- Avancerad hantering av borttagna familjemedlemmar.

## 4. Befintligt beteende som ska bevaras

- Privat och Jobb använder lokal klientlagring.
- Privat och Jobb delar befintlig huvudchecklista men filtreras efter läge.
- Privat och Jobb har Historik och Senare.
- Privat och Jobb raderar lokal historik som är äldre än 14 dagar.
- Privat och Jobb behåller sin befintliga möjlighet att återställa från Historik.
- Sekundära vyer skapas först när användaren navigerar till dem.
- Den nuvarande PWA-bygg- och service worker-strukturen ska fortsätta fungera.

Familj ska byggas separat och får inte tvingas in i den befintliga lokala repositorymodellen.

## 5. Familjemedlemmar och identitet

Den fullständiga medlemslistan i version 1 är:

- Nicklas
- Ida
- Thor
- Johanna

Alla är ett tilldelningsalternativ, inte en familjemedlem.

Varje installerad PWA kopplas till exakt en familjemedlem. En person kan tekniskt ha flera enheter, men målmiljön är en telefon per person.

Enhetens identitet används för:

- Skapad av.
- Tilldelad av.
- Senast ändrad av.
- Slutförd av.

Alla familjemedlemmar har samma rättigheter i appen.

## 6. Behörigheter

Alla fyra familjemedlemmar får:

- Se alla familjeuppgifter.
- Skapa uppgifter.
- Ändra titel.
- Ändra ansvarig.
- Ändra eller ta bort deadline.
- Flytta uppgifter till och från Senare.
- Markera valfri uppgift som klar.
- Radera uppgifter.

Varje ändring måste registreras på enhetens valda identitet.

Behörigheterna är familjeregler och skydd mot vanliga misstag. Identiteten bestäms på servern från en unik enhetsnyckel och får inte skickas som ett valbart medlemsnamn i API-anropet.

## 7. Huvudnavigering

Huvudlägen:

- Privat
- Jobb
- Familj

Familj har samma fyra nederdestinationer som övriga lägen:

1. Checklista
2. Snabblistan
3. Historik
4. Senare

Familjevyernas data och nätverkslager skapas först när Familj används.

## 8. Uppgiftens informationsmodell

Varje familjeuppgift innehåller minst:

- ID
- Uppgift
- Status
- Ansvarig
- Tilldelad av
- Tilldelad
- Skapad av
- Skapad
- Deadline
- Senast ändrad av
- Uppdaterad
- Slutförd av
- Slutförd
- Version

### Skapad av

Personen som skapade uppgiften. Värdet förändras aldrig.

### Ansvarig

Nuvarande ansvarig:

- Alla
- Nicklas
- Ida
- Thor
- Johanna

Alla är standardvalet.

### Tilldelad av

Personen som satte nuvarande ansvarig.

- Vid skapande blir Tilldelad av samma person som Skapad av.
- När ansvarig ändras blir Tilldelad av personen som gjorde ändringen.
- Fältet förändras inte av titeländring, deadlineändring, flytt, slutförande eller automatik.

Detta gör att en omfördelning aldrig döljs av ett senare slutförande.

### Senast ändrad av

Personen eller processen som senast ändrade uppgiften.

Tillåtna värden är familjemedlemmarnas namn samt:

- Automatik
- Nicklas (Sheet)

Senast ändrad av uppdateras vid titeländring, ansvarigändring, deadlineändring, statusändring, flytt, slutförande, radering och administrativ återaktivering.

### Slutförd av

Personen som faktiskt markerade uppgiften som klar. Slutförd av behöver inte vara samma person som Ansvarig.

## 9. Google Sheet

Google Sheet ägs av Nicklas Googlekonto. Samma konto äger Apps Script. Endast Nicklas redigerar Sheet manuellt.

Sheet och Apps Script är privata. Övriga familjemedlemmar använder endast Gumli. Ett separat Gumli-servicekonto får redigeringsåtkomst till just familjearket och används av Apps Script för Google Sheets API.

### Fil och placering

Familjens befintliga Google Sheets-fil används som auktoritativ datakälla:

- Filnamn: `gumlis-checklist-familj`.
- Privat placering i Google Drive: `AI/gumlis-checklist/gumlis-checklist-familj`.

Ingen alternativ produktionsfil ska skapas utan ett nytt uttryckligt beslut. Genomförbarhetstestet får inte blanda provdata med familjens riktiga uppgifter eller historik.

### Blad: Uppgifter

Rekommenderad kolumnordning:

1. Uppgift
2. Status
3. Ansvarig
4. Tilldelad av
5. Tilldelad
6. Skapad av
7. Skapad
8. Deadline
9. Senast ändrad av
10. Uppdaterad
11. Slutförd av
12. Slutförd
13. ID
14. Version

De tekniska kolumnerna ID och Version placeras längst till höger och markeras visuellt som tekniska, men förblir synliga.

Tillåtna statusvärden:

- Aktuell
- Senare
- Klar
- Raderad

Tillåtna personvärden:

- Nicklas
- Ida
- Thor
- Johanna

Ansvarig tillåter dessutom Alla.

Rubrikraden skyddas. Status-, person- och datumkolumner får datavalidering.

### Blad: Medlemmar

Minst följande kolumner:

- Namn
- Aktiv
- Sortering

Medlemmarna lagras med sina läsbara namn. Ingen rollkolumn behövs.

### Blad: Favoriter

Minst följande kolumner:

- Uppgift
- Aktiv
- Sortering
- ID

Nicklas ska kunna lägga till, ändra, sortera och inaktivera favoriter direkt i Sheet.

### Ingen Ändringslogg i version 1

Ett separat append-only-blad för varje fältändring ingår inte. Spårbarheten i version 1 bygger på Skapad av, Tilldelad av, Senast ändrad av och Slutförd av.

## 10. Manuell Sheet-redigering

Sheet är en auktoritativ datakälla. Giltiga manuella ändringar ska synas i appen vid nästa synkning.

Ett redigeringsflöde i Apps Script ska:

- Uppdatera Uppdaterad.
- Höja Version.
- Sätta Senast ändrad av till Nicklas (Sheet).
- Uppdatera Tilldelad av och Tilldelad när Ansvarig ändras.
- Validera status, personer och datum.

### Manuell markering som Klar

När Status ändras till Klar:

- Nicklas väljer Slutförd av.
- Slutförd fylls automatiskt.
- Saknad Slutförd av markeras tydligt som datofel.
- En ofullständig klar rad visas inte i Familjehistoriken förrän den korrigerats.

### Administrativ återaktivering

Appen erbjuder ingen återställning av klara eller raderade uppgifter.

Nicklas kan återaktivera dem genom att ändra Status i Sheet.

Vid Klar till Aktuell eller Senare:

- Slutförd av töms.
- Slutförd töms.
- Uppdaterad ändras.
- Version höjs.
- Senast ändrad av blir Nicklas (Sheet).

Vid Raderad till Aktuell eller Senare uppdateras motsvarande ändringsfält.

## 11. Status och livscykel

### Skapande

- Normal skapelse får Status Aktuell.
- Ansvarig är Alla om inget annat väljs.
- Skapad av, Tilldelad av och Senast ändrad av sätts till enhetens identitet.
- Klienten genererar ett stabilt ID före nätverksanropet.

### Senare

- En uppgift får flyttas till Senare.
- En Senare-uppgift får ha deadline.
- En Senare-uppgift utan deadline ligger kvar tills någon ändrar den.

### Automatisk flytt från Senare

När Familj öppnas ska Apps Script, innan aktuell data returneras:

1. Hitta Senare-uppgifter med deadline.
2. Flytta dem till Aktuell om deadline är inom sju kalenderdagar.
3. Flytta redan försenade Senare-uppgifter till Aktuell.
4. Sätta Senast ändrad av till Automatik.
5. Uppdatera Uppdaterad och Version.

Samma regel tillämpas direkt när en uppgift skapas eller ändras genom appens API.

Ingen tidsstyrd bakgrundskörning krävs i version 1.

### Slutförande

- Vem som helst får slutföra vilken uppgift som helst.
- Status blir Klar.
- Slutförd av blir den faktiska användaren.
- Slutförd sätts av servern.
- Senast ändrad av blir den faktiska användaren.
- Uppgiften försvinner från Checklista eller Senare och visas i Historik.
- Appen erbjuder ingen återställning.

### Radering

- Status blir Raderad.
- Raden tas inte bort från Sheet.
- Senast ändrad av blir personen som raderade.
- Uppdaterad och Version ändras.
- Radering kräver bekräftelse i appen.
- Ingen Ångra-funktion finns.

## 12. Deadline och sortering

Deadline är frivilligt och innehåller endast kalenderdatum.

Förseningsstatus beräknas av appen och sparas inte som separat kolumn.

Klassificering:

- Ingen deadline.
- Framtida deadline.
- Idag.
- Försenad.
- Klar, som aldrig visas som försenad.

Sorteringsordning för aktiva uppgifter:

1. Försenade, äldst deadline först.
2. Deadline idag, äldst skapad först.
3. Framtida deadline, närmast deadline först.
4. Ingen deadline, äldst skapad först.

Historik sorteras med nyast slutförd först.

## 13. Alla- och Mina-filter

Alla visar samtliga aktiva familjeuppgifter.

Mina visar endast uppgifter där Ansvarig är samma person som enhetens identitet.

Uppgifter med Ansvarig Alla visas inte under Mina.

Filterknapparna visar antal och uppdateras efter skapande, omfördelning, slutförande, radering och synkning.

## 14. Historik

Privat och Jobb behåller nuvarande lokala beteende:

- Visar de senaste 14 dagarna.
- Raderar lokala historikposter äldre än 14 dagar.
- Tillåter återställning i appen.

Familj skiljer sig:

- Fullständig klar historik behålls permanent i Sheet.
- Ingen automatisk rensning görs.
- Familjehistoriken hämtas först när Historik öppnas.
- Appen hämtar endast poster slutförda under de senaste 14 dagarna.
- Filtreringen baseras på Slutförd.
- Familjehistoriken saknar återställningsknapp.
- Äldre historik hämtas inte av appen men ligger kvar för framtida analys.

Historik får aldrig ingå i Familjens normala bootstrap.

## 15. Snabblistan

Familjens Snabblista hämtas från Favoriter-bladet.

Ett tryck på en favorit:

- Skapar uppgiften direkt.
- Sätter Status till Aktuell.
- Sätter Ansvarig till Alla.
- Lämnar Deadline tom.
- Sätter Skapad av och Tilldelad av till användaren.
- Visar bekräftelsen Tillagd för Alla med åtgärden Redigera.

Redigera öppnar samma redigeringsflöde som en vanlig uppgift.

## 16. Uppgiftsrad och redigering

Familj använder en separat kompakt uppgiftsrad.

Standardraden visar:

- Titel.
- Deadline eller förseningsstatus när det finns.
- Nuvarande ansvarig.
- Vem som satte nuvarande ansvarig när det behövs för tydlighet.

Försenad uppgift visar:

- Röd varningssymbol.
- Röd text, exempelvis Försenad två dagar.
- Diskret röd indikator.

Detaljpilen visar:

- Skapad av.
- Tilldelad av och tid.
- Senast ändrad av och tid.
- Deadline.
- Redigera.
- Flytta till Senare eller Aktuell.
- Radera.

Redigeringsfönstret innehåller:

- Uppgift.
- Ansvarig.
- Deadline med möjlighet att ta bort datumet.
- Spara ändringar.

Alla familjemedlemmar ser samma åtgärder.

## 17. Anslutningsflöde

Första gången Familj öppnas på en oansluten enhet visas:

1. Apps Script-adress.
2. Personlig enhetsnyckel som administratören har skapat för den aktuella familjemedlemmen.
3. Testa och anslut. Medlemsidentiteten returneras av servern och väljs inte i klienten.

Anslutningen sparas först efter ett lyckat test.

Anslutningen ska normalt ligga kvar efter:

- Stängning och återöppning.
- Omstart av Chrome.
- Omstart av telefon.
- Normal PWA-uppdatering.

Ny anslutning krävs efter:

- Frånkoppling.
- Rensad appdata.
- Avinstallation.
- Spärrning eller rotation av den aktuella enhetens nyckel.

Appen ska erbjuda Koppla från Familj.

## 18. Målmiljö

- Moderna Androidtelefoner.
- Google Chrome.
- Gumli installerad som PWA.
- En telefon per familjemedlem.
- Fast identitet per installation.
- Fyra produktionsenheter.

Teknisk verifiering görs först i Chrome med flera mobilbredder, sedan på minst två verkliga Androidtelefoner och slutligen på alla fyra under piloten.

## 19. Cache, synkning och offline

När Familj öppnas:

1. Senaste sparade familjedata visas omedelbart om cache finns.
2. Appen visar Synkar.
3. Apps Script kör automatisk Senare-kontroll.
4. Ny data ersätter cache.
5. Status ändras till Synkad nyss.

Vid timeout efter 10 sekunder:

- Visa begripligt fel.
- Visa Försök igen.
- Behåll och visa cache.

Offline:

- Cache får läsas.
- Synkstatus visar Offline – visar sparad data.
- Skapande och ändringar blockeras.
- Inga ändringar köas.

Cache, anslutningsinformation och Privat/Jobb-data lagras separat.

## 20. Tekniskt upplägg

### App

- Befintlig ClientStorageRepository fortsätter hantera Privat och Jobb.
- Familj får separata modeller och ett asynkront FamilyRepository.
- Familj får separata vyer och komponenter där nätverksbeteendet skiljer sig.
- Familj-repository och familjevyer konstrueras först när Familj väljs.
- Sena nätverkssvar får inte ersätta en vy efter att användaren bytt läge.

### Apps Script

Apps Script körs som Nicklas men får ingen kalkylarksbehörighet till Nicklas Googlekonto. Det använder ett separat Gumli-servicekonto via Google Sheets API och Script Properties för:

- Sheet-ID.
- Servicekontots privata JSON-nyckel, endast på serversidan.
- SHA-256-hashar av enheternas separata nycklar, kopplade till respektive medlem.
- Eventuell API-version.

API-anrop skickar enhetsnyckeln i begärans innehåll, aldrig i URL. Servern härleder användaridentiteten från nyckeln.

Minsta API-operationer:

- health
- bootstrap
- listLater
- listHistory
- createTask
- updateTask
- changeStatus
- deleteTask

bootstrap returnerar:

- Aktuella uppgifter.
- Medlemmar.
- Favoriter.
- Servertid.

bootstrap returnerar inte:

- Historik.
- Raderade uppgifter.
- Hela Senare-listan.

### Stabilt svarsformat

Alla svar innehåller:

- ok
- data
- error
- server_time
- api_version

Stabila felkoder omfattar minst:

- UNAUTHORIZED
- INVALID_INPUT
- NOT_FOUND
- VERSION_CONFLICT
- TIMEOUT
- SERVER_ERROR

## 21. Samtidighet och dubblettskydd

- Klienten skapar ID före createTask.
- Samma ID får inte skapa flera rader.
- Apps Script använder låsning vid skrivningar.
- Varje uppdatering skickar senast kända Version.
- Gammal Version ger VERSION_CONFLICT.
- Servern returnerar senaste raden vid konflikt.
- Appen får aldrig tyst skriva över en senare ändring.
- Dubbeltryck och återförsök ska vara idempotenta.

## 22. Säkerhet

- Ingen servicekontonyckel eller enhetsnyckel lagras i GitHub.
- Ingen servicekontonyckel byggs in i PWA:n eller sparas på familjens enheter.
- Ingen enhetsnyckel förekommer i URL, logg eller felmeddelande.
- Sheet-ID, servicekontonyckel och hashade enhetsnycklar lagras i Apps Script-konfiguration.
- Enhetsanslutningen lagras lokalt i PWA:ns ursprungsskyddade lagring.
- Editoradministration i Apps Script är privat för `google.script.run` och kan bara
  köras manuellt av en behörig scriptredigerare.
- PWA:n binder Apps Script-bryggan med en ny 256-bitars nonce per iframe, strikt
  sandbox-origin och exakt svarsfönster.
- Familjebryggan startar inte i en inbäddad Gumli-sida, och ett timeoutat anrop får
  aldrig skickas i efterhand.
- Fel nyckel och saknad nyckel ger inget familjeinnehåll.
- Varje enhetsnyckel kan spärras eller roteras separat.
- Rotation kräver endast omanslutning av den berörda enheten.
- Sheet och Apps Script delas inte med familjemedlemmarna.

## 23. Prestandakrav

- Privat och Jobb gör inga familjeanrop vid normal uppstart.
- Privat och Jobb konstruerar inga familjevyer eller nätverksrepositoryn vid normal uppstart.
- Privat/Jobb-start får inte försämras mer än fem procent eller 200 millisekunder jämfört med baslinjen, beroende på vilket som är störst.
- Cache ska visas utan att vänta på nätverket.
- Familjesynkning har tio sekunders timeout.
- Aktuell lista ska hantera minst 50 uppgifter utan märkbar låsning.
- Familjehistorikens totala storlek i Sheet får inte påverka normal Familj-start.

## 24. Obligatoriska vy- och feltillstånd

Följande tillstånd ska ha definierad text, tillåtna handlingar och test:

- Familj aldrig ansluten.
- Anslutning testas.
- Fel nyckel.
- Anslutning lyckad.
- Första laddning utan cache.
- Cache visas och synkning pågår.
- Synkad.
- Offline med cache.
- Offline utan cache.
- Timeout.
- Ogiltig Sheet-rad.
- Spärrad eller roterad enhetsnyckel.
- Tom aktuell lista.
- Många aktuella uppgifter.
- Tom Historik.
- Tom Senare.
- Ändring synkar.
- Ändring misslyckades.
- Versionskonflikt.

## 25. Teststrategi

### Enhetstester

- Familjemodeller.
- Validering av svenska Sheet-värden.
- Deadlineklassificering.
- Sjudagarsregeln.
- Sorteringsregler.
- Alla- och Mina-filter.
- Statusövergångar.
- Återaktivering och rensning av slutförandefält.
- Cacheformat.
- Felöversättning.

### Repository- och API-kontraktstester

- health och bootstrap.
- Autentisering.
- Skapande och idempotens.
- Uppdatering.
- Slutförande.
- Senare och automatisk aktivering.
- Radering.
- Konflikt.
- Ogiltiga manuella rader.
- Historikens 14-dagarsfilter utan radering.

### Komponenttester

- Trelägesväljaren.
- Anslutningsflödet.
- Kompakt familjerad.
- Detaljexpansion.
- Förseningsmarkering.
- Alla/Mina-räknare.
- Redigeringsdialog.
- Raderingsbekräftelse.
- Synk-, offline- och feltillstånd.

### E2E-tester

- Privat/Jobb-start utan familjeanrop.
- Första Familj-anslutning.
- Beständig anslutning.
- Skapa, ändra, tilldela, slutföra och radera.
- Snabblistan.
- Historik.
- Senare och sjudagarsregeln.
- Två samtidiga klienter.
- Långsam anslutning och timeout.
- Offline med cache.
- Responsivitet vid minst 320, 390 och 412 pixlars bredd.

### Verkliga enheter

- Nicklas telefon som första administratörspilot.
- Minst en andra familjemedlems telefon före utrullning.
- Alla fyra telefoner under slutlig pilot.

## 26. Första tekniska kontroll efter godkänd plan

Den första tekniska aktiviteten ska vara ett avgränsat genomförbarhetstest, inte full implementation.

Testet ska bevisa:

- En publicerad Gumli-PWA kan anropa Apps Script.
- Unik enhetsnyckel fungerar och servern returnerar rätt medlem.
- Fel nyckel nekas.
- Anropet fungerar i installerad Chrome-PWA på Android.
- Anslutningen kan lagras beständigt.
- Privat/Jobb-start gör inga familjeanrop.
- Apps Script kan läsa och skriva till ett separat testark.

Om testet misslyckas stoppas arbetet innan full implementation och backendvalet omprövas.

## 27. Kontrollpunktsprincip

- Endast en kontrollpunkt får vara aktiv åt gången.
- Nästa kontrollpunkt startar först när föregående är godkänd.
- Varje teknisk kontrollpunkt kräver sparat bevis.
- Varje godkänd implementationsträcka avslutas med en avgränsad commit.
- Produktbeslut godkänns av Nicklas.
- Objektiva tekniska kontrollpunkter får godkännas av Codex när beviset är tillräckligt.
- Verklig mobilupplevelse, Googlebehörigheter, pilot och utrullning kräver Nicklas godkännande.

## 28. Definition of Ready

Implementation får börja när samtliga följande rutor är godkända:

- [x] Nicklas har granskat och uttryckligen godkänt detta dokument.
- [x] Alla produktregler är beslutade.
- [x] Sheet-schemat är godkänt.
- [x] API-kontraktet är godkänt på konceptnivå.
- [x] Säkerhets- och anslutningsmodellen är godkänd.
- [x] Cache- och offlinebeteendet är godkänt.
- [x] Teststrategin är godkänd.
- [x] Målmiljön är dokumenterad.
- [x] Icke-mål är uttryckligen dokumenterade.
- [x] Inga produktionshemligheter har skapats eller delats i planeringsmaterialet.
- [x] Ingen implementationskod har ändrats från baslinjen.

Efter slutligt godkännande:

1. Skapa arbetsgren.
2. Kör och spara baslinjetester.
3. Mät uppstart.
4. Genomför det avgränsade Apps Script/PWA-testet.
5. Fortsätt endast om kontrollen godkänns.

## 29. Antaganden för slutlig granskning

Följande tekniska standardval används om de inte ändras vid slutgranskningen:

- Familj öppnas inte automatiskt vid PWA-start; Privat förblir initialt läge.
- Normal Lägg till uppgift skapar Aktuell.
- Flytt till Senare görs från uppgiftens detaljåtgärder.
- En separat direktknapp för Lägg till i Senare är inte nödvändig i version 1.
- Exakt 14 dygn används som Familjehistorikens visningsgräns.
- Senast ändrad av visas i detaljvyn, medan Tilldelad av får visas kompakt när ansvarig har ändrats.
- Manuella Sheet-fel markeras och isoleras; en felaktig rad får inte blockera övrig familjedata.

Ändringar i dessa antaganden ska göras före implementationsstart.

## 30. Resultat – teknisk kontrollpunkt 1

Datum: 2026-07-20

Codex-verifierat:

- [x] Den publicerade Apps Script-bryggan svarar från Gumli-PWA:n.
- [x] Fel enhetsnyckel nekas med `UNAUTHORIZED` och tydligt fel i appen.
- [x] Rätt enhetsnyckel returnerar `Nicklas`; medlemsnamnet väljs inte i klienten.
- [x] Anslutningen sparas separat i IndexedDB och återställs efter omladdning.
- [x] Privatläget skapar ingen familje-iframe och gör inget familjeanrop före aktivt val av Familj.
- [x] Apps Script-servicekontot kan skapa testbladet och skriva dess rubrik via Google Sheets API.
- [x] Script Properties är åter begränsade till `https://nicklasc.github.io` efter lokal verifiering.
- [x] Ingen enhetsnyckel, servicekontonyckel eller arkbehörighet byggs in i PWA:n eller versionshanteras.
- [x] Automatisk regression: 326/326 tester godkända.
- [x] Privat-startens eftermätning ligger inom prestandakravet.

Nicklas-verifierat på installerad Android-PWA 2026-07-20:

- [x] Publicera den färdiga kontrollpunktsbuilden.
- [x] Installera eller uppdatera Gumli som PWA i Chrome på Nicklas Androidtelefon.
- [x] Anslut enheten med Nicklas personliga enhetsnyckel.
- [x] Stäng och öppna den installerade appen och kontrollera att `Ansluten som Nicklas` ligger kvar.

Kontrollpunkt 1 är slutgodkänd. Full implementation av familjeuppgifter kan starta.
