# Graph Report - inoltro-email-outlook  (2026-09-03)

## Corpus Check
- 47 files · ~38,879 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 936 nodes · 2382 edges · 38 communities (35 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 311 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d888aa57`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- email_payload
- FakeOcrClient
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
- _BodyParser
- popup_clicker.py
- setup_logging
- confidence.py
- test_ocrspace.py
- app.py
- Settings
- message_guard.py
- InboundAttachment
- Esito
- test_api.py
- InboundEmail
- Certainty threshold - determines 200 vs 202 response
- plugin
- models.py
- graphify.js
- AGENTS.md - graphify instructions
- inoltro-email-outlook
- inspect_popup.py
- extractor.py
- __main__.py
- AttachmentFile
- ScreeningReport
- _read_email_request

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
- `analizza()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `test_allegato_illeggibile_non_blocca_la_risposta()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_analysis.py → src/inoltro_email/analysis.py
- `test_allegato_indicato_per_percorso_arriva_all_ocr()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_api.py → src/inoltro_email/analysis.py
- `test_email_di_telemedicina_che_non_e_prenotazione()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_api.py → src/inoltro_email/analysis.py
- `test_il_testo_puo_essere_escluso()` --uses--> `EmailAnalyzer`  [INFERRED]
  tests/test_api.py → src/inoltro_email/analysis.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Email analysis pipeline: screening -> OCR -> confidence -> response** — concept_screening, concept_ocr, concept_confidence, concept_sentiment, concept_api_analizza_email [EXTRACTED 1.00]
- **Production runtime dependencies** — concept_fastapi, concept_uvicorn, concept_pypdf, concept_pillow [EXTRACTED 1.00]
- **Design rationale decisions explaining service behavior** — concept_json_repair, concept_read_all_then_decide, concept_pdf_text_first, concept_ocr_noise_tolerance, concept_image_resize, concept_telemarketing_vs_booking, concept_dual_2xx_codes [INFERRED 0.85]

## Communities (38 total, 3 thin omitted)

### Community 0 - "email_payload"
Cohesion: 0.12
Nodes (48): attachment_payload(), email_payload(), make_blank_pdf(), Any, Fixture condivise: configurazione di prova, OCR fittizio, payload di esempio., Payload come quello inviato dall'azione HTTP di Power Automate., PDF senza alcun testo: simula una scansione da mandare all'OCR., Allegato nella forma prodotta dal connettore Office 365 Outlook. (+40 more)

### Community 1 - "FakeOcrClient"
Cohesion: 0.19
Nodes (28): Da dove arriva il testo di un allegato., TextSource, FakeOcrClient, Restituisce testi predefiniti per nome file e conta le chiamate., attachment_from(), Path, Test della scelta della strategia di lettura degli allegati., Una foto di impegnativa supera sempre il MB: si riduce, non si salta. (+20 more)

### Community 2 - "config.py"
Cohesion: 0.06
Nodes (64): Session, Solo il testo leggibile: via gli indirizzi e le righe di instradamento., _readable(), ApiSettings, _as_str_list(), AttachmentSettings, _clean(), FlowPopupSettings (+56 more)

### Community 3 - "ConfidenceSettings"
Cohesion: 0.14
Nodes (31): Quanto e' sicuro che il messaggio riguardi la telemedicina. ``document_text``,…, score_telemedicine(), ConfidenceSettings, Soglie e taratura delle percentuali di sicurezza., impostazioni(), _percentuali(), fixture, parametrize (+23 more)

### Community 4 - ".load"
Cohesion: 0.18
Nodes (33): ConfigError, Exception, Legge il YAML, unisce i segreti dall'ambiente e valida il tutto.…, Sovrascrive con l'ambiente cio' che non deve stare nel YAML., Configurazione assente, malformata o incoerente., ambiente_pulito(), fixture, MonkeyPatch (+25 more)

### Community 5 - "loads_tolerant"
Cohesion: 0.08
Nodes (35): _as_list(), _as_text(), _has_content(), loads_tolerant(), Any, ValueError, Lettura tollerante del JSON inviato da Power Automate. Il flusso costruisce il…, Parser a discesa ricorsiva che non si ferma davanti agli errori tipici. Le… (+27 more)

### Community 6 - "parse_email"
Cohesion: 0.08
Nodes (42): LocalFileSettings, Allegati passati come percorso su disco invece che in base64. Il flusso Power…, InboundError, parse_email(), ValueError, Payload non interpretabile: manca un campo o il base64 e' rotto., Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.…, b64() (+34 more)

### Community 7 - "riduci_sotto"
Cohesion: 0.11
Nodes (30): ImageError, _in_rgb(), _passi(), Exception, Path, Riduzione delle immagini troppo grandi per ocr.space. Il piano gratuito di…, Dimensioni da provare, dalla piu' grande utile alla piu' piccola., Porta l'immagine in RGB: il JPEG non ha canale di trasparenza. Le scansioni… (+22 more)

### Community 8 - "sentiment.py"
Cohesion: 0.13
Nodes (27): Soglie del punteggio di sentiment e di intento di prenotazione., SentimentSettings, BookingScore, Quanto il messaggio somiglia a una prenotazione di telemedicina., analyze_sentiment(), _booking(), _clamp(), _label() (+19 more)

### Community 9 - "analysis.py"
Cohesion: 0.13
Nodes (18): _aggregate(), _clip(), _decide(), _extend_unique(), Path, Orchestrazione: dall'email ricevuta al verdetto restituito. Il flusso, per ogni…, Legge allegati e foto del corpo finche' non trova un documento conforme.…, Riassume i criteri trovati su *tutti* i documenti letti. ``matched`` resta vero… (+10 more)

### Community 10 - "main"
Cohesion: 0.16
Nodes (27): ArgumentParser, build_parser(), main(), make_pdf(), PDF con un vero livello di testo, una pagina per elemento., config_file(), activate, fixture (+19 more)

### Community 11 - "trova_termini"
Cohesion: 0.10
Nodes (27): Un testo senza zone: il contenuto di un documento letto dall'OCR. Non si divide…, _TestoPiano, distanza_entro(), distanza_massima(), _parole(), _piu_vicina(), Riconoscimento dei termini scritti male. Le parole che contano per questo…, Termine piu' somigliante alla parola, se rientra nella tolleranza. (+19 more)

### Community 12 - "POST /analizza-email - main analysis endpoint"
Cohesion: 0.10
Nodes (26): Code 1501A - telemedicine booking code, POST /analizza-email - main analysis endpoint, GET /salute - health check endpoint, Confidence scores - telemedicina and booking percentages, FastAPI - HTTP framework, Image resize - downscale oversized images instead of skipping, JSON repair - tolerant parsing of malformed payloads, Local files - disk-path attachment reading (+18 more)

### Community 13 - "inbound.py"
Cohesion: 0.11
Nodes (31): _as_text(), _CaseInsensitive, _clean_text(), decode_base64(), _ensure_name(), _flatten(), _from_data_uri(), _inside_any() (+23 more)

### Community 14 - "_BodyParser"
Cohesion: 0.25
Nodes (3): HTMLParser, _BodyParser, Estrae testo e sorgenti delle immagini da un corpo HTML.

### Community 15 - "popup_clicker.py"
Cohesion: 0.07
Nodes (30): FlowRunner, Path, Esecuzione periodica di un flusso Power Automate. Il flusso viene avviato come…, Cerca il popup di conferma PAD e clicca 'Continue'. Il blocco input e' attivo…, Esegue un flusso Power Automate periodicamente., Avvia l'esecuzione periodica del flusso., Ferma l'esecuzione periodica., Esegue il flusso Power Automate aprendo la scorciatoia. Se ``auto_continue`` e'… (+22 more)

### Community 16 - "setup_logging"
Cohesion: 0.12
Nodes (30): datetime, prune_session_logs(), Path, Configurazione del logging: console + un file nuovo per ogni sessione. Ogni…, Da ``logs/inoltro.log`` a ``logs/inoltro-<data>-<ora>.log``. Se due sessioni…, Tiene i ``keep`` file di sessione piu' recenti, elimina gli altri. Con ``keep…, Installa gli handler sul logger radice (idempotente). Restituisce il file…, session_log_path() (+22 more)

### Community 17 - "confidence.py"
Cohesion: 0.08
Nodes (26): Match, La prenotazione e' certa, non solo probabile. Serve il tema confermato *e* una…, _Accumulator, _apply_context(), _build(), _cerca_nel_testo(), _etichetta(), _find_markers() (+18 more)

### Community 18 - "test_ocrspace.py"
Cohesion: 0.25
Nodes (18): image(), make_client(), no_sleep(), activate, fixture, MonkeyPatch, Path, Test del client HTTP verso ocr.space (rete simulata con `responses`). (+10 more)

### Community 19 - "app.py"
Cohesion: 0.17
Nodes (10): FastAPI, _check_api_key(), _constant_time_equals(), _ignored_message(), Applicazione HTTP (FastAPI) interrogata da Power Automate. ``POST /analizza-…, Confronto della chiave condivisa con Power Automate., Confronto a tempo costante: non rivela quanti caratteri combaciano., Risposta 2xx: il flow puo' ignorarla senza ritentare la HTTP action. (+2 more)

### Community 20 - "Settings"
Cohesion: 0.16
Nodes (28): LogCaptureFixture, EmailAnalyzer, Applica screening, OCR, criteri e sentiment a una singola email., create_app(), Path, Costruisce l'applicazione. ``analyzer`` si passa solo nei test, per evitare…, Crea la cartella dei log: il primo avvio non fallisce., Settings (+20 more)

### Community 21 - "message_guard.py"
Cohesion: 0.12
Nodes (30): Connection, html_to_text(), Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo., _attachment_identity(), _binary_hash(), _body_text(), _create_current_table(), _ensure_schema() (+22 more)

### Community 22 - "InboundAttachment"
Cohesion: 0.13
Nodes (8): _describe(), Logga il contenuto in ingresso per facilitare il debug del flusso., Gli allegati da analizzare: solo PDF e immagini, entro i limiti. Cio' che non…, Indizi del punteggio in una riga, per il log., Analizza il messaggio e restituisce il verdetto completo. Non solleva mai: un…, InboundAttachment, Allegato ricevuto da Power Automate. Arriva in due forme, entrambe supportate:…, C'e' qualcosa da leggere: byte in memoria o un file raggiungibile.

### Community 23 - "Esito"
Cohesion: 0.20
Nodes (12): Enum, Esito, Origine, Esito complessivo dell'analisi di un messaggio., Provenienza di un'immagine o di un documento analizzato., str, parametrize, L'impegnativa fotografata e incollata nel messaggio va letta comunque. (+4 more)

### Community 24 - "test_api.py"
Cohesion: 0.11
Nodes (29): TestClient, ocr(), _payload_del_flusso(), Test dell'endpoint HTTP interrogato da Power Automate., La sonda di stato non richiede la chiave: la usano i bilanciatori., Ricostruisce il JSON come lo scrive davvero Power Automate. A capo veri nel…, Il percorso del payload e' la base per l'invio a ocr.space., Foglio degli accessi mensili: telemedicina si', prenotazione no. (+21 more)

### Community 25 - "InboundEmail"
Cohesion: 0.13
Nodes (12): Logger, InboundEmail, Identificativo usato nei log e nella risposta., Oggetto e corpo insieme: e' cio' su cui si fa la prima verifica., Email singola inviata dal flusso Power Automate. ``body_text`` e' sempre testo…, EmailSessionReport, Registro in memoria delle email gestite nella singola sessione HTTP., Una riga del riepilogo di una sessione del servizio. (+4 more)

### Community 26 - "Certainty threshold - determines 200 vs 202 response"
Cohesion: 0.67
Nodes (4): Certainty threshold - determines 200 vs 202 response, Dual 2xx codes - avoid Power Automate error handling, HTTP 200 - certain telemedicine booking, HTTP 202 - analyzed, not a certain booking

### Community 27 - "plugin"
Cohesion: 0.40
Nodes (4): plugin, $schema, opencode-mem, .opencode/plugins/graphify.js

### Community 28 - "models.py"
Cohesion: 0.14
Nodes (20): analysis_to_dict(), _clip(), confidence_to_dict(), _criteria_to_dict(), _document_to_dict(), _evidence_to_dict(), _is_clipped(), Any (+12 more)

### Community 32 - "inspect_popup.py"
Cohesion: 0.50
Nodes (4): _dump_element(), main(), Diagnostic: dump the UIA tree of the Power Automate popup. Run this while the…, Recursive dump of a UIA element and its children.

### Community 33 - "extractor.py"
Cohesion: 0.13
Nodes (16): OcrResult, Risposta di ocr.space per un singolo file., Estrazione del testo da un allegato. Si legge sempre il modo piu' diretto per…, Lettura del testo degli allegati (ocr.space + livello testo dei PDF)., _error_message(), OcrSpaceClient, OcrSpaceError, Any (+8 more)

### Community 34 - "__main__.py"
Cohesion: 0.14
Nodes (16): Avvio rapido del servizio: ``python main.py``. Equivalente a ``python -m…, build(), _configure_reload_worker_logging(), Path, Avvio del servizio con uvicorn. Separato da ``app.py`` cosi' l'applicazione…, Fa scrivere il worker ricaricato nello stesso log della sessione CLI., Fabbrica per ``uvicorn --factory``: legge la configurazione da sola., Avvia il server HTTP (bloccante) fino a Ctrl+C. (+8 more)

### Community 35 - "AttachmentFile"
Cohesion: 0.21
Nodes (7): AttachmentFile, ExtractedText, Allegato salvato su disco, pronto per essere analizzato., Testo ricavato da un allegato, con la provenienza e l'eventuale errore., Path, Manda il PDF a ocr.space, a blocchi se supera i limiti del piano., Spezza il PDF in blocchi di pagine e concatena i testi riconosciuti.

### Community 36 - "ScreeningReport"
Cohesion: 0.29
Nodes (4): Motivo per non leggere gli allegati, oppure None per proseguire., Prima verifica: telemedicina/televisita nell'oggetto o nel corpo., Termini riconosciuti, senza ripetizioni e in ordine stabile., ScreeningReport

### Community 37 - "_read_email_request"
Cohesion: 0.27
Nodes (10): Request, _payload_to_log(), _payload_value(), Any, Legge pochi campi del JSON senza costruire l'email o gli allegati., Legge e valida il payload condiviso dagli endpoint email., Legge il corpo della richiesta e lo interpreta. Restituisce ``(payload,…, Serializza un payload in modo robusto per il logging di debug. (+2 more)

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem`, `inoltro-email-outlook`, `Code 1501A - telemedicine booking code` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `email_payload`, `extractor.py`, `config.py`, `__main__.py`, `.load`, `_read_email_request`, `FakeOcrClient`, `analysis.py`, `main`, `setup_logging`, `app.py`, `Esito`, `test_api.py`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `loads_tolerant()` connect `loads_tolerant` to `__main__.py`, `app.py`, `_read_email_request`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `parse_email()` connect `parse_email` to `email_payload`, `__main__.py`, `_read_email_request`, `inbound.py`, `app.py`, `Esito`, `InboundEmail`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `Settings` (e.g. with `EmailAnalyzer` and `_cmd_analizza()`) actually correct?**
  _`Settings` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `TextExtractor` (e.g. with `ImageError` and `OcrSpaceClient`) actually correct?**
  _`TextExtractor` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `FakeOcrClient` (e.g. with `OcrResult` and `client()`) actually correct?**
  _`FakeOcrClient` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `opencode-mem` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._