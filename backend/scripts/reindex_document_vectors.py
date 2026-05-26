#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from sqlmodel import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import engine
from app.services.qdrant_service import init_qdrant
from app.services.reindex_service import reindex_all_document_vectors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rebuild Qdrant vectors for existing document chunks.",
    )
    parser.add_argument("--bank-id", type=int, help="Only reindex one bank.")
    parser.add_argument(
        "--document-id",
        dest="document_ids",
        action="append",
        type=int,
        help="Only reindex this document id. Repeat for multiple documents.",
    )
    parser.add_argument("--batch-size", type=int, default=64)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    init_qdrant()
    with Session(engine) as db:
        results = reindex_all_document_vectors(
            db,
            bank_id=args.bank_id,
            document_ids=args.document_ids,
            batch_size=args.batch_size,
        )
    for result in results:
        print(
            f"document_id={result['document_id']} "
            f"status={result['status']} "
            f"indexed_chunks={result['indexed_chunks']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
