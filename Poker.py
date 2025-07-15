from dataclasses import dataclass
from enum import Enum

from DeckOfCards import PlayingCard

HEX_DIGIT_BITS = 4

HAND_RANK_HEX = 5
FIRST_KICKER_HEX = 4
SECOND_KICKER_HEX = 3
THIRD_KICKER_HEX = 2
FOURTH_KICKER_HEX = 1
FIFTH_KICKER_HEX = 0

handrank_hexes = [
    HAND_RANK_HEX,
    FIRST_KICKER_HEX,
    SECOND_KICKER_HEX,
    THIRD_KICKER_HEX,
    FOURTH_KICKER_HEX,
    FIFTH_KICKER_HEX
]

class HandRank(Enum):
    ROYAL_FLUSH = 9
    STRAIGHT_FLUSH = 8
    FOUR_OF_A_KIND = 7
    FULL_HOUSE = 6
    FLUSH = 5
    STRAIGHT = 4
    THREE_OF_A_KIND = 3
    TWO_PAIR = 2
    ONE_PAIR = 1
    HIGH_CARD = 0

    def __str__(self):
        return " ".join(self.name.split("_")).title()
    
    def value_from(values: list[int]) -> int:
        hand_rank_value = 0
        for value, hex_index in zip(values, handrank_hexes):
            hand_rank_value |= value << (hex_index * HEX_DIGIT_BITS)

        return hand_rank_value

@dataclass
class PokerGameResult:
    hand_value: int
    winning_hands: list[list[PlayingCard]]
    winning_hole_cards: list[list[PlayingCard]]

    def is_draw(self):
        return len(self.winning_hands) > 1
    
    def get_hand_rank(self) -> HandRank:
        rank = self.hand_value >> (HAND_RANK_HEX * HEX_DIGIT_BITS)
        return HandRank(rank)
    
    def winning_hands_serialized(self) -> str:
        return "|".join(",".join(card.serialize() for card in hand) for hand in self.winning_hands)
    
    def winning_hole_cards_serialied(self) -> str:
        return "|".join(",".join(card.serialize() for card in hand) for hand in self.winning_hole_cards)