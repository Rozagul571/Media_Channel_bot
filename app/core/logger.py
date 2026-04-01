import sys
from pathlib import Path
from loguru import logger

ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "pipeline.log"


def setup_logging(level: str = "INFO") -> None:
    logger.remove()

    logger.add(
        sys.stdout,
        level=level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
    )

    logger.add(
        str(LOG_FILE),
        level=level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{line} — {message}",
    )

    logger.info(f"✅ Logging initialized: {LOG_FILE}")