# Graph Report - inoltro-email-outlook  (2026-09-10)

## Corpus Check
- 51 files · ~40,981 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 980 nodes · 2464 edges · 42 communities (38 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 321 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `059e979d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- confidence.py
- Settings
- matching.py
- test_ocrspace.py
- config.py
- loads_tolerant
- parse_email
- riduci_sotto
- sentiment.py
- analysis.py
- main
- FintoPulsante
- POST /analizza-email - main analysis endpoint
- inbound.py
- _BodyParser
- popup_clicker.py
- test_logging_setup.py
- ConfidenceSettings
- Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?
- Origine
- conftest.py
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
- TextExtractor
- _cmd_analizza
- _Accumulator
- InboundEmail
- _read_path_attachments
- _parse_html_body
- _check_api_key
- app.py
- .log_summary

## God Nodes (most connected - your core abstractions)
1. `Settings` - 101 edges
2. `email_payload()` - 74 edges
3. `attachment_payload()` - 57 edges
4. `TextExtractor` - 56 edges
5. `FakeOcrClient` - 50 edges
6. `EmailAnalyzer` - 47 edges
7. `parse_email()` - 45 edges
8. `make_blank_pdf()` - 39 edges
9. `create_app()` - 36 edges
10. `analizza()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `settings()` --uses--> `ScreeningSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `RuleSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
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

## Communities (42 total, 4 thin omitted)

### Community 0 - "confidence.py"
Cohesion: 0.10
Nodes (21): Match, _apply_context(), _build(), _cerca_nel_testo(), _etichetta(), _find_markers(), level_for(), Percentuale di sicurezza: e' telemedicina? e' una prenotazione? Il servizio non… (+13 more)

### Community 1 - "Settings"
Cohesion: 0.06
Nodes (121): LogCaptureFixture, EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings (+113 more)

### Community 2 - "matching.py"
Cohesion: 0.05
Nodes (67): Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), Prima verifica su oggetto e corpo del messaggio., Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, ScreeningSettings, alnum_collapse(), apply_ocr_confusions() (+59 more)

### Community 3 - "test_ocrspace.py"
Cohesion: 0.25
Nodes (18): image(), make_client(), no_sleep(), activate, fixture, MonkeyPatch, Path, Test del client HTTP verso ocr.space (rete simulata con `responses`). (+10 more)

### Community 4 - "config.py"
Cohesion: 0.08
Nodes (55): Session, ApiSettings, _as_str_list(), AttachmentSettings, _clean(), ConfigError, FlowPopupSettings, LoggingSettings (+47 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.08
Nodes (35): _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le… (+27 more)

### Community 6 - "parse_email"
Cohesion: 0.13
Nodes (27): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment')., Servizio su un'altra macchina: il file si cerca nelle cartelle indicate. (+19 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.11
Nodes (30): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+22 more)

### Community 8 - "sentiment.py"
Cohesion: 0.13
Nodes (27): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., analyze_sentiment(), _booking(), _clamp(), _label() (+19 more)

### Community 9 - "analysis.py"
Cohesion: 0.12
Nodes (20): _aggregate(), _clip(), _decide(), _extend_unique(), Path, Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero… (+12 more)

### Community 10 - "main"
Cohesion: 0.17
Nodes (26): ArgumentParser, build_parser(), main(), config_file(), activate, fixture, MonkeyPatch, Path (+18 more)

### Community 11 - "FintoPulsante"
Cohesion: 0.18
Nodes (5): Servizio HTTP di analisi delle email di telemedicina. Riceve da Power Automate…, FintoPulsante, test_click_input_e_successo_solo_se_conferma_si_chiude(), test_click_input_non_e_successo_se_conferma_resta_visibile(), test_verifica_esterna_evita_loop_con_wrapper_uia_obsoleto()

### Community 12 - "POST /analizza-email - main analysis endpoint"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "inbound.py"
Cohesion: 0.16
Nodes (22): _as_text(), _CaseInsensitive, decode_base64(), _ensure_name(), _flatten(), _from_data_uri(), _is_html_flagged(), _is_inline() (+14 more)

### Community 14 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 15 - "popup_clicker.py"
Cohesion: 0.06
Nodes (36): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+28 more)

### Community 16 - "test_logging_setup.py"
Cohesion: 0.09
Nodes (39): datetime, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola., Avvia il server HTTP (bloccante) fino a Ctrl+C. (+31 more)

### Community 17 - "ConfidenceSettings"
Cohesion: 0.14
Nodes (31): Quanto e' sicuro che il messaggio riguardi la telemedicina. ``document_text``,…, score_telemedicine(), ConfidenceSettings, Soglie e taratura delle percentuali di sicurezza., impostazioni(), _percentuali(), fixture, parametrize (+23 more)

### Community 18 - "Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?, Source Nodes

### Community 19 - "Origine"
Cohesion: 0.22
Nodes (9): Enum, Origine, Provenienza di un'immagine o di un documento analizzato., str, La foto incollata nel corpo arriva come <img src="data:...">., PAD serializza gli oggetti del connettore in ``Properties``., test_allegati_office365_desktop_annidati_in_properties(), test_allegato_inline_marcato_come_foto_del_corpo() (+1 more)

