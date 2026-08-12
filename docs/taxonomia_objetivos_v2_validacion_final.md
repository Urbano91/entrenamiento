# Validación final de la taxonomía de objetivos V2

## Resultado

**EJECUCIÓN CORRECTA — MANIFIESTO V2 FINALIZADO**

La operación ha sido exclusivamente documental. No se ha ejecutado ninguna escritura, migración o cambio de esquema sobre SQLite o Supabase, ni se ha modificado código de aplicación.

## Ejecución

- Inicio: `2026-08-11T13:33:39+02:00`
- Fin de generación y primera validación final: `2026-08-11T13:38:01+02:00`
- SQLite utilizada: `/home/upalomar/Entrenamiento_ia/futbol-db/database/futbol_entrenamiento.sqlite`
- Manifiesto provisional utilizado: `docs/taxonomia_objetivos_v2_manifest.csv`
- Informe de revisión utilizado: `docs/taxonomia_objetivos_v2_revision_pendientes.md`

## Firmas de seguridad

### Fichero SQLite

| Momento | SHA-256 |
|---|---|
| Inicial | `c6996ac78c56f2d66c2ba65e1f9df00a93df25f07786dae54f7d51eeb8c2b9da` |
| Final | `c6996ac78c56f2d66c2ba65e1f9df00a93df25f07786dae54f7d51eeb8c2b9da` |

**SQLITE MODIFICADA: NO**

No se produjo cambio físico concurrente durante esta ejecución.

### Firmas lógicas de tablas protegidas

| Tabla/conjunto | Hash inicial | Hash final | Resultado |
|---|---|---|---|
| `ejercicios` | `104ebb7e899c41708987836fe95535731baeea092aefff6a217a7fa6a561c2b5` | `104ebb7e899c41708987836fe95535731baeea092aefff6a217a7fa6a561c2b5` | IDÉNTICO |
| `objetivos` | `fd1d29d4c03d240a5fee0de06b99b951389d83447dde306e0eca3b5e4b6f5702` | `fd1d29d4c03d240a5fee0de06b99b951389d83447dde306e0eca3b5e4b6f5702` | IDÉNTICO |
| `ejercicio_objetivo` | `f3046c590b3a341baf847a82418b92db9e6aaab2f63d439282c22c4c5938f075` | `f3046c590b3a341baf847a82418b92db9e6aaab2f63d439282c22c4c5938f075` | IDÉNTICO |
| `texto_original` | `a7c45f7de1c449176cb941931f5a9eb15fdb63a50ad79eb9fb940d97c1946a9c` | `a7c45f7de1c449176cb941931f5a9eb15fdb63a50ad79eb9fb940d97c1946a9c` | IDÉNTICO |

## Conteos de SQLite

| Comprobación | Inicial | Final | Resultado |
|---|---:|---:|---|
| Ejercicios | 114 | 114 | OK |
| Objetivos | 129 | 129 | OK |
| Relaciones `ejercicio_objetivo` | 709 | 709 | OK |
| Pares distintos ejercicio–objetivo | 577 | 577 | OK |
| Objetivos huérfanos | 0 | 0 | OK |
| Duplicados según PK | 0 | 0 | OK |
| Relaciones sin `objetivo_original` | 0 | 0 | OK |
| Valores originales distintos | 191 | 191 | OK |

## Integridad SQLite

- `PRAGMA integrity_check`: **ok**.
- `PRAGMA foreign_key_check`: **0 filas**.

## Cobertura del manifiesto

| Validación | Resultado |
|---|---:|
| Filas de cabecera | 129 |
| IDs de origen distintos | 129 |
| Nombres de origen distintos | 129 |
| Objetivos SQLite representados | 129/129 |
| Acciones vacías o desconocidas | 0 |
| Categorías `REV` | 0 |
| Estados `PENDIENTE` | 0 |
| Acciones `REVISAR` restantes | 0 |

La columna conservada `frecuencia_ejercicios` coincide con `COUNT(DISTINCT ejercicio_id)`. La nueva columna `frecuencia_relaciones` coincide exactamente con `COUNT(*)` para cada uno de los 129 objetivos.

## Distribución por acción

| Acción | Objetivos origen |
|---|---:|
| MANTENER | 39 |
| UNIFICAR | 69 |
| DIVIDIR | 12 |
| REUBICAR | 9 |
| REVISAR | 0 |
| **Total** | **129** |

## Estados de decisión

| Estado | Objetivos origen |
|---|---:|
| APROBADO | 122 |
| CONTEXTO | 4 |
| FORMATO | 1 |
| EXCEPCION | 2 |
| PENDIENTE | 0 |

## Catálogo normalizado final

Se calcularon **94 objetivos normalizados distintos** mediante `COUNT(DISTINCT objetivo_destino)`, incluyendo los destinos declarados en excepciones.

| Categoría | Objetivos normalizados |
|---|---:|
| TEC | 16 |
| TO | 27 |
| TD | 16 |
| TRA | 12 |
| MOD | 7 |
| FIS | 9 |
| CP | 5 |
| COG | 2 |
| **Total** | **94** |

Cada objetivo normalizado pertenece a exactamente una categoría. No existen destinos vacíos, destinos sin categoría ni nombres asociados a categorías diferentes.

## Validación de DIVIDIR

- Objetivos origen con acción `DIVIDIR`: **12**.
- Los diez mapeos globales tienen entre dos y tres destinos.
- Los dos mapeos con estado `EXCEPCION` contienen al menos dos destinos distintos en su conjunto.
- Destinos de excepción sin categoría válida: **0**.
- Relaciones de excepción sin decisión: **0**.

