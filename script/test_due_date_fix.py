#!/usr/bin/env python3
"""
Test script for due date fix - ensure due dates fall on month end
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from calendar import monthrange

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.database import get_database, init_database, close_database
from app.controllers.fee_controller import FeeController

async def test_due_date_fix():
    """Test that due dates are set to month end"""
    print("🧪 Testing due date fix - should fall on month end...")
    
    try:
        await init_database()
        db = get_database()
        fee_controller = FeeController()
        
        # Test different months
        test_months = [
            "2024-01",  # January (31 days)
            "2024-02",  # February (29 days - leap year)
            "2024-04",  # April (30 days)
            "2024-12",  # December (31 days)
        ]
        
        test_tarif = {
            "60M2": 150000,
            "72M2": 200000,
            "HOOK": 100000
        }
        
        for bulan in test_months:
            print(f"\n📅 Testing month: {bulan}")
            
            # Parse month to get expected last day
            year, month = map(int, bulan.split('-'))
            expected_last_day = monthrange(year, month)[1]
            
            # Generate fees for this month
            result = await fee_controller.generate_monthly_fees(bulan, test_tarif)
            print(f"✅ {result['message']}")
            
            # Check due dates
            fees = await db.fees.find({"bulan": bulan}).to_list(1000)
            print(f"📊 Generated {len(fees)} fees")
            
            for fee in fees:
                due_date = fee["due_date"]
                due_day = due_date.day
                due_month = due_date.month
                due_year = due_date.year
                
                print(f"   Fee {fee['id'][:8]}... - Due: {due_date.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Verify due date is on the last day of the month
                if due_day == expected_last_day and due_month == month and due_year == year:
                    print(f"   ✅ Correct - Due date is on last day ({expected_last_day})")
                else:
                    print(f"   ❌ ERROR - Expected day {expected_last_day}, got {due_day}")
                    return False
            
            # Clean up test data
            await db.fees.delete_many({"bulan": bulan})
            print(f"🧹 Cleaned up test data for {bulan}")
        
        print("\n🎉 All due date tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    finally:
        await close_database()

async def test_edge_cases():
    """Test edge cases for due date calculation"""
    print("\n🔍 Testing edge cases...")
    
    try:
        await init_database()
        db = get_database()
        fee_controller = FeeController()
        
        # Test invalid month format
        print("Testing invalid month format...")
        try:
            result = await fee_controller.generate_monthly_fees("invalid-month", {"60M2": 100000})
            # Check if it handled gracefully (should create 0 fees)
            if "0 tagihan" in result["message"]:
                print("✅ Correctly handled invalid month format (0 fees created)")
            else:
                print("❌ Should have created 0 fees for invalid month format")
                return False
        except Exception as e:
            print(f"✅ Correctly handled invalid month format with exception: {e}")
        
        # Test leap year February
        print("Testing leap year February...")
        result = await fee_controller.generate_monthly_fees("2024-02", {"60M2": 100000})
        fees = await db.fees.find({"bulan": "2024-02"}).to_list(1000)
        
        if fees:
            due_date = fees[0]["due_date"]
            if due_date.day == 29:  # Leap year has 29 days
                print("✅ Correctly handled leap year February (29 days)")
            else:
                print(f"❌ Expected 29 days, got {due_date.day}")
                return False
        
        # Clean up
        await db.fees.delete_many({"bulan": "2024-02"})
        
        print("✅ All edge case tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Edge case test failed: {str(e)}")
        return False
    finally:
        await close_database()

if __name__ == "__main__":
    async def main():
        success1 = await test_due_date_fix()
        success2 = await test_edge_cases()
        
        if success1 and success2:
            print("\n🎉 ALL TESTS PASSED! Due dates now fall on month end.")
        else:
            print("\n❌ Some tests failed.")
            sys.exit(1)
    
    asyncio.run(main())
