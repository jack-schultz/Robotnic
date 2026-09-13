class VoiceSanctionsRepository:  # bot.repos.voice_sanctions
    # Marks that Discord mute/deafen still need clearing
    # after the member left voice and the temp channel row was deleted.
    DISCORD_RESET = 0

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
        current = self.get(guild_id, channel_id, user_id)
        muted_now = current[0] if current else False
        deafened_now = current[1] if current else False
        if muted is not None:
            muted_now = bool(muted)
        if deafened is not None:
            deafened_now = bool(deafened)

        if not muted_now and not deafened_now:
            self.delete(guild_id, channel_id, user_id)
            return

        if current is None:
            self.db.cursor.execute("""
                INSERT INTO voice_sanctions (guild_id, channel_id, user_id, muted, deafened)
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, channel_id, user_id, int(muted_now), int(deafened_now)))
        else:
            self.db.cursor.execute("""
                UPDATE voice_sanctions
                SET muted = ?, deafened = ?
                WHERE guild_id = ? AND channel_id = ? AND user_id = ?
            """, (int(muted_now), int(deafened_now), guild_id, channel_id, user_id))
        self.db.connection.commit()

    def delete(self, guild_id, channel_id, user_id):
        self.db.cursor.execute("""
            DELETE FROM voice_sanctions
            WHERE guild_id = ? AND channel_id = ? AND user_id = ?
        """, (guild_id, channel_id, user_id))
        self.db.connection.commit()

    # Discord's server mute and deafen apply to the whole guild. When someone
    # leaves a temp channel, the bot tries to clear that mute so they are not muted everywhere else.
    # Discord rejects that edit if they are no longer in a voice channel.
    # If the temp channel is then deleted, delete_for_channel() removes the real sanction row, and
    # the bot would forget that it still needs to unmute them.
    # This allows for writing a placeholder row so that does not happen. channel_id is 0 and muted is set to 1.
    def mark_discord_reset(self, guild_id, user_id):
        current = self.get(guild_id, self.DISCORD_RESET, user_id)
        if current is None:
            self.db.cursor.execute("""
                INSERT INTO voice_sanctions (guild_id, channel_id, user_id, muted, deafened)
                VALUES (?, ?, ?, 1, 0)
            """, (guild_id, self.DISCORD_RESET, user_id))
            self.db.connection.commit()

    def clear_discord_reset(self, guild_id, user_id):
        self.delete(guild_id, self.DISCORD_RESET, user_id)

    def delete_for_channel(self, channel_id):
        if channel_id == self.DISCORD_RESET:
            return
        self.db.cursor.execute("""
            DELETE FROM voice_sanctions
            WHERE channel_id = ?
        """, (channel_id,))
        self.db.connection.commit()

    def delete_invalid(self):
        """
        Remove sanctions for channels that are no longer temp channels.
        Returns users who still had a mute or deafen flag, so the caller can
        clear Discord or keep a reset placeholder.
        """
        self.db.cursor.execute("""
            SELECT DISTINCT guild_id, user_id
            FROM voice_sanctions
            WHERE channel_id != ?
            AND channel_id NOT IN (SELECT channel_id FROM temp_channels)
            AND (muted = 1 OR deafened = 1)
        """, (self.DISCORD_RESET,))
        affected = [(row[0], row[1]) for row in self.db.cursor.fetchall()]

        self.db.cursor.execute("""
            DELETE FROM voice_sanctions
            WHERE channel_id != ?
            AND channel_id NOT IN (SELECT channel_id FROM temp_channels)
        """, (self.DISCORD_RESET,))
        deleted = self.db.cursor.rowcount
        self.db.connection.commit()
        return deleted, affected

    def delete_invalid_for_user(self, guild_id, user_id):
        """
        Remove user's sanctions for channels that are no longer
        in the temp channel db, meaning they no longer exist.
        """
        self.db.cursor.execute("""
            SELECT channel_id, muted, deafened
            FROM voice_sanctions
            WHERE guild_id = ? AND user_id = ? AND channel_id != ?
        """, (guild_id, user_id, self.DISCORD_RESET))
        removed_active = False
        for channel_id, muted, deafened in self.db.cursor.fetchall():
            if self.repos.temp_channels.get_info(channel_id) is not None:
                continue
            self.delete(guild_id, channel_id, user_id)
            if muted or deafened:
                removed_active = True
        return removed_active

    def any_active(self, guild_id, user_id, exclude_channel_id=None):
        sql = """
            SELECT 1 FROM voice_sanctions
            WHERE guild_id = ? AND user_id = ? AND (muted = 1 OR deafened = 1)
        """
        params = [guild_id, user_id]
        if exclude_channel_id is not None:
            sql += " AND channel_id != ?"
            params.append(exclude_channel_id)
        sql += " LIMIT 1"
        self.db.cursor.execute(sql, params)
        return self.db.cursor.fetchone() is not None
