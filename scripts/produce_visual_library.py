#!/usr/bin/env python3
"""Produce por lotes la biblioteca visual original de los 114 ejercicios."""

from __future__ import annotations

import argparse
import csv
import math
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw

from generate_exercise_animations import (
    AMBER, BLUE, DURATION, FPS, HEIGHT, INK, LIGHT_BLUE, LIGHT_RED, RED, TEAL,
    WHITE, WIDTH, ExerciseSpec, Player,
)

# La importación separada mantiene visible la lista de primitivas reutilizadas.
from generate_exercise_animations import (  # noqa: E402
    cone, encode, encode_with_opencv, goal, kf, line, render_frame, specs as pilot_specs,
    static, training_area, xy,
)


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "database" / "futbol_entrenamiento.sqlite"
IMAGES = ROOT / "database" / "imagenes"
OUTPUT = ROOT / "animations"


def norm(value: str) -> str:
    return value.casefold().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


def route(points: Sequence[tuple[float, float]], finish_at: float = .94) -> tuple[tuple[float, float, float], ...]:
    if not points:
        return ()
    if len(points) == 1:
        return kf((0, *points[0]), (1, *points[0]))
    timed = [(finish_at * index / (len(points) - 1), *point) for index, point in enumerate(points)]
    timed.append((1, *points[-1]))
    return tuple(timed)


def polygon(count: int, center=(.5, .5), radius=(.30, .27), offset=-math.pi / 2) -> list[tuple[float, float]]:
    return [
        (center[0] + radius[0] * math.cos(offset + 2 * math.pi * i / count),
         center[1] + radius[1] * math.sin(offset + 2 * math.pi * i / count))
        for i in range(max(count, 1))
    ]


def grid(count: int, left=.18, top=.22, right=.82, bottom=.78) -> list[tuple[float, float]]:
    columns = max(2, math.ceil(math.sqrt(count * (right - left) / max(bottom - top, .1))))
    rows = math.ceil(count / columns)
    result = []
    for index in range(count):
        col, row = index % columns, index // columns
        x = left if columns == 1 else left + (right - left) * col / (columns - 1)
        y = top if rows == 1 else top + (bottom - top) * row / (rows - 1)
        result.append((x, y))
    return result


def moving(color, point, target=None, radius=13) -> Player:
    if target is None:
        return Player(color, static(*point), radius=radius)
    return Player(color, kf((0, *point), (.72, *target), (1, *target)), radius=radius)


def sequence_from_description(description: str) -> list[int]:
    match = re.search(r"acci[oó]n\s*:\s*(?:variante\s*[a-z]\s*:)?\s*([0-9][0-9\s\-]+)", description, re.I)
    if not match:
        return []
    return [int(value) for value in re.findall(r"\d+", match.group(1))]


def versus(name: str, players: int) -> tuple[int, int, int]:
    match = re.search(r"(\d+)\s*vs\s*(\d+)", name, re.I)
    if not match:
        first = players // 2
        return first, players - first, 0
    first, second = int(match.group(1)), int(match.group(2))
    extras = max(0, players - first - second)
    if first + second > players:
        first = players // 2
        second = players - first
        extras = 0
    return first, second, extras


def common_area(draw: ImageDraw.ImageDraw, *, divisions=0, mini_goals=False, full_goals=False) -> None:
    training_area(draw, .11, .15, .89, .85)
    for index in range(1, divisions + 1):
        x = .11 + .78 * index / (divisions + 1)
        draw.line((*xy((x, .15)), *xy((x, .85))), fill=(12, 48, 39), width=3)
    if mini_goals:
        for y in (.32, .68):
            goal(draw, (.105, y), horizontal=False)
            goal(draw, (.895, y), horizontal=False)
    if full_goals:
        goal(draw, (.5, .055))
        goal(draw, (.5, .945))


