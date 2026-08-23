from app.services.training_load import (
    estimate_exercise_load,
    estimate_training_load,
)


EXERCISES = [
    {
        "name": "Rondo 3 vs 1",
        "task_type": "Rondo",
        "players": 4,
        "space": "5 x 5 metros",
        "time_description": "2 Series de 5'",
        "objective_1": "Apoyos",
        "objective_2": "Líneas de pase",
    },
    {
        "name": "Circuito Fuerza Explosiva",
        "task_type": "Circuito",
        "players": 10,
        "space": "Mediocampo",
        "time_description": "Trabajo 2' Descanso 30'' (5)",
        "objective_1": "Fuerza explosiva",
        "objective_2": "Coordinación",
    },
    {
        "name": "Juego de Posición Presión en campo contrario",
        "task_type": "Juego de Posición",
        "players": 12,
        "space": "40 x 20 metros",
        "time_description": "2 Series de 10'",
        "objective_1": "Presión",
        "objective_2": "Conservación de balón",
    },
    {
        "name": "Partido Condicionado 10 vs 10",
        "task_type": "Partido Condicionado",
        "players": 20,
        "space": "Campo entero",
        "time_description": "25'",
        "objective_1": "Juego real",
        "objective_2": "Conservación de balón",
    },
]


print("\n=== CARGA POR EJERCICIO ===\n")

for exercise in EXERCISES:
    result = estimate_exercise_load(**exercise)

    print(exercise["name"])
    print(f"  Score: {result['score']}/100")
    print(f"  Nivel: {result['level']}")
    print(f"  Trabajo: {result['work_minutes']} min")
    print(f"  Densidad: {result['density']}")
    print(f"  m²/jugador: {result['area_per_player']}")
    print(f"  Componentes: {result['components']}")

    print("  Motivos:")
    for reason in result["reasons"]:
        print(f"   - {reason}")

    print()


print("\n=== ENTRENAMIENTO COMPLETO ===\n")

training_result = estimate_training_load(
    exercises=EXERCISES,
    training_duration_minutes=80,
)

print(f"Carga estimada: {training_result['score']}/100")
print(f"Nivel: {training_result['level']}")
print(f"Trabajo efectivo: {training_result['total_work_minutes']} min")

print("\n¿Por qué?")

for reason in training_result["reasons"]:
    print(f" - {reason}")