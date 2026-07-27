# Contributing to Robotnic

Thank you for your interest in contributing! Robotnic is a free, open-source Discord bot for dynamic voice channels, and community help keeps it running.

## Ways to help

- **Report bugs**: open a GitHub Issue with steps to reproduce
- **Suggest features**: describe the use case and why it matters
- **Submit code**: fix bugs or add features via pull request

You can also discuss ideas on the [Support Server](https://discord.gg/rcAREJyMV5) or [sponsor the project](https://github.com/sponsors/jack-schultz) to help cover hosting costs.

## License

Robotnic is licensed under the [GNU Affero General Public License v3.0 (AGPLv3)](LICENSE).

By contributing, you agree that your contributions will be licensed under the same terms. If you run a modified version as a network service (including self-hosting for others), AGPLv3 requires that users of that service have access to the corresponding source code.

## Development setup

### Requirements

- **Python 3.13.9**
- A Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications)
- Required intents enabled: **message**, **member**, and **presence (activity)**

### Install

```bash
git clone https://github.com/jack-schultz/Robotnic.git
cd Robotnic
```

Install dependencies using the install script (recommended):

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

> **Important:** `topggpy` declares `discord.py` as a dependency, but this project uses **py-cord**. Installing `discord.py` alongside py-cord can break the `discord` package. Always install `requirements-topgg.txt` with `--no-deps`, or use the install scripts above.

### Configure and run

```bash
python main.py   # First run creates .env, settings.json, and database.db
```

Edit `.env` and set your bot token:

```
TOKEN=your_discord_bot_token
```

Then start the bot:

```bash
python main.py
```

The bot runs alongside a FastAPI stats server on port 8000 (configurable in `settings.json`).

### Files not to commit

Never commit secrets or local runtime files:

- `.env`
- `settings.json`
- `database.db`
- `logs/`

## Project structure

```
Robotnic/
├── main.py              # Entry point; starts bot and stats API
├── bot/                 # Bot class, events, background tasks
│   ├── bot.py           # Auto-loads cogs from cogs/
│   └── events/
├── cogs/                # Discord cogs (one *_cog.py per feature area)
│   ├── manage_vcs/      # Channel lifecycle, naming, renamer
│   ├── control_vc/      # Owner controls (views, modals)
│   ├── creator_menu/    # Creator channel setup UI
│   ├── settings/        # Guild settings UI
│   └── general/         # Help, support, ping
├── config/              # Environment, settings, logging
├── database/            # SQLite and repositories
├── api/                 # FastAPI /stats endpoint
└── docs/                # Static website. This isn't actually documentation, just a public site to share the bot
```

### Adding a cog

New cogs go in `cogs/` as `*_cog.py` with a `setup(bot)` function. `bot/bot.py` automatically loads every `.py` file in `cogs/` that does not start with `_`.

Keep cog files simple. Listeners and slash commands only. Put feature logic in a subpackage (e.g. `cogs/manage_vcs/lifecycle.py`).

## Branching and pull requests

**All pull requests should target the `canary` branch.**

1. Fork the repository
2. Create a feature branch from `canary`
3. Make your changes
4. Open a pull request back to `canary`

`main` is the stable branch. Maintainers merge `canary` into `main` for releases (semver tags like `v2.5.0`).

### Pull request checklist

- [ ] Describe what changed and why
- [ ] Include manual testing steps (see below)
- [ ] Avoid unrelated refactors
- [ ] Do not include secrets, tokens, or local config files

## Coding guidelines

There is no enforced format or anything, just match the existing code style:

- Use the `logging` module rather than print statements
- Follow the cog + subpackage layout described above
- Use Discord UI components (views, modals, embeds) consistent with existing cogs
- Read and write data through `database/repositories.py`
- Extend existing cogs and modules rather than introducing unnecessary abstractions
- Enable verbose logging with `"debug": { "bot": true }` in `settings.json` when troubleshooting

## Testing

There is no automated tests because I never made any, what can I say? Please manually verify your changes in a test Discord server:

1. Start the bot with a valid token and required intents
2. Run `/setup` to create or edit a creator channel
3. Join the creator channel and confirm a temp channel is created with the control panel
4. Exercise the controls or settings your change affects (rename, lock, ban, cleanup, etc.)
5. Leave the channel and confirm it is deleted when empty

Automated tests are welcome if a contributor adds the infrastructure.

## Reporting bugs and requesting features

Open a [GitHub Issue](https://github.com/jack-schultz/Robotnic/issues) with:

- Steps to reproduce the problem
- Expected vs actual behavior
- Whether you are using the public instance or self-hosting
- Relevant log output from `logs/` (redact tokens and IDs if sharing publicly)

For security-sensitive issues, contact the maintainer via the [Support Server](https://discord.gg/rcAREJyMV5) rather than opening a public issue.

## Docs 

This file and the [README](https://github.com/jack-schultz/Robotnic/blob/main/README.md) are all the documentation at this time. Contributors are welcome to expand the documentation.