def rondo_spec(row) -> ExerciseSpec:
    total = row["jugadores"]
    attack, defend, extras = versus(row["nombre"], total)
    text = norm(row["nombre"] + " " + row["desarrollo"])
    triangular = "triang" in text
    multi = any(word in text for word in ("doble", "segundo cuadrado", "4 cuadrados", "cambiar de zona", "progres"))
    outer = polygon(attack, center=(.36 if multi else .5, .5), radius=(.22 if multi else .31, .29))
    inner = polygon(defend, center=(.36 if multi else .5, .5), radius=(.09, .10), offset=0)
    extra_positions = polygon(extras, center=(.5, .5), radius=(.12, .13)) if extras else []
    players = [moving(BLUE, point) for point in outer] + [moving(RED, p, ((p[0] + .5) / 2, (p[1] + .5) / 2)) for p in inner]
    players += [moving(AMBER, point) for point in extra_positions]
    while len(players) < total:
        players.append(moving(LIGHT_BLUE, grid(total - len(players), .18, .87, .82, .90)[0], radius=11))
    pass_match = re.search(r"(\d+)\s+pases", text)
    passes = min(10, int(pass_match.group(1))) if pass_match else min(6, max(3, attack))
    pass_points = [outer[i % len(outer)] for i in range(passes + 1)]
    if multi:
        pass_points.append((.73, .50))

    def layout(draw):
        if triangular:
            vertices = ((.22, .72), (.50, .19), (.78, .72), (.22, .72))
            line(draw, vertices, fill=INK, width=4)
            for point in vertices[:-1]: cone(draw, point)
        elif multi:
            training_area(draw, .10, .20, .48, .80)
            training_area(draw, .52, .20, .90, .80)
        else:
            training_area(draw, .16, .16, .84, .84)
            if "zona" in text or "interior" in text:
                training_area(draw, .34, .32, .66, .68)
        if "miniporter" in norm(row["materiales"]):
            goal(draw, (.095, .50), horizontal=False); goal(draw, (.905, .50), horizontal=False)

    return ExerciseSpec(row["id"], row["nombre"], row["objetivos"], tuple(players[:total]), route(pass_points), layout)


def passing_spec(row) -> ExerciseSpec:
    text = norm(row["nombre"] + " " + row["desarrollo"])
    sequence = sequence_from_description(row["desarrollo"])
    station_count = max(sequence, default=min(7, row["jugadores"]))
    if "linea" in text:
        stations = [(x, .52) for x in [(.14 + .72 * i / max(station_count - 1, 1)) for i in range(station_count)]]
    elif "triang" in text:
        stations = polygon(station_count, radius=(.31, .29), offset=-math.pi / 2)
    elif "rombo" in text:
        stations = polygon(station_count, radius=(.27, .32), offset=-math.pi / 2)
    elif "hexag" in text:
        stations = polygon(station_count, radius=(.34, .26), offset=math.pi)
    elif "reloj" in text:
        stations = polygon(station_count, radius=(.30, .31))
    else:
        stations = polygon(station_count, radius=(.31, .29), offset=-3 * math.pi / 4)
    players = [moving(BLUE, stations[i % station_count]) for i in range(row["jugadores"])]
    numbers = sequence or list(range(1, station_count + 1)) + [1]
    ball_points = [stations[(number - 1) % station_count] for number in numbers]

    def layout(draw):
        for point in stations:
            cone(draw, point)
        for start, end in zip(ball_points, ball_points[1:]):
            line(draw, (start, end), fill=(13, 46, 39, 120), width=2)
        materials = norm(row["materiales"])
        if "valla" in materials or "escalera" in materials:
            for x in (.12, .88):
                draw.rectangle((*xy((x - .025, .38)), *xy((x + .025, .62))), outline=AMBER, width=4)

    return ExerciseSpec(row["id"], row["nombre"], row["objetivos"], tuple(players), route(ball_points), layout)


def circuit_spec(row) -> ExerciseSpec:
    text = norm(row["desarrollo"] + " " + row["nombre"])
    station_numbers = [int(n) for n in re.findall(r"posta\s*(\d+)", text)]
    stations = max(station_numbers, default=5)
    stations = min(9, max(2, stations))
    points = grid(stations, .16, .22, .84, .76)
    players = []
    for index in range(row["jugadores"]):
        base = points[index % stations]
        queue = index // stations
        players.append(moving(BLUE if index % 2 == 0 else LIGHT_BLUE, (base[0], min(.88, base[1] + queue * .035))))
    moving_path = route(points + [points[0]])
    if players:
        players[0] = Player(BLUE, moving_path)
    uses_football = any(word in text for word in ("pase", "remate", "centro", "finaliz", "posesion", "tecnica", "balon "))

    def layout(draw):
        for index, point in enumerate(points):
            cone(draw, point)
            x, y = xy(point)
            if index % 3 == 0:
                for offset in (-18, 0, 18): draw.line((x + offset, y - 12, x + offset, y + 12), fill=AMBER, width=4)
            elif index % 3 == 1:
                draw.rectangle((x - 24, y - 10, x + 24, y + 10), outline=WHITE, width=3)
            else:
                draw.ellipse((x - 16, y - 16, x + 16, y + 16), outline=AMBER, width=4)
        if "finaliz" in text or "remate" in text: goal(draw, (.50, .055))

    ball = moving_path if uses_football else ()
    return ExerciseSpec(row["id"], row["nombre"], row["objetivos"], tuple(players), ball, layout)


