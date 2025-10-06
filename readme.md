# RT/RW Fee Management System

Sistem manajemen IPL berbasis FastAPI untuk mengelola pembayaran iuran bulanan warga dengan integrasi payment gateway Midtrans dan notifikasi Telegram.

## 🚀 Fitur Utama

- **Manajemen User**: Registrasi, login, profil warga, dan manajemen user lengkap
- **Manajemen Iuran**: Generate iuran bulanan otomatis untuk semua warga
- **Sistem Pembayaran**: Integrasi Midtrans untuk pembayaran online (Credit Card, Bank Transfer, GoPay)
- **Notifikasi Real-time**: Sistem notifikasi WebSocket untuk pengumuman dan reminder
- **Notifikasi Telegram**: Broadcast notifikasi ke Telegram bot untuk semua warga
- **Dashboard Admin**: Statistik dan monitoring sistem lengkap
- **Export Laporan**: Export data iuran dan pembayaran ke Excel/PDF
- **Autentikasi JWT**: Keamanan dengan token-based authentication
- **Webhook Midtrans**: Otomatis update status pembayaran
- **User Management**: CRUD lengkap untuk manajemen user (Create, Read, Update, Delete)
- **Telegram Integration**: Bot Telegram untuk notifikasi otomatis ke warga

## 🛠️ Teknologi yang Digunakan

- **FastAPI** - Web framework modern untuk Python
- **MongoDB** - Database NoSQL dengan Motor (async driver)
- **Pydantic** - Data validation dan serialization
- **JWT** - JSON Web Token untuk autentikasi
- **Uvicorn** - ASGI server untuk production
- **Midtrans** - Payment gateway untuk pembayaran online
- **Telegram Bot API** - Notifikasi otomatis ke warga
- **WebSocket** - Real-time notifications
- **Pandas** - Data processing untuk export laporan
- **ReportLab** - PDF generation
- **XlsxWriter** - Excel export
- **OpenPyXL** - Excel file handling
- **PyJWT** - JWT token handling
- **Python-dotenv** - Environment variable management
- **Pyngrok** - Ngrok integration for development

## 📋 Prerequisites

- Python 3.8+
- MongoDB 4.0+
- pip (Python package manager)
- Telegram Bot Token (untuk notifikasi)

## 📦 Dependencies

### Core Dependencies

- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `motor==3.3.2` - Async MongoDB driver
- `pymongo==4.6.0` - MongoDB driver
- `pydantic==2.9.2` - Data validation
- `PyJWT==2.8.0` - JWT token handling
- `python-dotenv==1.0.0` - Environment variables

### Payment & External Services

- `midtransclient==1.4.2` - Midtrans payment gateway
- `pyngrok==7.3.0` - Ngrok integration
- `python-telegram-bot==20.7` - Telegram Bot API
- `aiohttp==3.9.1` - HTTP client untuk Telegram

### Data Processing & Export

- `pandas==2.2.3` - Data manipulation
- `XlsxWriter==3.2.0` - Excel export
- `openpyxl==3.1.2` - Excel file handling
- `reportlab==4.2.2` - PDF generation

### Real-time & Notifications

- `websockets==12.0` - WebSocket support
- `slowapi==0.1.9` - Rate limiting

### Framework Dependencies

- `starlette==0.27.0` - ASGI framework (FastAPI dependency)

## 🔧 Instalasi

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

   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
   TELEGRAM_CHAT_ID=your-telegram-chat-id-here
   TELEGRAM_WEBHOOK_URL=https://your-backend-domain.com/api/telegram/webhook
   TELEGRAM_SEND_INDIVIDUAL=true
   ```

4. **Setup Telegram Bot** (Opsional)

   ```bash
   # Setup webhook untuk Telegram bot
   python setup_telegram_webhook.py
   ```

5. **Jalankan aplikasi**

   ```bash
   python main.py
   ```

   Aplikasi akan berjalan di `http://localhost:8000`

## 📚 API Documentation

Setelah aplikasi berjalan, dokumentasi API dapat diakses di:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🏗️ Struktur Project

