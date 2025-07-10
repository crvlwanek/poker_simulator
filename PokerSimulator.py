import time
from typing import Self, Union
from enum import Enum
from dataclasses import dataclass, field
import random
import itertools


BLACK_SPADE_UNICODE = "\u2660"
BLACK_HEART_UNICODE = "\u2665"
BLACK_DIAMOND_UNICODE = "\u2666"
BLACK_CLUB_UNICODE = "\u2663"

HEX_DIGIT_BITS = 4
HAND_RANK_HEX = 4

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
    

STARTING_DECK = frozenset(PlayingCard(rank, suit) for rank in Rank for suit in Suit)
assert len(STARTING_DECK) == 52, "Incorrect starting deck"


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


Player = list[PlayingCard]
Cards = list[PlayingCard]

@dataclass
class PokerEvaluator:
    def evaluate(self, players: list[Player], community_cards: Cards):
        for player in players:
            evaluation = PokerEvaluator._eval_single_player(player, community_cards)
            if evaluation:
                print(hex(evaluation))

    @staticmethod
    def _eval_single_player(player: Player, community_cards: Cards) -> int:
        cards: list[PlayingCard] = [*player, *community_cards]
        flush_candidates = PokerEvaluator._get_flush_candidates(cards)
        straight_flush = PokerEvaluator._eval_straight(flush_candidates, need_sort=False)

        if straight_flush and straight_flush[1].rank == Rank.KING:
            assert len(straight_flush) == 5, "Incorrect rpyal flush"
            return HandRank.ROYAL_FLUSH.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
        
        if straight_flush:
            assert len(straight_flush) == 5, "Incorrect straight flush"
            hand_rank = HandRank.STRAIGHT_FLUSH.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            hand_rank |= straight_flush[0].rank.value << (3 * HEX_DIGIT_BITS)
            hand_rank |= straight_flush[1].rank.value << (2 * HEX_DIGIT_BITS)
            return hand_rank

        rank_groups = PokerEvaluator._get_rank_groups(cards)

        if len(rank_groups[0]) == 4:
            four_of_a_kind = rank_groups[0]
            hand_rank = HandRank.FOUR_OF_A_KIND.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            print(four_of_a_kind)

        return None

    @staticmethod
    def _get_flush_candidates(cards: Cards) -> Cards:
        groups = [list(group) for _, group in itertools.groupby(cards, key=lambda x: x.suit)]
        for group in groups:
            if len(group) >= 5:
                group.sort(key=lambda x: x.rank.value, reverse=True)
                return group
            
        return []
    
    @staticmethod
    def _eval_straight(cards: Cards, need_sort: bool = True) -> Cards:
        if not cards: 
            return cards
        
        if need_sort:
            cards.sort(key=lambda x: x.rank.value, reverse=True)

        straight = [cards[0]]
        for card in cards[1:]:
            if card.rank.value == straight[-1].rank.value - 1:
                straight.append(card)
                continue

            straight = [card]

        if straight and straight[-1].rank == Rank.TWO:
            ace = PokerEvaluator._find_rank(cards, Rank.ACE)
            if ace:
                while len(straight) > 4:
                    straight.pop(0)
                straight.insert(0, ace)

        if len(straight) >= 5:
            return straight[:5]
        
        return []
    
    @staticmethod
    def _get_rank_groups(cards: Cards) -> list[list[PlayingCard]]:
        groups = [list(group) for _, group in itertools.groupby(cards, key=lambda x: x.rank)]
        groups.sort(key=lambda x: len(x), reverse=True)

        return groups

    @staticmethod
    def _find_rank(cards: Cards, rank: Rank) -> Union[PlayingCard, None]:
        for card in cards:
            if card.rank == rank:
                return card
            
        return None



@dataclass
class PokerSimulation:
    number_of_players: int
    deck: DeckOfCards = field(default_factory=lambda: DeckOfCards().shuffle())
    evaluator: PokerEvaluator = field(default_factory=PokerEvaluator)

    players: list[Player] = field(default_factory=list)
    community_cards: Cards = field(default_factory=list)

    def __post_init__(self):
        if self.number_of_players > 22:
            raise ValueError(f"Too many players: (max: 22, given: {self.number_of_players})")
        
    def run(self):
        self.deal_hands()
        self.deal_community_cards()
        self.evaluator.evaluate(self.players, self.community_cards)

    def deal_hands(self):
        self.players = [[] for _ in range(self.number_of_players)]

        for _ in range(2):
            for player in self.players:
                player.append(self.deck.draw())

        assert len(self.deck.cards) == 52 - (2 * self.number_of_players), "Invalid deal"

    def deal_community_cards(self):
        for _ in range(5):
            self.community_cards.append(self.deck.draw())


@dataclass
class PokerSimulator:
    number_of_players: int

    def __post_init__(self):
        if self.number_of_players > 22:
            raise ValueError(f"Too many players: (max: 22, given: {self.number_of_players})")

    def run(self, iterations: int):
        start_time = time.perf_counter()

        for _ in range(iterations):
            simulation = PokerSimulation(self.number_of_players)
            simulation.run()

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        print()
        print(f"Iterations: {iterations}")
        print(f"Elapsed time: {elapsed_time:.6f} seconds")
        print(f"~{round(iterations / elapsed_time)} iterations per second")



simulator = PokerSimulator(number_of_players=6)
simulator.run(iterations=10000)