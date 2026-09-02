import logging
import asyncio
import discord
from discord.ui import View
from cogs.control_vc.enums import ChannelState
from cogs.control_vc.embeds import ChannelInfoEmbed, ControlIconsEmbed
from cogs.control_vc.owner import is_owner
from cogs.control_vc.modals.user_limit_modal import UserLimitModal
from cogs.control_vc.modals.change_name_modal import ChangeNameModal
from cogs.control_vc.views.give_ownership import GiveOwnershipView
from cogs.control_vc.views.ban_user import BanUserView

logger = logging.getLogger(__name__)


def _custom_id(channel_id, action):
    return f"ctrl:{channel_id}:{action}"


async def update_overwrites(bot, channel, new_overwrite):
    # Gets the default_role_id as stored by the creator channel db
    creator_id = bot.repos.temp_channels.get_info(channel.id).creator_id
    default_role_id = bot.repos.creator_channels.get_info(creator_id).default_role_id
    if default_role_id is None:
        default_role = channel.guild.default_role
    else:
        default_role = channel.guild.get_role(default_role_id)

    overwrites = channel.overwrites
    overwrites[default_role] = new_overwrite
    await channel.edit(overwrites=overwrites)


class ControlView(View):
    def __init__(self, bot, temp_channel):
        super().__init__(timeout=None)
        self.bot = bot
        self.temp_channel = temp_channel
        self.control_message = None

        self.create_items()

    async def send_initial_message(self, owner_member, channel_name=None):
        embed = discord.Embed(color=discord.Color.green())
        embed.description = f"This is a [FOSS](<https://wikipedia.org/wiki/Free_and_open-source_software>) project.\nYou can contribute [here](<https://github.com/jack-schultz/Robotnic>) or support it [here](<https://github.com/sponsors/jack-schultz>)."
        embeds = [
            embed,
            ChannelInfoEmbed(self.bot, self.temp_channel, title=channel_name)
        ]
        if "description_embed" in self.bot.repos.guild_settings.get(self.temp_channel.guild.id)["control_options"]:
            embeds.append(ControlIconsEmbed(self.bot, self.temp_channel))

        is_mention_owner = self.bot.repos.guild_settings.get(self.temp_channel.guild.id)["mention_owner_bool"]

        self.control_message = await self.temp_channel.send(embeds=embeds, view=self)

        if is_mention_owner:
            await self.temp_channel.send(f"{owner_member.mention}, this is *your* vc. Use the message above to control it.", delete_after=1)

    def create_items(self):
        channel_id = self.temp_channel.id
        control_options = self.bot.repos.guild_settings.get(self.temp_channel.guild.id)["control_options"]
        guild_settings = self.bot.repos.guild_settings.get(self.temp_channel.guild.id)
        enabled_controls = list(guild_settings["enabled_controls"])

        channel_state = self.bot.repos.temp_channels.get_info(self.temp_channel.id).channel_state

        if "buttons" in control_options:
            lock_button = discord.ui.Button(
                label="",
                emoji="🔒",
                style=discord.ButtonStyle.success if channel_state == ChannelState.LOCKED.value else discord.ButtonStyle.primary,
                row=3,
                custom_id=_custom_id(channel_id, "lock"),
            )
            hide_button = discord.ui.Button(
                label="",
                emoji="🙈",
                style=discord.ButtonStyle.success if channel_state == ChannelState.HIDDEN.value else discord.ButtonStyle.primary,
                row=3,
                custom_id=_custom_id(channel_id, "hide"),
            )
            public_button = discord.ui.Button(
                label="",
                emoji="🌐",
                style=discord.ButtonStyle.success if channel_state == ChannelState.PUBLIC.value else discord.ButtonStyle.primary,
                row=3,
                custom_id=_custom_id(channel_id, "public"),
            )
            name_button = discord.ui.Button(
                label="",
                emoji="🏷️",
                style=discord.ButtonStyle.secondary,
                row=0,
                custom_id=_custom_id(channel_id, "rename"),
            )
            limit_button = discord.ui.Button(
                label="",
                emoji="🚧",
                style=discord.ButtonStyle.secondary,
                row=0,
                custom_id=_custom_id(channel_id, "limit"),
            )
            clear_button = discord.ui.Button(
                label="",
                emoji="🧽",
                style=discord.ButtonStyle.danger,
                row=1,
                custom_id=_custom_id(channel_id, "clear"),
            )
            delete_button = discord.ui.Button(
                label="",
                emoji="🗑️",
                style=discord.ButtonStyle.danger,
                row=1,
                custom_id=_custom_id(channel_id, "delete"),
            )
            give_button = discord.ui.Button(
                label="",
                emoji="🎁",
                style=discord.ButtonStyle.success,
                row=0,
                custom_id=_custom_id(channel_id, "give"),
            )
            ban_button = discord.ui.Button(
                label="",
                emoji="🔨",
                style=discord.ButtonStyle.danger,
                row=1,
                custom_id=_custom_id(channel_id, "ban"),
            )
            banner_button = discord.ui.Button(
                label="- - - - - - - - - - - - - - - - - - - -",
                style=discord.ButtonStyle.secondary,
                row=2,
                disabled=True,
                custom_id=_custom_id(channel_id, "banner"),
            )

            if "rename" in enabled_controls:
                self.add_item(name_button)
            if "limit" in enabled_controls:
                self.add_item(limit_button)
            if "clear" in enabled_controls:
                self.add_item(clear_button)
            if "ban" in enabled_controls:
                self.add_item(ban_button)
            if "give" in enabled_controls:
                self.add_item(give_button)
            if "delete" in enabled_controls:
                self.add_item(delete_button)

            if "lock" in enabled_controls or "hide" in enabled_controls:
                self.add_item(banner_button)
                self.add_item(public_button)
            if "lock" in enabled_controls:
                self.add_item(lock_button)
            if "hide" in enabled_controls:
                self.add_item(hide_button)

            public_button.callback = self.public_button_callback
            lock_button.callback = self.lock_button_callback
            hide_button.callback = self.hide_button_callback
            name_button.callback = self.name_button_callback
            limit_button.callback = self.limit_button_callback
            clear_button.callback = self.clear_button_callback
            delete_button.callback = self.delete_button_callback
            give_button.callback = self.give_button_callback
            ban_button.callback = self.ban_button_callback

            if "labels" in control_options:
                lock_button.label = "Lock"
                hide_button.label = "Hide"
                public_button.label = "Public"
                name_button.label = "Rename"
                limit_button.label = "Edit Limit"
                clear_button.label = "Clear Msgs"
                delete_button.label = "Delete"
                give_button.label = "Give"
                ban_button.label = "Ban/Allow User"

        if not enabled_controls:
            button = discord.ui.Button(
                label="No Available Options",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                custom_id=_custom_id(channel_id, "no_options"),
            )
            self.add_item(button)
            return

        if "dropdown" in control_options:
            class ActionDropdown(discord.ui.Select):
                def __init__(select_self):
                    options = []

                    if "rename" in enabled_controls:
                        options.append(discord.SelectOption(value="rename", label="Rename Channel", emoji="🏷️"))
                    if "limit" in enabled_controls:
                        options.append(discord.SelectOption(value="limit", label="Edit User Limit", emoji="🚧"))
                    if "clear" in enabled_controls:
                        options.append(discord.SelectOption(value="clear", label="Clear Messages", emoji="🧽"))
                    if "ban" in enabled_controls:
                        options.append(discord.SelectOption(value="ban", label="Ban/Allow Users or Roles", emoji="🔨"))
                    if "give" in enabled_controls:
                        options.append(discord.SelectOption(value="give", label="Give Ownership", emoji="🎁"))
                    if "delete" in enabled_controls:
                        options.append(discord.SelectOption(value="delete", label="Delete Channel", emoji="🗑️"))

                    super().__init__(
                        placeholder="Settings",
                        min_values=1,
                        max_values=1,
                        options=options,
                        custom_id=_custom_id(channel_id, "action_select"),
                    )

                async def callback(select_self, interaction: discord.Interaction):
                    choice = select_self.values[0]

                    if choice == "rename":
                        await self.name_button_callback(interaction)
                    elif choice == "limit":
                        await self.limit_button_callback(interaction)
                    elif choice == "give":
                        await self.give_button_callback(interaction)
                    elif choice == "clear":
                        await self.clear_button_callback(interaction)
                    elif choice == "ban":
                        await self.ban_button_callback(interaction)
                    elif choice == "delete":
                        await self.delete_button_callback(interaction)

                    await self.recreate_items(interaction)

            class StateDropdown(discord.ui.Select):
                def __init__(select_self):
                    options = []

                    if len({"lock", "hide"}.intersection(enabled_controls)) > 0:
                        options.append(discord.SelectOption(value="public", label="Public", emoji="🌐", default=channel_state == ChannelState.PUBLIC.value))
                    if "lock" in enabled_controls:
                        options.append(discord.SelectOption(value="lock", label="Locked", emoji="🔒", default=channel_state == ChannelState.LOCKED.value))
                    if "hide" in enabled_controls:
                        options.append(discord.SelectOption(value="hide", label="Hidden", emoji="🙈", default=channel_state == ChannelState.HIDDEN.value))

                    super().__init__(
                        placeholder="Control Access",
                        min_values=1,
                        max_values=1,
                        options=options,
                        custom_id=_custom_id(channel_id, "state_select"),
                    )

                async def callback(select_self, interaction: discord.Interaction):
                    choice = select_self.values[0]

                    if choice == "public":
                        await self.public_button_callback(interaction)
                    elif choice == "lock":
                        await self.lock_button_callback(interaction)
                    elif choice == "hide":
                        await self.hide_button_callback(interaction)

            if len({"rename", "limit", "clear", "ban", "give", "delete"}.intersection(enabled_controls)) > 0:
                self.add_item(ActionDropdown())
            if len({"lock", "hide"}.intersection(enabled_controls)) > 0:
                self.add_item(StateDropdown())

    async def update_view(self, message=None):
        target_message = message or self.control_message
        if target_message is None:
            return
        try:
            await target_message.edit(view=self, embeds=target_message.embeds)
        except discord.NotFound:
            logger.debug(f"Control message gone while updating view for temp channel {self.temp_channel.id} in guild '{self.temp_channel.guild.name}'")

    async def recreate_items(self, interaction=None):
        self.clear_items()
        self.create_items()
        message = self.control_message
        if message is None and interaction is not None:
            message = interaction.message
        await self.update_view(message)

    async def on_timeout(self):
        logger.warning(f"Control message timed out for temp channel {self.temp_channel.id} in guild '{self.temp_channel.guild.name}'")
        self.clear_items()
        self.add_item(
            discord.ui.Button(
                label="This control message has expired",
                style=discord.ButtonStyle.secondary,
                disabled=True
            )
        )
        # Edit the message to show the new view
        try:
            await self.control_message.edit(view=self)
        except Exception as e:
            logger.warning(
                f"Failed to update control message after timeout for temp channel {self.temp_channel.id} in guild '{self.temp_channel.guild.name}': {e}"
            )

    # --- Callbacks ---
    async def public_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        logger.debug(
            f"Setting temp channel {interaction.channel.id} to public in guild '{interaction.guild.name}'"
        )
        self.bot.repos.temp_channels.change_state(interaction.channel.id, ChannelState.PUBLIC.value)

        new_overwrite = discord.PermissionOverwrite(view_channel=True, connect=True)
        await update_overwrites(self.bot, interaction.channel, new_overwrite)
        await self.recreate_items(interaction)

    async def lock_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        logger.debug(
            f"Setting temp channel {interaction.channel.id} to locked in guild '{interaction.guild.name}'"
        )
        self.bot.repos.temp_channels.change_state(interaction.channel.id, ChannelState.LOCKED.value)

        new_overwrite = discord.PermissionOverwrite(view_channel=True, connect=False)
        await update_overwrites(self.bot, interaction.channel, new_overwrite)
        await self.recreate_items(interaction)

    async def hide_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        logger.debug(
            f"Setting temp channel {interaction.channel.id} to hidden in guild '{interaction.guild.name}'"
        )
        self.bot.repos.temp_channels.change_state(interaction.channel.id, ChannelState.HIDDEN.value)

        new_overwrite = discord.PermissionOverwrite(view_channel=False, connect=False)
        await update_overwrites(self.bot, interaction.channel, new_overwrite)
        await self.recreate_items(interaction)

    async def name_button_callback(self, interaction: discord.Interaction):
        if not await is_owner(self, interaction):
            return
        modal = ChangeNameModal(self.bot, interaction.channel)
        await interaction.response.send_modal(modal)

    async def limit_button_callback(self, interaction: discord.Interaction):
        if not await is_owner(self, interaction):
            return
        modal = UserLimitModal(self.bot, interaction.channel)
        await interaction.response.send_modal(modal)

    async def clear_button_callback(self, interaction: discord.Interaction):
        if not await is_owner(self, interaction):
            return
        await interaction.response.defer(ephemeral=True)

        excluded_message_ids = []
        if interaction.message:
            excluded_message_ids.append(interaction.message.id)

        # Fetch messages from the channel
        messages_to_delete = []
        async for message in interaction.channel.history(limit=None):
            if message.id not in excluded_message_ids:
                messages_to_delete.append(message)

        # Bulk delete the filtered messages
        if messages_to_delete:
            try:
                await interaction.channel.delete_messages(messages_to_delete)
            except Exception as e:
                logger.warning(
                    f"Failed to bulk delete messages in temp channel {interaction.channel.id} in guild '{interaction.guild.name}': {e}"
                )
                await interaction.followup.send(f"Failed, {e}", ephemeral=True, delete_after=15)

        embed = discord.Embed(
            title="Messages Deleted",
            description=f"Deleted `{len(messages_to_delete)}` messages.",
            color=discord.Color.red()
        )
        embed.set_footer(text="This message will disappear in 15 seconds.")
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)

    async def delete_button_callback(self, interaction: discord.Interaction):
        if not await is_owner(self, interaction):
            return
        await interaction.response.defer(ephemeral=True)

        # Ask for confirmation
        embed = discord.Embed(
            title="Channel Deletion Confirmation",
            description="Are you sure you want to delete this channel? Reply with 'yes' within 60 seconds to confirm.",
            color=discord.Color.orange()  # You can adjust the color as needed
        )
        embed.set_footer(text="Awaiting your response...")
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=60)

        def check(message: discord.Message):
            # Check that the message is from the same user in the same channel and contains 'yes'
            return message.author == interaction.user and message.channel == interaction.channel and message.content.lower() == "yes"

        try:
            # Wait for the user to respond with "yes" within 60 seconds
            confirmation_message = await self.bot.wait_for("message", check=check, timeout=60)

            # Delete the channel from the database and then delete the channel
            deleted = False
            try:
                await interaction.channel.delete()
                deleted = True
            except discord.NotFound as e:
                logger.debug(
                    f"Channel not found removing temp channel in guild '{interaction.guild.name}', handled. {e}"
                )
                deleted = True
            except discord.Forbidden as e:
                logger.debug(
                    f"Permission error removing temp channel {interaction.channel.id} in guild '{interaction.guild.name}', notifying user of missing permissions. {e}"
                )
                try:
                    await interaction.followup.send(
                        f"Sorry {interaction.user.mention}, I do not have permission to delete this channel.",
                        ephemeral=True,
                    )
                except (discord.NotFound, discord.HTTPException):
                    pass
                return
            except Exception as e:
                logger.error(
                    f"Unknown error removing temp channel {interaction.channel.id} in guild '{interaction.guild.name}': {e}"
                )
                return

            if deleted:
                self.bot.repos.temp_channels.remove(interaction.channel.id)
                logger.debug(
                    f"Deleted temp channel {interaction.channel.id} via control message confirmation in guild '{interaction.guild.name}'"
                )
        except asyncio.TimeoutError:
            logger.debug(
                f"Channel deletion confirmation timed out for temp channel {interaction.channel.id} in guild '{interaction.guild.name}', handled."
            )
            try:
                # If the user does not respond in time, send a timeout message
                embed = discord.Embed(
                    title="Channel Deletion Timed Out",
                    description="Channel deletion timed out. No action was taken.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="This message will disappear in 15 seconds.")
                await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            except (discord.NotFound, discord.HTTPException):
                pass

    async def give_button_callback(self, interaction: discord.Interaction):
        if not await is_owner(self, interaction):
            return
        await interaction.response.defer(ephemeral=True)

        await GiveOwnershipView(self.bot, interaction.channel).send_initial_message(interaction)

    async def ban_button_callback(self, interaction: discord.Interaction):
        if not await is_owner(self, interaction):
            return
        await interaction.response.defer(ephemeral=True)

        await BanUserView(self.bot, interaction.channel).send_initial_message(interaction)


async def register_persistent_control_views(bot):
    db_channels = bot.repos.temp_channels.get_ids()
    logger.info(f"Registering {len(db_channels)} persistent control views")
    for channel_id in db_channels:
        channel = bot.get_channel(channel_id)

        if channel is None:
            continue

        logger.info(f"Registering {channel.name}")

        view = ControlView(bot, channel)
        bot.add_view(view)

        try:
            async for message in channel.history(limit=10, oldest_first=True):
                if message.author.id == bot.user.id and message.components:
                    view.control_message = message
                    await message.edit(view=view, embeds=message.embeds)
                    break
        except discord.NotFound:
            logger.debug(f"Control message already gone for temp channel {channel_id} during view registration")
        except Exception as e:
            logger.warning(f"Failed to refresh control message for temp channel {channel_id}: {e}")

