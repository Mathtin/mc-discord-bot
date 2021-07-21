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

import logging
import re

import discord

from overlord.extension import BotExtension
from services import UserService, RoleService
from util.resources import STRINGS as R

log = logging.getLogger('utility-extension')


#####################
# Utility Extension #
#####################

class UtilityExtension(BotExtension):

    __extname__ = '🛠 Utility Extension'
    __description__ = 'Basic utility commands collection'
    __color__ = 0xa83fc8

    PAGE_NUM_REGEX = re.compile(r'\[(\d+)/(\d+)]')

    #########
    # Props #
    #########

    @property
    def s_roles(self) -> RoleService:
        return self.bot.services.role

    @property
    def s_users(self) -> UserService:
        return self.bot.services.user

    ###########
    # Methods #
    ###########

    async def switch_help_page(self, emoji, msg: discord.Message):
        embed = msg.embeds[0]
        page = int(re.search(UtilityExtension.PAGE_NUM_REGEX, embed.author.name).group(1))
        if emoji == u'⏮':
            page = 1
        elif emoji == u'⏭':
            page = len(self.bot.extensions)
        elif emoji == u'◀':
            page -= 1
        elif emoji == u'▶':
            page += 1
        else:
            return
        ext = self.bot.resolve_extension(page)
        if ext is not None:
            i = self.bot.extension_idx(ext)
            e_count = len(self.bot.extensions)
            await msg.edit(embed=ext.help_embed(f"Overlord Help page [{i + 1}/{e_count}]"))

    #########
    # Hooks #
    #########

    async def on_control_reaction_add(self, _, message: discord.Message,
                                      emoji: discord.PartialEmoji):
        if not message.embeds or message.author != self.bot.me or not emoji.is_unicode_emoji():
            return

        emoji = emoji.name
        embed = message.embeds[0]

        if 'Overlord Help page' in embed.author.name:
            await self.switch_help_page(emoji, message)

    async def on_control_reaction_remove(self, _, message: discord.Message,
                                         emoji: discord.PartialEmoji):
        if not message.embeds or message.author != self.bot.me or not emoji.is_unicode_emoji():
            return

        emoji = emoji.name
        embed = message.embeds[0]

        if 'Overlord Help page' in embed.author.name:
            await self.switch_help_page(emoji, message)

    ############
    # Commands #
    ############

    @BotExtension.command("help", description="Help pages")
    async def cmd_help(self, msg: discord.Message, opt_page_or_ext_name: str = '1'):
        ext = self.bot.resolve_extension(opt_page_or_ext_name)
        if ext is None:
            await msg.channel.send("No such help page")
            return
        i = self.bot.extension_idx(ext)
        e_count = len(self.bot.extensions)
        help_msg = await msg.channel.send(embed=ext.help_embed(f"Overlord Help page [{i + 1}/{e_count}]"))
        await help_msg.add_reaction(u'⏮')
        await help_msg.add_reaction(u'◀')
        await help_msg.add_reaction(u'▶')
        await help_msg.add_reaction(u'⏭')

    @BotExtension.command("ping", description="Checks bot state")
    async def cmd_ping(self, msg: discord.Message):
        if self.bot.sync().locked():
            await msg.channel.send(R.MESSAGE.STATUS.BUSY)
        else:
            await msg.channel.send(R.MESSAGE.STATUS.PING)

    @BotExtension.command("sync_roles", description="Synchronize db data with guild data in terms of users and roles")
    async def cmd_sync_roles(self, msg: discord.Message):
        progress = self.new_progress(f'{R.MESSAGE.STATUS.SYNC_USERS} {R.NAME.COMMON.PROGRESS.lower()}')
        progress.add_step(R.MESSAGE.STATUS.SYNC_USERS)
        await progress.start(msg.channel)
        try:
            await self.bot.sync_users()
        except Exception:
            await progress.finish(failed=True)
            raise
        await progress.finish()

    @BotExtension.command("switch_lang", description="Switch bot language")
    async def cmd_switch_lang(self, msg: discord.Message, lang: str):
        R.switch_lang(lang)
        await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("status", description="Prints bot state summary")
    async def extension_status(self, msg: discord.Message):
        report = f'{R.NAME.COMMON.GUILD}: {self.bot.guild.name}\n'
        report += f'{R.NAME.COMMON.MAINTAINER}: {self.bot.maintainer.mention}\n'
        report += f'{R.NAME.COMMON.CONTROL_CHANNEL}: {self.bot.control_channel.mention}\n'
        if self.bot.log_channel is not None:
            report += f'{R.NAME.COMMON.LOG_CHANNEL}: {self.bot.log_channel.mention}\n'
        embed = self.bot.new_info_report(R.EMBED.TITLE.SUMMARY, report)
        # Report extensions
        ext_details = [f'✅ {ext.name}' if ext.enabled else f'❌ {ext.name}' for ext in self.bot.extensions]
        embed.add_field(name=R.EMBED.TITLE.EXTENSION_STATUS_LIST, value='\n'.join(ext_details), inline=False)
        await msg.channel.send(embed=embed)

