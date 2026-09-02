# Graph Report - inoltro-email-outlook  (2026-09-02)

## Corpus Check
- 46 files · ~37,670 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 911 nodes · 2298 edges · 37 communities (34 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 302 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4ab6b91d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Settings
- TextExtractor
- evaluate
- analysis.py
- config.py
- app.py
- parse_email
- riduci_sotto
- sentiment.py
- MatchReport
- main
- trova_termini
- POST /analizza-email - main analysis endpoint
- inbound.py
- OcrSpaceClient
- popup_clicker.py
- setup_logging
- _TolerantParser
- _read_path_attachments
- _BodyParser
- InboundError
- LocalMessageStore
- InboundEmail
- Origine
- InboundAttachment
- EmailAnalysis
- Certainty threshold - determines 200 vs 202 response
- plugin
- responses.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- matching.py
- screen
- ._read_documents
- ScreeningReport

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

## Communities (37 total, 3 thin omitted)

### Community 0 - "Settings"
Cohesion: 0.06
Nodes (109): LogCaptureFixture, EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings (+101 more)

### Community 1 - "TextExtractor"
Cohesion: 0.10
Nodes (41): Enum, AttachmentFile, ExtractedText, Strutture dati condivise fra i moduli. Sono tutte dataclass semplici, senza…, Allegato salvato su disco, pronto per essere analizzato., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Da dove arriva il testo di un allegato., TextSource (+33 more)

### Community 2 - "evaluate"
Cohesion: 0.27
Nodes (14): Criteri che il testo letto da allegati e foto deve soddisfare., RuleSettings, evaluate(), Confronta il testo con le regole e restituisce un report dettagliato. Con…, parametrize, Test dello screening su oggetto/corpo e delle regole sul testo estratto., telemedicina' non deve combaciare con la sua versione storpiata in cifre., test_confusioni_non_applicate_alle_keyword() (+6 more)

### Community 3 - "analysis.py"
Cohesion: 0.05
Nodes (61): Match, _describe(), Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Indizi del punteggio in una riga, per il log., _Accumulator, _apply_context(), _build(), _cerca_nel_testo() (+53 more)

### Community 4 - "config.py"
Cohesion: 0.09
Nodes (53): ApiSettings, _as_str_list(), AttachmentSettings, _clean(), ConfigError, FlowPopupSettings, LoggingSettings, _normalize_extension() (+45 more)

### Community 5 - "app.py"
Cohesion: 0.05
Nodes (51): FastAPI, Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, Request, _check_api_key(), _constant_time_equals(), _ignored_message(), _payload_to_log(), _payload_value() (+43 more)

### Community 6 - "parse_email"
Cohesion: 0.12
Nodes (30): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, parse_email(), Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, Test della lettura del payload inviato da Power Automate., Un <img> che punta a un URL non e' scaricabile: va semplicemente saltato., Il flusso salva il file e manda solo il percorso (campo 'attchment')., Servizio su un'altra macchina: il file si cerca nelle cartelle indicate. (+22 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.11
Nodes (30): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+22 more)

### Community 8 - "sentiment.py"
Cohesion: 0.13
Nodes (27): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., analyze_sentiment(), _booking(), _clamp(), _label() (+19 more)

### Community 9 - "MatchReport"
Cohesion: 0.17
Nodes (9): _aggregate(), _decide(), _extend_unique(), Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero…, Traduce l'esito della lettura dei documenti in un esito complessivo., AttachmentAnalysis, MatchReport, Esito del confronto fra un testo e le regole configurate. (+1 more)

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

### Community 14 - "OcrSpaceClient"
Cohesion: 0.08
Nodes (35): Session, OcrSettings, OcrResult, Risposta di ocr.space per un singolo file., Lettura del testo degli allegati (ocr.space + livello testo dei PDF)., _error_message(), OcrSpaceClient, OcrSpaceError (+27 more)

### Community 15 - "popup_clicker.py"
Cohesion: 0.07
Nodes (30): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+22 more)

### Community 16 - "setup_logging"
Cohesion: 0.09
Nodes (38): datetime, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola., Avvia il server HTTP (bloccante) fino a Ctrl+C. (+30 more)

