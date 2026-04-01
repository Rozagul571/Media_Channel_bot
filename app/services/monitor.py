import asyncio
from typing import Optional

from telethon import TelegramClient, events
from telethon.tl.types import Message
from telethon.errors import FloodWaitError, RPCError
from loguru import logger

from core.config import settings
from services.database import Database
from services.filter import ContentFilter
from services.translator import Translator
from services.poster import ChannelPoster
from utils.link_extractor import LinkExtractor


class ChannelMonitor:
    def __init__(
        self,
        db: Database,
        content_filter: ContentFilter,
        translator: Translator,
        poster: ChannelPoster
    ):
        self._db = db
        self._filter = content_filter
        self._translator = translator
        self._poster = poster
        self._link_extractor = LinkExtractor()
        self._running = False

        # User client
        self._client = TelegramClient(
            session=settings.get_session_path(),
            api_id=settings.TELEGRAM_API_ID,
            api_hash=settings.TELEGRAM_API_HASH,
            flood_sleep_threshold=60,
            connection_retries=5
        )

    async def start(self) -> None:
        """Start monitoring"""
        await self._client.start(phone=settings.TELEGRAM_PHONE)
        me = await self._client.get_me()
        logger.info(f"✅ User connected: @{me.username or me.first_name}")

    async def stop(self) -> None:
        """Stop monitoring"""
        self._running = False
        if self._client and self._client.is_connected():
            await self._client.disconnect()
        logger.info("✅ Monitor stopped")

    async def run(self) -> None:
        """Run monitor with polling"""
        self._running = True
        await self.start()

        logger.info(f"👀 Monitoring: @{settings.SOURCE_CHANNEL}")
        logger.info(f"⏱️ Polling every {settings.POLL_INTERVAL_SECONDS}s")

        last_message_id = 0

        while self._running:
            try:
                # Get channel
                try:
                    channel = await self._client.get_entity(settings.SOURCE_CHANNEL)
                except Exception as e:
                    logger.error(f"❌ Cannot get channel: {e}")
                    await asyncio.sleep(60)
                    continue

                # Get messages
                messages = await self._client.get_messages(
                    channel,
                    limit=settings.FETCH_LIMIT
                )

                # Process newest first
                for msg in messages:
                    if msg.id <= last_message_id:
                        continue

                    if await self._db.is_processed(msg.id):
                        last_message_id = max(last_message_id, msg.id)
                        continue

                    await self._process_message(msg)
                    last_message_id = max(last_message_id, msg.id)

                # Wait for next poll
                for _ in range(settings.POLL_INTERVAL_SECONDS):
                    if not self._running:
                        break
                    await asyncio.sleep(1)

            except FloodWaitError as e:
                logger.warning(f"⏳ Flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds + 5)
            except Exception as e:
                logger.error(f"❌ Polling error: {e}")
                await asyncio.sleep(30)

    async def _process_message(self, msg: Message) -> None:
        """Process single message"""
        msg_id = msg.id
        text = msg.text or msg.message or ""
        link = self._link_extractor.extract(msg)

        logger.info(f"📨 [#{msg_id}] Processing | {len(text)} chars")

        # Skip empty
        if not text and not link:
            logger.info(f"⏭️ [#{msg_id}] Empty message")
            return

        # Check length
        if len(text.strip()) < settings.MIN_TEXT_LENGTH and not link:
            logger.info(f"⏭️ [#{msg_id}] Too short ({len(text)} chars)")
            await self._db.save(
                message_id=msg_id,
                channel=settings.SOURCE_CHANNEL,
                original_text=text,
                link=link,
                is_relevant=False,
                skip_reason="too_short"
            )
            return

        # Russian check
        if text and not self._filter.is_russian(text):
            logger.info(f"⏭️ [#{msg_id}] Not Russian")
            await self._db.save(
                message_id=msg_id,
                channel=settings.SOURCE_CHANNEL,
                original_text=text,
                link=link,
                is_relevant=False,
                skip_reason="not_russian"
            )
            return

        # Keyword filter
        if text and not self._filter.is_relevant(text):
            logger.info(f"⏭️ [#{msg_id}] No keywords")
            await self._db.save(
                message_id=msg_id,
                channel=settings.SOURCE_CHANNEL,
                original_text=text,
                link=link,
                is_relevant=False,
                skip_reason="no_keywords"
            )
            return

        # AI relevance check
        if text and not await self._translator.is_relevant(text):
            logger.info(f"⏭️ [#{msg_id}] AI: not relevant")
            await self._db.save(
                message_id=msg_id,
                channel=settings.SOURCE_CHANNEL,
                original_text=text,
                link=link,
                is_relevant=False,
                skip_reason="ai_not_relevant"
            )
            return

        # Translate and create media post
        try:
            media_post = await self._translator.create_post(text, link)
            logger.info(f"🔄 [#{msg_id}] Translation + Media post created")
        except Exception as e:
            logger.error(f"❌ [#{msg_id}] Translation failed: {e}")
            await self._db.save(
                message_id=msg_id,
                channel=settings.SOURCE_CHANNEL,
                original_text=text,
                link=link,
                error=f"translation_failed: {str(e)[:100]}"
            )
            return

        # Post to channel
        try:
            posted = await self._poster.post(media_post)
            logger.info(f"📤 [#{msg_id}] Posted: {posted}")
        except Exception as e:
            logger.error(f"❌ [#{msg_id}] Posting failed: {e}")
            posted = False

        # Save to database
        await self._db.save(
            message_id=msg_id,
            channel=settings.SOURCE_CHANNEL,
            original_text=text,
            translated_text=translated,
            link=link,
            is_relevant=True,
            posted=posted,
            error=None if posted else "posting_failed"
        )

        logger.info(f"✅ [#{msg_id}] Complete | Posted: {posted}")