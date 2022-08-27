import logging as standard_logging


class Logger:
    def log_prefix(self, severity: str) -> str:
        return f"[VRM Add-on:{severity}] "

    def __init__(self, name: str) -> None:
        self.logger = standard_logging.getLogger(name)

    def info(self, message: str) -> None:
        self.logger.info(self.log_prefix("Info") + message)

    def warning(self, message: str) -> None:
        self.logger.warning(self.log_prefix("Warning") + message)

    def error(self, message: str) -> None:
        self.logger.error(self.log_prefix("Error") + message)


def get_logger(name: str) -> Logger:
    return Logger(name)
