import asyncio
import signal
import sys

from core.config import settings
from core.logger import setup_logging
from services.translator import Translator
setup_logging(settings.LOG_LEVEL)

from loguru import logger
from services.database import Database
from services.filter import ContentFilter
from services.poster import ChannelPoster
from services.monitor import ChannelMonitor


def build_pipeline():
    """Pipeline komponentlarini yaratish"""
    db = Database(url=settings.get_database_url())
    translator = Translator(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL
    )
    poster = ChannelPoster(
        api_id=settings.TELEGRAM_API_ID,
        api_hash=settings.TELEGRAM_API_HASH,
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        target_channel=settings.TARGET_CHANNEL
    )
    monitor = ChannelMonitor(
        db=db,
        content_filter=ContentFilter(),
        translator=translator,
        poster=poster
    )
    return monitor, db, poster


async def main():
    """Asosiy funksiya"""
    logger.info("=" * 60)
    logger.info("🚀  TENDERZON MEDIA - Professional Content Pipeline")
    logger.info("=" * 60)
    logger.info(f"📥 Source: @{settings.SOURCE_CHANNEL}")
    logger.info(f"📤 Target: {settings.TARGET_CHANNEL}")
    logger.info(f"🤖 Model: {settings.OPENAI_MODEL}")
    logger.info(f"⏱️  Polling: {settings.POLL_INTERVAL_SECONDS}s")
    logger.info("=" * 60)

    monitor, db, poster = build_pipeline()
    await db.init()

    loop = asyncio.get_running_loop()

    async def shutdown(sig_name):
        logger.warning(f"🛑 {sig_name} received - shutting down...")
        await poster.stop()
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s.name)))

    try:
        await monitor.run()
    except asyncio.CancelledError:
        pass
    finally:
        await poster.stop()
        await db.close()
        logger.info("✅ Pipeline stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)