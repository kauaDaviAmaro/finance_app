"""
Script para corrigir emails inválidos no banco de dados.
Atualiza emails com domínio @system.local para @example.com
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import User
from sqlalchemy import update

def fix_invalid_emails():
    """Corrige emails inválidos no banco de dados"""
    db = SessionLocal()
    try:
        # Buscar usuários com emails inválidos
        users_with_invalid_emails = db.query(User).filter(
            User.email.like('%@system.local')
        ).all()
        
        if not users_with_invalid_emails:
            print("Nenhum usuário com email inválido encontrado.")
            return
        
        print(f"Encontrados {len(users_with_invalid_emails)} usuário(s) com email inválido:")
        
        for user in users_with_invalid_emails:
            old_email = user.email
            new_email = old_email.replace('@system.local', '@example.com')
            print(f"  - ID {user.id}: {old_email} -> {new_email}")
            
            # Verificar se o novo email já existe
            existing = db.query(User).filter(User.email == new_email).first()
            if existing:
                print(f"    AVISO: Email {new_email} já existe! Pulando...")
                continue
            
            # Atualizar email
            user.email = new_email
        
        db.commit()
        print(f"\n✅ {len(users_with_invalid_emails)} email(s) corrigido(s) com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao corrigir emails: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_invalid_emails()



