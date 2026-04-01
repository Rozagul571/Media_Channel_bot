import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")

SESSION_PATH = "./data/user_session"


async def main():
    print("\n" + "=" * 60)
    print("  📱 TENDERZON MEDIA - Telegram Session Creator")
    print("=" * 60)

    if not API_ID or not API_HASH or not PHONE:
        print("\n❌ ERROR: .env file not configured properly!")
        print("   Check: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
        return

    Path("./data").mkdir(exist_ok=True)

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"\n✅ Session already exists: @{me.username or me.first_name}")
        print("\n   Run: docker-compose up -d")
        await client.disconnect()
        return

    print(f"\n📱 Sending code to: {PHONE}")
    await client.send_code_request(PHONE)

    try:
        code = input("\n📲 Enter 5-digit code from Telegram: ").strip()
        await client.sign_in(PHONE, code)
    except SessionPasswordNeededError:
        password = input("🔑 Enter 2FA password: ").strip()
        await client.sign_in(password=password)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await client.disconnect()
        return

    me = await client.get_me()
    print(f"\n✅ Success! Logged in as: {me.first_name}")
    print(f"✅ Session saved: {SESSION_PATH}.session")
    print("\n🚀 Run: docker-compose up -d")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())