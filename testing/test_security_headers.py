"""
Test 2: Security Headers
Memastikan aplikasi memiliki HTTP security headers yang proper
untuk proteksi dari XSS, clickjacking, dll.
"""

import requests
from typing import List, Dict, Any
from test_models import TestResult

class SecurityHeadersTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results: List[TestResult] = []
        
        # Define required security headers
        self.required_headers = {
            'X-Content-Type-Options': {
                'expected': 'nosniff',
                'severity': 'WARNING',
                'description': 'Prevents MIME type sniffing'
            },
            'X-Frame-Options': {
                'expected': ['DENY', 'SAMEORIGIN'],
                'severity': 'WARNING',
                'description': 'Prevents clickjacking attacks'
            },
            'X-XSS-Protection': {
                'expected_contains': '1',
                'severity': 'WARNING',
                'description': 'Enables XSS filter in older browsers'
            },
            'Strict-Transport-Security': {
                'expected_contains': 'max-age=',
                'severity': 'WARNING',
                'description': 'Forces HTTPS connections'
            }
        }
    
    def test_security_headers(self):
        """Test: Check all security headers"""
        print("  🔍 Checking security headers...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            
            for header_name, config in self.required_headers.items():
                self._check_header(header_name, config, response.headers)
            
        except Exception as e:
            self.results.append(TestResult(
                name="Security Headers Check",
                passed=False,
                message=f"❌ Error checking headers: {str(e)}",
                severity="WARNING"
            ))
    
    def _check_header(self, header_name: str, config: Dict[str, Any], headers: Dict[str, str]):
        """Check individual header"""
        actual_value = headers.get(header_name)
        
        if not actual_value:
            self.results.append(TestResult(
                name=f"Header: {header_name}",
                passed=False,
                message=f"❌ Missing header: {header_name}",
                severity=config['severity'],
                recommendation=f"Add {header_name} header. {config['description']}"
            ))
            return
        
        # Check expected value
        if 'expected' in config:
            expected = config['expected']
            if isinstance(expected, list):
                if actual_value in expected:
                    self.results.append(TestResult(
                        name=f"Header: {header_name}",
                        passed=True,
                        message=f"✅ {header_name}: {actual_value}",
                        severity="INFO"
                    ))
                else:
                    self.results.append(TestResult(
                        name=f"Header: {header_name}",
                        passed=False,
                        message=f"⚠️  {header_name} has unexpected value: {actual_value} (expected: {' or '.join(expected)})",
                        severity=config['severity'],
                        recommendation=f"Set {header_name} to one of: {', '.join(expected)}"
                    ))
            else:
                if actual_value == expected:
                    self.results.append(TestResult(
                        name=f"Header: {header_name}",
                        passed=True,
                        message=f"✅ {header_name}: {actual_value}",
                        severity="INFO"
                    ))
                else:
                    self.results.append(TestResult(
                        name=f"Header: {header_name}",
                        passed=False,
                        message=f"⚠️  {header_name} has incorrect value: {actual_value} (expected: {expected})",
                        severity=config['severity'],
                        recommendation=f"Set {header_name} to: {expected}"
                    ))
        
        elif 'expected_contains' in config:
            if config['expected_contains'] in actual_value:
                self.results.append(TestResult(
                    name=f"Header: {header_name}",
                    passed=True,
                    message=f"✅ {header_name}: {actual_value}",
                    severity="INFO"
                ))
            else:
                self.results.append(TestResult(
                    name=f"Header: {header_name}",
                    passed=False,
                    message=f"⚠️  {header_name} missing expected content: {actual_value}",
                    severity=config['severity'],
                    recommendation=f"Ensure {header_name} contains: {config['expected_contains']}"
                ))
    
    def test_cors_configuration(self):
        """Test: CORS configuration security"""
        print("  🔍 Checking CORS configuration...")
        
        try:
            # Test dengan origin yang tidak dikenal
            headers = {"Origin": "https://malicious-attacker-site.com"}
            response = requests.get(f"{self.base_url}/", headers=headers, timeout=5)
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_creds = response.headers.get('Access-Control-Allow-Credentials')
            
            # Check untuk wildcard dengan credentials (security issue)
            if cors_origin == '*' and cors_creds == 'true':
                self.results.append(TestResult(
                    name="CORS Configuration",
                    passed=False,
                    message="❌ CRITICAL: CORS allows all origins (*) with credentials enabled",
                    severity="CRITICAL",
                    recommendation="Never use wildcard (*) with allow_credentials=True. Specify exact origins."
                ))
            elif cors_origin == '*':
                self.results.append(TestResult(
                    name="CORS Configuration",
                    passed=False,
                    message="⚠️  CORS allows all origins (*)",
                    severity="WARNING",
                    recommendation="For production, specify exact allowed origins instead of wildcard"
                ))
            elif cors_origin and 'malicious-attacker-site.com' in cors_origin:
                self.results.append(TestResult(
                    name="CORS Configuration",
                    passed=False,
                    message="❌ CORS allows unauthorized origins",
                    severity="CRITICAL",
                    recommendation="Configure CORS to only allow trusted origins"
                ))
            else:
                self.results.append(TestResult(
                    name="CORS Configuration",
                    passed=True,
                    message="✅ CORS properly configured (rejects unauthorized origins)",
                    severity="INFO"
                ))
                
        except Exception as e:
            self.results.append(TestResult(
                name="CORS Configuration",
                passed=False,
                message=f"⚠️  Error testing CORS: {str(e)}",
                severity="WARNING"
            ))
    
    def test_content_security_policy(self):
        """Test: Content Security Policy header (optional but recommended)"""
        print("  🔍 Checking Content Security Policy...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            csp = response.headers.get('Content-Security-Policy')
            
            if csp:
                self.results.append(TestResult(
                    name="Content-Security-Policy",
                    passed=True,
                    message=f"✅ CSP configured: {csp[:100]}...",
                    severity="INFO"
                ))
            else:
                self.results.append(TestResult(
                    name="Content-Security-Policy",
                    passed=False,
                    message="ℹ️  CSP not configured (optional but recommended for API)",
                    severity="INFO",
                    recommendation="Consider adding CSP header for additional XSS protection"
                ))
        except Exception as e:
            self.results.append(TestResult(
                name="Content-Security-Policy",
                passed=False,
                message=f"⚠️  Error checking CSP: {str(e)}",
                severity="INFO"
            ))
    
    def run_tests(self) -> List[TestResult]:
        """Jalankan semua security header tests"""
        self.test_security_headers()
        self.test_cors_configuration()
        self.test_content_security_policy()
        
        # Print summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print(f"\n  ✅ Passed: {passed}/{total}")
        
        return self.results
