from fastapi import APIRouter, HTTPException, Request
from app.config.database import get_database
from app.services.telegram_service import telegram_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook untuk menangani pesan /start dari user"""
    try:
        data = await request.json()
        logger.info(f"Received webhook data: {data}")
        
        # Cek apakah ini adalah pesan dari user
        if "message" not in data:
            logger.info("No message in webhook data, ignoring")
            return {"ok": True}
        
        message = data["message"]
        chat_id = str(message["chat"]["id"])
        user_id = message["from"]["id"]
        username = message["from"].get("username", "")
        first_name = message["from"].get("first_name", "")
        last_name = message["from"].get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        
        logger.info(f"Processing message from {full_name} ({username}): {message.get('text', 'No text')}")
        
        # Cek apakah pesan adalah /start
        if message.get("text") == "/start":
            logger.info(f"Handling /start command from {full_name} (chat_id: {chat_id})")
            await handle_start_command(chat_id, user_id, username, full_name)
        elif message.get("text") == "/help":
            logger.info(f"Handling /help command from {full_name}")
            await send_help_message(chat_id)
        else:
            # Cek apakah pesan adalah nomor HP
            text = message.get("text", "").strip()
            if text and text.startswith("08") and len(text) >= 10:
                logger.info(f"Handling phone number from {full_name}: {text}")
                await handle_phone_number(chat_id, text, user_id, full_name)
            else:
                logger.info(f"Unknown message from {full_name}, sending help")
                await send_help_message(chat_id)
            
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error handling Telegram webhook: {e}")
        return {"ok": False, "error": str(e)}

async def handle_start_command(chat_id: str, user_id: int, username: str, full_name: str):
    """Handle /start command dari user"""
    try:
        db = get_database()
        
        # Log user yang mengirim /start
        logger.info(f"User {full_name} ({username}) mengirim /start dari chat_id: {chat_id}")
        
        # SELALU simpan chat_id untuk user yang mengirim /start
        # Cari user berdasarkan username atau full_name
        existing_user = None
        
        # Coba cari berdasarkan username
        if username:
            existing_user = await db.users.find_one({"username": username})
            if existing_user:
                logger.info(f"User ditemukan berdasarkan username: {username}")
        
        # Jika tidak ditemukan, coba cari berdasarkan nama
        if not existing_user and full_name:
            existing_user = await db.users.find_one({"nama": {"$regex": full_name, "$options": "i"}})
            if existing_user:
                logger.info(f"User ditemukan berdasarkan nama: {full_name}")
        
        if existing_user:
            # User sudah terdaftar, update telegram_chat_id
            result = await db.users.update_one(
                {"id": existing_user["id"]},
                {"$set": {"telegram_chat_id": chat_id}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated telegram_chat_id for user {existing_user['nama']}: {chat_id}")
            else:
                logger.info(f"ℹ️  User {existing_user['nama']} already has telegram_chat_id: {chat_id}")
            
            success_message = f"""✅ **Berhasil!**

Halo {existing_user.get('nama', full_name)}!

Notifikasi Telegram Anda telah diaktifkan untuk:
📱 Nomor HP: {existing_user.get('nomor_hp', 'N/A')}
🏠 Rumah: {existing_user.get('nomor_rumah', 'N/A')}
💬 Chat ID: {chat_id}

🔔 Anda akan menerima notifikasi tentang:
• Pengumuman RT/RW
• Reminder pembayaran iuran
• Informasi penting lainnya

Terima kasih telah bergabung! 🎉
"""
            
            await telegram_service._send_to_chat_id(chat_id, success_message)
            logger.info(f"✅ User {existing_user['nama']} berhasil diaktifkan untuk notifikasi")
            
        else:
            # User belum terdaftar, tetap simpan chat_id untuk future reference
            # Simpan sebagai temporary user dengan chat_id
            temp_user = {
                "id": f"temp_{user_id}_{chat_id}",
                "nama": full_name,
                "username": username,
                "telegram_chat_id": chat_id,
                "telegram_user_id": user_id,
                "is_temp": True,
                "created_at": datetime.now()
            }
            
            # Cek apakah sudah ada temp user dengan chat_id ini
            existing_temp = await db.users.find_one({"telegram_chat_id": chat_id, "is_temp": True})
            if not existing_temp:
                await db.users.insert_one(temp_user)
                logger.info(f"✅ Created temporary user for {full_name} with chat_id: {chat_id}")
            else:
                logger.info(f"ℹ️  Temporary user already exists for chat_id: {chat_id}")
            
            welcome_message = f"""👋 Halo {full_name}!

