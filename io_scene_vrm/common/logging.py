import logging as standard_logging


class Logger:
    def log_prefix(self, severity: str) -> str:
        # https://github.com/saturday06/VRM_Addon_for_Blender/blob/2_5_0/io_scene_vrm/__init__.py#L45-L46
        return f"[VRM Add-on:{severity}] "

    def __init__(self, name: str) -> None:
        self.logger = standard_logging.getLogger(name)

    def info(self, message: str) -> None:
        self.logger.info(self.log_prefix("Info") + message)

    def warning(self, message: str) -> None:
        self.logger.warning(self.log_prefix("Warning") + message)

    def error(self, message: str) -> None:
        self.logger.error(self.log_prefix("Error") + message)

    def exception(self, message: str) -> None:
        self.logger.exception(self.log_prefix("Exception") + message)


def get_logger(name: str) -> Logger:
    return Logger(name)
