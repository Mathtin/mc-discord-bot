#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###################################################
#........../\./\...___......|\.|..../...\.........#
#........./..|..\/\.|.|_|._.|.\|....|.c.|.........#
#......../....../--\|.|.|.|i|..|....\.../.........#
#        Mathtin (c)                              #
###################################################
#   Author: Daniel [Mathtin] Shiko                #
#   Copyright (c) 2020 <wdaniil@mail.ru>          #
#   This file is released under the MIT license.  #
###################################################

__author__ = 'Mathtin'

import logging
import discord, db as DB
from bot import Overlord, BotExtension
from util import *
import util.resources as res

#####################
# Ranking Extension #
#####################

log = logging.getLogger('ranking-extension')
class RankingExtension(BotExtension):

    async def update_rank(self, member: discord.Member) -> None:
        if self.bot.awaiting_sync():
            log.warn("Cannot update user rank: awaiting role sync")
            return False
        # Resolve user
        user = self.bot.s_users.get(member)
        # Skip non-existing users
        if user is None:
            log.warn(f'{qualified_name(member)} does not exist in db! Skipping user rank update!')
            return
        # Ignore inappropriate members
        if self.bot.s_ranking.ignore_member(member):
            return
        # Resolve roles to move
        roles_add, roles_del = self.bot.s_ranking.roles_to_add_and_remove(member, user)
        # Remove old roles
        if roles_del:
            log.info(f"Removing {qualified_name(member)}'s rank roles: {roles_del}")
            await member.remove_roles(*roles_del)
        # Add new roles
        if roles_add:
            log.info(f"Adding {qualified_name(member)}'s rank roles: {roles_add}")
            await member.add_roles(*roles_add)
        # Update user in db
        self.bot.s_users.update_member(member)
        return True

    async def update_all_ranks(self) -> None:
        if self.bot.awaiting_sync():
            log.error("Cannot update user ranks: awaiting role sync")
            return
        log.info(f'Updating user ranks')
        async for member in self.bot.guild.fetch_members(limit=None):
            if member.bot:
                continue
            await self.update_rank(member)
        log.info(f'Done updating user ranks')

    async def on_message(self, message: discord.Message) -> None:
        async with self.sync():
            await self.update_rank(message.author)

    async def on_message_edit(self, msg: DB.MessageEvent) -> None:
        async with self.sync():
            if self.bot.s_users.is_absent(msg.user):
                return
            member = await self.bot.guild.fetch_member(msg.user.did)
            await self.update_rank(member)

    async def on_message_delete(self, msg: DB.MessageEvent) -> None:
        async with self.sync():
            if self.bot.s_users.is_absent(msg.user):
                return
            member = await self.bot.guild.fetch_member(msg.user.did)
            await self.update_rank(member)
            
    async def on_vc_leave(self, member: discord.Member, channel: discord.VoiceChannel) -> None:
        async with self.sync():
            await self.update_rank(member)
            
    ############
    # Commands #
    ############

    @BotExtension.command("update_all_ranks", desciption="Fetches all members of guild and updates each rank")
    async def cmd_update_all_ranks(self, msg: discord.Message):
        async with self.sync():
            await msg.channel.send(res.get("messages.update_ranks_begin"))
            await self.update_all_ranks()
            await msg.channel.send(res.get("messages.done"))

    @BotExtension.command("update_rank", desciption="Update specified user rank")
    @member_mention_arg
    async def cmd_update_rank(self, msg: discord.Message, member: discord.Member):
        async with self.sync():
            await msg.channel.send(res.get("messages.update_rank_begin").format(member.mention))
            await self.update_rank(member)
            await msg.channel.send(res.get("messages.done"))

    