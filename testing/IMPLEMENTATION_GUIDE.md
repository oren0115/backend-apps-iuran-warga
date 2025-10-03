# 🔧 Implementation Guide - Security Fixes

Panduan implementasi untuk fix critical security issues yang ditemukan dari security testing.

## 🚨 Critical Issue #1: Webhook Signature Verification

### Problem

Webhook Midtrans menerima notification tanpa validasi signature, memungkinkan attacker mengirim fake payment notifications.

### Solution

#### Step 1: Update Midtrans Service

Tambahkan method signature verification di `app/services/midtrans_service.py`:

```python
import hashlib
from fastapi import HTTPException, status

class MidtransService:
    # ... existing code ...

    def verify_signature(self, order_id: str, status_code: str,
                        gross_amount: str, signature_key: str) -> bool:
        """
        Verify Midtrans notification signature

        Formula: SHA512(order_id + status_code + gross_amount + server_key)
        """
        # Create string to hash
        string_to_hash = f"{order_id}{status_code}{gross_amount}{self.config.server_key}"

        # Calculate SHA512 hash
        calculated_signature = hashlib.sha512(string_to_hash.encode()).hexdigest()

        # Compare with provided signature
        return calculated_signature == signature_key

    async def handle_notification(self, notification: MidtransNotificationRequest) -> dict:
        """Handle Midtrans payment notification with signature verification"""

        # STEP 1: VERIFY SIGNATURE (CRITICAL!)
        is_valid_signature = self.verify_signature(
            order_id=notification.order_id,
            status_code=notification.status_code,
            gross_amount=notification.gross_amount,
            signature_key=notification.signature_key
        )

        if not is_valid_signature:
            logger.warning(f"Invalid signature for order {notification.order_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        logger.info(f"✅ Signature verified for order {notification.order_id}")

        # STEP 2: Process notification (existing code)
        # ... rest of your existing implementation ...
```

#### Step 2: Ensure Model Has signature_key Field

Update `app/models/midtrans.py` jika belum ada field `signature_key`:

```python
class MidtransNotificationRequest(BaseModel):
    transaction_time: str
    transaction_status: str
    transaction_id: str
    status_message: str
    status_code: str
    signature_key: str  # ← Pastikan field ini ada!
    payment_type: str
    order_id: str
    merchant_id: Optional[str] = None
    gross_amount: str
    fraud_status: Optional[str] = None
    currency: Optional[str] = None
    # ... other fields ...
```

#### Step 3: Test Implementation

```bash
# Run webhook security test
python -c "from testing.test_webhook_security import WebhookSecurityTester; t = WebhookSecurityTester('http://localhost:8000'); t.run_tests()"
```

Expected result: `✅ EXCELLENT! Webhook rejects invalid signatures (401 Unauthorized)`

---

## 🚨 Critical Issue #2: Rate Limiting

### Problem

Tidak ada rate limiting, aplikasi rentan terhadap brute force dan abuse attacks.

### Solution

#### Step 1: Install SlowAPI

```bash
pip install slowapi
```

Update `requirements.txt`:

```
slowapi==0.1.9
```

#### Step 2: Configure Rate Limiter di `main.py`

```python
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create the main app
app = FastAPI(title="RT/RW Fee Management API")

# Configure rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/hour"]  # Global rate limit
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ... rest of your app configuration ...
```

#### Step 3: Add Rate Limiting to Login Endpoint

Update `app/routes/user_routes.py`:

```python
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
user_controller = UserController()

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(request: Request, login_data: UserLogin):
    """Login user and return access token"""
    return await user_controller.login_user(login_data)
```

#### Step 4: Add Rate Limiting to Payment Endpoint

Update `app/routes/payment_routes.py`:

```python
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
payment_controller = PaymentController()
limiter = Limiter(key_func=get_remote_address)

@router.post("/payments", response_model=PaymentCreateResponse)
@limiter.limit("10/minute")  # Max 10 payment creations per minute
async def create_payment(
    request: Request,
    payment_data: PaymentCreate,
    current_user=Depends(get_current_user)
):
    """Create a new payment using Midtrans"""
    return await payment_controller.create_payment(
        payment_data, current_user["id"], current_user
    )
```

