import json
from datetime import datetime
from typing import Iterable


def encode_json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def extract_source_document_ids(sources: Iterable[dict] | None) -> list[int]:
    ids: list[int] = []
    for source in sources or []:
        raw_id = source.get("document_id")
        if raw_id is None:
            continue
        try:
            document_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if document_id not in ids:
            ids.append(document_id)
    return ids


def touch(record) -> None:
    record.updated_at = datetime.utcnow()
