import re
from typing import List, Pattern
from loguru import logger


class ContentFilter:
    # Qonunchilik kalit so'zlari
    LEGAL_KEYWORDS: List[str] = [
        # Qonunlar
        "закон", "законодательство", "постановление", "приказ",
        "распоряжение", "решение", "регламент", "норматив",
        "положение", "изменени", "поправк", "введен",
        "вступает в силу", "утвержден", "опубликован",

        # Xaridlar
        "государственн", "госзакупк", "тендер", "конкурс",
        "аукцион", "заявк", "поставщик", "заказчик",
        "контракт", "договор", "закупк", "электронн",
        "торги", "лот", "реестр", "портал",

        # Qonunlar nomi
        "44-фз", "223-фз", "229-фз", "о публичных", "о закупках",

        # Vazirliklar
        "министерств", "ведомств", "нормативн", "правовой",

        # Iqtisodiyot
        "бюджет", "финансирование", "средства", "расходы",
        "экономия", "эффективность"
    ]

    # Shovqinli xabarlar
    NOISE_PATTERNS: List[str] = [
        r"^\s*подпиш",
        r"^\s*🔔\s*подпис",
        r"^\s*реклам",
        r"^\s*@\w+\s*$",
        r"^\s*https?://\S+\s*$",
        r"привет|здравствуй|добрый"
    ]

    def __init__(self):
        self._noise_patterns: List[Pattern] = [
            re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.NOISE_PATTERNS
        ]

    def is_relevant(self, text: str) -> bool:
        """Post davlat xaridlariga tegishlimi?"""
        if not text or not text.strip():
            return False

        lower = text.lower()

        # Shovqinni tekshirish
        for pattern in self._noise_patterns:
            if pattern.search(lower):
                logger.debug(f"Filter: noise pattern matched → skipping")
                return False

        # Kalit so'zlarni tekshirish
        for kw in self.LEGAL_KEYWORDS:
            if kw in lower:
                logger.debug(f"Filter: keyword '{kw}' found → relevant")
                return True

        logger.debug("Filter: no keywords found → not relevant")
        return False

    def is_russian(self, text: str) -> bool:
        """Matn rus tilidami?"""
        if not text:
            return False

        alpha = [c for c in text if c.isalpha()]
        if not alpha:
            return False

        cyrillic_count = sum(1 for c in alpha if '\u0400' <= c <= '\u04ff')
        ratio = cyrillic_count / len(alpha)

        return ratio >= 0.3