#### Step 5: Test Rate Limiting

```bash
# Run rate limiting test
python -c "from testing.test_rate_limiting import RateLimitingTester; t = RateLimitingTester('http://localhost:8000'); t.run_tests()"
```

Expected result: `✅ Rate limiting enabled (triggered after X requests)`

---

## ⚠️ Warning Issue #3: Security Headers

### Problem

Missing HTTP security headers untuk proteksi dari XSS, clickjacking, dll.

### Solution

#### Add Security Headers Middleware di `main.py`

```python
from fastapi import FastAPI, Request
from starlette.middleware.trustedhost import TrustedHostMiddleware
import os

app = FastAPI(title="RT/RW Fee Management API")

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Enable XSS filter in older browsers
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Force HTTPS (only for production)
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response

# Add trusted host middleware for production
if os.getenv("ENVIRONMENT") == "production":
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
    if allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
```

#### Update `.env` file

```bash
ENVIRONMENT=production
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

#### Test Security Headers

```bash
# Run security headers test
python -c "from testing.test_security_headers import SecurityHeadersTester; t = SecurityHeadersTester('http://localhost:8000'); t.run_tests()"
```

---

## ⚠️ Warning Issue #4: CORS Configuration

### Problem

CORS configuration mungkin terlalu permissive untuk production.

### Solution

#### Update CORS Configuration di `main.py`

```python
import os
from starlette.middleware.cors import CORSMiddleware

# Get allowed origins from environment
environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    # Production: Only allow specific domains
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
else:
    # Development: Allow localhost
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Update `.env.production`

```bash
ENVIRONMENT=production
ALLOWED_ORIGINS=https://your-production-domain.com,https://www.your-production-domain.com
```

---

## 🔐 Bonus: Upgrade Password Hashing

### Problem

SHA256 kurang secure untuk password hashing. Bcrypt atau Argon2 lebih baik.

### Solution

#### Step 1: Install bcrypt

```bash
pip install bcrypt
```

#### Step 2: Update AuthManager di `app/utils/auth.py`

```python
import bcrypt
import hashlib

class AuthManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds is good balance
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            # Fallback untuk old SHA256 hashes (untuk backward compatibility)
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            return sha256_hash == hashed

    # ... rest of the code ...
```

**Note**: Untuk backward compatibility, verify_password mencoba bcrypt dulu, jika fail coba SHA256.

#### Step 3: Migrate Existing Passwords

Buat script migrasi `migrate_passwords.py`:

```python
"""
Migrate existing SHA256 passwords to bcrypt
Run once: python migrate_passwords.py
"""

import asyncio
from app.config.database import init_database, get_database, close_database
from app.utils.auth import AuthManager

async def migrate_passwords():
    await init_database()
    db = get_database()

    users = await db.users.find({}).to_list(1000)

    for user in users:
        # Check if password is SHA256 (64 chars hex)
        if len(user['password']) == 64:
            # Re-hash with bcrypt using the CURRENT password hash
            # User will need to re-enter password, or you can force password reset
            print(f"User {user['username']} needs password update")
            # Option: Force password reset on next login

    await close_database()

if __name__ == "__main__":
    asyncio.run(migrate_passwords())
```

---

## 📋 Implementation Checklist

Sebelum deploy ke production, pastikan:

- [ ] ✅ Webhook signature verification implemented
- [ ] ✅ Rate limiting configured (login: 5/min, payment: 10/min, global: 200/hour)
- [ ] ✅ Security headers middleware added
- [ ] ✅ CORS configured untuk production domains only
- [ ] ✅ HTTPS enabled (SSL certificate installed)
- [ ] ✅ Environment variables properly set
- [ ] ✅ Password hashing upgraded to bcrypt (optional)
- [ ] ✅ All security tests PASSED

## 🧪 Run All Tests After Implementation

```bash
# Full security test suite
python testing/run_security_tests.py https://your-staging-url.com

# Dependency check
python testing/check_dependencies.py

# Expected: All critical tests should PASS
```

---

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Midtrans Security Documentation](https://docs.midtrans.com/en/after-payment/http-notification)

---

**Last Updated**: October 2025  
**Version**: 1.0