```
backend/
├── app/
│   ├── config/
│   │   ├── database.py          # Konfigurasi database MongoDB
│   │   ├── midtrans.py          # Konfigurasi Midtrans payment gateway
│   │   └── telegram.py          # Konfigurasi Telegram bot
│   ├── controllers/
│   │   ├── admin_controller.py  # Logic untuk admin operations
│   │   ├── fee_controller.py    # Logic untuk manajemen iuran
│   │   ├── notification_controller.py  # Logic untuk notifikasi
│   │   ├── payment_controller.py       # Logic untuk pembayaran
│   │   └── user_controller.py          # Logic untuk user operations
│   ├── models/
│   │   ├── user.py              # User models dan schemas
│   │   ├── fee.py               # Fee models dan schemas
│   │   ├── payment.py           # Payment models dan schemas
│   │   ├── notification.py      # Notification models dan schemas
│   │   └── response.py          # Response models
│   ├── routes/
│   │   ├── admin_routes.py      # API endpoints untuk admin
│   │   ├── fee_routes.py        # API endpoints untuk iuran
│   │   ├── notification_routes.py  # API endpoints untuk notifikasi
│   │   ├── payment_routes.py    # API endpoints untuk pembayaran
│   │   ├── user_routes.py       # API endpoints untuk user
│   │   ├── telegram_routes.py   # API endpoints untuk Telegram webhook
│   │   └── websocket_routes.py  # WebSocket endpoints
│   ├── services/
│   │   ├── midtrans_service.py  # Service untuk integrasi Midtrans
│   │   ├── telegram_service.py  # Service untuk integrasi Telegram
│   │   └── websocket_manager.py # WebSocket manager
│   └── utils/
│       ├── auth.py              # Utility untuk autentikasi JWT
│       └── webhook_security.py  # Utility untuk webhook security
├── main.py                      # Entry point aplikasi
├── requirements.txt             # Dependencies
├── setup_telegram_webhook.py   # Script setup Telegram webhook
├── debug_telegram.py           # Script debug Telegram integration
├── test_telegram_integration.py # Script test Telegram
├── TELEGRAM_SETUP.md           # Panduan setup Telegram
├── TELEGRAM_INDIVIDUAL_SETUP.md # Panduan setup individual notifications
├── TROUBLESHOOTING_TELEGRAM.md # Panduan troubleshooting Telegram
├── DEVELOPMENT_SETUP.md        # Panduan development dengan Ngrok
├── TESTING_GUIDE.md            # Panduan testing lengkap
└── readme.md                   # Dokumentasi project
```

## 🔐 API Endpoints

### User Endpoints

- `POST /api/register` - Registrasi user baru
- `POST /api/login` - Login user
- `GET /api/profile` - Get profil user (protected)
- `PUT /api/toggle-admin` - Toggle status admin (testing)

### Admin Endpoints

- `GET /api/admin/users` - Get semua users (admin only)
- `POST /api/admin/users` - Buat user baru (admin only)
- `PUT /api/admin/users/{user_id}` - Update user (admin only)
- `DELETE /api/admin/users/{user_id}` - Hapus user (admin only)
- `PATCH /api/admin/users/{user_id}/promote` - Promote user ke admin (admin only)
- `PATCH /api/admin/users/{user_id}/demote` - Demote admin ke user (admin only)
- `PATCH /api/admin/users/{user_id}/activate-telegram` - Aktifkan notifikasi Telegram (admin only)
- `PATCH /api/admin/users/{user_id}/deactivate-telegram` - Nonaktifkan notifikasi Telegram (admin only)
- `GET /api/admin/users/with-phone` - Get users dengan nomor HP (admin only)
- `GET /api/admin/users/telegram-status` - Get status Telegram users (admin only)
- `POST /api/admin/generate-fees` - Generate iuran bulanan (admin only)
- `GET /api/admin/fees` - Get semua iuran (admin only)
- `GET /api/admin/payments` - Get pending payments (admin only)
- `PUT /api/admin/payments/{id}/approve` - Approve pembayaran (admin only)
- `PUT /api/admin/payments/{id}/reject` - Reject pembayaran (admin only)
- `POST /api/admin/notifications/broadcast` - Broadcast notifikasi (admin only)
- `GET /api/admin/telegram/test` - Test koneksi Telegram (admin only)
- `GET /api/admin/dashboard` - Get dashboard stats (admin only)
- `POST /api/admin/init-sample-data` - Initialize sample data
- `GET /api/admin/reports/fees/export` - Export laporan iuran ke Excel/PDF (admin only)
- `GET /api/admin/reports/payments/export` - Export laporan pembayaran ke Excel/PDF (admin only)

### Fee Endpoints

- `GET /api/fees` - Get iuran user (protected)
- `POST /api/fees/pay` - Bayar iuran (protected)

### Payment Endpoints

- `GET /api/payments` - Get riwayat pembayaran user (protected)
- `POST /api/payments/create` - Buat pembayaran via Midtrans (protected)
- `POST /api/payments/notification` - Webhook Midtrans untuk update status
- `GET /api/payments/status/{order_id}` - Cek status pembayaran (protected)

### Notification Endpoints

