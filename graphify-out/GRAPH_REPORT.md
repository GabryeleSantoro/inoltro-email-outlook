# Graph Report - inoltro-email-outlook  (2026-09-04)

## Corpus Check
- 48 files · ~39,577 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 953 nodes · 2413 edges · 46 communities (43 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 313 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7e322c0b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- email_payload
- FakeOcrClient
- matching.py
- MatchReport
- .load
- loads_tolerant
- parse_email
- riduci_sotto
- sentiment.py
- ._read_documents
- main
- trova_termini
- POST /analizza-email - main analysis endpoint
- inbound.py
- _BodyParser
- popup_clicker.py
- setup_logging
- ConfidenceSettings
- test_ocrspace.py
- app.py
- test_api.py
- message_guard.py
- InboundAttachment
- models.py
- Settings
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- responses.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- OcrSpaceClient
- InboundError
- __main__.py
- InboundEmail
- _read_path_attachments
- extractor.py
- score_booking
- FintoPulsante
- ConfidenceScore
- confidence.py
- score_telemedicine
- _read_email_request
- analysis.py

## God Nodes (most connected - your core abstractions)
1. `Settings` - 99 edges
2. `email_payload()` - 72 edges
3. `attachment_payload()` - 55 edges
4. `TextExtractor` - 54 edges
5. `FakeOcrClient` - 48 edges
6. `EmailAnalyzer` - 46 edges
7. `parse_email()` - 45 edges
8. `make_blank_pdf()` - 38 edges
9. `create_app()` - 34 edges
10. `analizza()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `analizza()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `test_allegato_illeggibile_non_blocca_la_risposta()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `client()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_api.py → src/inoltro_email/analysis.py
- `settings()` --uses--> `ApiSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `OcrSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Email analysis pipeline: screening -> OCR -> confidence -> response** — concept_screening, concept_ocr, concept_confidence, concept_sentiment, concept_api_analizza_email [EXTRACTED 1.00]
- **Production runtime dependencies** — concept_fastapi, concept_uvicorn, concept_pypdf, concept_pillow [EXTRACTED 1.00]
- **Design rationale decisions explaining service behavior** — concept_json_repair, concept_read_all_then_decide, concept_pdf_text_first, concept_ocr_noise_tolerance, concept_image_resize, concept_telemarketing_vs_booking, concept_dual_2xx_codes [INFERRED 0.85]

## Communities (46 total, 3 thin omitted)

### Community 0 - "email_payload"
Cohesion: 0.10
Nodes (60): Esito, Esito complessivo dell'analisi di un messaggio., attachment_payload(), b64(), email_payload(), make_blank_pdf(), make_pdf(), Any (+52 more)

### Community 1 - "FakeOcrClient"
Cohesion: 0.19
Nodes (28): Da dove arriva il testo di un allegato., TextSource, FakeOcrClient, Restituisce testi predefiniti per nome file e conta le chiamate., attachment_from(), Path, Test della scelta della strategia di lettura degli allegati., Una foto di impegnativa supera sempre il MB: si riduce, non si salta. (+20 more)

### Community 2 - "matching.py"
Cohesion: 0.07
Nodes (49): Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), Prima verifica su oggetto e corpo del messaggio., Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, ScreeningSettings, alnum_collapse(), apply_ocr_confusions() (+41 more)

### Community 3 - "MatchReport"
Cohesion: 0.15
Nodes (8): _aggregate(), _extend_unique(), La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero…, AttachmentAnalysis, MatchReport, Esito del confronto fra un testo e le regole configurate., Esito della lettura di un singolo allegato o di una foto del corpo.

