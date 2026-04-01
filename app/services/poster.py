import asyncio
from typing import Optional

from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.types import Message
from loguru import logger

from core.config import settings


class ChannelPoster:
    def __init__(self, api_id: int, api_hash: str, bot_token: str, target_channel: str):
        self._target = target_channel
        self._bot_token = bot_token
        self._client = TelegramClient(
            session=settings.get_bot_session_path(),
            api_id=api_id,
            api_hash=api_hash,
            flood_sleep_threshold=60
        )
        self._started = False

    async def start(self) -> None:
        """Start bot"""
        if not self._started:
            await self._client.start(bot_token=self._bot_token)
            self._started = True
            me = await self._client.get_me()
            logger.info(f"✅ Bot connected: @{me.username}")

    async def stop(self) -> None:
        """Stop bot"""
        if self._started:
            await self._client.disconnect()
            self._started = False
            logger.info("✅ Bot disconnected")

    async def post(self, text: str) -> bool:
        """Send post to channel"""
        await self.start()

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                result: Message = await self._client.send_message(
                    entity=self._target,
                    message=text,
                    parse_mode="markdown",
                    link_preview=True
                )
                logger.info(f"✅ Posted to {self._target} (ID: {result.id})")
                return True

            except FloodWaitError as e:
                wait = e.seconds + 5
                logger.warning(f"⏳ Flood wait: {wait}s")
                await asyncio.sleep(wait)

            except RPCError as e:
                logger.error(f"❌ RPC error: {e}")
                if attempt < settings.MAX_RETRIES:
                    await asyncio.sleep(settings.RETRY_DELAY_SECONDS * attempt)

            except Exception as e:
                logger.error(f"❌ Post error: {e}")
                if attempt < settings.MAX_RETRIES:
                    await asyncio.sleep(settings.RETRY_DELAY_SECONDS * attempt)

        return False