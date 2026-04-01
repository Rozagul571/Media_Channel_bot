"""
Link Extractor - Telegram xabarlardan havolalarni ajratib olish
"""

import re
from typing import Optional, List
from urllib.parse import urlparse

from telethon.tl.types import Message, MessageEntityUrl, MessageEntityTextUrl
from loguru import logger


class LinkExtractor:
    """Telegram xabarlardan havolalarni ajratib olish"""

    @staticmethod
    def extract(message: Message) -> Optional[str]:
        """Xabardan birinchi havolani olish"""

        # 1. Text URL entity orqali
        for entity in message.entities or []:
            if isinstance(entity, MessageEntityTextUrl) and entity.url:
                return LinkExtractor._clean_url(entity.url)

            if isinstance(entity, MessageEntityUrl):
                text = message.text or ""
                url = text[entity.offset:entity.offset + entity.length]
                return LinkExtractor._clean_url(url)

        # 2. Button URL orqali
        if message.reply_markup:
            try:
                for row in message.reply_markup.rows:
                    for button in row.buttons:
                        if hasattr(button, "url") and button.url:
                            return LinkExtractor._clean_url(button.url)
            except Exception:
                pass

        # 3. Regex orqali matndan
        text = message.text or message.message or ""
        urls = re.findall(r'https?://[^\s\)\]\>\"\']+', text, re.IGNORECASE)

        if urls:
            return LinkExtractor._clean_url(urls[0])

        return None

    @staticmethod
    def extract_all(message: Message) -> List[str]:
        """Xabardan barcha havolalarni olish"""
        urls = []
        text = message.text or message.message or ""

        # Regex orqali barcha URL larni olish
        found = re.findall(r'https?://[^\s\)\]\>\"\']+', text, re.IGNORECASE)
        urls.extend([LinkExtractor._clean_url(u) for u in found])

        # Entity orqali
        for entity in message.entities or []:
            if isinstance(entity, MessageEntityTextUrl) and entity.url:
                if entity.url not in urls:
                    urls.append(LinkExtractor._clean_url(entity.url))

        return urls

    @staticmethod
    def _clean_url(url: str) -> str:
        """URL ni tozalash"""
        url = url.strip()
        if url.endswith((')', ']', '>', '"', "'", '.')):
            url = url[:-1]
        return url

    @staticmethod
    def is_telegram_link(url: str) -> bool:
        """Telegram havolasimi?"""
        parsed = urlparse(url)
        return 't.me' in parsed.netloc