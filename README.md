# Northstar Services Policy Knowledge Assistant

A local FastAPI app for questions about a fictional Northstar Services policy
corpus. It uses BM25 to retrieve passages from `policy_corpus/`, then asks the
configured Groq model to answer, clarify, abstain, or report a conflict. The
model receives the question and retrieved fictional policy passages only.

## Windows setup and run

Use Python 3.11 or 3.12 from PowerShell in the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The Windows dependency installation, connectivity check, tests, and server
launch commands in this section were run with Python 3.12.10. This workspace
already had `.venv`, so the environment-creation command above was not rerun.

Create a local `.env` file in the repository root. Do not share the key, put it
in browser code, or commit this file.

```text
GROQ_API_KEY=your_key_from_your_Groq_Free_account
GROQ_MODEL=openai/gpt-oss-20b
```

Use a model ID available to your own Groq Free account if the example model is
unavailable. Make one real server-side connectivity request before using the
application:

```powershell
.\.venv\Scripts\python.exe check_groq.py
```

Run tests and start the app on loopback:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn knowledge_assistant.app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/>. The launch command binds to `127.0.0.1`, not a
public network interface.

## macOS setup and run

In Terminal, use the repository root and Python 3.11 or 3.12:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Create `.env` with the same two variables shown above, then run:

```sh
.venv/bin/python check_groq.py
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn knowledge_assistant.app:app --host 127.0.0.1 --port 8000
```

These macOS commands are provided for reproducibility but have not been
executed in this Windows environment.

## API

`GET /api/health` reports the release, configured model tag, and number of
loaded passages without revealing the API key.

`POST /api/ask` accepts JSON in this shape:

```json
{
  "question": "What is the meal limit on approved business travel?",
  "department": null,
  "as_of": null,
  "release": "baseline"
}
```

The response includes the release, decision, answer, citation passage IDs,
retrieved passage IDs and text, model tag, trace ID, elapsed time, and an error
field. Model failures are returned as failures with no assistant answer;
upstream HTTP status is recorded in the error. A citation is accepted only if
it belongs to the loaded corpus and the passages retrieved for that request.

Each request is recorded in `traces/requests.jsonl`, including the retrieval,
raw model result when available, decision, error, and elapsed time. The trace
directory is ignored by Git. The local `.env` file is also ignored.

The browser page and API are currently the **baseline** release. The repository
also contains `SOURCE_RULES.md`, the ten synthetic policy documents, their
manifest, the corpus validator, and the six Day 2 smoke questions in `DAY2.md`.
