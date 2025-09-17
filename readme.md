# RT/RW Fee Management System

Sistem manajemen iuran RT/RW berbasis FastAPI untuk mengelola pembayaran iuran bulanan warga.

## 🚀 Fitur Utama

- **Manajemen User**: Registrasi, login, dan profil warga
- **Manajemen Iuran**: Generate iuran bulanan otomatis untuk semua warga
- **Sistem Pembayaran**: Upload bukti transfer dan approval pembayaran
- **Notifikasi**: Sistem notifikasi untuk pengumuman dan reminder
- **Dashboard Admin**: Statistik dan monitoring sistem
- **Autentikasi JWT**: Keamanan dengan token-based authentication

## 🛠️ Teknologi yang Digunakan

- **FastAPI** - Web framework modern untuk Python
- **MongoDB** - Database NoSQL dengan Motor (async driver)
- **Pydantic** - Data validation dan serialization
- **JWT** - JSON Web Token untuk autentikasi
- **Uvicorn** - ASGI server untuk production

## 📋 Prerequisites

- Python 3.8+
- MongoDB 4.0+
- pip (Python package manager)

## 🔧 Instalasi

1. **Clone repository**

   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirement.txt
   ```

3. **Setup environment variables**
   Buat file `.env` di root directory:

   ```env
   MONGO_URL=mongodb://localhost:27017
   DB_NAME=rt_rw_management
   JWT_SECRET_KEY=your-secret-key-here
   JWT_ALGORITHM=HS256
   ```

4. **Jalankan aplikasi**

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
│   │   └── database.py          # Konfigurasi database MongoDB
│   ├── controllers/
│   │   ├── admin_controller.py  # Logic untuk admin operations
│   │   ├── fee_controller.py    # Logic untuk manajemen iuran
│   │   ├── notification_controller.py  # Logic untuk notifikasi
│   │   ├── payment_controller.py       # Logic untuk pembayaran
│   │   └── user_controller.py          # Logic untuk user operations
│   ├── models/
│   │   └── schemas.py           # Pydantic models untuk data validation
│   ├── routes/
│   │   ├── admin_routes.py      # API endpoints untuk admin
│   │   ├── fee_routes.py        # API endpoints untuk iuran
│   │   ├── notification_routes.py  # API endpoints untuk notifikasi
│   │   ├── payment_routes.py    # API endpoints untuk pembayaran
│   │   └── user_routes.py       # API endpoints untuk user
│   └── utils/
│       └── auth.py              # Utility untuk autentikasi JWT
├── main.py                      # Entry point aplikasi
├── requirement.txt              # Dependencies
└── readme.md                    # Dokumentasi project
```

## 🔐 API Endpoints

### User Endpoints

- `POST /api/register` - Registrasi user baru
- `POST /api/login` - Login user
- `GET /api/profile` - Get profil user (protected)
- `PUT /api/toggle-admin` - Toggle status admin (testing)

### Admin Endpoints

- `GET /api/admin/users` - Get semua users (admin only)
- `POST /api/admin/generate-fees` - Generate iuran bulanan (admin only)
- `GET /api/admin/fees` - Get semua iuran (admin only)
- `GET /api/admin/payments` - Get pending payments (admin only)
- `PUT /api/admin/payments/{id}/approve` - Approve pembayaran (admin only)
- `PUT /api/admin/payments/{id}/reject` - Reject pembayaran (admin only)
- `POST /api/admin/notifications/broadcast` - Broadcast notifikasi (admin only)
- `GET /api/admin/dashboard` - Get dashboard stats (admin only)
- `POST /api/admin/init-sample-data` - Initialize sample data

### Fee Endpoints

- `GET /api/fees` - Get iuran user (protected)
- `POST /api/fees/pay` - Bayar iuran (protected)

### Payment Endpoints

- `GET /api/payments` - Get riwayat pembayaran user (protected)
- `POST /api/payments` - Upload bukti pembayaran (protected)

### Notification Endpoints

- `GET /api/notifications` - Get notifikasi user (protected)
- `PUT /api/notifications/{id}/read` - Mark notifikasi sebagai dibaca (protected)

## 🗄️ Database Schema

### Collections

**users**

```json
{
  "_id": "uuid",
  "username": "string",
  "nama": "string",
  "alamat": "string",
  "nomor_rumah": "string",
  "nomor_hp": "string",
  "password": "hashed_string",
  "is_admin": "boolean",
  "created_at": "datetime"
}
```

**fees**

```json
{
  "_id": "uuid",
  "user_id": "uuid",
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
  "fee_id": "uuid",
  "user_id": "uuid",
  "amount": "integer",
  "method": "string",
  "bukti_transfer": "string",
  "status": "string",
  "created_at": "datetime",
  "approved_at": "datetime",
  "approved_by": "uuid"
}
```

**notifications**

```json
{
  "_id": "uuid",
  "user_id": "uuid",
  "title": "string",
  "message": "string",
  "type": "string",
  "is_read": "boolean",
  "created_at": "datetime"
}
```

## 🚀 Deployment

### Development

```bash
python main.py
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔒 Environment Variables

| Variable         | Description               | Default                     |
| ---------------- | ------------------------- | --------------------------- |
| `MONGO_URL`      | MongoDB connection string | `mongodb://localhost:27017` |
| `DB_NAME`        | Database name             | `rt_rw_management`          |
| `JWT_SECRET_KEY` | Secret key for JWT        | Required                    |
| `JWT_ALGORITHM`  | JWT algorithm             | `HS256`                     |

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
    "bulan": "2024-01"
  }'
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

Untuk pertanyaan atau bantuan, silakan buat issue di repository ini.

---

**Dibuat dengan ❤️ untuk memudahkan manajemen iuran RT/RW**
