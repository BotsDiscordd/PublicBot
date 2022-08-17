from inspect import getsource
from time import time

import discord
import os
import sys
import asyncio
import psutil
import logging
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter
from copy import copy


def prepare(string):
    arr = string.strip("```").replace("py\n", "").replace("python\n", "").split("\n")
    if not arr[::-1][0].replace(" ", "").startswith("return"):
        arr[len(arr) - 1] = "return " + arr[::-1][0]
    return "".join(f"\n\t{i}" for i in arr)


def resolve_variable(variable):
    if hasattr(variable, "__iter__"):
        var_length = len(list(variable))
        if (var_length > 100) and (not isinstance(variable, str)):
            return f"<a {type(variable).__name__} iterable with more than 100 values ({var_length})>"
        elif not var_length:
            return f"<an empty {type(variable).__name__} iterable>"

    if (not variable) and (not isinstance(variable, bool)):
        return f"<an empty {type(variable).__name__} object>"
    return variable if (len(f"{variable}") <= 1000) else f"<a long {type(variable).__name__} object with the " \
                                                         f"length of {len(f'{variable}'):,}> "


class Owner(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='..eval')
    @commands.is_owner()
    async def __eval(self, ctx, *, code: codeblock_converter):
        """Eval some code"""
        cog = self.bot.get_cog("Jishaku")
        await cog.jsk_python(ctx, argument=code)

    @commands.command(name='refresh')
    @commands.is_owner()
    async def _refresh(self, ctx):
        """Refresh the bot by invoking `jsk git pull` and `restart`"""
        cog = self.bot.get_cog("Jishaku")
        await cog.jsk_git(ctx, argument=codeblock_converter('pull origin main'))
        await asyncio.sleep(2)  # allow jsk git pull to finish
        restart = self.bot.get_command('restart')
        await ctx.invoke(restart)

    @commands.command(name='re')
    @commands.is_owner()
    async def _restart(self, ctx, flag=None):
        """
        Restart the bot. Will wait for any running commands to stop (if
         --force is not used).
        """
        if not (flag == '--force' or flag == '-f'):
            if self.bot.processing_commands > 1:
                embed = discord.Embed(
                    title='Commands in progress...',
                    description=(f'Retrying in 30 seconds. Use `{ctx.prefix}'
                                 'restart --force` to force restart.'),
                    timestamp=ctx.message.created_at)
                embed.set_footer(text=(f'{self.bot.processing_commands - 1} '
                                       'commands currently in progress'))
                await ctx.send(embed=embed)
                for i in range(10):
                    await asyncio.sleep(30)
                    if self.bot.processing_commands > 1:
                        embed = discord.Embed(
                            title='Commands in progress...',
                            description=('Retrying in 30 seconds. Use `'
                                         f'{ctx.prefix}restart --force` to '
                                         'force restart.'),
                            timestamp=ctx.message.created_at)
                        embed.set_footer(
                            text=(f'{self.bot.processing_commands - 1} '
                                  'commands currently in progress')
                        )
                        await ctx.send(embed=embed)
                    else:
                        break
                if self.bot.processing_commands > 1:
                    embed = discord.Embed(title='Restart Failed', description=(
                        f'{self.bot.processing_commands - 1} commands '
                        f'currently in progress. Use `{ctx.prefix}restart '
                        '--force` to force restart.'),
                                          timestamp=ctx.message.created_at)
                    return await ctx.send(embed=embed)
        embed = discord.Embed(title="Be right back!")
        await ctx.send(embed=embed)
        if sys.stdin.isatty() or True:  # if the bot was run from the command line, updated to default true
            try:
                p = psutil.Process(os.getpid())
                for handler in p.open_files() + p.connections():
                    os.close(handler.fd)
            except Exception as e:
                logging.error(e)
            python = sys.executable
            os.execl(python, python, *sys.argv)
        await self.bot.logout()
        embed = ctx.error('Failed to restart')
        await ctx.send(embed=embed)

    @commands.command(name='shutdown', aliases=['off', 'die', 'shut', 'kill'])
    @commands.is_owner()
    async def _shutdown(self, ctx, flag=None):
        if flag == '--wait' or flag == '-w':
            if self.bot.processing_commands > 1:
                embed = discord.Embed(title='Commands in progress...',
                                      description='Retrying in 30 seconds.',
                                      timestamp=ctx.message.created_at)
                embed.set_footer(text=(
                    f'{self.bot.processing_commands - 1} commands currently '
                    'in progress'))
                await ctx.send(embed=embed)
                for i in range(10):
                    await asyncio.sleep(30)
                    if self.bot.processing_commands > 1:
                        embed = discord.Embed(
                            title='Commands in progress...',
                            description='Retrying in 30 seconds.',
                            timestamp=ctx.message.created_at
                        )
                        embed.set_footer(
                            text=(f'{self.bot.processing_commands - 1} '
                                  'commands currently in progress'))
                        await ctx.send(embed=embed)
                    else:
                        break
        await ctx.send(embed=discord.Embed(title='Shutting Down'))
        if sys.stdin.isatty():
            await self.bot.logout()
        else:
            if len(sys.argv) > 1:
                if sys.argv[1] == 'rewrite':
                    query = 'stoprewrite'
                else:
                    query = 'stopmain'
                os.system(f"sudo {query}")
            await asyncio.sleep(1)
            await ctx.send(embed=ctx.error((
                'Failed to stop systemd service, attempting to shut down both '
                'services'
            )))
            os.system('sudo stopall')
            await asyncio.sleep(1)
            await ctx.send(embed=ctx.error((
                'Failed to stop systemd service, attempting to logout normally'
            )))
            await self.bot.logout()

    @commands.command(name='disable')
    @commands.is_owner()
    async def _disable(self, ctx, toggle: bool = None):
        """
        Disable the bot in case of an exploit, major bug, or other emergency.
        The bot will remain online, but only bot owners will be able to run
        commands on it.
        """
        self.bot.disabled = not self.bot.disabled if toggle is None else toggle
        embed = discord.Embed(title='Bot Status', timestamp=ctx.message.created_at)
        embed.add_field(name='Disabled', value=f"{self.bot.disabled}")
        await ctx.send(embed=embed)

    @commands.command(name='sudo', aliases=['su'])
    @commands.is_owner()
    async def _sudo(self, ctx, victim: discord.Member, *, command):
        """
        Reinvoke someone's command, running with all checks overridden
        """
        new_message = copy(ctx.message)
        new_message.author = victim
        new_message.content = ctx.prefix + command
        await self.bot.process_commands(new_message)

    @commands.command(pass_context=True, aliases=['-e', '-ex', '-ev'], hidden=True)
    @commands.is_owner()
    async def _eval2(self, ctx, *, code: str):
        silent = ("-s" in code)

        code = prepare(code.replace("-s", ""))
        args = {
            "discord": discord,
            "sauce": getsource,
            "sys": sys,
            "os": os,
            "imp": __import__,
            "this": self,
            "ctx": ctx
        }

        try:
            exec(f"async def func():{code}", args)
            a = time()
            response = await eval("func()", args)
            if silent or (response is None) or isinstance(response, discord.Message):
                del args, code
                return

            embed = discord.Embed()
            embed.add_field(name="Eval",
                            value=f"```py\n{resolve_variable(response)}``````{type(response).__name__} | {(time() - a) / 1000} ms```")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed()
            embed.add_field(name="Error...", value=f"Error occurred:```\n{type(e).__name__}: {str(e)}```")
            await ctx.send(embed=embed)

        del args, code, silent


def setup(bot):
    bot.add_cog(Owner(bot))
