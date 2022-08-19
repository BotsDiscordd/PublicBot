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
    @discord.default_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, time: TimeConverter = None):
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
    async def unmute(self, ctx: ApplicationContext, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        await member.remove_roles(role)
        await ctx.respond(f"Unmuted {member.mention}")

    @commands.command()
    @commands.has_any_role("Cookie Queen", "Administrator Cookie", "Moderator Cookie")
    async def ban(self, ctx, member: discord.User, reason: str = "Breaking the rules", del_message_days: int = 0):
        try:
            whitelisted = ["Cookie Queen", "Administrator Cookie", "Moderator Cookie"]

            if ctx.author.top_role.name not in whitelisted:
                if member is None:
                    await ctx.channel.send("Please provide a user to ban!")
                    return

                await ctx.guild.ban(member,
                                    reason=f"mod: {ctx.author} | reason: {reason[:400]}{'...' if len(reason) > 400 else ''}",
                                    delete_message_days=del_message_days)
                embed = discord.Embed(color=0xff0000)
                embed.add_field(name='Banned ⚠️', value=f'{member} has been banned: `{reason}`')
                await ctx.send(embed=embed)
            else:
                await ctx.channel.send("Ban failed - You can't ban someone with hightened permissions")
        except commands.MissingRole:
            await ctx.channel.send("Ban failed - You're missing permissions")

    @commands.slash_command()
    @discord.default_permissions(manage_roles=True)
    async def role(self, ctx: ApplicationContext, user: discord.Member, *, role: discord.Role):
        await ctx.defer()
        if role.position > ctx.author.top_role.position:
            return await ctx.respond('**:x: | You cannot give that role since it is higher than your highest role**',
                                     ephemeral=True)
        if role in user.roles:
            return await ctx.respond(f"{user} already has that role", ephemeral=True)
        try:
            await user.add_roles(role)
            embed = discord.Embed()
            embed.set_author(name='Role 📜')
            embed.add_field(name='Role added', value=f'Gave {role.mention} to {user.mention}')
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            return await ctx.respond("I do not have permission to give that role to that user", ephemeral=True)

    logs = discord.SlashCommandGroup(
        "log",
        "set the log channel for your server", default_member_permissions=discord.Permissions(manage_roles=True)
    )

    @logs.command()
    @discord.default_permissions(manage_roles=True)
    async def set(self, ctx: ApplicationContext, channel: discord.TextChannel):
        await ctx.defer()
        logs = await guild_coll.find_one({"Guild": int(ctx.guild_id)})
        if logs is None:
            return
        await guild_coll.update_one({"Guild": int(ctx.guild_id)}, {"$set": {"ModLogs": int(channel.id)}})
        await ctx.respond(f"{channel.mention} is now the channel for mod logs")

    @logs.command()
    async def update(self, ctx: ApplicationContext, channel: discord.TextChannel):
        await ctx.defer()
        logs = await guild_coll.find_one({"Guild": int(ctx.guild_id)})
        if logs is None:
            return
        await guild_coll.update_one({"Guild": int(ctx.guild_id)}, {"$set": {"ModLogs": int(channel.id)}})

        await ctx.respond(f"Updated logs to {channel.mention}")

    @commands.user_command(name="User Info")
    async def userinfo(self, ctx: ApplicationContext, member: discord.Member):
        if member is None:
            member = ctx.message.author
        else:
            member = member

        roles = list(sorted(member.roles, key=lambda role: role.position))

        embed = discord.Embed(colour=member.colour.purple())
        embed.set_author(name=f"User Info - {member}")
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        embed.add_field(name="ID:", value=member.id, inline=False)
        embed.add_field(name="Guild name:", value=member.display_name, inline=False)
        embed.add_field(name="Created at:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p"), inline=False)
        embed.add_field(name="Joined at:", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p"), inline=False)
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join([role.mention for role in roles][1:]),
                        inline=False)
        embed.add_field(name="Top role:", value=member.top_role.mention, inline=False)
        embed.add_field(name="Bot", value=member.bot, inline=False)

        await ctx.respond(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def purge(self, ctx, limit: int):
        """Purges messages"""

        def check(m):
            return not m.pinned

        await ctx.trigger_typing()
        await ctx.channel.purge(limit=limit + 1, check=check)
        await ctx.send(f"Successfully purged {limit} messages!",
                       delete_after=2)

    @commands.command()
    @commands.has_any_role(978313566274854922, 978313704917581824, 978431363881525248)
    async def unban(self, ctx, member: discord.User):
        try:
            if member is None:
                await ctx.channel.send("Please provide a user to unban!")
                return

            await ctx.guild.unban(member, reason=f"mod: {ctx.author}")
            embed = discord.Embed(color=0xff0000)
            embed.add_field(name='Unban', value=f'{member} has been unbanned')
            await ctx.send(embed=embed)

        except commands.MissingRole:
            await ctx.channel.send("Unban failed - You're missing permissions")

    reactions = discord.SlashCommandGroup(
        "reactions",
        "setup reaction roles for your server", default_member_permissions=discord.Permissions(manage_roles=True)
    )

    @reactions.command()
    async def add(self, ctx: ApplicationContext, role: typing.Optional[discord.Role]):
        await ctx.defer()
        data = await guild_coll.find_one({"Guild": int(ctx.guild_id)})
        if data['reaction_roles'] is None:
            await guild_coll.update_one({"Guild": int(ctx.guild_id)}, {"$set": {"reaction_roles": []}})
        await guild_coll.update_one({"Guild": int(ctx.guild_id)}, {"$push": {"reaction_roles": role.id}})
        await ctx.respond(f"Added {role.name} to the list of reaction roles.\n Current roles {data['reaction_roles']}")



def setup(bot):
    bot.add_cog(Staff(bot))
