---
type: "code-explanation"
date: "2026-09-08T09:02:52.171695+00:00"
question: "Allegato Graph contiene id ma contentBytes null"
contributor: "graphify"
outcome: "useful"
source_nodes: ["_read_attachments()", "_is_inline()", "decode_base64()"]
---

# Q: Allegato Graph contiene id ma contentBytes null

## Answer

Metadati validi. Usare Email id come Message Id e Attachment id come Attachment Id in Get Attachment V2; output contentBytes contiene dati. contentBytes null nel risultato elenco indica contenuto non incluso. isInline true è immagine incorporata e backend la accetta se include_inline_images è true.

## Outcome

- Signal: useful

## Source Nodes

- _read_attachments()
- _is_inline()
- decode_base64()