#!/usr/bin/env python3
"""
Direct database admin user creation script
Run this to create an admin user directly in the cloud database
"""
import os
import sys
sys.path.append('.')

from gc_registry.core.database import db, events
from gc_registry.user.models import User
from gc_registry.authentication.services import get_password_hash
from gc_registry.core.models.base import UserRoles
from sqlmodel import select

def create_admin_user():
    """Create admin user directly in database"""
    
    # Set environment variables for cloud database
    os.environ['DATABASE_HOST_WRITE'] = 'dpg-ct5ej8pu0jms73e8kcog-a.oregon-postgres.render.com'
    os.environ['DATABASE_HOST_READ'] = 'dpg-ct5ej8pu0jms73e8kcog-a.oregon-postgres.render.com'
    os.environ['DATABASE_PORT'] = '5432'
    os.environ['POSTGRES_USER'] = 'registry_user'
    os.environ['POSTGRES_PASSWORD'] = 'VQlBOdNhVGJhqLJhqvJhqvJhqvJhqvJh'
    os.environ['POSTGRES_DB'] = 'registry_db'
    os.environ['ENVIRONMENT'] = 'PROD'
    os.environ['ESDB_CONNECTION_STRING'] = 'esdb://localhost:2113?tls=false'
    os.environ['JWT_SECRET_KEY'] = 'secret_key'
    os.environ['MIDDLEWARE_SECRET_KEY'] = 'secret_key'
    
    try:
        # Get database connections
        _ = db.get_db_name_to_client()
        write_session = db.get_write_session()
        read_session = db.get_read_session()
        esdb_client = events.get_esdb_client()
        
        # Check if admin already exists
        existing_admin = read_session.exec(
            select(User).where(User.email == "admin@registry.com")
        ).first()
        
        if existing_admin:
            print("Admin user already exists!")
            print(f"Email: admin@registry.com")
            print(f"Password: admin123")
            return
        
        # Create admin user
        admin_user_dict = {
            "email": "admin@registry.com",
            "name": "Admin User",
            "hashed_password": get_password_hash("admin123"),
            "role": UserRoles.ADMIN,
        }
        
        admin_user = User.create(
            admin_user_dict, write_session, read_session, esdb_client
        )[0]
        
        print("✅ Admin user created successfully!")
        print(f"Email: admin@registry.com")
        print(f"Password: admin123")
        print(f"User ID: {admin_user.id}")
        
        write_session.close()
        read_session.close()
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_admin_user()