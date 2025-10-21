#!/usr/bin/env python3
"""
Migration script to add versioning fields to existing fees
Run this script to update existing fee documents with new schema
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.database import get_database, init_database, close_database

async def migrate_fee_schema():
    """Migrate existing fees to include versioning fields"""
    print("🚀 Starting fee schema migration...")
    
    try:
        # Initialize database connection
        await init_database()
        db = get_database()
        
        # Check if migration is needed
        sample_fee = await db.fees.find_one({"version": {"$exists": False}})
        if not sample_fee:
            print("✅ Migration not needed - all fees already have versioning fields")
            return
        
        print(f"📊 Found fees without versioning fields, starting migration...")
        
        # Count total fees to migrate
        total_fees = await db.fees.count_documents({"version": {"$exists": False}})
        print(f"📈 Total fees to migrate: {total_fees}")
        
        # Add versioning fields to existing fees
        result = await db.fees.update_many(
            {"version": {"$exists": False}},
            {
                "$set": {
                    "version": 1,
                    "regenerated_at": None,
                    "regenerated_reason": None,
                    "parent_fee_id": None,
                    "is_regenerated": False
                }
            }
        )
        
        print(f"✅ Successfully migrated {result.modified_count} fees")
        
        # Create fee_audit_logs collection if it doesn't exist
        collections = await db.list_collection_names()
        if "fee_audit_logs" not in collections:
            await db.create_collection("fee_audit_logs")
            print("✅ Created fee_audit_logs collection")
        
        # Create indexes for better performance
        await db.fees.create_index([("bulan", 1), ("status", 1)])
        await db.fees.create_index([("user_id", 1), ("bulan", 1)])
        await db.fees.create_index([("regenerated_at", 1)])
        await db.fee_audit_logs.create_index([("month", 1), ("action", 1)])
        await db.fee_audit_logs.create_index([("timestamp", -1)])
        
        print("✅ Created performance indexes")
        
        # Verify migration
        migrated_count = await db.fees.count_documents({"version": {"$exists": True}})
        print(f"🔍 Verification: {migrated_count} fees now have versioning fields")
        
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        await close_database()

async def rollback_migration():
    """Rollback migration by removing versioning fields"""
    print("🔄 Starting rollback...")
    
    try:
        await init_database()
        db = get_database()
        
        # Remove versioning fields
        result = await db.fees.update_many(
            {"version": {"$exists": True}},
            {
                "$unset": {
                    "version": "",
                    "regenerated_at": "",
                    "regenerated_reason": "",
                    "parent_fee_id": "",
                    "is_regenerated": ""
                }
            }
        )
        
        print(f"✅ Rollback completed: {result.modified_count} fees reverted")
        
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        raise
    finally:
        await close_database()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate fee schema for versioning support")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    
    args = parser.parse_args()
    
    if args.rollback:
        asyncio.run(rollback_migration())
    else:
        asyncio.run(migrate_fee_schema())
