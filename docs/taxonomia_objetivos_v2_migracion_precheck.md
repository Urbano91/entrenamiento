# Precheck de migración de la taxonomía de objetivos V2

## Resultado

**PRECHECK CORRECTO — AUTORIZADA LA FASE TRANSACCIONAL**

Este informe se generó antes de cualquier escritura en SQLite. Todas las comprobaciones se realizaron abriendo la base de datos en modo de solo lectura.

- Fecha: `2026-08-11T14:02:12+02:00`
- SQLite: `database/futbol_entrenamiento.sqlite`
- Manifiesto: `docs/taxonomia_objetivos_v2_manifest_final.csv`
- Catálogo: `docs/taxonomia_objetivos_v2_catalogo_final.csv`

## Firmas de entrada

| Archivo | SHA-256 |
|---|---|
| SQLite antes de la migración | `c6996ac78c56f2d66c2ba65e1f9df00a93df25f07786dae54f7d51eeb8c2b9da` |
| Manifiesto final | `ae7b65c48415fa343ff7c574390fb977e0bdd9ff2738bacc07574a7bd399e80f` |
| Catálogo final | `253715f2aaa5b91469b47b658df78def9058f6e137e91afba979e9effe07a43e` |

## Firmas lógicas históricas

Las firmas se calculan serializando cada fila como un array JSON compacto UTF-8, con los valores en el orden de columnas indicado y una línea por fila. Las consultas tienen un orden estable por clave primaria.

| Tabla | Columnas incluidas | SHA-256 canónico antes |
|---|---|---|
| `ejercicios` | todas las 14 columnas existentes | `6c3aca23e15b3c208f35a67e1e3165a5fe5412a0150bf65f5c200473a07b9955` |
| `objetivos` | `id`, `nombre_normalizado` | `7e1993a3e361d6e99bc38b02e0008c27796ab6d6458401e6e46e4600e0e653e3` |
| `ejercicio_objetivo` | sus 4 columnas | `dd285267c2ecfdcca896bceb144cdf9b42bcc146833477b4a64bee367792e154` |
| `texto_original` | sus 7 columnas | `1fc052307b8edcaba023563d8c33b4137bc6752adb79488ffd9c152d89c46d52` |

Estas son las firmas de control que deben permanecer exactamente iguales dentro de la transacción y después del commit.

## Estado histórico comprobado

| Comprobación | Resultado esperado | Resultado |
|---|---:|---:|
| Ejercicios | 114 | 114 |
| Objetivos históricos | 129 | 129 |
| Relaciones históricas | 709 | 709 |
| Pares ejercicio–objetivo históricos | 577 | 577 |
| Valores originales distintos | 191 | 191 |
| Objetivos huérfanos | 0 | 0 |
| Duplicados de PK | 0 | 0 |
| Relaciones sin `objetivo_original` | 0 | 0 |
| `PRAGMA integrity_check` | `ok` | `ok` |
| Errores de `PRAGMA foreign_key_check` | 0 | 0 |

## Entradas V2 comprobadas

| Comprobación | Resultado |
|---|---:|
| Filas del manifiesto | 129 |
| IDs de origen distintos | 129 |
| Objetivos del catálogo | 94 |
| Categorías | 8 |
| `MANTENER` | 39 |
| `UNIFICAR` | 69 |
| `DIVIDIR` | 12 |
| `REUBICAR` | 9 |
| `REVISAR` | 0 |
| `PENDIENTE` | 0 |
| Fuentes con excepciones | 2 |
| Excepciones exactas ejercicio–objetivo–rol | 13 |

Distribución del catálogo: `TEC=16`, `TO=27`, `TD=16`, `TRA=12`, `MOD=7`, `FIS=9`, `CP=5`, `COG=2`.

## Comprobación del destino

Ninguna de las nueve tablas V2 existe todavía. Por tanto, la migración puede ejecutarse como una creación aditiva sin sobrescribir una capa V2 previa.

Tablas autorizadas:

1. `taxonomia_objetivo_versiones`
2. `categorias_objetivo`
3. `objetivos_normalizados_v2`
4. `mapeos_objetivo`
5. `mapeo_objetivo_destinos`
6. `terminos_clasificacion`
7. `mapeo_objetivo_terminos`
8. `mapeos_objetivo_excepciones`
9. `mapeo_excepcion_destinos`

## Condición de aborto

La migración debe ejecutar toda la creación y carga en una única transacción. Antes del commit debe volver a calcular las cuatro firmas lógicas históricas. Si una sola difiere, o falla cualquier métrica de cobertura y proyección, debe ejecutar `ROLLBACK` y terminar con error.

El SHA-256 físico del fichero se registrará después de la operación, pero no se exige que permanezca idéntico: la creación aditiva de tablas cambia legítimamente la representación física de SQLite.

