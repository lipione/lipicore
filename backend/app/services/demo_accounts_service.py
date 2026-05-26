import re
import secrets

from sqlmodel import Session, select

from ..core.security import get_password_hash
from ..models.bank import Bank
from ..models.document import Document  # noqa: F401 - registers Bank relationships
from ..models.user import User


DEMO_ACCOUNT_FIELDS = [
    "bank_code",
    "bank_name",
    "name",
    "email",
    "password",
    "role",
    "department",
    "status",
]


def _bank_code(raw: str) -> str:
    code = re.sub(r"[^A-Za-z0-9]+", "", raw).upper()
    if not code:
        raise ValueError("Bank code must contain at least one letter or digit.")
    return code[:24]


def _bank_slug(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "", raw.lower())
    if not slug:
        raise ValueError("Bank slug must contain at least one letter or digit.")
    return slug


def _bank_name(raw: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", raw.strip()) if part]
    return f"{' '.join(part.capitalize() for part in parts)} Demo Bank"


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one digit.")


def generate_temporary_password(bank_code: str) -> str:
    return f"{bank_code.title()}Demo{secrets.randbelow(9000) + 1000}!"


def _account_templates(slug: str, email_domain: str, staff_count: int) -> list[dict]:
    templates = [
        {
            "name": "Bank Admin",
            "email": f"bankadmin.{slug}.demo@{email_domain}",
            "role": "bank_admin",
            "department": "Administration",
        },
    ]
    for index in range(1, staff_count + 1):
        templates.append({
            "name": f"Staff User {index}",
            "email": f"staff{index}.{slug}.demo@{email_domain}",
            "role": "staff_user",
            "department": "Customer Care",
        })
    templates.extend([
        {
            "name": "Branch Staff",
            "email": f"branch.{slug}.demo@{email_domain}",
            "role": "staff_user",
            "department": "Branch Operations",
        },
        {
            "name": "Compliance User",
            "email": f"compliance.{slug}.demo@{email_domain}",
            "role": "compliance_user",
            "department": "Compliance",
        },
    ])
    return templates


def create_demo_bank_accounts(
    db: Session,
    bank_slugs: list[str],
    *,
    password: str | None = None,
    email_domain: str = "lipicore.test",
    staff_count: int = 3,
) -> list[dict]:
    if staff_count < 1 or staff_count > 20:
        raise ValueError("staff_count must be between 1 and 20.")

    email_domain = email_domain.strip().lower()
    if not email_domain or "@" in email_domain:
        raise ValueError("email_domain must be a domain like lipicore.test.")

    rows: list[dict] = []
    for raw_bank in bank_slugs:
        code = _bank_code(raw_bank)
        slug = _bank_slug(raw_bank)
        name = _bank_name(raw_bank)
        bank_password = password or generate_temporary_password(code)
        _validate_password(bank_password)

        bank = db.exec(select(Bank).where(Bank.code == code)).first()
        if bank is None:
            bank = Bank(name=name, code=code, status="active")
            db.add(bank)
            db.commit()
            db.refresh(bank)
        else:
            bank.name = bank.name or name
            bank.status = "active"
            db.add(bank)
            db.commit()
            db.refresh(bank)

        for template in _account_templates(slug, email_domain, staff_count):
            email = template["email"].lower()
            user = db.exec(select(User).where(User.email == email)).first()
            status = "updated"
            if user is None:
                user = User(
                    email=email,
                    password_hash=get_password_hash(bank_password),
                    name=template["name"],
                    role=template["role"],
                    department=template["department"],
                    bank_id=bank.id,
                    is_active=True,
                )
                status = "created"
            else:
                user.password_hash = get_password_hash(bank_password)
                user.name = template["name"]
                user.role = template["role"]
                user.department = template["department"]
                user.bank_id = bank.id
                user.is_active = True
            db.add(user)
            rows.append({
                "bank_code": bank.code,
                "bank_name": bank.name,
                "name": template["name"],
                "email": email,
                "password": bank_password,
                "role": template["role"],
                "department": template["department"],
                "status": status,
            })
        db.commit()

    return rows