- `GET /api/notifications` - Get notifikasi user (protected)
- `PUT /api/notifications/{id}/read` - Mark notifikasi sebagai dibaca (protected)

### Telegram Endpoints

- `POST /api/telegram/webhook` - Webhook untuk menerima pesan dari Telegram bot

### WebSocket Endpoints

- `WS /ws/{user_id}` - WebSocket connection untuk real-time notifications

## 🗄️ Database Schema

### Collections

**users**

```json
{
  "_id": "uuid",
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
  "_id": "uuid",
  "id": "string",
  "user_id": "string",
  "kategori": "string",
  "nominal": "integer",
  "bulan": "string",
  "status": "string",
  "due_date": "datetime",
  "created_at": "datetime"
}
```

**payments**

```json
{
  "_id": "uuid",
  "id": "string",
  "fee_id": "string",
  "user_id": "string",
  "order_id": "string",
  "transaction_id": "string",
  "amount": "integer",
  "payment_method": "string",
  "status": "string",
  "midtrans_status": "string",
  "payment_type": "string",
  "bank": "string",
  "va_number": "string",
  "payment_token": "string",
  "payment_url": "string",
  "expiry_time": "datetime",
  "settled_at": "datetime",
  "created_at": "datetime"
}
```

**notifications**

```json
{
  "_id": "uuid",
  "id": "string",
  "user_id": "string",
  "title": "string",
  "message": "string",
  "type": "string",
  "is_read": "boolean",
  "created_at": "datetime"
}
```

## 🤖 Telegram Bot Integration

### Setup Telegram Bot

