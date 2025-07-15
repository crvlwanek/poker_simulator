from dataclasses import dataclass
import sqlite3

from Poker import PokerGameResult

DB_NAME = "poker_repo.db"
HAND_VALUES_TABLE = "hand_values"
RESULTS_TABLE = "results"

CREATE_HANDVALUES_QUERY = f"""
    CREATE TABLE IF NOT EXISTS {HAND_VALUES_TABLE}
    (id INTEGER PRIMARY KEY, cards INTEGER, value INTEGER)
"""

CREATE_RESULTS_QUERY = f"""
    CREATE TABLE IF NOT EXISTS {RESULTS_TABLE}
    (id INTEGER PRIMARY KEY, draw INTEGER, winning_hands TEXT, winning_hole_cards TEXT, hand_value INTEGER)
"""

INSERT_VALUE_QUERY = f"""
    INSERT INTO {HAND_VALUES_TABLE} (cards, value) VALUES (?, ?)
"""

INSERT_RESULT_QUERY = f"""
    INSERT INTO {RESULTS_TABLE} (draw, winning_hands, winning_hole_cards, hand_value) VALUES (?, ?, ?, ?)
"""

SELECT_ALL_HANDVALUES_QUERY = f"""
    SELECT * FROM {HAND_VALUES_TABLE}
"""

SELECT_ALL_RESULTS_QUERY = f"""
    SELECT * FROM {RESULTS_TABLE}
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

    def commit(self):
        self._connection.commit()

    def disconnect(self):
        self._connection.close()

    def create_tables(self):
        self._cursor.execute(CREATE_HANDVALUES_QUERY)
        self._cursor.execute(CREATE_RESULTS_QUERY)

    def insert(self, cards: int, value: int):
        assert isinstance(cards, int), f"Incorrect type for cards: {cards}"
        assert isinstance(value, int), f"Incorrect type for value: {value}"
        self._cursor.execute(INSERT_VALUE_QUERY, (cards, value))

    def insert_result(self, result: PokerGameResult):
        draw = result.is_draw()
        winning_hands = result.winning_hands_serialized()
        winning_hole_cards = result.winning_hole_cards_serialied()
        hand_value = result.hand_value

        assert isinstance(draw, int), f"Incorrect type for draw: {draw}"
        assert isinstance(winning_hands, str), f"Incorrect type for winning_hands: {winning_hands}"
        assert isinstance(winning_hole_cards, str), f"Incorrect type for winning_hole_cards: {winning_hole_cards}"
        assert isinstance(hand_value, int), f"Incorrect type for hand_value: {hand_value}"

        self._cursor.execute(INSERT_RESULT_QUERY, (draw, winning_hands, winning_hole_cards, hand_value))

    def select_all(self) -> list[HandValueRecord]:
        try:
            self._cursor.execute(SELECT_ALL_HANDVALUES_QUERY)
            return [HandValueRecord(ID, cards, value) for (ID, cards, value) in self._cursor.fetchall()]
        
        except:
            return []
        
    def select_all_results(self):
        try:
            self._cursor.execute(SELECT_ALL_RESULTS_QUERY)
            return self._cursor.fetchall()
        except:
            return []