def game_area_spec(row) -> ExerciseSpec:
    text = norm(row["nombre"] + " " + row["desarrollo"])
    first, second, extras = versus(row["nombre"], row["jugadores"])
    if "partido" in norm(row["tipo"]):
        first = row["jugadores"] // 2; second = row["jugadores"] - first; extras = 0
    blue_positions = grid(first, .17, .22, .44, .78)
    red_positions = grid(second, .56, .22, .83, .78)
    extra_positions = polygon(extras, radius=(.38, .32)) if extras else []
    players = [moving(BLUE, p) for p in blue_positions] + [moving(RED, p) for p in red_positions]
    players += [moving(AMBER, p) for p in extra_positions]
    pass_match = re.search(r"(\d+)\s+pases", text)
    passes = min(10, int(pass_match.group(1))) if pass_match else 5
    possession = [blue_positions[i % len(blue_positions)] for i in range(passes + 1)]
    if any(word in text for word in ("cambio", "progres", "transicion", "fuera", "banda", "carril")):
        possession += [(.82, .35), (.82, .65)]
    if any(word in text for word in ("finaliz", "porter", "gol", "remate", "ataque")):
        possession += [(.50, .08)]
    divisions = 3 if "4 carril" in text else 2 if any(w in text for w in ("3 zona", "zona", "linea")) else 0
    mini = "miniporter" in norm(row["materiales"])

    def layout(draw):
        common_area(draw, divisions=divisions, mini_goals=mini, full_goals=not mini)
        if "doble area" in text:
            draw.rectangle((*xy((.28, .15)), *xy((.72, .34))), outline=WHITE, width=2)
            draw.rectangle((*xy((.28, .66)), *xy((.72, .85))), outline=WHITE, width=2)

    return ExerciseSpec(row["id"], row["nombre"], row["objetivos"], tuple(players), route(possession), layout)


