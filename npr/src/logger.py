"""Logging configuration module"""
import logging
import sys
from pathlib import Path

try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False


def setup_logger(name: str, log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    """Setup application logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(
        Path(log_dir) / f"{name}.log"
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Use JSON formatter if available, otherwise use standard formatter
    if JSON_LOGGER_AVAILABLE:
        json_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        file_handler.setFormatter(json_formatter)
    else:
        file_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    
    return logger