## Excepciones por ejercicio y rol

- Objetivos origen con excepciones: **2**.
- Ejercicios distintos afectados: **9**.
- Relaciones originales cubiertas mediante excepción: **13**.

### Cambio de chip

| Ejercicio | Rol | Destino V2 |
|---:|---|---|
| 11 | principal | Presión tras pérdida |
| 39 | principal | Transición inmediata + Ajuste posicional tras transición |
| 39 | defensivo | Transición inmediata + Ajuste posicional tras transición |
| 74 | principal | Transición inmediata |
| 74 | ofensivo | Transición inmediata |

### Sacar de zona

| Ejercicio | Rol | Destino V2 |
|---:|---|---|
| 5 | ofensivo | Cambio de orientación |
| 17 | principal | Salida de zona tras recuperación |
| 72 | secundario | Salida de zona tras recuperación |
| 72 | defensivo | Salida de zona tras recuperación |
| 73 | ofensivo | Juego exterior |
| 75 | principal | Progresión tras recuperación |
| 75 | defensivo | Progresión tras recuperación |
| 76 | ofensivo | Juego exterior tras recuperación |

Cada excepción conserva `ejercicio_id`, objetivo origen implícito en su fila, `tipo_objetivo`, destinos con categoría, contexto y motivo.

## Validación de REUBICAR

- Acciones `REUBICAR`: **9**.
- Reubicaciones puras sin objetivo normalizado: **5**.
- Reubicaciones que separan un objetivo normalizado de contexto/formato: **4**.
- Reubicaciones sin contexto ni formato: **0**.

Las cuatro reubicaciones con objetivo corresponden a frases condicionadas cuya decisión auditada separa explícitamente acción y contexto. Las demás no generan objetivos falsos.

## Simulación de relaciones normalizadas

La simulación recorrió las 709 relaciones originales y aplicó el mapeo global o la excepción exacta correspondiente.

| Métrica | Resultado |
|---|---:|
| Relaciones originales recuperables | 709 |
| Relaciones normalizadas de procedencia | 747 |
| Relaciones fuente reubicadas solo como contexto/formato | 11 |
| Pares semánticos distintos ejercicio–objetivo V2 | 585 |
| Ejercicios con al menos un objetivo V2 | 114 |
| Grupos con varias procedencias | 161 |
| Procedencias adicionales sobre pares ya existentes | 162 |

Las 747 relaciones de procedencia pueden superar las 709 originales porque un objetivo compuesto genera varios destinos. Los 585 pares semánticos son la proyección deduplicada que deberá utilizar el filtro.

### Duplicados semánticos

Los 161 grupos repetidos provienen de objetivos equivalentes, divisiones o roles diferentes. No se eliminan de la trazabilidad. La simulación deduplica por:

`ejercicio_id + objetivo_normalizado`

Resultado de la proyección deduplicada: **585 claves únicas, sin duplicados internos**.

**VALIDACIÓN DE DUPLICADOS SEMÁNTICOS: OK**

## Trazabilidad

Se verificó que:

- Cada una de las 129 decisiones conserva ID y nombre de origen.
- Los 191 textos originales permanecen recuperables desde las 709 relaciones.
- Cada destino global remite a su objetivo origen.
- Cada destino de excepción remite a ejercicio, objetivo origen y rol.
- Contexto y formato no se convierten silenciosamente en objetivos.
- El catálogo final incluye las fuentes de cada uno de los 94 destinos.
- Ningún ejercicio queda fuera de la proyección normalizada.

**VALIDACIÓN DE TRAZABILIDAD: OK**

## Decisiones conservadoras con confianza reducida

No quedan casos `REVISAR`, pero se preserva incertidumbre mediante la confianza:

- `Presión alta`: se mantiene con confianza BAJA sin fusionarla con Presión en campo rival.
- `Ayudas`: se normaliza como Ayudas defensivas con confianza BAJA, sin equipararla a Cobertura defensiva.
- `Ayudas defensivas`: se mantiene con confianza BAJA.
- `Balón aéreo`: se reubica como contexto con confianza BAJA.
- `Remate de cabeza`: se mantiene como acción técnica independiente con confianza MEDIA.
- `Dividir`: se normaliza como Fijar o dividir al rival con confianza MEDIA.

Estas decisiones conservan el significado original y pueden revisarse en una versión posterior sin modificar las relaciones fuente.

## Anomalías

- Anomalías de integridad: **0**.
- Objetivos fuente omitidos: **0**.
- Frecuencias discrepantes: **0**.
- Destinos sin categoría: **0**.
- Excepciones sin cobertura: **0**.
- Casos pendientes: **0**.
- Cambios físicos o lógicos en SQLite durante la ejecución: **0**.

## Archivos creados

1. `docs/taxonomia_objetivos_v2_manifest_final.csv`
2. `docs/taxonomia_objetivos_v2_catalogo_final.csv`
3. `docs/taxonomia_objetivos_v2_validacion_final.md`

Firmas de los CSV finales en el momento de validación:

- Manifiesto final: `ae7b65c48415fa343ff7c574390fb977e0bdd9ff2738bacc07574a7bd399e80f`
- Catálogo final: `253715f2aaa5b91469b47b658df78def9058f6e137e91afba979e9effe07a43e`

## Confirmación final

**NO SE HA MODIFICADO SQLITE, SUPABASE, BACKEND NI FRONTEND.**

No se han creado tablas, ejecutado migraciones, ejecutado `normalize_database.py`, realizado operaciones `INSERT`, `UPDATE` o `DELETE`, ni creado ningún commit.
