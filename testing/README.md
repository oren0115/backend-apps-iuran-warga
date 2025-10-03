# 🔒 Security Testing Suite

Script untuk testing keamanan aplikasi sebelum production deployment.

## 📋 Test Coverage

### Test 1: HTTPS Configuration & SSL/TLS

- ✅ Memastikan aplikasi menggunakan HTTPS
- ✅ Check HTTP to HTTPS redirect
- ✅ Validasi HSTS header
- ✅ Validasi SSL certificate

### Test 2: Security Headers

- ✅ X-Content-Type-Options (MIME sniffing protection)
- ✅ X-Frame-Options (Clickjacking protection)
- ✅ X-XSS-Protection (XSS filter)
- ✅ Strict-Transport-Security (HSTS)
- ✅ CORS configuration check
- ✅ Content-Security-Policy (optional)

### Test 3: Rate Limiting

- ✅ Login endpoint rate limiting (brute force protection)
- ✅ Global API rate limiting
- ✅ Payment endpoint protection
- ✅ Retry-After header check

### Test 4: Webhook Security (Midtrans Payment)

- ✅ Webhook endpoint accessibility
- ✅ **CRITICAL**: Signature verification
- ✅ Amount validation (dari database)
- ✅ Idempotency handling
- ✅ Error handling

## 🚀 Cara Menggunakan

### 1. Install Dependencies

```bash
# Install Python requests library
pip install requests
```

### 2. Jalankan Security Tests

#### Test Local Development

```bash
cd c:\Users\ADMIN\Desktop\PKM\backend
python testing/run_security_tests.py http://localhost:8000
```

#### Test Staging Environment

```bash
python testing/run_security_tests.py https://your-staging-url.com
```

#### Test Production Environment

```bash
python testing/run_security_tests.py https://your-production-url.com
```

### 3. Membaca Results

Output akan menampilkan:

- ✅ **PASSED**: Test berhasil, tidak ada masalah
- ⚠️ **WARNING**: Issue yang sebaiknya diperbaiki (tidak critical)
- ❌ **CRITICAL**: Issue yang HARUS diperbaiki sebelum production

#### Contoh Output:

```
================================================================================
🔒 SECURITY TESTING SUITE - PRODUCTION READINESS CHECK
================================================================================
📍 Target URL: http://localhost:8000
⏰ Started at: 2025-10-03 23:30:00
================================================================================

📋 TEST 1/4: HTTPS Configuration & SSL/TLS
--------------------------------------------------------------------------------
  🔍 Checking HTTPS usage...
  🔍 Checking HTTP to HTTPS redirect...
  🔍 Checking HSTS header...
  🔍 Checking SSL certificate...

  ✅ Passed: 2/4

📋 TEST 2/4: Security Headers (XSS, Clickjacking Protection)
--------------------------------------------------------------------------------
  🔍 Checking security headers...
  🔍 Checking CORS configuration...
  🔍 Checking Content Security Policy...

  ✅ Passed: 5/8

📋 TEST 3/4: Rate Limiting & Abuse Prevention
--------------------------------------------------------------------------------
  🔍 Testing rate limit on login endpoint...
     (This may take a few seconds)
  🔍 Testing global API rate limit...
  🔍 Testing rate limit on payment endpoint...
  🔍 Checking Retry-After header configuration...

  ✅ Passed: 2/4

📋 TEST 4/4: Payment Webhook Security (Midtrans)
--------------------------------------------------------------------------------
  🔍 Checking webhook endpoint...
  🔍 Testing webhook signature verification...
  🔍 Checking webhook amount validation...
  🔍 Checking webhook idempotency...
  🔍 Checking webhook error handling...

  ✅ Passed: 4/5

================================================================================
📊 DETAILED TEST RESULTS
================================================================================

🚨 CRITICAL ISSUES (MUST FIX BEFORE PRODUCTION):
--------------------------------------------------------------------------------
1. HTTPS Protocol
   Status: ❌ FAILED
   Message: ❌ Application is NOT using HTTPS - HTTP detected
   Fix: Enable HTTPS/SSL certificate before production deployment. Use Let's Encrypt for free SSL certificates.

2. Webhook Signature Verification
   Status: ❌ FAILED
   Message: ❌ CRITICAL! Webhook accepts notification without valid signature!
   Fix: MUST implement signature verification! See SECURITY_TESTING.md for implementation

⚠️  WARNINGS (RECOMMENDED TO FIX):
--------------------------------------------------------------------------------
1. HSTS Header
   Status: ⚠️  WARNING
   Message: ⚠️  HSTS header not configured
   Fix: Add middleware to set Strict-Transport-Security header

2. Login Rate Limiting
   Status: ⚠️  WARNING
   Message: ⚠️  No rate limiting detected after 15 requests
   Fix: Implement rate limiting to prevent brute force attacks (5-10 requests/minute recommended)

================================================================================
📈 SUMMARY
================================================================================
Total Tests Run: 20
✅ Passed: 13 (65.0%)
❌ Failed: 7 (35.0%)
🚨 Critical Issues: 2
⚠️  Warnings: 5
⏰ Completed at: 2025-10-03 23:30:15
================================================================================

🚫 PRODUCTION DEPLOYMENT: NOT READY
   Fix all CRITICAL issues before deploying to production!
```

