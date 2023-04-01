import logging as standard_logging
import sys
from os import environ


class Logger:
    def log_prefix(self, severity: str) -> str:
        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_5_0/io_scene_vrm/__init__.py#L45-L46
        return f"[VRM Add-on:{severity}] "

    def __init__(self, logger: standard_logging.Logger) -> None:
        self.logger = logger
        self.level = logger.level

    def debug(self, message: str) -> None:
        self.logger.debug(self.log_prefix("Debug") + message)

    def info(self, message: str) -> None:
        self.logger.info(self.log_prefix("Info") + message)

    def warning(self, message: str) -> None:
        self.logger.warning(self.log_prefix("Warning") + message)

    def error(self, message: str) -> None:
        self.logger.error(self.log_prefix("Error") + message)

    def exception(self, message: str) -> None:
        self.logger.exception(self.log_prefix("Exception") + message)


# https://docs.python.org/3.7/library/logging.html#logging.getLogger
def get_logger(name: str) -> Logger:
    logger = standard_logging.getLogger(name)
    if environ.get("BLENDER_VRM_LOGGING_LEVEL_DEBUG") == "yes":
        logger.setLevel(standard_logging.DEBUG)
        handler = standard_logging.StreamHandler(sys.stdout)
        handler.setLevel(standard_logging.DEBUG)
        logger.addHandler(handler)
    return Logger(logger)
