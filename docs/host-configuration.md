# Host configuration

Edit `settings.json` or `.env` in the repo folder, then restart Robotnic. If you’re missing those files, [run the bot once](self-hosting.md#run-the-bot) to create them.

## Settings file

- `debug.discord` logs more from Pycord. `debug.bot` logs more from Robotnic.
- `notifications.channel_id` is where Robotnic sends alerts for the bot owner.
- `notifications.*` lets you pick which alerts to get. It covers starts, stops, reconnects, server joins and leaves, and changes to creator channels and rooms.
- `api.port` is the port for the stats API. The default is `8000`.
- `status.text` sets what Discord shows as the bot’s activity. You can put `{server_count}`, `{member_count}`, `{creator_count}`, `{temp_channel_count}` or `{connected_users}` in the text.

A new `settings.json` starts with these values from [default_settings.json](../default_settings.json).

```json
{
    "debug": {
        "discord": false,
        "bot": false
    },
    "notifications": {
        "channel_id": null,
        "start": true,
        "reconnect": true,
        "stop": true,
        "guild_join": true,
        "guild_leave": true,
        "channel_create": false,
        "channel_remove": false,
        "creator_create": false
    },
    "api": {
        "port": 8000
    },
    "status": {
        "text": "Online in {server_count} servers | {member_count} users."
    }
}
```

## Top.gg

Set `TOPGG_TOKEN` in `.env` if you want Robotnic to send your bot’s server count to Top.gg.

## Stats and data

| Endpoint | What it returns |
| --- | --- |
| `GET /` | Returns `{"ok": true}` if the API is running. |
| `GET /stats` | Counts for servers, users, creator channels, temporary rooms and connected users. |
| `GET /stats/history` | The data behind the website’s charts. |

If you move the bot to another host, take `database.db` with you. It holds your creator channels, temporary rooms and server settings. Copy `logs/stats.csv` too if you want to keep the charts’ history.

## Publish the website

1. Enable Actions on your fork. In **Settings → Pages**, set the build source to **GitHub Actions**.
2. Copy [stats.config.example.json](stats.config.example.json) to `docs/stats.config.json`. Put the full `/stats` and `/stats/history` URLs in `statsUrl` and `historyUrl`. You can also set those URLs in the `STATS_API_URL` and `STATS_HISTORY_API_URL` Actions repository variables. GitHub’s runners need to reach both URLs.
3. Run the [Update bot stats workflow](../.github/workflows/update-stats.yml). It publishes the site and stats snapshot to Pages. It also runs every hour and after a push to `main` changes files in `docs/`.
