from database.repos.base_repo import BaseRepo


class PlaceholdersRepository(BaseRepo):  # bot.repos.placeholders
    def add(self, guild_id: int, placeholder: str, replace_text: str, role_id: int = None):
        # Strip and add {}
        placeholder = placeholder.strip("{}")
        placeholder = f"{{{placeholder}}}"
        self.db.cursor.execute("""
            INSERT INTO placeholders
            (guild_id, placeholder, replace_text, role_id)
            VALUES (?, ?, ?, ?)
        """, (int(guild_id), placeholder, replace_text, role_id))
        self.db.connection.commit()
        return self.db.cursor.lastrowid

    def get(self, guild_id: int, entry_id: int):
        self.db.cursor.execute("""
            SELECT rowid, placeholder, replace_text, role_id
            FROM placeholders
            WHERE guild_id = ? AND rowid = ?
        """, (int(guild_id), int(entry_id)))
        row = self.db.cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "placeholder": row[1],
            "replace_text": row[2],
            "role_id": row[3],
        }

    def get_all(self, guild_id: int):
        self.db.cursor.execute("""
            SELECT rowid, placeholder, replace_text, role_id
            FROM placeholders
            WHERE guild_id = ?
            ORDER BY rowid
        """, (int(guild_id),))
        rows = self.db.cursor.fetchall()
        return [
            {
                "id": row[0],
                "placeholder": row[1],
                "replace_text": row[2],
                "role_id": row[3],
            }
            for row in rows
        ]

    def remove(self, guild_id: int, entry_id: int):
        self.db.cursor.execute("""
            DELETE FROM placeholders
            WHERE guild_id = ? AND rowid = ?
        """, (int(guild_id), int(entry_id)))
        self.db.connection.commit()
        return self.db.cursor.rowcount > 0
