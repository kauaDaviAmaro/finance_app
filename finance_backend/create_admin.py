#!/usr/bin/env python3
"""
Script para criar usuário administrador.
Uso: python create_admin.py <email> <username> <password>
"""
import sys
import argparse
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import User, UserRole
from app.core.security import hash_password


def create_admin(email: str, username: str, password: str):
    """Cria um usuário administrador"""
    db: Session = SessionLocal()
    
    try:
        # Verifica se email já existe
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ Erro: Email '{email}' já está em uso.")
            return False
        
        # Verifica se username já existe
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ Erro: Username '{username}' já está em uso.")
            return False
        
        # Cria o usuário admin
        admin_user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Usuário administrador criado com sucesso!")
        print(f"   ID: {admin_user.id}")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.username}")
        print(f"   Role: {admin_user.role.value}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar usuário administrador: {e}")
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Cria um usuário administrador no sistema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python create_admin.py admin@example.com admin senha123
        """
    )
    
    parser.add_argument('email', help='Email do administrador')
    parser.add_argument('username', help='Username do administrador')
    parser.add_argument('password', help='Senha do administrador')
    
    args = parser.parse_args()
    
    # Validações básicas
    if len(args.password) < 6:
        print("❌ Erro: A senha deve ter pelo menos 6 caracteres.")
        sys.exit(1)
    
    if '@' not in args.email:
        print("❌ Erro: Email inválido.")
        sys.exit(1)
    
    success = create_admin(args.email, args.username, args.password)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

