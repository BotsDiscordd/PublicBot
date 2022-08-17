import discord
from discord.ext import commands


class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = self.bot.get_guild(962300982069432320)
        if member.guild == guild:
            role = self.bot.get_guild(962300982069432320).get_role(979548707143946251)
            await member.add_roles(role)


def setup(bot):
    bot.add_cog(Listeners(bot))
