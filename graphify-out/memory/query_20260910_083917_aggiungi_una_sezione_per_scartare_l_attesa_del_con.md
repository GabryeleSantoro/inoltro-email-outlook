---
type: "query"
date: "2026-09-10T08:39:17.882089+00:00"
question: "aggiungi una sezione per scartare l'attesa del conferma, ad esempio --skip"
contributor: "graphify"
outcome: "useful"
source_nodes: ["FlowRunner", "._click_continue()", "create_app()"]
---

# Q: aggiungi una sezione per scartare l'attesa del conferma, ad esempio --skip

## Answer

Expanded from original query via vocab: [flow, runner, confirmation, popup, click, continue]. Aggiunto serve --skip, alias --skip-confirmation: propaga skip_confirmation da CLI a server e create_app, imposta FlowRunner.auto_continue=False e funziona anche con reload.

## Outcome

- Signal: useful

## Source Nodes

- FlowRunner
- ._click_continue()
- create_app()