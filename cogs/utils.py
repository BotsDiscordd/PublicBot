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

    @commands.slash_command()
    async def reaction_roles(self, ctx: ApplicationContext):
        return

    @commands.slash_command()
    async def suggest(self, ctx: ApplicationContext, arg: str):
        suggestion_channel = self.bot.get_guild(996196908370493593).get_channel(1010040591431761951)
        embed = discord.Embed(description=arg)
        embed.set_author(icon_url=ctx.author.avatar.url, name=f"{ctx.author.name}#{ctx.author.discriminator}")
        message = await suggestion_channel.send(embed=embed)
        await ctx.channel.create_thread(name=arg, message=message, auto_archive_duration=10080)




    #@commands.command()
    #async def set

def setup(bot):
    bot.add_cog(Utils(bot))
