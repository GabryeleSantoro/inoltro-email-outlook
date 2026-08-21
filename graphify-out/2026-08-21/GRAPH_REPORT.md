# Graph Report - inoltro-email-outlook  (2026-08-21)

## Corpus Check
- Corpus is ~33,084 words - fits in a single context window. You may not need a graph.

## Summary
- 817 nodes · 2116 edges · 32 communities (29 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 284 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- FastAPI HTTP Server
- CLI Commands & File Check
- Text Matching & Screening Rules
- Confidence Scoring Engine
- Configuration & Settings
- Tolerant JSON Parsing
- Email Inbound Processing
- Image Processing & Resize
- Sentiment & Booking Analysis
- Email Analysis Pipeline
- Logging & Session Management
- CLI Interface & Argument Parser
- Architecture Concepts & Design Decisions
- Inbound Email Parsing
- OCR Integration Tests
- API Route Handlers
- Analysis Utility Functions
- API Response Formatting
- File Path Resolution
- HTML Body Parsing
- Main Entry Points
- Attachment Selection Logic
- Match Report Generation
- Screening Report Generation
- HTML to Text Conversion
- Email Analysis Result Model
- API Response Code Patterns
- OpenCode Plugin Integration
- Test Fixtures & Helpers
- Graphify Plugin
- Documentation Reference
- Package Root

## God Nodes (most connected - your core abstractions)
1. `Settings` - 92 edges
2. `email_payload()` - 66 edges
3. `TextExtractor` - 50 edges
4. `attachment_payload()` - 49 edges
5. `parse_email()` - 44 edges
6. `FakeOcrClient` - 43 edges
7. `EmailAnalyzer` - 42 edges
8. `make_blank_pdf()` - 33 edges
9. `analizza()` - 30 edges
10. `create_app()` - 26 edges

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
- **Design rationale decisions explaining service behavior** — concept_json_repair, concept_read_all_then_decide, concept_pdf_text_first, concept_ocr_noise_tolerance, concept_image_resize, concept_telemarketing_vs_booking, concept_dual_2xx_codes [INFERRED 0.85]
- **Production runtime dependencies** — concept_fastapi, concept_uvicorn, concept_pypdf, concept_pillow [EXTRACTED 1.00]

## Communities (32 total, 3 thin omitted)

### Community 0 - "FastAPI HTTP Server"
Cohesion: 0.05
Nodes (113): FastAPI, create_app(), Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, build(), Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fabbrica per ``uvicorn --factory``: legge la configurazione da sola., Avvia il server HTTP (bloccante) fino a Ctrl+C., run() (+105 more)

### Community 1 - "CLI Commands & File Check"
Cohesion: 0.06
Nodes (60): _cmd_check_file(), Path, Analizza un singolo file locale: utile per tarare regole e chiave API., AttachmentFile, ExtractedText, OcrResult, Allegato salvato su disco, pronto per essere analizzato., Risposta di ocr.space per un singolo file. (+52 more)

### Community 2 - "Text Matching & Screening Rules"
Cohesion: 0.05
Nodes (68): Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), Prima verifica su oggetto e corpo del messaggio., Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, ScreeningSettings, alnum_collapse(), apply_ocr_confusions() (+60 more)

### Community 3 - "Confidence Scoring Engine"
Cohesion: 0.06
Nodes (56): Match, _Accumulator, _apply_context(), _build(), _cerca_nel_testo(), _etichetta(), _find_markers(), level_for() (+48 more)

### Community 4 - "Configuration & Settings"
Cohesion: 0.10
Nodes (49): Session, ApiSettings, _as_str_list(), AttachmentSettings, _clean(), ConfigError, LoggingSettings, _normalize_extension() (+41 more)

### Community 5 - "Tolerant JSON Parsing"
Cohesion: 0.08
Nodes (35): _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le… (+27 more)

### Community 6 - "Email Inbound Processing"
Cohesion: 0.11
Nodes (30): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, Test della lettura del payload inviato da Power Automate., La foto incollata nel corpo arriva come <img src="data:...">., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment'). (+22 more)

### Community 7 - "Image Processing & Resize"
Cohesion: 0.12
Nodes (28): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+20 more)

### Community 8 - "Sentiment & Booking Analysis"
Cohesion: 0.13
Nodes (27): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., analyze_sentiment(), _booking(), _clamp(), _label() (+19 more)

### Community 9 - "Email Analysis Pipeline"
Cohesion: 0.13
Nodes (16): _describe(), EmailAnalyzer, Motivo per non leggere gli allegati, oppure None per proseguire., Logga il contenuto in ingresso per facilitare il debug del flusso., La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Indizi del punteggio in una riga, per il log., Applica screening, OCR, criteri e sentiment a una singola email., Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un… (+8 more)

### Community 10 - "Logging & Session Management"
Cohesion: 0.15
Nodes (25): datetime, prune_session_logs(), Path, Configurazione del logging: console + un file nuovo per ogni sessione. Ogni…, Da ``logs/inoltro.log`` a ``logs/inoltro-<data>-<ora>.log``. Se due sessioni…, Tiene i ``keep`` file di sessione piu' recenti, elimina gli altri. Con ``keep…, Installa gli handler sul logger radice (idempotente). Restituisce il file…, session_log_path() (+17 more)

