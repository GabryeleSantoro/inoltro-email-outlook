# inoltro-email-outlook

Servizio **HTTP** che analizza una email per volta, inviata da un flusso
**Power Automate**. Per ogni messaggio ricevuto il servizio:

1. verifica che **oggetto o corpo** parlino di **telemedicina** o **televisita**;
2. legge **allegati e foto incorporate nel corpo** con l'OCR di
   [ocr.space](https://ocr.space/ocrapi) e controlla che il testo contenga
   **sia "telemedicina" sia il codice "1501A"**;
3. calcola un **punteggio di sentiment** del messaggio e un punteggio di
   **intento di prenotazione** (quanto somiglia alla richiesta di prenotare una
   telemedicina).

La risposta e' un JSON che il flusso Power Automate puo' usare per decidere cosa
fare: inoltrare, aprire una pratica, rispondere al paziente o ignorare. Il
servizio non tocca la casella di posta e non invia nulla: legge, valuta e
risponde.

## Come funziona

```
Power Automate (nuova email)  --POST /analizza-email-->  servizio
                                                            |
                                            oggetto + corpo: telemedicina/televisita?
                                                            |
                                      no <-----------------/ \-----------------> si
                                       |                                          |
                            esito "scartata"                    allegati e foto del corpo
                            (nessuna chiamata OCR)                        |
                                                          PDF con testo? --si--> pypdf (niente OCR)
                                                                  |no
                                                                  v
                                                          ocr.space (POST /parse/image)
                                                                  |
                                                    criteri: "telemedicina" AND "1501A"
                                                                  |
                                                     esito "conforme" / "non_conforme"
                                                                  |
                                             + sentiment  + punteggio di prenotazione
                                                                  |
                                                              risposta JSON
```

Alcune scelte di funzionamento:

- **Screening prima dell'OCR**: se oggetto e corpo non parlano di telemedicina
  non si spende nemmeno una chiamata all'API (`screening.stop_on_failure`).
- **Risparmio di quota OCR**: se un PDF ha gia' il livello di testo lo si legge
  con `pypdf`, senza uscire dalla macchina; e non appena un documento soddisfa i
  criteri gli altri non vengono piu' analizzati.
- **Le foto del corpo contano**: spesso l'impegnativa e' fotografata e incollata
  nel messaggio. Vengono riconosciute sia come allegati `isInline`, sia come
  immagini `<img src="data:image/...;base64,...">` dentro l'HTML.
- **Tolleranza al rumore dell'OCR**: `15 0 1A`, `15-01A` e `l5O1A` vengono
  riconosciuti come `1501A`; `tele medicina` spezzata da un a capo come
  `telemedicina`.
- **Risposta sempre interpretabile**: un allegato illeggibile o un errore
  dell'OCR non fanno fallire la chiamata, diventano un esito con il motivo
  scritto nel JSON.
- **Sentiment spiegabile**: il punteggio e' calcolato con un lessico italiano e
  la risposta riporta i termini e gli indizi che lo hanno determinato. Nessun
  modello da scaricare, nessuna chiamata di rete aggiuntiva.

## Requisiti

- **Python 3.11+** su qualsiasi sistema operativo.
- Una chiave API di [ocr.space](https://ocr.space/ocrapi) (il piano gratuito e'
  sufficiente per volumi contenuti).
- Un flusso **Power Automate** che sappia raggiungere il servizio via HTTPS.

## Installazione

```bash
git clone https://github.com/GabryeleSantoro/inoltro-email-outlook.git
cd inoltro-email-outlook

python -m venv .venv
source .venv/bin/activate       # su Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Configurazione

**1. `.env`** — i segreti (copiare da `.env.example`, escluso dal versionamento):

```
OCR_SPACE_API_KEY=la-tua-chiave
SERVICE_API_KEY=una-stringa-lunga-e-casuale
```

`SERVICE_API_KEY` e' la chiave che Power Automate deve inviare nell'header
`X-API-Key`. Se resta vuota il controllo e' disattivato: accettabile solo in
locale.

**2. `config.yaml`** — i parametri (facoltativo: senza il file valgono i valori
predefiniti). Copiarlo da `config.example.yaml`:

```bash
cp config.example.yaml config.yaml
cp .env.example .env
```

Le voci da rivedere subito:

| Voce | Significato |
|---|---|
| `screening.keywords` / `screening.mode` | termini cercati in oggetto e corpo (`any` = ne basta uno) |
| `screening.stop_on_failure` | `true` = niente OCR se lo screening non passa |
| `rules.keywords` / `rules.codes` | criteri sul testo dei documenti; con `mode: all` servono tutti |
| `attachments.include_inline_images` | analizza anche le foto incorporate nel corpo |
| `attachments.max_files` | quanti file al massimo passare all'OCR per email |
| `sentiment.booking_threshold` | sopra questa soglia il messaggio e' "una prenotazione" |
| `api.host` / `api.port` | dove ascolta il servizio (le variabili `API_HOST` e `PORT` hanno la precedenza) |
| `ocr.max_file_bytes` / `ocr.max_pdf_pages_per_request` | limiti del piano ocr.space |

## Avvio del servizio

```bash
python -m inoltro_email serve                    # oppure: python main.py
python -m inoltro_email serve --port 9000 --reload
```

In produzione si puo' usare direttamente uvicorn con piu' processi:

```bash
uvicorn inoltro_email.api.server:build --factory --host 0.0.0.0 --port 8000 --workers 4
```

Documentazione interattiva (generata dal servizio): <http://localhost:8000/docs>.

## L'API

| Metodo | Percorso | Descrizione |
|---|---|---|
| `POST` | `/analizza-email` | analizza una singola email (richiede `X-API-Key` se configurata) |
| `GET` | `/salute` | sonda di funzionamento, sempre pubblica |
| `GET` | `/` | informazioni sul servizio |
| `GET` | `/docs`, `/openapi.json` | documentazione e schema OpenAPI |

### Richiesta

Il corpo e' il messaggio cosi' come lo consegna Power Automate. Sono accettate
sia la forma del connettore *Office 365 Outlook* sia quella di *Microsoft
Graph*, e le chiavi possono avere maiuscole o minuscole:

```json
{
  "id": "AAMkAGI2...",
  "internetMessageId": "<0123@example.com>",
  "subject": "Richiesta prenotazione televisita",
  "from": "paziente@example.com",
  "receivedDateTime": "2026-08-19T08:00:00Z",
  "isHtml": true,
  "body": "<p>Buongiorno, vorrei prenotare una televisita. In allegato l'impegnativa. Grazie.</p>",
  "attachments": [
    {
      "name": "impegnativa.pdf",
      "contentType": "application/pdf",
      "isInline": false,
      "contentBytes": "JVBERi0xLjQK...(base64)"
    }
  ]
}
```

### Risposta

```json
{
  "id_messaggio": "<0123@example.com>",
  "oggetto": "Richiesta prenotazione televisita",
  "esito": "conforme",
  "conforme": true,
  "screening": { "superato": true, "termini": ["televisita"], "dove": ["oggetto", "corpo"] },
  "criteri": {
    "soddisfatti": true,
    "trovati": ["telemedicina", "1501A"],
    "mancanti": [],
    "documento": "impegnativa.pdf"
  },
  "documenti": [
    {
      "nome": "impegnativa.pdf",
      "origine": "allegato",
      "sorgente": "pdf_text",
      "caratteri": 512,
      "conforme": true,
      "trovati": ["telemedicina", "1501A"],
      "mancanti": [],
      "errore": null
    }
  ],
  "sentiment": {
    "punteggio": 1.0,
    "etichetta": "positivo",
    "termini_positivi": ["grazie"],
    "termini_negativi": [],
    "prenotazione": {
      "punteggio": 1.0,
      "e_prenotazione": true,
      "indizi": ["prenotazione", "telemedicina", "impegnativa", "allegato conforme"]
    }
  },
  "errore": null,
  "durata_ms": 63,
  "analizzato_il": "2026-08-19T08:00:01+00:00"
}
```

Valori possibili di `esito`:

| Esito | Significato |
|---|---|
| `conforme` | screening superato e documento con tutti i criteri (`conforme: true`) |
| `non_conforme` | screening superato, ma nessun documento contiene i criteri |
| `scartata` | oggetto e corpo non parlano di telemedicina: nessun OCR eseguito |
| `senza_contenuto` | nessun allegato o foto leggibile (assente, tipo non previsto, OCR fallito) |
| `errore` | analisi interrotta: il motivo e' nel campo `errore` |

`sentiment.punteggio` va da `-1` (negativo) a `+1` (positivo);
`sentiment.prenotazione.punteggio` va da `0` a `1` ed e' confrontato con
`sentiment.booking_threshold` per ottenere `e_prenotazione`.

Codici di stato: `200` analisi eseguita (anche quando l'email non e' conforme),
`400` payload non interpretabile, `401` chiave assente o errata, `413` richiesta
oltre `api.max_request_bytes`. Gli errori hanno la forma
`{"errore": "...", "codice": 400}`.

## Il flusso Power Automate

1. **Trigger**: *Office 365 Outlook - Quando arriva un nuovo messaggio di posta
   elettronica (V3)*, sulla cartella da sorvegliare, con **"Includi allegati"**
   e **"Includi allegati inline"** impostati su **Si**.
2. **Azione HTTP**:
   - Metodo: `POST`
   - URI: `https://<indirizzo-del-servizio>/analizza-email`
   - Intestazioni: `Content-Type: application/json`, `X-API-Key: <SERVICE_API_KEY>`
   - Corpo: il messaggio del trigger. Il modo piu' semplice e' comporlo con i
     campi dinamici:

     ```
     {
       "internetMessageId": @{triggerOutputs()?['body/internetMessageId']},
       "subject": @{triggerOutputs()?['body/subject']},
       "body": @{triggerOutputs()?['body/body']},
       "isHtml": true,
       "from": @{triggerOutputs()?['body/from']},
       "receivedDateTime": @{triggerOutputs()?['body/receivedDateTime']},
       "attachments": @{triggerOutputs()?['body/attachments']}
     }
     ```

     Gli allegati del connettore contengono gia' `name`, `contentType` e
     `contentBytes` in base64: vanno passati cosi' come sono.
3. **Condizione** sul risultato, per esempio
   `body('HTTP')?['conforme']` uguale a `true`, oppure
   `body('HTTP')?['sentiment']?['prenotazione']?['e_prenotazione']` uguale a
   `true`.
4. **Azione conclusiva** a scelta: *Inoltra messaggio*, creazione di un
   elemento in un elenco, notifica in Teams, risposta automatica al paziente.

Suggerimenti: impostare un **timeout** generoso sull'azione HTTP (l'OCR di un
PDF di piu' pagine puo' richiedere qualche decina di secondi) e attivare
**"Riprova"** solo con criterio: l'analisi e' ripetibile, ma ogni tentativo
consuma quota OCR.

