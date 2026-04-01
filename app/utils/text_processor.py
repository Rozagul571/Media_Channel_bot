import re
from typing import Optional, Tuple


class TextProcessor:
    """Matnni tozalash va formatlash"""

    @staticmethod
    def clean_text(text: str) -> str:
        """Matnni tozalash"""
        if not text:
            return ""

        # Ortiqcha bo'shliqlarni tozalash
        text = re.sub(r'\s+', ' ', text)

        # Emoji va maxsus belgilarni saqlab qolish
        text = text.strip()

        return text

    @staticmethod
    def extract_summary(text: str, max_length: int = 200) -> str:
        """Matndan qisqa xulosa olish (birinchi gap)"""
        if not text:
            return ""

        # Birinchi gapni olish
        sentences = re.split(r'[.!?]+', text)
        if sentences:
            summary = sentences[0].strip()
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            return summary

        return text[:max_length] + "..." if len(text) > max_length else text

    @staticmethod
    def split_text(text: str, max_length: int = 4000) -> list:
        """Uzun matnni bo'laklarga ajratish"""
        if len(text) <= max_length:
            return [text]

        parts = []
        while text:
            if len(text) <= max_length:
                parts.append(text)
                break

            # Eng yaqin gap tugashini topish
            split_point = text.rfind('. ', 0, max_length)
            if split_point == -1:
                split_point = text.rfind(' ', 0, max_length)
            if split_point == -1:
                split_point = max_length

            parts.append(text[:split_point + 1])
            text = text[split_point + 1:].lstrip()

        return parts

    @staticmethod
    def remove_urls(text: str) -> Tuple[str, list]:
        """Matndan URL larni ajratish"""
        urls = re.findall(r'https?://[^\s\)\]\>\"\']+', text, re.IGNORECASE)
        clean = re.sub(r'https?://[^\s\)\]\>\"\']+', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()

        return clean, urls