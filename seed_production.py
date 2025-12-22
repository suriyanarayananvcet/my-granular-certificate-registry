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
    print("Starting database seeding...", flush=True)
    
    try:
        # Get database connections using the actual application logic
        from gc_registry.core.database.db import get_write_session, get_read_session
        
        write_gen = get_write_session()
        write_session = next(write_gen)
        
        read_gen = get_read_session()
        read_session = next(read_gen)
        
        # We might not have ESDB in production yet
        try:
            esdb_client = events.get_esdb_client()
        except Exception:
            print("⚠️ EventStoreDB not available, skipping event logging for seeding.", flush=True)
            esdb_client = None
        
        admin_email = "admin@registry.com"
        admin_pass = "admin123"
        
        print(f"Checking if user {admin_email} exists...", flush=True)
        
        # Check if admin already exists
        existing_admin = read_session.exec(
            select(User).where(User.email == admin_email)
        ).first()
        
        if existing_admin:
            print(f"✅ User {admin_email} already exists.", flush=True)
        else:
            print(f"Creating user {admin_email}...", flush=True)
            # Create admin user
            admin_user_dict = {
                "email": admin_email,
                "name": "Production Admin",
                "hashed_password": get_password_hash(admin_pass),
                "role": UserRoles.ADMIN,
            }
            
            # This calling convention matches the app's services
            User.create(
                admin_user_dict, write_session, read_session, esdb_client
            )
            
            # Explicitly commit just in case
            write_session.commit()
            read_session.commit()
            
            print(f"✅ User {admin_email} created successfully!", flush=True)
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}", flush=True)
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)

if __name__ == "__main__":
    seed()
