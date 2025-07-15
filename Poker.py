from dataclasses import dataclass
from enum import Enum
from typing import Self

from DeckOfCards import PlayingCard, Rank

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
    
class HandClassification:
    __suited_token = "s"
    __offsuit_token = "o"

    def __init__(self, cards: list[PlayingCard]):
        if len(cards) > 0:
            assert len(cards) == 2, "Incorrect number of cards in starting hand"
            self.ranks = [card.rank for card in cards]
            self.suited = cards[0].suit.value == cards[1].suit.value
            self._finish_init()

    def _finish_init(self):
        self.ranks.sort(key=lambda x: x.value, reverse=True)
        self.pair = self.ranks[0].value == self.ranks[1].value

    def get_suited_or_pair(self) -> str:
        if self.pair:
            return ""
        
        return self.__suited_token if self.suited else self.__offsuit_token

    def __repr__(self) -> str:
        return f"{self.ranks[0].serialize()}{self.ranks[1].serialize()}{self.get_suited_or_pair()}"

    @staticmethod
    def deserialize(value: str) -> Self:
        assert 2 <= len(value) <= 3, f"Could not deserialize value: {value}"

        classification = HandClassification([])
        classification.ranks = [Rank.deserialize(value[0]), Rank.deserialize(value[1])]
        classification.suited = len(value) == 3 and value[2] == "s"
        classification._finish_init()

SerializedResult = tuple[int, int, str, str, int]

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
    
    @staticmethod
    def deserialize_all(results: list[SerializedResult]) -> list[Self]:
        return [PokerGameResult.deserialize(result) for result in results]

    @staticmethod
    def deserialize(result_serialized: SerializedResult) -> Self:
        _, _, winning_hands, winning_hole_cards, hand_value = result_serialized

        winning_hands = [[
            PlayingCard.deserialize(card) for card in hand.split(",")
        ] for hand in winning_hands.split("|")]

        winning_hole_cards = [[
            PlayingCard.deserialize(card) for card in hand.split(",")
        ] for hand in winning_hole_cards.split("|")]

        return PokerGameResult(hand_value, winning_hands, winning_hole_cards)

