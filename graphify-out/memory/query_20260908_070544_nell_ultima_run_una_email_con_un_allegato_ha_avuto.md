---
type: "query"
date: "2026-09-08T07:05:44.826004+00:00"
question: "Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["parse_email()", "_read_attachments()", "_read_path_attachments()", "EmailAnalyzer"]
---

# Q: Nell'ultima run una email con un allegato ha avuto un problema. Nei log risulta Nessun allegato nel payload. Quando dice così si intende che non ci sono elementi nel corpo email? Poi ha tentato di analizzare un allegato, ma ha loggato Nessun dato base64 ritrovato, ignorato. In che condizioni succede ciò?

## Answer

Expanded from original query via vocab: [allegati, allegato, attachment, attachments, base, data, payload, inbound]. Nessun allegato nel payload significa che email.attachments e vuoto dopo il parsing, non che il corpo email sia vuoto. Un elemento attachments viene scartato prima dell OCR se nessuna delle chiavi contentBytes, content, contentBase64 o $content contiene una stringa non vuota; base64 non valido produce invece il log non decodificabile. Se era l unico elemento, il successivo analyzer vede zero allegati. Gli allegati per percorso sotto attchment e chiavi equivalenti sono gestiti separatamente e non richiedono base64.

## Outcome

- Signal: useful

## Source Nodes

- parse_email()
- _read_attachments()
- _read_path_attachments()
- EmailAnalyzer