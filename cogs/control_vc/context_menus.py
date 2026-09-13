import discord
from cogs.control_vc.owner import claim_or_verify_owner
from cogs.control_vc.views.ban_user import allow_targets, ban_targets


async def _resolve_controlled_channel(bot, ctx: discord.ApplicationContext):
    if not isinstance(ctx.author, discord.Member):
        return None

    voice_channel = ctx.author.voice.channel if ctx.author.voice else None

    if voice_channel is None:
        await ctx.respond(
            f"You are not connected to a voice channel {ctx.author.mention}!",
            ephemeral=True,
            delete_after=15,
        )
        return None

    if bot.repos.temp_channels.get_info(voice_channel.id) is None:
        await ctx.respond(
            "This is not a controlled voice channel.",
            ephemeral=True,
            delete_after=15,
        )
        return None

    ok, error = await claim_or_verify_owner(bot, voice_channel, ctx.author)
    if not ok:
        await ctx.respond(error, ephemeral=True, delete_after=15)
        return None

    return voice_channel


async def ban_user(bot, ctx: discord.ApplicationContext, user: discord.Member):
    channel = await _resolve_controlled_channel(bot, ctx)
    if channel is None:
        return

    affected = await ban_targets(bot, channel, [user])

    if len(affected) == 1:
        embed = discord.Embed(
            title="Banned!",
            description=f"Banned {affected[0].mention} from your channel.",
            color=0x00FF00,
        )
        embed.set_footer(text="This message will disappear in 10 seconds.")
        await ctx.respond(embed=embed, ephemeral=True, delete_after=10)
    elif len(affected) > 1:
        embed = discord.Embed(
            title="Banned!",
            description=f"Banned {len(affected)} member(s)/role(s) from your channel.",
            color=0x00FF00,
        )
        embed.set_footer(text="This message will disappear in 10 seconds.")
        await ctx.respond(embed=embed, ephemeral=True, delete_after=10)
    else:
        embed = discord.Embed(
            title="No bannable users or roles were selected.",
            description="",
            color=0x00FF00,
        )
        embed.set_footer(text="This message will disappear in 10 seconds.")
        await ctx.respond(embed=embed, ephemeral=True, delete_after=10)


async def allow_user(bot, ctx: discord.ApplicationContext, user: discord.Member):
    channel = await _resolve_controlled_channel(bot, ctx)
    if channel is None:
        return

    affected = await allow_targets(bot, channel, [user])

    if len(affected) == 1:
        embed = discord.Embed(
            title="Allowed!",
            description=f"Allowed {affected[0].mention} to your channel.",
            color=0x00FF00,
        )
        embed.set_footer(text="This message will disappear in 10 seconds.")
        await ctx.respond(embed=embed, ephemeral=True, delete_after=10)
    elif len(affected) > 1:
        embed = discord.Embed(
            title="Allowed!",
            description=f"Allowed {len(affected)} member(s)/role(s) in your channel.",
            color=0x00FF00,
        )
        embed.set_footer(text="This message will disappear in 10 seconds.")
        await ctx.respond(embed=embed, ephemeral=True, delete_after=10)
    else:
        embed = discord.Embed(
            title="No allowable users or roles were selected.",
            description="",
            color=0x00FF00,
        )
        embed.set_footer(text="This message will disappear in 10 seconds.")
        await ctx.respond(embed=embed, ephemeral=True, delete_after=10)


async def mute_user(bot, ctx: discord.ApplicationContext, user: discord.Member):
    channel = await _resolve_controlled_channel(bot, ctx)
    if channel is None:
        return

    await ctx.defer(ephemeral=True)
    # Add logic and response


async def deafen_user(bot, ctx: discord.ApplicationContext, user: discord.Member):
    channel = await _resolve_controlled_channel(bot, ctx)
    if channel is None:
        return

    await ctx.defer(ephemeral=True)
    # Add logic and response


async def unmute_and_undeafen_user(bot, ctx: discord.ApplicationContext, user: discord.Member):
    channel = await _resolve_controlled_channel(bot, ctx)
    if channel is None:
        return

    await ctx.defer(ephemeral=True)
    # Add logic and response
