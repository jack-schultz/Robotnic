from base_repo import BaseRepo


class VoiceSanctionsRepository(BaseRepo):  # bot.repos.voice_sanctions
    # Not a channel. Holds the server mute/deafen from before the bot changed it,
    # so leaving a temp channel can restore a moderator's mute.
    DISCORD_RESET = 0

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

    def _prior_row(self, guild_id, user_id):
        self.db.cursor.execute("""
            SELECT prior_muted, prior_deafened
            FROM voice_sanctions
            WHERE guild_id = ? AND channel_id = ? AND user_id = ?
        """, (guild_id, self.DISCORD_RESET, user_id))
        return self.db.cursor.fetchone()

    def get_prior(self, guild_id, user_id):
        row = self._prior_row(guild_id, user_id)
        if row is None:
            return None
        # Older reset rows have no priors and mean "restore unmuted".
        if row[0] is None or row[1] is None:
            return False, False
        return bool(row[0]), bool(row[1])

    def has_stored_prior(self, guild_id, user_id):
        row = self._prior_row(guild_id, user_id)
        return row is not None and row[0] is not None and row[1] is not None

    def save_prior(self, guild_id, user_id, muted, deafened):
        row = self._prior_row(guild_id, user_id)
        if row is not None and row[0] is not None and row[1] is not None:
            return
        if row is not None:
            self.update_prior(guild_id, user_id, muted, deafened)
            return
        self.db.cursor.execute("""
            INSERT INTO voice_sanctions
                (guild_id, channel_id, user_id, muted, deafened, prior_muted, prior_deafened)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (guild_id, self.DISCORD_RESET, user_id, int(muted), int(deafened)))
        self.db.connection.commit()

    def update_prior(self, guild_id, user_id, muted, deafened):
        if self._prior_row(guild_id, user_id) is None:
            return
        self.db.cursor.execute("""
            UPDATE voice_sanctions
            SET prior_muted = ?, prior_deafened = ?
            WHERE guild_id = ? AND channel_id = ? AND user_id = ?
        """, (int(muted), int(deafened), guild_id, self.DISCORD_RESET, user_id))
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
        restore their prior server mute if the bot had overridden it.
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