## Comandi di prova

**Analizzare un payload salvato su file** (stessa risposta dell'endpoint, senza
far partire il server):

```bash
python -m inoltro_email analizza email.json
cat email.json | python -m inoltro_email analizza
```

**Provare OCR e criteri su un singolo file**:

```bash
python -m inoltro_email check-file impegnativa.pdf --show-text
```

```
File      : impegnativa.pdf
Sorgente  : pdf_text
Caratteri : 512
Criteri   : trovati=[telemedicina, 1501A] mancanti=[-]
Esito     : CONFORME
```

Opzioni comuni: `--config <percorso>`, `--log-level DEBUG`.
Codici di uscita: `0` comando eseguito, `1` criteri non soddisfatti
(`check-file`) o analisi interrotta (`analizza`), `2` problema di
configurazione o file non leggibile, `130` interruzione da tastiera.

## Struttura del progetto

```
src/inoltro_email/
├── __main__.py        riga di comando (serve | analizza | check-file)
├── config.py          lettura e validazione di config.yaml + .env
├── inbound.py         lettura del payload di Power Automate (HTML, base64, foto del corpo)
├── matching.py        normalizzazione del testo, screening e criteri telemedicina/1501A
├── analysis.py        orchestrazione: screening -> OCR -> criteri -> sentiment
├── sentiment.py       punteggio di polarita' e di intento di prenotazione
├── models.py          strutture dati condivise
├── logging_setup.py   log su console e su file rotante
├── api/
│   ├── app.py         applicazione FastAPI e endpoint
│   ├── responses.py   traduzione del risultato nel JSON di risposta
│   └── server.py      avvio con uvicorn
└── ocr/
    ├── ocrspace.py    client HTTP di ocr.space, con nuovi tentativi
    └── extractor.py   scelta della strategia: livello di testo del PDF o OCR
```

