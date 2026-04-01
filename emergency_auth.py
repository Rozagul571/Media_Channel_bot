import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

async def main():
    print("📱 Telefonga kod so'ralmoqda...")
    
    client = TelegramClient("data/user_session", API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        # KOD YUBORISH
        await client.send_code_request(PHONE)
        print("\n✅ Kod yuborildi! Telefoningizni tekshiring")
        print("   SMS kelmasa - QO'NG'IROQ kuting...")
        print("   Qo'ng'iroq orqali kod keladi\n")
        
        code = input("📲 5 raqamli kodni kiriting: ").strip()
        
        try:
            await client.sign_in(PHONE, code)
            print("✅ Muvaffaqiyatli kirdi!")
        except Exception as e:
            print(f"❌ Xato: {e}")
    
    me = await client.get_me()
    print(f"✅ Xush kelibsiz, {me.first_name}!")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
