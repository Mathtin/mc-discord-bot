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

import io
import json
import logging
from typing import List, Dict

import discord

from db import PlayerProfile
from overlord import OverlordMember
from overlord.extension import BotExtension
from services import UserService, RoleService, PlayerProfileService
from util import ConfigView
from util.resources import STRINGS as R
from util.exceptions import InvalidConfigException
from util.extbot import is_text_channel, quote_msg, filter_roles, qualified_name
from util.mcuuid import PlayerData

log = logging.getLogger('ranking-extension')


def parse_colon_separated(msg: str) -> Dict[str, str]:
    lines = [s.strip() for s in msg.split('\n')]
    lines = [s for s in lines if s != ""]
    res = {}
    for s in lines:
        try:
            k = s[: s.index(':')].strip()
            v = s[s.index(':') + 1:].strip()
            if k == "":
                return {}
            res[k.lower()] = v
        except ValueError:
            continue
    return res


#####################
# Message Templates #
#####################

PROFILE_EXAMPLE = """IGN: MyCoolMinecraftNickname
Age: 18
Country: USA
Playstyle & mods you like: building with oak planks
Random info: I'm not even exisiting! I'm just example! Don't blame me please"""

INVALID_PROFILE_DM_MSG = \
    """Hi {0}, you left your profile on ECc server but unfortunately it doesn\'t match specified pattern :(

Please, follow this example:
""" + quote_msg(PROFILE_EXAMPLE) + """

The profile has been removed but don't worry. Here is copy of your message:
{1}
"""

INVALID_PROFILE_IGN_DM_MSG = \
    """Hi {0}, you left your profile on ECc server but unfortunately you specified invalid IGN :(
Please, check your IGN.

The profile has been removed but don't worry. Here is copy of your message:
{1}
"""

FOREIGN_PROFILE_DM_MSG = \
    """Hi {0}, you left your profile on ECc server but unfortunately you mentioned someone else's ign :(

If you believe it isn't your mistake (someone took your ign), please contact admins.

The profile has been removed but don't worry. Here is copy of your message:
{1}
"""


####################
# Whitelist Config #
####################

class WhitelistConfig(ConfigView):
    """
    whitelist {
        channel = ...
        remove_deprecated_profiles = ...
        required = ["────────[Minecraft]────────"]
    }
    """
    channel: int = 0
    remove_deprecated_profiles: bool = False
    required: List[str] = []


#####################
# Ranking Extension #
#####################

