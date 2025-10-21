# RT/RW Fee Management System

Sistem manajemen IPL berbasis FastAPI untuk mengelola pembayaran iuran bulanan warga dengan integrasi payment gateway Midtrans dan notifikasi Telegram.

## 🚀 Fitur Utama

- **Manajemen User**: Registrasi, login, profil warga, dan manajemen user lengkap
- **Manajemen Iuran**: Generate iuran bulanan otomatis dengan jatuh tempo akhir bulan
- **Smart Regeneration**: Regenerate tagihan dengan mempertahankan history pembayaran
- **Sistem Pembayaran**: Integrasi Midtrans untuk pembayaran online (Credit Card, Bank Transfer, GoPay)
- **Notifikasi Real-time**: Sistem notifikasi WebSocket untuk pengumuman dan reminder
- **Notifikasi Telegram**: Broadcast notifikasi ke Telegram bot untuk semua warga
- **Dashboard Admin**: Statistik dan monitoring sistem lengkap
- **Export Laporan**: Export data iuran dan pembayaran ke Excel/PDF
- **Security**: JWT authentication, rate limiting, webhook security

## 🛠️ Teknologi

- **FastAPI** - Web framework modern untuk Python
- **MongoDB** - Database NoSQL dengan Motor (async driver)
- **Midtrans** - Payment gateway untuk pembayaran online
- **Telegram Bot API** - Notifikasi otomatis ke warga
- **WebSocket** - Real-time notifications
- **JWT** - Token-based authentication

## 📦 Instalasi

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment variables**
   Buat file `.env` di root directory:
   ```env
   MONGO_URL=mongodb://localhost:27017
   DB_NAME=rt_rw_management
   JWT_SECRET_KEY=your-secret-key-here
   JWT_ALGORITHM=HS256
   MIDTRANS_SERVER_KEY=your-midtrans-server-key
   MIDTRANS_CLIENT_KEY=your-midtrans-client-key
   MIDTRANS_IS_PRODUCTION=false
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
   TELEGRAM_CHAT_ID=your-telegram-chat-id-here
   TELEGRAM_WEBHOOK_URL=https://your-backend-domain.com/api/telegram/webhook
   TELEGRAM_SEND_INDIVIDUAL=true
   ```

4. **Jalankan aplikasi**
   ```bash
   python main.py
   ```
   Aplikasi akan berjalan di `http://localhost:8000`

## 📚 API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🏗️ Struktur Project

```
backend/
├── app/
│   ├── config/           # Konfigurasi database, Midtrans, Telegram
│   ├── controllers/      # Business logic untuk semua operasi
│   ├── models/          # Data models dan schemas
│   ├── routes/          # API endpoints
│   ├── services/        # External services (Midtrans, Telegram, WebSocket)
│   ├── middleware/      # CORS, security, rate limiting
│   └── security/        # Authentication, webhook security
├── script/              # Migration dan testing scripts
├── testing/             # Security testing dan tools
└── main.py             # Entry point aplikasi
```

## 🔐 API Endpoints

### User Endpoints
- `POST /api/register` - Registrasi user baru
- `POST /api/login` - Login user
- `GET /api/profile` - Get profil user (protected)

### Admin Endpoints
- `GET /api/admin/users` - Get semua users (admin only)
- `POST /api/admin/users` - Buat user baru (admin only)
- `PUT /api/admin/users/{user_id}` - Update user (admin only)
- `DELETE /api/admin/users/{user_id}` - Hapus user (admin only)
- `POST /api/admin/generate-fees` - Generate iuran bulanan (admin only)
- `POST /api/admin/regenerate-fees` - Regenerate iuran dengan preserve history (admin only)
- `GET /api/admin/fees` - Get semua iuran (admin only)
- `GET /api/admin/payments` - Get pending payments (admin only)
- `PUT /api/admin/payments/{id}/approve` - Approve pembayaran (admin only)
- `POST /api/admin/notifications/broadcast` - Broadcast notifikasi (admin only)
- `GET /api/admin/dashboard` - Get dashboard stats (admin only)

### Fee Endpoints
- `GET /api/fees` - Get iuran user (hanya versi terbaru)

### Payment Endpoints
- `GET /api/payments` - Get riwayat pembayaran user (protected)
- `POST /api/payments/create` - Buat pembayaran via Midtrans (protected)
- `POST /api/payments/notification` - Webhook Midtrans untuk update status

### Notification Endpoints
- `GET /api/notifications` - Get notifikasi user (protected)
- `PUT /api/notifications/{id}/read` - Mark notifikasi sebagai dibaca (protected)

## 🗄️ Database Schema

### Collections

**users**
```json
{
  "id": "string",
  "username": "string",
  "nama": "string",
  "alamat": "string",
  "nomor_rumah": "string",
  "nomor_hp": "string",
  "tipe_rumah": "string",
  "telegram_chat_id": "string",
  "password": "hashed_string",
  "is_admin": "boolean",
  "created_at": "datetime"
}
```

