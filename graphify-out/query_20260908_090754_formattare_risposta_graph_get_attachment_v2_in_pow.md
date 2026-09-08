---
type: "code-explanation"
date: "2026-09-08T09:07:54.385075+00:00"
question: "Formattare risposta Graph Get Attachment V2 in Power Automate Desktop"
contributor: "graphify"
outcome: "useful"
source_nodes: ["_read_attachments()", "decode_base64()", "parse_email()"]
---

# Q: Formattare risposta Graph Get Attachment V2 in Power Automate Desktop

## Answer

La risposta è un singolo fileAttachment con contentBytes già base64. Convertire il testo JSON in oggetto personalizzato, estrarre name contentType contentBytes isInline, creare oggetto compatto e aggiungerlo a una lista attachments. Non ricodificare contentBytes e non inviare campi odata. Per più allegati ripetere dentro il ciclo metadata.

## Outcome

- Signal: useful

## Source Nodes

- _read_attachments()
- decode_base64()
- parse_email()