import asyncio
import logging
from typing import List, Optional
from datetime import datetime
from app.config.telegram import TelegramConfig
from app.config.database import get_database

logger = logging.getLogger(__name__)

class TelegramService:
    """Service untuk mengirim notifikasi via Telegram"""
    
    def __init__(self):
        self.bot_token = None
        self.chat_id = None
        self.is_configured = False
        
        # Inisialisasi konfigurasi
        if TelegramConfig.is_configured():
            try:
                self.bot_token = TelegramConfig.get_bot_token()
                self.chat_id = TelegramConfig.get_chat_id()
                self.is_configured = True
                logger.info("Telegram service berhasil dikonfigurasi")
            except Exception as e:
                logger.error(f"Gagal mengkonfigurasi Telegram service: {e}")
                self.is_configured = False
        else:
            logger.warning("Telegram tidak dikonfigurasi. Set TELEGRAM_BOT_TOKEN di environment variables")
    
    async def send_message_to_phone(self, phone_number: str, title: str, message: str, notification_type: str = "pengumuman") -> bool:
        """
        Kirim pesan ke nomor HP via Telegram
        
        Note: Telegram Bot API tidak mendukung pengiriman langsung ke nomor HP.
        Metode ini akan mencari user berdasarkan nomor HP di database dan mengirim ke chat_id mereka.
        """
        if not self.is_configured:
            logger.warning("Telegram service tidak dikonfigurasi")
            return False
        
        try:
            # Format pesan
            formatted_message = self._format_message(title, message, notification_type)
            
            # Untuk sekarang, kita akan mengirim ke chat_id yang dikonfigurasi
            # atau ke semua user yang memiliki nomor HP yang sama
            if self.chat_id:
                return await self._send_to_chat_id(self.chat_id, formatted_message)
            else:
                # Jika tidak ada chat_id, coba kirim ke user yang memiliki nomor HP tersebut
                return await self._send_to_user_by_phone(phone_number, formatted_message)
                
        except Exception as e:
            logger.error(f"Gagal mengirim pesan Telegram ke {phone_number}: {e}")
            return False
    
    async def send_broadcast_message(self, title: str, message: str, notification_type: str = "pengumuman") -> dict:
        """
        Kirim pesan broadcast ke semua user yang memiliki nomor HP
        """
        if not self.is_configured:
            logger.warning("Telegram service tidak dikonfigurasi")
            return {"success": False, "message": "Telegram tidak dikonfigurasi"}
        
        try:
            # Format pesan
            formatted_message = self._format_message(title, message, notification_type)
            
            # Kirim ke semua user yang memiliki nomor HP
            return await self._send_to_all_users_individual(formatted_message, title, message, notification_type)
                
        except Exception as e:
            logger.error(f"Gagal mengirim broadcast message: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def _send_to_chat_id(self, chat_id: str, message: str) -> bool:
        """Kirim pesan ke chat ID tertentu"""
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info(f"Pesan berhasil dikirim ke chat ID {chat_id}")
                        return True
                    else:
                        logger.error(f"Gagal mengirim pesan ke chat ID {chat_id}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error mengirim ke chat ID {chat_id}: {e}")
            return False
    
    async def _send_to_user_by_phone(self, phone_number: str, message: str) -> bool:
        """Kirim pesan ke user berdasarkan nomor HP (implementasi sederhana)"""
        # Untuk implementasi sederhana, kita akan mengirim ke chat_id yang dikonfigurasi
        # dengan informasi nomor HP
        if self.chat_id:
            message_with_phone = f"📱 **Nomor HP:** {phone_number}\n\n{message}"
            return await self._send_to_chat_id(self.chat_id, message_with_phone)
        return False
    
    async def _send_to_all_users(self, message: str) -> dict:
        """Kirim pesan ke semua user (implementasi sederhana)"""
        # Untuk implementasi sederhana, kita akan mengirim ke chat_id yang dikonfigurasi
        if self.chat_id:
            success = await self._send_to_chat_id(self.chat_id, message)
            return {
                "success": success,
                "message": f"Pesan broadcast dikirim ke chat ID {self.chat_id}" if success else "Gagal mengirim pesan"
            }
        
        # Jika tidak ada chat_id, coba ambil semua user dan kirim ke masing-masing
        try:
            db = get_database()
            users = await db.users.find({"nomor_hp": {"$exists": True, "$ne": ""}}, {"_id": 0}).to_list(1000)
            
            success_count = 0
            total_users = len(users)
            
            # Untuk sekarang, kirim ke chat_id yang dikonfigurasi dengan daftar user
            if self.chat_id:
                user_list = "\n".join([f"• {user.get('nama', 'Unknown')} - {user.get('nomor_hp', 'N/A')}" for user in users])
                message_with_users = f"{message}\n\n👥 **Daftar Penerima ({total_users} user):**\n{user_list}"
                success = await self._send_to_chat_id(self.chat_id, message_with_users)
                success_count = 1 if success else 0
            
            return {
                "success": success_count > 0,
                "message": f"Pesan broadcast dikirim ke {success_count}/{total_users} user"
            }
            
        except Exception as e:
            logger.error(f"Error mengirim ke semua user: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def _send_to_all_users_individual(self, formatted_message: str, title: str, message: str, notification_type: str) -> dict:
        """Kirim pesan ke semua user individual (ke nomor HP masing-masing)"""
        try:
            db = get_database()
            # Ambil user yang memiliki telegram_chat_id (sudah pernah chat dengan bot)
            users = await db.users.find(
                {
                    "nomor_hp": {"$exists": True, "$ne": ""}, 
                    "is_admin": False,
                    "telegram_chat_id": {"$exists": True, "$ne": ""}
                }, 
                {"_id": 0, "id": 1, "nama": 1, "nomor_hp": 1, "telegram_chat_id": 1}
            ).to_list(1000)
            
            if not users:
                return {
                    "success": False, 
                    "message": "Tidak ada user yang sudah mengirim /start ke bot. User perlu mengirim /start ke bot terlebih dahulu.",
                    "total_users": 0,
                    "success_count": 0,
                    "failed_users": []
                }
            
            success_count = 0
            failed_users = []
            total_users = len(users)
            
            # Kirim ke setiap user individual
            logger.info(f"Starting to send messages to {total_users} users")
            
            for user in users:
                try:
                    chat_id = user.get('telegram_chat_id')
                    user_name = user.get('nama', 'Unknown')
                    user_phone = user.get('nomor_hp', 'N/A')
                    
                    logger.info(f"Processing user: {user_name} ({user_phone}) - chat_id: {chat_id}")
                    
                    if chat_id:
                        # Kirim pesan ke chat_id individual user
                        logger.info(f"Sending message to {user_name} via chat_id: {chat_id}")
                        success = await self._send_to_chat_id(chat_id, formatted_message)
                        
                        if success:
                            success_count += 1
                            logger.info(f"✅ Message sent successfully to {user_name} (chat_id: {chat_id})")
                        else:
                            failed_users.append(user_name)
                            logger.warning(f"❌ Failed to send to {user_name} (chat_id: {chat_id})")
                    else:
                        failed_users.append(user_name)
                        logger.warning(f"❌ No telegram_chat_id for {user_name} ({user_phone})")
                        
                except Exception as e:
                    failed_users.append(user.get('nama', 'Unknown'))
                    logger.error(f"❌ Error sending to {user.get('nama', 'Unknown')}: {e}")
            
            logger.info(f"Broadcast completed: {success_count}/{total_users} successful")
            
            # Juga kirim ke grup/channel jika dikonfigurasi (untuk backup/notifikasi admin)
            if self.chat_id:
                try:
                    user_list = "\n".join([
                        f"• {user.get('nama', 'Unknown')} - {user.get('nomor_hp', 'N/A')}" 
                        for user in users
                    ])
                    
                    admin_message = f"""📢 **BROADCAST NOTIFICATION SENT**

{formatted_message}

👥 **Daftar Penerima ({total_users} user):**
{user_list}

📊 **Status Pengiriman:**
✅ Berhasil: {success_count}
❌ Gagal: {len(failed_users)}
"""
                    
                    await self._send_to_chat_id(self.chat_id, admin_message)
                    logger.info("Admin notification sent to group/channel")
                    
                except Exception as e:
                    logger.error(f"Failed to send admin notification: {e}")
            
            result_message = f"Pesan broadcast dikirim ke {success_count}/{total_users} user"
            if failed_users:
                result_message += f". Gagal: {', '.join(failed_users[:5])}{'...' if len(failed_users) > 5 else ''}"
            
            return {
                "success": success_count > 0,
                "message": result_message,
                "total_users": total_users,
                "success_count": success_count,
                "failed_users": failed_users
            }
            
        except Exception as e:
            logger.error(f"Error mengirim ke semua user individual: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def _format_message(self, title: str, message: str, notification_type: str) -> str:
        """Format pesan sesuai template"""
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        return TelegramConfig.MESSAGE_FORMAT.format(
            title=title,
            message=message,
            notification_type=notification_type.title(),
            timestamp=timestamp
        )
    
    async def test_connection(self) -> dict:
        """Test koneksi ke Telegram Bot API"""
        if not self.is_configured:
            return {"success": False, "message": "Telegram tidak dikonfigurasi"}
        
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        bot_info = data.get("result", {})
                        return {
                            "success": True,
                            "message": f"Bot berhasil dikonfigurasi: @{bot_info.get('username', 'Unknown')}"
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Gagal mengakses Bot API: {response.status}"
                        }
                        
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

# Instance global
telegram_service = TelegramService()
