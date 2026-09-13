from cogs.control_vc.enums import Action
from cogs.control_vc.member_actions.handler import handle_action


async def ban_user(bot, ctx, user):
    await handle_action(bot, ctx, Action.BAN, [user])


async def allow_user(bot, ctx, user):
    await handle_action(bot, ctx, Action.ALLOW, [user])


async def mute_user(bot, ctx, user):
    await handle_action(bot, ctx, Action.MUTE, [user])


async def deafen_user(bot, ctx, user):
    await handle_action(bot, ctx, Action.DEAFEN, [user])


async def unmute_and_undeafen_user(bot, ctx, user):
    # Discord allows 5 user commands, so unmute and undeafen share this one.
    await handle_action(bot, ctx, (Action.UNMUTE, Action.UNDEAFEN), [user])
