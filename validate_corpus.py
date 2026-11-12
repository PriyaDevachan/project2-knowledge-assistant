import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CORPUS_DIR = Path(__file__).resolve().parent / "policy_corpus"
PASSAGE_PATTERN = re.compile(r"^\*\*([A-Z0-9]+(?:-[A-Z0-9]+)*-P\d+)\*\*", re.MULTILINE)


def main() -> int:
    manifest_path = CORPUS_DIR / "manifest.json"
    try:
        manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read manifest {manifest_path}: {error}", file=sys.stderr)
        return 1

    documents = manifest.get("documents")
    if not isinstance(documents, list):
        print("Manifest must contain a 'documents' list.", file=sys.stderr)
        return 1

    errors: list[str] = []
    document_ids = [
        doc["document_id"]
        for doc in documents
        if isinstance(doc, dict) and isinstance(doc.get("document_id"), str)
    ]
    for duplicate in sorted(
        value for value, count in Counter(document_ids).items() if count > 1
    ):
        errors.append(f"Duplicate document ID in manifest: {duplicate}")

    manifest_passages: Counter[str] = Counter()
    document_passages: dict[str, set[str]] = {}
    seen_filenames: set[str] = set()

    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            errors.append(f"Document entry {index} must be an object.")
            continue

        filename = document.get("filename")
        passage_ids = document.get("passage_ids")
        if not isinstance(filename, str) or not isinstance(passage_ids, list):
            errors.append(
                f"Document entry {index} needs a filename and passage_ids list."
            )
            continue
        if filename in seen_filenames:
            errors.append(f"Duplicate document filename in manifest: {filename}")
        seen_filenames.add(filename)

        path = CORPUS_DIR / filename
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            errors.append(f"Cannot read document {filename}: {error}")
            continue

        actual_ids = PASSAGE_PATTERN.findall(text)
        actual_counter = Counter(actual_ids)
        for duplicate in sorted(
            value for value, count in actual_counter.items() if count > 1
        ):
            errors.append(f"Duplicate passage ID in {filename}: {duplicate}")
        document_passages[filename] = set(actual_ids)

        for passage_id in passage_ids:
            if not isinstance(passage_id, str):
                errors.append(
                    f"Non-string passage ID listed for {filename}: {passage_id!r}"
                )
                continue
            manifest_passages[passage_id] += 1
            if passage_id not in actual_counter:
                errors.append(
                    f"Manifest passage {passage_id} is missing from {filename}."
                )

    for duplicate in sorted(
        value for value, count in manifest_passages.items() if count > 1
    ):
        errors.append(f"Duplicate passage ID in manifest: {duplicate}")

    referenced_passages = set(manifest_passages)
    for filename, actual_ids in document_passages.items():
        for passage_id in sorted(actual_ids - referenced_passages):
            errors.append(
                f"Passage {passage_id} in {filename} is not referenced by the manifest."
            )

    if errors:
        print("Corpus validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Corpus validation passed: {len(documents)} documents, "
        f"{sum(manifest_passages.values())} unique passages."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
