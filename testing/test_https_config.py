"""
Test 1: HTTPS Configuration & SSL/TLS Security
Memastikan aplikasi menggunakan HTTPS dan konfigurasi SSL yang aman
"""

import requests
import urllib3
from typing import List
from test_models import TestResult

# Disable SSL warnings untuk testing purposes
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HTTPSConfigTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results: List[TestResult] = []
    
    def test_https_enabled(self):
        """Test: Aplikasi menggunakan HTTPS"""
        print("  🔍 Checking HTTPS usage...")
        
        if self.base_url.startswith("https://"):
            self.results.append(TestResult(
                name="HTTPS Protocol",
                passed=True,
                message="✅ Application is using HTTPS",
                severity="INFO"
            ))
        else:
            self.results.append(TestResult(
                name="HTTPS Protocol",
                passed=False,
                message="❌ Application is NOT using HTTPS - HTTP detected",
                severity="CRITICAL",
                recommendation="Enable HTTPS/SSL certificate before production deployment. Use Let's Encrypt for free SSL certificates."
            ))
    
    def test_http_to_https_redirect(self):
        """Test: HTTP redirect ke HTTPS"""
        print("  🔍 Checking HTTP to HTTPS redirect...")
        
        # Skip jika base URL bukan HTTPS
        if not self.base_url.startswith("https://"):
            self.results.append(TestResult(
                name="HTTP to HTTPS Redirect",
                passed=False,
                message="⚠️  Cannot test redirect - application not using HTTPS",
                severity="WARNING",
                recommendation="Configure web server to redirect all HTTP traffic to HTTPS"
            ))
            return
        
        # Test redirect dari HTTP
        http_url = self.base_url.replace("https://", "http://")
        try:
            response = requests.get(http_url, allow_redirects=False, timeout=5)
            
            if response.status_code in [301, 302, 307, 308]:
                location = response.headers.get('Location', '')
                if location.startswith('https://'):
                    self.results.append(TestResult(
                        name="HTTP to HTTPS Redirect",
                        passed=True,
                        message=f"✅ HTTP correctly redirects to HTTPS (status: {response.status_code})",
                        severity="INFO"
                    ))
                else:
                    self.results.append(TestResult(
                        name="HTTP to HTTPS Redirect",
                        passed=False,
                        message=f"⚠️  HTTP redirects but not to HTTPS: {location}",
                        severity="WARNING",
                        recommendation="Ensure redirect target is HTTPS"
                    ))
            else:
                self.results.append(TestResult(
                    name="HTTP to HTTPS Redirect",
                    passed=False,
                    message=f"⚠️  No redirect configured (status: {response.status_code})",
                    severity="WARNING",
                    recommendation="Configure automatic HTTP to HTTPS redirect in your web server"
                ))
        except requests.exceptions.RequestException:
            self.results.append(TestResult(
                name="HTTP to HTTPS Redirect",
                passed=True,
                message="✅ HTTP port appears to be closed (good if only HTTPS is accessible)",
                severity="INFO"
            ))
    
    def test_hsts_header(self):
        """Test: Strict-Transport-Security header"""
        print("  🔍 Checking HSTS header...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            hsts = response.headers.get('Strict-Transport-Security')
            
            if hsts:
                # Check HSTS configuration
                if 'max-age=' in hsts:
                    max_age = int(hsts.split('max-age=')[1].split(';')[0])
                    if max_age >= 31536000:  # 1 year
                        self.results.append(TestResult(
                            name="HSTS Header",
                            passed=True,
                            message=f"✅ HSTS properly configured: {hsts}",
                            severity="INFO"
                        ))
                    else:
                        self.results.append(TestResult(
                            name="HSTS Header",
                            passed=False,
                            message=f"⚠️  HSTS max-age too short: {max_age} seconds (recommended: 31536000)",
                            severity="WARNING",
                            recommendation="Set HSTS max-age to at least 31536000 (1 year)"
                        ))
                else:
                    self.results.append(TestResult(
                        name="HSTS Header",
                        passed=False,
                        message=f"⚠️  HSTS header present but invalid format: {hsts}",
                        severity="WARNING",
                        recommendation="Fix HSTS header format: 'max-age=31536000; includeSubDomains'"
                    ))
            else:
                self.results.append(TestResult(
                    name="HSTS Header",
                    passed=False,
                    message="⚠️  HSTS header not configured",
                    severity="WARNING",
                    recommendation="Add middleware to set Strict-Transport-Security header (see SECURITY_TESTING.md)"
                ))
        except Exception as e:
            self.results.append(TestResult(
                name="HSTS Header",
                passed=False,
                message=f"❌ Error checking HSTS: {str(e)}",
                severity="WARNING"
            ))
    
    def test_ssl_certificate(self):
        """Test: SSL certificate validity"""
        print("  🔍 Checking SSL certificate...")
        
        if not self.base_url.startswith("https://"):
            self.results.append(TestResult(
                name="SSL Certificate",
                passed=False,
                message="⚠️  Cannot check SSL certificate - HTTPS not enabled",
                severity="WARNING"
            ))
            return
        
        try:
            # Test dengan verify=True untuk check certificate
            response = requests.get(f"{self.base_url}/", verify=True, timeout=5)
            self.results.append(TestResult(
                name="SSL Certificate",
                passed=True,
                message="✅ SSL certificate is valid and trusted",
                severity="INFO"
            ))
        except requests.exceptions.SSLError as e:
            self.results.append(TestResult(
                name="SSL Certificate",
                passed=False,
                message=f"❌ SSL certificate error: {str(e)}",
                severity="CRITICAL",
                recommendation="Fix SSL certificate issues. For production, use valid certificate from trusted CA (e.g., Let's Encrypt)"
            ))
        except Exception as e:
            self.results.append(TestResult(
                name="SSL Certificate",
                passed=False,
                message=f"❌ Error checking SSL certificate: {str(e)}",
                severity="WARNING"
            ))
    
    def run_tests(self) -> List[TestResult]:
        """Jalankan semua HTTPS tests"""
        self.test_https_enabled()
        self.test_http_to_https_redirect()
        self.test_hsts_header()
        self.test_ssl_certificate()
        
        # Print summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print(f"\n  ✅ Passed: {passed}/{total}")
        
        return self.results
