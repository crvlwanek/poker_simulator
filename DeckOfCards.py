from dataclasses import dataclass
from enum import Enum
import functools
import operator
import random
from typing import Self


BLACK_SPADE_UNICODE = "\u2660"
BLACK_HEART_UNICODE = "\u2665"
BLACK_DIAMOND_UNICODE = "\u2666"
BLACK_CLUB_UNICODE = "\u2663"


class Suit(Enum):
    SPADE = 0
    HEART = 1
    DIAMOND = 2
    CLUB = 3

    __serialized = ["s", "h", "d", "c"]

    def to_unicode(suit) -> str:
        match (suit):
            case Suit.SPADE:
                return BLACK_SPADE_UNICODE
            case Suit.HEART:
                return BLACK_HEART_UNICODE
            case Suit.DIAMOND:
                return BLACK_DIAMOND_UNICODE
            case Suit.CLUB:
                return BLACK_CLUB_UNICODE
        
        raise TypeError("Unknown suit: " + suit)
    
    def serialize(self) -> str:
        return Suit.__serialized[self.value]
    
    @staticmethod
    def deserialize(value: str) -> Self:
        index = Suit.__serialized.index(value)
        if index == -1:
            raise ValueError(f"Could not deserialize value: {value}")
        
        return Suit(index)

class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    __mappings = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    __serialized = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
    assert len(__mappings) == 13, "Incorrect mappings"
    assert len(__serialized) == 13, "Incorrect mappings"

    def to_string(self) -> str:
        return Rank.__mappings[self.value - 2]
    
    def serialize(self) -> str:
        return Rank.__serialized[self.value - 2]
    
    @staticmethod
    def deserialize(value: str) -> Self:
        index = Rank.__serialized.index(value)
        if index == -1:
            raise ValueError(f"Could not deserialize value: {value}")
        
        return Rank(index + 2)


@dataclass(frozen=True)
class PlayingCard:
    rank: Rank
    suit: Suit

    def __repr__(self) -> str:
        return f"{self.rank.to_string()}{self.suit.to_unicode()}"
    
    @functools.cached_property
    def value(self) -> int:
        return 1 << (self.suit.value * 12 + self.rank.value - 2)
    
    def serialize(self) -> str:
        return f"{self.rank.serialize()}{self.suit.serialize()}"
    
    @staticmethod
    def deserialize(value: str) -> Self:
        assert len(value) == 2, f"String cannot be deserialized: {value}"
        return CARDS_BY_SERIALIZATION[value] 
    

STARTING_DECK = frozenset(PlayingCard(rank, suit) for rank in Rank for suit in Suit)
assert len(STARTING_DECK) == 52, "Incorrect starting deck"
CARDS_BY_VALUE = {card.value: card for card in STARTING_DECK}
CARDS_BY_SERIALIZATION = {card.serialize(): card for card in STARTING_DECK}


@dataclass
class DeckOfCards:
    cards: list[PlayingCard]

    def __init__(self):
        self.cards = list(STARTING_DECK)
    
    def shuffle(self) -> Self:
        random.shuffle(self.cards)
        return self

    def draw(self) -> PlayingCard:
        if len(self.cards) == 0:
            raise ValueError("Can't draw from an empty deck")
        
        return self.cards.pop()
    
    @staticmethod
    def get_card(value: int) -> PlayingCard:
        card = CARDS_BY_VALUE.get(value)
        if not card:
            raise ValueError("Card not found: " + str(value))
        
        return card
    
    @staticmethod
    def hash_cards(cards: list[PlayingCard]) -> int:
        return functools.reduce(operator.__or__, [card.value for card in cards])
    
    @staticmethod
    def unhash_cards(value: int) -> list[PlayingCard]:
        cards = []
        while value > 0:
            card = value & -value
            cards.append(DeckOfCards.get_card(card))
            value -= card

        return cards