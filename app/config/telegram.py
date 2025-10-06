import os
from dotenv import load_dotenv

load_dotenv()

class TelegramConfig:
    """Konfigurasi untuk Telegram Bot"""
    
    # Bot Token dari BotFather
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Chat ID untuk grup atau channel (opsional)
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Konfigurasi untuk mengirim ke nomor HP individual
    SEND_TO_INDIVIDUAL = os.getenv("TELEGRAM_SEND_INDIVIDUAL", "true").lower() == "true"
    
    # Format pesan default
    MESSAGE_FORMAT = """
🔔 **{title}**

{message}

📅 **Tipe:** {notification_type}
⏰ **Waktu:** {timestamp}
    """
    
    @classmethod
    def is_configured(cls) -> bool:
        """Cek apakah konfigurasi Telegram sudah lengkap"""
        return bool(cls.BOT_TOKEN)
    
    @classmethod
    def get_bot_token(cls) -> str:
        """Ambil bot token"""
        if not cls.BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN tidak ditemukan di environment variables")
        return cls.BOT_TOKEN
    
    @classmethod
    def get_chat_id(cls) -> str:
        """Ambil chat ID (opsional)"""
        return cls.CHAT_ID
