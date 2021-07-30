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
import os

import ftplib


def server_exists(server_name: str):
    return os.getenv(f'FTP_DOMAIN_{server_name}') and \
           os.getenv(f'FTP_PORT_{server_name}') and \
           os.getenv(f'FTP_USERNAME_{server_name}') and \
           os.getenv(f'FTP_PASSWORD_{server_name}')


def upload_file_content(content: bytes, dst_path: str, server_name: str):
    if not server_exists(server_name):
        raise EnvironmentError(f'Server {server_name} not found')
    domain = os.getenv(f'FTP_DOMAIN_{server_name}')
    port = int(os.getenv(f'FTP_PORT_{server_name}'))
    username = os.getenv(f'FTP_USERNAME_{server_name}')
    password = os.getenv(f'FTP_PASSWORD_{server_name}')
    with ftplib.FTP() as ftp:
        ftp.connect(domain, port)
        ftp.login(username, password)
        bio = io.BytesIO(content)
        ftp.storbinary(f"STOR {dst_path}", bio)

