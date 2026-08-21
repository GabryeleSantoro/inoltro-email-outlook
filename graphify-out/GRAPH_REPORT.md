# Graph Report - inoltro-email-outlook  (2026-08-21)

## Corpus Check
- 44 files · ~35,682 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 861 nodes · 2178 edges · 33 communities (30 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 284 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e8549771`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Settings
- TextExtractor
- config.py
- ConfidenceSettings
- .load
- app.py
- parse_email
- extractor.py
- sentiment.py
- ConfidenceScore
- __main__.py
- trova_termini
- POST /analizza-email - main analysis endpoint
- inbound.py
- OcrSpaceClient
- FlowRunner
- confidence.py
- responses.py
- _read_path_attachments
- _BodyParser
- _cmd_analizza
- InboundAttachment
- analysis.py
- Origine
- _parse_html_body
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- _Zones
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py

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
10. `create_app()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `settings()` --uses--> `ScreeningSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `RuleSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
- `settings()` --uses--> `OcrSettings`  [INFERRED]
  tests/conftest.py → src/inoltro_email/config.py
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

## Communities (33 total, 3 thin omitted)

### Community 0 - "Settings"
Cohesion: 0.06
Nodes (108): EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings, Esito (+100 more)

### Community 1 - "TextExtractor"
Cohesion: 0.11
Nodes (39): AttachmentFile, ExtractedText, Allegato salvato su disco, pronto per essere analizzato., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Da dove arriva il testo di un allegato., TextSource, Path, Manda il PDF a ocr.space, a blocchi se supera i limiti del piano. (+31 more)

### Community 2 - "config.py"
Cohesion: 0.09
Nodes (42): _clean(), FlowPopupSettings, _normalize_extension(), Caricamento e validazione della configurazione. La configurazione arriva da due…, Impostazioni per il click automatico sul popup di conferma PAD., Tiene solo i formati che il servizio sa davvero leggere. La configurazione puo'…, Prima verifica su oggetto e corpo del messaggio., Criteri che il testo letto da allegati e foto deve soddisfare. (+34 more)

### Community 3 - "ConfidenceSettings"
Cohesion: 0.14
Nodes (31): Quanto e' sicuro che il messaggio riguardi la telemedicina. ``document_text``,…, score_telemedicine(), ConfidenceSettings, Soglie e taratura delle percentuali di sicurezza., impostazioni(), _percentuali(), fixture, parametrize (+23 more)

### Community 4 - ".load"
Cohesion: 0.11
Nodes (45): ApiSettings, _as_str_list(), AttachmentSettings, ConfigError, LoggingSettings, Any, Exception, Path (+37 more)

### Community 5 - "app.py"
Cohesion: 0.05
Nodes (49): FastAPI, Request, _check_api_key(), _constant_time_equals(), _payload_to_log(), Any, Applicazione HTTP (FastAPI) interrogata da Power Automate. Un solo endpoint fa…, Confronto della chiave condivisa con Power Automate. (+41 more)

### Community 6 - "parse_email"
Cohesion: 0.12
Nodes (30): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment')., Servizio su un'altra macchina: il file si cerca nelle cartelle indicate. (+22 more)

### Community 7 - "extractor.py"
Cohesion: 0.11
Nodes (29): Estrazione del testo da un allegato. Si legge sempre il modo piu' diretto per…, ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola. (+21 more)

### Community 8 - "sentiment.py"
Cohesion: 0.12
Nodes (29): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., Polarita' del testo piu' l'intento di prenotazione., SentimentScore, analyze_sentiment(), _booking() (+21 more)

### Community 9 - "ConfidenceScore"
Cohesion: 0.11
Nodes (15): _clip(), _describe(), Motivo per non leggere gli allegati, oppure None per proseguire., Logga il contenuto in ingresso per facilitare il debug del flusso., Legge allegati e foto del corpo finche' non trova un documento conforme.…, La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Indizi del punteggio in una riga, per il log., Restituisce un'anteprima dei log senza allagare console/file. (+7 more)

### Community 10 - "__main__.py"
Cohesion: 0.06
Nodes (62): ArgumentParser, datetime, Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, build(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fabbrica per ``uvicorn --factory``: legge la configurazione da sola., Avvia il server HTTP (bloccante) fino a Ctrl+C. (+54 more)

### Community 11 - "trova_termini"
Cohesion: 0.09
Nodes (31): Un testo senza zone: il contenuto di un documento letto dall'OCR. Non si divide…, Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), _TestoPiano, normalize(), Minuscolo, senza accenti, con gli spazi collassati., distanza_entro(), distanza_massima() (+23 more)

### Community 12 - "POST /analizza-email - main analysis endpoint"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "inbound.py"
Cohesion: 0.19
Nodes (18): _as_text(), _CaseInsensitive, _ensure_name(), _flatten(), _is_html_flagged(), _is_inline(), _looks_like_html(), Any (+10 more)

### Community 14 - "OcrSpaceClient"
Cohesion: 0.08
Nodes (35): Session, OcrSettings, OcrResult, Risposta di ocr.space per un singolo file., Lettura del testo degli allegati (ocr.space + livello testo dei PDF)., _error_message(), OcrSpaceClient, OcrSpaceError (+27 more)

### Community 15 - "FlowRunner"
Cohesion: 0.08
Nodes (25): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+17 more)

### Community 16 - "confidence.py"
Cohesion: 0.10
Nodes (20): Match, _Accumulator, _apply_context(), _build(), _cerca_nel_testo(), _etichetta(), _find_markers(), level_for() (+12 more)

### Community 17 - "responses.py"
Cohesion: 0.31
Nodes (12): analysis_to_dict(), _clip(), confidence_to_dict(), _criteria_to_dict(), _document_to_dict(), _evidence_to_dict(), _is_clipped(), Any (+4 more)

### Community 18 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

### Community 19 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 20 - "_cmd_analizza"
Cohesion: 0.29
Nodes (7): InboundError, ValueError, Payload non interpretabile: manca un campo o il base64 e' rotto., _cmd_analizza(), Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP., test_email_vuota_rifiutata(), test_payload_non_oggetto_rifiutato()

### Community 21 - "InboundAttachment"
Cohesion: 0.15
Nodes (11): Path, Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, Rende l'allegato un file su disco, pronto per l'OCR. Se il payload ne ha…, Ripulisce il nome fornito dal mittente prima di scriverlo su disco., Evita che due allegati omonimi si sovrascrivano., _sanitize_filename(), _unique_path(), _write_to_disk() (+3 more)

### Community 22 - "analysis.py"
Cohesion: 0.13
Nodes (14): _aggregate(), _decide(), _extend_unique(), Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero…, Traduce l'esito della lettura dei documenti in un esito complessivo., AttachmentAnalysis, MatchReport (+6 more)

### Community 23 - "Origine"
Cohesion: 0.25
Nodes (8): Enum, Origine, Provenienza di un'immagine o di un documento analizzato., str, La foto incollata nel corpo arriva come <img src="data:...">., test_allegati_decodificati(), test_allegato_inline_marcato_come_foto_del_corpo(), test_immagine_data_uri_nel_corpo_diventa_allegato()

### Community 24 - "_parse_html_body"
Cohesion: 0.18
Nodes (11): _clean_text(), decode_base64(), _from_data_uri(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., Converte un ``<img src="data:image/png;base64,...">`` in allegato. (+3 more)

### Community 25 - "EmailAnalysis"
Cohesion: 0.40
Nodes (3): EmailAnalysis, Risultato completo restituito dal servizio HTTP., Verdetto richiesto dal flusso: e' una prenotazione di telemedicina?

### Community 26 - "Certainty threshold - determines 200 vs 202 response"
Cohesion: 0.67
Nodes (4): Certainty threshold - determines 200 vs 202 response, Dual 2xx codes - avoid Power Automate error handling, HTTP 200 - certain telemedicine booking, HTTP 202 - analyzed, not a certain booking

### Community 27 - "plugin"
Cohesion: 0.40
Nodes (4): plugin, $schema, opencode-mem, .opencode/plugins/graphify.js

### Community 28 - "_Zones"
Cohesion: 0.50
Nodes (3): Il testo diviso nelle zone che pesano in modo diverso. Ogni zona viene cercata…, Prima zona in cui compare il termine. Restituisce ``(zona, forma scorretta)``:…, _Zones

### Community 32 - "inspect_popup.py"
Cohesion: 0.50
Nodes (4): _dump_element(), main(), Diagnostic: dump the UIA tree of the Power Automate popup. Run this while the…, Recursive dump of a UIA element and its children.

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Code 1501A - telemedicine booking code` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `TextExtractor`, `config.py`, `.load`, `app.py`, `extractor.py`, `__main__.py`, `OcrSpaceClient`, `_cmd_analizza`, `analysis.py`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `app.py` to `__main__.py`, `_cmd_analizza`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `parse_email` to `Settings`, `app.py`, `ConfidenceScore`, `__main__.py`, `inbound.py`, `_read_path_attachments`, `_cmd_analizza`, `Origine`, `_parse_html_body`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 76 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 76 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Settings` be split into smaller, more focused modules?**
  _Cohesion score 0.059928582518242506 - nodes in this community are weakly interconnected._