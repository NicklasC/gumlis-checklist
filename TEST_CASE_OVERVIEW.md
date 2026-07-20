# Test case overview

Det här dokumentet beskriver samtliga automatiserade testfall i Gumli. Beskrivningarna är korta och grupperade på samma sätt som testkoden.

GUI-testerna beskrivs ur användarens perspektiv: vad användaren gör eller ser och varför det beteendet är viktigt. Namnet i kolumnen **Testfall** är testets tekniska namn i koden.

## Syfte och underhåll

Målet med dokumentet är att en människa snabbt och enkelt ska få en övergripande förståelse för vad testautomatiseringen faktiskt gör. Det ska gå att förstå testernas avsikt utan att först läsa eller kunna tolka testkoden.

**Dokumentet måste uppdateras samtidigt som ett test läggs till, tas bort eller ändras.** Uppdatera både beskrivningen av berörda testfall och antalen i översikten. En teständring är inte färdigdokumenterad förrän den här översikten stämmer med testkoden.

## Översikt

| Område | Antal | Innehåll |
|---|---:|---|
| Enhetstester | 67 | Datamodeller, lagring, migrering, historikregler och familjeanslutning |
| Komponenttester | 95 | Vyernas och komponenternas logik utan webbläsare |
| PWA- och distributionstester | 79 | Manifest, Apps Script-API, familjebrygga, byggfiler, sidmallar och de två repona |
| GUI/E2E-tester | 71 | Verkliga användarflöden i Chromium |
| **Totalt** | **312** | |

GUI-testerna körs bara när `GUMLI_RUN_E2E=1`. Vissa PWA-tester kräver att den byggda appen och deploy-repot finns lokalt; annars markeras de som överhoppade.

## Enhetstester

### Datamodeller — `tests/unit/test_models.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_defaults_to_unchecked` | En ny uppgift är inte markerad som klar. |
| `test_default_category_is_other` | En uppgift utan vald kategori får standardkategorin Övrigt. |
| `test_created_at_is_generated` | En ny uppgift får automatiskt en UTC-tidsstämpel. |
| `test_id_is_required` | En uppgift kan inte skapas utan id. |
| `test_title_is_required` | En uppgift kan inte skapas utan titel. |
| `test_swedish_text_round_trips_through_json` | Svenska tecken bevaras när en uppgift sparas som JSON och läses tillbaka. |
| `test_items_are_not_shared_between_instances` | Två checklistor får var sin separata lista med uppgifter. |
| `test_default_category_order_is_created` | En ny checklista får den förväntade kategoriordningen. |
| `test_template_defaults_to_false` | En vanlig ny checklista markeras inte som mall. |
| `test_last_cleaned_date_defaults_to_none` | En ny checklista saknar städdatum tills städning har gjorts. |
| `test_common_group_items_are_not_shared` | Två favoritgrupper får var sin separata lista med favoriter. |
| `test_checklists_data_defaults_to_empty_lists` | Ett tomt dataobjekt startar med tomma checklistor och favoritgrupper. |

### Historikens lagringstid — `tests/unit/test_history_retention.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_removes_item_older_than_retention` | Historik äldre än 14 dagar tas bort. |
| `test_keeps_recent_item` | Ny historik behålls. |
| `test_keeps_item_just_inside_boundary` | En post precis innanför 14-dagarsgränsen behålls. |
| `test_removes_item_just_outside_boundary` | En post precis utanför 14-dagarsgränsen tas bort. |
| `test_accepts_timestamp_without_z_suffix` | En giltig tidsstämpel utan avslutande `Z` kan läsas. |
| `test_keeps_item_with_invalid_timestamp` | En post med trasig tidsstämpel behålls i stället för att raderas av misstag. |

### Migrering av sparade data — `tests/unit/test_repository_migrations.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_normalizes_category_order` | Äldre kategoriordning ersätts med de stödda lägena Privat och Jobb. |
| `test_migrates_unknown_item_category_to_private` | En äldre eller okänd kategori flyttas säkert till Privat. |
| `test_preserves_work_category` | Befintliga jobbuppgifter förblir jobbuppgifter efter migrering. |
| `test_creates_missing_later_list` | Listan Senare skapas om den saknas i äldre data. |
| `test_creates_missing_history_list` | Historiklistan skapas om den saknas i äldre data. |
| `test_creates_exactly_two_supported_groups` | Migreringen lämnar exakt en privat och en jobbrelaterad favoritgrupp. |
| `test_preserves_legacy_favorite_in_private_group` | En äldre favorit bevaras i den privata favoritgruppen. |
| `test_does_not_duplicate_default_favorite` | En befintlig standardfavorit läggs inte in en gång till. |
| `test_current_data_stays_semantically_equal` | Redan aktuell data ändras inte innehållsmässigt av migreringen. |

### Direkt browserlagring och säker migrering — `tests/unit/test_browser_storage.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_direct_value_skips_legacy_loader` | En befintlig direkt IndexedDB-post används utan att det gamla filsystemet startas. |
| `test_confirmed_legacy_value_is_migrated` | Bekräftad gammal IDBFS-data kopieras till den nya direkta lagringen. |
| `test_confirmed_empty_legacy_store_enables_new_writes` | En kontrollerad tom gammal lagring tillåter att nya data sparas direkt. |
| `test_unavailable_legacy_store_never_persists_defaults` | Standarddata skrivs inte om den gamla lagringen inte kunnat kontrolleras. |
| `test_migrated_session_writes_directly_afterward` | Efter migreringen går efterföljande skrivningar direkt till den nya lagringen. |
| `test_direct_database_failure_keeps_legacy_data_read_only` | Vid fel i nya IndexedDB visas gamla data utan att något skrivs över. |