`analysis.py` non conosce HTTP e `api/app.py` non conosce l'OCR: la logica e'
collaudabile senza far partire il server e senza rete.

## Test

```bash
pip install -r requirements-dev.txt
pytest
```

La suite copre la lettura del payload di Power Automate (HTML, entita', base64
malformato, foto incorporate), lo screening e i criteri, il punteggio di
sentiment e di prenotazione, la scelta fra livello di testo del PDF e OCR, la
suddivisione dei PDF lunghi, il client ocr.space con rete simulata (compresi i
nuovi tentativi su HTTP 429), il flusso completo di analisi e l'endpoint HTTP
con la sua autenticazione. Non serve ne' rete ne' una casella vera.

## Note operative

**Esporre il servizio.** Power Automate deve poter raggiungere l'indirizzo:
serve un host pubblico con HTTPS (reverse proxy, container su un servizio cloud,
tunnel per le prove). Tenere sempre attiva `SERVICE_API_KEY` e, se possibile,
limitare gli indirizzi IP in ingresso.

**Limiti del piano gratuito di ocr.space.** File fino a 1 MB e PDF fino a 3
pagine. I PDF piu' lunghi vengono spezzati automaticamente in blocchi da
`ocr.max_pdf_pages_per_request` pagine; le immagini oltre il limite vengono
saltate con un avviso nel log (non vengono ricompresse). Con un piano a pagamento
si possono alzare `ocr.max_file_bytes` e `ocr.max_pdf_pages_per_request`.

