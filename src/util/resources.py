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
    
import os.path
from typing import Dict
import xml.etree.ElementTree as ET
from .exceptions import MissingResourceException


def res_path(local_path: str):
    path = os.getenv('RESOURCE_PATH')
    return os.path.join(path, local_path)


class XStrings(object):
    class XName(object):
        class XCommon(object):
            _type_name = "common"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def TRACEBACK(self) -> str:
                return self.get("traceback")
        
            @property
            def EXTENSION(self) -> str:
                return self.get("extension")
        
            @property
            def GUILD(self) -> str:
                return self.get("guild")
        
            @property
            def CHANNEL(self) -> str:
                return self.get("channel")
        
            @property
            def ERROR(self) -> str:
                return self.get("error")
        
            @property
            def INFO(self) -> str:
                return self.get("info")
        
            @property
            def LOG_CHANNEL(self) -> str:
                return self.get("log-channel")
        
            @property
            def CONTROL_CHANNEL(self) -> str:
                return self.get("control-channel")
        
            @property
            def MAINTAINER(self) -> str:
                return self.get("maintainer")
        
            @property
            def STATE(self) -> str:
                return self.get("state")
        
            @property
            def PROGRESS(self) -> str:
                return self.get("progress")
        
    
        _section_name = "names"
        COMMON: XCommon
    
        def __init__(self, res) -> None:
            self._res = res
            self.COMMON = XStrings.XName.XCommon(self)
    
        def get(self, type_name, string_name) -> str:
            return self._res.get(self._section_name, type_name, string_name)

    class XEmbed(object):
        class XHeader(object):
            _type_name = "header"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def DEFAULT(self) -> str:
                return self.get("default")
        
            @property
            def ERROR_REPORT(self) -> str:
                return self.get("error-report")
        
            @property
            def WARN_REPORT(self) -> str:
                return self.get("warn-report")
        
            @property
            def INFO_REPORT(self) -> str:
                return self.get("info-report")
        
            @property
            def LOG_REPORT(self) -> str:
                return self.get("log-report")
        
    
        class XFooter(object):
            _type_name = "footer"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def DEFAULT(self) -> str:
                return self.get("default")
        
    
        class XTitle(object):
            _type_name = "title"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def SUCCESS(self) -> str:
                return self.get("success")
        
            @property
            def ERROR(self) -> str:
                return self.get("error")
        
            @property
            def WARNING(self) -> str:
                return self.get("warning")
        
            @property
            def INFO(self) -> str:
                return self.get("info")
        
            @property
            def TRACEBACK(self) -> str:
                return self.get("traceback")
        
            @property
            def SUMMARY(self) -> str:
                return self.get("summary")
        
            @property
            def CALL_ARGS(self) -> str:
                return self.get("call-args")
        
            @property
            def COMMANDS_LIST(self) -> str:
                return self.get("commands-list")
        
            @property
            def STAT_TYPE_LIST(self) -> str:
                return self.get("stat-type-list")
        
            @property
            def STATS_LIST(self) -> str:
                return self.get("stats-list")
        
            @property
            def RANK_TABLE(self) -> str:
                return self.get("rank-table")
        
            @property
            def CONFIG_VALUE(self) -> str:
                return self.get("config-value")
        
            @property
            def EXTENSION_STATUS_LIST(self) -> str:
                return self.get("extension-status-list")
        
    
        _section_name = "embeds"
        HEADER: XHeader
        FOOTER: XFooter
        TITLE: XTitle
    
        def __init__(self, res) -> None:
            self._res = res
            self.HEADER = XStrings.XEmbed.XHeader(self)
            self.FOOTER = XStrings.XEmbed.XFooter(self)
            self.TITLE = XStrings.XEmbed.XTitle(self)
    
        def get(self, type_name, string_name) -> str:
            return self._res.get(self._section_name, type_name, string_name)

    class XMessage(object):
        class XStatus(object):
            _type_name = "status"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def COMMITTING(self) -> str:
                return self.get("committing")
        
            @property
            def BUSY(self) -> str:
                return self.get("busy")
        
            @property
            def PING(self) -> str:
                return self.get("ping")
        
            @property
            def REMOVING_DYNAMIC_PROFILES(self) -> str:
                return self.get("removing-dynamic-profiles")
        
            @property
            def LOADING_DYNAMIC_PROFILES(self) -> str:
                return self.get("loading-dynamic-profiles")
        
            @property
            def SYNC_WHITELIST(self) -> str:
                return self.get("sync-whitelist")
        
            @property
            def SYNC_USERS(self) -> str:
                return self.get("sync-users")
        
            @property
            def UPDATING_RANKS(self) -> str:
                return self.get("updating-ranks")
        
            @property
            def UPDATING_RANK(self) -> str:
                return self.get("updating-rank")
        
            @property
            def DB_DROP_TABLE(self) -> str:
                return self.get("db-drop-table")
        
            @property
            def DB_DROP(self) -> str:
                return self.get("db-drop")
        
            @property
            def STOP_EXTENSION(self) -> str:
                return self.get("stop-extension")
        
            @property
            def REPORTED_TO(self) -> str:
                return self.get("reported-to")
        
            @property
            def STARTED(self) -> str:
                return self.get("started")
        
            @property
            def SUCCESS(self) -> str:
                return self.get("success")
        
            @property
            def ELAPSED(self) -> str:
                return self.get("elapsed")
        
    
        class XState(object):
            _type_name = "state"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def FINISHED(self) -> str:
                return self.get("finished")
        
            @property
            def IN_PROGRESS(self) -> str:
                return self.get("in-progress")
        
            @property
            def FAILED(self) -> str:
                return self.get("failed")
        
            @property
            def SUCCESS(self) -> str:
                return self.get("success")
        
            @property
            def NOT_STARTED(self) -> str:
                return self.get("not-started")
        
            @property
            def UNKNOWN(self) -> str:
                return self.get("unknown")
        
            @property
            def SKIPPED(self) -> str:
                return self.get("skipped")
        
            @property
            def ENABLED(self) -> str:
                return self.get("enabled")
        
            @property
            def DISABLED(self) -> str:
                return self.get("disabled")
        
    
        class XError(object):
            _type_name = "error"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def INTERNAL(self) -> str:
                return self.get("internal")
        
            @property
            def NO_ACCESS(self) -> str:
                return self.get("no-access")
        
            @property
            def INVALID_ARGUMENT(self) -> str:
                return self.get("invalid-argument")
        
            @property
            def UNKNOWN_COMMAND(self) -> str:
                return self.get("unknown-command")
        
    
        class XDError(object):
            _type_name = "d-error"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def UNKNOWN_USER(self) -> str:
                return self.get("unknown-user")
        
            @property
            def INVALID_USER(self) -> str:
                return self.get("invalid-user")
        
            @property
            def INVALID_USER_MENTION(self) -> str:
                return self.get("invalid-user-mention")
        
            @property
            def UNKNOWN_MEMBER(self) -> str:
                return self.get("unknown-member")
        
            @property
            def INVALID_MEMBER(self) -> str:
                return self.get("invalid-member")
        
            @property
            def INVALID_MEMBER_MENTION(self) -> str:
                return self.get("invalid-member-mention")
        
            @property
            def USER_NOT_MEMBER(self) -> str:
                return self.get("user-not-member")
        
            @property
            def UNKNOWN_CHANNEL(self) -> str:
                return self.get("unknown-channel")
        
            @property
            def INVALID_CHANNEL(self) -> str:
                return self.get("invalid-channel")
        
            @property
            def CHANNEL_NOT_TEXT(self) -> str:
                return self.get("channel-not-text")
        
            @property
            def CHANNEL_NOT_VOICE(self) -> str:
                return self.get("channel-not-voice")
        
            @property
            def UNKNOWN_ROLE(self) -> str:
                return self.get("unknown-role")
        
            @property
            def INVALID_ROLE(self) -> str:
                return self.get("invalid-role")
        
    
        class XDbError(object):
            _type_name = "db-error"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def UNKNOWN_USER(self) -> str:
                return self.get("unknown-user")
        
            @property
            def INVALID_USER(self) -> str:
                return self.get("invalid-user")
        
    
        class XConfigError(object):
            _type_name = "config-error"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def INVALID_PATH(self) -> str:
                return self.get("invalid-path")
        
            @property
            def PARSE_FAIL(self) -> str:
                return self.get("parse-fail")
        
    
        class XErrorOther(object):
            _type_name = "error-other"
        
            def __init__(self, section) -> None:
                self._section = section
        
            def get(self, string_name) -> str:
                return self._section.get(self._type_name, string_name)
        
            @property
            def INVALID_RANK(self) -> str:
                return self.get("invalid-rank")
        
            @property
            def UNKNOWN_RANK(self) -> str:
                return self.get("unknown-rank")
        
            @property
            def DUPLICATE_RANK(self) -> str:
                return self.get("duplicate-rank")
        
            @property
            def INVALID_IGN(self) -> str:
                return self.get("invalid-ign")
        
            @property
            def DUPLICATE_IGN(self) -> str:
                return self.get("duplicate-ign")
        
            @property
            def DUPLICATE_PERSISTENT_PROFILE(self) -> str:
                return self.get("duplicate-persistent-profile")
        
            @property
            def DUPLICATE_PROFILE(self) -> str:
                return self.get("duplicate-profile")
        
    
        _section_name = "messages"
        STATUS: XStatus
        STATE: XState
        ERROR: XError
        D_ERROR: XDError
        DB_ERROR: XDbError
        CONFIG_ERROR: XConfigError
        ERROR_OTHER: XErrorOther
    
        def __init__(self, res) -> None:
            self._res = res
            self.STATUS = XStrings.XMessage.XStatus(self)
            self.STATE = XStrings.XMessage.XState(self)
            self.ERROR = XStrings.XMessage.XError(self)
            self.D_ERROR = XStrings.XMessage.XDError(self)
            self.DB_ERROR = XStrings.XMessage.XDbError(self)
            self.CONFIG_ERROR = XStrings.XMessage.XConfigError(self)
            self.ERROR_OTHER = XStrings.XMessage.XErrorOther(self)
    
        def get(self, type_name, string_name) -> str:
            return self._res.get(self._section_name, type_name, string_name)

    _lang: str
    _root: ET.Element
    _path_cache: Dict[str, str]
    NAME: XName
    EMBED: XEmbed
    MESSAGE: XMessage

    def __init__(self, lang: str = 'en') -> None:
        self._strings_path = res_path("strings.xml")
        if not os.path.isfile(self._strings_path):
            raise MissingResourceException(self._strings_path, "strings.xml")
        self._root = ET.parse(self._strings_path).getroot()
        self.NAME = XStrings.XName(self)
        self.EMBED = XStrings.XEmbed(self)
        self.MESSAGE = XStrings.XMessage(self)
        self.switch_lang(lang)

    def switch_lang(self, lang: str) -> None:
        self._lang = lang
        self._path_cache = {}

    def get(self, section_name, type_name, string_name) -> str:
        path = '.'.join([section_name, type_name, string_name])
        if path in self._path_cache:
            return self._path_cache[path]
        res = self._root.find(f'.//{section_name}/string[@lang="{self._lang}"][@type="{type_name}"][@name="{string_name}"]')
        self._path_cache[path] = res.text if res is not None else path
        return self._path_cache[path]


STRINGS = XStrings()
