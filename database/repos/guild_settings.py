import json
from database.repos.base_repo import BaseRepo

defaults = {
    "guild_id": None,
    "logs_channel_id": None,
    "enabled_controls": ["rename", "limit", "clear", "ban", "mute", "deafen", "give", "delete", "lock", "hide"],
    "mention_owner_bool": 0,
    "dm_owner_bool": 0,
    "profanity_filter": "alert & block",
    "enabled_log_events": ["channel_create", "channel_rename", "channel_remove", "profanity_block"],
    "control_options": ["dropdown", "labels"],
    "owner_role_id": None,
    "owner_prefix": None
}


class GuildSettingsRepository(BaseRepo):  # bot.repos.guild_settings
    def get(self, guild_id):
        self.db.cursor.execute("""
            SELECT logs_channel_id, enabled_controls, mention_owner_bool, dm_owner_bool, profanity_filter, enabled_log_events, control_options, owner_role_id, owner_prefix
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))
        row = self.db.cursor.fetchone()

        if row is None:
            # return Default settings, keys matching database
            defaults["guild_id"] = guild_id
            return defaults

        (
            logs_channel_id,
            enabled_controls_json,
            mention_owner_bool,
            dm_owner_bool,
            profanity_filter,
            enabled_log_events_json,
            control_options_json,
            owner_role_id,
            owner_prefix
        ) = row

        enabled_controls = json.loads(enabled_controls_json) if enabled_controls_json else {}
        enabled_log_events = json.loads(enabled_log_events_json) if enabled_log_events_json else {}
        control_options = json.loads(control_options_json) if control_options_json else {}

        return {
            "guild_id": guild_id,
            "logs_channel_id": logs_channel_id,
            "enabled_controls": list(enabled_controls),
            "mention_owner_bool": bool(mention_owner_bool),
            "dm_owner_bool": bool(dm_owner_bool),
            "profanity_filter": profanity_filter,
            "enabled_log_events": list(enabled_log_events),
            "control_options": list(control_options),
            "owner_role_id": int(owner_role_id),
            "owner_prefix": owner_prefix  # str | None
        }

    def edit(
            self,
            guild_id: int,
            logs_channel_id: int | None= None,
            enabled_controls: list | None = None,
            mention_owner: bool | None = None,
            dm_owner: bool | None = None,
            profanity_filter: str | None = None,
            enabled_log_events: list | None = None,
            control_options: list | None = None,
            owner_role_id: int | None = None,
            owner_prefix: str | int | None = None
        ):
        # Check if the server has an entry
        self.db.cursor.execute("""
            SELECT logs_channel_id
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))
        row = self.db.cursor.fetchone()
        if not row:
            self.add(
                guild_id=guild_id
            )

        fields = []
        values = []

        if logs_channel_id is not None:
            fields.append("logs_channel_id = ?")
            values.append(logs_channel_id)

        if enabled_controls is not None:
            fields.append("enabled_controls = ?")
            values.append(json.dumps(enabled_controls))

        if mention_owner is not None:
            fields.append("mention_owner_bool = ?")
            values.append(1 if mention_owner else 0)

        if dm_owner is not None:
            fields.append("dm_owner_bool = ?")
            values.append(1 if dm_owner else 0)

        if profanity_filter is not None:
            fields.append("profanity_filter = ?")
            values.append(None if profanity_filter == "off" else profanity_filter)

        if enabled_log_events is not None:
            fields.append("enabled_log_events = ?")
            values.append(json.dumps(enabled_log_events))

        if control_options is not None:
            fields.append("control_options = ?")
            values.append(json.dumps(control_options))

        if owner_role_id is not None:
            fields.append("owner_role_id = ?")
            values.append(owner_role_id)

        if owner_prefix is not None:
            fields.append("owner_prefix = ?")
            if owner_prefix not in (0, "0", "None", "none"):
                values.append(owner_prefix)
            else:
                values.append(None)

        if not fields:
            # Nothing to update
            return False

        # Add the WHERE clause value
        values.append(guild_id)

        query = f"""
            UPDATE guild_settings
            SET {', '.join(fields)}
            WHERE guild_id = ?
        """

        self.db.cursor.execute(query, tuple(values))
        self.db.connection.commit()

        return self.db.cursor.rowcount > 0  # Returns True if a row was updated

    def get_logs_channel_id(self, guild_id):
        self.db.cursor.execute("""
            SELECT logs_channel_id
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))
        row = self.db.cursor.fetchone()

        if row is None:
            # Default settings
            return {
                "guild_id": guild_id,
                "logs_channel_id": None,
            }

        logs_channel_id = row[0]

        return {
            "guild_id": guild_id,
            "logs_channel_id": logs_channel_id,
        }

    def get_profanity_filter(self, guild_id):
        self.db.cursor.execute("""
                            SELECT profanity_filter
                            FROM guild_settings
                            WHERE guild_id = ?
                            """, (guild_id,))
        row = self.db.cursor.fetchone()

        if row is None:
            # Default settings
            return {
                "guild_id": guild_id,
                "profanity_filter": 1,
            }

        profanity_filter = row[0]

        return {
            "guild_id": guild_id,
            "profanity_filter": profanity_filter,
        }

    def add(self, guild_id):
        logs_channel_id = defaults["logs_channel_id"]
        enabled_controls_json = json.dumps(defaults["enabled_controls"])
        mention_owner_bool = defaults["mention_owner_bool"]
        dm_owner_bool = defaults["dm_owner_bool"]
        profanity_filter = defaults["profanity_filter"]
        enabled_log_events_json = json.dumps(defaults["enabled_log_events"])
        control_options_json = json.dumps(defaults["control_options"])
        owner_role_id = defaults["owner_role_id"]

        self.db.cursor.execute("""
            INSERT OR REPLACE INTO guild_settings
            (guild_id, logs_channel_id, enabled_controls, mention_owner_bool, dm_owner_bool, profanity_filter, enabled_log_events, control_options, owner_role_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, logs_channel_id, enabled_controls_json, bool(mention_owner_bool), bool(dm_owner_bool), profanity_filter, enabled_log_events_json, control_options_json, owner_role_id))
        self.db.connection.commit()
