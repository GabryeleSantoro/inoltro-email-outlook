# inoltro-email-outlook

Servizio **HTTP** che analizza una email per volta, inviata da un flusso
**Power Automate**. Per ogni messaggio ricevuto il servizio:

1. verifica che **oggetto o corpo** parlino di **telemedicina** o **televisita**;
2. legge **PDF e immagini** allegati - i PDF direttamente quando hanno un
   livello di testo, gli altri con l'OCR di
   [ocr.space](https://ocr.space/ocrapi) - **restituisce il testo letto** e
   controlla che contenga **sia "telemedicina" sia il codice "1501A"**. Gli
   allegati possono arrivare in base64 dentro il payload oppure **come percorso
   su disco**. Le immagini troppo grandi per l'API vengono **ridimensionate**,
   non scartate;
3. restituisce due **percentuali di sicurezza**: quanto e' sicuro che il
   messaggio riguardi la **telemedicina** e quanto e' sicuro che sia una
   **prenotazione** di telemedicina, con l'elenco degli indizi che le hanno
   determinate;
4. calcola un **punteggio di sentiment** del messaggio.

Il codice di stato dice subito com'e' andata: **200** quando e' certamente una
prenotazione di telemedicina, **202** in tutti gli altri casi analizzati.

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
                                       |                                          |
                                       +--------------------+---------------------+
                                                            |
                                   allegati: solo PDF e immagini
                              (fogli di calcolo, Word, GIF: esclusi qui)
                                                  |
                        PDF leggibile? --si--> pypdf, niente OCR
                                |no
                                v
                        immagine oltre 1 MB --> ridimensionata
                                |
                                v
                        ocr.space (POST /parse/image)
                                                  |
                            criteri: "telemedicina" AND "1501A"
                                su ogni documento, poi riassunti
                                                  |
                          percentuali: telemedicina + prenotazione
                                    + sentiment
                                                  |
                    200 se prenotazione certa, altrimenti 202
                        (il verdetto e' nel corpo in entrambi i casi)
```

Alcune scelte di funzionamento:

- **Parlare di telemedicina non e' prenotarla.** Nella casella arrivano fogli
  di accessi mensili, variazioni economiche, preventivi di fornitori, aperture
  di agenda e segnalazioni di guasto: contengono tutti la parola
  "telemedicina", nessuno e' una prenotazione. Per questo le due percentuali
  sono separate e i contesti amministrativi, commerciali e di assistenza
  abbassano quella di prenotazione.
- **JSON riparato in lettura.** Power Automate costruisce il corpo della
  richiesta concatenando stringhe: arrivano a capo veri dentro il corpo HTML,
  virgolette non protette (`style="..."`) e percorsi Windows (`C:\Users\...`),
  tutte cose che rendono il JSON non valido. Il servizio lo legge lo stesso e
  segnala nella risposta (`avvisi`) che cosa ha dovuto aggiustare.
- **Si legge tutto, poi si decide.** Ogni allegato leggibile passa dall'OCR e
  ogni testo concorre al verdetto: nessuna scorciatoia si ferma al primo
  documento utile, e nessun filtro a monte impedisce di leggere gli allegati di
  un messaggio dall'oggetto generico. Un'impegnativa allegata a un'email che
  dice solo "in allegato quanto richiesto" e' esattamente il caso che si vuole
  riconoscere.
- **Il PDF si legge da solo, quando puo'.** Se ha un livello di testo, quello
  e' il testo del documento: esatto, immediato, senza consumare quota. All'OCR
  ci si va solo quando la lettura fallisce o non produce testo utile, cioe'
  quando il PDF e' una scansione.
- **Solo PDF e immagini.** Fogli di calcolo, documenti Word e archivi non
  vengono aperti: non c'e' modo di ricavarne testo con l'OCR. Non compaiono fra
  i documenti della risposta e **non entrano in nessun conteggio**: un file
  chiamato `ACCESSI IN TELEMEDICINA_Maggio.xlsx` non sposta di un punto la
  sicurezza del servizio, visto che il suo contenuto resta illeggibile. Le
  **GIF** sono escluse anche se immagini: ocr.space le rifiuta, e in una email
  aziendale sono quasi sempre il logo animato della firma.
- **Le immagini grandi si riducono, non si perdono**: una foto di impegnativa
  scattata col telefono supera sempre il MB del piano gratuito. Viene scalata
  per gradi finche' non rientra, conservando la risoluzione piu' alta possibile
  perche' i caratteri restino leggibili.
- **Chi vuole leggere di piu' o spendere di meno puo' regolarlo**:
  `ocr.always_call: true` manda all'OCR anche i PDF gia' leggibili (recupera i
  timbri, costa una chiamata a documento); `attachments.analyze_all: false`,
  `screening.stop_on_failure: true` e `confidence.min_percent_for_ocr`
  riportano il servizio al comportamento parsimonioso.
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

# Con uv (consigliato)
uv sync

# Oppure con venv + pip
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
| `attachments.analyze_all` | `true` legge tutti i file, `false` si ferma al primo conforme |
| `attachments.return_text` | restituisci nella risposta il testo letto dai documenti |
| `attachments.max_text_chars` | quanto testo restituire per documento (`0` = tutto) |
| `ocr.always_call` | `true` manda all'OCR anche i PDF che si leggono da soli |
| `ocr.resize_oversized_images` | ridimensiona le immagini oltre `ocr.max_file_bytes` invece di saltarle |
| `local_files.enabled` | leggi gli allegati indicati per percorso (campo `attchment`) |
| `local_files.allowed_directories` | cartelle da cui e' lecito leggere: da riempire se il servizio e' raggiungibile in rete |
| `local_files.search_directories` | dove cercare il file per nome se il percorso non esiste |
| `confidence.telemedicine_threshold` | sopra questa percentuale il messaggio "e' telemedicina" |
| `confidence.booking_threshold` | sopra questa percentuale "e' una prenotazione" |
| `confidence.certainty_threshold` | sopra questa percentuale la prenotazione e' *certa*: e' cio' che fa rispondere `200` |
| `confidence.min_percent_for_ocr` | sotto questa percentuale non si chiama l'OCR |
| `sentiment.booking_threshold` | sopra questa soglia il messaggio e' "una prenotazione" (punteggio storico, da `0` a `1`) |
| `api.host` / `api.port` | dove ascolta il servizio (le variabili `API_HOST` e `PORT` hanno la precedenza) |
| `ocr.max_file_bytes` / `ocr.max_pdf_pages_per_request` | limiti del piano ocr.space |

## Avvio del servizio

```bash
# Con uv (consigliato)
uv run --isolated inoltro-email serve
uv run --isolated inoltro-email serve --port 9000 --reload

# Oppure con modulo
uv run python -m inoltro_email serve
uv run python -m inoltro_email serve --port 9000 --reload

# Oppure direttamente (se il venv e' attivo)
python -m inoltro_email serve
python -m inoltro_email serve --port 9000 --reload
```

In produzione si puo' usare direttamente uvicorn con piu' processi:

```bash
# Con uv
uv run uvicorn inoltro_email.api.server:build --factory --host 0.0.0.0 --port 8000 --workers 4

# Oppure direttamente
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

E' accettata anche la forma del flusso che salva gli allegati su disco e ne
manda solo il percorso. La chiave `attchment` e' scritta cosi', senza la "a", ed
e' presa com'e'; `date` vale come data di ricezione:

```json
{
  "subject": "Richiesta prenotazione televisita",
  "body": "<html>...</html>",
  "date": "08/20/2026 10:26",
  "attchment": "C:\\Users\\user\\Documents\\Power Automate\\Allegati\\impegnativa.png"
}
```

Piu' allegati si indicano con un elenco. Se il flusso li scrive in fila senza
ripetere la chiave (`"attchment":"uno.png","due.pdf"`) vengono raccolti lo
stesso. I file vengono cercati al percorso indicato e, se non c'e', per nome
nelle cartelle di `local_files.search_directories`.

### Risposta

```json
{
  "id_messaggio": "<0123@example.com>",
  "oggetto": "Richiesta prenotazione televisita",
  "esito": "conforme",
  "conforme": true,
  "prenotazione_telemedicina": true,
  "prenotazione_certa": true,
  "telemedicina": {
    "percentuale": 99.9,
    "livello": "molto alta",
    "confermato": true,
    "indizi_a_favore": [
      { "indizio": "televisita", "dove": "oggetto", "peso": 3.2 },
      { "indizio": "televisita ripreso nel corpo", "dove": "corpo", "peso": 0.8 },
      { "indizio": "telemedicina nel documento letto", "dove": "documento", "peso": 2.4 },
      { "indizio": "documento con tutti i criteri", "dove": "documento", "peso": 2.5 }
    ],
    "indizi_contrari": []
  },
  "prenotazione": {
    "percentuale": 99.6,
    "livello": "molto alta",
    "confermato": true,
    "indizi_a_favore": [
      { "indizio": "tema telemedicina al 100%", "dove": "telemedicina", "peso": 2.0 },
      { "indizio": "prenotazione", "dove": "oggetto", "peso": 2.4 },
      { "indizio": "impegnativa", "dove": "corpo", "peso": 1.2 },
      { "indizio": "richiesta esplicita", "dove": "corpo", "peso": 0.4 },
      { "indizio": "documento con tutti i criteri", "dove": "documento", "peso": 2.8 }
    ],
    "indizi_contrari": []
  },
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
      "sorgente": "pdf_text+ocr",
      "caratteri": 512,
      "conforme": true,
      "trovati": ["telemedicina", "1501A"],
      "mancanti": [],
      "nota": null,
      "errore": null,
      "testo": "ASL SALERNO - RICHIESTA DI TELEMEDICINA\nprestazione 1501A ...",
      "testo_troncato": false
    },
    {
      "nome": "foto.png",
      "origine": "allegato",
      "sorgente": "ocr",
      "caratteri": 42,
      "conforme": false,
      "trovati": ["telemedicina"],
      "mancanti": ["1501A"],
      "nota": "immagine ridotta da 2400x1800 (3717838 byte) a lato lungo 2000 (316504 byte) per il limite dell'OCR",
      "errore": null,
      "testo": "TELEVISITA CARDIOLOGIA - piano terapeutico",
      "testo_troncato": false
    }
  ],
  "documenti_letti": 2,
  "documenti_conformi": 1,
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
  "avvisi": [],
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

### I documenti letti

`documenti` elenca **tutti** gli allegati analizzati, in ordine di arrivo: il
servizio non si ferma al primo utile. Compaiono solo PDF e immagini; ogni altro
formato viene escluso a monte, non entra nell'elenco e non influenza le
percentuali.

| Campo | Significato |
|---|---|
| `sorgente` | `pdf_text` letto direttamente dal PDF, senza OCR; `ocr` letto da ocr.space; `pdf_text+ocr` i due testi uniti (con `ocr.always_call: true`); `skipped` non leggibile; `error` lettura fallita |
| `testo` | il testo letto, troncato a `attachments.max_text_chars`. Si esclude con `attachments.return_text: false` |
| `nota` | cosa e' stato fatto al file prima di leggerlo, oggi il ridimensionamento di un'immagine troppo grande |
| `conforme` | questo singolo documento contiene **tutti** i criteri |

`criteri` riassume invece l'intero messaggio: `trovati` e' l'unione di quanto
letto in tutti i documenti, `mancanti` elenca solo cio' che non compare in
nessuno. `soddisfatti` resta vero soltanto se **un singolo** documento contiene
tutti i criteri: l'impegnativa e' un foglio solo, e trovare "telemedicina" in un
file e "1501A" in un altro non equivale ad averla.

`documenti_letti` e `documenti_conformi` sono i due conteggi che servono al
flusso per decidere senza scorrere l'elenco.

### Le percentuali di sicurezza

`telemedicina.percentuale` e `prenotazione.percentuale` vanno da `0` a `100` e
rispondono a due domande diverse:

| Campo | Domanda | Soglia |
|---|---|---|
| `telemedicina` | il messaggio riguarda la telemedicina? | `confidence.telemedicine_threshold` |
| `prenotazione` | e' la prenotazione di una prestazione di telemedicina? | `confidence.booking_threshold` |
| `prenotazione_telemedicina` | verdetto unico: entrambe sopra soglia | - |
| `prenotazione_certa` | prenotazione oltre la soglia di *certezza*: fa rispondere `200` | `confidence.certainty_threshold` |

Ogni indizio vale un peso: si sommano e la somma diventa una percentuale. Sono
tutti riportati in `indizi_a_favore` e `indizi_contrari`, con il punto del
messaggio da cui arrivano (`oggetto`, `corpo`, `citato`, `allegati`,
`documento`, `indirizzi`), quindi la percentuale e' sempre giustificabile.

Cosa alza la percentuale di **telemedicina**: i termini `telemedicina`,
`televisita`, `teleconsulto`, `telemonitoraggio`, `teleassistenza` nell'oggetto
(molto), nel corpo (parecchio), nel nome di un allegato o nel testo letto
dall'OCR. Pesano meno se compaiono solo nella parte citata di una risposta, e
quasi nulla se compaiono solo dentro un indirizzo di posta
(`telemedicina@aslsalerno.it` in copia non rende il messaggio una questione di
telemedicina).

Cosa alza quella di **prenotazione**: `prenotazione`, `televisita`, `visita`,
`impegnativa`, `piano terapeutico`, `telemedicina`, `appuntamento`, `ricetta`,
il codice `1501A`, i riferimenti di una prenotazione, la richiesta di
disponibilita' e - soprattutto - un allegato che soddisfa tutti i criteri. Cosa
la abbassa: rendiconti di accessi e presenze, pratiche economiche, documenti
commerciali, newsletter, segnalazioni di guasto, richieste di apertura agenda o
di abilitazione a una piattaforma, e risposte automatiche. Le disdette pesano
piu' di tutto il resto messo insieme: chi scrive per annullare usa le stesse
parole di chi prenota, quindi il segnale contrario deve poterle azzerare.

### Parole scritte male

I termini che contano vengono riconosciuti anche con un errore di battitura -
`telvisita`, `televista`, `telveisita`, `prenotazine`, `impegnatva`,
`terapetico` - e la stessa tolleranza copre gli errori dell'OCR, che su una
scansione storta sbaglia proprio queste parole. Il punteggio non cambia: una
richiesta scritta male vale quanto la stessa scritta bene, e l'indizio riporta
la forma davvero letta (`"televisita (scritto 'telvisita')"`).

Quanta differenza si accetta dipende dalla lunghezza: due lettere su
`telemonitoraggio`, una su `impegnativa`, nessuna sotto le sei lettere. Le
parole italiane vicine a un termine ma di altro significato sono escluse a
mano: `vista` dista una sola lettera da `visita`, e "dal nostro punto di vista"
non e' una richiesta di visita.

`sentiment.punteggio` va da `-1` (negativo) a `+1` (positivo);
`sentiment.prenotazione.punteggio` va da `0` a `1` ed e' confrontato con
`sentiment.booking_threshold` per ottenere `e_prenotazione`. Resta per
compatibilita': per decidere conviene usare `prenotazione_telemedicina`.

`avvisi` elenca i problemi non bloccanti trovati nel payload: JSON riparato in
lettura, allegati indicati per percorso ma non trovati, corpo non risolto dal
flusso (`Unknown Property 'HtmlBody'`). L'analisi va avanti lo stesso, ma sono
il segnale che il flusso Power Automate va corretto a monte.

### Codici di stato

Il codice dice l'esito senza bisogno di leggere il corpo:

| Codice | Significato |
|---|---|
| `200` | **e' una prenotazione di telemedicina**, con sicurezza oltre `confidence.certainty_threshold` |
| `202` | messaggio analizzato: non e' una prenotazione, o non lo e' con sicurezza sufficiente |
| `400` | payload non interpretabile nemmeno dopo le riparazioni |
| `401` | chiave assente o errata nell'header `X-API-Key` |
| `413` | richiesta oltre `api.max_request_bytes` |

`200` e `202` portano **entrambi** il verdetto completo nel corpo: il `202` non
e' un errore, e' l'esito "analizzato, non e' una prenotazione". Gli errori veri
hanno invece la forma `{"errore": "...", "codice": 400}`.

Sono due codici `2xx` per una ragione pratica: **Power Automate considera
fallita l'azione HTTP davanti a un `4xx`**. Usare un codice di errore per dire
"non e' una prenotazione" manderebbe il flusso in errore e, con i tentativi
automatici attivi, farebbe rianalizzare lo stesso messaggio consumando altra
quota OCR.

Nel flusso si distinguono cosi':

```
outputs('HTTP')['statusCode'] uguale a 200   ->  e' una prenotazione, si procede
```

La soglia si sposta con `confidence.certainty_threshold` (predefinita `80`).
Misurata sui messaggi reali, separa nettamente: una richiesta esplicita di
prenotazione sta sopra il 96%, una richiesta generica di televisita al 63%, un
rinnovo di piano terapeutico al 73%, un'apertura di agenda al 13%. Chi vuole
che anche i casi intermedi passino senza revisione umana la abbassa.

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

     **Racchiudere ogni campo dinamico fra virgolette e passarlo da
     `json()`/`string()`**: senza, il corpo HTML finisce nel JSON con gli a capo
     veri e le virgolette dei suoi attributi, e il payload non e' JSON valido.
     Il servizio lo ripara e lo analizza lo stesso, ma lo segnala in `avvisi`.

     Se il flusso salva gli allegati in una cartella invece di passarli in
     base64, basta mandarne il percorso:

     ```
     {
       "subject": "@{triggerOutputs()?['body/subject']}",
       "body": @{json(triggerOutputs()?['body/body'])},
       "date": "@{triggerOutputs()?['body/receivedDateTime']}",
       "attchment": "@{items('Applica_a_ogni')?['FullPath']}"
     }
     ```

     Il servizio legge i file da quei percorsi e li manda all'OCR: devono quindi
     essere raggiungibili dalla macchina su cui gira il servizio (stessa
     macchina, o una cartella condivisa indicata in
     `local_files.search_directories`).

     > **Attenzione**: i file indicati nel payload vengono caricati su
     > ocr.space. Se il servizio e' raggiungibile da altre macchine, riempire
     > `local_files.allowed_directories` con la sola cartella degli allegati:
     > senza, chiunque possa chiamare l'endpoint sceglie quali file del disco
     > (fra quelli con estensione ammessa) finiscono all'OCR. All'avvio il
     > servizio lo segnala nei log.
3. **Condizione** sul risultato. Il modo piu' diretto e' il codice di stato:
   `outputs('HTTP')['statusCode']` uguale a `200` significa "e' certamente una
   prenotazione di telemedicina". Attenzione: nell'azione HTTP va disattivato
   *"Considera come esito negativo"* per i codici diversi da 200, altrimenti il
   `202` interrompe il flusso.

   Se servono distinzioni piu' fini, i campi del corpo restano disponibili:
   - `body('HTTP')?['prenotazione_certa']` -> lo stesso verdetto del `200`;
   - `body('HTTP')?['prenotazione_telemedicina']` -> prenotazione probabile,
     sopra la soglia di conferma ma non necessariamente di certezza: e' il
     gruppo da far guardare a una persona;
   - `body('HTTP')?['telemedicina']?['percentuale']` maggiore di `70` -> riguarda
     la telemedicina, a qualunque titolo;
   - `body('HTTP')?['conforme']` uguale a `true` -> un allegato contiene tutti i
     criteri (`telemedicina` + `1501A`).
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
# Con uv (consigliato)
uv run --isolated inoltro-email analizza email.json
uv run --isolated inoltro-email analizza /path/to/email.json

# Oppure con modulo
uv run python -m inoltro_email analizza email.json

# Oppure con python direttamente
python -m inoltro_email analizza email.json
cat email.json | python -m inoltro_email analizza
```

**Provare OCR e criteri su un singolo file**:

```bash
# Con uv
uv run --isolated inoltro-email check-file impegnativa.pdf --show-text

# Oppure con python direttamente
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
├── rawjson.py         lettura tollerante del JSON non valido prodotto dal flusso
├── inbound.py         lettura del payload di Power Automate (HTML, base64, foto del corpo, percorsi su disco)
├── confidence.py      percentuali di sicurezza: telemedicina e prenotazione
├── spelling.py        riconoscimento dei termini scritti male (refusi e OCR)
├── matching.py        normalizzazione del testo, screening e criteri telemedicina/1501A
├── analysis.py        orchestrazione: screening -> sicurezza -> OCR -> criteri -> percentuali
├── sentiment.py       punteggio di polarita' e di intento di prenotazione
├── models.py          strutture dati condivise
├── logging_setup.py   log su console e su un file per ogni sessione
├── ocr/
│   ├── ocrspace.py    client HTTP di ocr.space, con nuovi tentativi
│   └── extractor.py   scelta della strategia: livello di testo del PDF o OCR
└── outlook/
    ├── protocol.py    interfacce usate dalla pipeline (niente Graph)
    ├── client.py      implementazione su Microsoft Graph (libreria O365)
    └── poller.py      controllo periodico della casella
```

`analysis.py` non conosce HTTP e `api/app.py` non conosce l'OCR: la logica e'
collaudabile senza far partire il server e senza rete.

## Test

```bash
# Con uv (consigliato)
uv sync --extra dev
uv run --isolated pytest

# Oppure con pip
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

**I log.** Ogni avvio del programma scrive il proprio file, con data e ora di
inizio nel nome: `logs/servizio-20250521-091500.log` per una sessione partita il
21 maggio 2025 alle 9:15. Le esecuzioni non si mescolano piu' e la prima riga di
ogni file dice quale comando e' stato lanciato e quando. Si regola dalla sezione
`logging` di `config.yaml`:

| Chiave | Effetto |
| --- | --- |
| `file` | modello del nome (`logs/servizio.log`), da cui si ricava quello di sessione |
| `per_session` | `false` per tornare a un unico file cumulativo |
| `keep_sessions` | quanti file conservare; i piu' vecchi vengono cancellati all'avvio (`0` = tutti) |
