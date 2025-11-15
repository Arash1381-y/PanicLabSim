from __future__ import annotations

import argparse
import random

from card import AmoebaCard, Card
from parser import parse_file
from render_art import (
    BOARD_OUTPUT_DEFAULT,
    PIE_OUTPUT_DEFAULT,
    DEFAULT_CARD_SCALE,
    plot_pie_chart,
    render_board_image,
)
from simulator import DEFAULT_EXPERIMENTS, configure_neighbors, simulate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate Panic Lab card experiments.")
    parser.add_argument(
        "-i",
        "--input",
        default="input.txt",
        help="Path to the input file describing the card ring.",
    )
    parser.add_argument(
        "-n",
        "--experiments",
        type=int,
        default=DEFAULT_EXPERIMENTS,
        help="Number of random experiments to run.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional RNG seed for deterministic runs.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip the matplotlib visualizations.",
    )
    parser.add_argument(
        "--pie-output",
        default=PIE_OUTPUT_DEFAULT,
        help="Where to save the pie chart image.",
    )
    parser.add_argument(
        "--board-output",
        default=BOARD_OUTPUT_DEFAULT,
        help="Where to save the circular board render.",
    )
    parser.add_argument(
        "--card-scale",
        type=float,
        default=DEFAULT_CARD_SCALE,
        help="Extra multiplier applied to the rendered card art size.",
    )
    return parser.parse_args()


def print_rankings(points: dict[Card, int]) -> bool:
    total_points = sum(points.values())
    if total_points == 0:
        print("No cards were matched in any experiment.")
        return False

    print("\n--- Experiment Results ---")
    amoeba_cards = [card for card in points if isinstance(card, AmoebaCard)]
    amoeba_cards.sort(key=lambda card: points[card], reverse=True)

    for card in amoeba_cards:
        if points[card] == 0:
            continue
        win_percentage = (points[card] / total_points) * 100
        print(f"Line {card.line_number}: {card} - Win Chance: {win_percentage:.2f}%")
    return True


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    cards = parse_file(args.input)
    if not cards:
        print("No cards parsed.")
        return

    configure_neighbors(cards)
    points = simulate(cards, rng, args.experiments)

    if not print_rankings(points):
        return

    if args.no_plot:
        return

    plot_pie_chart(points, args.pie_output)
    render_board_image(cards, points, args.board_output)


if __name__ == "__main__":
    main()
