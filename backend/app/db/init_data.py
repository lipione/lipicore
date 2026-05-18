from sqlmodel import Session, select
from .session import engine
from ..models.user import User
from ..core.config import settings
from ..core.security import get_password_hash

def create_super_admin():
    with Session(engine) as session:
        admin_emails = {settings.SUPER_ADMIN_EMAIL, "admin@lipicore.io"}
        user = session.exec(select(User).where(User.email.in_(admin_emails))).first()
        if not user:
            from ..models.bank import Bank
            print("Creating default bank...")
            bank = session.exec(select(Bank).where(Bank.code == "DEFAULT")).first()
            if not bank:
                bank = Bank(name="Default Bank", code="DEFAULT")
                session.add(bank)
                session.commit()
                session.refresh(bank)
                
            print(f"Creating super admin: {settings.SUPER_ADMIN_EMAIL}")
            admin = User(
                email=settings.SUPER_ADMIN_EMAIL,
                password_hash=get_password_hash(settings.SUPER_ADMIN_PASSWORD),
                name="Super Admin",
                role="super_admin",
                is_active=True,
                bank_id=bank.id
            )
            session.add(admin)
            session.commit()
            print("Super admin created.")
        else:
            print("Super admin already exists.")

if __name__ == "__main__":
    create_super_admin()
