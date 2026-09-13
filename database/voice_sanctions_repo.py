class VoiceSanctionsRepository:  # bot.repos.voice_sanctions
    def __init__(self, db, repos):
        self.db = db
        self.repos = repos

    def get(self, guild_id, channel_id, user_id):
        self.db.cursor.execute("""
            SELECT muted, deafened
            FROM voice_sanctions
            WHERE guild_id = ? AND channel_id = ? AND user_id = ?
        """, (guild_id, channel_id, user_id))
        row = self.db.cursor.fetchone()
        if row is None:
            return None
        return bool(row[0]), bool(row[1])

    def set_flags(self, guild_id, channel_id, user_id, muted=None, deafened=None):
        current = self.get(guild_id, user_id)
        muted_now = current[0] if current else False
        deafened_now = current[1] if current else False
        if muted is not None:
            muted_now = bool(muted)
        if deafened is not None:
            deafened_now = bool(deafened)

        if not muted_now and not deafened_now:
            self.clear(guild_id, user_id)
            return

        if current is None:
            self.db.cursor.execute("""
                INSERT INTO voice_sanctions (guild_id, channel_id, user_id, muted, deafened)
                VALUES (?, ?, ?, ?)
            """, (guild_id, channel_id, user_id, int(muted_now), int(deafened_now)))
        else:
            self.db.cursor.execute("""
                UPDATE voice_sanctions
                SET muted = ?, deafened = ?
                WHERE guild_id = ? AND channel_id = ? AND user_id = ?
            """, (int(muted_now), int(deafened_now), guild_id, channel_id, user_id))
        self.db.connection.commit()

    def clear(self, guild_id, user_id):
        self.db.cursor.execute("""
            DELETE FROM voice_sanctions
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id))
        self.db.connection.commit()
