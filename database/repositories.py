from repos.creator_channels import CreatorChannelsRepository
from repos.guild_settings import GuildSettingsRepository
from repos.placeholders import PlaceholdersRepository
from repos.temp_channels import TempChannelsRepository
from repos.user_notifications import UserNotificationsRepository
from repos.voice_sanctions import VoiceSanctionsRepository


class Repositories:
    def __init__(self, database):
        self.guild_settings = GuildSettingsRepository(database)
        self.creator_channels = CreatorChannelsRepository(database)
        self.temp_channels = TempChannelsRepository(database)
        self.user_notifications = UserNotificationsRepository(database)
        self.voice_sanctions = VoiceSanctionsRepository(database)
        self.placeholders = PlaceholdersRepository(database)
