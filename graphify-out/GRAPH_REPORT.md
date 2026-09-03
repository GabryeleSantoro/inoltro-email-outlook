# Graph Report - inoltro-email-outlook  (2026-09-03)

## Corpus Check
- 46 files · ~37,878 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 916 nodes · 2312 edges · 41 communities (37 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 305 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `366c42f0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Settings
- TextExtractor
- evaluate
- ConfidenceSettings
- config.py
- loads_tolerant
- parse_email
- riduci_sotto
- sentiment.py
- analysis.py
- main
- trova_termini
- POST /analizza-email - main analysis endpoint
- inbound.py
- OcrSpaceClient
- popup_clicker.py
- __main__.py
- _TolerantParser
- confidence.py
- app.py
- normalize
- LocalMessageStore
- InboundEmail
- Origine
- .repairs
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- responses.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- screen
- _parse_html_body
- _BodyParser
- models.py
- matching.py
- InboundAttachment
- _cmd_analizza
- _read_path_attachments

## God Nodes (most connected - your core abstractions)
1. `Settings` - 96 edges
2. `email_payload()` - 70 edges
3. `TextExtractor` - 53 edges
4. `attachment_payload()` - 53 edges
5. `FakeOcrClient` - 46 edges
6. `EmailAnalyzer` - 45 edges
7. `parse_email()` - 45 edges
8. `make_blank_pdf()` - 36 edges
9. `create_app()` - 33 edges
10. `analizza()` - 30 edges

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

## Communities (41 total, 4 thin omitted)

### Community 0 - "Settings"
Cohesion: 0.06
Nodes (112): LogCaptureFixture, EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings (+104 more)

### Community 1 - "TextExtractor"
Cohesion: 0.10
Nodes (39): AttachmentFile, ExtractedText, Allegato salvato su disco, pronto per essere analizzato., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Da dove arriva il testo di un allegato., TextSource, Path, Estrazione del testo da un allegato. Si legge sempre il modo piu' diretto per… (+31 more)

### Community 2 - "evaluate"
Cohesion: 0.24
Nodes (17): Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, evaluate(), Confronta il testo con le regole e restituisce un report dettagliato. Con…, parametrize, Test dello screening su oggetto/corpo e delle regole sul testo estratto., Evita il falso positivo reale: isola -> 1501A con le confusioni OCR., telemedicina' non deve combaciare con la sua versione storpiata in cifre. (+9 more)

### Community 3 - "ConfidenceSettings"
Cohesion: 0.14
Nodes (31): Quanto e' sicuro che il messaggio riguardi la telemedicina. ``document_text``,…, score_telemedicine(), ConfidenceSettings, Soglie e taratura delle percentuali di sicurezza., impostazioni(), _percentuali(), fixture, parametrize (+23 more)

### Community 4 - "config.py"
Cohesion: 0.09
Nodes (52): ApiSettings, _as_str_list(), AttachmentSettings, _clean(), ConfigError, FlowPopupSettings, LoggingSettings, _normalize_extension() (+44 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.12
Nodes (25): _as_text(), _has_content(), loads_tolerant(), ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Il payload non e' interpretabile nemmeno con le riparazioni., Interpreta ``raw`` restituendo ``(valore, riparazioni)``. ``riparazioni`` e'…, RawJsonError (+17 more)

### Community 6 - "parse_email"
Cohesion: 0.12
Nodes (30): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment')., Servizio su un'altra macchina: il file si cerca nelle cartelle indicate. (+22 more)

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
Nodes (25): ArgumentParser, build_parser(), main(), config_file(), activate, fixture, MonkeyPatch, Path (+17 more)

### Community 11 - "trova_termini"
Cohesion: 0.12
Nodes (21): Un testo senza zone: il contenuto di un documento letto dall'OCR. Non si divide…, _TestoPiano, distanza_entro(), Distanza di Damerau-Levenshtein, o None se supera ``limite``. Il calcolo si…, Termini riconosciuti nel testo, anche se scritti male. Restituisce ``{termine:…, trova_termini(), parametrize, Test del riconoscimento dei termini scritti male. (+13 more)

### Community 12 - "POST /analizza-email - main analysis endpoint"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "inbound.py"
Cohesion: 0.19
Nodes (18): _as_text(), _CaseInsensitive, _ensure_name(), _flatten(), _is_html_flagged(), _is_inline(), _looks_like_html(), Any (+10 more)

### Community 14 - "OcrSpaceClient"
Cohesion: 0.08
Nodes (35): Session, OcrSettings, OcrResult, Risposta di ocr.space per un singolo file., Lettura del testo degli allegati (ocr.space + livello testo dei PDF)., _error_message(), OcrSpaceClient, OcrSpaceError (+27 more)

### Community 15 - "popup_clicker.py"
Cohesion: 0.07
Nodes (30): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+22 more)

### Community 16 - "__main__.py"
Cohesion: 0.07
Nodes (44): datetime, Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola. (+36 more)

### Community 17 - "_TolerantParser"
Cohesion: 0.21
Nodes (9): _as_list(), Any, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le…, Legge una chiave, oppure restituisce None senza consumare nulla. Serve a…, Numeri, ``true``/``false``/``null`` e valori scritti senza virgolette., La virgoletta corrente chiude davvero la stringa?, Legge una sequenza di escape, tollerando quelle inesistenti., Primo carattere non bianco da ``start``, con la sua posizione. (+1 more)

### Community 18 - "confidence.py"
Cohesion: 0.09
Nodes (23): Match, _Accumulator, _apply_context(), _build(), _cerca_nel_testo(), _etichetta(), _find_markers(), level_for() (+15 more)

### Community 19 - "app.py"
Cohesion: 0.11
Nodes (18): FastAPI, Request, _check_api_key(), _constant_time_equals(), _ignored_message(), _payload_to_log(), _payload_value(), Any (+10 more)

### Community 20 - "normalize"
Cohesion: 0.21
Nodes (10): Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), normalize(), Minuscolo, senza accenti, con gli spazi collassati., distanza_massima(), _parole(), _piu_vicina(), Riconoscimento dei termini scritti male. Le parole che contano per questo… (+2 more)

### Community 21 - "LocalMessageStore"
Cohesion: 0.18
Nodes (10): Connection, LocalMessageStore, message_fingerprint(), Any, Path, Controlli locali, economici, prima dell'analisi di una email. Il database resta…, Registro SQLite persistente e sicuro anche con piu' worker., Salva il messaggio e lo riserva all'analisi. L'inserimento atomico e' anche il… (+2 more)

### Community 22 - "InboundEmail"
Cohesion: 0.13
Nodes (12): _describe(), Motivo per non leggere gli allegati, oppure None per proseguire., Logga il contenuto in ingresso per facilitare il debug del flusso., La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Indizi del punteggio in una riga, per il log., Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un…, ConfidenceScore, InboundEmail (+4 more)

### Community 23 - "Origine"
Cohesion: 0.25
Nodes (8): Origine, Provenienza di un'immagine o di un documento analizzato., La foto incollata nel corpo arriva come <img src="data:...">., PAD serializza gli oggetti del connettore in ``Properties``., test_allegati_decodificati(), test_allegati_office365_desktop_annidati_in_properties(), test_allegato_inline_marcato_come_foto_del_corpo(), test_immagine_data_uri_nel_corpo_diventa_allegato()

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

### Community 33 - "screen"
Cohesion: 0.26
Nodes (12): Prima verifica su oggetto e corpo del messaggio., ScreeningSettings, Prima verifica: i termini configurati compaiono in oggetto o corpo? Restituisce…, screen(), L'oggetto scritto a mano puo' contenere spazi o accenti di troppo., Lo stesso termine in oggetto e corpo va riportato una volta sola., test_screening_in_modalita_all_richiede_tutti_i_termini(), test_screening_non_passa_senza_termini() (+4 more)

### Community 34 - "_parse_html_body"
Cohesion: 0.17
Nodes (12): _clean_text(), decode_base64(), _from_data_uri(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., Converte un ``<img src="data:image/png;base64,...">`` in allegato. (+4 more)

### Community 35 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 36 - "models.py"
Cohesion: 0.25
Nodes (5): Enum, Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza…, Prima verifica: telemedicina/televisita nell'oggetto o nel corpo., Termini riconosciuti, senza ripetizioni e in ordine stabile., ScreeningReport

### Community 37 - "matching.py"
Cohesion: 0.27
Nodes (9): alnum_collapse(), apply_ocr_confusions(), _clean(), contains_code(), contains_keyword(), Regole di riconoscimento su oggetto, corpo e testo degli allegati. Il modulo…, Tiene solo lettere e cifre. Serve a rendere equivalenti "1501A", "15 0 1A",…, Riconduce i caratteri ambigui a una forma unica (O->0, l->1, ...). (+1 more)

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

- **Why does `Settings` connect `Settings` to `TextExtractor`, `config.py`, `_cmd_analizza`, `analysis.py`, `main`, `OcrSpaceClient`, `__main__.py`, `app.py`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `__main__.py`, `_TolerantParser`, `app.py`, `_cmd_analizza`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `parse_email` to `Settings`, `_parse_html_body`, `_cmd_analizza`, `_read_path_attachments`, `inbound.py`, `__main__.py`, `app.py`, `InboundEmail`, `Origine`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._