### Lokal repositorylagring — `tests/unit/test_client_storage_repository.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_initialization_creates_desktop_storage_file` | Lagringsfilen skapas vid första starten i skrivbordsmiljö. |
| `test_initialization_writes_valid_json` | Den nyskapade lagringsfilen innehåller giltig JSON. |
| `test_missing_raw_storage_returns_none` | Saknad rå lagring hanteras som att inga data finns. |
| `test_raw_round_trip_preserves_unicode` | Unicode och svenska tecken bevaras vid rå skrivning och läsning. |
| `test_corrupt_json_is_handled_as_empty_data` | Trasig JSON hanteras utan krasch och ger en tom datamängd. |
| `test_saves_new_checklist` | En ny checklista kan sparas och läsas tillbaka. |
| `test_updates_checklist_without_duplicate` | En befintlig checklista uppdateras utan att dupliceras. |
| `test_deletes_custom_checklist` | En egen checklista kan raderas. |
| `test_returns_none_for_unknown_checklist` | Sökning efter ett okänt id ger inget resultat. |
| `test_saves_new_favorite_group_to_storage` | En ny favoritgrupp skrivs till den lokala lagringen. |
| `test_updates_favorite_group_without_duplicate` | En favoritgrupp uppdateras utan att dupliceras. |
| `test_deleted_required_favorite_group_is_restored` | En obligatorisk favoritgrupp återskapas om den raderas. |

### Familjens enhetsanslutning — `tests/unit/test_family_repository.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_connect_verifies_and_persists_server_derived_member` | En ny enhetsnyckel sparas först efter att servern har godkänt den och returnerat rätt medlem. |
| `test_wrong_key_is_not_persisted` | En felaktig enhetsnyckel nekas och sparas aldrig på enheten. |
| `test_resume_reuses_persisted_connection` | En tidigare godkänd anslutning verifieras på nytt och återanvänds vid nästa öppning. |
| `test_invalid_local_state_does_not_make_network_request` | Trasig lokal anslutningsdata ignoreras utan att något familjeanrop görs. |
| `test_disconnect_removes_persisted_connection` | Koppla från tar bort den separat sparade familjeanslutningen. |

### Filbaserad lagring — `tests/unit/test_repository_crud.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_creates_database_file` | Databasfilen skapas när lagringen startas. |
| `test_creates_exactly_three_standard_lists` | En ny lagring innehåller exakt Checklista, Senare och Historik. |
| `test_creates_active_list` | Den aktiva checklistan skapas. |
| `test_creates_later_list` | Listan Senare skapas. |
| `test_creates_history_list` | Historiklistan skapas. |
| `test_creates_private_favorites` | Den privata favoritgruppen skapas. |
| `test_creates_work_favorites` | Favoritgruppen för jobb skapas. |
| `test_returns_none_for_unknown_checklist` | Ett okänt checklist-id ger inget resultat. |
| `test_saves_new_checklist` | En ny checklista kan sparas och hämtas. |
| `test_updates_existing_checklist_without_duplicate` | En befintlig checklista kan ändras utan att en kopia skapas. |
| `test_persists_checklist_item` | En uppgift i en checklista sparas och läses tillbaka med rätt text. |
| `test_deletes_checklist` | En checklista kan raderas. |
| `test_saves_new_group` | En ny favoritgrupp kan sparas. |
| `test_updates_group_without_duplicate` | En favoritgrupp kan uppdateras utan att dupliceras. |
| `test_deletes_group` | En favoritgrupp kan raderas. |
| `test_save_leaves_no_temporary_file` | En slutförd sparning lämnar ingen tillfällig fil efter sig. |
| `test_empty_existing_file_can_be_read` | En tom befintlig fil kan läsas utan krasch. |

## Komponenttester

### Huvudvyn — `tests/components/test_main_view.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_defaults_to_private_mode` | Appen startar i privat läge. |
| `test_defaults_to_checklist_page` | Appen startar på sidan Checklista. |
| `test_mode_change_updates_global_mode` | Ett byte till Jobb uppdaterar appens gemensamma läge. |
| `test_mode_change_refreshes_active_view` | Den öppna sidan uppdateras när läget ändras. |
| `test_navigation_has_four_destinations` | Huvudnavigeringen har fyra mål. |
| `test_navigation_labels_are_stable` | Flikarna heter Checklista, Snabblistan, Historik och Senare i rätt ordning. |
| `test_secondary_views_are_not_created_during_startup` | Sekundära vyer byggs inte under appens start. |
| `test_secondary_view_is_created_on_first_request` | En sekundär vy skapas först när användaren öppnar den. |
| `test_lazily_created_view_is_reused` | En lazy-loadad vy återanvänds i stället för att byggas om. |
| `test_unknown_navigation_destination_is_rejected` | Ett okänt navigationsmål avvisas tydligt. |
| `test_family_repository_and_view_are_lazy` | Familjens nätverkslager och vy skapas först när användaren väljer Familj. |
| `test_family_mode_does_not_reload_private_repository_view` | Ett byte till Familj startar inte om Privat/Jobb-lagringen. |
| `test_switching_from_family_to_private_replaces_family_view` | Ett direkt byte från Familj till Privat ersätter anslutningsvyn med den privata sidan. |
| `test_switching_from_family_to_work_replaces_family_view` | Ett direkt byte från Familj till Jobb ersätter anslutningsvyn med jobbsidan. |

