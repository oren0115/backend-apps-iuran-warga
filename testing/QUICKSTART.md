# ⚡ Quick Start - Security Testing

Panduan cepat untuk menjalankan security testing sebelum production deployment.

## 🎯 Tiga Langkah Mudah

### 1️⃣ Install Dependencies

```bash
pip install requests
```

### 2️⃣ Jalankan Quick Test

```bash
# Windows
quick_test.bat http://localhost:8000

# Linux/Mac
chmod +x quick_test.sh
./quick_test.sh http://localhost:8000

# Atau manual:
python testing/demo_security_test.py http://localhost:8000
```

### 3️⃣ Fix Critical Issues

Jika ada critical issues:

1. Baca `testing/IMPLEMENTATION_GUIDE.md`
2. Fix issues satu per satu
3. Re-run tests

## 📊 File-file Testing

| File                    | Fungsi                              |
| ----------------------- | ----------------------------------- |
| `demo_security_test.py` | Quick security check (5 menit)      |
| `run_security_tests.py` | Comprehensive testing (10-15 menit) |
| `check_dependencies.py` | Check vulnerability di dependencies |
| `quick_test.bat`        | Windows quick launcher              |
| `quick_test.sh`         | Linux/Mac quick launcher            |

## 📋 Individual Tests

```bash
# Test 1: HTTPS Configuration
python -c "from testing.test_https_config import HTTPSConfigTester; t = HTTPSConfigTester('http://localhost:8000'); t.run_tests()"

# Test 2: Security Headers
python -c "from testing.test_security_headers import SecurityHeadersTester; t = SecurityHeadersTester('http://localhost:8000'); t.run_tests()"

# Test 3: Rate Limiting
python -c "from testing.test_rate_limiting import RateLimitingTester; t = RateLimitingTester('http://localhost:8000'); t.run_tests()"

# Test 4: Webhook Security
python -c "from testing.test_webhook_security import WebhookSecurityTester; t = WebhookSecurityTester('http://localhost:8000'); t.run_tests()"
```

## ✅ Expected Output (All Pass)

```
================================================================================
🔒 QUICK SECURITY ASSESSMENT
================================================================================
Target: http://localhost:8000
Time: 2025-10-03 23:30:00

1️⃣  Checking HTTPS...
   ✅ PASS: Application uses HTTPS

2️⃣  Checking endpoint protection...
   ✅ PASS: Protected endpoints require authentication

3️⃣  Checking security headers...
   ✅ X-Content-Type-Options: nosniff
   ✅ X-Frame-Options: DENY

4️⃣  Checking CORS configuration...
   ✅ CORS configured

5️⃣  Checking webhook security...
   ✅ PASS: Webhook rejects invalid signatures

================================================================================
📊 SUMMARY
================================================================================

✅ Passed Checks: 5
   ✅ Using HTTPS
   ✅ Endpoints protected
   ✅ Security headers configured
   ✅ CORS configured
   ✅ Webhook signature verification enabled

================================================================================
✅ VERDICT: READY FOR PRODUCTION
   All basic security checks passed!
```

## 🚨 Common Issues & Quick Fixes

### Issue: "Application is NOT using HTTPS"

**Quick Fix (Development)**:

- Untuk development, ini OK
- Untuk production, HARUS pakai HTTPS!

**Quick Fix (Production)**:

```bash
# Get free SSL certificate dari Let's Encrypt
# Configure nginx/Apache untuk HTTPS
# Enable HTTPS redirect
```

### Issue: "Webhook accepts invalid signatures"

**Quick Fix**:

```python
# Add to app/services/midtrans_service.py
import hashlib

def verify_signature(self, order_id, status_code, gross_amount, signature_key):
    string_to_hash = f"{order_id}{status_code}{gross_amount}{self.config.server_key}"
    calculated = hashlib.sha512(string_to_hash.encode()).hexdigest()
    return calculated == signature_key

# Use in handle_notification:
if not self.verify_signature(...):
    raise HTTPException(status_code=401, detail="Invalid signature")
```

### Issue: "No rate limiting detected"

**Quick Fix**:

```bash
pip install slowapi
```

```python
# Add to main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

### Issue: "Security headers missing"

**Quick Fix**:

```python
# Add to main.py
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
```

## 📚 Dokumentasi Lengkap

- **`README.md`** - Panduan lengkap testing suite
- **`IMPLEMENTATION_GUIDE.md`** - Step-by-step fix issues
- **`../readme.md`** - Main project documentation

## 🆘 Need Help?

1. Read `IMPLEMENTATION_GUIDE.md` untuk detail implementation
2. Check individual test files untuk examples
3. Run tests dengan `-v` untuk verbose output

## 🔄 Integration dengan CI/CD

```yaml
# .github/workflows/security-test.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.10"
      - name: Install deps
        run: pip install requests
      - name: Run security tests
        run: python testing/run_security_tests.py ${{ secrets.STAGING_URL }}
```

---

**Last Updated**: October 2025
