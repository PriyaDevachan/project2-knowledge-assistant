import json
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

import knowledge_assistant.app as assistant_app
from knowledge_assistant.generation import ModelCallError, ModelResult
from knowledge_assistant.retrieval import load_corpus, search_passages


client = TestClient(assistant_app.app)


def _set_trace_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    monkeypatch.setattr(assistant_app, "TRACE_PATH", tmp_path / "requests.jsonl")


def _model_result(
    citations: list[str], decision: str = "answer"
) -> ModelResult:
    output = {
        "decision": decision,
        "answer": "A test response grounded in the retrieved passage.",
        "citations": citations,
    }
    return ModelResult(
        model="test-model",
        content=json.dumps(output),
        finish_reason="stop",
        output=output,
    )


def test_health_and_browser_page() -> None:
    health = client.get("/api/health")
    page = client.get("/")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["source_passage_count"] == 19
    assert page.status_code == 200
    assert "Northstar Services Policy Assistant" in page.text
    assert 'id="ask-form"' in page.text


def test_retrieval_returns_only_manifest_source_ids() -> None:
    valid_ids = {passage.passage_id for passage in load_corpus().passages}
    results = search_passages(
        "I am full-time, have worked eight months, and want learning leave in 2026. How many days?",
        as_of=date(2026, 12, 31),
    )

    assert results
    assert {passage.passage_id for passage in results} <= valid_ids
    assert any(passage.passage_id == "LEAVE-2026-P1" for passage in results)


def test_ask_accepts_only_retrieved_source_citations(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    _set_trace_path(monkeypatch, tmp_path)

    def fake_generate_answer(
        *, api_key: str, model: str, question: str, passages: list[Any],
        department: str | None, as_of: str | None
    ) -> ModelResult:
        return _model_result([passages[0].passage_id])

    monkeypatch.setattr(assistant_app, "generate_answer", fake_generate_answer)
    response = client.post(
        "/api/ask",
        json={
            "question": "I am full-time, have worked eight months, and want learning leave in 2026. How many days?"
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["decision"] == "answer"
    assert body["citations"]
    assert set(body["citations"]) <= set(body["retrieved_passage_ids"])
    assert set(body["citations"]) <= {
        passage.passage_id for passage in load_corpus().passages
    }
    trace = json.loads((tmp_path / "requests.jsonl").read_text(encoding="utf-8"))
    assert trace["model_result"]["content"]
    assert trace["error"] is None


def test_ask_rejects_non_retrieved_citation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    _set_trace_path(monkeypatch, tmp_path)
    monkeypatch.setattr(
        assistant_app,
        "generate_answer",
        lambda **kwargs: _model_result(["NOT-A-SOURCE-P1"]),
    )

    response = client.post(
        "/api/ask",
        json={"question": "What is the meal limit on approved business travel?"},
    )
    body = response.json()

    assert response.status_code == 502
    assert body["decision"] is None
    assert body["answer"].startswith("Request failed")
    assert body["error"]["type"] == "model_output_error"
    traces = (tmp_path / "requests.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(traces) == 1
    assert json.loads(traces[0])["model_result"]["content"]


def test_remote_question_missing_context_is_clarified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    _set_trace_path(monkeypatch, tmp_path)

    def unexpected_model_call(**kwargs: Any) -> ModelResult:
        pytest.fail("The assistant should clarify before calling the model.")

    monkeypatch.setattr(assistant_app, "generate_answer", unexpected_model_call)
    response = client.post("/api/ask", json={"question": "How many remote days can I work?"})
    body = response.json()

    assert response.status_code == 200
    assert body["decision"] == "clarify"
    assert "department" in body["answer"]
    assert "date" in body["answer"]
    assert len((tmp_path / "requests.jsonl").read_text(encoding="utf-8").splitlines()) == 1


@pytest.mark.parametrize(
    ("upstream_status", "expected_text"),
    [
        (400, "Groq rejected the request"),
        (401, "Groq authentication failed"),
        (429, "Groq rate limit reached"),
        (503, "Groq service error"),
    ],
)
def test_groq_errors_are_returned_as_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    upstream_status: int,
    expected_text: str,
) -> None:
    _set_trace_path(monkeypatch, tmp_path)

    def fail_generation(**kwargs: Any) -> ModelResult:
        raise ModelCallError(expected_text + f" (HTTP {upstream_status})", upstream_status)

    monkeypatch.setattr(assistant_app, "generate_answer", fail_generation)
    response = client.post(
        "/api/ask",
        json={"question": "What is the meal limit on approved business travel?"},
    )
    body = response.json()

    assert response.status_code == 502
    assert body["decision"] is None
    assert body["error"]["upstream_status"] == upstream_status
    assert expected_text in body["error"]["message"]
    assert body["answer"] == "Request failed; no assistant answer was generated."
