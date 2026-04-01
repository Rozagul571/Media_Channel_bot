import asyncio
import re
from typing import Optional
from openai import AsyncOpenAI
from loguru import logger
from core.config import settings

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

_RELEVANCE_SYSTEM = """Siz O'zbekiston davlat xaridlari mutaxassisisiz.
Faqat "HA" yoki "YOQ" deb javob bering.
HA: davlat xaridlari, tender, qonun, shartnoma, portal, byudjet, etkazib beruvchi.
YOQ: reklama, sport, ko'ngilochar, boshqa mavzular."""

_POST_SYSTEM = """Siz O'zbekiston davlat xaridlari sohasidagi professional media muharriri va tarjimonsiz.
Rus tilidagi davlat xaridlari ma'lumotini o'zbek tiliga o'girib Telegram uchun ideal post yarat.

QOIDALAR:
1. Faqat o'zbek tilida (lotin, rasmiy uslub).
2. Oddiy, tushunarli til.
3. Atamalar: zakupka=xarid/tender, zakazchik=buyurtmachi, postavshchik=yetkazib beruvchi,
   konkurs=tanlov, auktsion=kim oshdi savdosi, kontrakt=shartnoma, reestr=royxat.
4. Struktura: sarlavha + asosiy fikr + nima qilish kerak + muhim sana/raqam.
5. 3-5 ta emoji ishlat.
6. URL larni o'zgartirma.
7. Faqat tayyor post matni."""

_POST_WITH_LINK = """Telegram post:
{telegram_text}

Havola mazmuni:
{link_content}

O'zbek tilidagi ideal Telegram post yarat. 5-8 gapdan oshmasin.
Faqat post matnini yoz:"""

_POST_NO_LINK = """Quyidagi rus tilidagi matndan o'zbek tilidagi ideal Telegram post yarat.
Qisqa (3-6 gap), aniq, foydali. Sarlavha qoy.
Faqat post matnini yoz:

{text}"""


class Translator:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=GROQ_BASE_URL,
        )
        self._model = model
        logger.info(f"✅ Media Copywriter ishga tushdi | Model: {model}")

    async def is_relevant(self, text: str) -> bool:
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _RELEVANCE_SYSTEM},
                    {"role": "user", "content": text[:1000]},
                ],
                temperature=0.0,
                max_tokens=5,
            )
            answer = resp.choices[0].message.content.strip().upper()
            result = "HA" in answer
            logger.info(f"Relevantlik: {answer} → {'TEGISHLI' if result else 'SKIP'}")
            return result
        except Exception as exc:
            logger.warning(f"Relevantlik xato: {exc}")
            return True

    async def create_post(
        self,
        telegram_text: str,
        link_content: Optional[str] = None,
    ) -> str:
        if link_content and len(link_content) > 200:
            prompt = _POST_WITH_LINK.format(
                telegram_text=telegram_text[:1500],
                link_content=link_content[:2500],
            )
            logger.info("Post: telegram + link mazmunidan")
        else:
            prompt = _POST_NO_LINK.format(text=telegram_text[:3000])
            logger.info("Post: faqat telegram matnidan")

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                resp = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": _POST_SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=1024,
                )
                result = resp.choices[0].message.content.strip()
                logger.info(f"Post yaratildi: {len(result)} belgi")
                return result
            except Exception as exc:
                wait = settings.RETRY_DELAY_SECONDS * attempt
                logger.warning(f"Groq urinish {attempt}: {exc} — {wait}s")
                if attempt < settings.MAX_RETRIES:
                    await asyncio.sleep(wait)

        logger.error("Groq xato — asl matn qaytarildi")
        return telegram_text


def extract_urls(text: str) -> list[str]:
    pattern = re.compile(r"https?://[^\s\)\]\>\"\']+", re.IGNORECASE)
    return pattern.findall(text)
