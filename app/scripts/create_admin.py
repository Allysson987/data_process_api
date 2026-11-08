
import getpass
import sys

import app.models

from app.database.connection import SessionLocal
from app.models.user import User
from app.core.security import (
    hash_email,
    encrypt_email,
    hash_password,
)


def create_admin():
    print("\n=== CRIAR ADMINISTRADOR ===\n")

    name = input("Nome: ").strip()
    email = input("E-mail: ").strip().lower()

    password = getpass.getpass("Senha: ")
    confirm_password = getpass.getpass("Confirme a senha: ")

    if not name or not email or not password:
        print("Erro: todos os campos são obrigatórios.")
        return

    if password != confirm_password:
        print("Erro: as senhas não coincidem.")
        return

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.email_hash == hash_email(email))
            .first()
        )

        if existing_user:
            print("Erro: já existe um usuário com esse e-mail.")
            return

        admin = User(
            name=name,
            email_hash=hash_email(email),
            email_encrypted=encrypt_email(email),
            password_hash=hash_password(password),
            is_active=True,
            is_admin=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("\nAdministrador criado com sucesso!")
        print(f"ID: {admin.id}")
        print(f"Nome: {admin.name}")
        print(f"Administrador: {admin.is_admin}")

    except Exception as error:
        db.rollback()
        print(f"Erro ao criar administrador: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
