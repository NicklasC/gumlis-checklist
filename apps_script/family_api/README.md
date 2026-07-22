# Gumli Familj API

Detta är den versionshanterade Apps Script-koden för Familj. Mappen innehåller inga hemligheter och får ligga i GitHub.

## Script Properties

Följande värden konfigureras i Apps Script-projektets inställningar och får aldrig läggas i repositoryt:

- `SPREADSHEET_ID`: ID för det privata arket `gumlis-checklist-familj`.
- `SERVICE_ACCOUNT_JSON`: komplett JSON för ett separat servicekonto som bara har fått familjearket delat med sig. Värdet får aldrig skickas till klienten.
- `DEVICE_TOKEN_HASHES_JSON`: JSON-objekt där varje SHA-256-hash pekar på `Nicklas`, `Ida`, `Thor` eller `Johanna`. Endast hashar lagras på servern.
- `API_VERSION`: för genomförbarhetstestet `family-spike-v2`.
- `ALLOWED_ORIGINS`: JSON-lista, normalt `["https://nicklasc.github.io"]`.

## Genomförbarhetstest

1. Lägg in Script Properties.
2. Kör `verifyConfiguration` i editorn.
3. Kör `setupProbeSheet` för att skapa bladet `Tekniskt test`.
4. Dela endast familjearket med servicekontots e-postadress som redigerare.
5. Distribuera som webbapp som körs som den användare som distribuerar och tillåter anonym åtkomst.
6. Testa `ping`, `probeWrite` och `probeRead` med rätt och fel enhetsnyckel.

## Familj version 1

`setupFamilySheets` skapar den produktionsnära strukturen med ett statusbaserat blad
`Uppgifter` samt bladen `Medlemmar` och `Favoriter`. Funktionen ska bara köras i det
redan beslutade privata arket `gumlis-checklist-familj`.

API-kontraktet består av:

- `ping`: verifierar enheten och returnerar medlemmen.
- `bootstrap`: returnerar endast Aktuell, aktiva medlemmar, aktiva favoriter och servertid.
- `listLater`: returnerar Senare separat.
- `listHistory`: returnerar endast uppgifter slutförda under de senaste 14 dagarna.
- `createTask`: skapar en Aktuell-uppgift idempotent med klientens stabila ID.
- `updateTask`: ändrar titel, ansvarig eller deadline med versionskontroll.
- `changeStatus`: flyttar mellan Aktuell och Senare eller slutför uppgiften som Klar.
  Vid slutförande sätts `Slutförd av` från den autentiserade enheten och
  `Slutförd` från serverns klocka.
- `deleteTask`: sätter status Raderad utan att ta bort Sheet-raden.

Historik och raderade uppgifter ingår aldrig i `bootstrap`. Ogiltiga manuella rader
isoleras som `invalidRows` och blockerar inte övriga giltiga rader.
`listHistory` filtrerar exakt 14 dygn på `Slutförd`, sorterar nyast först och
rensar aldrig äldre Sheet-rader.

Alla svar använder fälten `ok`, `data`, `error`, `server_time` och `api_version`.

Skrivoperationerna använder Apps Script-lås. Servern härleder alltid aktören från
enhetsnyckeln, uppdaterar auditfälten och returnerar senaste rad vid
`VERSION_CONFLICT`; klienten skickar aldrig ett valbart medlemsnamn som aktör.

`doPost` finns för ett direkt CORS-test. `doGet` levererar en iframe-brygga som använder `google.script.run` om direkt browser-POST inte fungerar. Enhetsnyckeln skickas i requestens body eller `postMessage`, aldrig i URL:en.

## Google-behörighet och faktisk avgränsning

Apps Script får inte åtkomst till Nicklas Google-kalkylark. Det har bara behörighet att göra externa HTTPS-anrop. Skriptet autentiserar sig mot Google Sheets API som ett separat Gumli-servicekonto, och endast familjearket delas med den identiteten.

Servicekontots privata nyckel lagras endast i den privata Script Propertyn `SERVICE_ACCOUNT_JSON`. Den får aldrig byggas in i PWA:n, sparas på familjens enheter eller checkas in i GitHub. Telefonerna får separata slumpmässiga enhetsnycklar; servern lagrar bara deras SHA-256-hashar och bestämmer medlemmen från den autentiserade enheten.