class WhitelistExtension(BotExtension):
    __extname__ = '📃 Whitelist Extension'
    __description__ = 'Minecraft player whitelist managing extension'
    __color__ = 0xf6efef

    config: WhitelistConfig = WhitelistConfig()
    channel: discord.TextChannel

    _dry_sync: bool
    _dry_run: bool

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
    def s_profiles(self) -> PlayerProfileService:
        return self.bot.services.player_profiles

    @property
    def required_roles(self) -> List[str]:
        return self.config.required

    ###########
    # Methods #
    ###########

    def ignore_member(self, member: discord.Member) -> bool:
        return len(filter_roles(member, self.required_roles)) == 0

    def sync_whitelist(self) -> None:
        if self._dry_sync or self._dry_run:
            return
        log.info("Synchronizing whitelist")
        pass

    #################
    # Async Methods #
    #################

    async def _send_profile(self, channel: discord.TextChannel, profile: PlayerProfile):
        user = profile.user
        d_user = await self.bot.fetch_user(user.did)

        desc = f'User: {d_user.mention}\n' \
               f'IGN: \'{profile.ign}\'\n' \
               f'Persistent: {profile.banned}\n' \
               f'Banned: {profile.banned}'
        embed = self.bot.new_embed(f"📊 {qualified_name(d_user)} profile", desc, header=self.__extname__,
                                   color=self.__color__)

        if profile.profile is not None:
            embed.add_field(name=f'Profile content', value=profile.profile, inline=False)

        await channel.send(embed=embed)

    async def get_whitelist_json(self) -> str:
        profiles = await self.s_profiles.get_all()
        return json.dumps([{"uuid": p.uuid, "name": p.ign} for p in profiles], indent=4)

    #########
    # Hooks #
    #########

    async def on_ready(self) -> None:
        self._dry_sync = False
        self._dry_run = True

    async def on_config_update(self) -> None:
        self.config = self.bot.get_config_section(WhitelistConfig)
        if self.config is None:
            raise InvalidConfigException("WhitelistConfig section not found", "root")
        # Check channel
        if self.config.channel != 0:
            channel = self.bot.get_channel(self.config.channel)
            if channel is None:
                raise InvalidConfigException(f'Error channel id is invalid', self.config.path('channel'))
            if not is_text_channel(channel):
                raise InvalidConfigException(f"{channel.name}({channel.id}) is not text channel",
                                             self.config.path('channel'))
            permissions = channel.permissions_for(self.bot.me)
            if not permissions.read_message_history:
                raise InvalidConfigException(f'Can\'t read message history in {channel.name}({channel.id})',
                                             self.config.path('channel'))
            log.info(f'Attached to {channel.name} for whitelist parsing ({channel.id})')
            self.channel = channel
        # Check required roles
        for i, role_name in enumerate(self.required_roles):
            if self.s_roles.get_d_role(role_name) is None:
                raise InvalidConfigException(f"No such role: '{role_name}'", self.config.path(f"required[{i}]"))

    async def on_message(self, msg: discord.Message) -> None:
        if msg.channel != self.channel:
            return

        limited_msg = msg.content[:30].replace('\n', ' ') + '...' if len(msg.content) > 10 else msg.content

        try:
            member = await self.bot.guild.fetch_member(msg.author.id)
        except discord.NotFound:
            if self.config.remove_deprecated_profiles:
                '''
                await msg.delete()
                '''
                log.info(f'Removing \'{limited_msg}\' from {msg.author.name} (user left)')
            else:
                log.info(f'Ignoring \'{limited_msg}\' from {msg.author.name} (user left)')
            return

        if self.ignore_member(member):
            '''
            await msg.delete()
            '''
            log.info(f'Ignoring \'{limited_msg}\' from {member.display_name}')
            return

        user = await self.s_users.get(member)
        parsed = parse_colon_separated(msg.content)

        # Handle invalid profile
        if 'ign' not in parsed:
            if self.bot.is_admin(msg.author):
                log.info(f'Ignoring \'{limited_msg}\' from {member.display_name} (invalid profile from admin)')
                return
            log.info(f'Removing \'{limited_msg}\' from {member.display_name} (invalid profile)')
            '''
            report = INVALID_PROFILE_DM_MSG.format(member.name, quote_msg(msg.content))
            await msg.delete()
            try:
                await member.send(report)
            except discord.Forbidden:
                pass
            '''
            return

        ign = parsed['ign']
        player_data = PlayerData(ign)

        # Handle invalid ign
        if not player_data.valid:
            if self.bot.is_admin(msg.author):
                log.info(f'Ignoring \'{limited_msg}\' from {member.display_name} (invalid ign from admin)')
                return
            log.info(f'Removing \'{limited_msg}\' from {member.display_name} (invalid ign)')
            '''
            report = INVALID_PROFILE_IGN_DM_MSG.format(member.name, quote_msg(msg.content))
            await msg.delete()
            try:
                await member.send(report)
            except discord.Forbidden:
                pass
            '''
            return

        async with self.sync():
            # Handle existing
            existing = await self.s_profiles.get_by_ign(ign)
            if existing is not None:
                if existing.user.did != member.id:
                    log.info(f'Removing \'{limited_msg}\' from {member.display_name} (duplicate ign)')
                    '''
                    report = FOREIGN_PROFILE_DM_MSG.format(member.name, quote_msg(msg.content))
                    await msg.delete()
                    try:
                        await member.send(report)
                    except discord.Forbidden:
                        pass
                    '''
                else:
                    if existing.message_did is not None:
                        old_msg = await self.channel.fetch_message(existing.message_did)
                        limited_old_msg = old_msg.content[:30].replace('\n', ' ') + '...' if len(old_msg.content) > 10 \
                            else old_msg.content
                        log.info(f'Removing \'{limited_old_msg}\' from {member.display_name} (old profile)')
                        '''
                        await old_msg.delete()
                        '''
                    existing.message_did = msg.id
                    existing.profile = msg.content
                    await self.s_profiles.save(existing)
                    self.sync_whitelist()
                return
            await self.s_profiles.add_profile(user, player_data, msg)
            self.sync_whitelist()

    async def on_message_edit(self, raw: discord.RawMessageUpdateEvent) -> None:
        if raw.channel_id != self.channel.id:
            return

        profile = await self.s_profiles.get_by_message_did(raw.message_id)

        if profile is None:
            return

        msg = await self.channel.fetch_message(raw.message_id)
        limited_msg = msg.content[:30].replace('\n', ' ') + '...' if len(msg.content) > 10 else msg.content
        member: discord.Member = msg.author
        parsed = parse_colon_separated(msg.content)

        # Handle invalid profile
        if 'ign' not in parsed:
            log.info(f'Removing \'{limited_msg}\' from {member.display_name} (invalid profile)')
            '''
            report = INVALID_PROFILE_DM_MSG.format(member.name, quote_msg(msg.content))
            await msg.delete()
            try:
                await member.send(report)
            except discord.Forbidden:
                pass
            '''
            await self.s_profiles.remove(profile)
            self.sync_whitelist()
            return

        ign = parsed['ign']
        player_data = PlayerData(ign)

        # Handle invalid ign
        if not player_data.valid:
            log.info(f'Removing \'{limited_msg}\' from {member.display_name} (invalid ign)')
            '''
            report = INVALID_PROFILE_IGN_DM_MSG.format(member.name, quote_msg(msg.content))
            await msg.delete()
            try:
                await member.send(report)
            except discord.Forbidden:
                pass
            '''
            await self.s_profiles.remove(profile)
            self.sync_whitelist()
            return

        async with self.sync():
            # Handle existing
            existing = await self.s_profiles.get_by_ign(ign)
            if existing is not None:
                if existing.user.did != member.id:
                    log.info(f'Removing \'{limited_msg}\' from {member.display_name} (duplicate ign)')
                    '''
                    report = FOREIGN_PROFILE_DM_MSG.format(member.name, quote_msg(msg.content))
                    await msg.delete()
                    try:
                        await member.send(report)
                    except discord.Forbidden:
                        pass
                    '''
                    await self.s_profiles.remove(profile)
                    self.sync_whitelist()
                    return
                elif existing.message_did != profile.message_did:
                    old_msg = await self.channel.fetch_message(existing.message_did)
                    limited_old_msg = old_msg.content[:30].replace('\n', ' ') + '...' if len(old_msg.content) > 10 \
                        else old_msg.content
                    log.info(f'Removing \'{limited_old_msg}\' from {member.display_name} (old profile)')
                    '''
                    await old_msg.delete()
                    '''

        profile.profile = msg.content
        await self.s_profiles.save(profile)
        self.sync_whitelist()

    async def on_message_delete(self, raw: discord.RawMessageUpdateEvent) -> None:
        if raw.channel_id != self.channel.id:
            return
        async with self.sync():
            profile = await self.s_profiles.get_by_message_did(raw.message_id)
            if profile is None:
                return
            if profile.persistent:
                profile.profile = None
                profile.message_did = None
                await self.s_profiles.save(profile)
                self.sync_whitelist()
                return
            await self.s_profiles.remove(profile)
            self.sync_whitelist()

    ############
    # Commands #
    ############

    @BotExtension.command("wl_enable", description="Enable whitelist synchronization")
    async def cmd_wl_enable(self, msg: discord.Message):
        self._dry_run = False
        await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("wl_disable", description="Disable whitelist synchronization")
    async def cmd_wl_disable(self, msg: discord.Message):
        self._dry_run = True
        await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("wl_status", description="Check if whitelist synchronization is enabled")
    async def cmd_wl_status(self, msg: discord.Message):
        await msg.channel.send(R.MESSAGE.STATE.DISABLED if self._dry_run else R.MESSAGE.STATE.ENABLED)

    @BotExtension.command("reload_wl", description="Reloads profiles from channel")
    async def cmd_reload_wl(self, msg: discord.Message):
        progress = self.new_progress(f'{R.MESSAGE.STATUS.SYNC_WHITELIST}')
        progress.add_step(R.MESSAGE.STATUS.REMOVING_DYNAMIC_PROFILES)
        progress.add_step(R.MESSAGE.STATUS.LOADING_DYNAMIC_PROFILES)
        progress.add_step(R.MESSAGE.STATUS.SYNC_WHITELIST)
        await progress.start(msg.channel)
        try:
            self._dry_sync = True
            # Transaction begins
            async with self.bot.sync():
                await self.s_profiles.clear_dynamic()
                await progress.next_step()
                async for message in self.channel.history(limit=None, oldest_first=True):
                    await self.on_message(message)
            await progress.next_step()
        except Exception:
            await progress.finish(failed=True)
            raise
        finally:
            self._dry_sync = False
        self.sync_whitelist()
        await progress.finish()

    @BotExtension.command("sync_wl", description="Synchronize whitelist between servers")
    async def cmd_sync_wl(self, msg: discord.Message):
        self.sync_whitelist()
        await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("wl_add", description="Add persistent whitelist entry")
    async def cmd_wl_add(self, msg: discord.Message, user: OverlordMember, ign: str):
        player_data = PlayerData(ign)

        # Handle invalid ign
        if not player_data.valid:
            await msg.channel.send(R.MESSAGE.ERROR_OTHER.INVALID_IGN)
            return

        async with self.sync():
            # Handle existing
            existing = await self.s_profiles.get_by_ign(ign)
            if existing is not None:
                if existing.user.id != user.db.id:
                    await msg.channel.send(R.MESSAGE.ERROR_OTHER.DUPLICATE_IGN)
                    return
                else:
                    if existing.persistent:
                        await msg.channel.send(R.MESSAGE.ERROR_OTHER.DUPLICATE_PERSISTENT_PROFILE)
                        return
                    existing.persistent = True
                    await self.s_profiles.save(existing)
                    await msg.channel.send(f'{R.EMBED.TITLE.INFO}: {R.MESSAGE.ERROR_OTHER.DUPLICATE_PROFILE}.\n'
                                           f'{R.MESSAGE.STATUS.SUCCESS}')
                return
            await self.s_profiles.add_persistent_profile(user.db, player_data)
        await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("wl_remove", description="Remove persistent whitelist entry")
    async def cmd_wl_remove(self, msg: discord.Message, ign):
        async with self.sync():
            profile = await self.s_profiles.get_by_ign(ign)
            if profile is None:
                await msg.channel.send(R.MESSAGE.ERROR_OTHER.UNKNOWN_PLAYER)
                return
            if not profile.persistent:
                await msg.channel.send(f'{R.EMBED.TITLE.ERROR}: {R.MESSAGE.ERROR_OTHER.PROFILE_NON_PERSISTENT} '
                                       f'({R.MESSAGE.STATE.SKIPPED})')
                return
            if profile.message_did is not None:
                await msg.channel.send(f'{R.EMBED.TITLE.WARNING}: {R.MESSAGE.ERROR_OTHER.PROFILE_NON_PERSISTENT} '
                                       f'({R.MESSAGE.STATE.SKIPPED})')
                profile.persistent = False
                await self.s_profiles.save(profile)
                return
            await self.s_profiles.remove(profile)
        await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("wl_force_remove", description="Remove persistent whitelist entry including profile")
    async def cmd_wl_force_remove(self, msg: discord.Message, ign):
        async with self.sync():
            profile = await self.s_profiles.get_by_ign(ign)
            if profile is None:
                await msg.channel.send(R.MESSAGE.ERROR_OTHER.UNKNOWN_PLAYER)
                return
            if profile.message_did is not None:
                await msg.channel.send(f'{R.EMBED.TITLE.WARNING}: {R.MESSAGE.ERROR_OTHER.PROFILE_NON_PERSISTENT}')
                msg = await self.channel.fetch_message(profile.message_did)
                await msg.delete()
            await self.s_profiles.remove(profile)
        await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("get_profile", description="Get player profile")
    async def cmd_get_profile(self, msg: discord.Message, user_or_ign: str):
        profiles = []

        # Handle if user queried
        member = await self.bot.resolve_user(user_or_ign)
        if member is not None:
            profiles = await self.s_profiles.get_all(member)
        profile_ids = [p.id for p in profiles]
        profile = await self.s_profiles.get_by_ign(user_or_ign)
        if profile is not None and profile.id not in profile_ids:
            profiles.append(profile)

        if not len(profiles):
            await msg.channel.send(R.MESSAGE.ERROR_OTHER.UNKNOWN_PLAYER)
            return

        for profile in profiles:
            await self._send_profile(msg.channel, profile)

    @BotExtension.command("wl_ban", description="Ban player (preserving profile)")
    async def cmd_wl_ban(self, msg: discord.Message, ign: str):
        async with self.sync():
            profile = await self.s_profiles.get_by_ign(ign)
            if profile is None:
                await msg.channel.send(R.MESSAGE.ERROR_OTHER.UNKNOWN_PLAYER)
                return
            if profile.banned:
                await msg.channel.send(R.MESSAGE.ERROR_OTHER.ALREADY_BANNED)
                return
            profile.banned = True
            await self.s_profiles.save(profile)
        await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("wl_unban", description="Unban player")
    async def cmd_wl_unban(self, msg: discord.Message, ign: str):
        async with self.sync():
            profile = await self.s_profiles.get_by_ign(ign)
            if profile is None:
                await msg.channel.send(R.MESSAGE.ERROR_OTHER.UNKNOWN_PLAYER)
                return
            if not profile.banned:
                await msg.channel.send(R.MESSAGE.ERROR_OTHER.NOT_BANNED)
                return
            profile.banned = False
            await self.s_profiles.save(profile)
        await msg.channel.send(R.MESSAGE.STATUS.SUCCESS)

    @BotExtension.command("wl_get", description="Sends whitelist json")
    async def cmd_wl_get(self, msg: discord.Message):
        async with self.sync():
            f = io.StringIO(await self.get_whitelist_json())
            await msg.channel.send(content="Whitelist", file=discord.File(fp=f, filename="whitelist.json"))
