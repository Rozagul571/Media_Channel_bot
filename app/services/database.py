from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Boolean, Integer, select, desc
from loguru import logger
from core.config import settings


class Base(DeclarativeBase):
    pass


class ProcessedMessage(Base):
    __tablename__ = "processed_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    channel: Mapped[str] = mapped_column(String(128), nullable=False)
    original_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    translated_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=True)
    posted: Mapped[bool] = mapped_column(Boolean, default=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skip_reason: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Database:
    def __init__(self, url: str) -> None:
        self._engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        self._sessions = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    async def init(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database ready")

    async def close(self) -> None:
        await self._engine.dispose()
        logger.info("✅ Database closed")

    async def is_processed(self, message_id: int) -> bool:
        async with self._sessions() as s:
            result = await s.execute(select(ProcessedMessage).where(ProcessedMessage.message_id == message_id))
            return result.scalar_one_or_none() is not None

    async def save(self, **kwargs) -> None:
        async with self._sessions() as s:
            exists = await s.execute(
                select(ProcessedMessage).where(ProcessedMessage.message_id == kwargs.get("message_id"))
            )
            if exists.scalar_one_or_none():
                return

            msg = ProcessedMessage(
                message_id=kwargs.get("message_id"),
                channel=kwargs.get("channel", ""),
                original_text=kwargs.get("original_text", "")[:5000],
                translated_text=kwargs.get("translated_text", "")[:5000],
                summary=kwargs.get("summary", "")[:1000],
                link=kwargs.get("link", ""),
                is_relevant=kwargs.get("is_relevant", True),
                posted=kwargs.get("posted", False),
                posted_at=datetime.utcnow() if kwargs.get("posted") else None,
                error=kwargs.get("error"),
                skip_reason=kwargs.get("skip_reason")
            )
            s.add(msg)
            await s.commit()

    async def get_stats(self) -> Dict:
        async with self._sessions() as s:
            rows = (await s.execute(select(ProcessedMessage))).scalars().all()

        return {
            "total": len(rows),
            "posted": sum(1 for r in rows if r.posted),
            "skipped": sum(1 for r in rows if r.skip_reason),
            "errors": sum(1 for r in rows if r.error),
            "last_24h": sum(1 for r in rows if r.created_at > datetime.utcnow().replace(hour=0, minute=0, second=0))
        }