## 📝 Test Individual Modules

Jika ingin test modul tertentu saja:

```bash
# Test HTTPS configuration only
python -c "from testing.test_https_config import HTTPSConfigTester; t = HTTPSConfigTester('http://localhost:8000'); t.run_tests()"

# Test Security Headers only
python -c "from testing.test_security_headers import SecurityHeadersTester; t = SecurityHeadersTester('http://localhost:8000'); t.run_tests()"

# Test Rate Limiting only
python -c "from testing.test_rate_limiting import RateLimitingTester; t = RateLimitingTester('http://localhost:8000'); t.run_tests()"

# Test Webhook Security only
python -c "from testing.test_webhook_security import WebhookSecurityTester; t = WebhookSecurityTester('http://localhost:8000'); t.run_tests()"
```

## 🛠️ Fixing Critical Issues

### Issue 1: HTTPS Not Enabled

**Production deployment HARUS menggunakan HTTPS!**

**Solusi**:

1. Dapatkan SSL certificate (gratis dari Let's Encrypt)
2. Configure web server (nginx/Apache) untuk HTTPS
3. Enable HTTPS redirect di aplikasi

**Referensi**: Lihat `SECURITY_TESTING.md` section "HTTPS Configuration"

### Issue 2: Webhook Signature Verification Missing

**CRITICAL SECURITY ISSUE!** Tanpa signature verification, attacker bisa kirim fake payment notifications.

**Solusi**: Implement signature verification di `app/services/midtrans_service.py`

```python
def verify_signature(self, order_id: str, status_code: str,
                    gross_amount: str, server_key: str,
                    signature_key: str) -> bool:
    """Verify Midtrans signature"""
    import hashlib
    string_to_hash = f"{order_id}{status_code}{gross_amount}{server_key}"
    calculated_signature = hashlib.sha512(string_to_hash.encode()).hexdigest()
    return calculated_signature == signature_key
```

**Referensi**: Lihat `SECURITY_TESTING.md` section "Payment Security Testing"

### Issue 3: Rate Limiting Not Configured

**Untuk mencegah brute force dan abuse**

**Solusi**: Install slowapi dan configure rate limiting

```bash
pip install slowapi
```

**Referensi**: Lihat `SECURITY_TESTING.md` section "Rate Limiting & DDoS Protection"

### Issue 4: Security Headers Missing

**Untuk proteksi XSS, clickjacking, dll**

**Solusi**: Add middleware di `main.py`

**Referensi**: Lihat `SECURITY_TESTING.md` section "HTTP Security Headers"

## 📊 Interpretasi Exit Codes

Script akan return exit code untuk CI/CD integration:

- **Exit Code 0**: Semua tests passed ATAU hanya ada warnings (safe to deploy)
- **Exit Code 1**: Ada critical issues (DO NOT DEPLOY)

Contoh penggunaan di CI/CD:

```yaml
# GitHub Actions example
- name: Run Security Tests
  run: python testing/run_security_tests.py ${{ env.STAGING_URL }}
  # Will fail CI if critical issues found
```

## 🔄 Integrasi dengan CI/CD

### GitHub Actions

```yaml
name: Security Testing

on: [push, pull_request]

jobs:
  security-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.10"

      - name: Install Dependencies
        run: |
          pip install requests

      - name: Run Security Tests
        run: python testing/run_security_tests.py ${{ secrets.STAGING_URL }}
```

## 📚 Referensi Lengkap

Untuk dokumentasi security testing lengkap dan cara fix semua issues, lihat:

- `SECURITY_TESTING.md` - Full security testing documentation
- `app/services/midtrans_service.py` - Webhook implementation
- `main.py` - Security middleware configuration

## ⚠️ Important Notes

1. **Jangan skip critical issues!** Mereka ada karena alasan security yang sangat penting.

2. **Test di staging dulu** sebelum production deployment.

3. **Re-run tests** setelah fix issues untuk verify fixes.

4. **Regular testing**: Jalankan tests ini secara regular, tidak cuma sebelum deployment.

5. **Monitor production**: Setup monitoring untuk detect security issues di production.

## 🆘 Need Help?

Jika ada pertanyaan atau butuh bantuan fix security issues:

1. Baca dokumentasi di `SECURITY_TESTING.md`
2. Check implementasi referensi di masing-masing test file
3. Konsultasi dengan security expert jika necessary

---

**Last Updated**: October 2025  
**Version**: 1.0
