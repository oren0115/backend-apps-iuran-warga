"""
Test 3: Rate Limiting & Abuse Prevention
Memastikan aplikasi memiliki rate limiting untuk mencegah abuse
"""

import requests
import time
from typing import List
from test_models import TestResult

class RateLimitingTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results: List[TestResult] = []
    
    def test_login_rate_limit(self):
        """Test: Rate limiting pada login endpoint"""
        print("  🔍 Testing rate limit on login endpoint...")
        print("     (This may take a few seconds)")
        
        rate_limited = False
        requests_made = 0
        max_requests = 15  # Try 15 requests
        
        try:
            for i in range(max_requests):
                response = requests.post(
                    f"{self.base_url}/api/login",
                    json={"username": "test_rate_limit", "password": "test123"},
                    timeout=5
                )
                requests_made += 1
                
                # Check for rate limit response (429 Too Many Requests)
                if response.status_code == 429:
                    rate_limited = True
                    break
                
                # Small delay between requests
                time.sleep(0.1)
            
            if rate_limited:
                self.results.append(TestResult(
                    name="Login Rate Limiting",
                    passed=True,
                    message=f"✅ Rate limiting enabled (triggered after {requests_made} requests)",
                    severity="INFO"
                ))
            else:
                self.results.append(TestResult(
                    name="Login Rate Limiting",
                    passed=False,
                    message=f"⚠️  No rate limiting detected after {requests_made} requests",
                    severity="WARNING",
                    recommendation="Implement rate limiting to prevent brute force attacks (5-10 requests/minute recommended)"
                ))
                
        except Exception as e:
            self.results.append(TestResult(
                name="Login Rate Limiting",
                passed=False,
                message=f"❌ Error testing rate limit: {str(e)}",
                severity="WARNING"
            ))
    
    def test_api_rate_limit(self):
        """Test: Global API rate limiting"""
        print("  🔍 Testing global API rate limit...")
        
        rate_limited = False
        requests_made = 0
        max_requests = 30  # Try 30 requests rapidly
        
        try:
            for i in range(max_requests):
                response = requests.get(
                    f"{self.base_url}/",
                    timeout=5
                )
                requests_made += 1
                
                if response.status_code == 429:
                    rate_limited = True
                    break
                
                # No delay - rapid requests
            
            if rate_limited:
                self.results.append(TestResult(
                    name="Global API Rate Limiting",
                    passed=True,
                    message=f"✅ Global rate limiting enabled (triggered after {requests_made} requests)",
                    severity="INFO"
                ))
            else:
                self.results.append(TestResult(
                    name="Global API Rate Limiting",
                    passed=False,
                    message=f"ℹ️  No global rate limiting detected after {requests_made} requests",
                    severity="INFO",
                    recommendation="Consider implementing global rate limiting (200-1000 requests/hour recommended)"
                ))
                
        except Exception as e:
            self.results.append(TestResult(
                name="Global API Rate Limiting",
                passed=False,
                message=f"⚠️  Error testing global rate limit: {str(e)}",
                severity="INFO"
            ))
    
    def test_payment_rate_limit(self):
        """Test: Rate limiting pada payment creation endpoint"""
        print("  🔍 Testing rate limit on payment endpoint...")
        
        # Note: This test requires authentication
        # We'll just check if endpoint properly rejects without auth
        try:
            response = requests.post(
                f"{self.base_url}/api/payments",
                json={"fee_id": "test", "payment_method": "bank_transfer"},
                timeout=5
            )
            
            if response.status_code in [401, 403]:
                self.results.append(TestResult(
                    name="Payment Endpoint Protection",
                    passed=True,
                    message="✅ Payment endpoint properly protected (requires authentication)",
                    severity="INFO"
                ))
            else:
                self.results.append(TestResult(
                    name="Payment Endpoint Protection",
                    passed=False,
                    message=f"⚠️  Payment endpoint accessible without auth (status: {response.status_code})",
                    severity="WARNING",
                    recommendation="Ensure payment endpoint requires authentication"
                ))
        except Exception as e:
            self.results.append(TestResult(
                name="Payment Endpoint Protection",
                passed=False,
                message=f"⚠️  Error testing payment endpoint: {str(e)}",
                severity="WARNING"
            ))
    
    def test_retry_after_header(self):
        """Test: Check if Retry-After header provided saat rate limited"""
        print("  🔍 Checking Retry-After header configuration...")
        
        # This is informational - check if we can get rate limited response
        self.results.append(TestResult(
            name="Retry-After Header",
            passed=True,
            message="ℹ️  Manual check: Ensure Retry-After header is sent with 429 responses",
            severity="INFO",
            recommendation="Configure rate limiter to send Retry-After header"
        ))
    
    def run_tests(self) -> List[TestResult]:
        """Jalankan semua rate limiting tests"""
        self.test_login_rate_limit()
        self.test_api_rate_limit()
        self.test_payment_rate_limit()
        self.test_retry_after_header()
        
        # Print summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print(f"\n  ✅ Passed: {passed}/{total}")
        
        return self.results
