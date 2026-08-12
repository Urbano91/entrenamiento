"""Colores automáticos y estables para identificar entrenadores."""

from __future__ import annotations

import colorsys


def trainer_color(user_id: int) -> str:
    """Devuelve un color hexadecimal determinista sin persistir datos nuevos."""

    hue = (user_id * 0.618033988749895) % 1.0
    red, green, blue = colorsys.hls_to_rgb(hue, 0.42, 0.62)
    return f"#{round(red * 255):02X}{round(green * 255):02X}{round(blue * 255):02X}"
