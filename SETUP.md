# Day 2 setup: web app on your laptop, hosted model API

You do **not** need to install or run a language model on your computer. Your FastAPI app runs locally; it sends only the **fictional policy passages** and question to a model through a student-owned Groq Free account. Keep real personal, institute or company data out of this project.

## 1. Get a Groq API key on the Free plan

1. Open the [Groq Console](https://console.groq.com/) and sign in with your own legitimate account. Stay on the **Free** plan; do not enter a payment card or upgrade.
2. Open [API Keys](https://console.groq.com/keys), create a key for this project and copy it once. Treat it like a password. Do not send it to the trainer, classmates, a coding assistant or GitHub.
3. In the console, check which text models and limits are available **to your account**. The example model for this pack is `openai/gpt-oss-20b`, which Groq currently lists as supported. If it is not available to you, select a model your Free account allows and write its exact ID in your README. Free limits can differ by account and can change.

Groq's [official quickstart](https://console.groq.com/docs/quickstart) shows how to create a key and call the Python SDK. Its example model may differ from the current supported list; use the model shown in your own console. Check the [supported models](https://console.groq.com/docs/models) and [rate-limit explanation](https://console.groq.com/docs/rate-limits) before running a batch.

## 2. Install Python and create your own folder

Install Python **3.11 or 3.12** from [python.org](https://www.python.org/downloads/) if needed. Create a folder that you own, separate from Project 1.

**Windows PowerShell:**

```powershell
mkdir project2-knowledge-assistant
cd project2-knowledge-assistant
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

If Python 3.12 is unavailable, replace `-3.12` with `-3.11`. Later Python commands use `.\.venv\Scripts\python.exe`.

**macOS Terminal:**

```sh
mkdir project2-knowledge-assistant
cd project2-knowledge-assistant
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
```

If `python3.12` is unavailable but `python3.11` is installed, use `python3.11 -m venv .venv`. Check that your virtual-environment Python reports 3.11 or 3.12.

## 3. Store the key privately

Before entering a key, create a `.gitignore` file containing these lines:

```text
.env
.venv/
__pycache__/
*.log
```

Create a file named `.env` **inside your project folder**, with your real key on your own laptop:

```text
GROQ_API_KEY=your_actual_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

Do not paste the real key into a coding prompt or shared message. Ask the coding assistant to load `.env` using `python-dotenv` **on the server side only**. The key must never appear in browser JavaScript, an API response, Git history, a screenshot or the final ZIP. If you accidentally expose it, revoke it in Groq Console and create a new one.

## 4. Make one real model call before building the UI

Use Prompt 0 in `PROMPTS.md` to create `requirements.txt` and the repo skeleton. Install the generated requirements with the virtual-environment Python:

**Windows:**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS:**

```sh
.venv/bin/python -m pip install -r requirements.txt
```

The requirements should include the Groq Python SDK (`groq`), `python-dotenv`, FastAPI, Uvicorn, BM25 retrieval, pytest and any other packages the code actually imports. Use the coding assistant to create a **small server-side connectivity check** that sends “Reply with READY only” through Groq. Run it yourself. Record the model ID, status and response **without showing the key**. Only then move to policy documents and the web UI.

## 5. If the API call fails

- **401:** check that your key was copied correctly and `.env` was loaded. Do not print the key.
- **400/model not found:** use a model your console lists for your account; update `GROQ_MODEL` and record the choice.
- **429:** you reached a rate limit. Record the error and wait according to the response; do not create repeated accounts or replace the output with a fake success.
- **Network or 5xx:** record the exact error and time. Continue work on the corpus and evaluation cases while waiting. Report the blocked model call clearly.

No local LLM setup, paid service or trainer-provided key is required.
