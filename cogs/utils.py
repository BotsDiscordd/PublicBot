import discord
from discord import ApplicationContext
from discord.ext import commands

from config.connections import guild_coll


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def b_status(self, ctx):
        server_count = len(self.bot.guilds)
        member_count = len(set(self.bot.get_all_members()))

        embed = discord.Embed(title="Bot Stats")
        embed.add_field(name="Server Count", value=f"{server_count}", inline=False)
        embed.add_field(name="Member Count", value=f"{member_count}", inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utils(bot))
