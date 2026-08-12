#!/usr/bin/env python3
"""Genera las cinco animaciones tácticas del piloto como WebM/VP9."""

from __future__ import annotations

import argparse
import math
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 960
HEIGHT = 540
FPS = 24
DURATION = 8
FRAMES = FPS * DURATION

BLUE = (42, 111, 168)
LIGHT_BLUE = (95, 178, 211)
RED = (218, 71, 62)
LIGHT_RED = (238, 128, 108)
AMBER = (246, 174, 66)
TEAL = (32, 151, 138)
WHITE = (244, 247, 249)
INK = (14, 32, 39)

Point = tuple[float, float]
Keyframe = tuple[float, float, float]


@dataclass(frozen=True)
class Player:
    color: tuple[int, int, int]
    path: tuple[Keyframe, ...]
    radius: int = 13


@dataclass(frozen=True)
class ExerciseSpec:
    exercise_id: int
    name: str
    objective: str
    players: tuple[Player, ...]
    ball_path: tuple[Keyframe, ...]
    layout: Callable[[ImageDraw.ImageDraw], None]


def kf(*points: tuple[float, float, float]) -> tuple[Keyframe, ...]:
    return points


def static(x: float, y: float) -> tuple[Keyframe, ...]:
    return kf((0.0, x, y), (1.0, x, y))


def ease(value: float) -> float:
    return value * value * (3 - 2 * value)


def position(path: Sequence[Keyframe], phase: float) -> tuple[Point, Point, Point]:
    for index in range(len(path) - 1):
        start = path[index]
        end = path[index + 1]
        if start[0] <= phase < end[0]:
            progress = ease((phase - start[0]) / (end[0] - start[0]))
            current = (
                start[1] + (end[1] - start[1]) * progress,
                start[2] + (end[2] - start[2]) * progress,
            )
            return current, (start[1], start[2]), (end[1], end[2])
    final = path[-1]
    return (final[1], final[2]), (final[1], final[2]), (final[1], final[2])


def xy(point: Point) -> tuple[int, int]:
    return round(point[0] * WIDTH), round(point[1] * HEIGHT)


