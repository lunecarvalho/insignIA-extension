from loguru import logger as _logger
import sys


_logger.remove()
_logger.add(sys.stdout, level="INFO", format="{time} {level} {message}")

logger = _logger
