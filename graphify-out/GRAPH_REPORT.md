# Graph Report - inoltro-email-outlook  (2026-09-08)

## Corpus Check
- 51 files · ~40,758 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 977 nodes · 2452 edges · 38 communities (35 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 317 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bcab4756`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_api.py
- email_payload
- matching.py
- MatchReport
- config.py
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
- test_logging_setup.py
- analysis.py
- Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?
- Settings
- FakeOcrClient
- message_guard.py
- InboundAttachment
- Q: Diagnosi log allegato 132582.jpg senza base64 e aggiunta flag --dev per non salvare email e saltare duplicati
- Q: Tutte le email hanno allegati, cosa e andato storto nei log della run 2026-09-08 10:30
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- responses.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- models.py
- __main__.py
- InboundEmail
- Origine
- app.py

## God Nodes (most connected - your core abstractions)
1. `Settings` - 100 edges
2. `email_payload()` - 74 edges
3. `attachment_payload()` - 57 edges
4. `TextExtractor` - 55 edges
5. `FakeOcrClient` - 49 edges
6. `EmailAnalyzer` - 46 edges
7. `parse_email()` - 45 edges
8. `make_blank_pdf()` - 39 edges
9. `create_app()` - 35 edges
10. `analizza()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `analizza()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `test_allegato_illeggibile_non_blocca_la_risposta()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `test_registrazione_non_altera_il_riepilogo_analisi()` --uses--> `EmailAnalyzer`  [INFERRED]
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

## Communities (38 total, 3 thin omitted)

### Community 0 - "test_api.py"
Cohesion: 0.09
Nodes (35): LogCaptureFixture, TestClient, ocr(), _payload_del_flusso(), Test dell'endpoint HTTP interrogato da Power Automate., Un doppione non deve mai arrivare all'analizzatore/OCR., Il termine della sessione lascia un elenco leggibile, non solo righe sparse., L'allegato si legge lo stesso: e' il suo contenuto a decidere. (+27 more)

### Community 1 - "email_payload"
Cohesion: 0.10
Nodes (57): Esito, Esito complessivo dell'analisi di un messaggio., attachment_payload(), email_payload(), make_blank_pdf(), Any, Payload come quello inviato dall'azione HTTP di Power Automate., PDF senza alcun testo: simula una scansione da mandare all'OCR. (+49 more)

### Community 2 - "matching.py"
Cohesion: 0.07
Nodes (49): Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), Prima verifica su oggetto e corpo del messaggio., Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, ScreeningSettings, alnum_collapse(), apply_ocr_confusions() (+41 more)

### Community 3 - "MatchReport"
Cohesion: 0.20
Nodes (7): _aggregate(), _decide(), _extend_unique(), Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero…, Traduce l'esito della lettura dei documenti in un esito complessivo., MatchReport, Esito del confronto fra un testo e le regole configurate.

### Community 4 - "config.py"
Cohesion: 0.10
Nodes (49): ApiSettings, _as_str_list(), AttachmentSettings, _clean(), ConfigError, FlowPopupSettings, LoggingSettings, _normalize_extension() (+41 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.08
Nodes (35): _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le… (+27 more)

### Community 6 - "parse_email"
Cohesion: 0.11
Nodes (32): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, b64(), Test della lettura del payload inviato da Power Automate., La foto incollata nel corpo arriva come <img src="data:...">., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato. (+24 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.11
Nodes (30): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+22 more)

### Community 8 - "sentiment.py"
Cohesion: 0.13
Nodes (27): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., analyze_sentiment(), _booking(), _clamp(), _label() (+19 more)

### Community 9 - "._read_documents"
Cohesion: 0.24
Nodes (10): _clip(), Path, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Rende l'allegato un file su disco, pronto per l'OCR. Se il payload ne ha…, Ripulisce il nome fornito dal mittente prima di scriverlo su disco., Evita che due allegati omonimi si sovrascrivano., Restituisce un'anteprima dei log senza allagare console/file., _sanitize_filename() (+2 more)

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
Cohesion: 0.17
Nodes (20): _as_text(), _CaseInsensitive, decode_base64(), _ensure_name(), _flatten(), _is_html_flagged(), _is_inline(), _looks_like_html() (+12 more)

### Community 14 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 15 - "popup_clicker.py"
Cohesion: 0.06
Nodes (36): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+28 more)

