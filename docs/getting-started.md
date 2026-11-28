# Getting started

Robotnic makes a temporary voice room when someone joins a creator channel. The public bot is free and there’s no limit on how many creator channels you can set up.

## Add Robotnic

1. [Add Robotnic](https://discord.com/oauth2/authorize?client_id=853490879753617458) to your server.
2. Run `/setup` and click **Make new Creator**. You’ll need **Manage Channels**.
3. Join the creator channel. Robotnic moves you into the new room and posts the [controls](channel-controls.md) in its chat.

After you add the bot, it posts setup and support links in the first text channel it can use.

[Try the controls in your browser](https://jackschultz.dev/Robotnic/#demo).

## Creator settings

Run `/setup` again and pick a creator from the dropdown. You can give Gaming and Study different room names, limits and permissions.

| Setting | What it does |
| --- | --- |
| Name template | Choose what new rooms are called. You can use [placeholders](#name-templates) in the name. |
| User limit | Allow 1 to 99 people. Use `0` for no limit. |
| Category | Keep new rooms in the creator’s category or choose another one. |
| Permission inheritance | Copy permission overrides from the creator channel or the room’s category. You can leave this off. |
| Lock and hide role | Pick the role affected by Lock and Hide. It starts out as `@everyone`. |

## Name templates

| Placeholder | What it inserts | Example |
| --- | --- | --- |
| `{user}` | The room owner’s display name | `{user}'s Room` |
| `{activity}` | The games people in the room are playing | `{activity} Lobby` |
| `{count}` | The room’s number for this creator | `Channel #{count}` |

Room names that use `{activity}` update when people change games, join or leave. Robotnic queues renames to stay within Discord’s limits. Use [custom placeholders](server-settings.md#custom-placeholders) to put different text in the name depending on the owner’s role.

## Cleanup and restarts

Robotnic deletes a room when the last person leaves. It also checks for empty rooms it missed and drops records for channels that no longer exist. If you delete a creator channel, run `/setup` to clear its entry from the menu.

Robotnic keeps channel records and server settings in SQLite. After a restart it refreshes the control panels for rooms that are still open.

## Help

Ask questions or follow bot updates in the [support server](https://discord.gg/rcAREJyMV5).

[Live stats](https://jackschultz.dev/Robotnic/#stats) · [Project write-up](https://jackschultz.dev/projects/discordBot.html) · [Contributing](../CONTRIBUTING.md)
