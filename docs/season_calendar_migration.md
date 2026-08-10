# Aislamiento de temporadas y calendarios

Migración aplicada: `20260810_03_isolated_season_calendars`.

## Reglas implantadas

- `entrenamientos.temporada_id`, `partidos.temporada_id` y
  `planificaciones_diarias.temporada_id` son obligatorios.
- Las consultas de calendario, agenda, entrenamientos, partidos, notas y
  documentos filtran por la temporada activa o por una temporada histórica
  indicada expresamente en la consulta.
- Crear un entrenamiento o partido asigna siempre la temporada activa del
  perfil. Los schemas rechazan `temporada_id` enviado manualmente.
- Crear una temporada no copia eventos ni documentos. Si el entrenador ya
  tiene perfil, la nueva temporada pasa a ser la activa.
- Reutilizar un entrenamiento conserva el original y crea una copia
  independiente en la temporada activa, incluidas nuevas relaciones con los
  mismos ejercicios globales.
- La planificación diaria es única por `usuario_id`, `temporada_id` y `fecha`.

## Decisión sobre la hora del entrenamiento

La columna nullable `entrenamientos.hora` se conserva temporalmente para no
perder el dato histórico existente. No forma parte de los schemas de creación,
edición o respuesta, no se utiliza para ordenar el calendario y no aparece en
el frontend. Los entrenamientos nuevos y las copias reutilizadas guardan
`hora = NULL`.

Los partidos mantienen su hora en base de datos, API y frontend.

## Migración

El script `scripts/migrate_season_calendars.py`:

1. crea un backup automático antes de aplicar cambios;
2. asigna a los registros históricos sin temporada la temporada activa de su
   entrenador;
3. reconstruye de forma transaccional las tres tablas afectadas;
4. conserva y compara los recuentos de eventos, relaciones y documentos;
5. valida `PRAGMA foreign_key_check` e `integrity_check` antes de confirmar.

El script es idempotente mediante la tabla `schema_migrations`.