Selamat datang di Bot Notifikasi RT/RW Management!

📱 **Untuk menerima notifikasi, silakan:**
1. Kirim nomor HP Anda (contoh: 08123456789)
2. Pastikan nomor HP sudah terdaftar di sistem
3. Admin akan memverifikasi dan mengaktifkan notifikasi

💬 **Chat ID Anda:** {chat_id}
🔍 **Cara mencari nomor HP:**
- Gunakan format: 08xxxxxxxxx
- Pastikan nomor sudah terdaftar di sistem RT/RW

❓ **Bantuan:** Kirim /help untuk informasi lebih lanjut
"""
            
            await telegram_service._send_to_chat_id(chat_id, welcome_message)
            logger.info(f"ℹ️  User {full_name} belum terdaftar, meminta nomor HP")
        
    except Exception as e:
        logger.error(f"❌ Error handling start command: {e}")
        try:
            error_message = "❌ Terjadi kesalahan. Silakan coba lagi atau hubungi admin."
            await telegram_service._send_to_chat_id(chat_id, error_message)
        except:
            logger.error(f"❌ Failed to send error message to chat_id: {chat_id}")

async def handle_phone_number(chat_id: str, phone_number: str, user_id: int, full_name: str):
    """Handle nomor HP yang dikirim user"""
    try:
        db = get_database()
        
        # Cari user berdasarkan nomor HP
        user = await db.users.find_one({"nomor_hp": phone_number})
        
        if user:
            # Update telegram_chat_id user
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {"telegram_chat_id": chat_id}}
            )
            
            success_message = f"""✅ **Berhasil!**

Halo {user.get('nama', 'User')}!

Notifikasi Telegram Anda telah diaktifkan untuk:
📱 Nomor HP: {phone_number}
🏠 Rumah: {user.get('nomor_rumah', 'N/A')}

🔔 Anda akan menerima notifikasi tentang:
• Pengumuman RT/RW
• Reminder pembayaran iuran
• Informasi penting lainnya

Terima kasih telah bergabung! 🎉
"""
            
            await telegram_service._send_to_chat_id(chat_id, success_message)
            logger.info(f"User {user['nama']} ({phone_number}) connected to Telegram")
            
        else:
            error_message = f"""❌ **Nomor HP tidak ditemukan**

Nomor HP {phone_number} tidak terdaftar di sistem.

🔍 **Pastikan:**
• Nomor HP sudah terdaftar di sistem RT/RW
• Format nomor benar (contoh: 08123456789)
• Hubungi admin jika masih bermasalah

❓ **Bantuan:** Kirim /help untuk informasi lebih lanjut
"""
            
            await telegram_service._send_to_chat_id(chat_id, error_message)
            
    except Exception as e:
        logger.error(f"Error handling phone number: {e}")
        error_message = "❌ Terjadi kesalahan. Silakan coba lagi atau hubungi admin."
        await telegram_service._send_to_chat_id(chat_id, error_message)

async def send_help_message(chat_id: str):
    """Kirim pesan bantuan"""
    help_message = """❓ **Bantuan Bot Notifikasi**

🤖 **Perintah yang tersedia:**
/start - Mulai bot dan daftar notifikasi
/help - Tampilkan pesan bantuan ini

📱 **Cara mendaftar notifikasi:**
1. Kirim /start
2. Kirim nomor HP Anda (contoh: 08123456789)
3. Tunggu konfirmasi dari sistem

🔔 **Notifikasi yang akan diterima:**
• Pengumuman RT/RW
• Reminder pembayaran iuran
• Informasi penting lainnya

❓ **Masalah?** Hubungi admin RT/RW
"""
    
    await telegram_service._send_to_chat_id(chat_id, help_message)

@router.post("/webhook/phone")
async def handle_phone_message(request: Request):
    """Handle pesan nomor HP dari user"""
    try:
        data = await request.json()
        
        if "message" not in data:
            return {"ok": True}
        
        message = data["message"]
        chat_id = str(message["chat"]["id"])
        user_id = message["from"]["id"]
        first_name = message["from"].get("first_name", "")
        last_name = message["from"].get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        text = message.get("text", "").strip()
        
        # Cek apakah pesan adalah nomor HP
        if text and text.startswith("08") and len(text) >= 10:
            await handle_phone_number(chat_id, text, user_id, full_name)
        else:
            await send_help_message(chat_id)
            
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error handling phone message: {e}")
        return {"ok": False, "error": str(e)}
