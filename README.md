# MC Discord Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Minecraft Discord Bot

## Features

Control whitelist via specified channel

Add people to whitelist manually

Rank people (integration with various mods and plugins)

### Usage

Clone repository

```sh
git clone https://github.com/Mathtin/mc-discord-bot.git
cd mc-discord-bot
```

Install the dependencies via pip

```sh
python3 -m pip install -r requirements.txt
```

Create .env file  

```sh
cp .env.template .env
nano .env
```

Create configuration file  

```sh
cp mc-bot_example.cfg mc-bot.cfg
nano mc-bot.cfg
```

Start app

```sh
python3 src/main.py
```

### Docker

Pull latest image from hub

```sh
docker pull mathtin/mc-discord-bot:latest
```

Create env and configuration files

```sh
wget -O mc-bot.env https://raw.githubusercontent.com/Mathtin/mc-discord-bot/master/.env.template
nano mc-bot.env
wget -O mc-bot.cfg https://raw.githubusercontent.com/Mathtin/mc-discord-bot/master/mc-bot_example.cfg
nano mc-bot.cfg
```

Run container (attach to network where your db is reachable)

```sh
docker run -d --name mc-bot \ 
           -e $(pwd)/mc-bot.env \
           -v $(pwd)/mc-bot.cfg:/app/mc-bot.cfg \
           --network=multi-host-network \
           mathtin/mc-discord-bot:latest
```

Or you can use docker compose (postgres+mc-discord-bot) using files from repository

```sh
wget https://raw.githubusercontent.com/Mathtin/mc-discord-bot/master/docker-compose.yml
mkdir scripts && wget -P scripts https://raw.githubusercontent.com/Mathtin/mc-discord-bot/master/scripts/01_users.sql
wget https://raw.githubusercontent.com/Mathtin/mc-discord-bot/master/database.env
```

Set password in database.env

Note: `DATABASE_ACCESS_URL=postgresql+asyncpg://root:PASTE_PASSWORD_HERE@postgres_container/mc_discord_bot`

### Development

Issues and pull requests are highly welcomed!

Based on [Overlord project](https://github.com/Mathtin/overlord).

# Author

Copyright (c) 2021 Daniel [Mathtin](https://github.com/Mathtin/) Shiko