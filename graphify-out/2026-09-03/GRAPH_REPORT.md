# Graph Report - inoltro-email-outlook  (2026-09-03)

## Corpus Check
- 46 files · ~38,189 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 917 nodes · 2327 edges · 38 communities (34 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 309 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `275a93a2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Settings
- TextExtractor
- matching.py
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
- config.py
- popup_clicker.py
- __main__.py
- _TolerantParser
- ConfidenceScore
- app.py
- ._closes_string
- LocalMessageStore
- InboundEmail
- models.py
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- responses.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- _parse_html_body
- _BodyParser
- ScreeningReport
- InboundAttachment
- _cmd_analizza
- _read_path_attachments

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
- `settings()` --uses--> `ScreeningSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `RuleSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `SentimentSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `Settings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `test_ambiente_ha_la_precedenza()` --uses--> `Settings`  [INFERRED]
  tests/test_config.py → src/inoltro_email/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Email analysis pipeline: screening -> OCR -> confidence -> response** — concept_screening, concept_ocr, concept_confidence, concept_sentiment, concept_api_analizza_email [EXTRACTED 1.00]
- **Production runtime dependencies** — concept_fastapi, concept_uvicorn, concept_pypdf, concept_pillow [EXTRACTED 1.00]
- **Design rationale decisions explaining service behavior** — concept_json_repair, concept_read_all_then_decide, concept_pdf_text_first, concept_ocr_noise_tolerance, concept_image_resize, concept_telemarketing_vs_booking, concept_dual_2xx_codes [INFERRED 0.85]

## Communities (38 total, 4 thin omitted)

### Community 0 - "Settings"
Cohesion: 0.06
Nodes (117): LogCaptureFixture, EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings (+109 more)

### Community 1 - "TextExtractor"
Cohesion: 0.10
Nodes (39): AttachmentFile, ExtractedText, Allegato salvato su disco, pronto per essere analizzato., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Da dove arriva il testo di un allegato., TextSource, Path, Estrazione del testo da un allegato. Si legge sempre il modo piu' diretto per… (+31 more)

### Community 2 - "matching.py"
Cohesion: 0.09
Nodes (42): Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), Prima verifica su oggetto e corpo del messaggio., Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, ScreeningSettings, alnum_collapse(), apply_ocr_confusions() (+34 more)

### Community 3 - "ConfidenceSettings"
Cohesion: 0.06
Nodes (54): Match, _Accumulator, _apply_context(), _build(), _cerca_nel_testo(), _etichetta(), _find_markers(), level_for() (+46 more)

### Community 4 - ".load"
Cohesion: 0.18
Nodes (33): ConfigError, Exception, Legge il YAML, unisce i segreti dall'ambiente e valida il tutto.…, Sovrascrive con l'ambiente cio' che non deve stare nel YAML., Configurazione assente, malformata o incoerente., ambiente_pulito(), fixture, MonkeyPatch (+25 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.12
Nodes (25): _as_text(), _has_content(), loads_tolerant(), ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Il payload non e' interpretabile nemmeno con le riparazioni., Interpreta ``raw`` restituendo ``(valore, riparazioni)``. ``riparazioni`` e'…, RawJsonError (+17 more)

### Community 6 - "parse_email"
Cohesion: 0.10
Nodes (33): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, b64(), Fixture condivise: configurazione di prova, OCR fittizio, payload di esempio., Test della lettura del payload inviato da Power Automate., La foto incollata nel corpo arriva come <img src="data:...">. (+25 more)

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
Cohesion: 0.16
Nodes (27): ArgumentParser, build_parser(), main(), make_pdf(), PDF con un vero livello di testo, una pagina per elemento., config_file(), activate, fixture (+19 more)

### Community 11 - "trova_termini"
Cohesion: 0.12
Nodes (25): distanza_entro(), distanza_massima(), _parole(), _piu_vicina(), Riconoscimento dei termini scritti male. Le parole che contano per questo…, Termine piu' somigliante alla parola, se rientra nella tolleranza., Distanza di Damerau-Levenshtein, o None se supera ``limite``. Il calcolo si…, Quante differenze si accettano su una parola di questa lunghezza. (+17 more)

### Community 12 - "POST /analizza-email - main analysis endpoint"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "inbound.py"
Cohesion: 0.16
Nodes (22): _as_text(), _CaseInsensitive, decode_base64(), _ensure_name(), _flatten(), _from_data_uri(), _is_html_flagged(), _is_inline() (+14 more)

### Community 14 - "config.py"
Cohesion: 0.05
Nodes (54): Session, ApiSettings, _as_str_list(), AttachmentSettings, _clean(), FlowPopupSettings, LoggingSettings, _normalize_extension() (+46 more)

### Community 15 - "popup_clicker.py"
Cohesion: 0.07
Nodes (30): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+22 more)

### Community 16 - "__main__.py"
Cohesion: 0.07
Nodes (44): datetime, Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola. (+36 more)

### Community 17 - "_TolerantParser"
Cohesion: 0.24
Nodes (8): _as_list(), Any, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le…, Riparazioni applicate, con il numero di occorrenze., Legge una chiave, oppure restituisce None senza consumare nulla. Serve a…, Numeri, ``true``/``false``/``null`` e valori scritti senza virgolette., Legge una sequenza di escape, tollerando quelle inesistenti., _TolerantParser

### Community 18 - "ConfidenceScore"
Cohesion: 0.20
Nodes (7): _describe(), La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Indizi del punteggio in una riga, per il log., ConfidenceScore, Evidence, Un singolo indizio che sposta la percentuale di sicurezza. ``weight`` e'…, Quanto il servizio e' sicuro di un'affermazione, in percentuale.

### Community 19 - "app.py"
Cohesion: 0.11
Nodes (20): FastAPI, Request, _check_api_key(), _constant_time_equals(), _ignored_message(), _payload_to_log(), _payload_value(), Any (+12 more)

### Community 21 - "LocalMessageStore"
Cohesion: 0.19
Nodes (9): Connection, LocalMessageStore, message_fingerprint(), Any, Path, Registro locale dei messaggi che il flusso ha gia' gestito. Il database resta…, Registro SQLite persistente e sicuro anche con piu' worker., Registra il messaggio; ``False`` se la stessa impronta esiste gia'. (+1 more)

### Community 22 - "InboundEmail"
Cohesion: 0.20
Nodes (6): Logga il contenuto in ingresso per facilitare il debug del flusso., Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un…, InboundEmail, Identificativo usato nei log e nella risposta., Oggetto e corpo insieme: e' cio' su cui si fa la prima verifica., Email singola inviata dal flusso Power Automate. ``body_text`` e' sempre testo…

### Community 23 - "models.py"
Cohesion: 0.40
Nodes (5): Enum, Origine, Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza…, Provenienza di un'immagine o di un documento analizzato., str

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
Cohesion: 0.26
Nodes (14): analysis_to_dict(), _clip(), confidence_to_dict(), _criteria_to_dict(), _document_to_dict(), _evidence_to_dict(), _is_clipped(), Any (+6 more)

### Community 32 - "inspect_popup.py"
Cohesion: 0.50
Nodes (4): _dump_element(), main(), Diagnostic: dump the UIA tree of the Power Automate popup. Run this while the…, Recursive dump of a UIA element and its children.

### Community 34 - "_parse_html_body"
Cohesion: 0.33
Nodes (6): _clean_text(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., test_html_to_text_mantiene_gli_a_capo()

### Community 35 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 36 - "ScreeningReport"
Cohesion: 0.29
Nodes (4): Motivo per non leggere gli allegati, oppure None per proseguire., Prima verifica: telemedicina/televisita nell'oggetto o nel corpo., Termini riconosciuti, senza ripetizioni e in ordine stabile., ScreeningReport

### Community 38 - "InboundAttachment"
Cohesion: 0.25
Nodes (4): Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, InboundAttachment, Allegato ricevuto da Power Automate. Arriva in due forme, entrambe supportate:…, C'e' qualcosa da leggere: byte in memoria o un file raggiungibile.

### Community 39 - "_cmd_analizza"
Cohesion: 0.29
Nodes (7): InboundError, ValueError, Payload non interpretabile: manca un campo o il base64 e' rotto., _cmd_analizza(), Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP., test_email_vuota_rifiutata(), test_payload_non_oggetto_rifiutato()

### Community 40 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Code 1501A - telemedicine booking code` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `TextExtractor`, `.load`, `_cmd_analizza`, `analysis.py`, `main`, `config.py`, `__main__.py`, `app.py`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `__main__.py`, `_TolerantParser`, `app.py`, `_cmd_analizza`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `parse_email` to `Settings`, `_parse_html_body`, `_cmd_analizza`, `_read_path_attachments`, `inbound.py`, `__main__.py`, `app.py`, `InboundEmail`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._