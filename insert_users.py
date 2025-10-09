#!/usr/bin/env python3
"""
Script untuk insert user ke MongoDB
Menggunakan model User yang sudah ada di aplikasi
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
import hashlib
from typing import List, Dict, Any

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.config.database import init_database, close_database, get_database
from app.models.user import User, UserCreate

class UserInserter:
    def __init__(self):
        self.db = None
    
    async def init_connection(self):
        """Initialize database connection"""
        try:
            await init_database()
            self.db = get_database()
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise
    
    async def close_connection(self):
        """Close database connection"""
        await close_database()
        print("✅ Database connection closed")
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user_data(self, user_data: Dict[str, Any]) -> User:
        """Create User object from dictionary data"""
        # Hash password if provided
        if 'password' in user_data:
            user_data['password'] = self.hash_password(user_data['password'])
        
        # Set default values
        user_data.setdefault('id', str(uuid.uuid4()))
        user_data.setdefault('is_admin', False)
        user_data.setdefault('created_at', datetime.now(timezone(timedelta(hours=7))))
        
        return User(**user_data)
    
    async def insert_single_user(self, user_data: Dict[str, Any]) -> bool:
        """Insert a single user to MongoDB"""
        try:
            user = self.create_user_data(user_data)
            
            # Check if user already exists
            existing_user = await self.db.users.find_one({"username": user.username})
            if existing_user:
                print(f"⚠️  User with username '{user.username}' already exists")
                return False
            
            # Insert user
            result = await self.db.users.insert_one(user.dict())
            print(f"✅ User '{user.username}' inserted successfully with ID: {result.inserted_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to insert user '{user_data.get('username', 'unknown')}': {e}")
            return False
    
    async def insert_multiple_users(self, users_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Insert multiple users to MongoDB"""
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        print(f"🚀 Starting to insert {len(users_data)} users...")
        
        for user_data in users_data:
            try:
                user = self.create_user_data(user_data)
                
                # Check if user already exists
                existing_user = await self.db.users.find_one({"username": user.username})
                if existing_user:
                    print(f"⚠️  User with username '{user.username}' already exists - skipping")
                    results["skipped"] += 1
                    continue
                
                # Insert user
                result = await self.db.users.insert_one(user.dict())
                print(f"✅ User '{user.username}' inserted successfully with ID: {result.inserted_id}")
                results["success"] += 1
                
            except Exception as e:
                print(f"❌ Failed to insert user '{user_data.get('username', 'unknown')}': {e}")
                results["failed"] += 1
        
        return results
    
    async def get_sample_users(self) -> List[Dict[str, Any]]:
        """Get sample user data for testing"""
        return [
            {
                "username": "admin",
                "nama": "Administrator",
                "alamat": "Jl. Admin No. 1",
                "nomor_rumah": "A1",
                "nomor_hp": "081234567890",
                "tipe_rumah": "72M2",
                "password": "admin123",
                "is_admin": True
            },
            {
                "username": "warga001",
                "nama": "Budi Santoso",
                "alamat": "Jl. Merdeka No. 10",
                "nomor_rumah": "B5",
                "nomor_hp": "081234567891",
                "tipe_rumah": "60M2",
                "password": "warga123"
            },
            {
                "username": "warga002",
                "nama": "Siti Nurhaliza",
                "alamat": "Jl. Merdeka No. 12",
                "nomor_rumah": "B7",
                "nomor_hp": "081234567892",
                "tipe_rumah": "72M2",
                "password": "warga123"
            },
            {
                "username": "warga003",
                "nama": "Ahmad Wijaya",
                "alamat": "Jl. Merdeka No. 15",
                "nomor_rumah": "C2",
                "nomor_hp": "081234567893",
                "tipe_rumah": "HOOK",
                "password": "warga123"
            },
            {
                "username": "warga004",
                "nama": "Rina Sari",
                "alamat": "Jl. Merdeka No. 18",
                "nomor_rumah": "C5",
                "nomor_hp": "081234567894",
                "tipe_rumah": "60M2",
                "password": "warga123"
            }
        ]
    
    async def list_all_users(self):
        """List all users in the database"""
        try:
            users = await self.db.users.find({}).to_list(length=None)
            print(f"\n📋 Total users in database: {len(users)}")
            print("-" * 80)
            for user in users:
                print(f"ID: {user['_id']}")
                print(f"Username: {user['username']}")
                print(f"Nama: {user['nama']}")
                print(f"Alamat: {user['alamat']}")
                print(f"Nomor Rumah: {user['nomor_rumah']}")
                print(f"Nomor HP: {user['nomor_hp']}")
                print(f"Tipe Rumah: {user.get('tipe_rumah', 'N/A')}")
                print(f"Admin: {'Yes' if user.get('is_admin', False) else 'No'}")
                print(f"Created: {user.get('created_at', 'N/A')}")
                print("-" * 80)
        except Exception as e:
            print(f"❌ Failed to list users: {e}")

async def main():
    """Main function to run the user insertion script"""
    inserter = UserInserter()
    
    try:
        # Initialize database connection
        await inserter.init_connection()
        
        print("🔧 User Insertion Script")
        print("=" * 50)
        
        # Get sample users
        sample_users = await inserter.get_sample_users()
        
        # Insert users
        results = await inserter.insert_multiple_users(sample_users)
        
        # Print results
        print("\n📊 Insertion Results:")
        print(f"✅ Successfully inserted: {results['success']} users")
        print(f"❌ Failed to insert: {results['failed']} users")
        print(f"⚠️  Skipped (already exists): {results['skipped']} users")
        
        # List all users
        print("\n📋 Current users in database:")
        await inserter.list_all_users()
        
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1
    
    finally:
        # Close database connection
        await inserter.close_connection()
    
    return 0

if __name__ == "__main__":
    # Run the script
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
