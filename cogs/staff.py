import asyncio
import re
import typing

import discord
from discord import ApplicationContext
from discord.ext import commands

from config.connections import guild_coll

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k] * float(v)
            except KeyError:
                raise commands.BadArgument("{} is an invalid time-key! h/m/s/d are valid!".format(k))
            except ValueError:
                raise commands.BadArgument("{} is not a number!".format(v))
        return


class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    @commands.has_any_role(978341531868094475, 978313704917581824, 978431363881525248)
    async def mute(self, ctx, member: discord.Member, *,  time: TimeConverter = None):
        await ctx.defer()
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        staff_role = discord.utils.get(ctx.guild.roles, name="Moderator Cookie")
        if role is None:
            muted = await ctx.guild.create_role(name="Muted")
        if staff_role in member.roles:
            return await ctx.send("You cannot mute another staff member")
        if role in member.roles:
            await ctx.send(f"{member} is already muted")
        else:
            await member.add_roles(role)
            embed = discord.Embed()
            embed.add_field(name="Muted", value=("Muted {} for {}s" if time else "Muted {}").format(member, time))
            await ctx.respond(embed=embed)
            if time:
                await asyncio.sleep(time)
                await member.remove_roles(role)

    @commands.slash_command()
    @commands.has_any_role(978341531868094475, 978313704917581824, 978431363881525248)
    async def unmute(self, ctx: ApplicationContext, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        await member.remove_roles(role)
        await ctx.respond(f"Unmuted {member.mention}")


def setup(bot):
    bot.add_cog(Staff(bot))
