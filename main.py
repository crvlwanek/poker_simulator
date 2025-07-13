from PokerSimulator import PokerSimulator

simulator = PokerSimulator(number_of_players=6, use_precomputed_values=False)
simulator.run(iterations=100_000)