"""
Run once to create the Super Admin account.
After this, use the API to promote users to admin/reviewer.

    python -m app.db.seed.create_super_admin
"""

import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        )
    )
)

from app.db.session.database import SessionLocal
from app.models.user.user_model import User
from app.core.security.hashing import hash_password


def create_super_admin(
    email: str,
    full_name: str,
    password: str
):

    db = SessionLocal()

    try:

        existing = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing:
            print(
                f"User {email} already exists "
                f"with role: {existing.role}"
            )
            return

        # check if a super_admin already exists
        existing_super = (
            db.query(User)
            .filter(User.role == "super_admin")
            .first()
        )

        if existing_super:
            print(
                f"Super Admin already exists: "
                f"{existing_super.email}"
            )
            return

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role="super_admin"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print(
            f"Super Admin created successfully: {email}"
        )
        print(
            "Use PATCH /super-admin/users/{id}/role "
            "to promote users to admin or reviewer."
        )

    finally:

        db.close()


if __name__ == "__main__":

    # -----------------------------------
    # CHANGE THESE BEFORE RUNNING
    # -----------------------------------

    create_super_admin(
        email="superadmin@gmail.com",
        full_name="Super Admin",
        password="Super@123"
    )