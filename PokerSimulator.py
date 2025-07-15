import time
from collections import defaultdict
from dataclasses import dataclass, field

from PokerEvaluator import HandClassification, PokerEvaluator, PokerGameResult
from PokerRepository import PokerRepository
from DeckOfCards import DeckOfCards, PlayingCard


@dataclass
class PokerSimulation:
    number_of_players: int
    deck: DeckOfCards = field(default_factory=lambda: DeckOfCards().shuffle())
    evaluator: PokerEvaluator = field(default_factory=PokerEvaluator)

    players: list[list[PlayingCard]] = field(default_factory=list)
    community_cards: list[PlayingCard] = field(default_factory=list)

    def __post_init__(self):
        if self.number_of_players > 22:
            raise ValueError(f"Too many players: (max: 22, given: {self.number_of_players})")
        
    def run(self) -> PokerGameResult:
        self.deal_hands()
        self.deal_community_cards()
        result = self.evaluator.evaluate(self.players, self.community_cards)
        return result

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
    use_precomputed_values: bool = True

    def __post_init__(self):
        if self.number_of_players > 22:
            raise ValueError(f"Too many players: (max: 22, given: {self.number_of_players})")

    def run(self, iterations: int):

        print("Starting simulator...")

        repo = PokerRepository()
        repo.connect()
        repo.create_tables()
        evaluator = PokerEvaluator(repo, use_precomputed_values=self.use_precomputed_values)
        evaluator.precompute()

        print("Starting iterations...")
        start_time = time.perf_counter()

        draw_count = win_count = 0
        ranks = defaultdict(int)
        winning_opening_hands = defaultdict(int)
        all_opening_hands = defaultdict(int)

        for iter_count in range(iterations):
            if iter_count and iter_count % 10_000 == 0:
                print(f"{iter_count:,}")

            simulation = PokerSimulation(self.number_of_players, evaluator=evaluator)
            result = simulation.run()
            for player in simulation.players:
                classification = HandClassification(player)
                all_opening_hands[repr(classification)] += 1

            if result.is_draw():
                draw_count += 1
            else:
                win_count += 1
                classification = HandClassification(result.winning_hole_cards[0])
                winning_opening_hands[repr(classification)] += 1

            repo.insert_result(result)

            hand_rank = result.get_hand_rank()
            ranks[hand_rank] += 1

        repo.commit()
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        print()
        print(f"Iterations completed: {iterations:,}")
        print(f"⏱️  Elapsed time: {elapsed_time:.2f} seconds")
        print(f"~{round(iterations / elapsed_time):,} iterations per second")
        print()

        if win_count:
            print(f"Wins: {win_count:,}")
        if draw_count:
            print(f"Draws: {draw_count:,}")

        print()
        for rank in sorted(ranks.items(), key=lambda x: x[0].value, reverse=True):
            print(f"{rank[0]}: {rank[1]:,}")

        print()
        best_starting_hands = {key: winning_opening_hands[key] / num_times_drawn for key, num_times_drawn in all_opening_hands.items()}
        for hand, value in sorted(best_starting_hands.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"{hand}: {value * 100:.2f}%")



