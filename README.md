# inoltro-email-outlook

Inoltro automatico di email tramite **Outlook Desktop**: quando arriva un messaggio,
il programma ne legge gli allegati (PDF e immagini) con l'OCR di
[ocr.space](https://ocr.space/ocrapi) e, se il testo contiene **sia la parola
"televisita" sia il codice "1501A"**, inoltra il messaggio ai destinatari
configurati.

## Come funziona

```
Outlook (evento NewMailEx)
        |
        v
  allegati salvati in una cartella temporanea
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
  Outlook: Forward() -> destinatari  +  categoria "Inoltrata-Televisita"
```

Alcune scelte di funzionamento:

- **Attivazione reale all'arrivo**: si usa l'evento COM `NewMailEx` di Outlook,
  non un polling a intervalli.
- **Risparmio di quota OCR**: se un PDF ha gia' il livello di testo lo si legge
  con `pypdf`, senza chiamare l'API; e non appena un allegato soddisfa i criteri
  gli altri non vengono piu' analizzati.
- **Niente doppi inoltri**: ogni messaggio elaborato viene registrato in un
  database SQLite usando l'Internet Message-ID, cosi' l'evento e la scansione di
  recupero all'avvio non possono inoltrare due volte lo stesso messaggio.
- **Tolleranza al rumore dell'OCR**: `15 0 10`, `15-010` e `15010` vengono
  riconosciuti come `1501A`; `tele visita` spezzata da un a capo come
  `televisita`.
- **Predefinito prudente**: `forward.dry_run: true`, quindi al primo avvio il
  programma mostra cosa *avrebbe* inoltrato senza inviare nulla.

## Requisiti

- **Windows** con **Outlook Desktop** installato e configurato (la modalita' di
  ascolto usa COM; `check-file` funziona su qualsiasi sistema operativo).
- **Python 3.9+**.
- Una chiave API di [ocr.space](https://ocr.space/ocrapi) (il piano gratuito e'
  sufficiente per volumi contenuti).

## Installazione

```cmd
git clone https://github.com/GabryeleSantoro/inoltro-email-outlook.git
cd inoltro-email-outlook

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

## Configurazione

Servono due file, entrambi esclusi dal versionamento:

**1. `.env`** — la chiave API (copiare da `.env.example`):

```
OCR_SPACE_API_KEY=la-tua-chiave
```

**2. `config.yaml`** — i parametri (copiare da `config.example.yaml`):

```cmd
copy config.example.yaml config.yaml
copy .env.example .env
```

Le voci da rivedere subito:

| Voce | Significato |
|---|---|
| `forward.to` | destinatari dell'inoltro (obbligatorio) |
| `forward.dry_run` | `true` = simula soltanto. Mettere `false` per inviare davvero |
| `rules.keywords` / `rules.codes` | i termini cercati; con `mode: all` servono tutti |
| `outlook.folder` | cartella sorvegliata (`Inbox`, oppure `Inbox/Televisite`) |
| `outlook.catch_up_minutes` | all'avvio rilegge i messaggi degli ultimi N minuti |
| `ocr.max_file_bytes` / `ocr.max_pdf_pages_per_request` | limiti del piano ocr.space |

## Uso

**Provare i criteri su un file, senza toccare Outlook** (funziona anche su
Linux/macOS: e' il modo piu' rapido per verificare chiave API e regole):

```cmd
python -m inoltro_email check-file C:\percorso\referto.pdf --show-text
```

```
File      : C:\percorso\referto.pdf
Sorgente  : pdf_text
Caratteri : 512
Criteri   : trovati=[televisita, 1501A] mancanti=[-]
Esito     : CONFORME - la mail verrebbe inoltrata
```

**Esame una tantum dei messaggi recenti** (utile come prova, e adatto
all'Utilita' di pianificazione di Windows):

```cmd
python -m inoltro_email run-once --minutes 60 --dry-run
```

**Ascolto continuo** (modalita' di esercizio):

```cmd
python -m inoltro_email watch
```

Opzioni comuni: `--config <percorso>`, `--log-level DEBUG`,
`--dry-run` / `--no-dry-run` (hanno la precedenza sul file di configurazione).

Codici di uscita: `0` esito positivo, `1` criteri non soddisfatti o errori
durante l'elaborazione, `2` problema di configurazione, `3` Outlook non
raggiungibile, `130` interruzione da tastiera.

## Struttura del progetto

```
src/inoltro_email/
├── __main__.py        riga di comando (watch | run-once | check-file)
├── config.py          lettura e validazione di config.yaml + .env
├── matching.py        normalizzazione del testo e regole televisita/1501A
├── pipeline.py        orchestrazione: allegati -> testo -> criteri -> inoltro
├── state.py           registro SQLite anti-duplicato
├── models.py          strutture dati condivise
├── logging_setup.py   log su console e su file rotante
├── ocr/
│   ├── ocrspace.py    client HTTP di ocr.space, con nuovi tentativi
│   └── extractor.py   scelta della strategia: livello di testo del PDF o OCR
└── outlook/
    ├── protocol.py    interfacce usate dalla pipeline (niente COM)
    ├── client.py      implementazione COM (pywin32)
    └── watcher.py     evento NewMailEx e ciclo di ascolto
```

`pipeline.py` dipende soltanto dalle interfacce di `outlook/protocol.py`: la
logica di business e' quindi collaudabile senza Windows e senza rete, con un
client di posta e un client OCR fittizi.

## Test

```cmd
pip install -r requirements-dev.txt
pytest
```

La suite copre le regole di riconoscimento, il client ocr.space (rete simulata,
compresi i nuovi tentativi su HTTP 429 e l'assenza di tentativi su chiave non
valida), la scelta fra livello di testo del PDF e OCR, la suddivisione dei PDF
lunghi, il registro anti-duplicato e il flusso completo di inoltro. Non serve
Windows: il layer COM e' sostituito da un client fittizio.

## Note operative

**Limiti del piano gratuito di ocr.space.** File fino a 1 MB e PDF fino a 3
pagine. I PDF piu' lunghi vengono spezzati automaticamente in blocchi da
`ocr.max_pdf_pages_per_request` pagine; le immagini oltre il limite vengono
saltate con un avviso nel log (non vengono ricompresse). Con un piano a pagamento
si possono alzare `ocr.max_file_bytes` e `ocr.max_pdf_pages_per_request`.

**Motore OCR.** L'engine 2 rileva la lingua da solo e in genere e' il piu'
accurato sui documenti; se si vuole forzare l'italiano occorre impostare
`engine: 1` (o `3`) con `language: "ita"`.

**Il programma deve girare nella sessione desktop dell'utente**, con Outlook
aperto: gli eventi COM non arrivano a un servizio Windows in sessione 0. Per
l'avvio automatico conviene una voce nella cartella Esecuzione automatica o
un'attivita' pianificata "solo quando l'utente ha effettuato l'accesso".

**Avviso di sicurezza di Outlook.** L'invio programmatico puo' far comparire il
messaggio "Un programma sta tentando di inviare un messaggio per conto
dell'utente" se sulla macchina non risulta un antivirus aggiornato registrato in
Centro sicurezza PC. Su postazioni gestite il problema non si presenta; in
alternativa si puo' agire sui criteri di gruppo per l'accesso programmatico a
Outlook.

**Riservatezza.** Gli allegati vengono inviati a un servizio esterno
(ocr.space) per il riconoscimento del testo: se contengono dati personali o
sanitari occorre verificarne l'ammissibilita' prima di attivare il flusso in
produzione. I PDF gia' provvisti di testo non escono mai dalla macchina, perche'
vengono letti in locale.

**Dove finiscono i dati.** Gli allegati sono salvati in una cartella temporanea
di sistema, rimossa al termine dell'elaborazione di ogni messaggio. Restano su
disco soltanto il registro `state/processed.sqlite3` e i log in `logs/`.
