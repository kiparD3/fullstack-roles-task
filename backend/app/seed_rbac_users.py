"""Run explicitly with python -m app.seed_rbac_users in development only."""

import os

from sqlmodel import Session

from app import crud
from app.core.authorization import UserRole
from app.core.config import settings
from app.core.db import engine
from app.models import UserCreate


def main() -> None:
    if settings.FASTAPI_ENV != "development":
        raise RuntimeError("Demo users can only be seeded in development")
    password = os.environ["RBAC_DEMO_PASSWORD"]
    with Session(engine) as session:
        for name, role, superuser in [
            ("admin", UserRole.MEMBER, True),
            ("manager", UserRole.MANAGER, False),
            ("member", UserRole.MEMBER, False),
            ("legacy", None, False),
        ]:
            email = f"rbac-{name}@example.com"
            # Never overwrite an existing account's password or privileges.
            if crud.get_user_by_email(session=session, email=email):
                continue
            crud.create_user(
                session=session,
                user_create=UserCreate(
                    email=email,
                    password=password,
                    full_name=f"RBAC {name}",
                    role=role,
                    is_superuser=superuser,
                ),
            )


if __name__ == "__main__":
    main()