### Tidigt appskal — `tests/components/test_startup_view.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_shell_matches_main_navigation_structure` | Laddningsskalet visar samma fyra navigationsmål som huvudvyn. |
| `test_shell_navigation_is_not_interactive` | Skalet kan inte användas innan sparade data är redo. |
| `test_shell_identifies_application` | Namnet Gumli visas direkt i appskalet. |
| `test_shell_has_loading_feedback` | Skalet visar både aktivitet och begriplig laddningstext. |

### Lägesväljaren — `tests/components/test_mode_selector.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_defaults_to_private` | Lägesväljaren startar på Privat. |
| `test_switches_to_work` | Lägesväljaren kan byta till Jobb. |
| `test_switch_calls_callback` | Resten av appen meddelas när läget byts. |
| `test_selecting_active_mode_does_not_call_callback` | Ett klick på redan aktivt läge orsakar ingen onödig uppdatering. |
| `test_work_mode_highlights_work_button` | Jobbknappen markeras när Jobb är aktivt. |
| `test_private_mode_highlights_private_button` | Privatknappen markeras när Privat är aktivt. |
| `test_switches_to_family` | Lägesväljaren kan byta till Familj och markerar rätt knapp. |

### Familjens anslutningsvy — `tests/components/test_family_connection_view.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_successful_connection_shows_server_member` | En godkänd nyckel visar den medlem som servern har identifierat. |
| `test_wrong_key_shows_clear_error` | En felaktig nyckel ger ett tydligt svenskt felmeddelande. |
| `test_resume_shows_persisted_member` | En sparad anslutning återställs automatiskt när Familj öppnas igen. |
| `test_disconnect_returns_to_connection_form` | Koppla från återgår till formuläret för enhetsnyckel. |

### Snabbinmatning — `tests/components/test_quick_add.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_private_mode_uses_private_button_label` | Privat läge visar knappen `+ Att göra`. |
| `test_work_mode_uses_work_button_label` | Jobbläge visar knappen `+ Jobb`. |
| `test_today_button_routes_to_active_mode` | Idag-knappen skickar uppgiften till det aktiva läget. |
| `test_later_button_routes_to_later` | Senare-knappen skickar uppgiften till listan Senare. |
| `test_enter_routes_to_active_mode` | Enter lägger uppgiften i det aktiva läget. |
| `test_submission_trims_title` | Extra mellanslag runt titeln tas bort. |
| `test_submission_clears_field` | Inmatningsfältet töms efter en giltig uppgift. |
| `test_blank_submission_does_not_call_callback` | Tom text skapar ingen uppgift. |
| `test_blank_submission_focuses_field` | Fältet behåller fokus efter en tom inmatning. |

### Uppgiftskort — `tests/components/test_item_card.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_unchecked_item_has_complete_tooltip` | En öppen uppgift har hjälptexten Markera som klar. |
| `test_checked_item_has_undo_tooltip` | En klar uppgift har hjälptexten Markera som ogjord. |
| `test_later_button_is_visible_for_unchecked_item` | En öppen uppgift kan flyttas till Senare. |
| `test_later_button_is_hidden_for_checked_item` | En klar uppgift visar inte knappen för Senare. |
| `test_check_click_toggles_state` | Ett klick på klar-knappen växlar uppgiftens status. |
| `test_check_click_calls_callback` | Vyn meddelas när uppgiftens status ändras. |
| `test_checked_text_is_struck_through` | Texten stryks över när uppgiften markeras som klar. |
| `test_delete_click_calls_callback` | Vyn meddelas när raderingsknappen används. |
| `test_move_later_click_calls_callback` | Vyn meddelas när uppgiften flyttas till Senare. |
| `test_move_later_is_hidden_without_callback` | Senare-knappen döljs där flyttfunktionen inte stöds. |

### Checklistvyn — `tests/components/test_checklist_view.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_creates_private_item` | En uppgift som läggs till privat får kategorin Privat. |
| `test_creates_work_item` | En uppgift som läggs till i jobbläge får kategorin Jobb. |
| `test_generated_item_id_has_prefix` | En ny uppgift får ett id med förväntat prefix. |
| `test_routes_later_item_to_later_list` | En uppgift vald för Senare sparas i rätt lista. |
| `test_later_item_keeps_active_mode` | En Senare-uppgift behåller det aktiva läget Privat eller Jobb. |
| `test_favorite_adds_item` | Ett klick på en favorit skapar en aktiv uppgift. |
| `test_duplicate_active_favorite_is_ignored` | Samma favorit skapar inte en dubblett av en redan öppen uppgift. |
| `test_checked_favorite_can_be_added_again` | En favorit får användas igen när den tidigare uppgiften är klar. |
| `test_delete_removes_only_selected_item` | Radering tar bara bort den valda uppgiften. |
| `test_move_to_later_removes_active_item` | En flyttad uppgift försvinner från dagens checklista. |
| `test_move_to_later_adds_backlog_item` | En flyttad uppgift läggs i Senare och behåller sin kategori. |
| `test_private_mode_renders_only_private_items` | Privat läge visar bara privata uppgifter. |
| `test_work_mode_renders_only_work_items` | Jobbläge visar bara jobbuppgifter. |
| `test_unchecked_items_render_before_checked_items` | Öppna uppgifter visas före klara uppgifter. |
| `test_daily_cleanup_moves_checked_item_to_history` | Gårdagens klara uppgifter flyttas till historiken. |
| `test_daily_cleanup_keeps_unchecked_item_active` | Öppna uppgifter ligger kvar efter den dagliga städningen. |

