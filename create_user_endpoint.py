#!/usr/bin/env python3
"""
Emergency user creation script for Railway deployment
Run this to create admin user directly
"""

import requests
import json

def create_user_via_api():
    """Create user using Railway API"""
    url = "https://my-granular-certificate-registry-production.up.railway.app/user/register"
    
    user_data = {
        "email": "admin@registry.com",
        "password": "admin123",
        "name": "Admin User",
        "role": 4
    }
    
    try:
        response = requests.post(url, json=user_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ User created successfully!")
            print("Now you can login at: https://my-granular-certificate-registry-n6t50x4mi.vercel.app")
            print("Email: admin@registry.com")
            print("Password: admin123")
        else:
            print("❌ User creation failed")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_user_via_api()