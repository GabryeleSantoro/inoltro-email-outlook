# Graph Report - inoltro-email-outlook  (2026-09-08)

## Corpus Check
- 49 files · ~40,413 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 965 nodes · 2437 edges · 40 communities (37 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 317 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bcab4756`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- email_payload
- Settings
- matching.py
- MatchReport
- config.py
- app.py
- parse_email
- riduci_sotto
- sentiment.py
- analysis.py
- main
- trova_termini
- POST /analizza-email - main analysis endpoint
- inbound.py
- _BodyParser
- popup_clicker.py
- __main__.py
- ConfidenceSettings
- Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?
- score_booking
- TextExtractor
- message_guard.py
- InboundAttachment
- Origine
- _Zones
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- responses.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- extractor.py
- InboundError
- InboundEmail
- _read_path_attachments
- confidence.py
- FintoPulsante
- models.py

## God Nodes (most connected - your core abstractions)
1. `Settings` - 100 edges
2. `email_payload()` - 73 edges
3. `attachment_payload()` - 56 edges
4. `TextExtractor` - 55 edges
5. `FakeOcrClient` - 49 edges
6. `EmailAnalyzer` - 47 edges
7. `parse_email()` - 45 edges
8. `make_blank_pdf()` - 39 edges
9. `create_app()` - 35 edges
10. `analizza()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `analizza()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `test_allegato_illeggibile_non_blocca_la_risposta()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `settings()` --uses--> `ScreeningSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `RuleSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `OcrSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Email analysis pipeline: screening -> OCR -> confidence -> response** — concept_screening, concept_ocr, concept_confidence, concept_sentiment, concept_api_analizza_email [EXTRACTED 1.00]
- **Production runtime dependencies** — concept_fastapi, concept_uvicorn, concept_pypdf, concept_pillow [EXTRACTED 1.00]
- **Design rationale decisions explaining service behavior** — concept_json_repair, concept_read_all_then_decide, concept_pdf_text_first, concept_ocr_noise_tolerance, concept_image_resize, concept_telemarketing_vs_booking, concept_dual_2xx_codes [INFERRED 0.85]

## Communities (40 total, 3 thin omitted)

### Community 0 - "email_payload"
Cohesion: 0.08
Nodes (67): LogCaptureFixture, EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, TestClient, email_payload() (+59 more)

### Community 1 - "Settings"
Cohesion: 0.12
Nodes (45): Crea la cartella dei log: il primo avvio non fallisce., Settings, Esito, Esito complessivo dell'analisi di un messaggio., attachment_payload(), Allegato nella forma prodotta dal connettore Office 365 Outlook., analizza(), parametrize (+37 more)

### Community 2 - "matching.py"
Cohesion: 0.11
Nodes (37): Prima verifica su oggetto e corpo del messaggio., Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, ScreeningSettings, alnum_collapse(), apply_ocr_confusions(), _clean(), contains_code() (+29 more)

### Community 3 - "MatchReport"
Cohesion: 0.29
Nodes (4): _decide(), Traduce l'esito della lettura dei documenti in un esito complessivo., MatchReport, Esito del confronto fra un testo e le regole configurate.

### Community 4 - "config.py"
Cohesion: 0.09
Nodes (51): ApiSettings, _as_str_list(), AttachmentSettings, _clean(), ConfigError, FlowPopupSettings, LoggingSettings, _normalize_extension() (+43 more)

### Community 5 - "app.py"
Cohesion: 0.05
Nodes (54): FastAPI, Request, _check_api_key(), _constant_time_equals(), _ignored_message(), _payload_to_log(), _payload_value(), Any (+46 more)

### Community 6 - "parse_email"
Cohesion: 0.12
Nodes (30): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment')., Servizio su un'altra macchina: il file si cerca nelle cartelle indicate. (+22 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.12
Nodes (28): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+20 more)

### Community 8 - "sentiment.py"
Cohesion: 0.12
Nodes (29): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., Polarita' del testo piu' l'intento di prenotazione., SentimentScore, analyze_sentiment(), _booking() (+21 more)

### Community 9 - "analysis.py"
Cohesion: 0.19
Nodes (14): _aggregate(), _clip(), _extend_unique(), Path, Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero…, Rende l'allegato un file su disco, pronto per l'OCR. Se il payload ne ha… (+6 more)

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

### Community 14 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 15 - "popup_clicker.py"
Cohesion: 0.06
Nodes (36): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+28 more)

### Community 16 - "__main__.py"
Cohesion: 0.07
Nodes (45): datetime, Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola. (+37 more)

### Community 17 - "ConfidenceSettings"
Cohesion: 0.12
Nodes (34): _build(), level_for(), Quanto e' sicuro che il messaggio riguardi la telemedicina. ``document_text``,…, Etichetta leggibile della percentuale, per chi non vuole leggere i numeri., score_telemedicine(), ConfidenceSettings, Soglie e taratura delle percentuali di sicurezza., impostazioni() (+26 more)

### Community 18 - "Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?, Source Nodes

### Community 19 - "score_booking"
Cohesion: 0.18
Nodes (8): _Accumulator, _apply_context(), _etichetta(), Somma i pesi degli indizi tenendo l'elenco di cio' che ha contato., Quanto e' sicuro che il messaggio sia una prenotazione di telemedicina. Il…, Applica gli indizi di contesto, che valgono solo scritti per esteso. Non…, Etichetta dell'indizio, con la forma davvero letta se era scorretta., score_booking()

### Community 20 - "TextExtractor"
Cohesion: 0.15
Nodes (37): Da dove arriva il testo di un allegato., TextSource, Ricava il testo di un allegato usando la strategia piu' economica., TextExtractor, fake_ocr(), FakeOcrClient, make_pdf(), make_photo() (+29 more)

### Community 21 - "message_guard.py"
Cohesion: 0.13
Nodes (28): Connection, _attachment_identity(), _binary_hash(), _body_text(), _create_current_table(), _ensure_schema(), LocalMessageStore, message_fingerprint() (+20 more)

### Community 22 - "InboundAttachment"
Cohesion: 0.15
Nodes (11): _clean_text(), _from_data_uri(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., Converte un ``<img src="data:image/png;base64,...">`` in allegato., InboundAttachment (+3 more)

### Community 23 - "Origine"
Cohesion: 0.20
Nodes (10): Enum, Origine, Provenienza di un'immagine o di un documento analizzato., str, La foto incollata nel corpo arriva come <img src="data:...">., PAD serializza gli oggetti del connettore in ``Properties``., test_allegati_decodificati(), test_allegati_office365_desktop_annidati_in_properties() (+2 more)

### Community 24 - "_Zones"
Cohesion: 0.50
Nodes (3): Il testo diviso nelle zone che pesano in modo diverso. Ogni zona viene cercata…, Prima zona in cui compare il termine. Restituisce ``(zona, forma scorretta)``:…, _Zones

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

### Community 33 - "extractor.py"
Cohesion: 0.06
Nodes (45): Session, OcrSettings, _cmd_check_file(), Analizza un singolo file locale: utile per tarare regole e chiave API., AttachmentFile, ExtractedText, OcrResult, Allegato salvato su disco, pronto per essere analizzato. (+37 more)

### Community 34 - "InboundError"
Cohesion: 0.22
Nodes (9): decode_base64(), InboundError, ValueError, Decodifica tollerante: accetta a capo, spazi e padding mancante., Payload non interpretabile: manca un campo o il base64 e' rotto., b64(), test_base64_tollerante_a_spazi_e_padding(), test_email_vuota_rifiutata() (+1 more)

### Community 36 - "InboundEmail"
Cohesion: 0.15
Nodes (9): _describe(), Logga il contenuto in ingresso per facilitare il debug del flusso., Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, Indizi del punteggio in una riga, per il log., Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un…, InboundEmail, Identificativo usato nei log e nella risposta., Oggetto e corpo insieme: e' cio' su cui si fa la prima verifica. (+1 more)

### Community 37 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

### Community 39 - "confidence.py"
Cohesion: 0.14
Nodes (14): Match, _cerca_nel_testo(), _find_markers(), Percentuale di sicurezza: e' telemedicina? e' una prenotazione? Il servizio non…, Un testo senza zone: il contenuto di un documento letto dall'OCR. Non si divide…, Primo termine di telemedicina in un testo senza zone (nomi, documenti)., Solo il testo leggibile: via gli indirizzi e le righe di instradamento., Separa cio' che ha scritto il mittente dalla parte citata o inoltrata. (+6 more)

### Community 40 - "FintoPulsante"
Cohesion: 0.18
Nodes (5): Servizio HTTP di analisi delle email di telemedicina. Riceve da Power Automate…, FintoPulsante, test_click_input_e_successo_solo_se_conferma_si_chiude(), test_click_input_non_e_successo_se_conferma_resta_visibile(), test_verifica_esterna_evita_loop_con_wrapper_uia_obsoleto()

### Community 41 - "models.py"
Cohesion: 0.13
Nodes (10): Motivo per non leggere gli allegati, oppure None per proseguire., La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, ConfidenceScore, Evidence, Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza…, Prima verifica: telemedicina/televisita nell'oggetto o nel corpo., Termini riconosciuti, senza ripetizioni e in ordine stabile., Un singolo indizio che sposta la percentuale di sicurezza. ``weight`` e'… (+2 more)

## Knowledge Gaps
- **14 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Answer` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `email_payload`, `extractor.py`, `config.py`, `app.py`, `analysis.py`, `main`, `__main__.py`, `TextExtractor`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `app.py` to `__main__.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 83 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `email_payload` be split into smaller, more focused modules?**
  _Cohesion score 0.0784313725490196 - nodes in this community are weakly interconnected._