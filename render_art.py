from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Iterable, Sequence

from card import AmoebaCard, Card, EvolutionCard, LabCard, VentCard
from parser import parse_file
from simulator import DEFAULT_EXPERIMENTS, configure_neighbors, simulate

PIE_OUTPUT_DEFAULT = "results.png"
BOARD_OUTPUT_DEFAULT = "board.png"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# Rendering constants to keep spacing and sizing consistent
DEFAULT_CARD_SCALE = 1
CARD_RING_RADIUS = 1.2
CARD_TEXT_RADIUS = CARD_RING_RADIUS + 0.35
CARD_PIXEL_TARGET = 70  # Target size (px) each card should roughly occupy
CARD_TEXT_FONT_SIZE = 16
BACKGROUND_COLOR = "#C7C7C7"


def plot_pie_chart(points: dict[Card, int], output_path: str = PIE_OUTPUT_DEFAULT) -> bool:
    positive_cards = [
        (card, count)
        for card, count in points.items()
        if isinstance(card, AmoebaCard) and count > 0
    ]

    if not positive_cards:
        print("No data to plot.")
        return False

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        print(f"Matplotlib not available, skipping plot ({exc}).")
        return False

    labels = [f"Line {card.line_number}" for card, _ in positive_cards]
    sizes = [count for _, count in positive_cards]

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Pie plot saved to {output_path}")
    return True


def render_board_image(
    cards: Sequence[Card],
    points: dict[Card, int],
    output_path: str = BOARD_OUTPUT_DEFAULT,
    asset_dir: str | Path | None = None,
) -> bool:
    total_points = sum(points.values())
    if total_points == 0:
        print("No matches recorded; skipping board render.")
        return False
    try:
        import matplotlib.pyplot as plt
        from matplotlib.offsetbox import AnnotationBbox, OffsetImage
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        print(
            f"Matplotlib or Pillow not available, skipping board render ({exc}).")
        return False
    asset_root = Path(asset_dir) if asset_dir else ASSETS_DIR
    fig, ax = plt.subplots(figsize=(10, 10), facecolor=BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    for index, card in enumerate(cards):
        angle = (2 * math.pi * index / len(cards)) - math.pi / 2
        x = CARD_RING_RADIUS * math.cos(angle)
        y = CARD_RING_RADIUS * math.sin(angle)
        asset_path = _resolve_asset_path(card, asset_root)
        try:
            image = Image.open(asset_path).convert("RGBA")
        except (FileNotFoundError, OSError) as exc:
            print(f"Could not read asset {asset_path}: {exc}")
            continue

        # --- FIX: START ---
        # Calculate zoom based on the *original* image's max dimension
        # *before* rotating it. This ensures all cards are scaled uniformly.
        original_max_dim = max(image.size)
        if original_max_dim == 0:
            print(f"Skipping empty/corrupt asset: {asset_path}")
            continue
        zoom = CARD_PIXEL_TARGET / original_max_dim
        # --- FIX: END ---

        rotation_deg = math.degrees(angle) + 90
        rotated = image.rotate(
            rotation_deg, resample=Image.BICUBIC, expand=True)

        # The 'max_dim' and 'zoom' calculations were moved above the rotation.
        # Now, we just use the uniformly calculated 'zoom'.
        imagebox = OffsetImage(np.asarray(rotated), zoom=zoom)

        ab = AnnotationBbox(imagebox, (x, y), frameon=False)
        ax.add_artist(ab)
        text_x = CARD_TEXT_RADIUS * math.cos(angle)
        text_y = CARD_TEXT_RADIUS * math.sin(angle)
        if isinstance(card, AmoebaCard):
            win_percentage = (points[card] / total_points) * 100
            ax.text(
                text_x,
                text_y,
                f"{win_percentage:.1f}%",
                ha="center",
                va="center",
                fontsize=CARD_TEXT_FONT_SIZE,
                fontweight="bold",
                color="#333333",
            )
        elif isinstance(card, EvolutionCard):
            description = _describe_evolution(card)
            if description:
                ax.text(
                    text_x,
                    text_y,
                    description,
                    ha="center",
                    va="center",
                    fontsize=CARD_TEXT_FONT_SIZE,
                    fontweight="bold",
                    color="#333333",
                )
    limit = CARD_TEXT_RADIUS + 0.4
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.axis("off")
    fig.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    print(f"Board render saved to {output_path}")
    return True


def _resolve_asset_path(card: Card, asset_root: Path) -> Path:
    fallback = asset_root / "default.png"
    for candidate in _asset_candidates(card):
        asset_path = asset_root / candidate
        if asset_path.exists():
            return asset_path
    return fallback


def _asset_candidates(card: Card) -> Iterable[str]:
    if isinstance(card, LabCard):
        yield f"lab_{card.lab_color.name.lower()}.png"
    elif isinstance(card, VentCard):
        yield "vent.png"
    elif isinstance(card, AmoebaCard):
        color = card.configuration.color.name.lower()
        pattern = card.configuration.pattern.name.lower()
        eye = card.configuration.eye.name.lower()
        pattern_aliases = {pattern}
        if pattern == "striped":
            pattern_aliases.add("stripped")
        for pattern_alias in pattern_aliases:
            yield f"{color}_{pattern_alias}_{eye}.png"
    elif isinstance(card, EvolutionCard):
        if card.evolve_eye:
            yield "evolution_eye.png"
        elif card.evolve_color:
            yield "evolution_color.png"
        elif card.evolve_pattern:
            yield "evolution_pattern.png"
        else:
            yield "mutation.png"
    yield "default.png"


def _describe_evolution(card: EvolutionCard) -> str:
    axes = []
    if card.evolve_color:
        axes.append("Color")
    if card.evolve_pattern:
        axes.append("Pattern")
    if card.evolve_eye:
        axes.append("Eye")
    return " / ".join(axes)