**Motore OCR.** L'engine 2 rileva la lingua da solo e in genere e' il piu'
accurato sui documenti; se si vuole forzare l'italiano occorre impostare
`engine: 1` (o `3`) con `language: "ita"`.

**Tempo di risposta.** L'analisi e' sincrona: la chiamata HTTP resta aperta
finche' l'OCR non ha finito. Un PDF gia' provvisto di testo si risolve in
millisecondi, una scansione di piu' pagine puo' richiedere decine di secondi.
Se i volumi crescono conviene aumentare i `--workers` di uvicorn.

**Chiamate ripetute.** Il servizio non tiene un registro dei messaggi gia'
analizzati: analizzare due volte la stessa email restituisce lo stesso esito ma
consuma due volte la quota OCR. Se il flusso puo' ripetere le chiamate, conviene
filtrare i duplicati in Power Automate sull'`internetMessageId`.

**Riservatezza.** Gli allegati vengono inviati a un servizio esterno
(ocr.space) per il riconoscimento del testo: se contengono dati personali o
sanitari occorre verificarne l'ammissibilita' prima di attivare il flusso in
produzione. I PDF gia' provvisti di testo non escono mai dalla macchina, perche'
vengono letti in locale.

**Dove finiscono i dati.** Allegati e foto vengono scritti in una cartella
temporanea di sistema, rimossa al termine di ogni richiesta. Restano su disco
soltanto i log in `logs/`.

**Il sentiment e' un'indicazione.** Il punteggio nasce da un lessico e da regole
esplicite: e' utile per dare priorita' o per intercettare un reclamo, non per
decidere da solo. La decisione clinica o amministrativa resta al flusso e alle
persone.
