from __future__ import annotations

import random
from typing import Sequence

from card import (
    AmoebaColor,
    Card,
    Configuration,
    Direction,
    Eye,
    LabCard,
    Pattern,
    VentCard,
)

DEFAULT_EXPERIMENTS = 10_000
MAX_STEPS_PER_RUN = 100


def configure_neighbors(cards: Sequence[Card]) -> None:
    """
    Connect cards in a ring and handle special vent routing.
    """
    if not cards:
        return

    num_cards = len(cards)
    for index, card in enumerate(cards):
        card.set_neighbors(cards[(index + 1) % num_cards], cards[(index - 1) % num_cards])

    _link_vents(cards)


def _link_vents(cards: Sequence[Card]) -> None:
    vent_indices = [idx for idx, card in enumerate(cards) if isinstance(card, VentCard)]
    if len(vent_indices) <= 1:
        return

    num_cards = len(cards)
    for position, vent_idx in enumerate(vent_indices):
        next_vent_idx = vent_indices[(position + 1) % len(vent_indices)]
        prev_vent_idx = vent_indices[(position - 1) % len(vent_indices)]

        clk_neighbor = _walk_to_non_vent(cards, (next_vent_idx + 1) % num_cards, step=1)
        counter_neighbor = _walk_to_non_vent(cards, (prev_vent_idx - 1) % num_cards, step=-1)
        cards[vent_idx].set_neighbors(clk_neighbor, counter_neighbor)


def _walk_to_non_vent(cards: Sequence[Card], start_index: int, step: int) -> Card:
    num_cards = len(cards)
    index = start_index % num_cards
    while isinstance(cards[index], VentCard):
        index = (index + step) % num_cards
    return cards[index]


def run_experiment(configuration: Configuration, start_lab: LabCard, direction: Direction) -> Card | None:
    current_card: Card = start_lab
    for _ in range(MAX_STEPS_PER_RUN):
        if current_card.is_matched(configuration):
            return current_card
        current_card = current_card.get_next(direction)
    return None


def simulate(cards: Sequence[Card], rng: random.Random, experiments: int) -> dict[Card, int]:
    lab_cards = [card for card in cards if isinstance(card, LabCard)]
    if not lab_cards:
        raise RuntimeError("No lab cards available to start experiments.")

    points = {card: 0 for card in cards}
    for _ in range(experiments):
        random_config = Configuration(
            rng.choice(list(AmoebaColor)),
            rng.choice(list(Pattern)),
            rng.choice(list(Eye)),
        )
        start_lab = rng.choice(lab_cards)
        direction = rng.choice(list(Direction))

        matched_card = run_experiment(random_config, start_lab, direction)
        if matched_card:
            points[matched_card] += 1
    return points
