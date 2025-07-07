from enum import Enum
from dataclasses import dataclass
import random


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
    ACE = 1
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

    __mappings = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    assert len(__mappings) == 13, "Incorrect mappings"

    @staticmethod
    def to_string(rank: Enum) -> str:
        return Rank.__mappings[rank.value - 1]
    

@dataclass(frozen=True)
class PlayingCard:
    rank: Rank
    suit: Suit

    def __repr__(self):
        return f"{Rank.to_string(self.rank)}{Suit.to_unicode(self.suit)}"
    

STARTING_DECK = frozenset(PlayingCard(rank, suit) for rank in Rank for suit in Suit)
assert len(STARTING_DECK) == 52, "Incorrect starting deck"


@dataclass
class DeckOfCards:
    cards: list[PlayingCard]

    def __init__(self):
        self.cards = list(STARTING_DECK)
    
    def shuffle(self):
        random.shuffle(self.cards)

deck = DeckOfCards()
print(deck)
deck.shuffle()
print(deck)
