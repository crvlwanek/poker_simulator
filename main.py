import argparse
from PokerSimulator import PokerSimulator

parser = argparse.ArgumentParser(description="A script that processes two named arguments.")
parser.add_argument("--players", type=int, help="The number of players to simulate.")
parser.add_argument("--iterations", type=int, help="The number of iterations to simulate.")
parser.add_argument("--precompute", type=bool, help="Whether or not to use precomputed values.")
args = parser.parse_args()

# Argument defaults
number_of_players = args.players or 6
use_precomputed_values = args.precompute or False
iterations = args.iterations or 100_000

simulator = PokerSimulator(number_of_players, use_precomputed_values)
simulator.run(iterations)