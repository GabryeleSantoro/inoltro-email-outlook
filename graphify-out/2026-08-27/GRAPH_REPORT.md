# Graph Report - inoltro-email-outlook  (2026-08-25)

## Corpus Check
- 45 files · ~37,452 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 902 nodes · 2260 edges · 30 communities (27 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 291 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `41d36814`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Settings
- TextExtractor
- matching.py
- ConfidenceSettings
- config.py
- loads_tolerant
- parse_email
- riduci_sotto
- sentiment.py
- EmailAnalyzer
- main
- trova_termini
- POST /analizza-email - main analysis endpoint
- inbound.py
- test_ocrspace.py
- popup_clicker.py
- setup_logging
- FakeOcrClient
- _read_path_attachments
- _BodyParser
- InboundError
- app.py
- Origine
- InboundAttachment
- Certainty threshold - determines 200 vs 202 response
- plugin
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py

## God Nodes (most connected - your core abstractions)
1. `Settings` - 95 edges
2. `email_payload()` - 68 edges
3. `TextExtractor` - 52 edges
4. `attachment_payload()` - 51 edges
5. `FakeOcrClient` - 45 edges
6. `EmailAnalyzer` - 44 edges
7. `parse_email()` - 44 edges
8. `make_blank_pdf()` - 35 edges
9. `create_app()` - 31 edges
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

## Communities (30 total, 3 thin omitted)

### Community 0 - "Settings"
Cohesion: 0.06
Nodes (103): create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings, Esito, Esito complessivo dell'analisi di un messaggio., TestClient (+95 more)

### Community 1 - "TextExtractor"
Cohesion: 0.07
Nodes (32): Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, _cmd_analizza(), _cmd_check_file(), _cmd_serve(), Path, Interfaccia a riga di comando. Tre modi d'uso: * ``serve`` - avvia il servizio…, Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP., Analizza un singolo file locale: utile per tarare regole e chiave API. (+24 more)

### Community 2 - "matching.py"
Cohesion: 0.11
Nodes (37): Prima verifica su oggetto e corpo del messaggio., Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, ScreeningSettings, alnum_collapse(), apply_ocr_confusions(), _clean(), contains_code() (+29 more)

### Community 3 - "ConfidenceSettings"
Cohesion: 0.05
Nodes (58): Match, _Accumulator, _apply_context(), _build(), _cerca_nel_testo(), _etichetta(), _find_markers(), level_for() (+50 more)

### Community 4 - "config.py"
Cohesion: 0.09
Nodes (54): Session, ApiSettings, _as_str_list(), AttachmentSettings, _clean(), ConfigError, FlowPopupSettings, LoggingSettings (+46 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.08
Nodes (35): _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le… (+27 more)

### Community 6 - "parse_email"
Cohesion: 0.11
Nodes (32): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, b64(), Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment'). (+24 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.11
Nodes (30): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+22 more)

### Community 8 - "sentiment.py"
Cohesion: 0.13
Nodes (27): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., analyze_sentiment(), _booking(), _clamp(), _label() (+19 more)

### Community 9 - "EmailAnalyzer"
Cohesion: 0.05
Nodes (56): _aggregate(), _clip(), _decide(), _describe(), EmailAnalyzer, _extend_unique(), Path, Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni… (+48 more)

### Community 10 - "main"
Cohesion: 0.17
Nodes (25): ArgumentParser, build_parser(), main(), config_file(), activate, fixture, MonkeyPatch, Path (+17 more)

### Community 11 - "trova_termini"
Cohesion: 0.12
Nodes (25): distanza_entro(), distanza_massima(), _parole(), _piu_vicina(), Riconoscimento dei termini scritti male. Le parole che contano per questo…, Termine piu' somigliante alla parola, se rientra nella tolleranza., Distanza di Damerau-Levenshtein, o None se supera ``limite``. Il calcolo si…, Quante differenze si accettano su una parola di questa lunghezza. (+17 more)

### Community 12 - "POST /analizza-email - main analysis endpoint"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "inbound.py"
Cohesion: 0.19
Nodes (18): _as_text(), _CaseInsensitive, _ensure_name(), _flatten(), _is_html_flagged(), _is_inline(), _looks_like_html(), Any (+10 more)

### Community 14 - "test_ocrspace.py"
Cohesion: 0.25
Nodes (18): image(), make_client(), no_sleep(), activate, fixture, MonkeyPatch, Path, Test del client HTTP verso ocr.space (rete simulata con `responses`). (+10 more)

### Community 15 - "popup_clicker.py"
Cohesion: 0.07
Nodes (30): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+22 more)

### Community 16 - "setup_logging"
Cohesion: 0.08
Nodes (38): build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola., Avvia il server HTTP (bloccante) fino a Ctrl+C., run() (+30 more)

### Community 17 - "FakeOcrClient"
Cohesion: 0.15
Nodes (33): Da dove arriva il testo di un allegato., TextSource, fake_ocr(), FakeOcrClient, make_pdf(), Path, Fixture condivise: configurazione di prova, OCR fittizio, payload di esempio., PDF con un vero livello di testo, una pagina per elemento. (+25 more)

### Community 18 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

### Community 19 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 20 - "InboundError"
Cohesion: 0.29
Nodes (7): decode_base64(), InboundError, ValueError, Decodifica tollerante: accetta a capo, spazi e padding mancante., Payload non interpretabile: manca un campo o il base64 e' rotto., test_email_vuota_rifiutata(), test_payload_non_oggetto_rifiutato()

### Community 21 - "app.py"
Cohesion: 0.06
Nodes (35): Connection, FastAPI, Request, _check_api_key(), _constant_time_equals(), _ignored_message(), _payload_to_log(), _payload_value() (+27 more)

### Community 23 - "Origine"
Cohesion: 0.25
Nodes (8): Enum, Origine, Provenienza di un'immagine o di un documento analizzato., str, La foto incollata nel corpo arriva come <img src="data:...">., test_allegati_decodificati(), test_allegato_inline_marcato_come_foto_del_corpo(), test_immagine_data_uri_nel_corpo_diventa_allegato()

### Community 24 - "InboundAttachment"
Cohesion: 0.15
Nodes (11): _clean_text(), _from_data_uri(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., Converte un ``<img src="data:image/png;base64,...">`` in allegato., InboundAttachment (+3 more)

### Community 26 - "Certainty threshold - determines 200 vs 202 response"
Cohesion: 0.67
Nodes (4): Certainty threshold - determines 200 vs 202 response, Dual 2xx codes - avoid Power Automate error handling, HTTP 200 - certain telemedicine booking, HTTP 202 - analyzed, not a certain booking

### Community 27 - "plugin"
Cohesion: 0.40
Nodes (4): plugin, $schema, opencode-mem, .opencode/plugins/graphify.js

### Community 32 - "inspect_popup.py"
Cohesion: 0.50
Nodes (4): _dump_element(), main(), Diagnostic: dump the UIA tree of the Power Automate popup. Run this while the…, Recursive dump of a UIA element and its children.

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Code 1501A - telemedicine booking code` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `TextExtractor`, `config.py`, `EmailAnalyzer`, `main`, `setup_logging`, `FakeOcrClient`, `app.py`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `TextExtractor`, `app.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `parse_email` to `Settings`, `TextExtractor`, `EmailAnalyzer`, `inbound.py`, `_read_path_attachments`, `InboundError`, `app.py`, `Origine`, `InboundAttachment`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._