### Community 17 - "_TolerantParser"
Cohesion: 0.19
Nodes (10): _as_list(), Any, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le…, Riparazioni applicate, con il numero di occorrenze., Legge una chiave, oppure restituisce None senza consumare nulla. Serve a…, Numeri, ``true``/``false``/``null`` e valori scritti senza virgolette., La virgoletta corrente chiude davvero la stringa?, Legge una sequenza di escape, tollerando quelle inesistenti. (+2 more)

### Community 18 - "_read_path_attachments"
Cohesion: 0.40
Nodes (6): _inside_any(), Path, Legge gli allegati che il payload indica solo con il percorso su disco., Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce. Il…, _read_path_attachments(), _resolve_local_path()

### Community 19 - "_BodyParser"
Cohesion: 0.22
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 20 - "InboundError"
Cohesion: 0.22
Nodes (9): decode_base64(), InboundError, ValueError, Decodifica tollerante: accetta a capo, spazi e padding mancante., Payload non interpretabile: manca un campo o il base64 e' rotto., b64(), test_base64_tollerante_a_spazi_e_padding(), test_email_vuota_rifiutata() (+1 more)

### Community 21 - "LocalMessageStore"
Cohesion: 0.18
Nodes (10): Connection, LocalMessageStore, message_fingerprint(), Any, Path, Controlli locali, economici, prima dell'analisi di una email. Il database resta…, Registro SQLite persistente e sicuro anche con piu' worker., Salva il messaggio e lo riserva all'analisi. L'inserimento atomico e' anche il… (+2 more)

### Community 22 - "InboundEmail"
Cohesion: 0.14
Nodes (8): Logga il contenuto in ingresso per facilitare il debug del flusso., Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un…, InboundEmail, Identificativo usato nei log e nella risposta., Oggetto e corpo insieme: e' cio' su cui si fa la prima verifica., Email singola inviata dal flusso Power Automate. ``body_text`` e' sempre testo…

### Community 23 - "Origine"
Cohesion: 0.33
Nodes (6): Origine, Provenienza di un'immagine o di un documento analizzato., La foto incollata nel corpo arriva come <img src="data:...">., test_allegati_decodificati(), test_allegato_inline_marcato_come_foto_del_corpo(), test_immagine_data_uri_nel_corpo_diventa_allegato()

### Community 24 - "InboundAttachment"
Cohesion: 0.15
Nodes (11): _clean_text(), _from_data_uri(), html_to_text(), _parse_html_body(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., Normalizza spazi e a capo: il testo va poi a regole e sentiment., Converte un ``<img src="data:image/png;base64,...">`` in allegato., InboundAttachment (+3 more)

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

### Community 33 - "matching.py"
Cohesion: 0.21
Nodes (12): Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), alnum_collapse(), apply_ocr_confusions(), contains_code(), contains_keyword(), normalize(), Regole di riconoscimento su oggetto, corpo e testo degli allegati. Il modulo… (+4 more)

### Community 34 - "screen"
Cohesion: 0.23
Nodes (13): Prima verifica su oggetto e corpo del messaggio., ScreeningSettings, _clean(), Prima verifica: i termini configurati compaiono in oggetto o corpo? Restituisce…, screen(), L'oggetto scritto a mano puo' contenere spazi o accenti di troppo., Lo stesso termine in oggetto e corpo va riportato una volta sola., test_screening_in_modalita_all_richiede_tutti_i_termini() (+5 more)

### Community 35 - "._read_documents"
Cohesion: 0.24
Nodes (10): _clip(), Path, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Rende l'allegato un file su disco, pronto per l'OCR. Se il payload ne ha…, Ripulisce il nome fornito dal mittente prima di scriverlo su disco., Evita che due allegati omonimi si sovrascrivano., Restituisce un'anteprima dei log senza allagare console/file., _sanitize_filename() (+2 more)

### Community 36 - "ScreeningReport"
Cohesion: 0.29
Nodes (4): Motivo per non leggere gli allegati, oppure None per proseguire., Prima verifica: telemedicina/televisita nell'oggetto o nel corpo., Termini riconosciuti, senza ripetizioni e in ordine stabile., ScreeningReport

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Code 1501A - telemedicine booking code` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `TextExtractor`, `analysis.py`, `config.py`, `app.py`, `main`, `OcrSpaceClient`, `setup_logging`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `app.py` to `_TolerantParser`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `parse_email` to `Settings`, `app.py`, `inbound.py`, `_read_path_attachments`, `InboundError`, `InboundEmail`, `Origine`, `InboundAttachment`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._