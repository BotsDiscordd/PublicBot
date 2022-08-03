import json
import os

import discord
from discord.ext import commands


intents = discord.Intents.all()
bot = discord.AutoShardedBot(shard_count=10, intents=intents, case_insensitive=True,
                             command_prefix=commands.when_mentioned_or("p!"))

bot.run(os.getenv('BOT_TOKEN'))
