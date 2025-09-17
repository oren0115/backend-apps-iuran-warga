# Midtrans Payment Flow

## Sequence Diagram

```
User -> Frontend: Pilih tagihan & metode pembayaran
Frontend -> Backend: POST /api/payments/midtrans
Backend -> Midtrans: Create payment transaction
Midtrans -> Backend: Return payment URL & token
Backend -> Frontend: Return payment details
Frontend -> User: Redirect ke Midtrans payment page
User -> Midtrans: Lakukan pembayaran
Midtrans -> Backend: POST /api/payments/midtrans/notification (webhook)
Backend -> Database: Update payment status
Backend -> Database: Update fee status to "Lunas"
Backend -> Midtrans: Return success response
```

## Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend    │    │  Midtrans   │    │  Database   │
│             │    │              │    │             │    │             │
│ 1. Request  │───▶│ 2. Validate  │    │             │    │             │
│   Payment   │    │   & Create   │    │             │    │             │
│             │    │   Payment    │    │             │    │             │
│             │◀───│ 3. Return    │    │             │    │             │
│             │    │   Payment    │    │             │    │             │
│             │    │   Details    │    │             │    │             │
│             │    │              │    │             │    │             │
│ 4. Redirect │───▶│              │───▶│ 5. Process  │    │             │
│   to        │    │              │    │   Payment   │    │             │
│   Midtrans  │    │              │    │             │    │             │
│             │    │              │    │             │    │             │
│             │    │ 6. Receive   │◀───│ 7. Send     │    │             │
│             │    │   Webhook    │    │   Webhook   │    │             │
│             │    │              │    │             │    │             │
│             │    │ 8. Update    │───▶│             │    │ 9. Update   │
│             │    │   Status     │    │             │    │   Payment   │
│             │    │              │    │             │    │   & Fee     │
│             │    │              │    │             │    │   Status    │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
```

## Payment Methods Flow

### Credit Card

```
User -> Midtrans: Enter card details
Midtrans -> Bank: Process 3D Secure
Bank -> Midtrans: Return result
Midtrans -> Backend: Webhook notification
```

### Bank Transfer (Virtual Account)

```
User -> Bank: Transfer to VA number
Bank -> Midtrans: Payment notification
Midtrans -> Backend: Webhook notification
```

### E-Wallet (GoPay)

```
User -> GoPay: Authorize payment
GoPay -> Midtrans: Payment confirmation
Midtrans -> Backend: Webhook notification
```

## Database Schema Updates

### Payment Collection

```json
{
  "id": "payment_1234567890",
  "fee_id": "fee-uuid",
  "user_id": "user-uuid",
  "amount": 100000,
  "method": "credit_card",
  "status": "Approved",
  "transaction_id": "midtrans-transaction-id",
  "payment_token": "payment-token",
  "payment_url": "https://app.sandbox.midtrans.com/...",
  "midtrans_status": "settlement",
  "payment_type": "credit_card",
  "bank": null,
  "va_number": null,
  "expiry_time": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T10:00:00Z",
  "approved_at": "2024-01-01T10:05:00Z"
}
```

## Error Handling Flow

```
Error Occurs -> Log Error -> Return Appropriate HTTP Status -> Frontend Handle Error
```

### Common Error Scenarios

1. **Invalid Fee ID**: 404 Not Found
2. **Payment Already Exists**: 400 Bad Request
3. **Midtrans API Error**: 500 Internal Server Error
4. **Invalid Webhook Signature**: 400 Bad Request
5. **Database Connection Error**: 500 Internal Server Error
