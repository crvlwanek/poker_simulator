from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import itertools
import time
from typing import Union

from DeckOfCards import DeckOfCards, PlayingCard, Rank
from Poker import PokerGameResult
from PokerRepository import PokerRepository
from Poker import HandRank
    
class HandClassification:

    def __init__(self, cards: list[PlayingCard]):
        assert len(cards) == 2, "Incorrect number of cards in starting hand"
        cards.sort(key=lambda x: x.rank.value, reverse=True)

        self.ranks = [card.rank for card in cards]
        self.suited = cards[0].suit.value == cards[1].suit.value
        self.pair = cards[0].rank.value == cards[1].rank.value

    def get_suited_or_pair(self) -> str:
        if self.pair:
            return ""
        
        return "s" if self.suited else "o"

    def __repr__(self) -> str:
        return f"{self.ranks[0].serialize()}{self.ranks[1].serialize()}{self.get_suited_or_pair()}"


@dataclass
class PokerEvaluator:
    repository: PokerRepository
    use_precomputed_values: bool = True

    def __post_init__(self):
        self.values = {}

    def precompute(self):
        if not self.use_precomputed_values:
            return

        hand_values = self.repository.select_all()
        if hand_values:
            print("Precomputed values loaded from db")
            self.values = {}
            for record in hand_values:
                self.values[record.cards] = record.value

            return

        print("Starting precomputation...")
        start_time = time.perf_counter()

        deck = DeckOfCards().cards
        five_card_hands = itertools.combinations(deck, 5)

        for hand in five_card_hands:
            rank, hand = PokerEvaluator._eval_hand(list(hand))
            card_hash = DeckOfCards.hash_cards(hand)
            self.values[card_hash] = rank

            if len(self.values) % 100_000 == 0:
                print(f"{len(self.values):,}")

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print("✅ Precomputation complete")
        print(f"⏱️  Elapsed time: {elapsed_time:.6f} seconds")
        print("Adding to repository...")

        for cards, value in self.values.items():
            self.repository.insert(cards, value)

        self.repository.commit()

    def get_value(self, hand: list[PlayingCard]) -> int:
        hand_hash = DeckOfCards.hash_cards(hand)
        return self.values[hand_hash]

    def evaluate(self, players: list[list[PlayingCard]], community_cards: list[PlayingCard]) -> PokerGameResult:
        results = defaultdict(list)
        for index, player in enumerate(players):
            if not self.values:
                rank, hand = PokerEvaluator._eval_hand([*player, *community_cards])
                results[rank].append((index, hand))

            else:
                cards = [*player, *community_cards]
                ranks = defaultdict(list)
                for hand in itertools.combinations(cards, 5):
                    hand = list(hand)
                    value = self.get_value(hand)
                    ranks[value].append((index, hand))

                best_rank = max(ranks.keys())
                results[best_rank].append(ranks[best_rank][0])

        best_rank = max(results.keys())
        winning_hands = [result[1] for result in results[best_rank]]
        winning_indexes = [result[0] for result in results[best_rank]]
        winning_hole_cards = [players[index] for index in winning_indexes]

        assert len(winning_hands) == len(winning_hole_cards), "Lists are not the same length"

        return PokerGameResult(best_rank, winning_hands, winning_hole_cards)
        

    @staticmethod
    def _eval_hand(cards: list[PlayingCard]) -> tuple[int, list[PlayingCard]]:
        flush_candidates = PokerEvaluator._get_flush_candidates(cards)
        straight_flush = PokerEvaluator._eval_straight(flush_candidates, need_sort=False)

        # Royal flush
        if straight_flush and straight_flush[1].rank == Rank.KING:
            assert len(straight_flush) == 5, "Incorrect royal flush"
            hand_rank = HandRank.value_from([
                HandRank.ROYAL_FLUSH.value
             ])

            return hand_rank, straight_flush
        
        # Straight flush
        if straight_flush:
            assert len(straight_flush) == 5, "Incorrect straight flush"
            hand_rank = HandRank.value_from([
                HandRank.STRAIGHT_FLUSH.value,
                straight_flush[0].rank.value,
                straight_flush[1].rank.value
            ])

            return hand_rank, straight_flush

        rank_groups = PokerEvaluator._get_rank_groups(cards)

        # Four of a kind
        if len(rank_groups[0]) == 4:
            four_of_a_kind = rank_groups[0]
            kicker = max(PokerEvaluator._flatten_groups(rank_groups[1:]), key=lambda x: x.rank.value)
            hand_rank = HandRank.value_from([
                HandRank.FOUR_OF_A_KIND.value,
                four_of_a_kind[0].rank.value,
                kicker.rank.value
            ])
            four_of_a_kind.append(kicker)

            return hand_rank, four_of_a_kind

        # Full house
        if len(rank_groups[0]) == 3 and len(rank_groups[1]) >= 2:
            hand_rank = HandRank.value_from([
                HandRank.FULL_HOUSE.value,
                rank_groups[0][0].rank.value,
                rank_groups[1][0].rank.value
            ]) 
            full_house = [*rank_groups[0], *rank_groups[1][:2]]
            assert len(full_house) == 5, "Incorrect full house"

            return hand_rank, full_house
        
        # Flush
        if flush_candidates:
            flush = flush_candidates[:5]
            assert len(flush) == 5, "Incorrect straight flush"
            hand_rank = HandRank.value_from([
                HandRank.FLUSH.value,
                flush[0].rank.value,
                flush[1].rank.value,
                flush[2].rank.value,
                flush[3].rank.value,
                flush[4].rank.value 
            ]) 

            return hand_rank, flush
        
        straight = PokerEvaluator._eval_straight(cards)

        # Straight
        if straight:
            assert len(straight) == 5, "Incorrect straight"
            hand_rank = HandRank.value_from([
                HandRank.STRAIGHT.value,
                straight[0].rank.value,
                straight[1].rank.value 
            ])

            return hand_rank, straight
        
        # Three of a kind
        if len(rank_groups[0]) == 3:
            three_of_a_kind = rank_groups[0]
            kickers = sorted(PokerEvaluator._flatten_groups(rank_groups[1:]), key=lambda x: x.rank.value, reverse=True)[:2]
            three_of_a_kind = [*three_of_a_kind, *kickers]
            hand_rank = HandRank.value_from([
                HandRank.THREE_OF_A_KIND.value,
                three_of_a_kind[0].rank.value,
                kickers[0].rank.value,
                kickers[1].rank.value 
            ])

            assert kickers[0].rank != kickers[1].rank, "Missed a full house"
            
            return hand_rank, three_of_a_kind
        
        # Two pair
        if len(rank_groups[0]) == 2 and len(rank_groups[1]) == 2:
            kicker = max(PokerEvaluator._flatten_groups(rank_groups[2:]), key=lambda x: x.rank.value)
            two_pair = [*rank_groups[0], *rank_groups[1], kicker]
            
            hand_rank = HandRank.value_from([
                HandRank.TWO_PAIR.value,
                rank_groups[0][0].rank.value,
                rank_groups[1][0].rank.value,
                kicker.rank.value 
            ])

            return hand_rank, two_pair
        
        if len(rank_groups[0]) == 2:
            kickers = sorted(PokerEvaluator._flatten_groups(rank_groups[1:]), key=lambda x: x.rank.value, reverse=True)[:3]
            one_pair = [*rank_groups[0], *kickers]

            assert len(one_pair) == 5, "Incorrect one pair"

            hand_rank = HandRank.value_from([
                HandRank.ONE_PAIR.value,
                rank_groups[0][0].rank.value,
                kickers[0].rank.value,
                kickers[1].rank.value,
                kickers[2].rank.value 
            ])

            return hand_rank, one_pair
        
        cards.sort(key=lambda x: x.rank.value, reverse=True)
        cards = cards[:5]

        assert len(cards) == 5, "Incorrect high card"

        hand_rank = HandRank.value_from([
            HandRank.HIGH_CARD.value,
            cards[0].rank.value,
            cards[1].rank.value,
            cards[2].rank.value,
            cards[3].rank.value,
            cards[4].rank.value 
        ])

        return hand_rank, cards
    
    @staticmethod
    def _flatten_groups(groups: list[list[PlayingCard]]) -> list[PlayingCard]:
        return [card for group in groups for card in group]

    @staticmethod
    def _get_flush_candidates(cards: list[PlayingCard]) -> list[PlayingCard]:
        cards = sorted(cards, key=lambda x: x.suit.value)
        groups = [list(group) for _, group in itertools.groupby(cards, key=lambda x: x.suit.value)]
        for group in groups:
            if len(group) >= 5:
                group.sort(key=lambda x: x.rank.value, reverse=True)
                return group
            
        return []
    
    @staticmethod
    def _eval_straight(cards: list[PlayingCard], need_sort: bool = True) -> list[PlayingCard]:
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
    def _get_rank_groups(cards: list[PlayingCard]) -> list[list[PlayingCard]]:
        cards = sorted(cards, key=lambda x: x.rank.value)
        groups = [list(group) for _, group in itertools.groupby(cards, key=lambda x: x.rank.value)]
        groups.sort(key=lambda x: (len(x), x[0].rank.value), reverse=True)

        return groups

    @staticmethod
    def _find_rank(cards: list[PlayingCard], rank: Rank) -> Union[PlayingCard, None]:
        for card in cards:
            if card.rank == rank:
                return card
            
        return None

