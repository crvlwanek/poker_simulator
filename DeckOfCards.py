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

    @staticmethod
    def to_unicode(suit: Enum) -> str:
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
    assert len(__mappings) == 13, "Incorrect mappings"

    @staticmethod
    def to_string(rank: Enum) -> str:
        return Rank.__mappings[rank.value - 2]
    

@dataclass(frozen=True)
class PlayingCard:
    rank: Rank
    suit: Suit

    def __repr__(self):
        return f"{Rank.to_string(self.rank)}{Suit.to_unicode(self.suit)}"
    
    @functools.cached_property
    def value(self):
        return 1 << (self.suit.value * 12 + self.rank.value - 2)
    
    

STARTING_DECK = frozenset(PlayingCard(rank, suit) for rank in Rank for suit in Suit)
assert len(STARTING_DECK) == 52, "Incorrect starting deck"
CARDS_BY_VALUE = {card.value: card for card in STARTING_DECK}


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