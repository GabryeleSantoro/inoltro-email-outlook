# Initialization

When starting a new session, immediately read `graphify-out/graph.json` to load the codebase architecture into your context before answering any queries.

## Caveman Mode

Caveman mode active in this project unless user says "stop caveman" or "normal mode".

Respond terse like smart caveman. Technical substance exact. Only fluff die.

Drop articles, filler, pleasantries, and hedging. Fragments OK. Use short synonyms. Keep code, commands, quoted errors, identifiers, and security warnings exact.

Pattern: `[thing] [action] [reason]. [next step].`

Default mode: ultra. `/caveman lite`, `/caveman full`, `/caveman ultra`, `/caveman wenyan`, `/caveman wenyan-lite`, and `/caveman wenyan-ultra` switch intensity for current session.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:

- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Project

Python 3.11+ (currently 3.13) HTTP service. Analyzes one email at a time from Power Automate: checks subject/body for telemedicina keywords, reads PDF/image attachments (pypdf for text PDFs, ocr.space for scanned), returns confidence scores and sentiment.

Entry: `main.py` or `python -m inoltro_email`. Package: `src/inoltro_email/`.

## Commands

```bash
# Setup (uv preferred, pip fallback)
uv sync                          # install + lockfile
pip install -r requirements.txt  # fallback
pip install -r requirements-dev.txt  # add test deps

# Run server
python -m inoltro_email serve
python -m inoltro_email serve --port 9000 --reload

# CLI analysis (no server needed)
python -m inoltro_email analizza email.json
cat email.json | python -m inoltro_email analizza

# Single file check
python -m inoltro_email check-file impegnativa.pdf --show-text

# Production (multi-worker)
uvicorn inoltro_email.api.server:build --factory --host 0.0.0.0 --port 8000 --workers 4

# Tests (no network required)
pytest
pytest tests/test_confidence.py  # single file
pytest -k "test_booking"         # single test
```

## Config

- `.env` — secrets: `OCR_SPACE_API_KEY`, `SERVICE_API_KEY` (copied from `.env.example`)
- `config.yaml` — all params (copied from `config.example.yaml`, gitignored)
- Env vars `API_HOST`/`PORT` override `config.yaml`

## Key Architecture

- `analysis.py` — orchestrator: screening → confidence → OCR → criteria → scores. No HTTP knowledge.
- `api/app.py` — FastAPI routes. No OCR knowledge.
- `inbound.py` — Power Automate payload parsing (HTML, base64, inline images, disk paths).
- `ocr/ocrspace.py` — ocr.space HTTP client with retries.
- `ocr/extractor.py` — decides: PDF text layer vs OCR.
- `confidence.py` — scoring (telemedicina + booking).
- `spelling.py` — fuzzy matching for OCR typos and misspellings.
- `rawjson.py` — repairs broken JSON from Power Automate (unescaped quotes, real newlines).

## Gotchas

- Payload JSON often malformed (newlines in HTML body, unescaped quotes in attributes, Windows paths). `rawjson.py` fixes on read; warnings go to `avvisi`.
- `attchment` key is intentionally misspelled (matches Power Automate flow output).
- OCR quota: free tier = 1MB/file, 3 pages/PDF. Large images auto-resized before send.
- HTTP 200 = confirmed booking, 202 = analyzed but not booking. Both carry full result in body. Power Automate treats 4xx as failure, so 202 avoids false error retries.
- Only PDF and images processed; .xlsx, .docx, .gif ignored (GIF rejected by ocr.space).
- Tests use `FakeOcrClient` — no real network calls needed.
- `conftest.py` adds `src/` to sys.path; tests run from repo root.
- No CI, no pre-commit hooks, no Makefile in this repo.
