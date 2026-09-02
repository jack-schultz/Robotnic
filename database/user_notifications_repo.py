# When these bools are set to true, it means the user has been notified about the related thing
# A row not existing means that user has not been notified of anything
defaults = {
    "user_id": None,
    "dm_owner_controls": 0,
    "dm_admin_donate": 0,
}


class UserNotificationsRepository:  # bot.repos.guild_settings
    def __init__(self, db, repos):
        self.db = db
        self.repos = repos

    def get_dm_owner_controls(self, user_id: int):
        self.db.cursor.execute("""
            SELECT dm_owner_controls
            FROM user_notifications
            WHERE user_id = ?
        """, (user_id,))
        row = self.db.cursor.fetchone()

        if row is None or row[0] == 0:
            return False

        return True

    def set_dm_owner_controls(self, user_id: int):
        self.db.cursor.execute("""
            SELECT user_id
            FROM user_notifications
            WHERE user_id = ?
        """, (user_id,))
        if self.db.cursor.fetchone() is None:
            self.db.cursor.execute("""
                INSERT INTO user_notifications (user_id, dm_owner_controls, dm_admin_donate)
                VALUES (?, 1, 0)
            """, (user_id,))
        else:
            self.db.cursor.execute("""
                UPDATE user_notifications
                SET dm_owner_controls = 1
                WHERE user_id = ?
            """, (user_id,))
        self.db.connection.commit()

    def get_dm_admin_donate(self, user_id: int):
        self.db.cursor.execute("""
            SELECT dm_admin_donate
            FROM user_notifications
            WHERE user_id = ?
        """, (user_id,))
        row = self.db.cursor.fetchone()

        if row is None or row[0] == 0:
            return False

        return True

    def set_dm_admin_donate(self, user_id: int):
        self.db.cursor.execute("""
            SELECT user_id
            FROM user_notifications
            WHERE user_id = ?
        """, (user_id,))
        if self.db.cursor.fetchone() is None:
            self.db.cursor.execute("""
                INSERT INTO user_notifications (user_id, dm_owner_controls, dm_admin_donate)
                VALUES (?, 0, 1)
            """, (user_id,))
        else:
            self.db.cursor.execute("""
                UPDATE user_notifications
                SET dm_admin_donate = 1
                WHERE user_id = ?
            """, (user_id,))
        self.db.connection.commit()