### Snabblistan/favoriter — `tests/components/test_templates_view.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_private_mode_shows_private_group` | Privat läge visar gruppen Privat favoriter. |
| `test_work_mode_shows_work_group` | Jobbläge visar gruppen Jobb favoriter. |
| `test_adds_trimmed_favorite` | En favorit sparas utan extra mellanslag runt texten. |
| `test_blank_favorite_is_ignored` | Tom text skapar ingen favorit. |
| `test_duplicate_favorite_is_ignored` | Samma favorit kan inte läggas till två gånger i gruppen. |
| `test_add_clears_input` | Inmatningsfältet töms efter att en favorit lagts till. |
| `test_remove_deletes_selected_favorite` | Bara den valda favoriten tas bort. |
| `test_tap_calls_callback_with_active_mode` | Ett tryck på en favorit skickar text och aktivt läge till checklistan. |
| `test_empty_repository_shows_empty_state` | En begriplig tomvy visas om favoritgrupper saknas. |

### Senare-vyn — `tests/components/test_later_view.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_submit_adds_private_item` | En uppgift som skapas i privat läge sparas som Privat. |
| `test_submit_adds_work_item` | En uppgift som skapas i jobbläge sparas som Jobb. |
| `test_submit_trims_title` | Extra mellanslag runt titeln tas bort. |
| `test_submit_clears_field` | Inmatningsfältet töms efter en giltig uppgift. |
| `test_blank_submit_adds_nothing` | Tom text skapar ingen Senare-uppgift. |
| `test_delete_removes_selected_item` | Den valda Senare-uppgiften kan raderas. |
| `test_promote_moves_item_to_active_list` | En Senare-uppgift kan flyttas till dagens checklista. |
| `test_promote_preserves_category` | Uppgiften behåller Privat eller Jobb när den flyttas till idag. |
| `test_promote_calls_parent_callback` | Huvudvyn meddelas när en uppgift flyttas till idag. |
| `test_private_mode_filters_work_items` | Jobbuppgifter visas inte i privat Senare-vy. |
| `test_work_mode_renders_work_item` | En jobbuppgift visas i jobbets Senare-vy. |

### Historikvyn — `tests/components/test_history_view.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_formats_today` | Dagens datum visas som Idag. |
| `test_formats_yesterday` | Gårdagens datum visas som Igår. |
| `test_formats_older_date_with_swedish_month` | Äldre datum visas med svenskt månadsnamn. |
| `test_private_empty_state` | Privat historik visar rätt tommeddelande. |
| `test_work_empty_state` | Jobbhistorik visar rätt tommeddelande. |
| `test_private_mode_filters_work_history` | Jobbhistorik visas inte i privat läge. |
| `test_history_creates_date_header_and_card` | Historik med innehåll får både datumrubrik och uppgiftskort. |
| `test_restore_removes_item_from_history` | En återställd uppgift tas bort från historiken. |
| `test_restore_adds_unchecked_item_to_active` | En återställd uppgift läggs tillbaka som öppen i checklistan. |
| `test_restore_preserves_category` | En återställd uppgift behåller Privat eller Jobb. |
| `test_restore_calls_parent_callback` | Huvudvyn meddelas när historik återställs. |

## PWA- och distributionstester

### PWA-manifest — `tests/pwa/test_manifest.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_manifest_exists` | PWA-manifestet finns. |
| `test_name_is_gumli` | Appens fullständiga namn är Gumli. |
| `test_short_name_is_gumli` | Appens kortnamn är Gumli. |
| `test_start_url_is_relative` | Installerad app startar relativt den publicerade sökvägen. |
| `test_display_mode_is_standalone` | Installerad app är konfigurerad att visas som en fristående app. |
| `test_theme_color_is_defined` | Manifestet innehåller en giltig temafärg. |
| `test_contains_four_install_icons` | Manifestet listar de fyra förväntade installationsikonerna. |
| `test_all_manifest_icons_exist` | Varje ikon som manifestet hänvisar till finns på disk. |
| `test_all_manifest_icons_are_png` | Alla manifestikoner anges som PNG-filer. |
| `test_maskable_icons_declare_purpose` | Maskerbara ikoner är korrekt märkta för olika enheters ikonformer. |
| `test_install_icons_stay_within_size_budget` | Installationsikonerna håller den fastställda storleksbudgeten. |

