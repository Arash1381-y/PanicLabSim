from __future__ import annotations

from pathlib import Path
import re
import warnings
from typing import Sequence

from card import (
    AmoebaCard,
    AmoebaColor,
    Card,
    Configuration,
    EvolutionCard,
    Eye,
    LabCard,
    LabColor,
    Pattern,
    VentCard,
)

LAB_COLOR_MAP = {"red": LabColor.RED, "green": LabColor.GREEN, "yellow": LabColor.YELLOW}
AMOEBA_COLOR_MAP = {"red": AmoebaColor.RED, "blue": AmoebaColor.BLUE}
PATTERN_MAP = {
    "strip": Pattern.STRIPED,
    "striped": Pattern.STRIPED,
    "dot": Pattern.DOTTY,
    "dotty": Pattern.DOTTY,
}
EYE_MAP = {
    "single": Eye.SINGLE,
    "1": Eye.SINGLE,
    "double": Eye.DOUBLE,
    "2": Eye.DOUBLE,
}


def parse_file(input_file_path: str | Path) -> list[Card]:
    """
    Parse an input file into card instances, skipping blank or comment lines.
    """
    path = Path(input_file_path)
    cards: list[Card] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            card = parse_line(raw_line, line_number)
            if card is not None:
                cards.append(card)
    return cards


def parse_line(line: str, line_number: int) -> Card | None:
    """
    Parse a single line. Returns None for blank/comment/invalid entries.
    """
    sanitized = line.split("#", 1)[0].strip()
    if not sanitized:
        return None

    parts = sanitized.split()
    card_type = parts[0].lower()
    payload = parts[1:]

    if card_type == "vent":
        return VentCard(line_number)

    if card_type == "lab":
        return _parse_lab(payload, line_number)

    if card_type == "amoeba":
        return _parse_amoeba(payload, line_number)

    if card_type == "evolution":
        return _parse_evolution(payload, line_number)

    warnings.warn(f"Unknown card type at line {line_number}: '{line.strip()}'")
    return None


def _parse_lab(tokens: Sequence[str], line_number: int) -> Card | None:
    if not tokens:
        warnings.warn(f"Lab definition missing color at line {line_number}")
        return None
    color = LAB_COLOR_MAP.get(tokens[0].lower())
    if color is None:
        warnings.warn(f"Unsupported lab color at line {line_number}: '{tokens[0]}'")
        return None
    return LabCard(color, line_number)


def _parse_amoeba(tokens: Sequence[str], line_number: int) -> Card | None:
    if len(tokens) < 3:
        warnings.warn(f"Amoeba definition incomplete at line {line_number}")
        return None

    color = AMOEBA_COLOR_MAP.get(tokens[0].lower())
    pattern = PATTERN_MAP.get(tokens[1].lower())
    eye = EYE_MAP.get(tokens[2].lower())

    if None in (color, pattern, eye):
        warnings.warn(f"Invalid amoeba specification at line {line_number}: '{tokens[:3]}'")
        return None

    return AmoebaCard(Configuration(color, pattern, eye), line_number)


def _parse_evolution(tokens: Sequence[str], line_number: int) -> Card | None:
    if not tokens:
        warnings.warn(f"Evolution definition missing payload at line {line_number}")
        return None

    feature_blob = " ".join(tokens).lower()
    feature_tokens = _tokenize_features(feature_blob)
    evolve_color = "color" in feature_tokens
    evolve_pattern = "pattern" in feature_tokens
    evolve_eye = "eye" in feature_tokens

    if not any((evolve_color, evolve_pattern, evolve_eye)):
        warnings.warn(f"Evolution card without modifiers at line {line_number}")
        return None

    return EvolutionCard(evolve_color, evolve_pattern, evolve_eye, line_number)


def _tokenize_features(blob: str) -> set[str]:
    """
    Normalize feature descriptors that may be separated by punctuation.
    """
    return {token for token in re.split(r"[+\s|/,_-]+", blob) if token}