1. **Buat Bot di Telegram**

   - Chat dengan [@BotFather](https://t.me/botfather)
   - Kirim `/newbot` dan ikuti instruksi
   - Simpan bot token yang diberikan

2. **Konfigurasi Environment**

   ```env
   TELEGRAM_BOT_TOKEN=your-bot-token-here
   TELEGRAM_CHAT_ID=your-admin-chat-id-here
   TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/telegram/webhook
   TELEGRAM_SEND_INDIVIDUAL=true
   ```

3. **Setup Webhook**
   ```bash
   python setup_telegram_webhook.py
   ```

### Cara Kerja Telegram Bot

1. **User mengirim `/start` ke bot**
2. **Bot mencari user berdasarkan:**
   - Username (prioritas 1)
   - Nama lengkap (prioritas 2)
   - Nomor HP (prioritas 3)
3. **Jika ditemukan:** Notifikasi Telegram aktif
4. **Jika tidak ditemukan:** Bot minta nomor HP
5. **Admin bisa aktifkan manual** via API endpoint

### Admin Manual Activation

```bash
# Aktifkan notifikasi Telegram untuk user
curl -X PATCH "http://localhost:8000/api/admin/users/{user_id}/activate-telegram?telegram_chat_id=123456789" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Nonaktifkan notifikasi Telegram
curl -X PATCH "http://localhost:8000/api/admin/users/{user_id}/deactivate-telegram" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🔒 Security Testing

**PENTING**: Sebelum deploy ke production, jalankan security testing untuk memastikan aplikasi aman!

### Quick Security Check

```bash
# Quick security assessment
python testing/demo_security_test.py http://localhost:8000

# Comprehensive security testing
python testing/run_security_tests.py http://localhost:8000

# Check dependencies vulnerabilities
python testing/check_dependencies.py
```

### Security Test Coverage

✅ **HTTPS Configuration & SSL/TLS**
✅ **Security Headers** (XSS, Clickjacking Protection)
✅ **Rate Limiting** (Brute Force Prevention)
✅ **Webhook Security** (Midtrans Signature Verification)
✅ **CORS Configuration**
✅ **Dependency Vulnerabilities**

### Dokumentasi Lengkap

- **`testing/README.md`** - Panduan lengkap security testing
- **`testing/IMPLEMENTATION_GUIDE.md`** - Cara fix security issues
- **`SECURITY_TESTING.md`** - Security best practices (coming soon)

### Production Readiness Checklist

Sebelum deploy ke production:

- [ ] ✅ Semua security tests PASSED
- [ ] ✅ HTTPS enabled dengan valid SSL certificate
- [ ] ✅ Rate limiting configured
- [ ] ✅ Webhook signature verification implemented
- [ ] ✅ Security headers configured
- [ ] ✅ Environment variables properly set
- [ ] ✅ No known dependency vulnerabilities
- [ ] ✅ Telegram bot webhook configured
- [ ] ✅ Database backup strategy implemented

## 🚀 Deployment

### Development

```bash
python main.py
```

### Production

**⚠️ SEBELUM DEPLOY**: Jalankan security testing!

```bash
# 1. Run security tests
python testing/run_security_tests.py https://your-staging-url.com

# 2. Fix critical issues (lihat testing/IMPLEMENTATION_GUIDE.md)

# 3. Setup Telegram webhook
python setup_telegram_webhook.py

# 4. Deploy
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Render Deployment

**Build Command:**

```bash
pip install --upgrade pip && pip install -r requirements.txt
```

**Start Command:**

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 🔒 Environment Variables

| Variable                   | Description                   | Default                     |
| -------------------------- | ----------------------------- | --------------------------- |
| `MONGO_URL`                | MongoDB connection string     | `mongodb://localhost:27017` |
| `DB_NAME`                  | Database name                 | `rt_rw_management`          |
| `JWT_SECRET_KEY`           | Secret key for JWT            | Required                    |
| `JWT_ALGORITHM`            | JWT algorithm                 | `HS256`                     |
| `MIDTRANS_SERVER_KEY`      | Midtrans server key           | Required                    |
| `MIDTRANS_CLIENT_KEY`      | Midtrans client key           | Required                    |
| `MIDTRANS_IS_PRODUCTION`   | Midtrans production mode      | `false`                     |
| `TELEGRAM_BOT_TOKEN`       | Telegram bot token            | Required                    |
| `TELEGRAM_CHAT_ID`         | Admin chat ID                 | Required                    |
| `TELEGRAM_WEBHOOK_URL`     | Webhook URL                   | Required                    |
| `TELEGRAM_SEND_INDIVIDUAL` | Send individual notifications | `true`                      |

## 📝 Usage Examples

### 1. Registrasi User Baru

```bash
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "warga001",
    "nama": "John Doe",
    "alamat": "Jl. Contoh No. 123",
    "nomor_rumah": "123",
    "nomor_hp": "08123456789",
    "tipe_rumah": "60M2",
    "password": "password123"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "warga001",
    "password": "password123"
  }'
```

### 3. Generate Iuran Bulanan (Admin)

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

### 4. Buat Pembayaran via Midtrans

```bash
curl -X POST "http://localhost:8000/api/payments/create" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fee_id": "fee_123456",
    "payment_method": "credit_card"
  }'
```

### 5. Broadcast Notifikasi (Admin)

```bash
curl -X POST "http://localhost:8000/api/admin/notifications/broadcast" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Pengumuman Penting",
    "message": "Ada rapat RT pada hari Minggu",
    "notification_type": "pengumuman"
  }'
```

### 6. Export Laporan Iuran (Admin)

```bash
curl -X GET "http://localhost:8000/api/admin/reports/fees/export?bulan=2024-01&format=excel" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o "laporan_iuran_2024-01.xlsx"
```

### 7. Aktifkan Notifikasi Telegram (Admin)

```bash
curl -X PATCH "http://localhost:8000/api/admin/users/warga001/activate-telegram?telegram_chat_id=123456789" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 8. Test Koneksi Telegram (Admin)

```bash
curl -X GET "http://localhost:8000/api/admin/telegram/test" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Error**

   - Pastikan MongoDB sudah berjalan
   - Periksa koneksi string di file `.env`
   - Pastikan database name sudah benar

2. **JWT Token Error**

   - Periksa `JWT_SECRET_KEY` di file `.env`
   - Pastikan token tidak expired
   - Restart aplikasi setelah mengubah secret key

3. **Midtrans Integration Error**

   - Periksa `MIDTRANS_SERVER_KEY` dan `MIDTRANS_CLIENT_KEY`
   - Pastikan mode production/sandbox sudah benar
   - Periksa webhook URL configuration

4. **Telegram Integration Error**

   - Periksa `TELEGRAM_BOT_TOKEN` di file `.env`
   - Pastikan webhook URL sudah dikonfigurasi
   - Periksa koneksi internet untuk webhook
   - Lihat `TROUBLESHOOTING_TELEGRAM.md` untuk panduan lengkap

5. **Import/Export Error**
   - Pastikan semua dependencies sudah terinstall
   - Periksa permission untuk menulis file
   - Pastikan format data sudah benar

### Development Tips

- Gunakan `uvicorn main:app --reload` untuk auto-reload
- Periksa logs di terminal untuk debugging
- Gunakan MongoDB Compass untuk melihat data
- Test API endpoints menggunakan Swagger UI
- Gunakan `debug_telegram.py` untuk debug Telegram integration
- Test webhook dengan `test_webhook.py`

## 📞 Support

Untuk pertanyaan atau bantuan, silakan buat issue di repository ini.

---

**Dibuat dengan ❤️ untuk memudahkan manajemen iuran RT/RW dengan notifikasi Telegram**
