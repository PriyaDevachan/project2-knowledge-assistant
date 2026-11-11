# Northstar Services Policy Knowledge Assistant

A fictional Northstar Services policy assistant project. The current repository
contains only an application skeleton; the policy corpus and web app have not
been built yet. Only fictional policy passages will be sent to the hosted model.

## Setup

Use Python 3.11 or 3.12. On Windows, create the environment and install the
project dependencies from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a local `.env` file in the project root. Keep it private; `.env` is
ignored by Git. Do not paste the key into chat or put it in browser code.

```text
GROQ_API_KEY=your_key_from_your_Groq_Free_account
GROQ_MODEL=openai/gpt-oss-20b
```

Choose a model available to your own Groq Free account and set its exact ID as
`GROQ_MODEL` if the example model is unavailable. Before building the UI, run
the server-side connectivity check:

```powershell
.\.venv\Scripts\python.exe check_groq.py
```

The check sends “Reply with READY only” to the configured model and reports the
model and actual response. It never prints the API key. Do not treat a failed
or unrun check as a successful connection.

The planned evaluation data can use Python's standard-library CSV support; the
four stages are policy corpus, baseline API/UI, evaluation, and candidate
release. `knowledge_assistant/` and `tests/` currently contain only the starter
skeleton and its starter test.
