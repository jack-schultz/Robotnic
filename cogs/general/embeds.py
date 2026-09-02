import discord


class DonateEmbed(discord.Embed):
    def __init__(self):
        super().__init__()
        self.color = discord.Color.green()
        self.title = "💚 A Message from the Developer"
        self.description = (
            "Thank you for using Robotnic!\n"
            "I created this bot as a **[FOSS](<https://wikipedia.org/wiki/Free_and_open-source_software>)** project with a **free** public instance as I was fed up with lack-luster bots which cost ridiculous amounts of money. I provide this service for free, you can check out my other projects on my [GitHub account](https://github.com/jack-schultz)."
        )
        self.add_field(
            name="💸 Donations",
            value=(
                "Robotnic took a long time to develop and also **costs money to host**, which I currently pay for out of my own pocket."
            ),
            inline=False
        )
        self.add_field(
            name="🙏 Please Consider Supporting Me",
            value="Every bit of support helps keep Robotnic running smoothly. ❤️",
            inline=False
        )
        self.set_footer(text="📩 Need more help? Reach out for support below!")


class HelpEmbed(discord.Embed):
    def __init__(self):
        super().__init__()
        self.color = discord.Color.green()
        self.title = "Command List"
        self.description = (
        )
        self.add_field(
            name="/setup",
            value=(
                "Use this menu to create new `Creator Channel`s by clicking the green \"Make new Creator\" button or edit existing `Creator Channel`s using the dropdown list."
            ),
            inline=False
        )
        self.add_field(
            name="/settings controls",
            value="Allows changing the controls available to channel owners. Every button is togglable and you can choose between labeled buttons, icons or a dropdown menu as controls. You can also adjust if the owner gets pinged on channel creation.",
            inline=False
        )
        self.add_field(
            name="/settings logging",
            value="Allows for setting a log channel, if set, selected events will be logged in that channel. To customise the list, simply deselect the ones you would not like to include.",
            inline=False
        )
        self.add_field(
            name="/settings profanity_filter",
            value="While still basic, this setting allows for disabling or only sending an alert if the profanity filter is triggered rather than blocking the action.",
            inline=False
        )
        self.add_field(
            name="/donate /support",
            value="Returns with information on how to support Robotnic's uptime.",
            inline=False
        )
        self.add_field(
            name="/ping",
            value="Returns the bot's latency",
            inline=False
        )
        self.set_footer(text="📩 Need more help? Reach out to support below!")