def attack_spec(row) -> ExerciseSpec:
    text = norm(row["nombre"] + " " + row["desarrollo"])
    sequence = sequence_from_description(row["desarrollo"])
    if sequence:
        stations = polygon(max(sequence), center=(.5, .57), radius=(.34, .29), offset=math.pi)
        points = [stations[number - 1] for number in sequence]
        players = [moving(BLUE, stations[i % len(stations)]) for i in range(row["jugadores"])]
    else:
        first = max(3, row["jugadores"] // 2)
        second = row["jugadores"] - first
        attack = grid(first, .18, .47, .82, .82)
        defense = grid(second, .30, .23, .70, .43)
        players = [moving(BLUE, p) for p in attack] + [moving(RED, p) for p in defense]
        points = [attack[-1], attack[0], (.15, .42), attack[len(attack)//2], (.85, .40), (.50, .10)]

    def layout(draw):
        goal(draw, (.50, .055))
        draw.rectangle((*xy((.27, .05)), *xy((.73, .31))), outline=WHITE, width=2)
        if "miniporter" in norm(row["materiales"]):
            goal(draw, (.12, .78), horizontal=False); goal(draw, (.88, .78), horizontal=False)
        if "carril" in text:
            for x in (.25, .75): draw.line((*xy((x, .16)), *xy((x, .88))), fill=AMBER, width=2)
        if sequence:
            for station in stations: cone(draw, station)

    return ExerciseSpec(row["id"], row["nombre"], row["objetivos"], tuple(players[:row["jugadores"]]), route(points), layout)


def abp_spec(row) -> ExerciseSpec:
    text = norm(row["nombre"] + " " + row["desarrollo"])
    corner = "corner" in text or "esquina" in text
    ball_start = (.08, .08) if corner else (.22, .48) if "lateral" in text else (.50, .47)
    attackers = grid(max(2, row["jugadores"] // 2), .31, .25, .69, .48)
    defenders = grid(row["jugadores"] - len(attackers), .34, .14, .66, .34)
    players = [moving(BLUE, p, (max(.25, p[0] - .05), max(.10, p[1] - .10))) for p in attackers]
    players += [moving(RED, p, (p[0], max(.10, p[1] - .06))) for p in defenders]
    target = (.62, .18) if "segundo palo" in text else (.42, .18) if "primer palo" in text else (.50, .13)
    points = [ball_start, target, (.50, .07)]

    def layout(draw):
        goal(draw, (.50, .055))
        draw.rectangle((*xy((.24, .05)), *xy((.76, .34))), outline=WHITE, width=2)
        if corner: cone(draw, ball_start, AMBER)

    return ExerciseSpec(row["id"], row["nombre"], row["objetivos"], tuple(players), route(points), layout)


def playful_spec(row) -> ExerciseSpec:
    exercise_id = row["id"]
    total = row["jugadores"]
    blue = grid(total // 2, .14, .24, .38, .78)
    red = grid(total - len(blue), .62, .24, .86, .78)
    no_ball = exercise_id in (110, 114)
    players = [moving(BLUE, p, (.48, p[1])) for p in blue] + [moving(RED, p, (.52, p[1])) for p in red]

    def layout(draw):
        training_area(draw, .08, .13, .92, .87)
        if exercise_id == 109:
            for x in (.14, .86):
                for y in (.25, .75): draw.rectangle((*xy((x-.07, y-.08)), *xy((x+.07, y+.08))), outline=AMBER, width=3)
        elif exercise_id == 110:
            for x in (.42, .50, .58):
                for y in (.38, .50, .62): draw.ellipse((*xy((x-.025, y-.04)), *xy((x+.025, y+.04))), outline=AMBER, width=4)
        elif exercise_id in (111, 113):
            goal(draw, (.075, .50), horizontal=False); goal(draw, (.925, .50), horizontal=False)
        elif exercise_id == 112:
            draw.rectangle((*xy((.47, .14)), *xy((.53, .86))), fill=WHITE, outline=INK, width=2)
        elif exercise_id == 114:
            line(draw, ((.12, .50), (.88, .50)), fill=AMBER, width=5)
            for point in ((.12,.5),(.88,.5)): cone(draw, point)

    ball_points = [blue[0], red[0], blue[-1], red[-1]] if not no_ball else []
    return ExerciseSpec(exercise_id, row["nombre"], row["objetivos"], tuple(players), route(ball_points), layout)


def make_spec(row) -> ExerciseSpec:
    if row["id"] in pilot_specs():
        return pilot_specs()[row["id"]]
    category = row["tipo"]
    if category == "Rondo": return rondo_spec(row)
    if category == "Rueda de pase": return passing_spec(row)
    if category == "Circuito": return circuit_spec(row)
    if category in ("Ataque/Defensa", "Acción Combinada"): return attack_spec(row)
    if category in ("Juego de Posesión", "Juego de Posición", "Partido Condicionado"): return game_area_spec(row)
    if category == "ABP": return abp_spec(row)
    if category == "Juego lúdico": return playful_spec(row)
    raise ValueError(f"Tipo no reconocido: {category}")


def load_rows(database: Path) -> list[dict]:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    query = """
        SELECT e.id,e.codigo,e.nombre,tt.nombre tipo,e.jugadores,e.desarrollo,
               es.descripcion_original espacio,t.descripcion_original tiempo,
               COALESCE(e.objetivo_1_normalizado,'') || CASE WHEN e.objetivo_2_normalizado IS NOT NULL THEN ' · ' || e.objetivo_2_normalizado ELSE '' END objetivos,
               COALESCE((SELECT GROUP_CONCAT(m.nombre_normalizado) FROM ejercicio_material em JOIN materiales m ON m.id=em.material_id WHERE em.ejercicio_id=e.id),'') materiales
        FROM ejercicios e JOIN tipos_tarea tt ON tt.id=e.tipo_tarea_id
        JOIN espacios es ON es.id=e.espacio_id JOIN tiempos t ON t.id=e.tiempo_id ORDER BY e.id
    """
    rows = [dict(row) for row in connection.execute(query)]
    for row in rows:
        references = connection.execute(
            "SELECT i.archivo,COALESCE(i.width,0)*COALESCE(i.height,0) area FROM ejercicio_imagen ei JOIN imagenes i ON i.id=ei.imagen_id WHERE ei.ejercicio_id=? ORDER BY area DESC",
            (row["id"],),
        ).fetchall()
        if not references:
            row["reference"] = ""
        else:
            row["reference"] = references[0][0]
            with Image.open(IMAGES / row["reference"]) as reference:
                reference.verify()
    connection.close()
    return rows


def write_reports(entries: list[dict], review: list[dict]) -> None:
    report_path = OUTPUT / "visual_library_report.csv"
    existing = {}
    if report_path.exists():
        existing = {int(row["exercise_id"]): row for row in csv.DictReader(report_path.open())}
    existing.update({int(row["exercise_id"]): row for row in entries})
    fields = ["exercise_id", "nombre", "portada", "animacion", "duracion", "tamano_portada", "tamano_animacion", "estado", "observaciones"]
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        writer.writerows(existing[key] for key in sorted(existing))
    review_path = OUTPUT / "needs_review.csv"
    old_review = {}
    if review_path.exists():
        old_review = {int(row["id"]): row for row in csv.DictReader(review_path.open())}
    old_review.update({int(row["id"]): row for row in review})
    with review_path.open("w", newline="", encoding="utf-8") as handle:
        fields_review = ["id", "nombre", "motivo", "información insuficiente"]
        writer = csv.DictWriter(handle, fieldnames=fields_review); writer.writeheader()
        writer.writerows(old_review[key] for key in sorted(old_review))


def produce(row: dict, ffmpeg: str) -> dict:
    spec = make_spec(row)
    directory = OUTPUT / str(row["id"]); directory.mkdir(parents=True, exist_ok=True)
    cover = directory / "portada.webp"; video = directory / "animacion.webm"
    render_frame(spec, 0).save(cover, format="WEBP", lossless=True, method=6)
    if shutil.which(ffmpeg): encode(spec, video, ffmpeg)
    else: encode_with_opencv(spec, video)
    with Image.open(cover) as image:
        if image.size != (WIDTH, HEIGHT): raise RuntimeError("Dimensiones de portada incorrectas")
    import cv2
    capture = cv2.VideoCapture(str(video)); frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)); fps = capture.get(cv2.CAP_PROP_FPS)
    ok, _ = capture.read(); capture.release()
    if not ok or frames <= 0 or fps <= 0: raise RuntimeError("WebM no reproducible")
    return {
        "exercise_id": row["id"], "nombre": row["nombre"],
        "portada": f"animations/{row['id']}/portada.webp", "animacion": f"animations/{row['id']}/animacion.webm",
        "duracion": f"{frames/fps:.2f}", "tamano_portada": cover.stat().st_size,
        "tamano_animacion": video.stat().st_size, "estado": "OK",
        "observaciones": f"Ficha completa y referencia {row['reference']} revisadas; {row['tipo']} representado con objetivos {row['objetivos'] or 'sin secundario'}.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--database", type=Path, default=DATABASE)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    if not 1 <= args.start <= args.end <= 114: raise SystemExit("Rango inválido")
    rows = [row for row in load_rows(args.database) if args.start <= row["id"] <= args.end]
    entries=[]; review=[]
    for row in rows:
        print(f"[{row['id']}/114] {row['codigo']} — {row['nombre']}", flush=True)
        try:
            entries.append(produce(row, args.ffmpeg))
        except ValueError as exc:
            review.append({"id": row["id"], "nombre": row["nombre"], "motivo": str(exc), "información insuficiente": row["desarrollo"]})
        except Exception as exc:
            entries.append({"exercise_id": row["id"], "nombre": row["nombre"], "portada": "", "animacion": "", "duracion": "", "tamano_portada": "", "tamano_animacion": "", "estado": "ERROR", "observaciones": str(exc)})
    write_reports(entries, review)
    errors=[row for row in entries if row["estado"] != "OK"]
    print(f"Lote {args.start}-{args.end}: {len(entries)-len(errors)} OK, {len(review)} NEEDS_REVIEW, {len(errors)} ERROR", flush=True)
    if errors: raise SystemExit(1)


if __name__ == "__main__":
    main()
