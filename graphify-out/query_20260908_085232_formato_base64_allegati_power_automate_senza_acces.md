---
type: "code-explanation"
date: "2026-09-08T08:52:32.428328+00:00"
question: "Formato base64 allegati Power Automate senza accesso disco"
contributor: "graphify"
outcome: "useful"
source_nodes: ["_read_attachments()", "decode_base64()", "parse_email()"]
---

# Q: Formato base64 allegati Power Automate senza accesso disco

## Answer

Usare connettore Office 365 Outlook. Get emails V3 con Include Attachments true restituisce attachments con id, name, contentType e contentBytes di tipo byte, già rappresentato base64 nel JSON. Metodo robusto: per ogni metadato chiamare Get Attachment V2 con Email id e attachment id, creare lista di oggetti name contentType contentBytes isInline e assegnarla a EmailPayload attachments. Il parser accetta contentBytes direttamente o dentro Properties.

## Outcome

- Signal: useful

## Source Nodes

- _read_attachments()
- decode_base64()
- parse_email()