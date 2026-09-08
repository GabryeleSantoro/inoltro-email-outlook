---
type: "code-explanation"
date: "2026-09-08T08:41:49.121001+00:00"
question: "Guidare modifica Power Automate Desktop per invio allegati"
contributor: "graphify"
outcome: "useful"
source_nodes: ["_read_attachments()", "_read_path_attachments()", "parse_email()"]
---

# Q: Guidare modifica Power Automate Desktop per invio allegati

## Answer

Power Automate Desktop serializza Email attachments come metadati e non include i byte. Configurare Recupera messaggi email da Outlook per salvare gli allegati, creare per ogni email una lista dei percorsi completi e assegnarla a EmailPayload attchment, chiave intenzionalmente senza a. Alternativa: convertire ogni file in Base64 e creare oggetti con name e contentBytes.

## Outcome

- Signal: useful

## Source Nodes

- _read_attachments()
- _read_path_attachments()
- parse_email()