# Graph Report - inoltro-email-outlook  (2026-09-16)

## Corpus Check
- 50 files · ~40,846 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 983 nodes · 2465 edges · 39 communities (36 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 314 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e6027f8f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- FintoPulsante
- Settings
- trova_termini
- PaddleOcrClient
- config.py
- loads_tolerant
- parse_email
- __main__.py
- sentiment.py
- responses.py
- main
- POST /analizza-email - main analysis endpoint
- inbound.py
- _BodyParser
- popup_clicker.py
- test_logging_setup.py
- ConfidenceSettings
- Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?
- Origine
- ScreeningReport
- message_guard.py
- InboundAttachment
- Q: Diagnosi log allegato 132582.jpg senza base64 e aggiunta flag --dev per non salvare email e saltare duplicati
- Q: Tutte le email hanno allegati, cosa e andato storto nei log della run 2026-09-08 10:30
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- TextExtractor
- InboundError
- EmailAnalyzer
- _read_path_attachments
- evaluate
- app.py
- analysis.py
- Q: aggiungi una sezione per scartare l'attesa del conferma, ad esempio --skip

## God Nodes (most connected - your core abstractions)
1. `Settings` - 99 edges
2. `email_payload()` - 81 edges
3. `attachment_payload()` - 62 edges
4. `TextExtractor` - 51 edges
5. `EmailAnalyzer` - 47 edges
6. `parse_email()` - 47 edges
7. `FakeOcrClient` - 47 edges
8. `make_blank_pdf()` - 41 edges
9. `create_app()` - 36 edges
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

## Communities (39 total, 3 thin omitted)

### Community 0 - "FintoPulsante"
Cohesion: 0.18
Nodes (5): Servizio HTTP di analisi delle email di telemedicina. Riceve da Power Automate…, FintoPulsante, test_click_input_e_successo_solo_se_conferma_si_chiude(), test_click_input_non_e_successo_se_conferma_resta_visibile(), test_verifica_esterna_evita_loop_con_wrapper_uia_obsoleto()

### Community 1 - "Settings"
Cohesion: 0.05
Nodes (125): create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare il…, Crea le cartelle runtime che possono nascere al primo avvio., Settings, TestClient, attachment_payload(), email_payload() (+117 more)

### Community 2 - "trova_termini"
Cohesion: 0.12
Nodes (25): distanza_entro(), distanza_massima(), _parole(), _piu_vicina(), Riconoscimento dei termini scritti male. Le parole che contano per questo…, Termine piu' somigliante alla parola, se rientra nella tolleranza., Distanza di Damerau-Levenshtein, o None se supera ``limite``. Il calcolo si…, Quante differenze si accettano su una parola di questa lunghezza. (+17 more)

### Community 3 - "PaddleOcrClient"
Cohesion: 0.10
Nodes (27): paddle, skipif, OcrSettings, OCR Paddle locale. Nessun file viene inviato a servizi esterni., _create_check_image(), _load_paddleocr(), OcrError, PaddleOcrClient (+19 more)

### Community 4 - "config.py"
Cohesion: 0.09
Nodes (52): ApiSettings, _as_str_list(), AttachmentSettings, _clean(), ConfigError, FlowPopupSettings, LoggingSettings, _normalize_extension() (+44 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.08
Nodes (35): _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le… (+27 more)

### Community 6 - "parse_email"
Cohesion: 0.11
Nodes (31): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment')., Servizio su un'altra macchina: il file si cerca nelle cartelle indicate. (+23 more)

### Community 7 - "__main__.py"
Cohesion: 0.16
Nodes (12): Enum, Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, _cmd_analizza(), _cmd_serve(), Path, Interfaccia a riga di comando. Tre modi d'uso: * ``serve`` - avvia il servizio…, Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP., Regole di riconoscimento su oggetto, corpo e testo degli allegati. Il modulo… (+4 more)

### Community 8 - "sentiment.py"
Cohesion: 0.13
Nodes (27): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., analyze_sentiment(), _booking(), _clamp(), _label() (+19 more)

### Community 9 - "responses.py"
Cohesion: 0.26
Nodes (14): analysis_to_dict(), _clip(), confidence_to_dict(), _criteria_to_dict(), _document_to_dict(), _evidence_to_dict(), _is_clipped(), Any (+6 more)

### Community 10 - "main"
Cohesion: 0.12
Nodes (33): ArgumentParser, build_parser(), _cmd_prepara_ocr(), main(), Prepara pesi e inferenza PaddleOCR prima del deploy isolato., OcrResult, Risultato OCR locale per un singolo file., Path (+25 more)

### Community 12 - "POST /analizza-email - main analysis endpoint"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "inbound.py"
Cohesion: 0.16
Nodes (22): _as_text(), _CaseInsensitive, _ensure_name(), _flatten(), _is_html_flagged(), _is_inline(), _looks_like_html(), Any (+14 more)

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
Cohesion: 0.05
Nodes (58): Match, _Accumulator, _apply_context(), _build(), _cerca_nel_testo(), _etichetta(), _find_markers(), level_for() (+50 more)

### Community 18 - "Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?, Source Nodes

### Community 19 - "Origine"
Cohesion: 0.22
Nodes (9): Origine, Provenienza di un'immagine o di un documento analizzato., str, PAD serializza gli oggetti del connettore in ``Properties``., La foto incollata nel corpo arriva come <img src="data:...">., test_allegati_decodificati(), test_allegati_office365_desktop_annidati_in_properties(), test_allegato_inline_marcato_come_foto_del_corpo() (+1 more)

### Community 20 - "ScreeningReport"
Cohesion: 0.40
Nodes (3): Prima verifica: telemedicina/televisita nell'oggetto o nel corpo., Termini riconosciuti, senza ripetizioni e in ordine stabile., ScreeningReport

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
Cohesion: 0.13
Nodes (11): Logger, EmailAnalysis, Risultato completo restituito dal servizio HTTP., Verdetto richiesto dal flusso: e' una prenotazione di telemedicina?, EmailSessionReport, Una riga del riepilogo di una sessione del servizio., Raccoglie esiti HTTP e li stampa ordinati allo spegnimento dell'app., Registra una risposta automatica preparata dal servizio. (+3 more)

### Community 26 - "Certainty threshold - determines 200 vs 202 response"
Cohesion: 0.67
Nodes (4): Certainty threshold - determines 200 vs 202 response, Dual 2xx codes - avoid Power Automate error handling, HTTP 200 - certain telemedicine booking, HTTP 202 - analyzed, not a certain booking

### Community 27 - "plugin"
Cohesion: 0.40
Nodes (4): plugin, $schema, opencode-mem, .opencode/plugins/graphify.js

### Community 32 - "inspect_popup.py"
Cohesion: 0.50
Nodes (4): _dump_element(), main(), Diagnostic: dump the UIA tree of the Power Automate popup. Run this while the…, Recursive dump of a UIA element and its children.

### Community 33 - "TextExtractor"
Cohesion: 0.09
Nodes (36): _cmd_check_file(), Analizza un singolo file locale: utile per tarare regole e OCR., AttachmentFile, ExtractedText, Allegato salvato su disco, pronto per essere analizzato., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Da dove arriva il testo di un allegato., TextSource (+28 more)

### Community 34 - "InboundError"
Cohesion: 0.22
Nodes (9): decode_base64(), InboundError, ValueError, Decodifica tollerante: accetta a capo, spazi e padding mancante., Payload non interpretabile: manca un campo o il base64 e' rotto., b64(), test_base64_tollerante_a_spazi_e_padding(), test_email_vuota_rifiutata() (+1 more)

### Community 36 - "EmailAnalyzer"
Cohesion: 0.13
Nodes (15): _describe(), EmailAnalyzer, Motivo per non leggere gli allegati, oppure None per proseguire., Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Indizi del punteggio in una riga, per il log., Applica screening, OCR, criteri e sentiment a una singola email., Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un… (+7 more)

### Community 37 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

### Community 38 - "evaluate"
Cohesion: 0.10
Nodes (39): Prima verifica su oggetto e corpo del messaggio., Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, ScreeningSettings, alnum_collapse(), apply_ocr_confusions(), _clean(), contains_code() (+31 more)

### Community 40 - "app.py"
Cohesion: 0.09
Nodes (33): FastAPI, JSONResponse, Request, _check_api_key(), _constant_time_equals(), _forwarding_block_reason(), _ignored_message(), _missing_recipe_response() (+25 more)

### Community 42 - "analysis.py"
Cohesion: 0.12
Nodes (20): _aggregate(), _clip(), _decide(), _extend_unique(), Path, Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero… (+12 more)

### Community 45 - "Q: aggiungi una sezione per scartare l'attesa del conferma, ad esempio --skip"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: aggiungi una sezione per scartare l'attesa del conferma, ad esempio --skip, Source Nodes

## Knowledge Gaps
- **23 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Answer` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `_read_attachments()` (3× useful, score=2.995231791) _(code changed — re-verify)_
- `parse_email()` (2× useful, score=1.996614382) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `TextExtractor`, `EmailAnalyzer`, `config.py`, `__main__.py`, `app.py`, `analysis.py`, `main`, `test_logging_setup.py`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `app.py`, `__main__.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 82 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 82 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `TextExtractor` (e.g. with `OcrError` and `analizza()`) actually correct?**
  _`TextExtractor` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `EmailAnalyzer` (e.g. with `Settings` and `AttachmentAnalysis`) actually correct?**
  _`EmailAnalyzer` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _23 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Settings` be split into smaller, more focused modules?**
  _Cohesion score 0.05247465712581992 - nodes in this community are weakly interconnected._