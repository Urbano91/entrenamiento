# Informe de normalización de la base de datos

Estado: **APLICADO Y VALIDADO**

## Resumen

| Métrica | Antes | Después |
|---|---:|---:|
| Ejercicios | 114 | 114 |
| Objetivos | 182 | 129 |
| Relaciones ejercicio-objetivo | 709 | 709 |
| Tipos de tarea | 10 | 10 |
| Espacios | 36 | 31 |
| Tiempos | 29 | 23 |
| Materiales | 54 | 44 |
| Imágenes | 122 | 122 |
| Texto original | 989 | 989 |

- Variantes duplicadas de objetivos detectadas: **53**.
- Variantes de objetivo clasificadas como errores ortográficos: **18**.
- Ejercicios distintos afectados por fusiones de objetivos: **82**.
- Relaciones ejercicio-objetivo reasignadas: **145**.
- Objetivos redundantes unificados/eliminados: **53**.
- Variantes redundantes en el resto de catálogos: **21** (5 espacios, 6 tiempos y 10 materiales).
- Referencias reasignadas en espacios/tiempos/materiales: **7 / 24 / 10**.
- Nombres de objetivos ajustados para presentación: **51**.
- Nombres de materiales corregidos ortográfica/formalmente: **20**.
- Nombres de ejercicios corregidos ortográficamente: **19**.
- Casos ambiguos no modificados: **17**.
- `texto_original`, `nombre_original`, objetivos originales y materiales originales se conservaron.
- No se detectaron duplicados en tipos de tarea ni en nombres normalizados de ejercicios.

## Normalizaciones de objetivos

| ID original | Original | ID canónico | Canónico | Motivo | Ejercicios |
|---:|---|---:|---|---|---:|
| 15 | Movilidad sin balón | 3 | Movilidad sin balón | variante de puntuación | 1 |
| 20 | Crear lineas de pase | 4 | Crear líneas de pase | variante de puntuación | 16 |
| 129 | Crear Lineas de pase | 4 | Crear líneas de pase | variante de mayúsculas y tilde | 1 |
| 10 | Cerrar Lineas de pase | 7 | Cerrar líneas de pase | variante de mayúsculas | 1 |
| 21 | Cerrar lineas de pase | 7 | Cerrar líneas de pase | variante de puntuación | 32 |
| 17 | Cerrar lines de pase | 7 | Cerrar líneas de pase | errata: lines | 1 |
| 137 | Cerrrar lineas de pase | 7 | Cerrar líneas de pase | errata: cerrrar | 1 |
| 9 | Mejora tecnica de control y pase | 5 | Mejora técnica del control y el pase | variante ortográfica equivalente | 1 |
| 29 | Mejora tecnica del control y el pase | 5 | Mejora técnica del control y el pase | variante con artículo equivalente | 13 |
| 34 | Mejora tecnica del control y el pase. | 5 | Mejora técnica del control y el pase | variante de puntuación | 3 |
| 37 | Mejora tecnica del control y el pase.5 | 5 | Mejora técnica del control y el pase | carácter espurio al final | 1 |
| 59 | Mejora tecnica del pase y el control | 5 | Mejora técnica del control y el pase | orden equivalente de control y pase | 1 |
| 44 | Conversación de balón | 6 | Conservación de balón | errata: conversación | 1 |
| 47 | Convervación de balon | 6 | Conservación de balón | errata: convervación | 1 |
| 77 | Orientación de la presión | 22 | Orientación de la presión | variante de tilde | 4 |
| 18 | Orientación presión | 22 | Orientación de la presión | variante sin artículo | 1 |
| 43 | Evitar pases interiores | 30 | Evitar pases interiores | variante singular/plural | 1 |
| 83 | Cambio chip | 39 | Cambio de chip | variante sin preposición | 2 |
| 48 | Cambios de orientación | 46 | Cambio de orientación | variante singular/plural | 3 |
| 89 | Interceptacion | 45 | Interceptación | variante sin tilde | 1 |
| 133 | Intercepttación | 45 | Interceptación | errata: intercepttación | 1 |
| 139 | Dejar de Cara | 58 | Dejar de cara | variante de mayúsculas | 1 |
| 103 | Trabajo Coordinativo | 61 | Trabajo coordinativo | variante de mayúsculas | 4 |
| 121 | Trabajo coordinativo. | 61 | Trabajo coordinativo | variante de puntuación | 4 |
| 70 | Trabajo cordinativo | 61 | Trabajo coordinativo | errata: cordinativo | 1 |
| 64 | Inicio de juego | 62 | Inicio de juego | variante con preposición | 3 |
| 75 | Inicio juego | 62 | Inicio de juego | variante sin preposición | 1 |
| 156 | Juego Directo | 82 | Juego directo | variante de mayúsculas | 2 |
| 118 | . Trabajo Preventivo | 91 | Trabajo preventivo | puntuación inicial y mayúsculas | 1 |
| 108 | Mejora tecnica del pase. | 92 | Mejora técnica del pase | variante de puntuación | 10 |
| 100 | Trabajo propiocepcion | 93 | Trabajo de propiocepción | variante sin tilde | 1 |
| 104 | Trabajo Propiocepción | 93 | Trabajo de propiocepción | variante de mayúsculas | 3 |
| 112 | Trabajo de propiocepción | 93 | Trabajo de propiocepción | variante con preposición | 1 |
| 117 | Trabjo Propiocepción | 93 | Trabajo de propiocepción | errata: trabjo | 1 |
| 102 | Fuerza Tren Superior | 95 | Fuerza del tren superior | variante de mayúsculas | 1 |
| 107 | Trabajo Tren superior | 97 | Trabajo de tren superior | variante de mayúsculas | 2 |
| 106 | Trabajo Fuerza Explosiva | 99 | Trabajo de fuerza explosiva | variante de mayúsculas | 1 |
| 120 | Resistencia Aeróbica. | 109 | Resistencia aeróbica | variante de puntuación | 1 |
| 114 | Trabajo de resistencia aerobica | 111 | Trabajo de resistencia aeróbica | variante sin tilde | 1 |
| 161 | Juego Áereo | 122 | Juego aéreo | errata en tilde de aéreo | 2 |
| 125 | Balón aéreo | 124 | Balón aéreo | variante de mayúsculas | 1 |
| 127 | Ampitud | 72 | Amplitud | errata: ampitud | 1 |
| 126 | Finañización | 80 | Finalización | errata: finañización | 1 |
| 143 | Basculacion | 53 | Basculaciones | variante singular/plural y tilde | 1 |
| 158 | Marcajes y Basulaciones | 162 | Marcajes y basculaciones | errata: basulaciones | 1 |
| 147 | Organización ofensiva | 145 | Organización ofensiva | variante de mayúsculas | 1 |
| 149 | Organización Defensiva | 148 | Organización defensiva | variante de mayúsculas | 3 |
| 180 | Remate de cabeza | 164 | Remate de cabeza | variante de mayúsculas | 1 |
| 168 | Despeje Orientado | 165 | Despeje orientado | variante de mayúsculas | 1 |
| 170 | Defensa en zona | 169 | Defensa en zona | variante de mayúsculas | 2 |
| 182 | Trabajo de Velocidad de reacción | 176 | Trabajo de velocidad de reacción | variante de mayúsculas | 1 |
| 171 | Despeje | 84 | Despeje | variante singular/plural | 1 |
| 178 | . Toma de decisiones | 36 | Toma de decisiones | puntuación inicial redundante | 1 |

