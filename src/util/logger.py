#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2021-present Daniel [Mathtin] Shiko <wdaniil@mail.ru>
Project: Minecraft Discord Bot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__author__ = "Mathtin"

import logging.config

from .config import ConfigView


#################
# Logger Config #
#################

class LogFileConfig(ConfigView):
    """
    file {
        filename = "..."
        maxBytes = ...
        backupCount = ...
    }
    """
    filename: str = "overlord-bot.log"
    maxBytes: int = 1048576
    backupCount: int = 10


class DiscordLogConfig(ConfigView):
    """
    discord {
        channel = ...
    }
    """
    channel: int = 0


class LoggerRootConfig(ConfigView):
    """
    logger {
        format = "..."
        level = "..."
        file : LogFileConfig
        discord : DiscordLogConfig
    }
    """
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    level: str = "INFO"
    file: LogFileConfig = LogFileConfig()
    discord: DiscordLogConfig = DiscordLogConfig()


def update_config(config: LoggerRootConfig) -> None:
    config_dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": config.format
            }
        },
        "handlers": {
            "console": {
                "level": config.level,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr"
            },
            "file": {
                "level": config.level,
                "formatter": "standard",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": config.file.filename,
                "maxBytes": config.file.maxBytes,
                "backupCount": config.file.backupCount
            }
        },
        "root": {
            "handlers": [
                "console",
                "file"
            ],
            "level": config.level
        }
    }
    logging.config.dictConfig(config_dict)
