---
type: "code-explanation"
date: "2026-09-08T08:58:44.418436+00:00"
question: "Power Automate Attachments non contiene id per Get Attachment V2"
contributor: "graphify"
outcome: "useful"
source_nodes: ["_read_attachments()", "parse_email()"]
---

# Q: Power Automate Attachments non contiene id per Get Attachment V2

## Answer

La variabile proviene dall azione Outlook desktop Retrieve email messages, che produce Outlook mail objects e salva allegati solo su disco; non espone attachment Graph id. Sostituire recupero con Office 365 Outlook Get emails V3. Il risultato ha value, ogni email ha id e attachments; ogni attachment Graph ha id. Con Include Attachments true arriva anche contentBytes. In alternativa usare email id e attachment id con Get Attachment V2.

## Outcome

- Signal: useful

## Source Nodes

- _read_attachments()
- parse_email()