### Community 16 - "test_logging_setup.py"
Cohesion: 0.09
Nodes (39): datetime, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola., Avvia il server HTTP (bloccante) fino a Ctrl+C. (+31 more)

### Community 17 - "analysis.py"
Cohesion: 0.05
Nodes (61): Match, _describe(), Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Indizi del punteggio in una riga, per il log., _Accumulator, _apply_context(), _build(), _cerca_nel_testo() (+53 more)

### Community 18 - "Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?, Source Nodes

### Community 19 - "Settings"
Cohesion: 0.15
Nodes (32): EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings, Ricava il testo di un allegato usando la strategia piu' economica. (+24 more)

### Community 20 - "FakeOcrClient"
Cohesion: 0.16
Nodes (32): Da dove arriva il testo di un allegato., TextSource, FakeOcrClient, make_pdf(), Fixture condivise: configurazione di prova, OCR fittizio, payload di esempio., PDF con un vero livello di testo, una pagina per elemento., Restituisce testi predefiniti per nome file e conta le chiamate., test_pdf_leggibile_unito_all_ocr_se_richiesto() (+24 more)

### Community 21 - "message_guard.py"
Cohesion: 0.13
Nodes (28): Connection, _attachment_identity(), _binary_hash(), _body_text(), _create_current_table(), _ensure_schema(), LocalMessageStore, message_fingerprint() (+20 more)

### Community 22 - "InboundAttachment"
Cohesion: 0.15
Nodes (11): _clean_text(), _from_data_uri(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., Converte un ``<img src="data:image/png;base64,...">`` in allegato., InboundAttachment (+3 more)

### Community 23 - "Q: Diagnosi log allegato 132582.jpg senza base64 e aggiunta flag --dev per non salvare email e saltare duplicati"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Diagnosi log allegato 132582.jpg senza base64 e aggiunta flag --dev per non salvare email e saltare duplicati, Source Nodes

### Community 24 - "Q: Tutte le email hanno allegati, cosa e andato storto nei log della run 2026-09-08 10:30"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Tutte le email hanno allegati, cosa e andato storto nei log della run 2026-09-08 10:30, Source Nodes

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

### Community 33 - "models.py"
Cohesion: 0.06
Nodes (46): Session, OcrSettings, _cmd_check_file(), Analizza un singolo file locale: utile per tarare regole e chiave API., AttachmentFile, ExtractedText, OcrResult, Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza… (+38 more)

### Community 34 - "__main__.py"
Cohesion: 0.22
Nodes (9): Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, InboundError, ValueError, Payload non interpretabile: manca un campo o il base64 e' rotto., _cmd_analizza(), _cmd_serve(), Path, Interfaccia a riga di comando. Tre modi d'uso: * ``serve`` - avvia il servizio… (+1 more)

### Community 36 - "InboundEmail"
Cohesion: 0.13
Nodes (10): Motivo per non leggere gli allegati, oppure None per proseguire., Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un…, InboundEmail, Identificativo usato nei log e nella risposta., Oggetto e corpo insieme: e' cio' su cui si fa la prima verifica., Polarita' del testo piu' l'intento di prenotazione. (+2 more)

### Community 37 - "Origine"
Cohesion: 0.22
Nodes (10): Enum, _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path(), Origine (+2 more)

### Community 40 - "app.py"
Cohesion: 0.07
Nodes (27): FastAPI, Request, _check_api_key(), _constant_time_equals(), _ignored_message(), _payload_to_log(), _payload_value(), Any (+19 more)

## Knowledge Gaps
- **20 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Answer` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `_read_attachments()` (3× useful, score=2.997992996)
- `parse_email()` (2× useful, score=1.998454995)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `test_api.py`, `models.py`, `__main__.py`, `matching.py`, `config.py`, `email_payload`, `app.py`, `main`, `test_logging_setup.py`, `analysis.py`, `FakeOcrClient`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `app.py`, `__main__.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 83 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09206349206349207 - nodes in this community are weakly interconnected._