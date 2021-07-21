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

import http.client
import json
from uuid import UUID


def is_valid_minecraft_username(username):
    """https://help.mojang.com/customer/portal/articles/928638-minecraft-usernames"""
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz1234567890_'
    allowed_len = [3, 16]

    username = username.lower()

    if len(username) < allowed_len[0] or len(username) > allowed_len[1]:
        return False

    for char in username:
        if char not in allowed_chars:
            return False

    return True


def is_valid_mojang_uuid(uuid):
    """https://minecraft-de.gamepedia.com/UUID"""
    allowed_chars = '0123456789abcdef'
    allowed_len = 32

    uuid = uuid.lower()

    if len(uuid) != 32:
        return False

    for char in uuid:
        if char not in allowed_chars:
            return False

    return True


class GetPlayerData:
    def __init__(self, identifier, timestamp=None):
        self.valid = True
        """
            Get the UUID of the player.

            Parameters
            ----------
            username: string
                The known minecraft username
            timestamp : long integer (optional)
                The time at which the player used this name, expressed as a Unix timestamp.
        """

        # Handle the timestamp
        get_args = ""
        if timestamp is not None:
            get_args = "?at=" + str(timestamp)

        # Build the request path based on the identifier
        req = ""
        if is_valid_minecraft_username(identifier):
            req = "/users/profiles/minecraft/" + identifier + get_args
        elif is_valid_mojang_uuid(identifier):
            req = "/user/profiles/" + identifier + "/names" + get_args
        else:
            self.valid = False

        # Proceed only, when the identifier was valid
        if self.valid:
            # Request the player data
            http_conn = http.client.HTTPSConnection("api.mojang.com")
            http_conn.request("GET", req,
                              headers={'User-Agent': 'https://github.com/clerie/mcuuid',
                                       'Content-Type': 'application/json'})
            response = http_conn.getresponse().read().decode("utf-8")

            # In case the answer is empty, the user dont exist
            if not response:
                self.valid = False
            # If there is an answer, fill out the variables
            else:
                # Parse the JSON
                json_data = json.loads(response)
                uuid = None

                ### Handle the response of the different requests on different ways
                # Request using username
                if is_valid_minecraft_username(identifier):
                    # The UUID
                    uuid = json_data['id']
                    # The username written correctly
                    self.username = json_data['name']
                # Request using UUID
                elif is_valid_mojang_uuid(identifier):
                    # The UUID
                    uuid = identifier

                    current_name = ""
                    current_time = 0

                    # Getting the username based on timestamp
                    for name in json_data:
                        # Prepare the JSON
                        # The first name has no change time
                        if 'changedToAt' not in name:
                            name['changedToAt'] = 0

                        # Get the right name on timestamp
                        if current_time <= name['changedToAt'] and (
                                timestamp is None or name['changedToAt'] <= timestamp):
                            current_time = name['changedToAt']
                            current_name = name['name']

                    # The username written correctly
                    self.username = current_name
                self.uuid = UUID(uuid)
