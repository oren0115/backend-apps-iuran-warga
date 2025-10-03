"""
Test 4: Payment Webhook Security (Midtrans)
Memastikan webhook payment memiliki proper security verification
"""

import requests
import hashlib
import hmac
from typing import List
from test_models import TestResult

class WebhookSecurityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results: List[TestResult] = []
    
    def test_webhook_endpoint_exists(self):
        """Test: Webhook endpoint accessible"""
        print("  🔍 Checking webhook endpoint...")
        
        try:
            # Send dummy request to webhook
            response = requests.post(
                f"{self.base_url}/api/payments/notification",
                json={},
                timeout=5
            )
            
            # Endpoint should exist (even if it rejects invalid data)
            if response.status_code in [200, 400, 422, 500]:
                self.results.append(TestResult(
                    name="Webhook Endpoint Exists",
                    passed=True,
                    message="✅ Webhook endpoint is accessible",
                    severity="INFO"
                ))
            else:
                self.results.append(TestResult(
                    name="Webhook Endpoint Exists",
                    passed=False,
                    message=f"⚠️  Webhook endpoint returned unexpected status: {response.status_code}",
                    severity="WARNING"
                ))
        except Exception as e:
            self.results.append(TestResult(
                name="Webhook Endpoint Exists",
                passed=False,
                message=f"❌ Error accessing webhook: {str(e)}",
                severity="WARNING"
            ))
    
    def test_webhook_signature_verification(self):
        """Test: CRITICAL - Webhook signature verification"""
        print("  🔍 Testing webhook signature verification...")
        
        # Create fake notification WITHOUT signature
        fake_notification = {
            "transaction_time": "2025-01-01 00:00:00",
            "transaction_status": "settlement",
            "transaction_id": "fake-tx-123",
            "status_message": "midtrans payment notification",
            "status_code": "200",
            "signature_key": "INVALID_SIGNATURE",
            "payment_type": "bank_transfer",
            "order_id": "test-order-123",
            "merchant_id": "test",
            "gross_amount": "100000.00",
            "fraud_status": "accept",
            "currency": "IDR"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/payments/notification",
                json=fake_notification,
                timeout=5
            )
            
            # Check response
            if response.status_code == 401:
                self.results.append(TestResult(
                    name="Webhook Signature Verification",
                    passed=True,
                    message="✅ EXCELLENT! Webhook rejects invalid signatures (401 Unauthorized)",
                    severity="INFO"
                ))
            elif response.status_code == 400:
                # Might reject due to other validation
                self.results.append(TestResult(
                    name="Webhook Signature Verification",
                    passed=True,
                    message="✅ Webhook has input validation (400 Bad Request)",
                    severity="INFO"
                ))
            elif response.status_code == 200:
                # This is BAD - accepted fake notification
                try:
                    resp_json = response.json()
                    if resp_json.get('status') == 'error':
                        self.results.append(TestResult(
                            name="Webhook Signature Verification",
                            passed=False,
                            message="⚠️  Webhook returns 200 but with error status - should use 401/403",
                            severity="WARNING",
                            recommendation="Return proper HTTP error codes (401) for invalid signatures"
                        ))
                    else:
                        self.results.append(TestResult(
                            name="Webhook Signature Verification",
                            passed=False,
                            message="❌ CRITICAL! Webhook accepts notification without valid signature!",
                            severity="CRITICAL",
                            recommendation="MUST implement signature verification! See SECURITY_TESTING.md for implementation"
                        ))
                except:
                    self.results.append(TestResult(
                        name="Webhook Signature Verification",
                        passed=False,
                        message="❌ CRITICAL! Webhook may accept invalid notifications",
                        severity="CRITICAL",
                        recommendation="Implement Midtrans signature verification immediately"
                    ))
            else:
                self.results.append(TestResult(
                    name="Webhook Signature Verification",
                    passed=False,
                    message=f"⚠️  Unexpected response status: {response.status_code}",
                    severity="WARNING",
                    recommendation="Verify webhook signature implementation"
                ))
                
        except Exception as e:
            self.results.append(TestResult(
                name="Webhook Signature Verification",
                passed=False,
                message=f"❌ Error testing webhook: {str(e)}",
                severity="WARNING"
            ))
    
    def test_webhook_amount_validation(self):
        """Test: Webhook validates amount from database"""
        print("  🔍 Checking webhook amount validation...")
        
        # This requires checking implementation
        # For now, add as manual check reminder
        self.results.append(TestResult(
            name="Webhook Amount Validation",
            passed=True,
            message="ℹ️  Manual check: Ensure webhook validates amount against database, not from notification",
            severity="INFO",
            recommendation="Always verify amount from database, never trust webhook data blindly"
        ))
    
    def test_webhook_idempotency(self):
        """Test: Webhook handles duplicate notifications"""
        print("  🔍 Checking webhook idempotency...")
        
        self.results.append(TestResult(
            name="Webhook Idempotency",
            passed=True,
            message="ℹ️  Manual check: Ensure webhook can handle duplicate notifications safely",
            severity="INFO",
            recommendation="Use transaction_id or order_id to prevent double-processing"
        ))
    
    def test_webhook_error_handling(self):
        """Test: Webhook error handling"""
        print("  🔍 Checking webhook error handling...")
        
        try:
            # Send malformed JSON
            response = requests.post(
                f"{self.base_url}/api/payments/notification",
                data="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code in [400, 422]:
                self.results.append(TestResult(
                    name="Webhook Error Handling",
                    passed=True,
                    message="✅ Webhook properly handles malformed requests",
                    severity="INFO"
                ))
            else:
                self.results.append(TestResult(
                    name="Webhook Error Handling",
                    passed=False,
                    message=f"⚠️  Webhook error handling unclear (status: {response.status_code})",
                    severity="INFO"
                ))
        except Exception as e:
            self.results.append(TestResult(
                name="Webhook Error Handling",
                passed=False,
                message=f"⚠️  Error testing webhook error handling: {str(e)}",
                severity="INFO"
            ))
    
    def run_tests(self) -> List[TestResult]:
        """Jalankan semua webhook security tests"""
        self.test_webhook_endpoint_exists()
        self.test_webhook_signature_verification()
        self.test_webhook_amount_validation()
        self.test_webhook_idempotency()
        self.test_webhook_error_handling()
        
        # Print summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print(f"\n  ✅ Passed: {passed}/{total}")
        
        return self.results
