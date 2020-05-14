import functools
import io

import discord
from discord.ext import commands

from cogs.utilities import exceptions, imaging


class Images(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
        self.bot.imaging = imaging.Imaging(self.bot)
    
    async def create_embed(self, image: io.BytesIO, image_format: str):
        file = discord.File(filename=f'Image.{image_format.lower()}', fp=image)
        embed = discord.Embed(colour=discord.Colour.gold())
        embed.set_image(url=f'attachment://Image.{image_format.lower()}')
        return file, embed

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='user_graph', aliases=['ug'])
    async def user_graph(self, ctx, history: int = 24):
        """
        Show the bot's user count over the past 24 (by default) hours.

        `history`: The amount of hours to get the user count of.
        """

        async with ctx.channel.typing():

            query = 'WITH t AS (SELECT * from bot_growth ORDER BY date DESC LIMIT $1) SELECT * FROM t ORDER BY date'
            user_growth = await self.bot.db.fetch(query, history)

            if not user_growth:
                return await ctx.send('No growth data.')

            title = f'User growth over the last {len(user_growth)} hour(s)'
            y_axis = [record['member_count'] for record in user_growth]
            x_axis = [record['date'] for record in user_growth]

            plot = await self.bot.loop.run_in_executor(None, functools.partial(self.bot.imaging.do_growth_plot, title,
                                                                               'Datetime (YYYY-MM-DD: HH:MM)', 'Users',
                                                                               y_axis, x_axis))
            return await ctx.send(file=discord.File(fp=plot, filename='UserGraph.png'))

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='guild_graph', aliases=['gg'])
    async def guild_graph(self, ctx, history: int = 24):
        """
        Show the bot's guild count over the past 24 (by default) hours.

        `history`: The amount of hours to get the guild count of.
        """

        async with ctx.channel.typing():

            query = 'WITH t AS (SELECT * from bot_growth ORDER BY date DESC LIMIT $1) SELECT * FROM t ORDER BY date'
            guild_growth = await self.bot.db.fetch(query, history)

            if not guild_growth:
                return await ctx.send('No growth data.')

            title = f'Guild growth over the last {len(guild_growth)} hour(s)'
            y_axis = [record['guild_count'] for record in guild_growth]
            x_axis = [record['date'] for record in guild_growth]

            plot = await self.bot.loop.run_in_executor(None, functools.partial(self.bot.imaging.do_growth_plot, title,
                                                                               'Datetime (YYYY-MM-DD: HH:MM)', 'Guilds',
                                                                               y_axis, x_axis))
            return await ctx.send(file=discord.File(fp=plot, filename='GuildGraph.png'))

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='ping_graph', aliases=['pg'])
    async def ping_graph(self, ctx, history: int = 60):
        """
        Show the bot's latency over the last 60 (by default) minutes.

        `history`: The amount of minutes to get the latency of.
        """

        async with ctx.channel.typing():

            if not self.bot.pings:
                return await ctx.send('No ping data.')

            plot = await self.bot.loop.run_in_executor(None, functools.partial(self.bot.imaging.do_ping_plot, history))
            return await ctx.send(file=discord.File(fp=plot, filename='PingGraph.png'))

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='guildstatus', aliases=['serverstatus', 'gs'])
    async def guildstatus(self, ctx, graph_type: str = 'pie', all_guilds=False):
        """
        Display a graph showing how many members are in each status.

        `graph_type`: The graph type to produce. Can be either `pie` or `bar`.
        `all_guilds`: Whether the graph should be for this guild, or all guilds, Can be `True` or `False`.
        """

        if graph_type not in ('bar', 'pie'):
            raise exceptions.ArgumentError('That was not a valid graph type. Please choose either `pie` or `bar`.')

        async with ctx.channel.typing():

            plot = await self.bot.loop.run_in_executor(None, functools.partial(self.bot.imaging.do_status_plot,
                                                                               ctx, graph_type, all_guilds))
            return await ctx.send(file=discord.File(fp=plot, filename='GuildStatus.png'))

    @commands.cooldown(1, 30, commands.cooldowns.BucketType.guild)
    @commands.command(name='floor')
    async def floor(self, ctx, url: str = None):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='floor')

            file, embed = await self.create_embed(image=image, image_format=image_format)
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='colorize', aliases=['colorise'])
    async def colorize(self, ctx, url: str = None, colour: str = None):

        async with ctx.channel.typing():

            if not colour:
                colour = self.bot.utils.random_colour()

            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='colorize',
                                                                    color=colour)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Colour: {colour}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='solarize', aliases=['solarise'])
    async def solarize(self, ctx, url: str = None, threshold: float = 0.5):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='solarize',
                                                                    threshold=threshold)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Threshold: {threshold}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='sketch')
    async def sketch(self, ctx, url: str = None, radius: float = 0.5, sigma: float = 0.0, angle: float = 98.0):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='sketch',
                                                                    radius=radius, sigma=sigma, angle=angle)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Radius: {radius} | Sigma: {sigma} | Angle: {angle}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='implode')
    async def implode(self, ctx, url: str = None, amount: float = 0.35):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='implode',
                                                                    amount=amount)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Amount: {amount}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='sepiatone', aliases=['sepia_tone'])
    async def sepia_tone(self, ctx, url: str = None, threshold: float = 0.8):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='sepia_tone',
                                                                    threshold=threshold)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Threshold: {threshold}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='polaroid')
    async def polaroid(self, ctx, url: str = None, angle: float = 0.0, *, caption: str = None):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='polaroid',
                                                                    angle=angle, caption=caption)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Angle: {angle} | Caption: {caption}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='vignette')
    async def vignette(self, ctx, url: str = None, sigma: float = 3, x: int = 10, y: int = 10):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='vignette',
                                                                    sigma=sigma, x=x, y=y)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Sigma: {sigma} | X: {x} | Y: {y}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='swirl')
    async def swirl(self, ctx, url: str = None, degree: int = 90):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='swirl',
                                                                    degree=degree)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Degree: {degree}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='charcoal')
    async def charcoal(self, ctx, url: str = None, radius: float = 1.5, sigma: float = 0.5):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='charcoal',
                                                                    radius=radius, sigma=sigma)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Radius: {radius} | Sigma: {sigma}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='noise')
    async def noise(self, ctx, url: str = None, method: str = 'gaussian', attenuate: float = 0.5):

        async with ctx.channel.typing():

            methods = ['gaussian', 'impulse', 'laplacian', 'multiplicative_gaussian', 'poisson', 'random', 'uniform']
            if method not in methods:
                return await ctx.send(f'That was not a valid method. Please use one of `gaussian`, `impulse`, `'
                                      f'laplacian`, `multiplicative_gaussian`, `poisson`, `random`, `uniform`')

            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='noise',
                                                                    method=method, attenuate=attenuate)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Method: {method} | Attenuate: {attenuate}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='blueshift', aliases=['blue_shift'])
    async def blue_shift(self, ctx, url: str = None, factor: float = 1.25):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='blue_shift',
                                                                    factor=factor)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Factor: {factor}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='spread')
    async def spread(self, ctx, url: str = None, radius: float = 5.0):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='spread',
                                                                    radius=radius)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Radius: {radius}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='sharpen')
    async def sharpen(self, ctx, url: str = None, radius: float = 8, sigma: float = 4):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='sharpen',
                                                                    radius=radius, sigma=sigma)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Radius: {radius} | Sigma: {sigma}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='kuwahara')
    async def kuwahara(self, ctx, url: str = None, radius: float = 2, sigma: float = 1.5):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='kuwahara',
                                                                    radius=radius, sigma=sigma)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Radius: {radius} | Sigma: {sigma}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='emboss')
    async def emboss(self, ctx, url: str = None, radius: float = 3, sigma: float = 1.75):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='emboss',
                                                                    radius=radius, sigma=sigma)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Radius: {radius} | Sigma: {sigma}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='edge')
    async def edge(self, ctx, url: str = None, radius: float = 1):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='edge',
                                                                    radius=radius)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Radius: {radius}')
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='flip')
    async def flip(self, ctx, url: str = None):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='flip')

            file, embed = await self.create_embed(image=image, image_format=image_format)
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='flop')
    async def flop(self, ctx, url: str = None):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='flop')

            file, embed = await self.create_embed(image=image, image_format=image_format)
            return await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.cooldowns.BucketType.guild)
    @commands.command(name='rotate')
    async def rotate(self, ctx, url: str = None, degree: int = 90):

        async with ctx.channel.typing():
            image, image_format = await self.bot.imaging.edit_image(ctx=ctx, url=url, edit_type='rotate',
                                                                    degree=degree)

            file, embed = await self.create_embed(image=image, image_format=image_format)
            embed.set_footer(text=f'Degree: {degree}')
            return await ctx.send(file=file, embed=embed)


def setup(bot):
    bot.add_cog(Images(bot))
