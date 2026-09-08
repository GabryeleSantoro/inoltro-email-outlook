---
type: "query"
date: "2026-09-08T09:22:14.795951+00:00"
question: "nel log, stampa il json ricevuto troncando il contentByte invece del corpo e di tutte le informazioni. Stampa dunque il risultato così come sta"
contributor: "graphify"
outcome: "useful"
source_nodes: ["_read_email_request()", "_payload_to_log()", "._log_inbound_email()", "test_api.py"]
---

# Q: nel log, stampa il json ricevuto troncando il contentByte invece del corpo e di tutte le informazioni. Stampa dunque il risultato così come sta

## Answer

Query expanded to graph vocab: [payload, logging, json, request, body, content, bytes, email, attachments, ricevuto, corpo, troncato]. Implementato log INFO PAYLOAD JSON RICEVUTO con struttura completa del payload e troncamento ricorsivo dei soli campi contentBytes/contentByte a 80 caratteri più lunghezza totale. Rimossi log duplicati Email ricevuta, Corpo testo/HTML, riepilogo allegati e EMAIL RICEVUTA. Screening, OCR ed esiti restano. Aggiunto test di integrazione; suite 278 test passata.

## Outcome

- Signal: useful

## Source Nodes

- _read_email_request()
- _payload_to_log()
- ._log_inbound_email()
- test_api.py