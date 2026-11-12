import json
import os
import threading
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

from knowledge_assistant.generation import (
    ModelCallError,
    ModelOutputError,
    generate_answer,
)
from knowledge_assistant.retrieval import (
    Passage,
    department_from_question,
    extract_date,
    load_corpus,
    search_passages,
)


ROOT_DIR = Path(__file__).resolve().parent.parent
TRACE_PATH = ROOT_DIR / "traces" / "requests.jsonl"
TRACE_LOCK = threading.Lock()
DECISIONS = {"answer", "clarify", "abstain", "conflict"}

app = FastAPI(title="Northstar Policy Knowledge Assistant")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    department: str | None = None
    as_of: date | None = None
    release: Literal["baseline"] = "baseline"

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question must not be blank.")
        return value.strip()


def _configuration() -> tuple[str | None, str | None]:
    load_dotenv(ROOT_DIR / ".env")
    return os.getenv("GROQ_API_KEY"), os.getenv("GROQ_MODEL")


def _write_trace(record: dict[str, Any]) -> None:
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_LOCK, TRACE_PATH.open("a", encoding="utf-8") as trace_file:
        trace_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _response(
    *,
    request: AskRequest,
    trace_id: str,
    started_at: float,
    retrieved: list[Passage],
    model_tag: str | None,
    decision: str | None,
    answer: str,
    citations: list[str] | None = None,
    model_result: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
    status_code: int = 200,
) -> JSONResponse:
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    retrieved_ids = [passage.passage_id for passage in retrieved]
    citation_ids = citations or []
    body = {
        "release": request.release,
        "decision": decision,
        "answer": answer,
        "citations": citation_ids,
        "retrieved_passage_ids": retrieved_ids,
        "retrieved_passages": [passage.as_dict() for passage in retrieved],
        "model_tag": model_tag,
        "trace_id": trace_id,
        "elapsed_ms": elapsed_ms,
        "error": error,
    }
    _write_trace(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "request": {
                "question": request.question,
                "department": request.department,
                "as_of": request.as_of.isoformat() if request.as_of else None,
                "release": request.release,
            },
            "retrieved_passages": body["retrieved_passages"],
            "model_result": model_result,
            "decision": decision,
            "citations": citation_ids,
            "error": error,
            "elapsed_ms": elapsed_ms,
        }
    )
    return JSONResponse(status_code=status_code, content=body)


def _context_clarification(
    question: str,
    department: str | None,
    as_of: date | None,
    retrieved: list[Passage],
) -> str | None:
    passage_ids = {passage.passage_id for passage in retrieved}
    text = question.casefold()
    remote_question = (
        "remote" in text
        or "work from home" in text
        or "work remotely" in text
    )
    has_remote_sources = any(
        passage_id.startswith(("REMOTE-", "SUPPORT-"))
        for passage_id in passage_ids
    )
    if remote_question and has_remote_sources:
        missing = []
        if not department:
            missing.append("your department")
        if not as_of:
            missing.append("the date the remote-work rule should apply to")
        if missing:
            return "Please provide " + " and ".join(missing) + "."

    learning_question = any(
        word in text for word in ("learning leave", "learning-leave")
    )
    has_historical_and_current_leave = (
        "LEAVE-2025-P1" in passage_ids
        and any(passage_id.startswith("LEAVE-2026-") for passage_id in passage_ids)
    )
    if learning_question and has_historical_and_current_leave and not as_of:
        return "Please specify the year or date for the learning-leave rule."
    return None


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Northstar Policy Assistant</title></head>
<body>
  <h1>Northstar Services Policy Assistant</h1>
  <p>Ask a question about the fictional policy documents. Do not enter personal or confidential information.</p>
  <form id="ask-form">
    <label>Question <input id="question" name="question" required maxlength="2000"></label>
    <label>Department (optional) <input id="department" name="department"></label>
    <label>As-of date (optional) <input id="as-of" name="as_of" type="date"></label>
    <button type="submit">Ask</button>
  </form>
  <h2>Result</h2>
  <pre id="result" aria-live="polite"></pre>
  <h2>Retrieved passages</h2>
  <ol id="passages"></ol>
  <script>
    const form = document.getElementById("ask-form");
    const result = document.getElementById("result");
    const passages = document.getElementById("passages");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      result.textContent = "Requesting an answer...";
      passages.replaceChildren();
      const payload = {
        question: document.getElementById("question").value,
        department: document.getElementById("department").value || null,
        as_of: document.getElementById("as-of").value || null,
        release: "baseline"
      };
      try {
        const response = await fetch("/api/ask", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        const lines = [
          `HTTP ${response.status}`,
          `Decision: ${data.decision ?? "not completed"}`,
          `Answer: ${data.answer}`,
          `Citations: ${(data.citations || []).join(", ") || "none"}`,
          `Model: ${data.model_tag || "not configured"}`,
          `Trace: ${data.trace_id}`,
          `Elapsed: ${data.elapsed_ms} ms`
        ];
        if (data.error) lines.push(`Error: ${data.error.message}`);
        result.textContent = lines.join("\\n");
        for (const passage of data.retrieved_passages || []) {
          const item = document.createElement("li");
          item.textContent = `${passage.passage_id}: ${passage.text}`;
          passages.append(item);
        }
      } catch (error) {
        result.textContent = `Request failed; no assistant answer was generated. ${error}`;
      }
    });
  </script>
