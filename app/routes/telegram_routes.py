from fastapi import APIRouter, Request, HTTPException, Depends
from app.config.database import get_database
from app.models.response import MessageResponse
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Webhook endpoint untuk menerima update dari Telegram Bot
    """
    try:
        # Parse request body
        body = await request.json()
        logger.info(f"Received Telegram webhook: {json.dumps(body, indent=2)}")
        
        # Extract message data
        message = body.get("message", {})
        if not message:
            logger.warning("No message in webhook data")
            return {"ok": True}
        
        # Get chat and user info
        chat = message.get("chat", {})
        user = message.get("from", {})
        text = message.get("text", "")
        
        chat_id = chat.get("id")
        user_id = user.get("id")
        username = user.get("username", "")
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")
        
        # Handle commands
        if text == "/start":
            await handle_start_command(chat_id, user_id, username, first_name, last_name)
        elif text == "/status":
            await handle_status_command(chat_id, user_id)
        elif text == "/help":
            await handle_help_command(chat_id, first_name)
        else:
            # Handle phone number input
            await handle_phone_number_input(chat_id, user_id, text, first_name)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        return {"ok": False, "error": str(e)}

async def handle_phone_number_input(chat_id: int, user_id: int, phone_input: str, first_name: str):
    """
    Handle phone number input from user
    """
    try:
        db = get_database()
        
        # Clean phone number input (remove spaces, dashes, etc.)
        phone_clean = phone_input.strip().replace(" ", "").replace("-", "").replace("+", "")
        
        # Check if input looks like a phone number (contains digits)
        if not phone_clean.isdigit() or len(phone_clean) < 10:
            await send_telegram_message(
                chat_id,
                f"❌ **Format nomor HP tidak valid!**\n\n"
                f"📱 **Contoh format yang benar:**\n"
                f"• 081234567890\n"
                f"• 6281234567890\n\n"
                f"⚠️ **Pastikan nomor HP yang Anda ketik sama persis dengan yang terdaftar di sistem.**\n\n"
                f"🔄 Silakan coba lagi atau ketik /start untuk memulai ulang."
            )
            return
        
        # Try to find user by phone number
        user = await db.users.find_one({"nomor_hp": phone_clean})
        
        if not user:
            # Try with different phone number formats
            # Format 1: 08xx -> 628xx
            if phone_clean.startswith("08"):
                phone_alt = "62" + phone_clean[1:]
                user = await db.users.find_one({"nomor_hp": phone_alt})
            
            # Format 2: 628xx -> 08xx
            elif phone_clean.startswith("62"):
                phone_alt = "0" + phone_clean[2:]
                user = await db.users.find_one({"nomor_hp": phone_alt})
        
        if not user:
            await send_telegram_message(
                chat_id,
                f"❌ **Nomor HP tidak ditemukan di sistem!**\n\n"
                f"📱 **Nomor yang Anda masukkan:** {phone_input}\n\n"
                f"🔍 **Kemungkinan penyebab:**\n"
                f"• Nomor HP belum terdaftar di sistem\n"
                f"• Format nomor tidak sesuai dengan yang terdaftar\n"
                f"• Belum mendaftar sebagai warga\n\n"
                f"💡 **Solusi:**\n"
                f"• Pastikan nomor HP sudah terdaftar di aplikasi web\n"
                f"• Cek format nomor HP yang terdaftar\n"
                f"• Hubungi admin jika sudah terdaftar tapi tidak ditemukan\n\n"
                f"🔄 Ketik /start untuk mencoba lagi."
            )
            return
        
        # Check if user already has telegram_chat_id
        if user.get("telegram_chat_id"):
            await send_telegram_message(
                chat_id,
                f"⚠️ **Nomor HP sudah terhubung dengan akun Telegram lain!**\n\n"
                f"👤 **Nama:** {user.get('nama', 'Unknown')}\n"
                f"📱 **Nomor HP:** {user.get('nomor_hp', 'N/A')}\n\n"
                f"🔒 Akun ini sudah memiliki notifikasi Telegram aktif.\n\n"
                f"💡 **Jika ini adalah akun Anda:**\n"
                f"• Gunakan akun Telegram yang sudah terhubung\n"
                f"• Atau hubungi admin untuk reset koneksi\n\n"
                f"🔄 Ketik /start untuk mencoba dengan nomor lain."
            )
            return
        
        # Link telegram_chat_id to user
        result = await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"telegram_chat_id": str(chat_id)}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Successfully linked Telegram chat_id {chat_id} to user {user.get('nama', 'Unknown')}")
            
            # Send success message
            await send_telegram_message(
                chat_id,
                f"✅ **Notifikasi Telegram Berhasil Diaktifkan!**\n\n"
                f"👤 **Nama:** {user.get('nama', 'Unknown')}\n"
                f"📱 **Nomor HP:** {user.get('nomor_hp', 'N/A')}\n"
                f"🏠 **Nomor Rumah:** {user.get('nomor_rumah', 'N/A')}\n"
                f"🏘️ **Alamat:** {user.get('alamat', 'N/A')}\n\n"
                f"🎉 **Selamat!** Anda akan menerima notifikasi penting dari RT/RW melalui bot ini.\n\n"
                f"📢 **Notifikasi yang akan Anda terima:**\n"
                f"• Pengumuman penting\n"
                f"• Reminder pembayaran iuran\n"
                f"• Informasi kegiatan RT/RW\n"
                f"• Notifikasi lainnya\n\n"
                f"💡 **Tips:** Jangan hapus chat dengan bot ini agar notifikasi tetap aktif.\n\n"
                f"🔄 Ketik /start kapan saja untuk melihat status notifikasi."
            )
        else:
            logger.warning(f"Failed to update telegram_chat_id for user {user.get('nama', 'Unknown')}")
            await send_telegram_message(
                chat_id,
                f"❌ **Gagal mengaktifkan notifikasi!**\n\n"
                f"Terjadi kesalahan sistem. Silakan coba lagi atau hubungi admin untuk bantuan.\n\n"
                f"🔄 Ketik /start untuk mencoba lagi."
            )
            
    except Exception as e:
        logger.error(f"Error handling phone number input: {e}")
        await send_telegram_message(
            chat_id,
            f"❌ **Terjadi kesalahan sistem!**\n\n"
            f"Silakan coba lagi atau hubungi admin untuk bantuan.\n\n"
            f"🔄 Ketik /start untuk memulai ulang."
        )

async def handle_status_command(chat_id: int, user_id: int):
    """
    Handle /status command to check notification status
    """
    try:
        db = get_database()
        
        # Find user by telegram_chat_id
        user = await db.users.find_one({"telegram_chat_id": str(chat_id)})
        
        if not user:
            await send_telegram_message(
                chat_id,
                f"❌ **Notifikasi Telegram Belum Aktif!**\n\n"
                f"🔗 **Chat ID:** {chat_id}\n\n"
                f"📱 **Untuk mengaktifkan notifikasi:**\n"
                f"• Ketik /start untuk memulai proses aktivasi\n"
                f"• Masukkan nomor HP yang terdaftar di sistem\n\n"
                f"💡 **Pastikan nomor HP sudah terdaftar di aplikasi web.**"
            )
            return
        
        # Send status information
        await send_telegram_message(
            chat_id,
            f"✅ **Status Notifikasi Telegram**\n\n"
            f"👤 **Nama:** {user.get('nama', 'Unknown')}\n"
            f"📱 **Nomor HP:** {user.get('nomor_hp', 'N/A')}\n"
            f"🏠 **Nomor Rumah:** {user.get('nomor_rumah', 'N/A')}\n"
            f"🏘️ **Alamat:** {user.get('alamat', 'N/A')}\n"
            f"🔗 **Chat ID:** {chat_id}\n\n"
            f"🎉 **Status:** Notifikasi Telegram AKTIF\n\n"
            f"📢 **Anda akan menerima:**\n"
            f"• Pengumuman penting\n"
            f"• Reminder pembayaran iuran\n"
            f"• Informasi kegiatan RT/RW\n"
            f"• Notifikasi lainnya\n\n"
            f"💡 **Tips:** Jangan hapus chat dengan bot ini agar notifikasi tetap aktif."
        )
        
    except Exception as e:
        logger.error(f"Error handling status command: {e}")
        await send_telegram_message(
            chat_id,
            f"❌ **Terjadi kesalahan sistem!**\n\n"
            f"Silakan coba lagi atau hubungi admin untuk bantuan."
        )

async def handle_help_command(chat_id: int, first_name: str):
    """
    Handle /help command to show available commands
    """
    try:
        await send_telegram_message(
            chat_id,
            f"👋 Halo {first_name}!\n\n"
            f"🤖 **Bot Notifikasi RT/RW Management**\n\n"
            f"📋 **Perintah yang tersedia:**\n\n"
            f"🔸 **/start** - Memulai aktivasi notifikasi\n"
            f"🔸 **/status** - Cek status notifikasi Anda\n"
            f"🔸 **/help** - Tampilkan bantuan ini\n\n"
            f"📱 **Cara mengaktifkan notifikasi:**\n"
            f"1. Ketik /start\n"
            f"2. Masukkan nomor HP yang terdaftar di sistem\n"
            f"3. Tunggu konfirmasi aktivasi\n\n"
            f"⚠️ **Penting:**\n"
            f"• Pastikan nomor HP sudah terdaftar di aplikasi web\n"
            f"• Format nomor HP harus sama dengan yang terdaftar\n"
            f"• Jangan hapus chat dengan bot ini\n\n"
            f"🆘 **Butuh bantuan?**\n"
            f"Hubungi admin RT/RW untuk bantuan lebih lanjut."
        )
        
    except Exception as e:
        logger.error(f"Error handling help command: {e}")

async def handle_start_command(chat_id: int, user_id: int, username: str, first_name: str, last_name: str):
    """
    Handle /start command from Telegram bot
    """
    try:
        db = get_database()
        
        # Check if user already has telegram_chat_id
        existing_user = await db.users.find_one({"telegram_chat_id": str(chat_id)})
        if existing_user:
            await send_telegram_message(
                chat_id,
                f"✅ **Notifikasi Telegram Sudah Aktif!**\n\n"
                f"👤 **Nama:** {existing_user.get('nama', 'Unknown')}\n"
                f"📱 **Nomor HP:** {existing_user.get('nomor_hp', 'N/A')}\n"
                f"🏠 **Nomor Rumah:** {existing_user.get('nomor_rumah', 'N/A')}\n\n"
                f"🎉 Anda sudah terdaftar untuk menerima notifikasi dari RT/RW.\n\n"
                f"💡 **Tips:** Jangan hapus chat dengan bot ini agar notifikasi tetap aktif."
            )
            return
        
        # Try to find user by username first (if provided)
        user = None
        if username:
            user = await db.users.find_one({"username": username})
            if user:
                logger.info(f"Found user by username: {user.get('nama', 'Unknown')}")
        
        # If not found by username, ask for phone number to match
        if not user:
            await send_telegram_message(
                chat_id,
                f"👋 Halo {first_name}!\n\n"
                f"Selamat datang di bot notifikasi RT/RW Management.\n\n"
                f"📱 **Untuk mengaktifkan notifikasi, silakan ketik nomor HP Anda:**\n"
                f"Contoh: 081234567890\n\n"
                f"⚠️ **Pastikan nomor HP yang Anda ketik sama persis dengan yang terdaftar di sistem.**"
            )
            return
        
        # Update user with telegram_chat_id
        result = await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"telegram_chat_id": str(chat_id)}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Successfully linked Telegram chat_id {chat_id} to user {user.get('nama', 'Unknown')}")
            
            # Send confirmation message
            await send_telegram_message(
                chat_id,
                f"✅ **Notifikasi Telegram Berhasil Diaktifkan!**\n\n"
                f"👤 **Nama:** {user.get('nama', 'Unknown')}\n"
                f"📱 **Nomor HP:** {user.get('nomor_hp', 'N/A')}\n"
                f"🏠 **Nomor Rumah:** {user.get('nomor_rumah', 'N/A')}\n\n"
                f"🎉 Anda akan menerima notifikasi penting dari RT/RW melalui bot ini.\n\n"
                f"💡 **Tips:** Jangan hapus chat dengan bot ini agar notifikasi tetap aktif."
            )
        else:
            logger.warning(f"Failed to update telegram_chat_id for user {user.get('nama', 'Unknown')}")
            await send_telegram_message(
                chat_id,
                "❌ Gagal mengaktifkan notifikasi. Silakan hubungi admin untuk bantuan."
            )
            
    except Exception as e:
        logger.error(f"Error handling /start command: {e}")
        await send_telegram_message(
            chat_id,
            "❌ Terjadi kesalahan sistem. Silakan hubungi admin untuk bantuan."
        )

async def send_telegram_message(chat_id: int, message: str):
    """
    Send message to Telegram chat
    """
    try:
        import aiohttp
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not found")
            return False
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info(f"Message sent successfully to chat_id {chat_id}")
                    return True
                else:
                    logger.error(f"Failed to send message: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

@router.get("/telegram/webhook/info")
async def webhook_info():
    """
    Get webhook information (for debugging)
    """
    return {
        "message": "Telegram webhook endpoint is active",
        "endpoint": "/api/telegram/webhook",
        "status": "ready"
    }
