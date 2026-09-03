# Graph Report - inoltro-email-outlook  (2026-09-03)

## Corpus Check
- 47 files · ~39,123 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 940 nodes · 2396 edges · 39 communities (35 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 313 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dc7a136b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- email_payload
- TextExtractor
- config.py
- MatchReport
- Settings
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
- __main__.py
- analysis.py
- test_ocrspace.py
- app.py
- make_blank_pdf
- message_guard.py
- InboundAttachment
- models.py
- test_api.py
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- responses.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- OcrSpaceClient
- _cmd_analizza
- _parse_html_body
- InboundEmail
- _read_path_attachments
- fake_ocr

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
- `make_client()` --uses--> `OcrSettings`  [INFERRED]
  tests/test_ocrspace.py → src/inoltro_email/config.py
- `settings()` --uses--> `SentimentSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `Settings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Email analysis pipeline: screening -> OCR -> confidence -> response** — concept_screening, concept_ocr, concept_confidence, concept_sentiment, concept_api_analizza_email [EXTRACTED 1.00]
- **Production runtime dependencies** — concept_fastapi, concept_uvicorn, concept_pypdf, concept_pillow [EXTRACTED 1.00]
- **Design rationale decisions explaining service behavior** — concept_json_repair, concept_read_all_then_decide, concept_pdf_text_first, concept_ocr_noise_tolerance, concept_image_resize, concept_telemarketing_vs_booking, concept_dual_2xx_codes [INFERRED 0.85]

## Communities (39 total, 4 thin omitted)

### Community 0 - "email_payload"
Cohesion: 0.11
Nodes (51): Esito, Esito complessivo dell'analisi di un messaggio., attachment_payload(), email_payload(), Any, Payload come quello inviato dall'azione HTTP di Power Automate., Allegato nella forma prodotta dal connettore Office 365 Outlook., analizza() (+43 more)

### Community 1 - "TextExtractor"
Cohesion: 0.09
Nodes (43): _cmd_check_file(), Path, Analizza un singolo file locale: utile per tarare regole e chiave API., AttachmentFile, ExtractedText, Allegato salvato su disco, pronto per essere analizzato., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Da dove arriva il testo di un allegato. (+35 more)

### Community 2 - "config.py"
Cohesion: 0.06
Nodes (64): Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), ApiSettings, _as_str_list(), AttachmentSettings, _clean(), FlowPopupSettings, LoggingSettings (+56 more)

### Community 3 - "MatchReport"
Cohesion: 0.17
Nodes (9): _aggregate(), _decide(), _extend_unique(), Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero…, Traduce l'esito della lettura dei documenti in un esito complessivo., AttachmentAnalysis, MatchReport, Esito del confronto fra un testo e le regole configurate. (+1 more)

### Community 4 - "Settings"
Cohesion: 0.16
Nodes (38): Avvia il server HTTP (bloccante) fino a Ctrl+C., run(), ConfigError, Exception, Legge il YAML, unisce i segreti dall'ambiente e valida il tutto.…, Sovrascrive con l'ambiente cio' che non deve stare nel YAML., Crea la cartella dei log: il primo avvio non fallisce., Configurazione assente, malformata o incoerente. (+30 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.08
Nodes (35): _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le… (+27 more)

### Community 6 - "parse_email"
Cohesion: 0.11
Nodes (29): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, b64(), Fixture condivise: configurazione di prova, OCR fittizio, payload di esempio., Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato. (+21 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.12
Nodes (28): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+20 more)

### Community 8 - "sentiment.py"
Cohesion: 0.12
Nodes (29): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., Polarita' del testo piu' l'intento di prenotazione., SentimentScore, analyze_sentiment(), _booking() (+21 more)

### Community 9 - "._read_documents"
Cohesion: 0.24
Nodes (10): _clip(), Path, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Rende l'allegato un file su disco, pronto per l'OCR. Se il payload ne ha…, Ripulisce il nome fornito dal mittente prima di scriverlo su disco., Evita che due allegati omonimi si sovrascrivano., Restituisce un'anteprima dei log senza allagare console/file., _sanitize_filename() (+2 more)

### Community 10 - "main"
Cohesion: 0.16
Nodes (27): ArgumentParser, build_parser(), main(), make_pdf(), PDF con un vero livello di testo, una pagina per elemento., config_file(), activate, fixture (+19 more)

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
Cohesion: 0.25
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 15 - "popup_clicker.py"
Cohesion: 0.07
Nodes (30): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+22 more)