</body>
</html>"""


@app.get("/api/health")
def health() -> dict[str, Any]:
    try:
        index = load_corpus()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "error": str(error)},
        )
    api_key, model = _configuration()
    return {
        "status": "ok",
        "release": "baseline",
        "model_tag": model,
        "model_configured": bool(api_key and model),
        "source_passage_count": len(index.passages),
    }


@app.post("/api/ask")
def ask(request: AskRequest) -> JSONResponse:
    started_at = time.perf_counter()
    trace_id = str(uuid.uuid4())
    retrieved: list[Passage] = []
    model_tag: str | None = None
    try:
        api_key, model_tag = _configuration()
        effective_department = (
            request.department or department_from_question(request.question)
        )
        effective_as_of = request.as_of or extract_date(request.question)
        retrieved = search_passages(
            request.question,
            department=effective_department,
            as_of=effective_as_of,
        )
        clarification = _context_clarification(
            request.question, effective_department, effective_as_of, retrieved
        )
        if clarification:
            return _response(
                request=request,
                trace_id=trace_id,
                started_at=started_at,
                retrieved=retrieved,
                model_tag=model_tag,
                decision="clarify",
                answer=clarification,
            )
        if not api_key or not model_tag:
            return _response(
                request=request,
                trace_id=trace_id,
                started_at=started_at,
                retrieved=retrieved,
                model_tag=model_tag,
                decision=None,
                answer="Request failed; no assistant answer was generated.",
                error={
                    "type": "configuration_error",
                    "message": "GROQ_API_KEY and GROQ_MODEL must be set on the server.",
                },
                status_code=503,
            )
        result = generate_answer(
            api_key=api_key,
            model=model_tag,
            question=request.question,
            passages=retrieved,
            department=effective_department,
            as_of=effective_as_of.isoformat() if effective_as_of else None,
        )
        model_result = {
            "model": result.model,
            "content": result.content,
            "finish_reason": result.finish_reason,
        }
        output = result.output
        decision = output.get("decision")
        answer = output.get("answer")
        citations = output.get("citations")
        if decision not in DECISIONS or not isinstance(answer, str) or not answer.strip():
            raise ModelOutputError(
                "Groq response must include a valid decision and answer.",
                model_result=model_result,
            )
        if not isinstance(citations, list) or not all(
            isinstance(citation, str) for citation in citations
        ):
            raise ModelOutputError(
                "Groq response citations must be a list of passage IDs.",
                model_result=model_result,
            )
        retrieved_ids = {passage.passage_id for passage in retrieved}
        source_ids = {passage.passage_id for passage in load_corpus().passages}
        invalid_citations = [
            citation
            for citation in citations
            if citation not in retrieved_ids or citation not in source_ids
        ]
        if invalid_citations:
            raise ModelOutputError(
                "Groq returned citations that are not valid retrieved source passages.",
                model_result=model_result,
            )
        if decision == "answer" and not citations:
            raise ModelOutputError(
                "Groq returned an answer without a source citation.",
                model_result=model_result,
            )
        response = _response(
            request=request,
            trace_id=trace_id,
            started_at=started_at,
            retrieved=retrieved,
            model_tag=result.model,
            decision=decision,
            answer=answer,
            citations=citations,
            model_result=model_result,
        )
        return response
    except ModelCallError as error:
        return _response(
            request=request,
            trace_id=trace_id,
            started_at=started_at,
            retrieved=retrieved,
            model_tag=model_tag,
            decision=None,
            answer="Request failed; no assistant answer was generated.",
            error={
                "type": "model_call_error",
                "message": str(error),
                "upstream_status": error.upstream_status,
            },
            status_code=502,
        )
    except ModelOutputError as error:
        return _response(
            request=request,
            trace_id=trace_id,
            started_at=started_at,
            retrieved=retrieved,
            model_tag=model_tag,
            decision=None,
            answer="Request failed; no assistant answer was generated.",
            model_result=error.model_result,
            error={"type": "model_output_error", "message": str(error)},
            status_code=502,
        )
