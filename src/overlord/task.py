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
from typing import Callable, Awaitable, Dict, Optional, Union

from discord.ext import tasks
from discord.ext.tasks import Loop

from overlord.types import IOverlordTask


class OverlordTask(IOverlordTask):

    func: Callable[..., Awaitable[None]]
    kwargs: Dict[str, Union[Optional[int], asyncio.AbstractEventLoop]]

    def __init__(self, func: Callable[..., Awaitable[None]],
                 seconds: int = 0,
                 minutes: int = 0,
                 hours: int = 0,
                 count: Optional[int] = None,
                 reconnect: bool = True) -> None:
        super().__init__()
        self.func = func
        self.kwargs = {
            'seconds': seconds,
            'minutes': minutes,
            'hours': hours,
            'count': count,
            'reconnect': reconnect
        }

    def task(self, ext) -> Loop:
        self.kwargs['loop'] = asyncio.get_running_loop()

        async def method(*args, **kwargs):
            try:
                await self.func(ext, *args, **kwargs)
            except KeyboardInterrupt:
                raise
            except:
                await ext.on_error(self.func.__name__, *args, **kwargs)

        return tasks.loop(**self.kwargs)(method)