### Community 4 - ".load"
Cohesion: 0.11
Nodes (45): ApiSettings, _as_str_list(), AttachmentSettings, _clean(), ConfigError, FlowPopupSettings, LoggingSettings, Any (+37 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.08
Nodes (35): _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le… (+27 more)

### Community 6 - "parse_email"
Cohesion: 0.12
Nodes (30): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment')., Servizio su un'altra macchina: il file si cerca nelle cartelle indicate. (+22 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.11
Nodes (30): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+22 more)

### Community 8 - "sentiment.py"
Cohesion: 0.12
Nodes (29): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., Polarita' del testo piu' l'intento di prenotazione., SentimentScore, analyze_sentiment(), _booking() (+21 more)

### Community 9 - "._read_documents"
Cohesion: 0.31
Nodes (8): Path, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Rende l'allegato un file su disco, pronto per l'OCR. Se il payload ne ha…, Ripulisce il nome fornito dal mittente prima di scriverlo su disco., Evita che due allegati omonimi si sovrascrivano., _sanitize_filename(), _unique_path(), _write_to_disk()

### Community 10 - "main"
Cohesion: 0.18
Nodes (23): ArgumentParser, build_parser(), main(), config_file(), activate, fixture, MonkeyPatch, Path (+15 more)

### Community 11 - "trova_termini"
Cohesion: 0.12
Nodes (25): distanza_entro(), distanza_massima(), _parole(), _piu_vicina(), Riconoscimento dei termini scritti male. Le parole che contano per questo…, Termine piu' somigliante alla parola, se rientra nella tolleranza., Distanza di Damerau-Levenshtein, o None se supera ``limite``. Il calcolo si…, Quante differenze si accettano su una parola di questa lunghezza. (+17 more)

### Community 12 - "POST /analizza-email - main analysis endpoint"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "inbound.py"
Cohesion: 0.19
Nodes (18): _as_text(), _CaseInsensitive, _ensure_name(), _flatten(), _is_html_flagged(), _is_inline(), _looks_like_html(), Any (+10 more)

### Community 14 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 15 - "popup_clicker.py"
Cohesion: 0.07
Nodes (32): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+24 more)

### Community 16 - "setup_logging"
Cohesion: 0.12
Nodes (30): datetime, prune_session_logs(), Path, Configurazione del logging: console + un file nuovo per ogni sessione. Ogni…, Da ``logs/inoltro.log`` a ``logs/inoltro-<data>-<ora>.log``. Se due sessioni…, Tiene i ``keep`` file di sessione piu' recenti, elimina gli altri. Con ``keep…, Installa gli handler sul logger radice (idempotente). Restituisce il file…, session_log_path() (+22 more)

### Community 17 - "ConfidenceSettings"
Cohesion: 0.19
Nodes (22): ConfidenceSettings, Soglie e taratura delle percentuali di sicurezza., impostazioni(), _percentuali(), fixture, parametrize, Test delle percentuali di sicurezza. I casi non sono inventati: sono i messaggi…, Chi legge la risposta deve vedere cosa e' stato interpretato e come. (+14 more)

### Community 18 - "test_ocrspace.py"
Cohesion: 0.19
Nodes (20): Session, OcrSettings, image(), make_client(), no_sleep(), activate, fixture, MonkeyPatch (+12 more)

### Community 19 - "app.py"
Cohesion: 0.20
Nodes (9): FastAPI, _check_api_key(), _constant_time_equals(), _ignored_message(), Applicazione HTTP (FastAPI) interrogata da Power Automate. ``POST /analizza-…, Confronto della chiave condivisa con Power Automate., Confronto a tempo costante: non rivela quanti caratteri combaciano., Risposta 2xx: il flow puo' ignorarla senza ritentare la HTTP action. (+1 more)

### Community 20 - "test_api.py"
Cohesion: 0.11
Nodes (28): TestClient, client(), ocr(), _payload_del_flusso(), fixture, Test dell'endpoint HTTP interrogato da Power Automate., Un doppione non deve mai arrivare all'analizzatore/OCR., Applicazione con OCR fittizio: nessuna chiamata di rete nei test. (+20 more)

