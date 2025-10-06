#!/usr/bin/env python3
"""
Script untuk setup Telegram webhook
Menghubungkan bot Telegram dengan backend API
"""

import os
import sys
import asyncio
import aiohttp
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramWebhookSetup:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN tidak ditemukan di environment variables")
        
        if not self.webhook_url:
            raise ValueError("TELEGRAM_WEBHOOK_URL tidak ditemukan di environment variables")
    
    async def get_bot_info(self):
        """Get bot information from Telegram API"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            bot_info = data.get("result", {})
                            logger.info(f"✅ Bot info: @{bot_info.get('username', 'Unknown')} ({bot_info.get('first_name', 'Unknown')})")
                            return bot_info
                        else:
                            logger.error(f"❌ Telegram API error: {data.get('description', 'Unknown error')}")
                            return None
                    else:
                        logger.error(f"❌ HTTP error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ Error getting bot info: {e}")
            return None
    
    async def set_webhook(self):
        """Set webhook URL for the bot"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
            data = {
                "url": self.webhook_url,
                "allowed_updates": ["message", "callback_query"]
            }
            
            logger.info(f"🔗 Setting webhook to: {self.webhook_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info("✅ Webhook berhasil diset!")
                            logger.info(f"📝 Description: {result.get('description', 'No description')}")
                            return True
                        else:
                            logger.error(f"❌ Telegram API error: {result.get('description', 'Unknown error')}")
                            return False
                    else:
                        logger.error(f"❌ HTTP error: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error setting webhook: {e}")
            return False
    
    async def get_webhook_info(self):
        """Get current webhook information"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getWebhookInfo"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            webhook_info = data.get("result", {})
                            logger.info("📊 Webhook Info:")
                            logger.info(f"   URL: {webhook_info.get('url', 'Not set')}")
                            logger.info(f"   Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
                            logger.info(f"   Pending update count: {webhook_info.get('pending_update_count', 0)}")
                            logger.info(f"   Last error date: {webhook_info.get('last_error_date', 'Never')}")
                            logger.info(f"   Last error message: {webhook_info.get('last_error_message', 'None')}")
                            return webhook_info
                        else:
                            logger.error(f"❌ Telegram API error: {data.get('description', 'Unknown error')}")
                            return None
                    else:
                        logger.error(f"❌ HTTP error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ Error getting webhook info: {e}")
            return None
    
    async def delete_webhook(self):
        """Delete current webhook"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook"
            data = {"drop_pending_updates": True}
            
            logger.info("🗑️  Deleting current webhook...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info("✅ Webhook berhasil dihapus!")
                            return True
                        else:
                            logger.error(f"❌ Telegram API error: {result.get('description', 'Unknown error')}")
                            return False
                    else:
                        logger.error(f"❌ HTTP error: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error deleting webhook: {e}")
            return False
    
    async def test_webhook(self):
        """Test webhook endpoint"""
        try:
            logger.info(f"🧪 Testing webhook endpoint: {self.webhook_url}")
            
            # Test with a simple GET request first
            async with aiohttp.ClientSession() as session:
                async with session.get(self.webhook_url) as response:
                    if response.status == 200:
                        logger.info("✅ Webhook endpoint is accessible")
                        return True
                    else:
                        logger.warning(f"⚠️  Webhook endpoint returned status: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error testing webhook: {e}")
            return False

async def main():
    """Main function"""
    print("🤖 Telegram Webhook Setup")
    print("=" * 50)
    
    try:
        setup = TelegramWebhookSetup()
        
        # 1. Get bot info
        print("\n1️⃣  Getting bot information...")
        bot_info = await setup.get_bot_info()
        if not bot_info:
            print("❌ Failed to get bot information. Check your TELEGRAM_BOT_TOKEN")
            return False
        
        # 2. Test webhook endpoint
        print("\n2️⃣  Testing webhook endpoint...")
        webhook_accessible = await setup.test_webhook()
        if not webhook_accessible:
            print("⚠️  Webhook endpoint is not accessible. Make sure your backend is running and accessible.")
            print(f"   URL: {setup.webhook_url}")
        
        # 3. Get current webhook info
        print("\n3️⃣  Getting current webhook info...")
        await setup.get_webhook_info()
        
        # 4. Set webhook
        print("\n4️⃣  Setting webhook...")
        success = await setup.set_webhook()
        
        if success:
            print("\n✅ Webhook setup completed successfully!")
            print("\n📋 Next steps:")
            print("1. Make sure your backend is running and accessible")
            print("2. Test the bot by sending /start to your bot")
            print("3. Check the webhook info again to verify it's working")
            
            # 5. Verify webhook was set
            print("\n5️⃣  Verifying webhook...")
            await setup.get_webhook_info()
            
        else:
            print("\n❌ Webhook setup failed!")
            print("\n🔧 Troubleshooting:")
            print("1. Check if TELEGRAM_BOT_TOKEN is correct")
            print("2. Check if TELEGRAM_WEBHOOK_URL is accessible")
            print("3. Make sure your backend is running")
            print("4. Check if the webhook URL uses HTTPS")
            
        return success
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n🔧 Please check your .env file and make sure:")
        print("   - TELEGRAM_BOT_TOKEN is set")
        print("   - TELEGRAM_WEBHOOK_URL is set")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def print_usage():
    """Print usage information"""
    print("Usage: python setup_telegram_webhook.py [command]")
    print("\nCommands:")
    print("  setup     - Set webhook (default)")
    print("  info      - Get webhook info")
    print("  delete    - Delete webhook")
    print("  test      - Test webhook endpoint")
    print("  help      - Show this help")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "help":
            print_usage()
            sys.exit(0)
        elif command == "info":
            asyncio.run(TelegramWebhookSetup().get_webhook_info())
        elif command == "delete":
            asyncio.run(TelegramWebhookSetup().delete_webhook())
        elif command == "test":
            asyncio.run(TelegramWebhookSetup().test_webhook())
        elif command == "setup":
            asyncio.run(main())
        else:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)
    else:
        # Default: setup webhook
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
