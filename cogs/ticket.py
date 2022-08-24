import asyncio
import datetime
from datetime import datetime

import discord
from discord import Embed, ApplicationContext
from discord.ext import commands, tasks

from config.connections import guild_coll

answers = []
users = []


class TicketButton(discord.ui.View):
    def __init__(self, bot=None):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Giveaway", emoji="💰", style=discord.ButtonStyle.blurple, custom_id="GiveawayB")
    async def ticket_giveaway(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await interaction.user.send("Giveaway Ticket Creation")
            await interaction.response.defer()
        except discord.Forbidden:
            await interaction.response.send_message(content="I couldn't dm you please turn dms on to proceed with the "
                                                            "ticket process", ephemeral=True)

        questions = ["What is the prize",
                     "How many winners",
                     "How long will the giveaway last"]

        for i, question in enumerate(questions):
            embed = Embed(title=f"Question {i}",
                          description=question)
            msg = await interaction.user.send(embed=embed)
            try:
                message = await interaction.client.wait_for('message', timeout=100, check=lambda
                    m: m.channel.id == msg.channel.id and m.author.id == interaction.user.id)
            except asyncio.TimeoutError:
                return await interaction.user.send("You took to long to respond please try again")
            answers.append(message.content)
        guild = await guild_coll.find_one({"Guild": interaction.guild.id})
        logs = self.bot.get_channel(guild['Ticket_Cat'])
        guild_get = interaction.client.get_guild(guild)
        ticket_cat = discord.utils.get(guild_get.categories, name=f"{logs}")
        ticket_channel = await ticket_cat.create_text_channel(
            name=f"{interaction.user.name} - {interaction.user.discriminator}",
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False),
                interaction.guild.get_role(
                    978341531868094475): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True),
                interaction.guild.get_role(
                    978431363881525248): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True)})
        embed = Embed(title=f"Giveaway Creation",
                      description=f"Host: {interaction.user.mention}\n"
                                  f"Prize: {answers[0]}\n"
                                  f"Giveaway Time: {answers[2]}\n"
                                  f"Winner Amount: {answers[1]}"
                                  f"\n\n To close the ticket click the Close button.\n -add: Adds a user to the ticket")
        msg = await ticket_channel.send(embed=embed, view=InnerTicketView())
        await ticket_channel.send('<@867023276882657300>')
        await msg.pin()

    @discord.ui.button(label="Normal", emoji="📩", style=discord.ButtonStyle.green, custom_id="Normal")
    async def norm_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(content="Creating Ticket", ephemeral=True)
        guild = await guild_coll.find_one({"Guild": interaction.guild.id})
        logs = self.bot.get_channel(guild['Ticket_Cat'])
        guild_get = interaction.client.get_guild(guild)
        ticket_cat = discord.utils.get(guild_get.categories, name=f"{logs}")
        ticket_channel = await ticket_cat.create_text_channel(
            name=f"{interaction.user.name} - {interaction.user.discriminator}",
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False),
                interaction.guild.get_role(
                    978341531868094475): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True),
                interaction.guild.get_role(
                    978431363881525248): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True)})
        embed = Embed(title=f"Ticket Creation",
                      description=f"Thank you for creating a ticket.\n Staff will be with you shortly\n"
                                  f"\n\n To close the ticket click the Close button.\n -add: Adds a user to the ticket\n"
                                  f"Created by {interaction.user.mention}")
        msg = await ticket_channel.send(embed=embed, view=InnerTicketView())
        await ticket_channel.send('<@867023276882657300>')
        await msg.pin()
        await guild_coll.insert_one({"Ticket": int(ticket_channel.id),
                                     "Creator": int(interaction.user.id),
                                     "closed": False})


class InnerTicketView(discord.ui.View):
    def __init__(self, bot=None):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close Ticket", emoji="❌", style=discord.ButtonStyle.blurple, custom_id="Close")
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.channel.delete()
        doc = await guild_coll.find_one({"Guild": interaction.guild.id})
        logs = self.bot.get_channel(doc['ModLogs'])
        fileName = f"{interaction.channel.name}.txt"
        with open(fileName, "w") as file:
            async for msg in interaction.channel.history(limit=None):
                file.write(f"{msg.created_at} - {msg.author.display_name}:{msg.clean_content}\n")
        file = discord.File(fileName)
        t_log = interaction.client.get_channel(logs)
        await t_log.send(content=f"Ticket Closed By {interaction.user.mention}", file=file)


class AdminCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticket")
    @commands.has_permissions(manage_channels=True)
    async def create_ticket_message(self, ctx):
        embed = Embed(
            title="Create a ticket",
            description="Ticket Types\n"
                        "🤑  - Giveaway creation\n"
                        "📩 - Normal Ticket Creation"
        )
        await ctx.send(embed=embed, view=TicketButton())

    @commands.command()
    async def add(self, ctx, user: discord.Member):
        doc = await self.bot.guild_coll.find_one({"Ticket": ctx.channel.id})
        if not doc:
            return await ctx.reply(f"This isn\'t a ticket channel")
        else:
            await ctx.channel.set_permissions(user, read_messages=True)
            await ctx.reply(f"Added {user.mention} to ticket")

    @commands.command()
    async def remove(self, ctx, user: discord.Member):
        doc = await self.bot.guild_coll.find_one({"Ticket": ctx.channel.id})
        if not doc:
            return await ctx.reply(f"This isn\'t a ticket channel")
        else:
            await ctx.channel.set_permissions(user, read_messages=False)
            await ctx.reply(f"Removed {user.mention} to ticket")

    @commands.slash_command()
    @discord.default_permissions(manage_channels=True)
    async def set_ticket_category(self, ctx: ApplicationContext, channel: discord.CategoryChannel):
        await ctx.defer()
        logs = await guild_coll.find_one({"Guild": int(ctx.guild_id)})
        if logs is None:
            return
        await guild_coll.update_one({"Guild": int(ctx.guild_id)}, {"$set": {"Ticket_Cat": channel.name}})


def setup(bot):
    bot.add_cog(AdminCommands(bot))