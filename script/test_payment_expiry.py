#!/usr/bin/env python3
"""
Test script untuk memverifikasi konfigurasi waktu kadaluarsa pembayaran.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_payment_expiry_configuration():
    """Test konfigurasi waktu kadaluarsa pembayaran"""
    
    print("🧪 Testing Payment Expiry Configuration")
    print("=" * 50)
    
    # Test 1: Default value (30 minutes)
    print("\n1. Testing default expiry time (30 minutes):")
    expiry_minutes = int(os.getenv("PAYMENT_EXPIRY_MINUTES", "30"))
    print(f"   PAYMENT_EXPIRY_MINUTES = {expiry_minutes}")
    
    current_time = datetime.now(timezone.utc)
    expiry_time = current_time + timedelta(minutes=expiry_minutes)
    
    print(f"   Current time (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Expiry time (UTC):  {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Duration: {expiry_minutes} minutes")
    
    # Test 2: Different values
    print("\n2. Testing different expiry values:")
    test_values = [15, 30, 60, 120]
    
    for minutes in test_values:
        test_expiry = current_time + timedelta(minutes=minutes)
        print(f"   {minutes:3d} minutes: {test_expiry.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 3: Environment variable validation
    print("\n3. Environment variable validation:")
    env_value = os.getenv("PAYMENT_EXPIRY_MINUTES")
    if env_value:
        try:
            parsed_value = int(env_value)
            if parsed_value > 0:
                print(f"   ✅ PAYMENT_EXPIRY_MINUTES is valid: {parsed_value}")
            else:
                print(f"   ❌ PAYMENT_EXPIRY_MINUTES must be positive: {parsed_value}")
        except ValueError:
            print(f"   ❌ PAYMENT_EXPIRY_MINUTES must be a number: {env_value}")
    else:
        print("   ℹ️  PAYMENT_EXPIRY_MINUTES not set, using default: 30")
    
    # Test 4: Comparison with old value (24 hours)
    print("\n4. Comparison with previous configuration:")
    old_expiry = current_time + timedelta(hours=24)
    new_expiry = current_time + timedelta(minutes=expiry_minutes)
    
    print(f"   Old expiry (24 hours): {old_expiry.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   New expiry ({expiry_minutes} min): {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}")
    
    time_diff = old_expiry - new_expiry
    print(f"   Time difference: {time_diff}")
    
    print("\n✅ Payment expiry configuration test completed!")
    print("\n📝 Notes:")
    print("   - Set PAYMENT_EXPIRY_MINUTES in your .env file to customize expiry time")
    print("   - Default value is 30 minutes if not specified")
    print("   - Value must be a positive integer (minutes)")

if __name__ == "__main__":
    test_payment_expiry_configuration()
