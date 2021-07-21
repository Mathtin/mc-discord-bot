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
from typing import Optional, List, Tuple

import discord

import db as DB
from services import UserService
from services.role import RoleService
from util import ConfigView, FORMATTERS
from util.exceptions import InvalidConfigException
from util.extbot import filter_roles, is_role_applied, qualified_name, is_text_channel
from util.resources import STRINGS as R
from overlord.extension import BotExtension

log = logging.getLogger('ranking-extension')


##################
# Ranking Config #
##################


class RankingConfig(ConfigView):
    """
    rank {
        required = [...]
    }
    """
    required: List[str] = []


#####################
# Ranking Extension #
#####################

class RankingExtension(BotExtension):
    __extname__ = '🎖 Ranking Extension'
    __description__ = 'Player ranking system'
    __color__ = 0xc84e3f

    config: RankingConfig = RankingConfig()
    log_channel: discord.TextChannel

    #########
    # Props #
    #########

    @property
    def s_users(self) -> UserService:
        return self.bot.services.user

    @property
    def s_roles(self) -> RoleService:
        return self.bot.services.role

    @property
    def ranks(self) -> List[str]:
        return []

    @property
    def required_roles(self) -> List[str]:
        return self.config.required

    ###########
    # Methods #
    ###########

    async def find_user_rank_name(self, user: DB.User) -> Optional[str]:
        return None

    def ignore_member(self, member: discord.Member) -> bool:
        return len(filter_roles(member, self.required_roles)) == 0

    async def roles_to_add_and_remove(self, member: discord.Member, user: DB.User) -> \
            Tuple[List[discord.Role], List[discord.Role]]:
        rank_roles = [self.s_roles.get_d_role(r) for r in self.ranks]
        applied_rank_roles = filter_roles(member, rank_roles)
        effective_rank_name = await self.find_user_rank_name(user)
        ranks_to_remove = [r for r in applied_rank_roles if r.name != effective_rank_name]
        ranks_to_apply = []
        if effective_rank_name is not None and not is_role_applied(member, effective_rank_name):
            ranks_to_apply.append(self.s_roles.get_d_role(effective_rank_name))
        return ranks_to_apply, ranks_to_remove

    #################
    # Async Methods #
    #################

    async def update_rank(self, member: discord.Member):
        pass

    async def update_all_ranks(self) -> None:
        pass

    #########
    # Hooks #
    #########

    async def on_config_update(self) -> None:
        self.config = self.bot.get_config_section(RankingConfig)
        if self.config is None:
            raise InvalidConfigException("RankingRootConfig section not found", "root")
        # Check rank roles
        for i, role_name in enumerate(self.required_roles):
            if self.s_roles.get_d_role(role_name) is None:
                raise InvalidConfigException(f"No such role: '{role_name}'", self.config.path(f"required[{i}]"))

    ############
    # Commands #
    ############

    @BotExtension.command("update_all_ranks", description="Fetches all members of guild and updates each rank")
    async def cmd_update_all_ranks(self, msg: discord.Message):
        async with self.sync():
            await msg.channel.send(R.MESSAGE.STATUS.UPDATING_RANKS)
            await self.update_all_ranks()
            await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("update_rank", description="Update specified user rank")
    async def cmd_update_rank(self, msg: discord.Message, member: discord.Member):
        async with self.sync():
            await msg.channel.send(f'{R.MESSAGE.STATUS.UPDATING_RANK}: {member.mention}')
            await self.update_rank(member)
            await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("list_ranks", description="List all configured ranks")
    async def cmd_list_ranks(self, msg: discord.Message):
        desc = f'Configured ranks list'
        embed = self.bot.new_embed(f"🎖 Ranks", desc, header="Overlord Ranking", color=self.__color__)
        for name, rank in self.ranks.items():
            lines = [f'{p}: {FORMATTERS[p](v)}' for p, v in rank]
            rank_s = '\n'.join(lines)
            embed.add_field(name=name, value=rank_s, inline=True)
        await msg.channel.send(embed=embed)

    @BotExtension.command("add_rank", description="Creates new user rank")
    async def cmd_add_rank(self, msg: discord.Message, role: discord.Role, weight: int, membership: int, msg_count: int,
                           vc_time: int):
        # Check already existed rank for specified role 
        if role.name in self.ranks:
            await msg.channel.send(R.MESSAGE.ERROR_OTHER.DUPLICATE_RANK)
            return
        # Check weight uniqueness
        ranks_weights = {r.weight: n for n, r in self.ranks.items()}
        if weight in ranks_weights:
            await msg.channel.send(f'{R.MESSAGE.ERROR_OTHER.DUPLICATE_WEIGHT}: {ranks_weights[weight]}')
            return
        # Add new rank
        rank = {}
        rank.weight = weight
        rank.membership = membership
        rank.messages = msg_count
        rank.vc = vc_time
        self.ranks[role.name] = rank
        # Update config properly
        err = await self.bot.safe_update_config()
        if not err:
            await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)
        else:
            details = str(err) + '\n' + 'Config reverted'
            embed = self.bot.new_error_report(err.__class__.__name__, details)
            await msg.channel.send(embed=embed)

    @BotExtension.command("remove_rank", description="Update specified user rank")
    async def cmd_remove_rank(self, msg: discord.Message, role: discord.Role):
        if role.name not in self.ranks:
            await msg.channel.send(R.ERROR_OTHER.UNKNOWN_RANK)
            return
        del self.ranks[role.name]
        # Update config properly
        err = await self.bot.safe_update_config()
        if not err:
            await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)
        else:
            details = str(err) + '\n' + 'Config reverted'
            embed = self.bot.new_error_report(err.__class__.__name__, details)
            await msg.channel.send(embed=embed)

    @BotExtension.command("edit_rank", description="Update specified user rank")
    async def cmd_edit_rank(self, msg: discord.Message, role: discord.Role, weight: int, membership: int,
                            msg_count: int, vc_time: int):
        if role.name not in self.ranks:
            await msg.channel.send(R.ERROR_OTHER.UNKNOWN_RANK)
            return
        # Check weight uniqueness
        ranks_weights = {r.weight: n for n, r in self.ranks.items()}
        if weight in ranks_weights:
            await msg.channel.send(f'{R.MESSAGE.ERROR_OTHER.DUPLICATE_WEIGHT}: {ranks_weights[weight]}')
            return
        # Update rank
        rank = self.ranks[role.name]
        rank.weight = weight
        rank.membership = membership
        rank.messages = msg_count
        rank.vc = vc_time
        # Update config properly
        err = await self.bot.safe_update_config()
        if not err:
            await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)
        else:
            details = str(err) + '\n' + 'Config reverted'
            embed = self.bot.new_error_report(err.__class__.__name__, details)
            await msg.channel.send(embed=embed)
        list_ranks = ["list-ranks", "ranks", "ranks-list"]
        add_rank = ["add-rank", "new-rank", "ranks-add", "ranks-new"]
        remove_rank = ["remove-rank", "del-rank", "delete-rank", "ranks-remove", "ranks-del", "ranks-delete"]
        edit_rank = ["edit-rank", "alter-rank", "ranks-edit"]
