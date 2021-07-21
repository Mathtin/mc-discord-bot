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

import asyncio
import logging
import os
import sys
import traceback
from typing import Dict, List, Callable, Awaitable, Optional, Union, Any, Tuple

import discord

import db as DB
from services.provider import ServiceProvider
from util import parse_control_message, limit_traceback
from util.config import ConfigManager
from util.exceptions import InvalidConfigException, NotCoroutineException
from util.extbot import qualified_name, is_dm_message, filter_roles, is_text_channel
from util.extbot import skip_bots, after_initialized, guild_member_event, get_coroutine_attrs
from util.logger import DiscordLogConfig
from util.resources import STRINGS as R
from .types import OverlordMember, OverlordRole, IBotExtension, OverlordRootConfig

log = logging.getLogger('overlord-bot')


#############################
# Main class implementation #
#############################

class Overlord(discord.Client):
    # Internal stuff
    _async_lock: asyncio.locks
    _initialized: bool
    _extensions: List[IBotExtension]
    _handlers: Dict[str, Callable[..., Awaitable[None]]]
    _call_plan_map: Dict[str, List[List[Callable[..., Awaitable[None]]]]]
    _cmd_cache: Dict[str, Callable[..., Awaitable[None]]]

    # Members loaded from ENV
    _token: str
    _guild_id: int
    _maintainer_id: int

    # Members passed via constructor
    cnf_manager: ConfigManager
    config: OverlordRootConfig
    log_config: DiscordLogConfig
    services: ServiceProvider

    # Values initiated on_ready
    guild: discord.Guild
    control_channel: discord.TextChannel
    log_channel: Optional[discord.TextChannel]
    maintainer: discord.Member
    me: discord.Member

    def __init__(self, cnf_manager: ConfigManager, services: ServiceProvider) -> None:
        # Init base class
        intents = discord.Intents.none()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.reactions = True
        super().__init__(intents=intents)

        # Init internal fields
        self._async_lock = asyncio.Lock()
        self._initialized = False
        self.log_channel = None
        self._extensions = []
        handlers = get_coroutine_attrs(self, name_filter=lambda x: x.startswith('on_'))
        self._handlers = {n.replace('_raw', ''): h for n, h in handlers.items()}
        self._call_plan_map = {}
        self._cmd_cache = {}

        # Set user supplied fields
        self.cnf_manager = cnf_manager
        self.reload_sections()
        self.services = services

        # Load env values
        self._token = os.getenv('DISCORD_TOKEN')
        self._guild_id = int(os.getenv('DISCORD_GUILD'))
        self._maintainer_id = int(os.getenv('MAINTAINER_DISCORD_ID'))

    ########################
    # Private sync methods #
    ########################

    def _build_call_plan(self, handler_name) -> None:
        if handler_name == 'on_error':
            return
        # Build call plan
        call_plan = [[] for _ in range(64)]
        for extension in self._extensions:
            if not hasattr(extension, handler_name):
                continue
            call_plan[extension.priority].append(getattr(extension, handler_name))
        self._call_plan_map[handler_name] = [call for call in call_plan if call]

    def _find_cmd_handler(self, name: str) -> Callable[..., Awaitable[None]]:
        for ext in self._extensions:
            handler = ext.cmd_handler(name)
            if handler is not None:
                return handler
        raise InvalidConfigException(f"Command handler not found for {name}", "bot.commands")

    #########################
    # Private async methods #
    #########################

    async def _run_call_plan(self, name: str, *args, **kwargs) -> None:
        call_plan = self._call_plan_map[name]
        for handlers in call_plan:
            calls = [h(*args, **kwargs) for h in handlers]
            await asyncio.gather(*calls)

    ###########
    # Getters #
    ###########

    @property
    def extensions(self) -> List[IBotExtension]:
        return self._extensions

    @property
    def prefix(self) -> str:
        return self.config.control.prefix

    def sync(self) -> asyncio.Lock:
        return self._async_lock

    def is_guild_member(self, member: discord.Member) -> bool:
        return member.guild.id == self.guild.id

    def is_guild_member_message(self, msg: discord.Message) -> bool:
        return not is_dm_message(msg) and msg.guild.id == self.guild.id

    def is_special_channel_id(self, channel_id: int) -> bool:
        return channel_id == self.control_channel.id or channel_id == self.log_channel.id

    def get_role(self, role_name: str) -> Optional[discord.Role]:
        return self.services.role.get_d_role(role_name)

    def is_admin(self, user: discord.Member) -> bool:
        if user == self.maintainer:
            return True
        return len(filter_roles(user, self.config.control.roles)) > 0

    def extension_idx(self, ext: IBotExtension) -> int:
        for i in range(len(self._extensions)):
            if self._extensions[i] is ext:
                return i
        return -1

    def get_config_section(self, section_type: Any) -> Any:
        return self.cnf_manager.find_section(section_type)

    ##########
    # Embeds #
    ##########

    def new_embed(self, title, body, footer: str = None, header: str = None, color: int = 0xd75242):
        header = header or R.EMBED.HEADER.DEFAULT
        footer = footer or R.EMBED.FOOTER.DEFAULT
        embed = discord.Embed(title=title, description=body, color=color)
        embed.set_author(name=header, icon_url=self.me.avatar_url)
        embed.set_footer(text=footer, icon_url=self.me.avatar_url)
        return embed

    def new_error_report(self, name: str, details: str,
                         traceback_: Optional[List[str]] = None,
                         args: Optional[Tuple[Any]] = None,
                         kwargs: Optional[Dict[str, Any]] = None,
                         color: int = 0xd75242):
        header = R.EMBED.HEADER.ERROR_REPORT
        title = f'❗ {name}'
        embed = self.new_embed(title=title, body=details, header=header, color=color)
        if traceback_ is not None:
            traceback_limited = limit_traceback(traceback_, "src", 6)
            tb_line = '\n'.join(traceback_limited)[:1000]
            embed.add_field(name=R.NAME.COMMON.TRACEBACK, value=f'```python\n{tb_line}\n```', inline=False)
        if args or kwargs:
            call_args = [f'[{i}] {a}' for i, a in enumerate(args)]
            call_kwargs = [f'[{k}] {a}' for k, a in kwargs.items()]
            call_arg_report = '\n'.join(call_args + call_kwargs)
            embed.add_field(name=R.EMBED.TITLE.CALL_ARGS, value=f'```python\n{call_arg_report}\n```')
        return embed

    def new_warn_report(self, name: str, details: str, color: int = 0xd75242):
        header = R.EMBED.HEADER.WARN_REPORT
        title = f'⚠ {name}'
        embed = self.new_embed(title=title, body=details, header=header, color=color)
        return embed

    def new_info_report(self, name: str, details: str, color: int = 0xd75242):
        header = R.EMBED.HEADER.INFO_REPORT
        title = f'📰 {name}'
        embed = self.new_embed(title=title, body=details, header=header, color=color)
        return embed

    #############
    # Resolvers #
    #############

    async def resolve_user(self, user_mention: str) -> Optional[DB.User]:
        try:
            if '#' in user_mention:
                return await self.services.user.get_by_qualified_name(user_mention)
            elif user_mention.startswith('<@'):
                d_user = await self.fetch_user(int(user_mention[2:-1]))
                return await self.services.user.get(d_user)
            else:
                return await self.services.user.get_by_display_name(user_mention)
        except discord.NotFound:
            return None
        except ValueError:
            return None

    async def resolve_text_channel(self, channel_mention: str) -> Optional[discord.TextChannel]:
        if '<' in channel_mention:
            channel = [c for c in self.guild.text_channels if c.mention == channel_mention]
            return channel[0] if channel else None
        if '#' in channel_mention:
            channel_name = channel_mention[1:]
        else:
            channel_name = channel_mention
        channel = [c for c in self.guild.text_channels if c.name == channel_name]
        return channel[0] if channel else None

    async def resolve_voice_channel(self, channel_mention: str) -> Optional[discord.VoiceChannel]:
        if '<' in channel_mention:
            channel = [c for c in self.guild.voice_channels if c.mention == channel_mention]
            return channel[0] if channel else None
        if '#' in channel_mention:
            channel_name = channel_mention[1:]
        else:
            channel_name = channel_mention
        channel = [c for c in self.guild.voice_channels if c.name == channel_name]
        return channel[0] if channel else None

    def resolve_extension(self, ext: Union[int, str]) -> Optional[IBotExtension]:
        if isinstance(ext, int):
            if 0 < ext <= len(self._extensions):
                return self._extensions[ext - 1]
            return None
        try:
            return self.resolve_extension(int(ext))
        except ValueError:
            search = [e for e in self._extensions if e.name == ext]
            return search[0] if search else None

    #######################
    # Public sync methods #
    #######################

    def run(self) -> None:
        super().run(self._token)

    def save_config(self) -> None:
        log.info(f'Saving configuration on disk')
        self.cnf_manager.save()

    def reload_sections(self) -> None:
        self.config = self.get_config_section(OverlordRootConfig)
        if self.config is None:
            raise InvalidConfigException("OverlordRootConfig section not found", "root")
        self.log_config = self.get_config_section(DiscordLogConfig)
        if self.log_config is None:
            raise InvalidConfigException("DiscordLogConfig section not found", "root")

    def extend(self, extension: IBotExtension) -> None:
        self._extensions.append(extension)
        self._extensions.sort(key=lambda e: e.priority)
        self._call_plan_map = {}
        for h in self._handlers:
            self._build_call_plan(h)

    def update_command_cache(self) -> None:
        self._cmd_cache = {}
        for cmd, aliases in self.config.command.items():
            handler = self._find_cmd_handler(cmd)
            for alias in aliases:
                if alias in self._cmd_cache:
                    raise InvalidConfigException(f"Command alias collision for {alias}: {cmd}", "bot.commands")
                self._cmd_cache[alias] = handler

    #################
    # Async methods #
    #################

    async def logout(self) -> None:
        for ext in self._extensions:
            ext.stop()
        return await super().logout()

    async def init_lock(self) -> None:
        while not self._initialized:
            await asyncio.sleep(0.1)
        return

    async def send_error(self, from_: str, msg: str) -> None:
        error_report = self.new_error_report(from_, msg)
        if self.log_channel is not None:
            await self.log_channel.send(embed=error_report)
        await self.maintainer.send(embed=error_report)
        return

    async def send_warning(self, from_: str, msg: str) -> None:
        warn_report = self.new_warn_report(from_, msg)
        if self.log_channel is not None:
            await self.log_channel.send(embed=warn_report)
        await self.maintainer.send(embed=warn_report)
        return

    async def send_info(self, from_: str, msg: str) -> None:
        info_report = self.new_info_report(from_, msg)
        if self.log_channel is not None:
            await self.log_channel.send(embed=info_report)
        await self.maintainer.send(embed=info_report)
        return

    async def _sync_users(self):
        log.info('Syncing roles')
        await self.services.role.load(self.guild.roles)
        log.info(f'Syncing users')
        await self.services.user.mark_everyone_absent()
        async for member in self.guild.fetch_members(limit=None):
            if member.bot:
                continue
            # Update and repair
            user = await self.services.user.merge_member(member)
        # Remove effectively absent
        if not self.config.keep_absent_users:
            await self.services.user.remove_absent()
        log.info(f'Syncing is done')

    async def sync_users(self, no_lock: bool = False) -> None:
        if no_lock:
            return await self._sync_users()
        async with self.sync():
            await self._sync_users()

    async def alter_config(self, config: str) -> None:
        log.info(f'Altering configuration')
        self.cnf_manager.alter(config)
        self.reload_sections()
        await self.on_config_update()

    async def safe_alter_config(self, config: str) -> Optional[Exception]:
        old_config = self.cnf_manager.raw
        try:
            await self.alter_config(config)
        except (InvalidConfigException, TypeError) as e:
            log.warning(f'Invalid config data: {e}. Reverting.')
            await self.alter_config(old_config)
            return e
        return None

    async def update_config(self) -> None:
        log.info(f'Updating configuration')
        self.save_config()
        self.reload_sections()
        await self.on_config_update()

    async def safe_update_config(self) -> Optional[Exception]:
        old_config = self.cnf_manager.raw
        try:
            await self.update_config()
        except (InvalidConfigException, TypeError) as e:
            log.warning(f'Invalid config data. Reverting.')
            await self.alter_config(old_config)
            return e
        return None

    async def reload_config(self) -> None:
        log.info(f'Altering configuration')
        self.cnf_manager.reload()
        self.reload_sections()
        await self.on_config_update()

    #########
    # Hooks #
    #########

    async def on_error(self, event, *args, **kwargs) -> None:
        """
            Async error event handler

            Sends stacktrace to error channel
        """
        logging.exception(f'Error on event: {event}, args: {args}, kwargs: {kwargs}')

        ex_type = sys.exc_info()[0]
        ex = sys.exc_info()[1]
        tb = traceback.format_exception(*sys.exc_info())
        name = ex_type.__name__

        reported_to = f'{R.MESSAGE.STATUS.REPORTED_TO} {self.maintainer.mention}'

        maintainer_report = self.new_error_report(name, str(ex), tb, args, kwargs)
        channel_report = self.new_error_report(name, str(ex) + '\n' + reported_to)

        if self.log_channel is not None and event != 'on_ready':
            await self.log_channel.send(embed=channel_report)

        await self.maintainer.send(embed=maintainer_report)

        if ex_type is InvalidConfigException:
            await self.logout()
        if ex_type is NotCoroutineException:
            await self.logout()
        if event == 'on_ready':
            await self.logout()

    async def on_ready(self) -> None:
        """
            Async ready event handler

            Completely initialize bot state
        """
        # Attach guild
        self.guild = self.get_guild(self._guild_id)
        if self.guild is None:
            raise InvalidConfigException("Discord server id is invalid", "DISCORD_GUILD")
        log.info(f'{self.user} is connected to the following guild: {self.guild.name}(id: {self.guild.id})')
        # Resolve maintainer
        try:
            self.maintainer = await self.guild.fetch_member(self._maintainer_id)
            await self.maintainer.send('**STARTING...**')
        except discord.NotFound:
            raise InvalidConfigException(f'Error maintainer id is invalid', 'MAINTAINER_DISCORD_ID')
        except discord.Forbidden:
            raise InvalidConfigException(f'Error cannot send messages to maintainer', 'MAINTAINER_DISCORD_ID')
        log.info(f'Maintainer is {qualified_name(self.maintainer)} ({self.maintainer.id})')
        # Resolve bot as member
        self.me = await self.guild.fetch_member(self.user.id)
        # Sync roles and users
        await self.sync_users()
        # Start extensions
        for ext in self._extensions:
            ext.start()
        # Check config value
        await self.on_config_update()
        self._initialized = True
        # Call 'on_ready' extension handlers
        await self._run_call_plan('on_ready')
        # Report success
        print(self.config.egg_done)
        start_report = f'{R.NAME.COMMON.GUILD}: {self.guild.name}\n'
        start_report += f'{R.NAME.COMMON.MAINTAINER}: {self.maintainer.mention}\n'
        start_report += f'{R.NAME.COMMON.CONTROL_CHANNEL}: {self.control_channel.mention}\n'
        if self.log_channel is not None:
            start_report += f'{R.NAME.COMMON.LOG_CHANNEL}: {self.log_channel.mention}\n'
        embed = self.new_info_report(R.MESSAGE.STATUS.STARTED, start_report)
        # Report extensions
        ext_details = [f'✅ {ext.name}' if ext.enabled else f'❌ {ext.name}' for ext in self._extensions]
        embed.add_field(name=R.EMBED.TITLE.EXTENSION_STATUS_LIST, value='\n'.join(ext_details), inline=False)
        await self.maintainer.send(embed=embed)

    async def on_config_update(self) -> None:
        log.info(f'Checking configuration')
        for i, role_name in enumerate(self.config.control.roles):
            if self.get_role(role_name) is None:
                raise InvalidConfigException(f"No such role: '{role_name}'", self.config.control.path(f'roles[{i}]'))
        self.update_command_cache()
        # Attach control channel
        channel = self.get_channel(self.config.control.channel)
        if channel is None:
            raise InvalidConfigException(f'Control channel id is invalid', self.config.control.path('channel'))
        if not is_text_channel(channel):
            raise InvalidConfigException(f"{channel.name}({channel.id}) is not text channel",
                                         self.config.control.path('channel'))
        log.info(f'Attached to {channel.name} as control channel ({channel.id})')
        self.control_channel = channel
        # Attach error channel
        if self.log_config.channel != 0:
            channel = self.get_channel(self.log_config.channel)
            if channel is None:
                raise InvalidConfigException(f'Error channel id is invalid', self.log_config.path('channel'))
            if not is_text_channel(channel):
                raise InvalidConfigException(f"{channel.name}({channel.id}) is not text channel",
                                             self.log_config.path('channel'))
            log.info(f'Attached to {channel.name} as logging channel ({channel.id})')
            self.log_channel = channel
        # Call extension 'on_config_update' handlers
        await self._run_call_plan('on_config_update')

    @after_initialized
    @skip_bots
    async def on_message(self, message: discord.Message) -> None:
        """
            Async new message event handler

            Saves event in database
        """
        # handle control commands separately
        if message.channel == self.control_channel or (message.author == self.maintainer and is_dm_message(message)):
            await self._on_control_message(message)
            return
        if not self.is_guild_member_message(message):
            return
        user = await self.services.user.get(message.author)
        # Skip non-existing users
        if user is None:
            log.warning(f'{qualified_name(message.author)} does not exist in db! Skipping new message event!')
            return
        # Call extension 'on_message' handlers
        await self._run_call_plan('on_message', message)

    async def _on_control_message(self, message: discord.Message) -> None:
        """
            Async new control message event handler

            Calls appropriate control callback
        """
        # Filter non-admins
        if not self.is_admin(message.author):
            return
        # Parse argv
        argv = parse_control_message(self.prefix, message)
        if argv is None or len(argv) == 0:
            return
        # Resolve cmd handler
        cmd_name = argv[0]
        if cmd_name not in self._cmd_cache:
            await message.channel.send(R.MESSAGE.ERROR.UNKNOWN_COMMAND)
            return
        handler = self._cmd_cache[cmd_name]
        # Call handler
        await handler(message, self.prefix, argv)

    @after_initialized
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        """
            Async message edit event handler

            Saves event in database
        """
        if self.is_special_channel_id(payload.channel_id):
            return
        # Call extension 'on_message_edit' handlers
        await self._run_call_plan('on_message_edit', payload)

    @after_initialized
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        """
            Async message delete event handler

            Saves event in database
        """
        if self.is_special_channel_id(payload.channel_id):
            return
        # Call extension 'on_message_delete' handlers
        await self._run_call_plan('on_message_delete', payload)

    @after_initialized
    @skip_bots
    @guild_member_event
    async def on_member_join(self, member: discord.Member) -> None:
        """
            Async member join event handler

            Saves user in database
        """
        async with self.sync():
            # Add/update user
            user = await self.services.user.merge_member(member)
        # Call extension 'on_member_join' handlers
        await self._run_call_plan('on_member_join', OverlordMember(member, user))

    @after_initialized
    @skip_bots
    @guild_member_event
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """
            Async member remove event handler

            Removes user from database (or keep it, depends on config)
        """
        # track only role/nickname change
        if not (before.roles != after.roles or
                before.display_name != after.display_name or
                before.name != after.name or
                before.discriminator != after.discriminator):
            return
        async with self.sync():
            # Skip absent
            user = await self.services.user.get(before)
            if user is None:
                log.warning(f'{qualified_name(after)} does not exist in db! Skipping user update event!')
                return
            # Update user
            await self.services.user.merge_member(after)
        # Call extension 'on_member_update' handlers
        await self._run_call_plan('on_member_update', OverlordMember(before, user), OverlordMember(after, user))

    @after_initialized
    @skip_bots
    @guild_member_event
    async def on_member_remove(self, member: discord.Member) -> None:
        """
            Async member remove event handler

            Removes user from database (or keep it, depends on config)
        """
        async with self.sync():
            if self.config.keep_absent_users:
                user = await self.services.user.make_user_absent(member)
                if user is None:
                    log.warning(f'{qualified_name(member)} does not exist in db! Skipping user leave event!')
                    return
            else:
                user = await self.services.user.remove(member)
                if user is None:
                    log.warning(f'{qualified_name(member)} does not exist in db! Skipping user leave event!')
                    return
        # Call extension 'on_member_remove' handlers
        await self._run_call_plan('on_member_remove', OverlordMember(member, user))

    @after_initialized
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """
            Async guild role create event handler

            Saves event in database
        """
        await self.sync_users()
        # Call extension 'on_guild_role_create' handlers
        await self._run_call_plan('on_guild_role_create', OverlordRole(role, self.services.role.get_d_role(role.name)))

    @after_initialized
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """
            Async guild role delete event handler

            Saves event in database
        """
        await self.sync_users()
        # Call extension 'on_guild_role_delete' handlers
        await self._run_call_plan('on_guild_role_delete', OverlordRole(role, self.services.role.get_d_role(role.name)))

    @after_initialized
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        """
            Async guild role update event handler

            Saves event in database
        """
        await self.sync_users()
        role = self.services.role.get_d_role(before.name)
        # Call extension 'on_guild_role_update' handlers
        await self._run_call_plan('on_guild_role_update', OverlordRole(before, role), OverlordRole(after, role))

    @after_initialized
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """
            Async new reaction event handler

            Saves event in database
        """
        try:
            # Resolve member, channel, message
            member = await self.guild.fetch_member(payload.user_id)
            channel = await self.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        if member.bot:
            return
        # handle control reactions
        if channel == self.control_channel or (
                member == self.maintainer and isinstance(channel, discord.DMChannel)):
            return await self.on_control_reaction_add(member, message, payload.emoji)
        if not self.is_guild_member_message(message):
            return
        user = await self.services.user.get(member)
        if user is None:
            log.warning(f'{qualified_name(message.author)} does not exist in db! Skipping new reaction event!')
            return
        # Call extension 'on_reaction_add' handlers
        await self._run_call_plan('on_reaction_add',
                                  OverlordMember(member, user),
                                  message,
                                  payload.emoji)

    async def on_control_reaction_add(self, member: discord.Member, message: discord.Message,
                                      emoji: discord.PartialEmoji) -> None:
        """
            Async control reaction add event handler

            Saves event in database
        """
        # Call extension 'on_control_reaction_add' handlers
        await self._run_call_plan('on_control_reaction_add', member, message, emoji)

    @after_initialized
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        """
            Async reaction remove event handler

            Saves event in database
        """
        try:
            # Resolve member, channel, message
            member = await self.guild.fetch_member(payload.user_id)
            channel = await self.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        if member.bot:
            return
        # handle control reactions
        if channel == self.control_channel or (
                member == self.maintainer and isinstance(channel, discord.DMChannel)):
            await self.on_control_reaction_remove(member, message, payload.emoji)
            return
        if not self.is_guild_member_message(message):
            return
        user = await self.services.user.get(member)
        if user is None:
            log.warning(f'{qualified_name(message.author)} does not exist in db! Skipping new reaction event!')
            return
        # Call extension 'on_reaction_remove' handlers
        await self._run_call_plan('on_reaction_remove',
                                  OverlordMember(member, user),
                                  message,
                                  payload.emoji)

    async def on_control_reaction_remove(self, member: discord.Member, message: discord.Message,
                                         emoji: discord.PartialEmoji) -> None:
        """
            Async control reaction add event handler

            Saves event in database
        """
        # Call extension 'on_control_reaction_add' handlers
        await self._run_call_plan('on_control_reaction_remove', member, message, emoji)
