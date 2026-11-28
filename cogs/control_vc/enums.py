from enum import Enum


class ChannelState(Enum):
    PUBLIC = 0
    LOCKED = 1
    HIDDEN = 2


class Action(Enum):
    BAN = "ban"
    ALLOW = "allow"
    MUTE = "mute"
    UNMUTE = "unmute"
    DEAFEN = "deafen"
    UNDEAFEN = "undeafen"
    ENABLE_VOICE_ACTIVITY = "enable_voice_activity"
    DISABLE_VOICE_ACTIVITY = "disable_voice_activity"