### Community 21 - "message_guard.py"
Cohesion: 0.13
Nodes (28): Connection, _attachment_identity(), _binary_hash(), _body_text(), _create_current_table(), _ensure_schema(), LocalMessageStore, message_fingerprint() (+20 more)

### Community 22 - "InboundAttachment"
Cohesion: 0.15
Nodes (11): _clean_text(), _from_data_uri(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., Converte un ``<img src="data:image/png;base64,...">`` in allegato., InboundAttachment (+3 more)

### Community 23 - "models.py"
Cohesion: 0.18
Nodes (11): Enum, Origine, Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza…, Provenienza di un'immagine o di un documento analizzato., str, La foto incollata nel corpo arriva come <img src="data:...">., PAD serializza gli oggetti del connettore in ``Properties``., test_allegati_decodificati() (+3 more)

### Community 24 - "Settings"
Cohesion: 0.15
Nodes (31): LogCaptureFixture, EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings (+23 more)

### Community 25 - "EmailAnalysis"
Cohesion: 0.14
Nodes (11): Logger, EmailAnalysis, Risultato completo restituito dal servizio HTTP., Verdetto richiesto dal flusso: e' una prenotazione di telemedicina?, EmailSessionReport, Registro in memoria delle email gestite nella singola sessione HTTP., Una riga del riepilogo di una sessione del servizio., Raccoglie esiti HTTP e li stampa ordinati allo spegnimento dell'app. (+3 more)

### Community 26 - "Certainty threshold - determines 200 vs 202 response"
Cohesion: 0.67
Nodes (4): Certainty threshold - determines 200 vs 202 response, Dual 2xx codes - avoid Power Automate error handling, HTTP 200 - certain telemedicine booking, HTTP 202 - analyzed, not a certain booking

### Community 27 - "plugin"
Cohesion: 0.40
Nodes (4): plugin, $schema, opencode-mem, .opencode/plugins/graphify.js

### Community 28 - "responses.py"
Cohesion: 0.31
Nodes (12): analysis_to_dict(), _clip(), confidence_to_dict(), _criteria_to_dict(), _document_to_dict(), _evidence_to_dict(), _is_clipped(), Any (+4 more)

### Community 32 - "inspect_popup.py"
Cohesion: 0.50
Nodes (4): _dump_element(), main(), Diagnostic: dump the UIA tree of the Power Automate popup. Run this while the…, Recursive dump of a UIA element and its children.

### Community 33 - "OcrSpaceClient"
Cohesion: 0.13
Nodes (15): OcrResult, Risposta di ocr.space per un singolo file., Lettura del testo degli allegati (ocr.space + livello testo dei PDF)., _error_message(), OcrSpaceClient, OcrSpaceError, Any, Exception (+7 more)

### Community 34 - "InboundError"
Cohesion: 0.25
Nodes (8): decode_base64(), InboundError, ValueError, Decodifica tollerante: accetta a capo, spazi e padding mancante., Payload non interpretabile: manca un campo o il base64 e' rotto., test_base64_tollerante_a_spazi_e_padding(), test_email_vuota_rifiutata(), test_payload_non_oggetto_rifiutato()

### Community 35 - "__main__.py"
Cohesion: 0.14
Nodes (16): Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola., Avvia il server HTTP (bloccante) fino a Ctrl+C. (+8 more)

### Community 36 - "InboundEmail"
Cohesion: 0.12
Nodes (12): _clip(), _decide(), Motivo per non leggere gli allegati, oppure None per proseguire., Logga il contenuto in ingresso per facilitare il debug del flusso., Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, Traduce l'esito della lettura dei documenti in un esito complessivo., Restituisce un'anteprima dei log senza allagare console/file., Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un… (+4 more)

### Community 37 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

### Community 38 - "extractor.py"
Cohesion: 0.18
Nodes (8): AttachmentFile, ExtractedText, Allegato salvato su disco, pronto per essere analizzato., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Path, Estrazione del testo da un allegato. Si legge sempre il modo piu' diretto per…, Manda il PDF a ocr.space, a blocchi se supera i limiti del piano., Spezza il PDF in blocchi di pagine e concatena i testi riconosciuti.

### Community 39 - "score_booking"
Cohesion: 0.17
Nodes (9): _apply_context(), Quanto e' sicuro che il messaggio sia una prenotazione di telemedicina. Il…, Applica gli indizi di contesto, che valgono solo scritti per esteso. Non…, Un testo senza zone: il contenuto di un documento letto dall'OCR. Non si divide…, Il testo diviso nelle zone che pesano in modo diverso. Ogni zona viene cercata…, Prima zona in cui compare il termine. Restituisce ``(zona, forma scorretta)``:…, score_booking(), _TestoPiano (+1 more)

### Community 40 - "FintoPulsante"
Cohesion: 0.19
Nodes (5): Servizio HTTP di analisi delle email di telemedicina. Riceve da Power Automate…, FintoPulsante, test_click_input_e_successo_solo_se_conferma_si_chiude(), test_click_input_non_e_successo_se_conferma_resta_visibile(), test_verifica_esterna_evita_loop_con_wrapper_uia_obsoleto()

### Community 41 - "ConfidenceScore"
Cohesion: 0.20
Nodes (6): _Accumulator, Somma i pesi degli indizi tenendo l'elenco di cio' che ha contato., ConfidenceScore, Evidence, Un singolo indizio che sposta la percentuale di sicurezza. ``weight`` e'…, Quanto il servizio e' sicuro di un'affermazione, in percentuale.

### Community 42 - "confidence.py"
Cohesion: 0.22
Nodes (10): Match, _build(), _cerca_nel_testo(), _find_markers(), level_for(), Percentuale di sicurezza: e' telemedicina? e' una prenotazione? Il servizio non…, Primo termine di telemedicina in un testo senza zone (nomi, documenti)., Separa cio' che ha scritto il mittente dalla parte citata o inoltrata. (+2 more)

### Community 43 - "score_telemedicine"
Cohesion: 0.18
Nodes (11): _etichetta(), Quanto e' sicuro che il messaggio riguardi la telemedicina. ``document_text``,…, Etichetta dell'indizio, con la forma davvero letta se era scorretta., score_telemedicine(), L'OCR sbaglia proprio questi termini: la tolleranza serve soprattutto qui., L'oggetto generico non deve affossare un corpo esplicito., telemedicina@aslsalerno.it" fra i destinatari non e' l'argomento., test_oggetto_esplicito_da_sicurezza_alta() (+3 more)

### Community 44 - "_read_email_request"
Cohesion: 0.27
Nodes (10): Request, _payload_to_log(), _payload_value(), Any, Legge pochi campi del JSON senza costruire l'email o gli allegati., Legge e valida il payload condiviso dagli endpoint email., Legge il corpo della richiesta e lo interpreta. Restituisce ``(payload,…, Serializza un payload in modo robusto per il logging di debug. (+2 more)

### Community 45 - "analysis.py"
Cohesion: 0.25
Nodes (7): _describe(), Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Indizi del punteggio in una riga, per il log., _normalize_extension(), Caricamento e validazione della configurazione. La configurazione arriva da due…, Tiene solo i formati che il servizio sa davvero leggere. La configurazione puo'…, _supported_only()

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Code 1501A - telemedicine booking code` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `email_payload`, `FakeOcrClient`, `matching.py`, `__main__.py`, `.load`, `extractor.py`, `main`, `_read_email_request`, `analysis.py`, `setup_logging`, `app.py`, `test_api.py`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `__main__.py`, `app.py`, `_read_email_request`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 82 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 82 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 17 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `email_payload` be split into smaller, more focused modules?**
  _Cohesion score 0.09624537281861449 - nodes in this community are weakly interconnected._