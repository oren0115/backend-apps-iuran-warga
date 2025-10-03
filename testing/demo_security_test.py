"""
Demo Security Test - Simplified untuk quick check
Jalankan test ini untuk quick security assessment
"""

import requests
import sys
from datetime import datetime

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)

def test_basic_security(base_url):
    """Quick security checks"""
    
    print_section("🔒 QUICK SECURITY ASSESSMENT")
    print(f"Target: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    issues = []
    warnings = []
    passed = []
    
    # Test 1: HTTPS Check
    print("1️⃣  Checking HTTPS...")
    if base_url.startswith("https://"):
        passed.append("✅ Using HTTPS")
        print("   ✅ PASS: Application uses HTTPS")
    else:
        issues.append("❌ NOT using HTTPS")
        print("   ❌ FAIL: Application uses HTTP (insecure!)")
    
    # Test 2: Protected endpoints
    print("\n2️⃣  Checking endpoint protection...")
    try:
        response = requests.get(f"{base_url}/api/profile", timeout=5)
        if response.status_code in [401, 403]:
            passed.append("✅ Endpoints protected")
            print("   ✅ PASS: Protected endpoints require authentication")
        else:
            issues.append("❌ Endpoints not protected")
            print("   ❌ FAIL: Endpoints accessible without authentication")
    except Exception as e:
        warnings.append(f"⚠️  Could not test endpoint protection: {e}")
        print(f"   ⚠️  WARNING: {e}")
    
    # Test 3: Security Headers
    print("\n3️⃣  Checking security headers...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        headers_found = 0
        headers_missing = 0
        
        critical_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"]
        }
        
        for header, expected in critical_headers.items():
            if header in response.headers:
                headers_found += 1
                print(f"   ✅ {header}: {response.headers[header]}")
            else:
                headers_missing += 1
                print(f"   ⚠️  {header}: Missing")
        
        if headers_missing > 0:
            warnings.append(f"⚠️  {headers_missing} security headers missing")
        else:
            passed.append("✅ Security headers configured")
            
    except Exception as e:
        warnings.append(f"⚠️  Could not check headers: {e}")
        print(f"   ⚠️  WARNING: {e}")
    
    # Test 4: CORS Check
    print("\n4️⃣  Checking CORS configuration...")
    try:
        response = requests.get(
            f"{base_url}/", 
            headers={"Origin": "https://malicious-site.com"},
            timeout=5
        )
        cors = response.headers.get("Access-Control-Allow-Origin")
        
        if cors == "*":
            warnings.append("⚠️  CORS allows all origins")
            print("   ⚠️  WARNING: CORS allows all origins (*)")
        elif cors:
            print(f"   ℹ️  CORS configured: {cors}")
            passed.append("✅ CORS configured")
        else:
            print("   ℹ️  CORS headers not present")
            
    except Exception as e:
        print(f"   ⚠️  WARNING: {e}")
    
    # Test 5: Webhook endpoint check
    print("\n5️⃣  Checking webhook security...")
    try:
        fake_notification = {
            "order_id": "fake-123",
            "status_code": "200",
            "gross_amount": "100000",
            "signature_key": "invalid_signature_xyz"
        }
        
        response = requests.post(
            f"{base_url}/api/payments/notification",
            json=fake_notification,
            timeout=5
        )
        
        if response.status_code == 401:
            passed.append("✅ Webhook signature verification enabled")
            print("   ✅ PASS: Webhook rejects invalid signatures")
        elif response.status_code in [400, 422]:
            passed.append("✅ Webhook input validation enabled")
            print("   ✅ PASS: Webhook validates input")
        elif response.status_code == 200:
            issues.append("❌ Webhook may accept fake notifications")
            print("   ❌ CRITICAL: Webhook might accept invalid signatures!")
        else:
            print(f"   ℹ️  Webhook response: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  WARNING: {e}")
    
    # Print Summary
    print_section("📊 SUMMARY")
    
    print(f"\n✅ Passed Checks: {len(passed)}")
    for p in passed:
        print(f"   {p}")
    
    if warnings:
        print(f"\n⚠️  Warnings: {len(warnings)}")
        for w in warnings:
            print(f"   {w}")
    
    if issues:
        print(f"\n❌ Critical Issues: {len(issues)}")
        for i in issues:
            print(f"   {i}")
    
    print(f"\n{'='*80}")
    
    # Verdict
    if len(issues) > 0:
        print("🚫 VERDICT: NOT READY FOR PRODUCTION")
        print("   Fix critical issues before deployment!")
        return False
    elif len(warnings) > 0:
        print("⚠️  VERDICT: READY WITH WARNINGS")
        print("   Consider fixing warnings for better security.")
        return True
    else:
        print("✅ VERDICT: READY FOR PRODUCTION")
        print("   All basic security checks passed!")
        return True

def main():
    if len(sys.argv) < 2:
        print("\n🔒 Quick Security Assessment Tool")
        print("\nUsage: python testing/demo_security_test.py <base_url>")
        print("Example: python testing/demo_security_test.py http://localhost:8000")
        print("\nFor comprehensive testing, use: python testing/run_security_tests.py\n")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    try:
        success = test_basic_security(base_url)
        
        print(f"\n{'='*80}")
        print("📋 NEXT STEPS:")
        print("="*80)
        print("\n1. Run comprehensive tests:")
        print("   python testing/run_security_tests.py", base_url)
        print("\n2. Check implementation guide:")
        print("   See testing/IMPLEMENTATION_GUIDE.md")
        print("\n3. Check dependencies:")
        print("   python testing/check_dependencies.py")
        print()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