### Community 16 - "__main__.py"
Cohesion: 0.09
Nodes (38): datetime, Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola. (+30 more)

### Community 17 - "analysis.py"
Cohesion: 0.05
Nodes (61): Match, _describe(), Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Indizi del punteggio in una riga, per il log., _Accumulator, _apply_context(), _build(), _cerca_nel_testo() (+53 more)

### Community 18 - "test_ocrspace.py"
Cohesion: 0.25
Nodes (18): image(), make_client(), no_sleep(), activate, fixture, MonkeyPatch, Path, Test del client HTTP verso ocr.space (rete simulata con `responses`). (+10 more)

### Community 19 - "app.py"
Cohesion: 0.11
Nodes (20): FastAPI, Request, _check_api_key(), _constant_time_equals(), _ignored_message(), _payload_to_log(), _payload_value(), Any (+12 more)

### Community 20 - "make_blank_pdf"
Cohesion: 0.20
Nodes (10): make_blank_pdf(), PDF senza alcun testo: simula una scansione da mandare all'OCR., Un doppione non deve mai arrivare all'analizzatore/OCR., L'allegato si legge lo stesso: e' il suo contenuto a decidere., test_duecento_solo_per_una_prenotazione_certa(), test_email_conforme(), test_email_fuori_tema_letta_comunque(), test_email_gia_registrata_non_viene_analizzata() (+2 more)

### Community 21 - "message_guard.py"
Cohesion: 0.11
Nodes (31): Connection, html_to_text(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., _attachment_identity(), _binary_hash(), _body_text(), _create_current_table(), _ensure_schema() (+23 more)

### Community 22 - "InboundAttachment"
Cohesion: 0.25
Nodes (4): Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, InboundAttachment, Allegato ricevuto da Power Automate. Arriva in due forme, entrambe supportate:…, C'e' qualcosa da leggere: byte in memoria o un file raggiungibile.

### Community 23 - "models.py"
Cohesion: 0.12
Nodes (18): Enum, OcrResult, Origine, Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza…, Risposta di ocr.space per un singolo file., Provenienza di un'immagine o di un documento analizzato., Estrazione del testo da un allegato. Si legge sempre il modo piu' diretto per…, Lettura del testo degli allegati (ocr.space + livello testo dei PDF). (+10 more)

### Community 24 - "test_api.py"
Cohesion: 0.08
Nodes (53): LogCaptureFixture, EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, TestClient, client() (+45 more)

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
Cohesion: 0.18
Nodes (8): Session, _error_message(), OcrSpaceClient, Any, Path, Attende con backoff esponenziale. False se i tentativi sono finiti., Wrapper minimale e sincrono sull'API di ocr.space., Manda un file a ocr.space e restituisce il testo riconosciuto. Sollevare…

### Community 34 - "_cmd_analizza"
Cohesion: 0.29
Nodes (7): InboundError, ValueError, Payload non interpretabile: manca un campo o il base64 e' rotto., _cmd_analizza(), Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP., test_email_vuota_rifiutata(), test_payload_non_oggetto_rifiutato()

### Community 35 - "_parse_html_body"
Cohesion: 0.29
Nodes (7): _clean_text(), decode_base64(), _from_data_uri(), _parse_html_body(), Normalizza spazi e a capo: il testo va poi a regole e sentiment., Converte un ``<img src="data:image/png;base64,...">`` in allegato., Decodifica tollerante: accetta a capo, spazi e padding mancante.

### Community 36 - "InboundEmail"
Cohesion: 0.15
Nodes (8): Motivo per non leggere gli allegati, oppure None per proseguire., Logga il contenuto in ingresso per facilitare il debug del flusso., La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un…, InboundEmail, Identificativo usato nei log e nella risposta., Oggetto e corpo insieme: e' cio' su cui si fa la prima verifica., Email singola inviata dal flusso Power Automate. ``body_text`` e' sempre testo…

### Community 37 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Code 1501A - telemedicine booking code` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `email_payload`, `TextExtractor`, `config.py`, `_cmd_analizza`, `OcrSpaceClient`, `main`, `__main__.py`, `analysis.py`, `app.py`, `make_blank_pdf`, `models.py`, `test_api.py`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `__main__.py`, `_cmd_analizza`, `app.py`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `parse_email` to `email_payload`, `_cmd_analizza`, `_parse_html_body`, `InboundEmail`, `_read_path_attachments`, `inbound.py`, `__main__.py`, `app.py`, `models.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 82 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 82 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 17 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._