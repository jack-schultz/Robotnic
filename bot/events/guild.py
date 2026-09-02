import discord


async def on_guild_join(bot, guild):
    # This event is triggered when the bot joins a new guild
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title=f"Hello {guild.name}! 🎉",
                description="Thank you for inviting me to your server! 😊\nHere are the commands to get started.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="/setup",
                value="Allows an admin to setup a channel creator (or channel hub) which dynamically creates voice channels when users join them.",
                inline=False
            )
            embed.add_field(
                name="/help",
                value="Lists all the commands available to you and what they do.",
                inline=False
            )
            embed.set_footer(text="Need more help? Reach out to support below!")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.url,
                                            label="Contact Support",
                                            url=f"https://discord.gg/rcAREJyMV5"))
            # view.add_item(discord.ui.Button(style=discord.ButtonStyle.url,
            #                                 label="Visit Website",
            #                                 url=f"link"))
            await channel.send("Thanks for inviting me!", embed=embed, view=view)
            break

    # Create the embed with the server information
    embed = discord.Embed(
        title="Joined a New Server!",
        description=f"",
        color=discord.Color.green()
    )
    embed.add_field(name="Server Name", value=guild.name, inline=True)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=f"{guild.owner} (ID: {guild.owner_id})", inline=True)
    embed.add_field(name="Member Count", value=guild.member_count, inline=True)
    embed.add_field(name="Text Channel Count", value=str(len(guild.text_channels)), inline=True)
    embed.add_field(name="Region/Locale", value=str(guild.preferred_locale), inline=True)
    unix_time = int(guild.created_at.timestamp())
    embed.add_field(name="Creation Date", value=f"<t:{unix_time}:f>\n<t:{unix_time}:R>", inline=True)
    unix_time = int(guild.get_member(bot.user.id).joined_at.timestamp())
    embed.add_field(name="Joined Date", value=f"<t:{unix_time}:f>\n<t:{unix_time}:R>", inline=True)
    await bot.BotLogService.send(event="guild_join", message=f"", embed=embed)


async def on_guild_remove(bot, guild):
    # Create the embed with the server information
    embed = discord.Embed(
        title="Left a Server!",
        description=f"",
        color=discord.Color.red()
    )
    embed.add_field(name="Server Name", value=guild.name, inline=True)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=f"{guild.owner} (ID: {guild.owner_id})", inline=True)
    embed.add_field(name="Member Count", value=guild.member_count, inline=True)
    embed.add_field(name="Text Channel Count", value=str(len(guild.text_channels)), inline=True)
    embed.add_field(name="Region/Locale", value=str(guild.preferred_locale), inline=True)
    unix_time = int(guild.created_at.timestamp())
    embed.add_field(name="Creation Date", value=f"<t:{unix_time}:f>\n<t:{unix_time}:R>", inline=True)
    unix_time = int(guild.get_member(bot.user.id).joined_at.timestamp())
    embed.add_field(name="Joined Date", value=f"<t:{unix_time}:f>\n<t:{unix_time}:R>", inline=True)
    await bot.BotLogService.send(event="guild_leave", message=f"", embed=embed)
