import json
import re
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

ROOT_DIR = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT_DIR / "policy_corpus"
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
PASSAGE_PATTERN = re.compile(
    r"^\*\*([A-Z0-9]+(?:-[A-Z0-9]+)*-P\d+)\*\*\s*(.+)$", re.MULTILINE
)
DATE_PATTERN = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{4})\b",
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")


@dataclass(frozen=True)
class Passage:
    passage_id: str
    text: str
    document_id: str
    title: str
    effective_start: date | None
    effective_end: date | None
    status: str
    department_scope: str

    def as_dict(self) -> dict[str, str]:
        return {"passage_id": self.passage_id, "text": self.text}


@dataclass(frozen=True)
class CorpusIndex:
    passages: tuple[Passage, ...]
    bm25: BM25Okapi


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.casefold())


@lru_cache(maxsize=1)
def load_corpus() -> CorpusIndex:
    manifest_path = CORPUS_DIR / "manifest.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("The policy manifest must contain documents.")

    passages: list[Passage] = []
    for document in documents:
        path = CORPUS_DIR / document["filename"]
        text = path.read_text(encoding="utf-8")
        passage_text_by_id = {
            passage_id: passage_text.strip()
            for passage_id, passage_text in PASSAGE_PATTERN.findall(text)
        }
        for passage_id in document["passage_ids"]:
            passage_text = passage_text_by_id.get(passage_id)
            if passage_text is None:
                raise ValueError(
                    f"Manifest passage {passage_id} is missing from {path.name}."
                )
            passages.append(
                Passage(
                    passage_id=passage_id,
                    text=passage_text,
                    document_id=document["document_id"],
                    title=document["title"],
                    effective_start=_parse_date(document.get("effective_start")),
                    effective_end=_parse_date(document.get("effective_end")),
                    status=document["status"],
                    department_scope=document["department_scope"],
                )
            )

    if len({passage.passage_id for passage in passages}) != len(passages):
        raise ValueError("The policy corpus contains duplicate passage IDs.")

    tokenized_documents = [
        _tokenize(f"{passage.title} {passage.department_scope} {passage.text}")
        for passage in passages
    ]
    return CorpusIndex(tuple(passages), BM25Okapi(tokenized_documents))


def extract_date(question: str) -> date | None:
    month_match = DATE_PATTERN.search(question)
    if month_match:
        month_number = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }[month_match.group(1).casefold()]
        return date(int(month_match.group(2)), month_number, 1)
    year_match = YEAR_PATTERN.search(question)
    if year_match:
        return date(int(year_match.group(1)), 12, 31)
    return None


def department_from_question(question: str) -> str | None:
    for passage in load_corpus().passages:
        if (
            passage.department_scope != "All departments"
            and passage.department_scope.casefold() in question.casefold()
        ):
            return passage.department_scope
    return None


def search_passages(
    question: str,
    *,
    department: str | None = None,
    as_of: date | None = None,
    top_k: int = 5,
) -> list[Passage]:
    index = load_corpus()
    query = " ".join(part for part in (question, department or "") if part)
    scores = index.bm25.get_scores(_tokenize(query))
    eligible = [
        (score, position, passage)
        for position, (score, passage) in enumerate(zip(scores, index.passages))
        if (
            as_of is None
            or passage.effective_start is None
            or passage.effective_start <= as_of
        )
        and (
            as_of is None
            or passage.effective_end is None
            or passage.effective_end >= as_of
        )
    ]
    eligible.sort(key=lambda result: (-result[0], result[1]))
    return [passage for score, _, passage in eligible[:top_k] if score > 0]
