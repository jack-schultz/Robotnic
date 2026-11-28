# Self-host Robotnic

You’ll need Python **3.13.9** for the steps below. For Docker, use the included [Dockerfile](../Dockerfile).

> [!NOTE]
> Robotnic uses the [GNU Affero General Public License v3.0](../LICENSE). If people use a modified version over a network, offer them access to the corresponding source code.

## Discord app

Create an app in the [Discord Developer Portal](https://discord.com/developers/applications). On the app’s **Bot** page, turn on **Server Members Intent** and **Presence Intent**.

## Install dependencies

```sh
git clone https://github.com/ohne-b/Robotnic.git
cd Robotnic
```

On Linux, macOS or Git Bash, run `bash scripts/install.sh`. On Windows, run `.\scripts\install.ps1` in PowerShell.

For a manual install, run both commands from the repo folder.

```sh
python -m pip install -r requirements.txt
python -m pip install -r requirements-topgg.txt --no-deps
```

[requirements.txt](../requirements.txt) lists Pycord 2.7+, PyNaCl 1.5.0, python-dotenv 1.0+, requests 2.31+, FastAPI and Uvicorn. SQLite comes with Python. The Top.gg client is in [requirements-topgg.txt](../requirements-topgg.txt).

> [!IMPORTANT]
> Use `--no-deps` for `requirements-topgg.txt`. The bot imports `topggpy` at startup. Its `discord.py` dependency conflicts with Pycord.

## Run the bot

1. Run `python main.py` from the repo folder. The first run creates `settings.json` and `.env`, then stops so you can add a token.
2. Open `.env` and replace `TOKEN_HERE` with the token from your app’s **Bot** page.
3. Run `python main.py` again. Robotnic opens `database.db` and starts the stats API.
4. Install the app on your Discord server with the `bot` and `applications.commands` scopes. Give it the permissions below, then [run `/setup`](getting-started.md#add-robotnic).

## Bot permissions

Give Robotnic these permissions in the categories where it creates rooms.

- **View Channel**, **Manage Channels** and **Manage Roles**
- **Send Messages**, **Embed Links**, **Manage Messages** and **Read Message History**
- **Connect** and **Move Members**

If you turn on the mute or deafen controls, add **Mute Members** and **Deafen Members**.

[Configure your bot and its stats page](host-configuration.md).
