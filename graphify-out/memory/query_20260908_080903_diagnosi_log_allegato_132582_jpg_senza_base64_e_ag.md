---
type: "query"
date: "2026-09-08T08:09:03.554182+00:00"
question: "Diagnosi log allegato 132582.jpg senza base64 e aggiunta flag --dev per non salvare email e saltare duplicati"
contributor: "graphify"
outcome: "useful"
source_nodes: ["LocalMessageStore", "create_app()", "run()", "main()", "_read_attachments()"]
---

# Q: Diagnosi log allegato 132582.jpg senza base64 e aggiunta flag --dev per non salvare email e saltare duplicati

## Answer

Expanded from original query via vocab: [dev, development, registra, registrazione, registro, localmessagestore, message, serve, cli]. Il payload contiene il descrittore 132582.jpg ma non i byte: la presenza visiva in Outlook o nel messaggio inoltrato non implica contentBytes nel JSON HTTP. Implementato serve --dev: nessuna apertura o scrittura del registro SQLite, nessun controllo duplicati, registra-email risponde 202 registrata false; propagazione supportata anche da main.py e worker reload. Suite completa: 277 test passati.

## Outcome

- Signal: useful

## Source Nodes

- LocalMessageStore
- create_app()
- run()
- main()
- _read_attachments()