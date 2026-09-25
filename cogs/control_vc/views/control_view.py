import logging
import asyncio
import discord
from discord.ui import View
from cogs.control_vc.channel_actions.visibility import channel_action
from cogs.control_vc.enums import ChannelState
from cogs.control_vc.embeds import ChannelInfoEmbed, ControlIconsEmbed
from cogs.control_vc.owner import is_owner
from cogs.control_vc.modals.user_limit_modal import UserLimitModal
from cogs.control_vc.modals.change_name_modal import ChangeNameModal
from cogs.control_vc.views.give_ownership import GiveOwnershipView
from cogs.control_vc.member_actions.views import BanUserView, DeafenUserView, MuteUserView
from cogs.manage_vcs.owner_role import remove_owner_role
from cogs.manage_vcs.owner_prefix import remove_owner_prefix

logger = logging.getLogger(__name__)

ALL_CONTROLS = ("rename", "limit", "clear", "ban", "mute", "deafen", "give", "delete", "lock", "hide")
STATE_ACTIONS = frozenset({"public", "lock", "hide"})
SELECT_CUSTOM_IDS = frozenset({"action_select", "state_select"})
_MODAL_ACTIONS = frozenset({"rename", "limit"})


class ControlView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @classmethod
    def for_channel(cls, bot, channel):
        view = cls(bot)
        view.create_items(channel)
        return view

    # This is a view that discord never sees.
    # Old messages still have their for_channel layout on Discord
    # however the bot no longer has those instances in memory
    # This re-registers all handlers so clicks on those old messages still work
    # Effectively this class is split in two. One which is the Discord UI (above), the other (this one) registers the custom_ids
    @classmethod
    def for_persistence(cls, bot):
        view = cls(bot)
        view._create_persistent_items()
        return view

    async def send_control_message(self, channel, owner_member, channel_name=None):
        embed = discord.Embed(color=discord.Color.green())
        embed.description = (
            "This is a [FOSS](<https://wikipedia.org/wiki/Free_and_open-source_software>) project.\n"
            "You can contribute [here](<https://github.com/jack-schultz/Robotnic>) or support the dev "
            "[here](<https://ko-fi.com/jackschultzdev>)."
        )
        embeds = [
            embed,
            ChannelInfoEmbed(self.bot, channel, title=channel_name),
        ]
        guild_settings = self.bot.repos.guild_settings.get(channel.guild.id)
        if "description_embed" in guild_settings["control_options"]:
            embeds.append(ControlIconsEmbed(self.bot, channel))

        await channel.send(embeds=embeds, view=self)

        if guild_settings["mention_owner_bool"]:
            await channel.send(
                f"{owner_member.mention}, this is *your* vc. Use the message above to control it.",
                delete_after=1,
            )

    def _create_persistent_items(self):
        channel_state = ChannelState.PUBLIC.value
        self._add_button_items(
            ALL_CONTROLS,
            channel_state,
            control_options={"buttons": True},
        )
        self._add_dropdown_items(ALL_CONTROLS, channel_state, row=4)

    def create_items(self, channel):
        guild_settings = self.bot.repos.guild_settings.get(channel.guild.id)
        control_options = guild_settings["control_options"]
        enabled_controls = list(guild_settings["enabled_controls"])
        channel_state = self.bot.repos.temp_channels.get_info(channel.id).channel_state

        if not enabled_controls:
            self.add_item(
                discord.ui.Button(
                    label="No Available Options",
                    style=discord.ButtonStyle.secondary,
                    disabled=True,
                    custom_id="no_options",
                )
            )
            return

        if "buttons" in control_options:
            self._add_button_items(enabled_controls, channel_state, control_options)

        if "dropdown" in control_options:
            self._add_dropdown_items(enabled_controls, channel_state)

    def _add_button_items(self, enabled_controls, channel_state, control_options):
        lock_button = discord.ui.Button(
            label="",
            emoji="🔒",
            style=discord.ButtonStyle.success if channel_state == ChannelState.LOCKED.value else discord.ButtonStyle.primary,
            row=3,
            custom_id="lock",
        )
        hide_button = discord.ui.Button(
            label="",
            emoji="🙈",
            style=discord.ButtonStyle.success if channel_state == ChannelState.HIDDEN.value else discord.ButtonStyle.primary,
            row=3,
            custom_id="hide",
        )
        public_button = discord.ui.Button(
            label="",
            emoji="🌐",
            style=discord.ButtonStyle.success if channel_state == ChannelState.PUBLIC.value else discord.ButtonStyle.primary,
            row=3,
            custom_id="public",
        )
        name_button = discord.ui.Button(
            label="",
            emoji="🏷️",
            style=discord.ButtonStyle.secondary,
            row=0,
            custom_id="rename",
        )
        limit_button = discord.ui.Button(
            label="",
            emoji="🚧",
            style=discord.ButtonStyle.secondary,
            row=0,
            custom_id="limit",
        )
        clear_button = discord.ui.Button(
            label="",
            emoji="🧽",
            style=discord.ButtonStyle.danger,
            row=2,
            custom_id="clear",
        )
        delete_button = discord.ui.Button(
            label="",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            row=2,
            custom_id="delete",
        )
        give_button = discord.ui.Button(
            label="",
            emoji="🎁",
            style=discord.ButtonStyle.success,
            row=0,
            custom_id="give",
        )
        ban_button = discord.ui.Button(
            label="",
            emoji="🔨",
            style=discord.ButtonStyle.danger,
            row=2,
            custom_id="ban",
        )
        mute_button = discord.ui.Button(
            label="",
            emoji="🔇",
            style=discord.ButtonStyle.secondary,
            row=1,
            custom_id="mute",
        )
        deafen_button = discord.ui.Button(
            label="",
            emoji="🔕",
            style=discord.ButtonStyle.secondary,
            row=1,
            custom_id="deafen",
        )

        # Add buttons dependent on settings
        if "rename" in enabled_controls:
            self.add_item(name_button)
        if "limit" in enabled_controls:
            self.add_item(limit_button)
        if "mute" in enabled_controls:
            self.add_item(mute_button)
        if "deafen" in enabled_controls:
            self.add_item(deafen_button)
        if "give" in enabled_controls:
            self.add_item(give_button)
        if "ban" in enabled_controls:
            self.add_item(ban_button)
        if "clear" in enabled_controls:
            self.add_item(clear_button)
        if "delete" in enabled_controls:
            self.add_item(delete_button)

        if "lock" in enabled_controls or "hide" in enabled_controls:
            self.add_item(public_button)
        if "lock" in enabled_controls:
            self.add_item(lock_button)
        if "hide" in enabled_controls:
            self.add_item(hide_button)

        # Gives all the buttons the universal call_back
        for button in (
            public_button,
            lock_button,
            hide_button,
            name_button,
            limit_button,
            clear_button,
            delete_button,
            give_button,
            ban_button,
            mute_button,
            deafen_button,
        ):
            button.callback = self._callback

        if "labels" in control_options:
            lock_button.label = "Lock"
            hide_button.label = "Hide"
            public_button.label = "Public"
            name_button.label = "Rename"
            limit_button.label = "Limit"
            clear_button.label = "Clear"
            delete_button.label = "Delete"
            give_button.label = "Give"
            ban_button.label = "Ban"
            mute_button.label = "Mute"
            deafen_button.label = "Deafen"

    def _add_dropdown_items(self, enabled_controls, channel_state, row=None):
        # Handles non-state controls
        class ActionDropdown(discord.ui.Select):
            def __init__(select_self):
                options = []
                if "rename" in enabled_controls:
                    options.append(discord.SelectOption(value="rename", label="Rename Channel", emoji="🏷️"))
                if "limit" in enabled_controls:
                    options.append(discord.SelectOption(value="limit", label="Edit User Limit", emoji="🚧"))
                if "ban" in enabled_controls:
                    options.append(discord.SelectOption(value="ban", label="Ban/Allow Users or Roles", emoji="🔨"))
                if "mute" in enabled_controls:
                    options.append(discord.SelectOption(value="mute", label="Mute/Unmute Users", emoji="🔇"))
                if "deafen" in enabled_controls:
                    options.append(discord.SelectOption(value="deafen", label="Deafen/Undeafen Users", emoji="🔕"))
                if "give" in enabled_controls:
                    options.append(discord.SelectOption(value="give", label="Give Ownership", emoji="🎁"))
                if "clear" in enabled_controls:
                    options.append(discord.SelectOption(value="clear", label="Clear Messages", emoji="🧽"))
                if "delete" in enabled_controls:
                    options.append(discord.SelectOption(value="delete", label="Delete Channel", emoji="🗑️"))

                select_kwargs = {
                    "placeholder": "Settings",
                    "min_values": 1,
                    "max_values": 1,
                    "options": options,
                    "custom_id": "action_select",
                }
                if row is not None:
                    select_kwargs["row"] = row
                super().__init__(**select_kwargs)

        # Handles state controls
        class StateDropdown(discord.ui.Select):
            def __init__(select_self):
                options = []
                if len({"lock", "hide"}.intersection(enabled_controls)) > 0:
                    options.append(
                        discord.SelectOption(
                            value="public",
                            label="Public",
                            emoji="🌐",
                            default=channel_state == ChannelState.PUBLIC.value,
                        )
                    )
                if "lock" in enabled_controls:
                    options.append(
                        discord.SelectOption(
                            value="lock",
                            label="Locked",
                            emoji="🔒",
                            default=channel_state == ChannelState.LOCKED.value,
                        )
                    )
                if "hide" in enabled_controls:
                    options.append(
                        discord.SelectOption(
                            value="hide",
                            label="Hidden",
                            emoji="🙈",
                            default=channel_state == ChannelState.HIDDEN.value,
                        )
                    )

                select_kwargs = {
                    "placeholder": "Control Access",
                    "min_values": 1,
                    "max_values": 1,
                    "options": options,
                    "custom_id": "state_select",
                }
                if row is not None:
                    select_kwargs["row"] = row
                super().__init__(**select_kwargs)

        # Adds dropdowns if selected
        selected_options = {"rename", "limit", "clear", "ban", "mute", "deafen", "give", "delete"}.intersection(enabled_controls)
        selected_visibility_options = {"lock", "hide"}.intersection(enabled_controls)
        if len(selected_options) > 0:
            dropdown = ActionDropdown()
            dropdown.callback = self._callback
            self.add_item(dropdown)
        if len(selected_visibility_options) > 0:
            dropdown = StateDropdown()
            dropdown.callback = self._callback
            self.add_item(dropdown)

    # All buttons and dropdowns callback to this
    async def _callback(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        is_from_select = custom_id in SELECT_CUSTOM_IDS
        action = interaction.data["values"][0] if is_from_select else custom_id

        if not await is_owner(self, interaction):
            if is_from_select or custom_id in STATE_ACTIONS:
                await self._recreate_items(interaction)
            return

        # Everything uses followups however modals require a .response call
        if action not in _MODAL_ACTIONS:
            await interaction.response.defer(ephemeral=True)

        # Run related method
        await getattr(self, f"{action}_callback")(interaction)

        if is_from_select or action in STATE_ACTIONS:
            await self._recreate_items(interaction)

    async def _recreate_items(self, interaction):
        channel = interaction.channel
        new_view = ControlView.for_channel(self.bot, channel)
        try:
            await interaction.message.edit(view=new_view, embeds=interaction.message.embeds)
        except discord.NotFound:
            logger.debug(
                f"Control message gone while updating view for temp channel {channel.id} in guild '{channel.guild.name}'"
            )

    # The callback methods should match the actions. These are triggered in ._callback()
    # Example: `public` maps to `public_callback` following pattern `{action}_callback`
    async def public_callback(self, interaction: discord.Interaction):
        await channel_action(bot=self.bot, interaction=interaction, new_state=ChannelState.PUBLIC.value)

    async def lock_callback(self, interaction: discord.Interaction):
        await channel_action(bot=self.bot, interaction=interaction, new_state=ChannelState.LOCKED.value)

    async def hide_callback(self, interaction: discord.Interaction):
        await channel_action(bot=self.bot, interaction=interaction, new_state=ChannelState.HIDDEN.value)

    async def rename_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ChangeNameModal(self.bot, interaction.channel))

    async def limit_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(UserLimitModal(self.bot, interaction.channel))

    async def clear_callback(self, interaction: discord.Interaction):
        excluded_message_ids = []
        if interaction.message:
            excluded_message_ids.append(interaction.message.id)

        messages_to_delete = []
        async for message in interaction.channel.history(limit=None):
            if message.id not in excluded_message_ids:
                messages_to_delete.append(message)

        if messages_to_delete:
            try:
                await interaction.channel.delete_messages(messages_to_delete)
            except Exception as e:
                logger.warning(
                    f"Failed to bulk delete messages in temp channel {interaction.channel.id} "
                    f"in guild '{interaction.guild.name}': {e}"
                )
                reply = await interaction.followup.send(
                    f"Failed, {e}", ephemeral=True, wait=True
                )
                await reply.delete(delay=15)

        embed = discord.Embed(
            title="Messages Deleted",
            description=f"Deleted `{len(messages_to_delete)}` messages.",
            color=discord.Color.red(),
        )
        embed.set_footer(text="This message will disappear in 15 seconds.")
        reply = await interaction.followup.send(embed=embed, ephemeral=True, wait=True)
        await reply.delete(delay=15)

    async def delete_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Channel Deletion Confirmation",
            description="Are you sure you want to delete this channel? Reply with 'yes' within 60 seconds to confirm.",
            color=discord.Color.orange(),
        )
        embed.set_footer(text="Awaiting your response...")
        reply = await interaction.followup.send(embed=embed, ephemeral=True, wait=True)
        await reply.delete(delay=60)

        def check(message: discord.Message):
            return (
                message.author == interaction.user
                and message.channel == interaction.channel
                and message.content.lower() == "yes"
            )

        try:
            await self.bot.wait_for("message", check=check, timeout=60)
            deleted = False
            try:
                await interaction.channel.delete()
                deleted = True
            except discord.NotFound:
                deleted = True
            except discord.Forbidden as e:
                logger.debug(
                    f"Permission error removing temp channel {interaction.channel.id} "
                    f"in guild '{interaction.guild.name}', notifying user of missing permissions. {e}"
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
                    f"Unknown error removing temp channel {interaction.channel.id} "
                    f"in guild '{interaction.guild.name}': {e}"
                )
                return

            if deleted:
                self.bot.repos.temp_channels.remove(interaction.channel.id)
                await remove_owner_role(self.bot, interaction.user)
                await remove_owner_prefix(self.bot, interaction.user)
                logger.debug(
                    f"Deleted temp channel {interaction.channel.id} via control message confirmation "
                    f"in guild '{interaction.guild.name}'"
                )
        except asyncio.TimeoutError:
            logger.debug(
                f"Channel deletion confirmation timed out for temp channel {interaction.channel.id} "
                f"in guild '{interaction.guild.name}', handled."
            )
            try:
                embed = discord.Embed(
                    title="Channel Deletion Timed Out",
                    description="Channel deletion timed out. No action was taken.",
                    color=discord.Color.red(),
                )
                embed.set_footer(text="This message will disappear in 15 seconds.")
                reply = await interaction.followup.send(embed=embed, ephemeral=True, wait=True)
                await reply.delete(delay=15)
            except (discord.NotFound, discord.HTTPException):
                pass

    async def give_callback(self, interaction: discord.Interaction):
        await GiveOwnershipView(self.bot, interaction.channel).send_initial_message(interaction)

    async def ban_callback(self, interaction: discord.Interaction):
        await BanUserView(self.bot, interaction.channel).send_initial_message(interaction)

    async def mute_callback(self, interaction: discord.Interaction):
        await MuteUserView(self.bot, interaction.channel).send_initial_message(interaction)

    async def deafen_callback(self, interaction: discord.Interaction):
        await DeafenUserView(self.bot, interaction.channel).send_initial_message(interaction)


async def refresh_control_messages(bot):
    db_channels = bot.repos.temp_channels.get_ids()
    logger.info(f"Registering {len(db_channels)} persistent control views")

    for channel_id in db_channels :
        channel = bot.get_channel(channel_id)
        if channel is None:
            continue

        logger.info(f"Registering {channel.name}")

        view = ControlView.for_channel(bot, channel)
        try:
            async for message in channel.history(limit=10, oldest_first=True):
                if message.author.id == bot.user.id and message.components:
                    await message.edit(view=view, embeds=message.embeds)
                    break
        except discord.NotFound:
            logger.debug(f"Control message already gone for temp channel {channel_id} during view refresh")
        except Exception as e:
            logger.warning(f"Failed to refresh control message for temp channel {channel_id}: {e}")