### HTML- och service worker-mallar — `tests/pwa/test_templates.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_uses_github_pages_base_path` | HTML-mallen använder `/gumlis-checklist/` som bassökväg. |
| `test_sets_flet_entrypoint_base` | Flets startpunkt använder rätt publiceringssökväg. |
| `test_sets_flet_asset_base` | Flets resurser hämtas från rätt publiceringssökväg. |
| `test_uses_flet_runtime_cdn` | Den fungerande Flet-runtimeversionen hämtas från dess CDN. |
| `test_references_manifest` | HTML-mallen länkar till PWA-manifestet. |
| `test_references_favicon` | HTML-mallen länkar till faviconen. |
| `test_registers_service_worker` | HTML-mallen registrerar appens service worker. |
| `test_cache_busts_python_app_archive` | Python-paketets URL innehåller en platshållare för byggversion. |
| `test_exposes_startup_timing_marks` | Startsidan erbjuder permanenta prestandamätpunkter. |
| `test_startup_console_logging_is_opt_in` | Starttider skrivs bara i konsolen när diagnostik uttryckligen aktiveras. |
| `test_marks_flutter_ready` | Tidpunkten då Flutter är redo registreras. |
| `test_has_versioned_cache_name` | Service workern använder ett versionshanterat cachenamn. |
| `test_has_install_handler` | Service workern hanterar installation. |
| `test_has_activate_handler` | Service workern hanterar aktivering. |
| `test_has_fetch_handler` | Service workern hanterar nätverksanrop. |
| `test_precaches_lightweight_app_shell` | Ett litet appskal förhandslagras utan att blockera installationen på stora filer. |
| `test_removes_old_versioned_caches` | Gamla Gumli-cacher rensas när en ny version aktiveras. |
| `test_navigation_uses_network_first` | Navigation söker en ny version online men kan falla tillbaka på cache. |
| `test_static_resources_use_cache_first` | Versionsbundna resurser hämtas från cache före nätverket. |
| `test_only_trusted_runtime_cdns_are_cacheable` | Bara Flets uttryckligt betrodda runtimevärdar får cachas över domängränsen. |
| `test_only_caches_successful_responses` | Felaktiga nätverkssvar sparas inte i cachen. |

### Familjens Apps Script-API — `tests/pwa/test_family_apps_script.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_contains_no_spreadsheet_url_or_local_secret_file` | Den versionshanterade API-koden innehåller ingen direkt arklänk, privat Google-nyckel eller lokal hemlighetsfil. |
| `test_reads_configuration_from_script_properties` | Ark-ID, servicekonto och hashade enhetsnycklar hämtas från privata Script Properties. |
| `test_service_account_private_key_stays_server_side` | Servicekontots privata nyckel används bara på serversidan och förekommer aldrig i iframe-klienten. |
| `test_member_identity_comes_from_device_token` | Servern härleder medlemmen från enhetsnyckeln och accepterar inte ett självrapporterat namn från klienten. |
| `test_rejects_wrong_key_before_action_dispatch` | Fel enhetsnyckel nekas innan någon API-åtgärd körs. |
| `test_supports_ping_read_and_idempotent_write_probe` | Spiken har ping, läsning och dubblettskyddad provskrivning. |
| `test_serializes_probe_writes_with_script_lock` | Samtidiga provskrivningar skyddas med Apps Script-låsning. |
| `test_probe_sheet_is_separate_from_family_tasks` | Provdata skrivs till ett avskilt tekniskt blad. |
| `test_direct_post_returns_json_without_putting_key_in_url` | Direkt POST ger JSON och lägger aldrig enhetsnyckeln i URL:en. |
| `test_bridge_restricts_parent_origin_and_targets_reply_origin` | Reservbryggan accepterar bara tillåtna ursprung och svarar endast till anroparen. |
| `test_manifest_runs_as_owner_and_allows_anonymous_web_app_calls` | Webbappen körs som Nicklas men har bara behörighet att göra externa HTTPS-anrop; den får ingen åtkomst till Nicklas Google-kalkylark. |

### PWA-brygga för Familj — `tests/pwa/test_family_bridge.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_family_iframe_is_created_lazily` | Apps Script-ramen skapas först när Familj faktiskt gör ett anrop. |
| `test_bridge_has_ten_second_timeout` | Ett familjeanrop avslutas med ett kontrollerat timeoutfel efter tio sekunder. |
| `test_bridge_validates_iframe_source_and_response_origin` | PWA:n accepterar bara svar från den inramade, betrodda Google-sidan. |
| `test_device_token_is_not_part_of_api_url` | Enhetsnyckeln förekommer inte i Apps Script-adressen. |
| `test_diagnostics_never_store_request_payload_or_token` | Den säkra webbläsardiagnostiken lagrar varken anropsinnehåll eller enhetsnyckel. |
| `test_deploy_forwards_only_family_worker_messages` | Den byggda Pythonvärden vidarebefordrar endast uttryckliga familjemeddelanden till bryggan. |

### Färdigbyggd PWA — `tests/pwa/test_build_output.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_index_exists` | Den byggda appen innehåller `index.html`. |
| `test_manifest_exists` | Den byggda appen innehåller manifestet. |
| `test_service_worker_exists` | Den byggda appen innehåller service workern. |
| `test_python_application_archive_exists` | Den byggda appen innehåller Python-paketet. |
| `test_flet_javascript_bundle_exists` | Den byggda appen innehåller Flets JavaScript-paket. |
| `test_flet_wasm_bundle_exists` | Den byggda appen innehåller Flets WebAssembly-paket. |
| `test_python_worker_exists` | Den byggda appen innehåller Python-arbetaren. |
| `test_python_host_forwards_startup_marks` | Den byggda Pythonvärden skickar worker-mätpunkter till startsidan. |
| `test_built_manifest_is_valid_json` | Det byggda manifestet är giltig JSON och avser Gumli. |
| `test_built_index_uses_expected_base` | Den byggda startsidan använder `/gumlis-checklist/`. |
| `test_built_index_uses_hashed_python_archive_url` | Startsidan hänvisar till en versionsmärkt Python-fil. |
| `test_built_icons_directory_exists` | Den byggda appen innehåller en ikonmapp. |
| `test_built_192_icon_exists` | Installationsikonen i storlek 192 px finns. |
| `test_built_512_icon_exists` | Installationsikonen i storlek 512 px finns. |

