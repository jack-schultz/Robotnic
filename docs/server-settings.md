# Server settings

You’ll need **Manage Channels** to use `/settings`. These settings apply to the whole server. To change one creator channel, use [`/setup`](getting-started.md#creator-settings).

## Control panel

Open `/settings controls` and pick a dropdown, labeled buttons or icons without labels. In the same form, choose which buttons or menu items to show and whether to ping the owner when Robotnic opens their room. Submit to save.

## Staff logs

Run `/settings logging` and choose a channel for staff logs. Select the events you want, then submit the form.

- `channel_create` for room creation
- `channel_rename` for room renames
- `channel_remove` for room deletion
- `profanity_block` for profanity alerts

## Profanity filter

Robotnic checks custom room names with [profanity.dev](https://www.profanity.dev/). Run `/settings profanity_filter` to pick a mode.

- `off` skips the check.
- `alert` allows the rename and logs the flagged name.
- `alert & block` rejects the rename and logs the flagged name.

Turn on `profanity_block` in [Staff logs](#staff-logs) to get alerts.

## Owner settings

- `/settings owner dm-on-create` turns DMs to new room owners on or off. Set `enabled` to `true` or `false`.
- `/settings owner role-set` gives room owners a role. Give Robotnic **Manage Roles** and place its role above the role it gives out. Run `role-get` to check the setting or `role-clear` to stop assigning the role.
- `/settings owner prefix-set` adds a prefix to a member’s nickname while they own a room. Robotnic needs **Manage Nicknames** and its role must be above the member’s highest role. Discord protects the server owner’s nickname. Run `prefix-get` to check the prefix or `prefix-clear` to stop applying it.

## Custom placeholders

Run `/settings placeholder add` to set up a placeholder. For example, enter `{region}`, set its text to `EU` and pick a role. Add `{region}` to the [name template](getting-started.md#name-templates). Robotnic puts `EU` in the room name when the owner has that role.

Run `/settings placeholder list` to see your placeholders. To delete one, run `/settings placeholder remove` and pick it from the suggestions for `entry`.

## Language

Run `/settings language` to change the language Robotnic uses on your server.
