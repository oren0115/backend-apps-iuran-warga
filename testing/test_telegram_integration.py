#!/usr/bin/env python3
"""
Test script untuk integrasi Telegram dengan broadcast notification
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.telegram_service import telegram_service
from app.config.telegram import TelegramConfig

async def test_telegram_connection():
    """Test koneksi ke Telegram Bot API"""
    print("🔍 Testing Telegram connection...")
    
    if not TelegramConfig.is_configured():
        print("❌ Telegram tidak dikonfigurasi!")
        print("   Pastikan TELEGRAM_BOT_TOKEN sudah diset di environment variables")
        return False
    
    result = await telegram_service.test_connection()
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
        return True
    else:
        print(f"❌ {result.get('message')}")
        return False

async def test_broadcast_message():
    """Test mengirim pesan broadcast"""
    print("\n📢 Testing broadcast message...")
    
    if not TelegramConfig.is_configured():
        print("❌ Telegram tidak dikonfigurasi!")
        return False
    
    result = await telegram_service.send_broadcast_message(
        title="Test Notifikasi",
        message="Ini adalah test notifikasi dari sistem RT/RW Management",
        notification_type="pengumuman"
    )
    
    if result.get("success"):
        print(f"✅ {result.get('message')}")
        return True
    else:
        print(f"❌ {result.get('message')}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Telegram Integration Test")
    print("=" * 50)
    
    # Test 1: Koneksi
    connection_ok = await test_telegram_connection()
    
    if not connection_ok:
        print("\n❌ Test gagal: Koneksi Telegram tidak berhasil")
        return
    
    # Test 2: Broadcast message
    broadcast_ok = await test_broadcast_message()
    
    if broadcast_ok:
        print("\n✅ Semua test berhasil!")
        print("   Telegram integration siap digunakan")
    else:
        print("\n❌ Test broadcast gagal")
        print("   Cek konfigurasi TELEGRAM_CHAT_ID")

if __name__ == "__main__":
    asyncio.run(main())
