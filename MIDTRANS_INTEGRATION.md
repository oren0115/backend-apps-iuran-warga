# Integrasi Midtrans Payment Gateway (Midtrans Only)

Dokumentasi ini menjelaskan sistem pembayaran yang menggunakan **hanya Midtrans** sebagai payment gateway untuk sistem RT/RW Management. Semua pembayaran dilakukan melalui Midtrans, tidak ada lagi pembayaran manual.

## Konfigurasi

### 1. Environment Variables

Buat file `.env` berdasarkan `env.example` dan isi dengan konfigurasi Midtrans:

```env
# Midtrans Configuration
MIDTRANS_SERVER_KEY=your-midtrans-server-key-here
MIDTRANS_CLIENT_KEY=your-midtrans-client-key-here
MIDTRANS_IS_PRODUCTION=false
```

### 2. Install Dependencies

```bash
pip install -r requirement.txt
```

## API Endpoints

### 1. Create Payment (Midtrans Only)

**POST** `/api/payments`

Membuat pembayaran menggunakan Midtrans. Ini adalah satu-satunya cara untuk membuat pembayaran.

**Request Body:**

```json
{
  "fee_id": "fee-uuid-here",
  "amount": 100000,
  "payment_method": "credit_card" // atau "bank_transfer", "gopay"
}
```

**Response:**

```json
{
  "payment_id": "payment_1234567890",
  "transaction_id": "midtrans-transaction-id",
  "payment_token": "payment-token",
  "payment_url": "https://app.sandbox.midtrans.com/snap/v2/vtweb/...",
  "expiry_time": "2024-01-01T12:00:00Z",
  "payment_type": "credit_card",
  "bank": null,
  "va_number": null
}
```

### 2. Handle Payment Notification (Webhook)

**POST** `/api/payments/notification`

Endpoint untuk menerima notifikasi dari Midtrans (webhook). Otomatis dipanggil oleh Midtrans.

### 3. Check Payment Status

**GET** `/api/payments/status/{transaction_id}`

Mengecek status pembayaran dari Midtrans.

**Response:**

```json
{
  "transaction_id": "midtrans-transaction-id",
  "status": "settlement",
  "payment_type": "credit_card",
  "gross_amount": "100000",
  "fraud_status": "accept"
}
```

### 4. Get User Payments

**GET** `/api/payments`

Mendapatkan semua pembayaran user yang sedang login.

### 5. Get All Payments (Admin Only)

**GET** `/api/admin/payments`

Mendapatkan semua pembayaran untuk admin.

## Metode Pembayaran yang Didukung

1. **Credit Card** (`credit_card`)

   - Visa, MasterCard, JCB
   - 3D Secure enabled

2. **Bank Transfer** (`bank_transfer`)

   - BCA Virtual Account
   - BNI Virtual Account
   - BRI Virtual Account
   - Mandiri Virtual Account

3. **E-Wallet** (`gopay`)
   - GoPay

## Flow Pembayaran (Midtrans Only)

1. **User Request Payment**

   - User memilih tagihan dan metode pembayaran
   - System memanggil endpoint `/api/payments` (hanya Midtrans)

2. **Midtrans Response**

   - System menerima payment URL dan token dari Midtrans
   - User diarahkan ke halaman pembayaran Midtrans

3. **Payment Processing**

   - User melakukan pembayaran di Midtrans
   - Midtrans mengirim notifikasi ke webhook `/api/payments/notification`

4. **Automatic Status Update**
   - System otomatis update status pembayaran berdasarkan notifikasi Midtrans
   - Status tagihan berubah menjadi "Lunas" jika pembayaran berhasil
   - Tidak ada lagi proses approve/reject manual oleh admin

## Status Mapping

| Midtrans Status | Internal Status | Keterangan            |
| --------------- | --------------- | --------------------- |
| capture         | Approved        | Pembayaran berhasil   |
| settlement      | Approved        | Pembayaran berhasil   |
| pending         | Pending         | Menunggu pembayaran   |
| deny            | Rejected        | Pembayaran ditolak    |
| cancel          | Rejected        | Pembayaran dibatalkan |
| expire          | Rejected        | Pembayaran expired    |
| failure         | Rejected        | Pembayaran gagal      |

## Webhook Configuration

Di Midtrans Dashboard, set webhook URL ke:

```
https://yourdomain.com/api/payments/notification
```

## Testing

### Sandbox Mode

- Set `MIDTRANS_IS_PRODUCTION=false`
- Gunakan test card numbers dari dokumentasi Midtrans
- Test webhook menggunakan ngrok atau tools serupa

### Production Mode

- Set `MIDTRANS_IS_PRODUCTION=true`
- Gunakan production server key dan client key
- Pastikan webhook URL dapat diakses dari internet

## Error Handling

System akan menangani error berikut:

- Invalid signature pada webhook
- Payment not found
- Midtrans API errors
- Database connection errors

## Security

- Signature verification pada webhook
- JWT authentication untuk API endpoints
- Environment variables untuk sensitive data
- HTTPS required untuk production

## Monitoring

Monitor log untuk:

- Payment creation success/failure
- Webhook notifications
- Status updates
- Error messages

## Perubahan dari Sistem Manual

### Yang Dihapus:

- ❌ Upload bukti transfer manual
- ❌ Approve/reject pembayaran oleh admin
- ❌ Field `bukti_transfer` di database
- ❌ Endpoint `/api/payments/midtrans` (diganti dengan `/api/payments`)
- ❌ Endpoint approve/reject di admin

### Yang Ditambahkan:

- ✅ Semua pembayaran otomatis melalui Midtrans
- ✅ Status pembayaran otomatis terupdate via webhook
- ✅ Field Midtrans di database (transaction_id, payment_token, dll)
- ✅ Endpoint webhook untuk notifikasi Midtrans
- ✅ Automatic fee status update

## Troubleshooting

### Common Issues

1. **Webhook tidak diterima**

   - Pastikan URL webhook dapat diakses dari internet
   - Check firewall settings
   - Verify signature verification

2. **Payment gagal dibuat**

   - Check Midtrans credentials
   - Verify fee exists dan belongs to user
   - Check network connectivity

3. **Status tidak terupdate**

   - Check webhook endpoint
   - Verify database connection
   - Check log untuk error messages

4. **Payment tidak muncul di admin**
   - Semua pembayaran sekarang otomatis, tidak perlu approve manual
   - Admin hanya bisa melihat status pembayaran, tidak bisa approve/reject
