from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path


def configure_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("sql_batch_export_tool")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        log_path = log_dir / f"app_{datetime.now():%Y%m%d}.log"
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
