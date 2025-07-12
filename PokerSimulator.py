from collections import defaultdict
from functools import lru_cache
import time
from typing import Union
from enum import Enum
from dataclasses import dataclass, field
import itertools

from PokerRepository import PokerRepository
from DeckOfCards import DeckOfCards, PlayingCard, Rank

HEX_DIGIT_BITS = 4

HAND_RANK_HEX = 5
FIRST_KICKER_HEX = 4
SECOND_KICKER_HEX = 3
THIRD_KICKER_HEX = 2
FOURTH_KICKER_HEX = 1
FIFTH_KICKER_HEX = 0
    

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

@lru_cache
def get_card_hash(card: PlayingCard) -> int:
    return 1 << (card.suit.value * 12 + card.rank.value - 2)

@dataclass
class PokerEvaluator:
    repository: PokerRepository

    def hash_hand(self, cards: list[PlayingCard]) -> int:
        card_hash = 0
        for card in cards:
            card_hash |= get_card_hash(card)

        return card_hash

    def precompute(self):

        hand_values = self.repository.select_all()
        if hand_values:
            print("Precomputed values loaded from db")
            self.values = {}
            for record in hand_values:
                self.values[record.cards] = record.value

            return


        print("Starting precomputation...")
        start_time = time.perf_counter()

        self.values = {}

        deck = DeckOfCards().cards

        count = 0
        for i, card1 in enumerate(deck):
            for j, card2 in enumerate(deck[i+1:], start=i+1):
                for k, card3 in enumerate(deck[j+1:], start=j+1):
                    for l, card4 in enumerate(deck[k+1:], start=k+1):
                        for _, card5 in enumerate(deck[l+1:], start=l+1):
                            cards = [card1, card2, card3, card4, card5]
                            rank, hand = PokerEvaluator._eval_hand(cards)
                            card_hash = self.hash_hand(hand)
                            self.values[card_hash] = rank
                            count += 1

                            if count % 100_000 == 0:
                                print(count)

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print("✅ Precomputation complete")
        print(f"⏱️  Elapsed time: {elapsed_time:.6f} seconds")
        print("Adding to repository...")

        self.repository.create_table()
        for cards, value in self.values.items():
            self.repository.insert(cards, value)

        self.repository.commit()

    def get_value(self, hand: list[PlayingCard]) -> int:
        hand_hash = self.hash_hand(hand)
        return self.values[hand_hash]

    def evaluate(self, players: list[Player], community_cards: Cards):
        results = defaultdict(list)
        for i, player in enumerate(players):
            if not self.values:
                rank, hand = PokerEvaluator._eval_hand([*player, *community_cards])
                results[rank].append(hand)

            else:
                cards = [*player, *community_cards]
                ranks = defaultdict(list)
                for i in range(3):
                    hand = cards[i:i+5]
                    value = self.get_value(hand)
                    ranks[value].append(hand)

                best_rank = max(ranks.keys())
                results[best_rank].append(ranks[best_rank][0])

        best_rank = max(results.keys())
        winning_hands = results[best_rank]
        result = "Win" if len(winning_hands) == 1 else "Draw"
        #print(result, winning_hands)

    @staticmethod
    def _eval_hand(cards: list[PlayingCard]) -> tuple[int, list[PlayingCard]]:
        flush_candidates = PokerEvaluator._get_flush_candidates(cards)
        straight_flush = PokerEvaluator._eval_straight(flush_candidates, need_sort=False)

        # Royal flush
        if straight_flush and straight_flush[1].rank == Rank.KING:
            assert len(straight_flush) == 5, "Incorrect royal flush"
            hand_rank = HandRank.ROYAL_FLUSH.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)

            return hand_rank, straight_flush
        
        # Straight flush
        if straight_flush:
            assert len(straight_flush) == 5, "Incorrect straight flush"
            hand_rank = HandRank.STRAIGHT_FLUSH.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            hand_rank |= straight_flush[0].rank.value << (FIRST_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= straight_flush[1].rank.value << (SECOND_KICKER_HEX * HEX_DIGIT_BITS)

            return hand_rank, straight_flush

        rank_groups = PokerEvaluator._get_rank_groups(cards)

        # Four of a kind
        if len(rank_groups[0]) == 4:
            four_of_a_kind = rank_groups[0]
            kicker = max(PokerEvaluator._flatten_groups(rank_groups[1:]), key=lambda x: x.rank.value)
            hand_rank = HandRank.FOUR_OF_A_KIND.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            hand_rank |= four_of_a_kind[0].rank.value << (FIRST_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= kicker.rank.value << (SECOND_KICKER_HEX * HEX_DIGIT_BITS)
            four_of_a_kind.append(kicker)

            return hand_rank, four_of_a_kind

        # Full house
        if len(rank_groups[0]) == 3 and len(rank_groups[1]) >= 2:
            hand_rank = HandRank.FULL_HOUSE.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            hand_rank |= rank_groups[0][0].rank.value << (FIRST_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= rank_groups[1][0].rank.value << (SECOND_KICKER_HEX * HEX_DIGIT_BITS)
            full_house = [*rank_groups[0], *rank_groups[1][:2]]
            assert len(full_house) == 5, "Incorrect full house"

            return hand_rank, full_house
        
        # Flush
        if flush_candidates:
            flush = flush_candidates[:5]
            assert len(flush) == 5, "Incorrect straight flush"
            hand_rank = HandRank.FLUSH.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            hand_rank |= flush[0].rank.value << (FIRST_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= flush[1].rank.value << (SECOND_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= flush[2].rank.value << (THIRD_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= flush[3].rank.value << (FOURTH_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= flush[4].rank.value << (FIFTH_KICKER_HEX * HEX_DIGIT_BITS)

            return hand_rank, flush
        
        straight = PokerEvaluator._eval_straight(cards)

        # Straight
        if straight:
            assert len(straight) == 5, "Incorrect straight"
            hand_rank = HandRank.STRAIGHT.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            hand_rank |= straight[0].rank.value << (FIRST_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= straight[1].rank.value << (SECOND_KICKER_HEX * HEX_DIGIT_BITS)

            return hand_rank, straight
        
        # Three of a kind
        if len(rank_groups[0]) == 3:
            three_of_a_kind = rank_groups[0]
            kickers = sorted(PokerEvaluator._flatten_groups(rank_groups[1:]), key=lambda x: x.rank.value, reverse=True)[:2]
            three_of_a_kind = [*three_of_a_kind, *kickers]
            hand_rank = HandRank.THREE_OF_A_KIND.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            hand_rank |= three_of_a_kind[0].rank.value << (FIRST_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= kickers[0].rank.value << (SECOND_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= kickers[1].rank.value << (THIRD_KICKER_HEX * HEX_DIGIT_BITS)

            assert kickers[0].rank != kickers[1].rank, "Missed a full house"
            
            return hand_rank, three_of_a_kind
        
        # Two pair
        if len(rank_groups[0]) == 2 and len(rank_groups[1]) == 2:
            kicker = max(PokerEvaluator._flatten_groups(rank_groups[2:]), key=lambda x: x.rank.value)
            two_pair = [*rank_groups[0], *rank_groups[1], kicker]
            
            hand_rank = HandRank.TWO_PAIR.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            hand_rank |= rank_groups[0][0].rank.value << (FIRST_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= rank_groups[1][0].rank.value << (SECOND_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= kicker.rank.value << (THIRD_KICKER_HEX * HEX_DIGIT_BITS)

            return hand_rank, two_pair
        
        if len(rank_groups[0]) == 2:
            kickers = sorted(PokerEvaluator._flatten_groups(rank_groups[1:]), key=lambda x: x.rank.value, reverse=True)[:3]
            one_pair = [*rank_groups[0], *kickers]

            assert len(one_pair) == 5, "Incorrect one pair"

            hand_rank = HandRank.ONE_PAIR.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
            hand_rank |= rank_groups[0][0].rank.value << (FIRST_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= kickers[0].rank.value << (SECOND_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= kickers[1].rank.value << (THIRD_KICKER_HEX * HEX_DIGIT_BITS)
            hand_rank |= kickers[2].rank.value << (FOURTH_KICKER_HEX * HEX_DIGIT_BITS)

            return hand_rank, one_pair
        
        cards.sort(key=lambda x: x.rank.value, reverse=True)
        cards = cards[:5]

        assert len(cards) == 5, "Incorrect high card"

        hand_rank = HandRank.HIGH_CARD.value << (HAND_RANK_HEX * HEX_DIGIT_BITS)
        hand_rank |= cards[0].rank.value << (FIRST_KICKER_HEX * HEX_DIGIT_BITS)
        hand_rank |= cards[1].rank.value << (SECOND_KICKER_HEX * HEX_DIGIT_BITS)
        hand_rank |= cards[2].rank.value << (THIRD_KICKER_HEX * HEX_DIGIT_BITS)
        hand_rank |= cards[3].rank.value << (FOURTH_KICKER_HEX * HEX_DIGIT_BITS)
        hand_rank |= cards[4].rank.value << (FIFTH_KICKER_HEX * HEX_DIGIT_BITS)

        return hand_rank, cards
    
    @staticmethod
    def _flatten_groups(groups: list[Cards]) -> Cards:
        return [card for group in groups for card in group]

    @staticmethod
    def _get_flush_candidates(cards: Cards) -> Cards:
        cards = sorted(cards, key=lambda x: x.suit.value)
        groups = [list(group) for _, group in itertools.groupby(cards, key=lambda x: x.suit.value)]
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
        cards = sorted(cards, key=lambda x: x.rank.value)
        groups = [list(group) for _, group in itertools.groupby(cards, key=lambda x: x.rank.value)]
        groups.sort(key=lambda x: (len(x), x[0].rank.value), reverse=True)

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

        print("Starting simulator...")

        repo = PokerRepository()
        repo.connect()
        evaluator = PokerEvaluator(repo)
        evaluator.precompute()

        start_time = time.perf_counter()

        for _ in range(iterations):
            simulation = PokerSimulation(self.number_of_players, evaluator=evaluator)
            simulation.run()

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        print()
        print(f"Iterations: {iterations}")
        print(f"⏱️  Elapsed time: {elapsed_time:.6f} seconds")
        print(f"~{round(iterations / elapsed_time)} iterations per second")



simulator = PokerSimulator(number_of_players=6)
simulator.run(iterations=100_000)