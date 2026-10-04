import sqlite3
import json


class ConversationMemory:

    def __init__(self, db_name="conversation.db"):

        self.connection = sqlite3.connect(db_name)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                summary TEXT,
                messages TEXT NOT NULL
            )
        """)

        self.connection.commit()

    def save(self, messages, summary=""):

        messages_json = json.dumps(
            messages,
            default=str
        )

        self.connection.execute(
            """
            INSERT OR REPLACE INTO conversations
            (id, summary, messages)
            VALUES (1, ?, ?)
            """,
            (summary, messages_json)
        )

        self.connection.commit()

    def load(self):

        cursor = self.connection.execute(
            """
            SELECT summary, messages
            FROM conversations
            WHERE id = 1
            """
        )

        row = cursor.fetchone()

        if row is None:
            return {
                "summary": "",
                "messages": []
            }
        
        summary, messages_json = row
        return {
            "summary": summary or "",
            "messages": json.loads(messages_json)
        }

    def clear(self):

        self.connection.execute(
            "DELETE FROM conversations"
        )

        self.connection.commit()

    def close(self):

        self.connection.close()