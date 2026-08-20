# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import logging
import sys
import traceback
from collections.abc import Mapping
from os import environ
from types import TracebackType
from typing import TYPE_CHECKING, Optional, Union

import bpy

# https://github.com/python/typeshed/issues/7855
if TYPE_CHECKING or sys.version_info >= (3, 11):
    LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    LoggerAdapter = logging.LoggerAdapter


class VrmAddonLoggerAdapter(LoggerAdapter):
    def __init__(self, logger: logging.Logger, extra: Mapping[str, object]) -> None:
        super().__init__(logger, extra)
        self._log_output_match_counts: dict[str, int] = {}

    def register_log_output_match(self, pattern: str) -> None:
        self._log_output_match_counts[pattern] = 0

    def get_log_output_match_count(self, pattern: str) -> int:
        return self._log_output_match_counts.get(pattern, 0)

    def clear_log_output_match_count(self) -> None:
        self._log_output_match_counts.clear()

    def log(
        self,
        level: int,
        msg: object,
        *args: object,
        exc_info: Union[
            bool,
            Union[
                tuple[type[BaseException], BaseException, Optional[TracebackType]],
                tuple[None, None, None],
            ],
            BaseException,
            None,
        ] = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Optional[Mapping[str, object]] = None,
        **kwargs: object,
    ) -> None:
        level_name = logging.getLevelName(level)
        if self._log_output_match_counts:
            try:
                formatted_message = str(msg) % args if args else str(msg)
            except (TypeError, ValueError):
                formatted_message = str(msg)
            if exc_info is True:
                formatted_message += f"\n{traceback.format_exc()}"
            elif exc_info:
                formatted_message += f"\n{exc_info}"
            for pattern, match_count in self._log_output_match_counts.items():
                if pattern in formatted_message:
                    self._log_output_match_counts[pattern] = match_count + 1
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
def get_logger(name: str) -> VrmAddonLoggerAdapter:
    logger = logging.getLogger(name)
    if bpy.app.debug or environ.get("BLENDER_VRM_LOGGING_LEVEL_DEBUG") == "yes":
        logger.setLevel(min(logging.DEBUG, logger.getEffectiveLevel()))
    else:
        logger.setLevel(max(logging.INFO, logger.getEffectiveLevel()))
    return VrmAddonLoggerAdapter(logger, {})
