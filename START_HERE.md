# Project 2 — Build and test a knowledge assistant

**Four-day individual project. Day 2 is Thursday, 12 November 2026.**

## What changed

You will **create the application yourself with a coding assistant**, then act as its AI Quality Analyst. The earlier Project 2 design assumed the application and eight example cases would be supplied. That assumption has changed. This pack replaces those dependencies: use the fixed fictional rules in `SOURCE_RULES.md`, write your own policy files, build your own assistant, and evaluate it. Do not wait for the trainer to build, host, configure or repair anything.

The final result is a **knowledge assistant web app running on your laptop, connected to a hosted LLM API** for Northstar Services employees. A user asks a policy question; the app retrieves relevant policy passages and uses an LLM to answer with passage citations, asks for missing context, or says the documents do not establish an answer. A human can inspect which passages were retrieved. This is a real model call, not a hardcoded response or a static mockup.

For this project, “agent” means **one assistant with a document-retrieval step and an answer/clarify/abstain decision**. A multi-agent framework, autonomous web browsing and external actions are not required.

## Required result and scope

Your repository must contain:

1. Ten short, fictional policy files derived from `SOURCE_RULES.md`, plus a manifest with document ID, version, effective date, scope, status and passage IDs. You author and check these files; do not paste the rules sheet directly as the only searchable document.
2. A locally runnable web app and `POST /api/ask`. Each answer records the question, release, decision (`answer`, `clarify`, `abstain`, or `conflict`), answer text, citations, retrieved passage IDs, model name, and elapsed time. Add `GET /api/health` and a way to inspect saved traces or JSON run logs.
3. Two reproducible releases in one repo: **baseline** and **candidate**. Baseline is your first honest implementation. Candidate changes one or more retrieval/authority controls based on development-case evidence. Do not deliberately insert bugs.
4. A **12-case** evidence-backed benchmark: four direct, two conditional/multi-document, two unknown, two outdated/conflicting, two ambiguous. Freeze eight development and four held-out cases before tuning candidate. The previous 24-case / 64-run target is **stretch work**, not required for this self-build four-day version.
5. Run each case once on both releases, and run two selected high-risk cases two additional times on each release: **32 application attempts** total. Keep all raw outputs and failures. Human-review the 24 first-pass outputs using `EVALUATION_RULES.md`. Report retrieval evidence, citation validity, unsupported claims, and paired improvements/regressions.
6. A short release recommendation and reproducible README. A locally runnable project is sufficient; cloud deployment is not required.

**Core tools:** Python 3.11 or 3.12, FastAPI, a student-owned Groq Free API account, BM25 retrieval, pytest, pandas or CSV, and Git. Use only fictional data because policy passages go to the hosted model. Arize Phoenix for trace viewing and one small Ragas judge comparison are valuable extensions **after the core flow works**; if these tools fail, preserve raw JSON traces and human scores and explain the limitation. Pandera and DVC are optional in this revised four-day scope. Do not buy services or enter a payment card for this project.

The example model is `openai/gpt-oss-20b`, listed in Groq's current model documentation. Check that it is available to **your** free account; if not, select another permitted text model shown in your console and record its exact ID. Keep your API key in an ignored `.env` file, never in Git, screenshots or prompts. Free limits vary by account; check yours before batch runs. See `SETUP.md`. No local LLM setup is required.

## Four-day checkpoints

| Day | Main work | End-of-day proof |
| --- | --- | --- |
| 1 | Orientation: the earlier four-day plan was shared. | No code, corpus, cases or model setup is assumed complete. |
| **2 — tomorrow** | Create the corpus and working baseline app. | A user can ask a question and see an answer/clarification/abstention with real passage IDs; six saved smoke results. See `DAY2.md`. |
| 3 | Freeze 12 cases, run baseline, improve candidate, run both. | 32 raw attempts, 24 first-pass human reviews, trace/log references, paired table. |
| 4 | Diagnose at least three evidence-backed findings, verify held-out behavior, and hand over. | Code, data, tests, results, README, demo, and go/conditional-go/no-go recommendation. |

## Submission checklist

- Source repository or ZIP without `.env`, API keys, model weights, virtual environments or caches.
- README with Windows/macOS steps **you actually tested**, model/provider, versions, release switch and limitations.
- Ten policy files, manifest, frozen benchmark, raw baseline/candidate results and human scoring.
- `pytest` output or equivalent API/logic test evidence; screenshots of UI and trace viewer/logs.
- Defect or investigation notes with expected source evidence, actual retrieved passages and answer, impact, and retest.
- One-page release decision. Do not claim a model is production-ready from this small local benchmark.

## Work rules

Use the prompts in `PROMPTS.md` one at a time in your coding assistant. Read and run the code it writes. Commit after each working stage. Never submit code you have not launched yourself. Do not fabricate a pass, screenshot, trace, citation, model version, or score. If blocked for more than 30 minutes, record the exact step, error, operating system and time and choose the documented fallback. You remain responsible for the product and the QA judgment; the coding assistant is a helper.
