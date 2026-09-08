---
type: "query"
date: "2026-09-08T08:33:36.753818+00:00"
question: "Tutte le email hanno allegati, cosa e andato storto nei log della run 2026-09-08 10:30"
contributor: "graphify"
outcome: "useful"
source_nodes: ["_read_attachments()", "parse_email()", "_from_data_uri()", "InboundAttachment"]
---

# Q: Tutte le email hanno allegati, cosa e andato storto nei log della run 2026-09-08 10:30

## Answer

Expanded from original query via vocab: [attachments, attachment, content, base, payload, inbound, flow, email]. Causa a monte nel payload Power Automate. Andrea Esposito.pdf e CRISTALDI-1.pdf arrivano come descrittori con nome ma senza contentBytes stringa, quindi _read_attachments li scarta prima dell OCR. La mail Amato arriva senza alcun descrittore attachment e senza data URI nel corpo. Il servizio non legge Outlook: vede solo JSON HTTP. Formati, limiti, --dev e avviso GIF non sono la causa. Correggere trigger/mapping per includere byte base64 o inviare percorsi attchment.

## Outcome

- Signal: useful

## Source Nodes

- _read_attachments()
- parse_email()
- _from_data_uri()
- InboundAttachment