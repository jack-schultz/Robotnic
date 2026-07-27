# Robotnic - Dynamic Voice Channels Discord Bot

Robotnic is an open-source Discord bot designed to intelligently 
manage dynamic voice channels. It automatically creates, manages, and 
deletes temporary voice channels based on user activity. This keeps your 
server clean and organized.

You can invite the public instance to your own server for free using
👉[invite Robotnic](https://discord.com/oauth2/authorize?client_id=853490879753617458)
or join the support server to test it out 👉[Support Server](https://discord.gg/rcAREJyMV5).

Alternatively, you can test its functionality in our 👉[Example Server](https://discord.gg/xm5aNaW737). It includes pre-configured creator channels that show off the variety of use cases for Robotnic.

See the bot's current stats on its 👉[website](https://jackschultz.dev/Robotnic/) or read a bit about its development on 👉[jackschultz.dev](https://jackschultz.dev/projects/discordBot.html).

## Example gif
![dr-robotnic](https://github.com/user-attachments/assets/c20813de-2453-497d-adc2-e1d23843603d)

## Features

### Why server admins choose Robotnic

Robotnic goes beyond basic “join hub → get a channel” bots. You get unlimited configurable creator hubs per server, an in-channel control panel (no command memorization for members) and admin tools to decide exactly what users are allowed to do. All this without a paywall and hosted for free if using the public instance.

**Standout features for admins:**
- **Activity-based channel names** - templates can include `{activity}` so channels rename when members start playing a game (great for gaming communities).
- **UNLIMITED creator channels** - run separate hubs (e.g. “Gaming”, “Study”, “Hangout”) each with their own naming, limits, category, and permissions.
- **Granular user controls** - toggle each owner action individually (rename, limit, lock, hide, ban/allow, transfer ownership, clear chat, delete).
- **Flexible control UI** - choose dropdown menus or icon buttons (with or without text labels) for the in-channel panel and optionally ping the owner when their channel is created.
- **Role-aware privacy** - lock/hide affects a configurable role (not just `@everyone`), with separate ban/allow menus for users and roles.
- **Profanity filter on renames** - powered by [profanity.dev](https://www.profanity.dev/). modes: off, log-only, or log and block.
- **Audit logging** - send channel create, rename, delete, and profanity events (or a customizable combination) to a staff log channel you pick.
- **Survives restarts** - SQLite tracks every creator and temp channel. Orphaned entries are cleaned up automatically.

### Dynamic voice channels

When a user joins a **creator channel**, Robotnic:
1. Creates a temporary voice channel (with your chosen name pattern, limit, category, and permission inheritance).
2. Moves the user into it.
3. Posts an interactive control panel in the channel’s text chat.
4. Deletes the channel when it becomes empty.

Name templates support **`{user}`**, **`{activity}`** (games being played), and **`{count}`** (sequential numbering per creator). Names update when members change activity or leave, with a built-in rename queue to respect Discord rate limits.

### Automatic cleanup

Empty temporary channels are removed as soon as the last member leaves. A background sweep also catches any empty channels that were missed (I haven't found this to be a problem, but this is just in case), and stale database entries are pruned when channels are deleted manually.

### Creator channel configuration (`/setup`)

Each creator channel can be configured independently:
- **Name pattern** - e.g. `{user}'s Room`, `{activity} Lobby`, `Channel #{count}`
- **User limit** - 0 for unlimited, or 1–99
- **Category** - place new channels in a specific category, or inherit from the creator
- **Permission inheritance** - none, copy from the creator channel, or copy from the category
- **Lock/hide target role** - which role is blocked when a channel is locked or hidden (defaults to `@everyone`)

### In-channel owner controls (dropdown menu or buttons)

Channel owners manage everything from buttons or dropdowns inside the voice channel. No slash commands required. Available actions (all optional per server, meaning admins can enable/disable any of the following):
- **Public / Lock / Hide** - control who can see and join (this affects the "target role" mentioned above)
- **Rename** - custom name, or leave blank to revert to the template, this respects the profanity filter
- **User limit** - changeable at any time
- **Ban / Allow** - block or grant access for specific members or roles (banned members are disconnected)
- **Give ownership** - transfer to someone in the channel, or release ownership so anyone can claim it
- **Clear messages** - bulk-delete chat history (keeps the control panel)
- **Delete channel** - owner-initiated removal with confirmation

If the owner leaves, the next member to use the controls can claim ownership automatically.

### Server-wide settings (`/settings`)

Admins configure guild defaults without touching code:
- **`/settings controls`** - enable/disable each owner action; choose control UI style; toggle owner mention on creation
- **`/settings logging`** - set a log channel and pick events: `channel_create`, `channel_rename`, `channel_remove`, `profanity_block`
- **`/settings profanity_filter`** - `off`, `alert`, or `alert & block`

### Persistence & reliability

All creator channels, temp channels, and per-guild settings live in **SQLite**. Restarts do not lose configuration or leave ghost channels behind. On startup and on run of `/setup` removes creator entries whose Discord channels were deleted.

### Built-in Discord UX

Everything is configured through slash commands, modals, dropdowns, and buttons (Pycord 2.7+). New servers receive a welcome message with quick-start links when the bot joins. This also means no stupid external setup website, I hate those things.

## Requirements

See `requirements.txt` and `requirements-topgg.txt`. Main dependencies:
- py-cord>=2.7.0
- PyNaCl==1.5.0
- python-dotenv>=1.0.0
- topggpy (optional; for self-hosted Top.gg stats; **install with `--no-deps` or you will have issues**)
- requests>=2.31 (profanity filter API)
- fastapi & uvicorn (stats API for the docs site)
- SQLite (included with Python)

## Commands

| Command | Who | Description                                                |
|---------|-----|------------------------------------------------------------|
| `/setup` | Manage Channels | Create or edit creator channels and their options          |
| `/settings controls` | Manage Channels | Toggle owner controls, UI style, and owner mention         |
| `/settings logging` | Manage Channels | Set a log channel and choose which events to record        |
| `/settings profanity_filter` | Manage Channels | Set profanity handling: `off`, `alert`, or `alert & block` |
| `/help` | Everyone | Command list and usage                                     |
| `/support` | Everyone | Support links and how to contribute                        |
| `/donate` | Everyone | Same as `/support`. Ways to help keep Robotnic running     |
| `/ping` | Manage Channels | Bot latency                                                |

## Self-Hosting Setup

**THIS BOT IS LICENSED UNDER THE AGPLv3 LICENSE** WHICH REQUIRES YOUR USERS TO HAVE ACCESS TO THE SOURCE CODE RUNNING YOUR APPLICATION.

**Python 3.13.9** (also available as a [Dockerfile](Dockerfile) for container deployments)

Self-hosted instances also get:
- A **stats API** on port 8000 (`GET /stats` guild, user, creator, and temp channel counts) for dashboards or the included docs site
- Configurable **bot presence** text with `{server_count}`, `{member_count}`, `{creator_count}`, and `{temp_channel_count}`
- Optional **Top.gg** guild count posting (set `TOPGG_TOKEN` in `.env`)
- **Owner notifications** for bot start/stop, reconnects, and guild joins (via `settings.json`)

1. Clone the repository
```bash
git clone https://github.com/jack-schultz/Robotnic.git
cd Robotnic
```
2. Install Dependencies

   `topggpy` declares `discord.py` as a dependency, but this project uses **py-cord** instead. Installing `discord.py` alongside (or uninstalling it after) py-cord can leave a broken `discord` package. Use the install script so topggpy is installed with `--no-deps`:

```bash
# Linux / macOS / Git Bash
./scripts/install.sh

# Windows PowerShell
.\scripts\install.ps1
```

   Or manually:

```bash
pip install -r requirements.txt
pip install -r requirements-topgg.txt --no-deps
```
3. Run the main.py file to create the settings.json, database.db and .env files.
```bash
python main.py
```
4. Configure the Bot. In the .env file, replace `TOKEN_HERE` with your bot's token. (You need to make a Discord Bot through Discord's Developer Portal)
```
TOKEN=TOKEN_HERE
```
5. Run the Bot
```bash
python main.py
```
6. (Optional) Host the docs site from the `docs/` folder. In **Settings → Pages**, set the source to **GitHub Actions**. Copy `docs/stats.config.example.json` to `docs/stats.config.json` and set `statsUrl` to your bot's `/stats` endpoint (or set a `STATS_API_URL` repo variable under **Settings → Secrets and variables → Actions**). The workflow (`.github/workflows/update-stats.yml`) fetches stats hourly and deploys the site without committing to `main`. Pushes to `docs/**` on `main` also trigger a redeploy. Enable Actions on your fork and ensure the API is reachable from GitHub's runners.

Optionally: Edit the settings.json. 

Below is the default `settings.json` with a table to explain.

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

| Key | Purpose |
|-----|---------|
| `debug.discord` / `debug.bot` | Verbose logging for Discord.py or bot internals. Set `bot` to `true` when troubleshooting. |
| `notifications.channel_id` | Discord channel ID where the bot owner receives lifecycle alerts. |
| `notifications.*` | Toggle which owner alerts fire: start, reconnect, stop, guild join, channel create/remove. |
| `api.port` | Port for the FastAPI stats server (`GET /stats`, `GET /`). |
| `status.text` | Playing status; supports `{server_count}`, `{member_count}`, `{creator_count}`, `{temp_channel_count}`. |

Please make sure you have **message**, **member**, and **presence (activity)** intents enabled in the Discord Developer Portal for your bot.

## Future Features
Join the 👉[Discord Server](https://discord.gg/rcAREJyMV5) to keep up to date with any developments.