**fees**
```json
{
  "id": "string",
  "user_id": "string",
  "kategori": "string",
  "nominal": "integer",
  "bulan": "string",
  "status": "string",
  "due_date": "datetime",
  "created_at": "datetime",
  "version": "integer",
  "regenerated_at": "datetime",
  "regenerated_reason": "string",
  "parent_fee_id": "string",
  "is_regenerated": "boolean"
}
```

**payments**
```json
{
  "id": "string",
  "fee_id": "string",
  "user_id": "string",
  "amount": "integer",
  "payment_method": "string",
  "status": "string",
  "created_at": "datetime",
  "transaction_id": "string",
  "payment_url": "string",
  "expiry_time": "datetime",
  "settled_at": "datetime"
}
```

## 🆕 Fitur Terbaru

### 1. Smart Fee Regeneration
- **Preserve Payment History**: Tagihan yang sudah dibayar tidak hilang saat regenerate
- **Version Control**: Track perubahan tagihan dengan versioning system
- **Audit Trail**: Log lengkap untuk semua regenerasi
- **Rollback Capability**: Bisa membatalkan regenerasi jika diperlukan

### 2. Due Date Fix
- **End of Month**: Jatuh tempo selalu pada akhir bulan
- **Accurate Display**: Due date ditampilkan sesuai database
- **Leap Year Support**: Otomatis handle tahun kabisat

### 3. Home Page Optimization
- **Latest Fees Only**: Hanya menampilkan tagihan terbaru
- **No Duplicates**: Tidak ada duplikasi tagihan regenerated
- **Clean Interface**: Interface yang bersih dan mudah dipahami

### 4. Enhanced Security
- **Rate Limiting**: Protection against brute force attacks
- **Webhook Security**: Signature verification untuk Midtrans
- **Security Headers**: XSS, clickjacking protection
- **CORS Configuration**: Proper cross-origin setup

## 🔒 Security Testing

**PENTING**: Jalankan security testing sebelum deploy ke production!

```bash
# Quick security check
python testing/demo_security_test.py http://localhost:8000

# Comprehensive security testing
python testing/run_security_tests.py http://localhost:8000
```

## 🚀 Deployment

### Development
```bash
python main.py
```

### Production
```bash
# 1. Run security tests
python testing/run_security_tests.py https://your-staging-url.com

# 2. Setup Telegram webhook
python script/setup_telegram_webhook.py

# 3. Deploy
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📝 Usage Examples

### 1. Generate Iuran Bulanan (Admin)
```bash
curl -X POST "http://localhost:8000/api/admin/generate-fees" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bulan": "2024-01",
    "tarif_60m2": 50000,
    "tarif_72m2": 75000,
    "tarif_hook": 100000
  }'
```

### 2. Regenerate Iuran (Admin)
```bash
curl -X POST "http://localhost:8000/api/admin/regenerate-fees" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bulan": "2024-01",
    "tarif_60m2": 60000,
    "tarif_72m2": 80000,
    "tarif_hook": 120000
  }'
```

### 3. Buat Pembayaran
```bash
curl -X POST "http://localhost:8000/api/payments/create" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fee_id": "fee_123456",
    "payment_method": "credit_card"
  }'
```

## 🔧 Migration & Testing

### Database Migration
```bash
# Migrate existing data untuk fitur baru
python script/migrate_fee_schema.py

# Test regenerate system
python script/test_regenerate_system.py

# Test due date fix
python script/test_due_date_fix.py
```

### Cleanup Test Data
```bash
# Cleanup test data
python script/test_regenerate_system.py --cleanup
python script/test_due_date_fix.py --cleanup
```

## 🤖 Telegram Bot Integration

1. **Buat Bot di Telegram** - Chat dengan [@BotFather](https://t.me/botfather)
2. **Konfigurasi Environment** - Set `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID`
3. **Setup Webhook** - `python script/setup_telegram_webhook.py`

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Pastikan MongoDB sudah berjalan
   - Periksa `MONGO_URL` di file `.env`

2. **JWT Token Error**
   - Periksa `JWT_SECRET_KEY` di file `.env`
   - Restart aplikasi setelah mengubah secret key

3. **Midtrans Integration Error**
   - Periksa `MIDTRANS_SERVER_KEY` dan `MIDTRANS_CLIENT_KEY`
   - Pastikan mode production/sandbox sudah benar

4. **Telegram Integration Error**
   - Periksa `TELEGRAM_BOT_TOKEN` di file `.env`
   - Pastikan webhook URL sudah dikonfigurasi

## 📞 Support

Untuk pertanyaan atau bantuan, silakan buat issue di repository ini.

---

**Dibuat dengan ❤️ untuk memudahkan manajemen iuran RT/RW dengan fitur regenerasi cerdas dan notifikasi Telegram**