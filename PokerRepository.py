from dataclasses import dataclass
import sqlite3

DB_NAME = "poker_repo.db"
HAND_VALUES_TABLE = "hand_values"

CREATE_TABLE_QUERY = f"""
    CREATE TABLE IF NOT EXISTS {HAND_VALUES_TABLE}
    (id INTEGER PRIMARY KEY, cards INTEGER, value INTEGER)
"""

INSERT_VALUE_QUERY = f"""
    INSERT INTO {HAND_VALUES_TABLE} (cards, value) VALUES (?, ?)
"""

SELECT_ALL_QUERY = f"""
    SELECT * FROM {HAND_VALUES_TABLE}
"""

@dataclass
class HandValueRecord:
    ID: int
    cards: int
    value: int

class PokerRepository:
    _connection: sqlite3.Connection
    _cursor: sqlite3.Cursor
    
    def connect(self):
        self._connection = sqlite3.connect(DB_NAME)
        self._cursor = self._connection.cursor()

    def create_table(self):
        self._cursor.execute(CREATE_TABLE_QUERY)

    def insert(self, cards: int, value: int):
        assert isinstance(cards, int), f"Incorrect type for cards: {cards}"
        assert isinstance(value, int), f"Incorrect type for value: {value}"
        self._cursor.execute(INSERT_VALUE_QUERY, (cards, value))

    def commit(self):
        self._connection.commit()

    def select_all(self) -> list[HandValueRecord]:
        try:
            self._cursor.execute(SELECT_ALL_QUERY)
            return [HandValueRecord(ID, cards, value) for (ID, cards, value) in self._cursor.fetchall()]
        
        except:
            return []

    def disconnect(self):
        self._connection.close()