def pitch() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), (42, 111, 70))
    draw = ImageDraw.Draw(image)
    stripe_width = WIDTH // 10
    for stripe in range(10):
        color = (48, 125, 78) if stripe % 2 == 0 else (42, 114, 71)
        draw.rectangle((stripe * stripe_width, 0, (stripe + 1) * stripe_width, HEIGHT), fill=color)
    draw.rounded_rectangle((28, 26, WIDTH - 28, HEIGHT - 26), radius=7, outline=(225, 241, 221), width=3)
    draw.line((WIDTH // 2, 26, WIDTH // 2, HEIGHT - 26), fill=(225, 241, 221), width=2)
    draw.ellipse((WIDTH // 2 - 76, HEIGHT // 2 - 76, WIDTH // 2 + 76, HEIGHT // 2 + 76), outline=(225, 241, 221), width=2)
    draw.ellipse((WIDTH // 2 - 3, HEIGHT // 2 - 3, WIDTH // 2 + 3, HEIGHT // 2 + 3), fill=(225, 241, 221))
    return image


def line(draw: ImageDraw.ImageDraw, points: Iterable[Point], *, fill=WHITE, width=3) -> None:
    draw.line([xy(point) for point in points], fill=fill, width=width, joint="curve")


def cone(draw: ImageDraw.ImageDraw, point: Point, color=AMBER) -> None:
    x, y = xy(point)
    # El cono se representa como material bajo y no como un triángulo que
    # pueda confundirse visualmente con una bandera o marcador direccional.
    draw.rounded_rectangle((x - 7, y - 5, x + 7, y + 5), radius=3, fill=color, outline=INK, width=2)
    draw.line((x - 9, y + 6, x + 9, y + 6), fill=INK, width=2)


def goal(draw: ImageDraw.ImageDraw, center: Point, horizontal: bool = True) -> None:
    x, y = xy(center)
    if horizontal:
        draw.rectangle((x - 48, y - 7, x + 48, y + 7), fill=(234, 241, 236), outline=INK, width=2)
        for offset in range(-40, 41, 10):
            draw.line((x + offset, y - 6, x + offset, y + 6), fill=(118, 139, 128), width=1)
    else:
        draw.rectangle((x - 7, y - 35, x + 7, y + 35), fill=(234, 241, 236), outline=INK, width=2)
        for offset in range(-28, 29, 9):
            draw.line((x - 6, y + offset, x + 6, y + offset), fill=(118, 139, 128), width=1)


def training_area(draw: ImageDraw.ImageDraw, left: float, top: float, right: float, bottom: float) -> None:
    draw.rounded_rectangle((*xy((left, top)), *xy((right, bottom))), radius=5, outline=(10, 37, 32), width=3)
    for corner in ((left, top), (right, top), (right, bottom), (left, bottom)):
        cone(draw, corner)


def draw_dashed_arrow(draw: ImageDraw.ImageDraw, start: Point, end: Point, color: tuple[int, int, int, int]) -> None:
    sx, sy = xy(start)
    ex, ey = xy(end)
    dx, dy = ex - sx, ey - sy
    distance = math.hypot(dx, dy)
    if distance < 5:
        return
    ux, uy = dx / distance, dy / distance
    cursor = 4.0
    while cursor < distance - 18:
        finish = min(cursor + 10, distance - 18)
        draw.line((sx + ux * cursor, sy + uy * cursor, sx + ux * finish, sy + uy * finish), fill=color, width=4)
        cursor += 17


def draw_player(draw: ImageDraw.ImageDraw, point: Point, color: tuple[int, int, int], radius: int) -> None:
    x, y = xy(point)
    draw.ellipse((x - radius + 2, y - radius + 4, x + radius + 2, y + radius + 4), fill=(11, 31, 28, 90))
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline=WHITE, width=3)
    draw.ellipse((x - radius + 4, y - radius + 3, x - radius + 8, y - radius + 7), fill=(255, 255, 255, 130))


def draw_ball(draw: ImageDraw.ImageDraw, point: Point) -> None:
    x, y = xy(point)
    radius = 8
    draw.ellipse((x - radius + 2, y - radius + 3, x + radius + 2, y + radius + 3), fill=(8, 27, 25, 100))
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=WHITE, outline=INK, width=2)
    draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=INK)


def hexagon_layout(draw: ImageDraw.ImageDraw) -> None:
    vertices = ((0.23, 0.50), (0.34, 0.23), (0.66, 0.23), (0.77, 0.50), (0.66, 0.77), (0.34, 0.77), (0.23, 0.50))
    line(draw, vertices, fill=(13, 46, 39), width=4)
    for vertex in vertices[:-1]:
        cone(draw, vertex)


def amplitude_layout(draw: ImageDraw.ImageDraw) -> None:
    goal(draw, (0.50, 0.055))
    draw.rectangle((*xy((0.31, 0.05)), *xy((0.69, 0.30))), outline=WHITE, width=2)
    draw.line((*xy((0.25, 0.08)), *xy((0.25, 0.90))), fill=(239, 202, 83), width=2)
    draw.line((*xy((0.75, 0.08)), *xy((0.75, 0.90))), fill=(239, 202, 83), width=2)


def finishing_layout(draw: ImageDraw.ImageDraw) -> None:
    goal(draw, (0.50, 0.055))
    draw.rectangle((*xy((0.32, 0.05)), *xy((0.68, 0.31))), outline=WHITE, width=2)
    route = ((0.14, 0.20), (0.15, 0.39), (0.24, 0.70), (0.47, 0.69), (0.47, 0.50), (0.84, 0.20), (0.52, 0.30))
    for point in route:
        cone(draw, point, RED)
    for start, end in zip(route, route[1:]):
        draw_dashed_arrow(draw, start, end, (13, 38, 34, 135))


def pressing_layout(draw: ImageDraw.ImageDraw) -> None:
    training_area(draw, 0.08, 0.14, 0.92, 0.86)
    draw.line((*xy((0.50, 0.14)), *xy((0.50, 0.86))), fill=(10, 37, 32), width=3)


def transition_layout(draw: ImageDraw.ImageDraw) -> None:
    training_area(draw, 0.23, 0.16, 0.77, 0.84)
    draw.line((*xy((0.50, 0.16)), *xy((0.50, 0.84))), fill=(10, 37, 32), width=3)
    for y in (0.29, 0.50, 0.71):
        goal(draw, (0.225, y), horizontal=False)
        goal(draw, (0.775, y), horizontal=False)


def specs() -> dict[int, ExerciseSpec]:
    possession_players = (
        Player(BLUE, kf((0, .37, .35), (.5, .40, .32), (1, .37, .35))),
        Player(BLUE, kf((0, .50, .34), (.5, .53, .37), (1, .50, .34))),
        Player(BLUE, kf((0, .61, .48), (.5, .64, .50), (1, .61, .48))),
        Player(BLUE, kf((0, .54, .65), (.5, .50, .63), (1, .54, .65))),
        Player(BLUE, kf((0, .39, .61), (.5, .36, .57), (1, .39, .61))),
        Player(RED, kf((0, .43, .46), (.5, .47, .43), (1, .43, .46))),
        Player(RED, kf((0, .56, .52), (.5, .58, .56), (1, .56, .52))),
        Player(RED, kf((0, .48, .57), (.5, .45, .58), (1, .48, .57))),
        Player(LIGHT_BLUE, static(.33, .22)), Player(LIGHT_BLUE, static(.77, .50)), Player(LIGHT_BLUE, static(.34, .78)),
        Player(LIGHT_RED, static(.66, .22)), Player(LIGHT_RED, static(.66, .78)), Player(LIGHT_RED, static(.23, .50)),
    )
    amplitude_players = (
        Player(BLUE, static(.50, .84)),
        Player(BLUE, kf((0, .34, .72), (.5, .30, .68), (1, .34, .72))),
        Player(BLUE, kf((0, .66, .72), (.5, .70, .68), (1, .66, .72))),
        Player(BLUE, kf((0, .18, .54), (.5, .12, .46), (1, .18, .54))),
        Player(BLUE, kf((0, .82, .54), (.5, .88, .46), (1, .82, .54))),
        Player(BLUE, kf((0, .50, .48), (.5, .54, .39), (1, .50, .48))),
        Player(RED, static(.40, .52)), Player(RED, static(.60, .52)), Player(RED, static(.34, .35)),
        Player(RED, static(.66, .35)), Player(RED, static(.47, .27)), Player(RED, static(.53, .27)),
        Player(AMBER, static(.50, .10), radius=14),
    )
    finishing_players = (
        Player(RED, static(.14, .20)), Player(RED, static(.15, .39)), Player(RED, static(.24, .70)),
        Player(RED, static(.47, .69)), Player(RED, static(.47, .50)), Player(RED, static(.84, .20)),
        Player(RED, kf((0, .50, .33), (.65, .55, .22), (1, .50, .33))),
        Player(LIGHT_BLUE, static(.50, .095), radius=15),
    )
    pressing_players = (
        Player(BLUE, kf((0, .16, .27), (.55, .21, .30), (.78, .59, .29), (1, .59, .29))),
        Player(BLUE, kf((0, .38, .30), (.55, .34, .35), (.78, .68, .36), (1, .68, .36))),
        Player(BLUE, kf((0, .18, .67), (.55, .23, .63), (.78, .60, .61), (1, .60, .61))),
        Player(BLUE, kf((0, .40, .66), (.55, .36, .61), (.78, .73, .67), (1, .73, .67))),
        Player(RED, static(.27, .37)), Player(RED, static(.40, .49)), Player(RED, static(.28, .56)), Player(RED, static(.12, .48)),
        Player(TEAL, static(.62, .27)), Player(TEAL, static(.83, .37)), Player(TEAL, static(.65, .63)), Player(TEAL, static(.84, .68)),
    )
    transition_players = (
        Player(BLUE, kf((0, .31, .29), (.45, .35, .33), (1, .31, .29))),
        Player(BLUE, kf((0, .31, .50), (.45, .36, .48), (1, .31, .50))),
        Player(BLUE, kf((0, .32, .70), (.45, .37, .65), (1, .32, .70))),
        Player(BLUE, kf((0, .58, .31), (.7, .61, .34), (1, .58, .31))),
        Player(BLUE, kf((0, .62, .67), (.7, .59, .63), (1, .62, .67))),
        Player(RED, kf((0, .39, .28), (.45, .42, .38), (1, .39, .28))),
        Player(RED, kf((0, .40, .50), (.45, .43, .49), (1, .40, .50))),
        Player(RED, kf((0, .40, .72), (.45, .43, .62), (1, .40, .72))),
        Player(RED, kf((0, .61, .38), (.72, .66, .36), (1, .61, .38))),
        Player(RED, kf((0, .61, .64), (.72, .68, .56), (1, .61, .64))),
        Player(AMBER, static(.50, .12)), Player(AMBER, static(.50, .88)),
    )
    return {
        73: ExerciseSpec(73, "Juego de Posesión en Hexágono", "Conservación de balón · Cambio de orientación", possession_players,
                         kf((0, .37, .35), (.09, .33, .22), (.18, .50, .34), (.27, .61, .48),
                            (.36, .77, .50), (.45, .54, .65), (.54, .39, .61), (.63, .34, .78),
                            (.72, .37, .35), (.81, .61, .48), (.90, .50, .34), (1, .50, .34)), hexagon_layout),
        34: ExerciseSpec(34, "Ataque/Defensa Juego real", "Conservación de balón · Amplitud", amplitude_players,
                         kf((0, .50, .84), (.18, .34, .72), (.35, .18, .54), (.55, .50, .48), (.72, .82, .54), (.90, .50, .23), (1, .50, .23)), amplitude_layout),
        60: ExerciseSpec(60, "Acción combinada Centro lateral", "Finalización · Técnica", finishing_players,
                         kf((0, .14, .20), (.08, .15, .39), (.16, .14, .20), (.24, .15, .39),
                            (.34, .24, .70), (.42, .15, .39), (.52, .47, .69), (.60, .24, .70),
                            (.68, .47, .50), (.76, .47, .69), (.87, .84, .20), (.96, .52, .30),
                            (1, .50, .055)), finishing_layout),
        72: ExerciseSpec(72, "Juego de Posesión Presión en campo contrario", "Presión · Sacar de zona", pressing_players,
                         kf((0, .16, .27), (.10, .38, .30), (.20, .40, .66), (.30, .18, .67),
                            (.40, .16, .27), (.50, .38, .30), (.62, .62, .27), (.75, .83, .37),
                            (.88, .65, .63), (1, .65, .63)), pressing_layout),
        89: ExerciseSpec(89, "Juego de Posición 5 vs 5 + 2 Comodines", "Organización ofensiva · Transiciones", transition_players,
                         kf((0, .31, .29), (.18, .50, .12), (.34, .31, .50), (.47, .40, .50),
                            (.58, .61, .38), (.72, .68, .56), (.88, .77, .50), (1, .77, .50)), transition_layout),
    }


def render_frame(spec: ExerciseSpec, frame_number: int) -> Image.Image:
    phase = frame_number / FRAMES
    image = pitch().convert("RGBA")
    layout_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    spec.layout(ImageDraw.Draw(layout_layer))
    image.alpha_composite(layout_layer)

    movement_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    movement_draw = ImageDraw.Draw(movement_layer)
    ball_state = position(spec.ball_path, phase) if spec.ball_path else None
    if ball_state:
        _, segment_start, segment_end = ball_state
        draw_dashed_arrow(movement_draw, segment_start, segment_end, (250, 244, 189, 205))
    for player in spec.players:
        _, start, end = position(player.path, phase)
        if start != end:
            draw_dashed_arrow(movement_draw, start, end, (*player.color, 80))
    image.alpha_composite(movement_layer)

    tokens_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    tokens_draw = ImageDraw.Draw(tokens_layer)
    for player in spec.players:
        current, _, _ = position(player.path, phase)
        draw_player(tokens_draw, current, player.color, player.radius)
    if ball_state:
        draw_ball(tokens_draw, ball_state[0])
    image.alpha_composite(tokens_layer)
    return image.convert("RGB")


def validate_database(database: Path, selected: Sequence[ExerciseSpec]) -> None:
    with sqlite3.connect(database) as connection:
        for spec in selected:
            row = connection.execute("SELECT nombre FROM ejercicios WHERE id=?", (spec.exercise_id,)).fetchone()
            if row != (spec.name,):
                raise RuntimeError(f"El ejercicio {spec.exercise_id} no coincide con la ficha esperada: {row!r}")


def encode(spec: ExerciseSpec, destination: Path, ffmpeg: str) -> None:
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "0", "-deadline", "good", "-cpu-used", "2",
        "-row-mt", "1", "-pix_fmt", "yuv420p", "-metadata", f"title={spec.name}", str(destination),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdin is not None
    for frame_number in range(FRAMES):
        process.stdin.write(render_frame(spec, frame_number).tobytes())
    process.stdin.close()
    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    if process.wait() != 0:
        raise RuntimeError(f"FFmpeg no pudo generar {destination}: {stderr}")


def encode_with_opencv(spec: ExerciseSpec, destination: Path) -> None:
    """Fallback local cuando no hay CLI de FFmpeg, usando su backend en OpenCV."""
    import cv2
    import numpy as np

    writer = cv2.VideoWriter(
        str(destination),
        cv2.VideoWriter_fourcc(*"VP90"),
        FPS,
        (WIDTH, HEIGHT),
    )
    if not writer.isOpened():
        raise RuntimeError("OpenCV no dispone de un codificador WebM/VP9")
    try:
        for frame_number in range(FRAMES):
            rgb = np.asarray(render_frame(spec, frame_number))
            writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    finally:
        writer.release()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exercise-id", type=int, action="append", choices=sorted(specs()), help="ID a generar; se puede repetir")
    parser.add_argument("--database", type=Path, default=ROOT / "database" / "futbol_entrenamiento.sqlite")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "animations")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--encoder", choices=("auto", "ffmpeg", "opencv"), default="auto")
    args = parser.parse_args()

    catalog = specs()
    selected_ids = args.exercise_id or list(catalog)
    selected = [catalog[exercise_id] for exercise_id in selected_ids]
    validate_database(args.database.resolve(), selected)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for spec in selected:
        destination_dir = args.output_dir / str(spec.exercise_id)
        destination_dir.mkdir(parents=True, exist_ok=True)
        cover = destination_dir / "portada.webp"
        destination = destination_dir / "animacion.webm"
        render_frame(spec, 0).save(cover, format="WEBP", lossless=True, method=6)
        print(f"Generando {spec.exercise_id}/portada.webp y animacion.webm: {spec.name}", flush=True)
        use_ffmpeg = args.encoder == "ffmpeg" or (args.encoder == "auto" and shutil.which(args.ffmpeg))
        if use_ffmpeg:
            encode(spec, destination, args.ffmpeg)
        else:
            encode_with_opencv(spec, destination)


if __name__ == "__main__":
    main()
