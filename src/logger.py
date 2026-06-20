from config_loader import load_config
from dotenv import load_dotenv

import logging
import sys
import os



LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str) -> None:
    
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.setLevel(log_level.upper())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    load_dotenv()
    log_level = os.getenv("LOG_LEVEL") or config["logging"]["level"]
    setup_logging(log_level)
    return logging.getLogger(name)
