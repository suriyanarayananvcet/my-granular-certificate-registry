#!/usr/bin/env python3
import os
import sys
sys.path.append('.')

from gc_registry.core.database import db, events
from gc_registry.user.models import User
from gc_registry.authentication.services import get_password_hash
from gc_registry.core.models.base import UserRoles
from sqlmodel import select

def seed():
    print("Starting database seeding...")
    
    # Ensure we are using the environment variables
    # (db.py is already robust enough to pick them up)
    
    try:
        # Get database connections
        _ = db.get_db_name_to_client()
        write_session = db.get_write_session()
        read_session = db.get_read_session()
        
        # We might not have ESDB in production yet, so we'll mock the client if it fails
        try:
            esdb_client = events.get_esdb_client()
        except Exception:
            print("⚠️ EventStoreDB not available, skipping event logging for seeding.")
            esdb_client = None
        
        admin_email = "admin@registry.com"
        admin_pass = "admin123"
        
        # Check if admin already exists
        existing_admin = read_session.exec(
            select(User).where(User.email == admin_email)
        ).first()
        
        if existing_admin:
            print(f"✅ Admin user already exists: {admin_email}")
        else:
            # Create admin user
            admin_user_dict = {
                "email": admin_email,
                "name": "Production Admin",
                "hashed_password": get_password_hash(admin_pass),
                "role": UserRoles.ADMIN,
            }
            
            admin_user = User.create(
                admin_user_dict, write_session, read_session, esdb_client
            )[0]
            
            print(f"✅ Admin user created successfully!")
            print(f"Email: {admin_email}")
            print(f"Password: {admin_pass}")
        
        write_session.close()
        read_session.close()
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed()
