"""
Logger centralise avec suivi des lignes traitees.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from config.settings import LOGS_DIR


def setup_logger(name: str = "mexora_etl") -> logging.Logger:
    """Configure le logger fichier + console."""
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")

    log_file = LOGS_DIR / f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def log_transform(logger: logging.Logger, rule: str, before: int, after: int, detail: str = ""):
    """Log standardise pour une transformation."""
    removed = before - after
    msg = f"[TRANSFORM] {rule} : {removed} ligne(s) supprimee(s) / affectee(s)"
    if detail:
        msg += f" — {detail}"
    msg += f" ({before} -> {after})"
    logger.info(msg)
