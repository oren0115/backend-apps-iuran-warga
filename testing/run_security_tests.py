"""
Main Security Testing Runner
Jalankan semua security tests untuk memastikan aplikasi siap production

Usage:
    python testing/run_security_tests.py http://localhost:8000
    python testing/run_security_tests.py https://your-staging-url.com
"""

import sys
import os
from typing import List
from dataclasses import dataclass
from datetime import datetime

# Import all test modules
from test_webhook_security import WebhookSecurityTester
from test_rate_limiting import RateLimitingTester
from test_security_headers import SecurityHeadersTester
from test_https_config import HTTPSConfigTester

@dataclass
class TestSummary:
    total_tests: int
    passed: int
    failed: int
    critical_failures: int
    warnings: int
    timestamp: str

class SecurityTestRunner:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
        
    def run_all_tests(self) -> TestSummary:
        """Jalankan semua security tests"""
        print("\n" + "="*80)
        print("🔒 SECURITY TESTING SUITE - PRODUCTION READINESS CHECK")
        print("="*80)
        print(f"📍 Target URL: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        # Test 1: HTTPS Configuration
        print("\n📋 TEST 1/4: HTTPS Configuration & SSL/TLS")
        print("-" * 80)
        https_tester = HTTPSConfigTester(self.base_url)
        https_results = https_tester.run_tests()
        self.results.extend(https_results)
        
        # Test 2: Security Headers
        print("\n📋 TEST 2/4: Security Headers (XSS, Clickjacking Protection)")
        print("-" * 80)
        headers_tester = SecurityHeadersTester(self.base_url)
        headers_results = headers_tester.run_tests()
        self.results.extend(headers_results)
        
        # Test 3: Rate Limiting
        print("\n📋 TEST 3/4: Rate Limiting & Abuse Prevention")
        print("-" * 80)
        rate_limit_tester = RateLimitingTester(self.base_url)
        rate_limit_results = rate_limit_tester.run_tests()
        self.results.extend(rate_limit_results)
        
        # Test 4: Webhook Security
        print("\n📋 TEST 4/4: Payment Webhook Security (Midtrans)")
        print("-" * 80)
        webhook_tester = WebhookSecurityTester(self.base_url)
        webhook_results = webhook_tester.run_tests()
        self.results.extend(webhook_results)
        
        # Generate summary
        return self.generate_summary()
    
    def generate_summary(self) -> TestSummary:
        """Generate test summary"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total_tests - passed
        critical_failures = sum(1 for r in self.results if not r.passed and r.severity == "CRITICAL")
        warnings = sum(1 for r in self.results if not r.passed and r.severity == "WARNING")
        
        return TestSummary(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            critical_failures=critical_failures,
            warnings=warnings,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def print_results(self, summary: TestSummary):
        """Print detailed results"""
        print("\n" + "="*80)
        print("📊 DETAILED TEST RESULTS")
        print("="*80 + "\n")
        
        # Group results by severity
        critical_issues = [r for r in self.results if not r.passed and r.severity == "CRITICAL"]
        warnings = [r for r in self.results if not r.passed and r.severity == "WARNING"]
        passed_tests = [r for r in self.results if r.passed]
        
        # Print critical issues first
        if critical_issues:
            print("🚨 CRITICAL ISSUES (MUST FIX BEFORE PRODUCTION):")
            print("-" * 80)
            for i, result in enumerate(critical_issues, 1):
                print(f"{i}. {result.name}")
                print(f"   Status: ❌ FAILED")
                print(f"   Message: {result.message}")
                if result.recommendation:
                    print(f"   Fix: {result.recommendation}")
                print()
        
        # Print warnings
        if warnings:
            print("\n⚠️  WARNINGS (RECOMMENDED TO FIX):")
            print("-" * 80)
            for i, result in enumerate(warnings, 1):
                print(f"{i}. {result.name}")
                print(f"   Status: ⚠️  WARNING")
                print(f"   Message: {result.message}")
                if result.recommendation:
                    print(f"   Fix: {result.recommendation}")
                print()
        
        # Print summary
        print("\n" + "="*80)
        print("📈 SUMMARY")
        print("="*80)
        print(f"Total Tests Run: {summary.total_tests}")
        print(f"✅ Passed: {summary.passed} ({summary.passed/summary.total_tests*100:.1f}%)")
        print(f"❌ Failed: {summary.failed} ({summary.failed/summary.total_tests*100:.1f}%)")
        print(f"🚨 Critical Issues: {summary.critical_failures}")
        print(f"⚠️  Warnings: {summary.warnings}")
        print(f"⏰ Completed at: {summary.timestamp}")
        print("="*80)
        
        # Final verdict
        print()
        if summary.critical_failures > 0:
            print("🚫 PRODUCTION DEPLOYMENT: NOT READY")
            print("   Fix all CRITICAL issues before deploying to production!")
            return False
        elif summary.warnings > 0:
            print("⚠️  PRODUCTION DEPLOYMENT: READY WITH WARNINGS")
            print("   Consider fixing warnings for better security posture.")
            return True
        else:
            print("✅ PRODUCTION DEPLOYMENT: READY")
            print("   All security tests passed!")
            return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python testing/run_security_tests.py <base_url>")
        print("Example: python testing/run_security_tests.py http://localhost:8000")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    runner = SecurityTestRunner(base_url)
    summary = runner.run_all_tests()
    success = runner.print_results(summary)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
