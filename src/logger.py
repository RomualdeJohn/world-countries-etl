from config_loader import load_config
from dotenv import load_dotenv

import logging
import sys
import os


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str) -> None:
    """
    Configure the root logger once so all modules share the same format.

    Skips setup if handlers already exist, avoiding duplicate log lines.

    Input:
        log_level (str): logging level name applied to the root logger.
            Sample: "INFO"

    Result:
        None
    """
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.setLevel(log_level.upper())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger after applying project logging settings.

    Reads LOG_LEVEL from the environment when set; otherwise uses config logging.level.

    Input:
        name (str): logger name, usually __name__ of the calling module.
            Sample: "extract"

    Result:
        logging.Logger: configured logger for the given name.
            Sample: <Logger extract (INFO)>
    """
    load_dotenv()
    env = os.getenv("APP_ENV", "dev")
    config = load_config(env)
    log_level = os.getenv("LOG_LEVEL") or config["logging"]["level"]
    setup_logging(log_level)
    return logging.getLogger(name)
