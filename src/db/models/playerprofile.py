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

from sqlalchemy import ForeignKey, Column, Integer, Unicode, BOOLEAN, BigInteger
from sqlalchemy.orm import relationship
from .base import BaseModel


class PlayerProfile(BaseModel):
    __tablename__ = 'player_profiles'

    ign = Column(Unicode(127), nullable=False, unique=True)
    persistent = Column(BOOLEAN, nullable=False, default=False)
    banned = Column(BOOLEAN, nullable=False, default=False)
    profile = Column(Unicode(1000), nullable=True)
    message_did = Column(BigInteger, nullable=True)

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    user = relationship("User", lazy="joined")

    def __repr__(self):
        s = super().__repr__()[:-2]
        f = "user_id={0.user_id!r},ign={0.ign!r},persistent={0.persistent!r},banned={0.banned!r}".format(self)
        return s + f + ")>"
