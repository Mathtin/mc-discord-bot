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

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from util import ConfigView, ConfigManager
from util.logger import LoggerRootConfig, update_config as update_logger
from db import DBConnection
from services.provider import ServiceProvider
from overlord import OverlordRootConfig
from overlord.bot import Overlord
from extensions import UtilityExtension, RankingExtension, ConfigExtension, WhitelistExtension
from extensions import RankingConfig, WhitelistConfig


class ExtensionsConfig(ConfigView):
    """
    extension {
        rank      : RankingRootConfig
        whitelist : WhitelistConfig
    }
    """
    rank: RankingConfig = RankingConfig()
    whitelist: WhitelistConfig = WhitelistConfig()


class RootConfig(ConfigView):
    """
    logger      : LoggerRootConfig
    bot         : OverlordRootConfig
    extension   : ExtensionsConfig
    """
    logger: LoggerRootConfig = LoggerRootConfig()
    bot: OverlordRootConfig = OverlordRootConfig()
    extension: ExtensionsConfig = ExtensionsConfig()


class Configuration(ConfigManager):
    config: RootConfig

    def alter(self, raw: str) -> None:
        super().alter(raw)
        update_logger(self.config.logger)


def main(argv):

    # Parse arguments
    parser = argparse.ArgumentParser(description='Minecraft Discord Bot')
    parser.add_argument('-c', '--config', nargs='?', type=str, default='mc-bot.cfg', help='config path')
    args = parser.parse_args(argv[1:])

    # Load config
    cnf_manager = Configuration(args.config)

    # Init database
    url = os.getenv('DATABASE_ACCESS_URL')
    connection = DBConnection(url)
    services = ServiceProvider(connection)

    # Init bot
    discord_bot = Overlord(cnf_manager, services)

    # Init extensions
    extras_ext = UtilityExtension(bot=discord_bot)
    conf_ext = ConfigExtension(bot=discord_bot)
    wl_ext = WhitelistExtension(bot=discord_bot)
    # ranking_ext = RankingExtension(bot=discord_bot)

    # Attach extensions
    discord_bot.extend(extras_ext)
    discord_bot.extend(conf_ext)
    discord_bot.extend(wl_ext)
    # discord_bot.extend(ranking_ext)

    # Start bot
    discord_bot.run()

    return 0


if __name__ == "__main__":
    res = main(sys.argv)
    exit(res)
