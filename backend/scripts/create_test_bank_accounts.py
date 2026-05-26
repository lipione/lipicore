#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path

from sqlmodel import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import engine
from app.services.demo_accounts_service import DEMO_ACCOUNT_FIELDS, create_demo_bank_accounts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or update demo bank tenants and test user accounts.",
    )
    parser.add_argument("banks", nargs="+", help="Bank slugs/codes, for example: sanima nabil nic")
    parser.add_argument("--password", help="Temporary password to assign to every created/updated account.")
    parser.add_argument("--email-domain", default="lipicore.test", help="Email domain for demo users.")
    parser.add_argument("--staff-count", type=int, default=3, help="Number of staffN users per bank.")
    parser.add_argument("--output", help="Write generated credentials to this CSV path instead of stdout.")
    return parser


def write_rows(rows: list[dict], output: str | None) -> None:
    target = open(output, "w", newline="") if output else sys.stdout
    try:
        writer = csv.DictWriter(target, fieldnames=DEMO_ACCOUNT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if output:
            target.close()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with Session(engine) as db:
        rows = create_demo_bank_accounts(
            db,
            args.banks,
            password=args.password,
            email_domain=args.email_domain,
            staff_count=args.staff_count,
        )
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_rows(rows, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
