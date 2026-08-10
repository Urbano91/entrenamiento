# Biblioteca visual original

La biblioteca contiene una portada WebP y una animación WebM para cada uno de los 114 ejercicios. Los recursos se localizan por el ID real, sin columnas nuevas en SQLite:

```text
animations/<exercise_id>/portada.webp
animations/<exercise_id>/animacion.webm
```

Las portadas se generan desde el mismo fotograma inicial entregado al codificador de vídeo. Todo el material gráfico utiliza el sistema propio de pizarra táctica aprobado en el piloto: campo, fichas genéricas, balón, conos, porterías, zonas y flechas. No contiene fotografías, logos, tipografías propietarias ni píxeles copiados de las 122 referencias externas.

La información individual de producción —nombre, rutas, duración, tamaños, estado y observaciones— está en `visual_library_report.csv`. Los ejercicios que no puedan representarse sin inventar deben aparecer en `needs_review.csv`.

## Regeneración por lotes

Requisitos locales: Python 3, Pillow y OpenCV con codificador WebM/VP9, o FFmpeg con `libvpx-vp9`.

```bash
python3 scripts/produce_visual_library.py --start 1 --end 20
python3 scripts/produce_visual_library.py --start 21 --end 40
python3 scripts/produce_visual_library.py --start 41 --end 60
python3 scripts/produce_visual_library.py --start 61 --end 80
python3 scripts/produce_visual_library.py --start 81 --end 100
python3 scripts/produce_visual_library.py --start 101 --end 114
```

Cada ejecución consulta y valida nombre, descripción, objetivos, espacio, tiempo, materiales y referencia vinculada antes de generar. La salida estándar es 960×540 px, 24 fps, 8 segundos, sin audio y con vídeo VP9. La portada se guarda como WebP sin pérdida.

La interfaz carga únicamente `portada.webp` en el catálogo. `animacion.webm` se inserta al pulsar «Ver movimiento». Si falta el vídeo pero existe la portada, la portada continúa visible.
