# Validación de migración de la taxonomía de objetivos V2

## Resultado

**MIGRACIÓN ADITIVA Y VALIDACIÓN CORRECTAS**

- Fecha de validación final: `2026-08-11T14:08:51+02:00`
- SQLite: `database/futbol_entrenamiento.sqlite`
- Versión creada: `V2`
- Estado: `BORRADOR`
- Activación: **NO**
- Supabase, backend funcional, frontend y API: **NO MODIFICADOS**

La creación del esquema y la carga se realizaron dentro de una única transacción `BEGIN IMMEDIATE`. Todas las validaciones críticas, incluidas las firmas lógicas históricas y la proyección completa, se ejecutaron antes del `COMMIT`. No fue necesario ejecutar `ROLLBACK` porque no se produjo ninguna discrepancia.

## Archivos de entrada

| Archivo | SHA-256 validado |
|---|---|
| `docs/taxonomia_objetivos_v2_manifest_final.csv` | `ae7b65c48415fa343ff7c574390fb977e0bdd9ff2738bacc07574a7bd399e80f` |
| `docs/taxonomia_objetivos_v2_catalogo_final.csv` | `253715f2aaa5b91469b47b658df78def9058f6e137e91afba979e9effe07a43e` |

Los dos hashes coinciden con los CSV definitivos aprobados. La migración no alteró ninguno de ellos.

## Integridad física de SQLite

| Momento | SHA-256 físico |
|---|---|
| Antes | `c6996ac78c56f2d66c2ba65e1f9df00a93df25f07786dae54f7d51eeb8c2b9da` |
| Después | `11f906bf82161d432ee4d0786a3f0b46d8eed7a6c10f6f931b928e25d6414b56` |

**El cambio físico es esperado y correcto.** Se debe exclusivamente a la modificación aditiva del esquema y a la carga de la capa V2. La igualdad del hash físico no era un criterio de éxito.

## Integridad lógica de las tablas históricas

Las firmas se calcularon con la serialización canónica documentada en el precheck.

| Tabla | SHA-256 antes | SHA-256 después | Resultado |
|---|---|---|---|
| `ejercicios` | `6c3aca23e15b3c208f35a67e1e3165a5fe5412a0150bf65f5c200473a07b9955` | `6c3aca23e15b3c208f35a67e1e3165a5fe5412a0150bf65f5c200473a07b9955` | IDÉNTICO |
| `objetivos` | `7e1993a3e361d6e99bc38b02e0008c27796ab6d6458401e6e46e4600e0e653e3` | `7e1993a3e361d6e99bc38b02e0008c27796ab6d6458401e6e46e4600e0e653e3` | IDÉNTICO |
| `ejercicio_objetivo` | `dd285267c2ecfdcca896bceb144cdf9b42bcc146833477b4a64bee367792e154` | `dd285267c2ecfdcca896bceb144cdf9b42bcc146833477b4a64bee367792e154` | IDÉNTICO |
| `texto_original` | `1fc052307b8edcaba023563d8c33b4137bc6752adb79488ffd9c152d89c46d52` | `1fc052307b8edcaba023563d8c33b4137bc6752adb79488ffd9c152d89c46d52` | IDÉNTICO |

No se modificó ninguna fila, columna, clave ni relación de las cuatro tablas protegidas.

## Tablas V2 creadas

Se crearon exclusivamente estas nueve tablas:

1. `taxonomia_objetivo_versiones`
2. `categorias_objetivo`
3. `objetivos_normalizados_v2`
4. `mapeos_objetivo`
5. `mapeo_objetivo_destinos`
6. `terminos_clasificacion`
7. `mapeo_objetivo_terminos`
8. `mapeos_objetivo_excepciones`
9. `mapeo_excepcion_destinos`

La versión guarda además los SHA-256 de los CSV que originaron su contenido. Las claves foráneas conservan la trazabilidad hasta `objetivos` y, para las excepciones, hasta la relación histórica exacta `ejercicio_id + objetivo_id + tipo_objetivo`.

## Conteos históricos

| Validación | Esperado | Obtenido |
|---|---:|---:|
| Ejercicios | 114 | 114 |
| Objetivos | 129 | 129 |
| Relaciones | 709 | 709 |
| Pares originales ejercicio–objetivo | 577 | 577 |
| Valores originales distintos | 191 | 191 |
| Objetivos huérfanos | 0 | 0 |
| Duplicados de PK | 0 | 0 |
| Relaciones sin `objetivo_original` | 0 | 0 |

## Carga V2

| Entidad | Resultado |
|---|---:|
| Versiones | 1 |
| Categorías | 8 |
| Objetivos normalizados | 94 |
| Mapeos de objetivos fuente | 129 |
| Destinos globales de mapeo | 133 |
| Términos de clasificación | 12 |
| Relaciones mapeo–término | 12 |
| Excepciones exactas | 13 |
| Destinos de excepción | 15 |

Distribución de acciones: `MANTENER=39`, `UNIFICAR=69`, `DIVIDIR=12`, `REUBICAR=9`, `REVISAR=0`.

Estados de decisión: `APROBADO=122`, `CONTEXTO=4`, `FORMATO=1`, `EXCEPCION=2`, `PENDIENTE=0`.

## Proyección y trazabilidad

| Validación | Esperado | Obtenido |
|---|---:|---:|
| Mapeos V2 | 129 | 129 |
| Objetivos normalizados | 94 | 94 |
| Categorías | 8 | 8 |
| Relaciones originales recuperables | 709 | 709 |
| Relaciones normalizadas de procedencia | 747 | 747 |
| Pares semánticos únicos | 585 | 585 |
| Ejercicios representados | 114 | 114 |
| Grupos con procedencia múltiple | 161 | 161 |
| Duplicados semánticos internos | 0 | 0 |
| Excepciones sin cobertura | 0 | 0 |
| Destinos sin categoría | 0 | 0 |
| Casos `REVISAR` o `PENDIENTE` | 0 | 0 |

Las 747 relaciones conservan la procedencia completa. La vista semántica se deduplica por `ejercicio_id + objetivo_normalizado` y produce exactamente 585 pares. Los 11 usos reubicados exclusivamente como contexto o formato permanecen trazables aunque no generen un objetivo normalizado falso.

## Integridad SQLite final

- `PRAGMA integrity_check`: `ok`.
- `PRAGMA foreign_key_check`: 0 incidencias.
- Tablas V2 presentes: 9/9.
- Tablas V2 adicionales no autorizadas: 0.
- Estado `ACTIVA`: 0 versiones.
- Estado de V2: `BORRADOR`.

## Herramientas reproducibles

- `python3 scripts/migrate_taxonomia_v2.py --check`: precheck sin escritura; antes de migrar devolvió `PRECHECK_OK`.
- `python3 scripts/migrate_taxonomia_v2.py --apply`: creación y carga transaccional; devolvió `MIGRATION_OK`.
- `python3 scripts/validate_taxonomia_v2.py`: validación final en modo de solo lectura; devolvió `VALIDATION_OK`.
- `python3 -m py_compile scripts/migrate_taxonomia_v2.py scripts/validate_taxonomia_v2.py`: correcto.

## Confirmación

La capa V2 quedó creada y cargada como **BORRADOR**, sin activarla ni conectarla al backend o frontend. No se ejecutó `normalize_database.py`, no se modificaron los CSV definitivos, no se tocó Supabase y no se realizó ningún commit.