## Casos ambiguos no modificados

- Pressing ↔ Presión
- Pressing tras pérdida ↔ Presión / Presión alta
- Conservación de balón ↔ Posesión
- Marcajes ↔ Marcas
- Crear / Buscar / Cerrar líneas de pase
- Cerrar líneas de pase interiores ↔ Tapar / Evitar pases interiores
- Coordinación ↔ Trabajo coordinativo ↔ Trabajo de coordinación
- Fuerza explosiva ↔ Trabajo de fuerza explosiva
- Fuerza resistencia ↔ Trabajo de fuerza resistencia
- Fuerza preventiva ↔ Trabajo preventivo
- Velocidad de reacción ↔ Trabajo de velocidad de reacción
- Técnica ↔ Trabajo técnico
- Juego aéreo ↔ Balón aéreo ↔ Remate de cabeza
- Inicio ↔ Inicio de juego
- Marcajes y basculaciones ↔ Marcajes / Basculaciones por separado
- Materiales con las mismas palabras pero distinto orden o conjunción
- Ejercicio ABP3: nombre normalizado ofensivo y nombre original defensivo

## Integridad y trazabilidad

- `PRAGMA integrity_check`: **ok**.
- Claves foráneas: **activadas y verificadas**.
- Backup: `/home/upalomar/Entrenamiento_ia/futbol-db/database/futbol_entrenamiento.sqlite.bak-before-normalization-20260810105623`.
- Mapeo completo de objetivos: `docs/normalizacion_objetivos.csv`.
- Mapeo de espacios, tiempos y materiales: `docs/normalizacion_catalogos.csv`.

## Criterios conservadores

Solo se fusionaron diferencias mecánicas, erratas inequívocas y variantes cuya equivalencia fue confirmada con sus ejercicios asociados. Los conceptos que podrían expresar matices tácticos diferentes permanecen separados. La búsqueda semántica debe usar `objetivos.id` y `ejercicio_objetivo`, no `LIKE`.
