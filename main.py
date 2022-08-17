import json
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config.connections import guild_coll

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, case_insensitive=True,
                   command_prefix=commands.when_mentioned_or("p!"))
bot.load_extension('jishaku')

for file in os.listdir("./cogs"):
    if file.endswith(".py"):
        bot.load_extension(f"cogs.{file[:-3]}")
        print(f"{file[:-3]} loaded!")


@bot.event
async def on_guild_join(guild):
    data = await guild_coll.find_one({"Guild": int(guild.id)})
    if data is None:
        await guild_coll.insert_one({"Guild": int(guild.id),
                                     "prefix": "p!",
                                     "staff_roles": []})


@bot.event
async def on_ready():
    for guild in bot.guilds:
        guild_check = await guild_coll.find_one({"Guild": int(guild.id)})
        print("Joined {}".format(guild.name))
        if guild_check is None:
            await guild_coll.insert_one({"Guild": int(guild.id),
                                         "prefix": "p!",
                                         "staff_roles": []})
    await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name=f"Cookies bake"))


@bot.command(pass_context=True, aliases=['-r'], hidden=True)
@commands.is_owner()
async def reload(ctx, *, msg):
    """Load a module."""
    await ctx.message.delete()
    try:
        if os.path.exists("custom_cogs/{}.py".format(msg)):
            bot.reload_extension("custom_cogs.{}".format(msg))
        elif os.path.exists("cogs/{}.py".format(msg)):
            bot.reload_extension("cogs.{}".format(msg))
        else:
            raise ImportError("No module named '{}'".format(msg))
    except Exception as e:
        await ctx.send('Failed to reload module: `{}.py`'.format(msg))
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('Reloaded module: `{}.py`'.format(msg))


@bot.command(pass_context=True, aliases=['-u'], hidden=True)
@commands.is_owner()
async def unload(ctx, *, msg):
    """Unload a module"""
    await ctx.message.delete()
    try:
        if os.path.exists("cogs/{}.py".format(msg)):
            bot.unload_extension("cogs.{}".format(msg))
        elif os.path.exists("custom_cogs/{}.py".format(msg)):
            bot.unload_extension("custom_cogs.{}".format(msg))
        else:
            raise ImportError("No module named '{}'".format(msg))
    except Exception as e:
        await ctx.send('Failed to unload module: `{}.py`'.format(msg))
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('Unloaded module: `{}.py`'.format(msg))


@bot.command(pass_context=True, aliases=['-l'], hidden=True)
@commands.is_owner()
async def load(ctx, *, msg):
    """Load a module"""
    await ctx.message.delete()
    try:
        if os.path.exists("cogs/{}.py".format(msg)):
            bot.load_extension("cogs.{}".format(msg))
        elif os.path.exists("custom_cogs/{}.py".format(msg)):
            bot.load_extension("custom_cogs.{}".format(msg))
        else:
            raise ImportError("No module named '{}'".format(msg))
    except Exception as e:
        await ctx.send('Failed to load module: `{}.py`'.format(msg))
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('Loaded module: `{}.py`'.format(msg))


@bot.command()
async def ping(ctx):
    await ctx.send("The bots ping is currently: `{0}`".format(round(bot.latency * 1000)))


bot.run(os.getenv('BOT_TOKEN'))
