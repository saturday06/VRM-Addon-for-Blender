import logging as standard_logging
import sys
from collections.abc import Mapping
from os import environ
from types import TracebackType
from typing import TYPE_CHECKING, Optional, Union

# https://github.com/python/typeshed/issues/7855
if TYPE_CHECKING or sys.version_info >= (3, 11):
    LoggerAdapter = standard_logging.LoggerAdapter[standard_logging.Logger]
else:
    LoggerAdapter = standard_logging.LoggerAdapter


class VrmAddonLoggerAdapter(LoggerAdapter):
    def log(
        self,
        level: int,
        msg: object,
        *args: object,
        exc_info: Union[
            None,
            bool,
            Union[
                tuple[type[BaseException], BaseException, Optional[TracebackType]],
                tuple[None, None, None],
            ],
            BaseException,
        ] = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Optional[Mapping[str, object]] = None,
        **kwargs: object,
    ) -> None:
        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_20_36/src/io_scene_vrm/__init__.py#L132-L134
        level_name = standard_logging.getLevelName(level)
        super().log(
            level,
            f"[VRM Add-on:{level_name}] {msg}",
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )


# https://docs.python.org/3.7/library/logging.html#logging.getLogger
def get_logger(name: str) -> LoggerAdapter:
    logger = standard_logging.getLogger(name)
    if environ.get("BLENDER_VRM_LOGGING_LEVEL_DEBUG") == "yes":
        logger.setLevel(standard_logging.DEBUG)
    else:
        logger.setLevel(max(standard_logging.INFO, logger.getEffectiveLevel()))
    return VrmAddonLoggerAdapter(logger, {})
