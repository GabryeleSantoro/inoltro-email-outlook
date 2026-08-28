# Graph Report - inoltro-email-outlook  (2026-08-27)

## Corpus Check
- 46 files · ~38,031 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 919 nodes · 2301 edges · 37 communities (34 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 298 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8464487d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Settings
- TextExtractor
- config.py
- ConfidenceSettings
- .load
- loads_tolerant
- parse_email
- riduci_sotto
- sentiment.py
- analysis.py
- main
- trova_termini
- POST /analizza-email - main analysis endpoint
- inbound.py
- test_ocrspace.py
- popup_clicker.py
- setup_logging
- confidence.py
- _read_path_attachments
- _BodyParser
- InboundError
- app.py
- EmailAnalyzer
- Origine
- _parse_html_body
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- responses.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- _Accumulator
- InboundEmail
- InboundAttachment
- models.py

## God Nodes (most connected - your core abstractions)
1. `Settings` - 96 edges
2. `email_payload()` - 69 edges
3. `TextExtractor` - 53 edges
4. `attachment_payload()` - 52 edges
5. `FakeOcrClient` - 46 edges
6. `EmailAnalyzer` - 45 edges
7. `parse_email()` - 44 edges
8. `make_blank_pdf()` - 36 edges
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

## Communities (37 total, 3 thin omitted)

### Community 0 - "Settings"
Cohesion: 0.06
Nodes (106): LogCaptureFixture, create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings, Esito, Esito complessivo dell'analisi di un messaggio. (+98 more)

### Community 1 - "TextExtractor"
Cohesion: 0.06
Nodes (59): AttachmentFile, ExtractedText, OcrResult, Allegato salvato su disco, pronto per essere analizzato., Risposta di ocr.space per un singolo file., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Da dove arriva il testo di un allegato., TextSource (+51 more)

### Community 2 - "config.py"
Cohesion: 0.06
Nodes (59): Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, Session, ApiSettings, _as_str_list(), AttachmentSettings, FlowPopupSettings, LoggingSettings, _normalize_extension() (+51 more)

### Community 3 - "ConfidenceSettings"
Cohesion: 0.12
Nodes (34): _build(), level_for(), Quanto e' sicuro che il messaggio riguardi la telemedicina. ``document_text``,…, Etichetta leggibile della percentuale, per chi non vuole leggere i numeri., score_telemedicine(), ConfidenceSettings, Soglie e taratura delle percentuali di sicurezza., impostazioni() (+26 more)

### Community 4 - ".load"
Cohesion: 0.15
Nodes (36): _clean(), ConfigError, Exception, Path, Legge il YAML, unisce i segreti dall'ambiente e valida il tutto.…, Sovrascrive con l'ambiente cio' che non deve stare nel YAML., Configurazione assente, malformata o incoerente., _read_yaml() (+28 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.07
Nodes (37): _cmd_analizza(), Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP., _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError (+29 more)

### Community 6 - "parse_email"
Cohesion: 0.12
Nodes (30): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment')., Servizio su un'altra macchina: il file si cerca nelle cartelle indicate. (+22 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.12
Nodes (28): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+20 more)

### Community 8 - "sentiment.py"
Cohesion: 0.13
Nodes (27): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., analyze_sentiment(), _booking(), _clamp(), _label() (+19 more)

### Community 9 - "analysis.py"
Cohesion: 0.12
Nodes (20): _aggregate(), _clip(), _decide(), _extend_unique(), Path, Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero… (+12 more)

### Community 10 - "main"
Cohesion: 0.17
Nodes (25): ArgumentParser, build_parser(), main(), config_file(), activate, fixture, MonkeyPatch, Path (+17 more)

### Community 11 - "trova_termini"
Cohesion: 0.10
Nodes (29): Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), normalize(), Minuscolo, senza accenti, con gli spazi collassati., distanza_entro(), distanza_massima(), _parole(), _piu_vicina() (+21 more)

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

### Community 17 - "confidence.py"
Cohesion: 0.11
Nodes (18): Match, _apply_context(), _cerca_nel_testo(), _etichetta(), _find_markers(), Percentuale di sicurezza: e' telemedicina? e' una prenotazione? Il servizio non…, Quanto e' sicuro che il messaggio sia una prenotazione di telemedicina. Il…, Applica gli indizi di contesto, che valgono solo scritti per esteso. Non… (+10 more)

### Community 18 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

### Community 19 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 20 - "InboundError"
Cohesion: 0.22
Nodes (9): decode_base64(), InboundError, ValueError, Decodifica tollerante: accetta a capo, spazi e padding mancante., Payload non interpretabile: manca un campo o il base64 e' rotto., b64(), test_base64_tollerante_a_spazi_e_padding(), test_email_vuota_rifiutata() (+1 more)

### Community 21 - "app.py"
Cohesion: 0.06
Nodes (35): Connection, FastAPI, Request, _check_api_key(), _constant_time_equals(), _ignored_message(), _payload_to_log(), _payload_value() (+27 more)

### Community 22 - "EmailAnalyzer"
Cohesion: 0.16
Nodes (12): _describe(), EmailAnalyzer, Motivo per non leggere gli allegati, oppure None per proseguire., Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Indizi del punteggio in una riga, per il log., Applica screening, OCR, criteri e sentiment a una singola email., Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un… (+4 more)

### Community 23 - "Origine"
Cohesion: 0.25
Nodes (8): Enum, Origine, Provenienza di un'immagine o di un documento analizzato., str, La foto incollata nel corpo arriva come <img src="data:...">., test_allegati_decodificati(), test_allegato_inline_marcato_come_foto_del_corpo(), test_immagine_data_uri_nel_corpo_diventa_allegato()

### Community 24 - "_parse_html_body"
Cohesion: 0.25
Nodes (8): _clean_text(), _from_data_uri(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., Converte un ``<img src="data:image/png;base64,...">`` in allegato., test_html_to_text_mantiene_gli_a_capo()

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

### Community 33 - "_Accumulator"
Cohesion: 0.25
Nodes (4): _Accumulator, Somma i pesi degli indizi tenendo l'elenco di cio' che ha contato., Evidence, Un singolo indizio che sposta la percentuale di sicurezza. ``weight`` e'…

### Community 34 - "InboundEmail"
Cohesion: 0.25
Nodes (5): Logga il contenuto in ingresso per facilitare il debug del flusso., InboundEmail, Identificativo usato nei log e nella risposta., Oggetto e corpo insieme: e' cio' su cui si fa la prima verifica., Email singola inviata dal flusso Power Automate. ``body_text`` e' sempre testo…

### Community 35 - "InboundAttachment"
Cohesion: 0.29
Nodes (3): InboundAttachment, Allegato ricevuto da Power Automate. Arriva in due forme, entrambe supportate:…, C'e' qualcosa da leggere: byte in memoria o un file raggiungibile.

### Community 36 - "models.py"
Cohesion: 0.29
Nodes (4): Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza…, Prima verifica: telemedicina/televisita nell'oggetto o nel corpo., Termini riconosciuti, senza ripetizioni e in ordine stabile., ScreeningReport

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Code 1501A - telemedicine booking code` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `TextExtractor`, `config.py`, `.load`, `loads_tolerant`, `analysis.py`, `main`, `setup_logging`, `app.py`, `EmailAnalyzer`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `config.py`, `app.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `parse_email` to `Settings`, `InboundEmail`, `config.py`, `loads_tolerant`, `inbound.py`, `_read_path_attachments`, `InboundError`, `app.py`, `Origine`, `_parse_html_body`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._