### Deploy-kontrakt och två repon — `tests/pwa/test_deployment_contract.py`

| Testfall | Vad testet kontrollerar |
|---|---|
| `test_builds_src_main` | Deployskriptet bygger appen från `src/main.py`. |
| `test_uses_expected_base_url` | Deployskriptet bygger för sökvägen `/gumlis-checklist/`. |
| `test_includes_assets` | Deployskriptet tar med appens resursmapp. |
| `test_targets_github_pages_repository` | Deployskriptet riktar sig mot rätt GitHub Pages-repo. |
| `test_restores_manifest_after_build` | Deployskriptet återställer det anpassade manifestet efter bygget. |
| `test_restores_service_worker_after_build` | Deployskriptet återställer den anpassade service workern efter bygget. |
| `test_restores_index_after_build` | Deployskriptet återställer den anpassade startsidan efter bygget. |
| `test_versions_python_app_archive` | Deployskriptet versionsmärker Python-paketets URL. |
| `test_versions_both_index_and_service_worker` | Samma byggversion används i startsidan och service workern. |
| `test_prunes_production_unneeded_debug_artifacts` | Källkartor, symbolfiler och oanvänd diagnostik tas bort från produktionsbygget. |
| `test_bridges_worker_startup_marks_to_main_page` | Deployskriptet installerar bryggan för Pythonworkerns mätpunkter. |
| `test_checks_deploy_repository_status` | Deployskriptet kontrollerar deploy-repots Git-status. |
| `test_source_repository_has_git_metadata` | Källkodsrepot är ett eget Git-repo. |
| `test_deploy_repository_has_git_metadata` | Deploy-repot är ett eget Git-repo. |
| `test_source_and_deploy_are_distinct_repositories` | Källkod och publicerad app ligger i två skilda Git-repon. |
| `test_deploy_origin_is_github_pages_repository` | Deploy-repots `origin` pekar på GitHub Pages-repot. |

## GUI/E2E-tester — användarens perspektiv

### Start och navigering — `tests/e2e/test_navigation.py`

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `test_app_title_is_visible` | Användaren öppnar appen och ser namnet Gumli. | Det ska vara tydligt att rätt app har öppnats. |
| `test_has_four_navigation_tabs` | Användaren ser fyra flikar i huvudmenyn. | Alla huvudområden måste vara möjliga att nå. |
| `test_checklist_tab_is_selected_initially` | Checklista är vald när appen öppnas. | Användaren ska landa direkt där dagens uppgifter hanteras. |
| `test_favorites_page_opens` | Användaren trycker på Snabblistan och ser Hantera favoriter. | Favoriter måste gå att nå från huvudmenyn. |
| `test_history_page_opens` | Användaren trycker på Historik och ser historiksidan. | Tidigare klara uppgifter måste gå att nå. |
| `test_later_page_opens` | Användaren trycker på Senare och ser Senare-sidan. | Uppgifter som inte gäller idag måste gå att nå. |
| `test_switches_to_work_mode` | Användaren byter till Jobb och ser jobbets checklista. | Privat och jobb måste kunna hanteras separat. |
| `test_switches_back_to_private_mode` | Användaren byter från Jobb tillbaka till Privat och ser den privata checklistan. | Växlingen måste fungera åt båda hållen utan att fastna i fel läge. |
| `test_switches_directly_from_family_back_to_private` | Användaren öppnar Familj och trycker sedan direkt på Privat utan att använda nedersta navigationen. | Familjens anslutningsvy får inte ligga kvar när huvudläget byts. |
| `test_boot_has_no_console_errors` | Appen öppnas och fungerar utan fel under starten. | Dolda startfel kan annars ge tom sida eller trasiga funktioner senare. |