### Community 20 - "conftest.py"
Cohesion: 0.50
Nodes (3): b64(), Fixture condivise: configurazione di prova, OCR fittizio, payload di esempio., test_base64_tollerante_a_spazi_e_padding()

### Community 21 - "message_guard.py"
Cohesion: 0.13
Nodes (28): Connection, _attachment_identity(), _binary_hash(), _body_text(), _create_current_table(), _ensure_schema(), LocalMessageStore, message_fingerprint() (+20 more)

### Community 22 - "InboundAttachment"
Cohesion: 0.25
Nodes (4): Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, InboundAttachment, Allegato ricevuto da Power Automate. Arriva in due forme, entrambe supportate:…, C'e' qualcosa da leggere: byte in memoria o un file raggiungibile.

### Community 23 - "Q: Diagnosi log allegato 132582.jpg senza base64 e aggiunta flag --dev per non salvare email e saltare duplicati"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Diagnosi log allegato 132582.jpg senza base64 e aggiunta flag --dev per non salvare email e saltare duplicati, Source Nodes

### Community 24 - "Q: Tutte le email hanno allegati, cosa e andato storto nei log della run 2026-09-08 10:30"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Tutte le email hanno allegati, cosa e andato storto nei log della run 2026-09-08 10:30, Source Nodes

### Community 25 - "EmailAnalysis"
Cohesion: 0.17
Nodes (9): EmailAnalysis, Risultato completo restituito dal servizio HTTP., Verdetto richiesto dal flusso: e' una prenotazione di telemedicina?, EmailSessionReport, Registro in memoria delle email gestite nella singola sessione HTTP., Una riga del riepilogo di una sessione del servizio., Raccoglie esiti HTTP e li stampa ordinati allo spegnimento dell'app., Registra una decisione completata e restituisce la riga creata. (+1 more)

### Community 26 - "Certainty threshold - determines 200 vs 202 response"
Cohesion: 0.67
Nodes (4): Certainty threshold - determines 200 vs 202 response, Dual 2xx codes - avoid Power Automate error handling, HTTP 200 - certain telemedicine booking, HTTP 202 - analyzed, not a certain booking

### Community 27 - "plugin"
Cohesion: 0.40
Nodes (4): plugin, $schema, opencode-mem, .opencode/plugins/graphify.js

### Community 28 - "responses.py"
Cohesion: 0.26
Nodes (14): analysis_to_dict(), _clip(), confidence_to_dict(), _criteria_to_dict(), _document_to_dict(), _evidence_to_dict(), _is_clipped(), Any (+6 more)

### Community 32 - "inspect_popup.py"
Cohesion: 0.50
Nodes (4): _dump_element(), main(), Diagnostic: dump the UIA tree of the Power Automate popup. Run this while the…, Recursive dump of a UIA element and its children.

### Community 33 - "TextExtractor"
Cohesion: 0.06
Nodes (60): Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, _cmd_check_file(), _cmd_serve(), Path, Interfaccia a riga di comando. Tre modi d'uso: * ``serve`` - avvia il servizio…, Analizza un singolo file locale: utile per tarare regole e chiave API., AttachmentFile, ExtractedText (+52 more)

### Community 34 - "_cmd_analizza"
Cohesion: 0.29
Nodes (7): InboundError, ValueError, Payload non interpretabile: manca un campo o il base64 e' rotto., _cmd_analizza(), Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP., test_email_vuota_rifiutata(), test_payload_non_oggetto_rifiutato()

### Community 35 - "_Accumulator"
Cohesion: 0.25
Nodes (4): _Accumulator, Somma i pesi degli indizi tenendo l'elenco di cio' che ha contato., Evidence, Un singolo indizio che sposta la percentuale di sicurezza. ``weight`` e'…

### Community 36 - "InboundEmail"
Cohesion: 0.11
Nodes (14): _describe(), Motivo per non leggere gli allegati, oppure None per proseguire., La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Indizi del punteggio in una riga, per il log., Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un…, ConfidenceScore, InboundEmail, Identificativo usato nei log e nella risposta. (+6 more)

### Community 37 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

### Community 38 - "_parse_html_body"
Cohesion: 0.33
Nodes (6): _clean_text(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., test_html_to_text_mantiene_gli_a_capo()

### Community 39 - "_check_api_key"
Cohesion: 0.50
Nodes (4): _check_api_key(), _constant_time_equals(), Confronto della chiave condivisa con Power Automate., Confronto a tempo costante: non rivela quanti caratteri combaciano.

### Community 40 - "app.py"
Cohesion: 0.15
Nodes (18): FastAPI, Request, _ignored_message(), _payload_to_log(), _payload_value(), Any, Applicazione HTTP (FastAPI) interrogata da Power Automate. ``POST /analizza-…, Copia ricorsivamente il payload senza riversare il base64 intero nei log. (+10 more)

## Knowledge Gaps
- **20 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Answer` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `_read_attachments()` (3× useful, score=2.995231791)
- `parse_email()` (2× useful, score=1.996614382)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `TextExtractor`, `_cmd_analizza`, `config.py`, `_check_api_key`, `app.py`, `analysis.py`, `main`, `test_logging_setup.py`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `app.py`, `TextExtractor`, `_cmd_analizza`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 84 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 84 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `confidence.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10153846153846154 - nodes in this community are weakly interconnected._