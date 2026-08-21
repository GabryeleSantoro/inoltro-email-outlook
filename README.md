# inoltro-email-outlook

Inoltro automatico di email da una casella **Microsoft 365 / Outlook.com**: ogni
cinque minuti il programma cerca i messaggi **non letti arrivati negli ultimi
cinque minuti**, ne legge gli allegati (PDF e immagini) con l'OCR di
[ocr.space](https://ocr.space/ocrapi) e, se il testo contiene **sia la parola
"televisita" sia il codice "1501A"**, inoltra il messaggio ai destinatari
configurati.

L'accesso alla posta avviene via **Microsoft Graph** con la libreria
[O365](https://github.com/O365/python-o365): **non serve Outlook installato**,
ne' Windows. Il programma gira anche su Linux, su macOS o dentro un container.

## Come funziona

```
ogni 5 minuti: Microsoft Graph
  messaggi non letti degli ultimi 5 minuti
        |
        v
  allegati scaricati in una cartella temporanea
        |
        v
  PDF con testo? --si--> pypdf legge il testo (nessuna chiamata OCR)
        |no
        v
  ocr.space (POST /parse/image)
        |
        v
  criteri: "televisita" AND "1501A"
        |
        v
  Graph: inoltro -> destinatari  +  categoria "Inoltrata-Televisita"
```

Alcune scelte di funzionamento:

- **Selezione fatta dal servizio**: la finestra temporale e il filtro sui
  messaggi da leggere sono un `$filter` di Graph, quindi a ogni giro si scarica
  solo il poco che serve, non l'intera Posta in arrivo.
- **Nessun buco fra un controllo e l'altro**: i giri partono a intervalli fissi
  e, se uno dura piu' del previsto, la finestra del successivo si allarga al
  tempo realmente trascorso.
- **Risparmio di quota OCR**: se un PDF ha gia' il livello di testo lo si legge
  con `pypdf`, senza chiamare l'API; e non appena un allegato soddisfa i criteri
  gli altri non vengono piu' analizzati.
- **Niente doppi inoltri**: ogni messaggio elaborato viene registrato in un
  database SQLite usando l'Internet Message-ID, cosi' le finestre sovrapposte di
  due controlli consecutivi non possono inoltrare due volte lo stesso messaggio.
- **Tolleranza al rumore dell'OCR**: `15 0 10`, `15-010` e `15010` vengono
  riconosciuti come `1501A`; `tele visita` spezzata da un a capo come
  `televisita`.
- **Predefinito prudente**: `forward.dry_run: true`, quindi al primo avvio il
  programma mostra cosa *avrebbe* inoltrato senza inviare nulla.

## Requisiti

- **Python 3.9+** su qualsiasi sistema operativo (Windows, Linux, macOS).
- Una casella **Microsoft 365 / Outlook.com** e un'**applicazione registrata**
  su [Microsoft Entra ID](https://entra.microsoft.com) (vedi sotto).
- Una chiave API di [ocr.space](https://ocr.space/ocrapi) (il piano gratuito e'
  sufficiente per volumi contenuti).

Non servono Outlook Desktop ne' `pywin32`.

## Installazione

```bash
git clone https://github.com/GabryeleSantoro/inoltro-email-outlook.git
cd inoltro-email-outlook

python -m venv .venv
source .venv/bin/activate       # su Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Registrazione dell'applicazione

Una volta sola, su <https://entra.microsoft.com> -> **Registrazioni per l'app**
-> **Nuova registrazione**:

1. tipo di account: quello della propria casella (solo l'organizzazione, oppure
   anche gli account Microsoft personali);
2. **URI di reindirizzamento**: tipo *Web*, valore
   `https://login.microsoftonline.com/common/oauth2/nativeclient`;
3. in **Certificati e segreti** creare un **nuovo segreto client** e copiarne
   subito il valore (non sara' piu' visibile);
4. in **Autorizzazioni API** -> *Microsoft Graph* -> **Autorizzazioni
   delegate** aggiungere `Mail.ReadWrite` e `Mail.Send`.

Client id, segreto e tenant vanno nel file `.env` (vedi sotto). Chi preferisce
far girare il programma senza utente collegato (per esempio su un server) puo'
usare `outlook.auth_flow: credentials` con le corrispondenti **autorizzazioni
applicazione** e indicare la casella in `outlook.mailbox`.

## Configurazione

Servono due file, entrambi esclusi dal versionamento:

**1. `.env`** — i segreti (copiare da `.env.example`):

```
OCR_SPACE_API_KEY=la-tua-chiave
MS_CLIENT_ID=id-applicazione-client
MS_CLIENT_SECRET=segreto-client
MS_TENANT_ID=common
```

**2. `config.yaml`** — i parametri (copiare da `config.example.yaml`):

```bash
cp config.example.yaml config.yaml
cp .env.example .env
```

Le voci da rivedere subito:

| Voce | Significato |
|---|---|
| `forward.to` | destinatari dell'inoltro (obbligatorio) |
| `forward.dry_run` | `true` = simula soltanto. Mettere `false` per inviare davvero |
| `rules.keywords` / `rules.codes` | i termini cercati; con `mode: all` servono tutti |
| `outlook.folder` | cartella sorvegliata (`Inbox`, oppure `Inbox/Televisite`) |
| `outlook.poll_interval_minutes` | ogni quanto controllare la posta (default 5) |
| `outlook.lookback_minutes` | quanto indietro guardare a ogni controllo (default 5) |
| `outlook.unread_only` | `true` = solo i messaggi ancora da leggere |
| `outlook.catch_up_minutes` | al primo controllo dopo l'avvio guarda indietro di N minuti |
| `outlook.auth_flow` / `outlook.mailbox` | come ci si autentica e quale casella si legge |
| `ocr.max_file_bytes` / `ocr.max_pdf_pages_per_request` | limiti del piano ocr.space |

## Uso

**Autorizzare l'applicazione** (una volta sola: apre un URL da incollare nel
browser e salva il token, con il suo refresh token, in `state/o365_token.txt`):

```bash
python -m inoltro_email authenticate
```

**Provare i criteri su un file, senza toccare la casella** (e' il modo piu'
rapido per verificare chiave API e regole):

```bash
python -m inoltro_email check-file referto.pdf --show-text
```

```
File      : referto.pdf
Sorgente  : pdf_text
Caratteri : 512
Criteri   : trovati=[televisita, 1501A] mancanti=[-]
Esito     : CONFORME - la mail verrebbe inoltrata
```

**Esame una tantum dei messaggi recenti** (utile come prova, e adatto a un cron
o all'Utilita' di pianificazione di Windows):

```bash
python -m inoltro_email run-once --minutes 60 --dry-run
```

Per default si guardano solo i messaggi non letti; con `--include-read` si
esaminano anche quelli gia' aperti.

**Controllo continuo ogni cinque minuti** (modalita' di esercizio):

```bash
python -m inoltro_email watch
```

Opzioni comuni: `--config <percorso>`, `--log-level DEBUG`,
`--dry-run` / `--no-dry-run` (hanno la precedenza sul file di configurazione).

Codici di uscita: `0` esito positivo, `1` criteri non soddisfatti o errori
durante l'elaborazione, `2` problema di configurazione, `3` casella non
raggiungibile o token assente, `130` interruzione da tastiera.

## Struttura del progetto

```
src/inoltro_email/
├── __main__.py        riga di comando (authenticate | watch | run-once | check-file)
├── config.py          lettura e validazione di config.yaml + .env
├── matching.py        normalizzazione del testo e regole televisita/1501A
├── pipeline.py        orchestrazione: allegati -> testo -> criteri -> inoltro
├── state.py           registro SQLite anti-duplicato
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

`pipeline.py` dipende soltanto dalle interfacce di `outlook/protocol.py`: la
logica di business e' quindi collaudabile senza rete, con un client di posta e
un client OCR fittizi.

## Test

```bash
pip install -r requirements-dev.txt
pytest
```

La suite copre le regole di riconoscimento, il client ocr.space (rete simulata,
compresi i nuovi tentativi su HTTP 429 e l'assenza di tentativi su chiave non
valida), la scelta fra livello di testo del PDF e OCR, la suddivisione dei PDF
lunghi, il registro anti-duplicato, il flusso completo di inoltro, il filtro
OData inviato a Graph e la tempistica del controllo periodico (con orologio
finto, quindi immediata). Non serve ne' rete ne' una casella vera.

## Note operative

**Limiti del piano gratuito di ocr.space.** File fino a 1 MB e PDF fino a 3
pagine. I PDF piu' lunghi vengono spezzati automaticamente in blocchi da
`ocr.max_pdf_pages_per_request` pagine; le immagini oltre il limite vengono
saltate con un avviso nel log (non vengono ricompresse). Con un piano a pagamento
si possono alzare `ocr.max_file_bytes` e `ocr.max_pdf_pages_per_request`.

**Motore OCR.** L'engine 2 rileva la lingua da solo e in genere e' il piu'
accurato sui documenti; se si vuole forzare l'italiano occorre impostare
`engine: 1` (o `3`) con `language: "ita"`.

**Ritardo di consegna.** Il controllo e' periodico: un messaggio viene trattato
entro `poll_interval_minutes` dal suo arrivo (cinque minuti nella
configurazione predefinita). Abbassare l'intervallo aumenta le chiamate a
Graph; tenere sempre `lookback_minutes` maggiore o uguale all'intervallo.

**Messaggi non letti.** Con `unread_only: true` un messaggio aperto in Outlook
prima del controllo successivo non viene piu' esaminato. Se la casella e'
condivisa e qualcuno la legge di persona, conviene mettere `unread_only: false`
e affidarsi al solo registro anti-duplicato.

**Il token.** `state/o365_token.txt` contiene il refresh token della casella:
va trattato come una password e non finisce nel repository (e' escluso dal
versionamento). Se scade o viene revocato, basta rieseguire
`python -m inoltro_email authenticate`. Il programma non ha bisogno di una
sessione desktop: puo' girare come servizio, in un container o su un server.

**Riservatezza.** Gli allegati vengono inviati a un servizio esterno
(ocr.space) per il riconoscimento del testo: se contengono dati personali o
sanitari occorre verificarne l'ammissibilita' prima di attivare il flusso in
produzione. I PDF gia' provvisti di testo non escono mai dalla macchina, perche'
vengono letti in locale.

**Dove finiscono i dati.** Gli allegati sono salvati in una cartella temporanea
di sistema, rimossa al termine dell'elaborazione di ogni messaggio. Restano su
disco soltanto il registro `state/processed.sqlite3` e i log in `logs/`.

**I log.** Ogni avvio del programma scrive il proprio file, con data e ora di
inizio nel nome: `logs/inoltro-20250521-091500.log` per una sessione partita il
21 maggio 2025 alle 9:15. Le esecuzioni non si mescolano piu' e la prima riga di
ogni file dice quale comando e' stato lanciato e quando. Si regola dalla sezione
`logging` di `config.yaml`:

| Chiave | Effetto |
| --- | --- |
| `file` | modello del nome (`logs/inoltro.log`), da cui si ricava quello di sessione |
| `per_session` | `false` per tornare a un unico file cumulativo |
| `keep_sessions` | quanti file conservare; i piu' vecchi vengono cancellati all'avvio (`0` = tutti) |
