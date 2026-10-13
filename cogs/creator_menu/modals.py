import discord
from config.i18n import t


class EditModal(discord.ui.DesignerModal):
    def __init__(self, view, creator_id):
        self.lang = view.lang
        super().__init__(title=t("creator_menu.modal.title", self.lang))
        self.view = view
        self.creator_id = creator_id
        creator_info = self.view.bot.repos.creator_channels.get_info(self.creator_id)

        self.child_name_label = discord.ui.Label(
            t("creator_menu.modal.child_name", self.lang),
            discord.ui.TextInput(
                placeholder=f"{creator_info.child_name}",
                required=False,
                max_length=100,
            ),
        )
        self.add_item(self.child_name_label)

        self.user_limit_label = discord.ui.Label(
            t("creator_menu.modal.user_limit", self.lang),
            discord.ui.TextInput(
                placeholder=f"{creator_info.user_limit}",
                required=False,
                max_length=500,
            ),
        )
        self.add_item(self.user_limit_label)

        self.child_overwrites_label = discord.ui.Label(
            t("creator_menu.modal.permissions", self.lang),
            discord.ui.Select(
                options=[
                    discord.SelectOption(value="1", label=t("creator_menu.modal.copy_creator_channel", self.lang), default=True if creator_info.child_overwrites == 1 else False),
                    discord.SelectOption(value="2", label=t("creator_menu.modal.copy_child_category", self.lang), default=True if creator_info.child_overwrites == 2 else False),
                    discord.SelectOption(value="0", label=t("creator_menu.modal.no_permissions", self.lang), default=True if creator_info.child_overwrites == 0 else False),
                ],
                min_values=1,
                max_values=1,
                required=True
            ),
        )
        self.add_item(self.child_overwrites_label)

        category = self.view.bot.get_channel(creator_info.child_category_id)
        self.category_label = discord.ui.Label(
            t("creator_menu.modal.category", self.lang),
            discord.ui.ChannelSelect(
                channel_types=[discord.ChannelType.category],
                min_values=0,
                max_values=1,
                required=False,
                default_values=[category] if category else None,
                placeholder=t("creator_menu.modal.category_placeholder", self.lang)
            ),
        )
        self.add_item(self.category_label)

        default_role = self.view.author.guild.get_role(creator_info.default_role_id)
        self.default_role_label = discord.ui.Label(
            t("creator_menu.modal.default_role", self.lang),
            discord.ui.RoleSelect(
                min_values=1,
                max_values=1,
                required=False,
                default_values=[default_role] if default_role else None,
                placeholder=t("creator_menu.modal.default_role_placeholder", self.lang)
            ),
        )
        self.add_item(self.default_role_label)

    async def callback(self, interaction: discord.Interaction):
        errors = []

        child_name = self.child_name_label.item.value
        user_limit = self.user_limit_label.item.value
        child_overwrites = self.child_overwrites_label.item.values[0] if len(self.child_overwrites_label.item.values) > 0 else None
        child_category_id = self.category_label.item.values[0].id if len(self.category_label.item.values) > 0 else None
        if len(self.default_role_label.item.values) > 0:
            default_role_id = self.default_role_label.item.values[0].id
        else:
            default_role_id = None

        creator_info = self.view.bot.repos.creator_channels.get_info(self.creator_id)
        if child_name:
            # Validate Child name length
            child_name = child_name.strip()
            if len(child_name) > 100:
                errors.append(t("creator_menu.modal.error_child_name_length", self.lang))
        else:
            child_name = creator_info.child_name

        if user_limit:
            try:
                user_limit = int(user_limit)
                if not (0 <= user_limit <= 99):
                    errors.append(t("creator_menu.modal.error_user_limit_range", self.lang))
            except ValueError:
                errors.append(t("creator_menu.modal.error_user_limit_integer", self.lang))
        else:
            user_limit = creator_info.user_limit

        # Does not default to current selection if None (like all other options) because the Current role is pre-selected in the menu
        # This means for it to be None it would be manually cleared.
        # In this case we reset to @everyone as it is the only role which is not selectable
        if not default_role_id:
            default_role_id = interaction.guild.default_role.id

        if errors:
            await interaction.response.send_message(
                t("creator_menu.modal.invalid_input", self.lang) + "\n" + "\n".join(f"- {error}" for error in errors),
                ephemeral=True
            )
            await self.view.update()
            return

        self.view.bot.repos.creator_channels.edit(
            channel_id=self.creator_id,
            child_name=child_name,
            user_limit=user_limit,
            child_category_id=child_category_id,
            child_overwrites=child_overwrites,
            default_role_id=default_role_id
        )

        embed = discord.Embed(
            title=t("creator_menu.modal.updated", self.lang),
            description=f"",
            color=discord.Color.green()
        )
        embed.set_footer(text=t("common.disappear_seconds", self.lang, seconds=10))
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=10)
        await self.view.update()
