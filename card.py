from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Direction(Enum):
    CLK_WISE = 0
    COUNTER_CLK_WISE = 1


class LabColor(Enum):
    RED = 0
    GREEN = 1
    YELLOW = 2


class AmoebaColor(Enum):
    RED = 0
    BLUE = 1


class Pattern(Enum):
    STRIPED = 0
    DOTTY = 1


class Eye(Enum):
    SINGLE = 0
    DOUBLE = 1


def _rotate_enum_value(member: Enum) -> Enum:
    """
    Return the next value in an Enum, wrapping around.
    This keeps the evolution logic future-proof if more values are added.
    """
    members = list(member.__class__)
    current_index = members.index(member)
    return members[(current_index + 1) % len(members)]


@dataclass(eq=True)
class Configuration:
    color: AmoebaColor
    pattern: Pattern
    eye: Eye

    def evolve(self, evolve_color: bool, evolve_pattern: bool, evolve_eye: bool) -> None:
        """
        Mutate the configuration on the requested axes.
        """
        if evolve_color:
            self.color = _rotate_enum_value(self.color)
        if evolve_pattern:
            self.pattern = _rotate_enum_value(self.pattern)
        if evolve_eye:
            self.eye = _rotate_enum_value(self.eye)

    def __str__(self) -> str:
        return f"({self.color.name}, {self.pattern.name}, {self.eye.name})"


class Card(ABC):
    """
    Base class for all cards that form the circular board.
    """

    def __init__(self, line_number: int):
        self.line_number = line_number
        self._clk_wise_neighbor: Optional["Card"] = None
        self._counter_clk_wise_neighbor: Optional["Card"] = None

    def set_neighbors(self, clk_wise_neighbor: "Card", counter_clk_wise_neighbor: "Card") -> None:
        self._clk_wise_neighbor = clk_wise_neighbor
        self._counter_clk_wise_neighbor = counter_clk_wise_neighbor

    def get_next(self, direction: Direction) -> "Card":
        neighbor = (
            self._clk_wise_neighbor
            if direction == Direction.CLK_WISE
            else self._counter_clk_wise_neighbor
        )
        if neighbor is None:
            raise RuntimeError(f"Neighbors not configured for card at line {self.line_number}")
        return neighbor

    @abstractmethod
    def is_matched(self, configuration: Configuration) -> bool:
        """
        Determine whether traversal stops on this card.
        """


class LabCard(Card):
    """
    Lab cards are only traversal entry points.
    """

    def __init__(self, lab_color: LabColor, line_number: int):
        super().__init__(line_number)
        self.lab_color = lab_color

    def __str__(self) -> str:
        return f"LabCard({self.lab_color.name})"

    def is_matched(self, configuration: Configuration) -> bool:
        return False


class AmoebaCard(Card):
    def __init__(self, configuration: Configuration, line_number: int):
        super().__init__(line_number)
        self.configuration = configuration

    def __str__(self) -> str:
        return f"AmoebaCard({self.configuration})"

    def is_matched(self, configuration: Configuration) -> bool:
        return self.configuration == configuration


class VentCard(Card):
    """
    A vent simply redirects flow to the next available card.
    """

    def is_matched(self, configuration: Configuration) -> bool:
        return False

    def __str__(self) -> str:
        return "VentCard"


class EvolutionCard(Card):
    """
    Mutates a configuration before traversal continues.
    """

    def __init__(self, evolve_color: bool, evolve_pattern: bool, evolve_eye: bool, line_number: int):
        super().__init__(line_number)
        self.evolve_color = evolve_color
        self.evolve_pattern = evolve_pattern
        self.evolve_eye = evolve_eye

    def is_matched(self, configuration: Configuration) -> bool:
        configuration.evolve(self.evolve_color, self.evolve_pattern, self.evolve_eye)
        return False

    def __str__(self) -> str:
        return (
            "EvolutionCard("
            f"color={self.evolve_color}, pattern={self.evolve_pattern}, eye={self.evolve_eye}"
            ")"
        )
