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

from sqlalchemy import Column, Integer, VARCHAR, BigInteger, Unicode
from .base import BaseModel


class User(BaseModel):
    __tablename__ = 'users'

    did = Column(BigInteger, nullable=False, unique=True)
    name = Column(Unicode(127), nullable=False)
    disc = Column(Integer, nullable=False)
    display_name = Column(Unicode(127), nullable=True)
    roles = Column(VARCHAR(127), nullable=True)

    def __repr__(self):
        s = super().__repr__()[:-2]
        f = ",did={0.did!r},name={0.name!r},disc={0.disc!r},display_name={0.display_name!r},roles={0.roles!r}".format(
            self)
        return s + f + ")>"
