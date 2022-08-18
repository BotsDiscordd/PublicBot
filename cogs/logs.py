from copy import copy

import discord
from discord.ext import commands

from config.connections import guild_coll


class ModLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        guild = await guild_coll.find_one({"Guild": before.guild.id})
        logs = self.bot.get_channel(guild['ModLogs'])
        if before.author.bot:
            return
        if before.content != after.content:
            if before.attachments:
                embed = discord.Embed(title=f"{before.author} Edited a message:", color=0xe74c3c)
                embed.set_footer(text=f"Mod Logs")
                embed.add_field(name="Previous message",
                                value=f"``{before.content}``\n Channel: {before.channel.mention}", inline=False)
                embed.set_image(before.attachments[0].url)
                embed.add_field(name="Edited Message", value=f"``{after.content}``", inline=False)
                await logs.send(embed=embed)
            else:
                if before.author.id == 191977040449110016:
                    if after.content.startswith("p!-e"):
                        new_message = copy(after.content)
                        new_message.author = before.author
                        new_message.content = "p!" + "-e"
                        await self.bot.process_commands(new_message)

                embed = discord.Embed(title=f"{before.author} Edited a message:", color=0xe74c3c)
                embed.set_footer(text=f"Mod Logs")
                embed.add_field(name="Previous message",
                                value=f"``{before.content}``\n Channel: {before.channel.mention}", inline=False)
                embed.add_field(name="Edited Message", value=f"``{after.content}``", inline=False)
                await logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, before):
        guild = await guild_coll.find_one({"Guild": before.guild.id})
        logs = self.bot.get_channel(guild['ModLogs'])
        async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
            deleter = entry.user
            if entry is None:
                deleter = before.author
        if before.author.bot:
            return
        else:
            if before.attachments:
                embed = discord.Embed(color=discord.Color.red(), title=f"{deleter.name} deleted:",
                                      description=f"``{before.content}``\n Author: {before.author.name} \n Channel: {before.channel.mention}")
                embed.set_image(url=before.attachments[0].url)
                await logs.send(embed=embed)
            else:
                embed = discord.Embed(color=discord.Color.red(), title=f"{deleter.name} deleted:",
                                      description=f"``{before.content}``\n Author: {before.author.name} \n Channel: {before.channel.mention}")
                await logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild = await guild_coll.find_one({"Guild": before.guild.id})
        logs = self.bot.get_channel(guild['ModLogs'])
        async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
            deleter = entry.user
        if len(before.roles) > len(after.roles):
            role = next(role for role in before.roles if role not in after.roles)
            embed = discord.Embed(title=f"{deleter.name} removed a role",
                                  description=f"{role.mention} was removed from {before.mention} by {deleter.mention}")
            await logs.send(embed=embed)


def setup(bot):
    bot.add_cog(ModLogs(bot))
