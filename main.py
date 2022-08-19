import json
import os
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config.connections import guild_coll

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, case_insensitive=True,
                   command_prefix=commands.when_mentioned_or("p!"))
bot.load_extension('jishaku')
bot.remove_command("help")

for file in os.listdir("./cogs"):
    if file.endswith(".py"):
        bot.load_extension(f"cogs.{file[:-3]}")
        print(f"{file[:-3]} loaded!")


async def send_embed(ctx, embed):
    """
    Function that handles the sending of embeds
    -> Takes context and embed to send
    - tries to send embed in channel
    - tries to send normal message when that fails
    - tries to send embed private with information abot missing permissions
    If this all fails: https://youtu.be/dQw4w9WgXcQ
    """
    try:
        await ctx.send(embed=embed)
    except discord.Forbidden:
        try:
            await ctx.send("Hey, seems like I can't send embeds. Please check my permissions :)")
        except discord.Forbidden:
            await ctx.author.send(
                f"Hey, seems like I can't send any message in {ctx.channel.name} on {ctx.guild.name}\n"
                f"May you inform the server team about this issue? :slight_smile: ", embed=embed)


@bot.event
async def on_guild_join(guild):
    data = await guild_coll.find_one({"Guild": int(guild.id)})
    if data is None:
        await guild_coll.insert_one({"Guild": int(guild.id),
                                     "prefix": "p!",
                                     "staff_roles": [],
                                     "ModLogs": 0})


@bot.event
async def on_ready():
    for guild in bot.guilds:
        guild_check = await guild_coll.find_one({"Guild": int(guild.id)})
        print("Joined {}".format(guild.name))
        if guild_check is None:
            await guild_coll.insert_one({"Guild": int(guild.id),
                                         "prefix": "p!",
                                         "reaction_roles": [],
                                         "ModLogs": 0})
    await bot.change_presence(status=discord.Status.do_not_disturb,
                              activity=discord.Activity(type=discord.ActivityType.watching, name=f"Cookies bake"))


@bot.event
async def on_command_error(ctx, error: Exception):
    if isinstance(error, commands.UserInputError):
        embed = discord.Embed()
        embed.add_field(name="Incorrect Usage!",
                        value=f"Correct Usage: `p!{ctx.command.qualified_name} {ctx.command.signature}`")
        return await ctx.channel.send(embed=embed)
    if isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(title="Bot Missing Permissions", description=f"{error}")
        return await ctx.send(embed=embed)
    else:
        report = bot.get_guild(996196908370493593).get_channel(1002743711790268457)
        embed = discord.Embed(title='An Error has occurred', description=f'Error: \n `{error}`',
                              timestamp=ctx.message.created_at, color=discord.Color.nitro_pink())
        await report.send(embed=embed)
        print(error)
        print(f"EXCEPTION TRACE PRINT:\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))}")


@bot.command()
async def help(ctx, *input):
    prefix = "p!"  # ENTER YOUR PREFIX - loaded from config, as string or how ever you want!
    version = "Beta 1.0"  # enter version of your code

    # setting owner name - if you don't wanna be mentioned remove line 49-60 and adjust help text (line 88)
    owner = "191977040449110016"  # ENTER YOU DISCORD-ID
    owner_name = "Lightning#4225"  # ENTER YOUR USERNAME#1234

    # checks if cog parameter was given
    # if not: sending all modules and commands not associated with a cog

    async def predicate(cmd):
        try:
            return await cmd.can_run(ctx)
        except commands.CommandError:
            return False

    if not input:
        # checks if owner is on this server - used to 'tag' owner
        try:
            owner = ctx.guild.get_member(owner).mention

        except AttributeError as e:
            owner = owner

        # starting to build embed
        emb = discord.Embed(title='Commands and modules', color=discord.Color.blue(),
                            description=f'Use `{prefix}help <module>` to gain more information about that module '
                                        f':smiley:\n')

        # iterating trough cogs, gathering descriptions
        cogs_desc = ''
        for cog in bot.cogs:
            valid = False
            for command in bot.get_cog(cog).get_commands():
                if not command.hidden:
                    valid = await predicate(command)
                if valid:
                    break
            if valid:
                cogs_desc += f'`{cog}` {bot.cogs[cog].__doc__}\n'

        # adding 'list' of cogs to embed
        emb.add_field(name='Modules', value=cogs_desc, inline=False)

        # integrating trough uncategorized commands
        commands_desc = ''
        for command in bot.walk_commands():
            # if cog not in a cog
            # listing command if cog name is None and command isn't hidden
            if not command.cog_name and not command.hidden:
                commands_desc += f'{command.name} - {command.help}\n'

        # adding those commands to embed
        if commands_desc:
            emb.add_field(name='Not belonging to a module', value=commands_desc, inline=False)

        # setting information about author

        # block called when one cog-name is given
        # trying to find matching cog and it's commands
    elif len(input) == 1:

        # iterating trough cogs
        for cog in bot.cogs:
            # check if cog is the matching one
            if cog.lower() == input[0].lower():

                # making title - getting description from doc-string below class
                emb = discord.Embed(title=f'{cog} - Commands', description=bot.cogs[cog].__doc__,
                                    color=discord.Color.green())

                # getting commands from cog
                for command in bot.get_cog(cog).get_commands():
                    # if cog is not hidden
                    if not command.hidden:
                        valid = await predicate(command)
                        if valid:
                            emb.add_field(name=f"`{prefix}{command.name}`", value=command.help, inline=False)
                # found cog - breaking loop
                break

        # if input not found
        # yes, for-loops have an else statement, it's called when no 'break' was issued
        else:
            emb = discord.Embed(title="What's that?!",
                                description=f"I've never heard from a module called `{input[0]}` before :scream:",
                                color=discord.Color.orange())

        # too many cogs requested - only one at a time allowed
    elif len(input) > 1:
        emb = discord.Embed(title="That's too much.",
                            description="Please request only one module at once :sweat_smile:",
                            color=discord.Color.orange())

    else:
        emb = discord.Embed(title="It's a magical place.",
                            description="Ping lightning saying you got an error pls",
                            color=discord.Color.red())

    # sending reply embed using our own function defined above
    await send_embed(ctx, emb)


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