### Checklista — `tests/e2e/test_checklist_page.py`

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `test_adds_item_with_enter` | Användaren skriver en uppgift, trycker Enter och ser den i listan. | Det vanligaste sättet att snabbt lägga till en uppgift måste fungera. |
| `test_blank_text_does_not_add_item` | Användaren skickar bara mellanslag och ingen uppgift skapas. | Listan ska inte fyllas med tomma rader. |
| `test_submission_trims_visible_title` | Användaren skriver extra mellanslag runt texten men ser en ren titel. | Små inmatningsmisstag ska inte ge fula eller svårjämförda uppgifter. |
| `test_submission_clears_input` | Efter att en uppgift lagts till är skrivfältet tomt. | Användaren ska direkt kunna skriva nästa uppgift. |
| `test_deletes_item` | Användaren raderar en uppgift och den försvinner. | Felaktiga eller irrelevanta uppgifter måste kunna tas bort. |
| `test_marks_item_complete` | Användaren markerar en uppgift som klar och kan se att statusen ändrats. | Checklistans viktigaste återkoppling är att en uppgift är färdig. |
| `test_marks_completed_item_undone` | Användaren ångrar en klarmarkering och uppgiften blir öppen igen. | Ett felklick måste gå att rätta till. |
| `test_moves_item_to_later` | Användaren flyttar en uppgift till Senare och den försvinner från dagens lista. | Dagens lista ska kunna rensas utan att uppgiften raderas. |
| `test_private_item_is_hidden_in_work_mode` | En privat uppgift syns inte efter byte till Jobb. | Privat information får inte blandas med jobbets lista. |
| `test_work_item_is_visible_in_work_mode` | Användaren skapar en jobbuppgift och ser den i jobbläget. | Uppgifter måste hamna i den lista användaren arbetar i. |
| `test_private_empty_state_is_visible` | En tom privat lista visar ett tydligt allt-klart-meddelande. | En tom sida ska kännas avsiktlig, inte trasig. |
| `test_work_empty_state_is_visible` | En tom jobblista visar ett tydligt allt-klart-meddelande. | Användaren ska förstå att det inte finns några jobbuppgifter. |

### Snabblistan/favoriter — `tests/e2e/test_favorites_page.py`

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `test_private_group_is_visible` | Användaren öppnar Snabblistan i privat läge och ser Privat favoriter. | Det måste vara tydligt vilken favoritsamling som redigeras. |
| `test_work_group_is_visible_after_mode_switch` | Användaren byter till Jobb och ser Jobb favoriter. | Jobbets favoriter måste vara separata och lätta att hitta. |
| `test_adds_favorite_with_enter` | Användaren skriver en favorit, trycker Enter och ser den i listan. | Återkommande uppgifter ska snabbt kunna sparas som favoriter. |
| `test_blank_favorite_is_ignored` | Tom text skapar ingen ny favorit. | Favoritlistan ska inte innehålla tomma val. |
| `test_duplicate_favorite_is_ignored` | Samma favorit skrivs in två gånger men visas bara en gång. | Dubbletter gör Snabblistan rörig och kan skapa fel uppgift. |
| `test_deletes_new_favorite` | Användaren tar bort en ny favorit och ser att den försvinner. | Favoritlistan måste kunna hållas aktuell. |
| `test_tapping_favorite_adds_checklist_item` | Användaren trycker på en favorit och hittar uppgiften i Checklista. | Hela poängen med en favorit är att snabbt skapa dagens uppgift. |
| `test_private_favorite_is_not_shown_in_work_group` | En privat favorit syns inte i jobbgruppen. | Privata och arbetsrelaterade snabbval får inte blandas. |

### Senare — `tests/e2e/test_later_page.py`

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `test_adds_private_later_item` | Användaren lägger till en privat uppgift på Senare och ser den. | Framtida privata uppgifter måste kunna sparas utanför dagens lista. |
| `test_adds_work_later_item` | Användaren lägger till en jobbuppgift på Senare och ser den. | Även framtida jobbuppgifter måste kunna planeras. |
| `test_blank_later_item_is_ignored` | Tom text skapar ingen Senare-uppgift. | Listan ska inte fyllas med tomma poster. |
| `test_deletes_later_item` | Användaren raderar en Senare-uppgift och den försvinner. | Planer som inte längre gäller måste kunna tas bort. |
| `test_promotes_later_item_to_today` | Användaren flyttar en uppgift till idag och ser den i Checklista. | En planerad uppgift måste enkelt kunna bli aktuell. |
| `test_private_later_item_is_hidden_in_work_mode` | En privat Senare-uppgift syns inte i jobbläge. | Privat och jobb måste hållas åtskilda även på Senare. |
| `test_checklist_later_button_routes_to_later_page` | Användaren skriver på Checklista, väljer `+ Senare` och hittar uppgiften på Senare-sidan. | Uppgiften måste hamna där knappen lovar, utan att tappas bort. |

### Historik — `tests/e2e/test_history_page.py`

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `test_private_empty_state` | Användaren öppnar tom privat historik och ser ett tydligt meddelande. | Användaren ska förstå att historiken är tom och inte trasig. |
| `test_work_empty_state` | Användaren öppnar tom jobbhistorik och ser ett tydligt meddelande. | Samma tydlighet behövs i jobbläget. |
| `test_history_page_has_no_restore_button_when_empty` | Ingen återställningsknapp visas när historiken är tom. | Användaren ska inte erbjudas en åtgärd som saknar mål. |

### Sparade data — `tests/e2e/test_persistence.py`

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `test_favorite_survives_reload` | Användaren skapar en favorit, laddar om sidan och ser favoriten igen. | Favoriter får inte försvinna när appen öppnas på nytt. |
| `test_checklist_item_survives_reload` | Användaren skapar en uppgift, laddar om och ser uppgiften igen. | Dagens lista måste bevaras mellan besök. |
| `test_deletion_survives_reload` | Användaren raderar en uppgift, laddar om och den förblir borta. | Raderade uppgifter får inte komma tillbaka. |
| `test_checked_state_survives_reload` | Användaren markerar en uppgift som klar, laddar om och den är fortfarande klar. | Användarens framsteg måste sparas. |
| `test_later_item_survives_reload` | Användaren skapar en Senare-uppgift, laddar om och ser den igen. | Framtida planer får inte försvinna. |
| `test_favorite_survives_new_page_in_same_context` | Användaren stänger appsidan, öppnar en ny sida och ser sin favorit igen. | Data måste överleva att användaren lämnar och återkommer till appen. |