### Community 11 - "CLI Interface & Argument Parser"
Cohesion: 0.17
Nodes (25): ArgumentParser, build_parser(), main(), config_file(), activate, fixture, MonkeyPatch, Path (+17 more)

### Community 12 - "Architecture Concepts & Design Decisions"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "Inbound Email Parsing"
Cohesion: 0.16
Nodes (22): _as_text(), _CaseInsensitive, decode_base64(), _ensure_name(), _flatten(), _from_data_uri(), _is_html_flagged(), _is_inline() (+14 more)

### Community 14 - "OCR Integration Tests"
Cohesion: 0.25
Nodes (18): image(), make_client(), no_sleep(), activate, fixture, MonkeyPatch, Path, Test del client HTTP verso ocr.space (rete simulata con `responses`). (+10 more)

### Community 15 - "API Route Handlers"
Cohesion: 0.14
Nodes (13): Request, _check_api_key(), _constant_time_equals(), _payload_to_log(), Any, Applicazione HTTP (FastAPI) interrogata da Power Automate. Un solo endpoint fa…, Confronto della chiave condivisa con Power Automate., Confronto a tempo costante: non rivela quanti caratteri combaciano. (+5 more)

### Community 16 - "Analysis Utility Functions"
Cohesion: 0.19
Nodes (14): _aggregate(), _clip(), _extend_unique(), Path, Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero…, Rende l'allegato un file su disco, pronto per l'OCR. Se il payload ne ha… (+6 more)

### Community 17 - "API Response Formatting"
Cohesion: 0.23
Nodes (14): analysis_to_dict(), _clip(), confidence_to_dict(), _criteria_to_dict(), _document_to_dict(), _evidence_to_dict(), _is_clipped(), Any (+6 more)

### Community 18 - "File Path Resolution"
Cohesion: 0.22
Nodes (10): Enum, _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path(), Origine (+2 more)

### Community 19 - "HTML Body Parsing"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 20 - "Main Entry Points"
Cohesion: 0.25
Nodes (7): Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, InboundError, ValueError, Payload non interpretabile: manca un campo o il base64 e' rotto., _cmd_analizza(), Interfaccia a riga di comando. Tre modi d'uso: * ``serve`` - avvia il servizio…, Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP.

### Community 21 - "Attachment Selection Logic"
Cohesion: 0.25
Nodes (4): Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, InboundAttachment, Allegato ricevuto da Power Automate. Arriva in due forme, entrambe supportate:…, C'e' qualcosa da leggere: byte in memoria o un file raggiungibile.

### Community 22 - "Match Report Generation"
Cohesion: 0.29
Nodes (4): _decide(), Traduce l'esito della lettura dei documenti in un esito complessivo., MatchReport, Esito del confronto fra un testo e le regole configurate.

### Community 23 - "Screening Report Generation"
Cohesion: 0.29
Nodes (4): Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza…, Prima verifica: telemedicina/televisita nell'oggetto o nel corpo., Termini riconosciuti, senza ripetizioni e in ordine stabile., ScreeningReport

### Community 24 - "HTML to Text Conversion"
Cohesion: 0.33
Nodes (6): _clean_text(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., test_html_to_text_mantiene_gli_a_capo()

### Community 25 - "Email Analysis Result Model"
Cohesion: 0.40
Nodes (3): EmailAnalysis, Risultato completo restituito dal servizio HTTP., Verdetto richiesto dal flusso: e' una prenotazione di telemedicina?

### Community 26 - "API Response Code Patterns"
Cohesion: 0.67
Nodes (4): Certainty threshold - determines 200 vs 202 response, Dual 2xx codes - avoid Power Automate error handling, HTTP 200 - certain telemedicine booking, HTTP 202 - analyzed, not a certain booking

### Community 27 - "OpenCode Plugin Integration"
Cohesion: 0.50
Nodes (3): plugin, $schema, .opencode/plugins/graphify.js

### Community 28 - "Test Fixtures & Helpers"
Cohesion: 0.50
Nodes (3): b64(), Fixture condivise: configurazione di prova, OCR fittizio, payload di esempio., test_base64_tollerante_a_spazi_e_padding()

## Knowledge Gaps
- **10 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `inoltro-email-outlook`, `AGENTS.md - graphify instructions`, `Code 1501A - telemedicine booking code` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `FastAPI HTTP Server` to `CLI Commands & File Check`, `Text Matching & Screening Rules`, `Configuration & Settings`, `Email Analysis Pipeline`, `CLI Interface & Argument Parser`, `API Route Handlers`, `Analysis Utility Functions`, `Main Entry Points`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `Tolerant JSON Parsing` to `Main Entry Points`, `API Route Handlers`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `Email Inbound Processing` to `FastAPI HTTP Server`, `Email Analysis Pipeline`, `Inbound Email Parsing`, `API Route Handlers`, `File Path Resolution`, `Main Entry Points`, `HTML to Text Conversion`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 76 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 76 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `inoltro-email-outlook` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `FastAPI HTTP Server` be split into smaller, more focused modules?**
  _Cohesion score 0.052166224580017684 - nodes in this community are weakly interconnected._