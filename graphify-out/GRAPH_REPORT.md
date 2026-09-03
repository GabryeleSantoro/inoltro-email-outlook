# Graph Report - inoltro-email-outlook  (2026-09-03)

## Corpus Check
- 47 files · ~38,359 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 923 nodes · 2338 edges · 36 communities (32 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 309 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `275a93a2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_api.py
- TextExtractor
- config.py
- ConfidenceSettings
- .load
- loads_tolerant
- email_payload
- riduci_sotto
- sentiment.py
- analysis.py
- main
- trova_termini
- POST /analizza-email - main analysis endpoint
- parse_email
- OcrSpaceClient
- popup_clicker.py
- setup_logging
- Settings
- test_ocrspace.py
- app.py
- extractor.py
- message_guard.py
- EmailAnalyzer
- no_sleep
- .ensure_directories
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- responses.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- models.py
- InboundAttachment
- __main__.py

## God Nodes (most connected - your core abstractions)
1. `Settings` - 98 edges
2. `email_payload()` - 71 edges
3. `TextExtractor` - 54 edges
4. `attachment_payload()` - 54 edges
5. `FakeOcrClient` - 47 edges
6. `EmailAnalyzer` - 46 edges
7. `parse_email()` - 45 edges
8. `make_blank_pdf()` - 37 edges
9. `create_app()` - 33 edges
10. `analizza()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `analizza()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `test_allegato_illeggibile_non_blocca_la_risposta()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `client()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_api.py → src/inoltro_email/analysis.py
- `client_protetto()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_api.py → src/inoltro_email/analysis.py
- `test_allegato_indicato_per_percorso_arriva_all_ocr()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_api.py → src/inoltro_email/analysis.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Email analysis pipeline: screening -> OCR -> confidence -> response** — concept_screening, concept_ocr, concept_confidence, concept_sentiment, concept_api_analizza_email [EXTRACTED 1.00]
- **Production runtime dependencies** — concept_fastapi, concept_uvicorn, concept_pypdf, concept_pillow [EXTRACTED 1.00]
- **Design rationale decisions explaining service behavior** — concept_json_repair, concept_read_all_then_decide, concept_pdf_text_first, concept_ocr_noise_tolerance, concept_image_resize, concept_telemarketing_vs_booking, concept_dual_2xx_codes [INFERRED 0.85]

## Communities (36 total, 4 thin omitted)

### Community 0 - "test_api.py"
Cohesion: 0.08
Nodes (54): LogCaptureFixture, create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, TestClient, make_blank_pdf(), PDF senza alcun testo: simula una scansione da mandare all'OCR., _payload_del_flusso() (+46 more)

### Community 1 - "TextExtractor"
Cohesion: 0.08
Nodes (49): Enum, AttachmentFile, ExtractedText, Allegato salvato su disco, pronto per essere analizzato., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Da dove arriva il testo di un allegato., TextSource, Path (+41 more)

### Community 2 - "config.py"
Cohesion: 0.06
Nodes (64): Session, Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), ApiSettings, _as_str_list(), AttachmentSettings, _clean(), FlowPopupSettings (+56 more)

### Community 3 - "ConfidenceSettings"
Cohesion: 0.06
Nodes (56): Match, _Accumulator, _apply_context(), _build(), _cerca_nel_testo(), _etichetta(), _find_markers(), level_for() (+48 more)

### Community 4 - ".load"
Cohesion: 0.18
Nodes (33): ConfigError, Exception, Legge il YAML, unisce i segreti dall'ambiente e valida il tutto.…, Sovrascrive con l'ambiente cio' che non deve stare nel YAML., Configurazione assente, malformata o incoerente., ambiente_pulito(), fixture, MonkeyPatch (+25 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.08
Nodes (35): _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le… (+27 more)

### Community 6 - "email_payload"
Cohesion: 0.13
Nodes (25): Origine, Provenienza di un'immagine o di un documento analizzato., b64(), email_payload(), Any, Fixture condivise: configurazione di prova, OCR fittizio, payload di esempio., Payload come quello inviato dall'azione HTTP di Power Automate., Test della lettura del payload inviato da Power Automate. (+17 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.12
Nodes (28): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+20 more)

### Community 8 - "sentiment.py"
Cohesion: 0.13
Nodes (27): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., analyze_sentiment(), _booking(), _clamp(), _label() (+19 more)

### Community 9 - "analysis.py"
Cohesion: 0.13
Nodes (18): _aggregate(), _clip(), _decide(), _extend_unique(), Path, Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero… (+10 more)

### Community 10 - "main"
Cohesion: 0.17
Nodes (25): ArgumentParser, build_parser(), main(), config_file(), activate, fixture, MonkeyPatch, Path (+17 more)

### Community 11 - "trova_termini"
Cohesion: 0.12
Nodes (25): distanza_entro(), distanza_massima(), _parole(), _piu_vicina(), Riconoscimento dei termini scritti male. Le parole che contano per questo…, Termine piu' somigliante alla parola, se rientra nella tolleranza., Distanza di Damerau-Levenshtein, o None se supera ``limite``. Il calcolo si…, Quante differenze si accettano su una parola di questa lunghezza. (+17 more)

### Community 12 - "POST /analizza-email - main analysis endpoint"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "parse_email"
Cohesion: 0.05
Nodes (61): HTMLParser, LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, _as_text(), _BodyParser, _CaseInsensitive, _clean_text(), decode_base64() (+53 more)

### Community 14 - "OcrSpaceClient"
Cohesion: 0.16
Nodes (10): OcrResult, Risposta di ocr.space per un singolo file., _error_message(), OcrSpaceClient, Any, Path, Attende con backoff esponenziale. False se i tentativi sono finiti., Wrapper minimale e sincrono sull'API di ocr.space. (+2 more)

### Community 15 - "popup_clicker.py"
Cohesion: 0.07
Nodes (30): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+22 more)

### Community 16 - "setup_logging"
Cohesion: 0.09
Nodes (38): datetime, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola., Avvia il server HTTP (bloccante) fino a Ctrl+C. (+30 more)

### Community 17 - "Settings"
Cohesion: 0.13
Nodes (43): Settings, Esito, Esito complessivo dell'analisi di un messaggio., attachment_payload(), Allegato nella forma prodotta dal connettore Office 365 Outlook., analizza(), parametrize, Test del flusso completo: email -> screening -> OCR -> criteri -> sentiment. (+35 more)

### Community 18 - "test_ocrspace.py"
Cohesion: 0.35
Nodes (14): image(), make_client(), activate, Path, Test del client HTTP verso ocr.space (rete simulata con `responses`)., ocr.space segnala gli errori nel corpo, non nello status code., test_errore_applicativo_con_http_200(), test_estrae_il_testo_da_tutte_le_pagine() (+6 more)

### Community 19 - "app.py"
Cohesion: 0.11
Nodes (20): FastAPI, Request, _check_api_key(), _constant_time_equals(), _ignored_message(), _payload_to_log(), _payload_value(), Any (+12 more)

### Community 20 - "extractor.py"
Cohesion: 0.31
Nodes (6): Estrazione del testo da un allegato. Si legge sempre il modo piu' diretto per…, Lettura del testo degli allegati (ocr.space + livello testo dei PDF)., OcrSpaceError, Exception, Client HTTP per l'API di ocr.space. Documentazione: https://ocr.space/ocrapi…, Errore restituito da ocr.space o impossibilita' di contattarlo.

### Community 21 - "message_guard.py"
Cohesion: 0.16
Nodes (14): Connection, _create_current_table(), _ensure_schema(), LocalMessageStore, _migrate_to_message_key_primary_key(), Any, Path, Registro locale dei messaggi che il flusso ha gia' gestito. Il database resta… (+6 more)

### Community 22 - "EmailAnalyzer"
Cohesion: 0.12
Nodes (17): _describe(), EmailAnalyzer, Motivo per non leggere gli allegati, oppure None per proseguire., Logga il contenuto in ingresso per facilitare il debug del flusso., Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Indizi del punteggio in una riga, per il log., Applica screening, OCR, criteri e sentiment a una singola email. (+9 more)

### Community 23 - "no_sleep"
Cohesion: 0.50
Nodes (4): no_sleep(), fixture, MonkeyPatch, Azzera l'attesa fra i tentativi: i test non devono impiegare secondi.

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
Cohesion: 0.23
Nodes (14): analysis_to_dict(), _clip(), confidence_to_dict(), _criteria_to_dict(), _document_to_dict(), _evidence_to_dict(), _is_clipped(), Any (+6 more)

### Community 32 - "inspect_popup.py"
Cohesion: 0.50
Nodes (4): _dump_element(), main(), Diagnostic: dump the UIA tree of the Power Automate popup. Run this while the…, Recursive dump of a UIA element and its children.

### Community 36 - "models.py"
Cohesion: 0.29
Nodes (4): Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza…, Prima verifica: telemedicina/televisita nell'oggetto o nel corpo., Termini riconosciuti, senza ripetizioni e in ordine stabile., ScreeningReport

### Community 38 - "InboundAttachment"
Cohesion: 0.33
Nodes (3): InboundAttachment, Allegato ricevuto da Power Automate. Arriva in due forme, entrambe supportate:…, C'e' qualcosa da leggere: byte in memoria o un file raggiungibile.

### Community 39 - "__main__.py"
Cohesion: 0.24
Nodes (8): Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, _cmd_analizza(), _cmd_check_file(), _cmd_serve(), Path, Interfaccia a riga di comando. Tre modi d'uso: * ``serve`` - avvia il servizio…, Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP., Analizza un singolo file locale: utile per tarare regole e chiave API.

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Code 1501A - telemedicine booking code` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `test_api.py`, `TextExtractor`, `config.py`, `.load`, `__main__.py`, `analysis.py`, `main`, `OcrSpaceClient`, `setup_logging`, `app.py`, `extractor.py`, `EmailAnalyzer`, `.ensure_directories`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `app.py`, `__main__.py`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `parse_email` to `email_payload`, `__main__.py`, `Settings`, `app.py`, `EmailAnalyzer`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._