### Responsivitet och tillgänglighet — `tests/e2e/test_responsive_accessibility.py`

#### Minsta skärm, 320 × 600

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `MinimumViewportTests.test_no_horizontal_overflow` | Sidan ryms på en mycket smal skärm utan sidledes rullning. | Innehåll och knappar ska inte hamna utanför skärmen. |
| `MinimumViewportTests.test_navigation_remains_visible` | Fliken Senare är fortfarande synlig. | Alla huvudområden måste gå att nå även på den minsta skärmen. |
| `MinimumViewportTests.test_input_remains_visible` | Fältet för nya uppgifter är synligt. | Appens huvudfunktion måste vara användbar på små mobiler. |
| `MinimumViewportTests.test_viewport_renders_a_nonempty_screenshot` | Appen visar faktiskt innehåll på skärmen. | Testet fångar en helt tom eller misslyckad rendering. |

#### Mobil, 410 × 820

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `MobileViewportTests.test_no_horizontal_overflow` | Mobilsidan ryms utan sidledes rullning. | Layouten ska kännas naturlig på en vanlig mobil. |
| `MobileViewportTests.test_all_tabs_have_accessible_names` | Alla fyra flikar har begripliga namn för hjälpmedel. | Användare med skärmläsare måste kunna förstå navigeringen. |
| `MobileViewportTests.test_primary_controls_are_keyboard_focusable` | Skrivfältet kan nås och aktiveras med tangentbord. | Appen måste gå att använda utan mus eller pekskärm. |
| `MobileViewportTests.test_viewport_renders_a_nonempty_screenshot` | Appen visar innehåll i mobilstorlek. | En tom eller misslyckad mobilrendering ska upptäckas. |

#### Surfplatta, 768 × 1024

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `TabletViewportTests.test_no_horizontal_overflow` | Surfplattelayouten ryms utan sidledes rullning. | Layouten ska fungera även mellan mobil- och skrivbordsstorlek. |
| `TabletViewportTests.test_header_is_visible` | Rubriken Gumli är synlig på surfplattan. | Användaren ska behålla orienteringen i den större layouten. |
| `TabletViewportTests.test_viewport_renders_a_nonempty_screenshot` | Appen visar innehåll i surfplattestorlek. | En tom eller misslyckad surfplatterendering ska upptäckas. |

#### Skrivbord, 1280 × 800

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `DesktopViewportTests.test_no_horizontal_overflow` | Skrivbordslayouten ryms utan onödig sidledes rullning. | Appen ska vara välordnad även på bredare skärmar. |
| `DesktopViewportTests.test_mode_buttons_are_visible` | Knapparna Privat och Jobb är synliga. | Användaren måste alltid kunna se och byta arbetsläge. |
| `DesktopViewportTests.test_long_title_does_not_create_page_overflow` | En mycket lång uppgift bryter inte sidans bredd. | Långa texter får inte göra knappar eller innehåll oåtkomliga. |
| `DesktopViewportTests.test_viewport_renders_a_nonempty_screenshot` | Appen visar innehåll i skrivbordsstorlek. | En tom eller misslyckad skrivbordsrendering ska upptäckas. |

### PWA i webbläsaren — `tests/e2e/test_pwa_runtime.py`

| Testfall | Vad användaren gör eller ser | Varför det behöver testas |
|---|---|---|
| `test_index_returns_html` | Användaren öppnar appens adress och webbläsaren får en riktig webbsida. | Fel filtyp kan ge nedladdning eller en tom sida i stället för appen. |
| `test_mjs_uses_javascript_mime_type` | Webbläsaren kan läsa appens JavaScript-del. | Fel filtyp kan stoppa appen innan något visas. |
| `test_wasm_uses_wasm_mime_type` | Webbläsaren kan läsa appens WebAssembly-del. | Fel filtyp kan göra att appens funktioner inte startar. |
| `test_manifest_is_reachable` | Webbläsaren kan hämta informationen som behövs för att installera Gumli. | Appinstallation och appidentitet är beroende av manifestet. |
| `test_service_worker_is_reachable` | Webbläsaren kan hämta appens service worker. | PWA-funktioner och säker uppdatering kräver att filen går att nå. |
| `test_service_worker_registers_in_browser` | Webbläsaren lyckas aktivera Gumlis service worker. | Appen ska fungera som PWA, inte bara som en vanlig webbsida. |
| `test_startup_milestones_are_recorded` | Diagnostiken registrerar hela kedjan från HTML-start till synlig checklista. | Prestandaförbättringar måste kunna mätas utan gissningar. |
| `test_runtime_assets_are_cached_after_warm_reload` | Efter en varm omladdning finns Flutter och Pyodide i versionscachen. | Återkommande starter ska inte vara beroende av nya stora hämtningar. |
| `test_warm_app_starts_offline` | Användaren kan öppna en tidigare startad app helt utan nätverk. | PWA-cachen måste fungera i praktiken, inte bara vara registrerad. |
| `test_app_boots_without_console_errors` | Användaren kan öppna den publicerade appen utan startfel. | Ett rent uppstartsförlopp minskar risken för tom sida och trasiga funktioner. |
