#!/usr/bin/env python3
"""
Test script for the new regenerate fee system
This script tests the improved regeneration functionality
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.database import get_database, init_database, close_database
from app.controllers.fee_controller import FeeController

async def test_regenerate_system():
    """Test the new regenerate fee system"""
    print("🧪 Testing new regenerate fee system...")
    
    try:
        await init_database()
        db = get_database()
        fee_controller = FeeController()
        
        # Test data
        test_month = "2024-12"
        test_tarif = {
            "60M2": 150000,
            "72M2": 200000,
            "HOOK": 100000
        }
        
        print(f"📅 Testing with month: {test_month}")
        print(f"💰 Test rates: {test_tarif}")
        
        # Step 1: Generate initial fees
        print("\n1️⃣ Generating initial fees...")
        initial_result = await fee_controller.generate_monthly_fees(test_month, test_tarif)
        print(f"✅ {initial_result['message']}")
        
        # Check initial fees
        initial_fees = await db.fees.find({"bulan": test_month}).to_list(1000)
        print(f"📊 Initial fees created: {len(initial_fees)}")
        
        # Step 2: Simulate some payments
        print("\n2️⃣ Simulating some payments...")
        # Mark some fees as paid
        paid_count = 0
        for i, fee in enumerate(initial_fees[:3]):  # Mark first 3 as paid
            await db.fees.update_one(
                {"id": fee["id"]},
                {"$set": {"status": "Berhasil"}}
            )
            paid_count += 1
        
        print(f"✅ Marked {paid_count} fees as paid")
        
        # Step 3: Test regeneration (should preserve paid fees)
        print("\n3️⃣ Testing regeneration (should preserve paid fees)...")
        new_tarif = {
            "60M2": 180000,  # Increased rates
            "72M2": 220000,
            "HOOK": 120000
        }
        
        regenerate_result = await fee_controller.regenerate_fees_for_month(
            test_month, new_tarif, "test_admin"
        )
        print(f"✅ {regenerate_result['message']}")
        print(f"💰 Paid fees preserved: {regenerate_result['paid_fees_preserved']}")
        print(f"🔄 Unpaid fees regenerated: {regenerate_result['unpaid_fees_regenerated']}")
        print(f"🆕 New fees created: {regenerate_result['new_fees_created']}")
        
        # Step 4: Check final state
        print("\n4️⃣ Checking final state...")
        final_fees = await db.fees.find({"bulan": test_month}).to_list(1000)
        paid_fees = [f for f in final_fees if f["status"] == "Berhasil"]
        regenerated_fees = [f for f in final_fees if f["status"] == "Regenerated"]
        new_fees = [f for f in final_fees if f["status"] == "Belum Bayar" and f.get("version", 1) == 1]
        
        print(f"📊 Final state:")
        print(f"   - Total fees: {len(final_fees)}")
        print(f"   - Paid fees (preserved): {len(paid_fees)}")
        print(f"   - Regenerated fees: {len(regenerated_fees)}")
        print(f"   - New unpaid fees: {len(new_fees)}")
        
        # Step 5: Test regeneration history
        print("\n5️⃣ Testing regeneration history...")
        history = await fee_controller.get_regeneration_history(test_month)
        print(f"📜 Regeneration history entries: {len(history)}")
        for entry in history:
            print(f"   - {entry['action']} by {entry['admin_user']} at {entry['timestamp']}")
        
        # Step 6: Test rollback
        print("\n6️⃣ Testing rollback...")
        rollback_result = await fee_controller.rollback_regeneration(test_month, "test_admin")
        print(f"✅ {rollback_result['message']}")
        
        # Check state after rollback
        post_rollback_fees = await db.fees.find({"bulan": test_month}).to_list(1000)
        paid_after_rollback = [f for f in post_rollback_fees if f["status"] == "Berhasil"]
        unpaid_after_rollback = [f for f in post_rollback_fees if f["status"] == "Belum Bayar"]
        
        print(f"📊 After rollback:")
        print(f"   - Paid fees: {len(paid_after_rollback)}")
        print(f"   - Unpaid fees: {len(unpaid_after_rollback)}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
    finally:
        await close_database()

async def cleanup_test_data():
    """Clean up test data"""
    print("🧹 Cleaning up test data...")
    
    try:
        await init_database()
        db = get_database()
        
        # Remove test fees
        result = await db.fees.delete_many({"bulan": "2024-12"})
        print(f"✅ Removed {result.deleted_count} test fees")
        
        # Remove test audit logs
        audit_result = await db.fee_audit_logs.delete_many({"month": "2024-12"})
        print(f"✅ Removed {audit_result.deleted_count} test audit logs")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        raise
    finally:
        await close_database()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the new regenerate fee system")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data")
    
    args = parser.parse_args()
    
    if args.cleanup:
        asyncio.run(cleanup_test_data())
    else:
        asyncio.run(test_regenerate_system())
