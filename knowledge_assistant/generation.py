import json
from dataclasses import dataclass
from typing import Any

from groq import APIStatusError, Groq, GroqError

from knowledge_assistant.retrieval import Passage


class ModelCallError(Exception):
    def __init__(self, message: str, upstream_status: int | None = None) -> None:
        super().__init__(message)
        self.upstream_status = upstream_status


class ModelOutputError(Exception):
    def __init__(
        self, message: str, model_result: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.model_result = model_result


@dataclass(frozen=True)
class ModelResult:
    model: str
    content: str
    finish_reason: str | None
    output: dict[str, Any]


def _failure_message(status_code: int) -> str:
    if status_code == 400:
        return "Groq rejected the request (HTTP 400). Verify GROQ_MODEL and request settings."
    if status_code == 401:
        return "Groq authentication failed (HTTP 401). Check the local GROQ_API_KEY."
    if status_code == 429:
        return "Groq rate limit reached (HTTP 429). Wait before retrying."
    if 500 <= status_code <= 599:
        return f"Groq service error (HTTP {status_code}). Retry later."
    return f"Groq request failed (HTTP {status_code})."


def generate_answer(
    *,
    api_key: str,
    model: str,
    question: str,
    passages: list[Passage],
    department: str | None,
    as_of: str | None,
) -> ModelResult:
    passage_context = [
        {"passage_id": passage.passage_id, "text": passage.text}
        for passage in passages
    ]
    instructions = (
        "You answer employee questions using only the supplied fictional policy "
        "passages. Decide exactly one of answer, clarify, abstain, or conflict. "
        "Do not add policy facts that the passages do not establish. Cite only "
        "passage IDs present in the supplied passages. If required context is "
        "missing, choose clarify and ask for it. If the documents do not establish "
        "the answer, choose abstain and state that the provided policy documents "
        "do not establish it. Never return an empty answer. If applicable authoritative passages conflict, "
        "choose conflict rather than guessing. Include relevant eligibility, "
        "approval, and other conditions from the passages when they affect the "
        "answer; do not omit a directly applicable approval requirement or limitation. "
        "When multiple passages support an answer, cite each relevant passage. "
        "Output only one valid JSON object, with no markdown or surrounding text, "
        "using this shape: "
        '{"decision":"answer|clarify|abstain|conflict","answer":"...","citations":["PASSAGE-ID"]}.'
    )
    user_context = {
        "question": question,
        "department": department,
        "as_of": as_of,
        "passages": passage_context,
    }

    try:
        response = Groq(api_key=api_key).chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(user_context, ensure_ascii=False)},
            ],
            temperature=0,
            max_tokens=512,
        )
    except APIStatusError as error:
        raise ModelCallError(
            _failure_message(error.status_code), upstream_status=error.status_code
        ) from error
    except GroqError as error:
        raise ModelCallError(
            f"Groq request failed ({type(error).__name__}). Check network and configuration."
        ) from error

    if not response.choices:
        raise ModelOutputError("Groq returned no completion choices.")
    choice = response.choices[0]
    content = choice.message.content
    raw_result = {
        "model": model,
        "content": content,
        "finish_reason": choice.finish_reason,
    }
    if not isinstance(content, str) or not content.strip():
        raise ModelOutputError(
            f"Groq returned empty content (finish_reason={choice.finish_reason!r}).",
            model_result=raw_result,
        )
    try:
        output = json.loads(content)
    except json.JSONDecodeError as error:
        raise ModelOutputError(
            "Groq response was not valid JSON.", model_result=raw_result
        ) from error
    if not isinstance(output, dict):
        raise ModelOutputError(
            "Groq response JSON must be an object.", model_result=raw_result
        )
    return ModelResult(
        model=model,
        content=content,
        finish_reason=choice.finish_reason,
        output=output,
    )
