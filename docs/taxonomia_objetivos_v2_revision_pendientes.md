# Revisión pendiente de la taxonomía de objetivos V2

## Alcance y método

Este documento analiza exclusivamente los 26 objetivos marcados como `REVISAR` en `taxonomia_objetivos_v2_manifest.csv`. La fuente factual es la SQLite actual, abierta en modo de solo lectura. Las recomendaciones son provisionales: ninguna cambia el manifiesto ni constituye una decisión del entrenador.

Para cada objetivo se contrastaron todas sus relaciones, los ejercicios afectados, el texto original conservado, los roles y los demás objetivos presentes en esos ejercicios. “Frecuencia” significa número de ejercicios distintos; “relaciones” conserva las repeticiones por rol.

## Objetivo: 1 vs 1

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **2**.
- Roles: `ofensivo` (1), `secundario` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 94 | Juego de Posición 8 vs 8 Duelos Posicionales | 1 vs 1 | `secundario` |
| 94 | Juego de Posición 8 vs 8 Duelos Posicionales | 1 vs 1 | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Conservación de balón`, `Disputa`, `Marcajes`.

### Destinos candidatos existentes en el manifiesto

Duelo y disputa, Marcaje, Regate y Finalización. Duelo 1 contra 1 pertenece a la taxonomía auditada, pero aún no es destino usado.

### Problema semántico

La notación también puede ser un formato numérico, por lo que era necesario comprobar si funciona como objetivo real.

### Interpretación

JPC13 asigna una zona y rival a cada jugador, exige ganar el duelo posicional y realizar acciones ofensivas rápidas de uno contra uno que finalicen. Aquí sí representa una competencia individual, no solo el formato del ejercicio.

### Opciones

- A. Normalizar como Duelo 1 contra 1.
- B. Dividir en Regate ofensivo y Duelo y disputa.
- C. Mantener 1 vs 1 como formato.

### Recomendación

Normalizar como Duelo 1 contra 1 y conservarlo como objetivo independiente. La dimensión 8 contra 8 seguirá siendo formato, pero los duelos individuales son la finalidad.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Acumulación de gente

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `ofensivo` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 83 | Juego de Posición 5 vs 3 en banda + Cambio | Acumulación de gente | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Agrupar gente`, `Basculaciones`, `Cambio de orientación`, `Finalización`, `Interceptación`.

### Destinos candidatos existentes en el manifiesto

Cambio de orientación, Finalización y Basculación defensiva. Atraer y liberar espacio aún no aparece como destino usado.

### Problema semántico

Es una formulación poco profesional y duplicada con Agrupar gente dentro del mismo ejercicio.

### Interpretación

JPC2 busca atraer rivales a la banda antes de filtrar al mediocentro y cambiar al lado liberado. La acumulación es una conducta instrumental para liberar espacio.

### Opciones

- A. Unificar con Agrupar gente.
- B. Normalizar ambos como Atraer y liberar espacio.
- C. Reubicar como contexto de superioridad en banda.

### Recomendación

Unificar con Agrupar gente bajo Atraer y liberar espacio. El mismo ejercicio y desarrollo sustentan una única intención táctica.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Agrupar gente

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `principal` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 83 | Juego de Posición 5 vs 3 en banda + Cambio | Agrupar gente | `principal` |

### Otros objetivos que aparecen en esos ejercicios

`Acumulación de gente`, `Basculaciones`, `Cambio de orientación`, `Finalización`, `Interceptación`.

### Destinos candidatos existentes en el manifiesto

Cambio de orientación, Finalización y Basculación defensiva. Atraer y liberar espacio aún no aparece como destino usado.

### Problema semántico

Coexiste con Acumulación de gente en el mismo ejercicio y ambas expresiones parecen describir el mismo mecanismo ofensivo.

### Interpretación

JPC2 concentra jugadores y rivales en una banda mediante cinco pases para liberar el lado opuesto y cambiar la orientación. Agrupar no es una finalidad aislada, sino el medio para atraer y liberar espacio.

### Opciones

- A. Unificar con Acumulación de gente.
- B. Normalizar ambos como Atraer y liberar espacio.
- C. Convertir la acumulación en contexto y mantener Cambio de orientación.

### Recomendación

Unificar Agrupar gente y Acumulación de gente en Atraer y liberar espacio, conservando Cambio de orientación como objetivo adicional.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Asignación de tareas

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `general` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 109 | Juego de las Casas | Asignación de tares | `general` |

### Otros objetivos que aparecen en esos ejercicios

`Activación`, `Comunicación`, `Regate`.

### Destinos candidatos existentes en el manifiesto

Toma de decisiones, Comunicación, Activación y Regate.

### Problema semántico

Describe la organización de roles o reglas del juego, no una capacidad u objetivo de entrenamiento claramente evaluable.

### Interpretación

En Juego de las Casas se asignan casas, protección, robo, rescate y transporte de balones. El ejercicio ya contiene Activación, Comunicación y Regate; la asignación estructura el formato lúdico.

### Opciones

- A. Reubicar como contexto de roles/tareas asignadas.
- B. Convertirlo en Toma de decisiones.
- C. Mantenerlo como objetivo organizativo.
- D. Retirarlo del filtro conservando el original.

### Recomendación

Reubicar como contexto o regla de organización del juego. No mantenerlo como objetivo independiente.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Ayudas

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `defensivo` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 35 | Ataque/Defensa Inicio juego | Ayudas | `defensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Basculaciones`, `Conservación de balón`, `Inicio de juego`, `Orientación de la presión`, `Salir jugando`.

### Destinos candidatos existentes en el manifiesto

Cobertura defensiva, Basculación defensiva, Organización defensiva y Orientación de la presión.

### Problema semántico

No especifica si son coberturas, permutas, apoyos defensivos o coordinación colectiva.

### Interpretación

Solo figura como defensivo en AD2, junto a basculación y orientación de la presión. El desarrollo describe la salida ofensiva con detalle, pero no concreta el comportamiento defensivo denominado Ayudas.

### Opciones

- A. Unificar con Cobertura defensiva.
- B. Mantener Ayudas defensivas como objetivo propio.
- C. Integrarlo en Organización defensiva.
- D. Corregir o retirar la etiqueta en AD2.

### Recomendación

Solicitar al entrenador qué conducta defensiva se pretendía en AD2. No hay base textual suficiente para elegir cobertura, basculación u organización.

**Confianza provisional: BAJA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Ayudas defensivas

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `defensivo` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 92 | Juego de Posición en Doble área II | Ayudas defensivas | `defensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Amplitud`, `Basculaciones`, `Conservación de balón`.

### Destinos candidatos existentes en el manifiesto

Cobertura defensiva, Basculación defensiva y Organización defensiva.

### Problema semántico

Puede equivaler a cobertura, pero el desarrollo no documenta posiciones de ayuda, permutas ni coberturas concretas.

### Interpretación

Solo aparece en JPC11 junto a Basculaciones. El texto explica amplitud, conservación y reglas de finalización, pero no desarrolla la conducta defensiva etiquetada como ayudas.

### Opciones

- A. Unificar con Cobertura defensiva.
- B. Mantener Ayudas defensivas independiente.
- C. Integrar en Organización defensiva.
- D. Corregir o retirar la etiqueta de JPC11.

### Recomendación

Pedir al entrenador que confirme si JPC11 trabaja coberturas. No unificar automáticamente a partir del nombre.

**Confianza provisional: BAJA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Balón aéreo

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **3**.
- Roles: `defensivo` (1), `ofensivo` (1), `principal` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 66 | Juego de Posesión 4 vs 4 Inicio Saque de puerta | Balón Aéreo | `principal` |
| 66 | Juego de Posesión 4 vs 4 Inicio Saque de puerta | Balón aéreo | `ofensivo` |
| 66 | Juego de Posesión 4 vs 4 Inicio Saque de puerta | Balón aéreo | `defensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Cerrar líneas de pase`, `Conservación de balón`, `Finalización`.

### Destinos candidatos existentes en el manifiesto

Inicio de juego, Juego directo y Finalización. Juego aéreo y Desmarque de ruptura continúan pendientes.

### Problema semántico

La etiqueta aparece tres veces por roles en un único ejercicio, pero el desarrollo no describe de manera inequívoca una repetición de acciones aéreas.

### Interpretación

JPS1 comienza con saque de puerta, exige cinco pases y después desmarque hacia portería. Solo una variante permite bajar a recibir si el saque no llega al cuadrado. Balón aéreo parece una condición del envío o del reinicio, no un objetivo demostrable.

### Opciones

- A. Reubicar Balón aéreo como contexto o tipo de envío.
- B. Unificar con Juego aéreo si el entrenador confirma duelos aéreos.
- C. Sustituir por Juego directo o Inicio de juego.
- D. Corregir la etiqueta del ejercicio.

### Recomendación

Reubicar provisionalmente como contexto de envío y pedir confirmación sobre JPS1 antes de asignar un objetivo normalizado.

**Confianza provisional: BAJA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Cambio de chip

### Uso actual

- Frecuencia del manifiesto: **3 ejercicios**.
- Ejercicios distintos afectados: **3**.
- Relaciones totales: **5**.
- Roles: `defensivo` (1), `ofensivo` (1), `principal` (3).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 11 | Rondo 4 vs 1 (4 Grupos) | Cambio de chip | `principal` |
| 39 | Ataque/Defensa 1 vs 1 + Cambio chip | Cambio chip | `principal` |
| 39 | Ataque/Defensa 1 vs 1 + Cambio chip | Cambio de chip | `defensivo` |
| 74 | Juego de Posesión 3 equipos | Cambio chip | `principal` |
| 74 | Juego de Posesión 3 equipos | Cambio de chip | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Cambio de chip y desplazamiento`, `Cerrar líneas de pase`, `Conservación de balón`, `Despeje`, `Finalización`, `Interceptación`.

### Destinos candidatos existentes en el manifiesto

Presión tras pérdida y Juego tras recuperación. Transición inmediata y Ajuste posicional tras transición forman parte de la taxonomía auditada, pero aún no son destinos usados en el manifiesto.

### Problema semántico

La expresión coloquial cubre comportamientos distintos según el cambio de posesión y no define la dirección de la transición.

### Interpretación

R11 pide reaccionar a la pérdida y presionar otro cuadrado; AD6 exige pasar de finalizar a defender la portería opuesta; JPS9 cambia de inmediato los roles tras recuperación/pérdida. Los tres casos son transicionales, pero no equivalentes.

### Opciones

- A. Mantener Cambio de chip como concepto paraguas.
- B. Mapear cada ejercicio a una transición concreta.
- C. Dividirlo globalmente en presión tras pérdida, transición inmediata y ajuste posicional.

### Recomendación

No crear Cambio de chip como objetivo V2. Resolver cada relación: Presión tras pérdida en R11 y objetivos transicionales específicos en AD6 y JPS9.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Cambio de chip y desplazamiento

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `defensivo` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 11 | Rondo 4 vs 1 (4 Grupos) | Cambio de chip y desplazamiento | `defensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Cambio de chip`, `Cerrar líneas de pase`, `Conservación de balón`.

### Destinos candidatos existentes en el manifiesto

Presión tras pérdida; el desplazamiento al cuadrado libre puede conservarse como contexto.

### Problema semántico

Combina una reacción transicional con una instrucción espacial.

### Interpretación

Su único uso está en R11: después de perder, los jugadores deben desplazarse y presionar inmediatamente el cuadrado libre. El significado resulta mucho más concreto que Cambio de chip genérico.

### Opciones

- A. Unificar con Presión tras pérdida.
- B. Dividir en Presión tras pérdida y Ajuste posicional tras transición.
- C. Mantener el desplazamiento como contexto.

### Recomendación

Unificar con Presión tras pérdida y conservar desplazamiento al cuadrado libre como contexto del ejercicio.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Colocación

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `secundario` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 26 | Rueda de pase colocación | Colocación | `secundario` |

### Otros objetivos que aparecen en esos ejercicios

`Balón de cara`, `Inicio de juego`, `Mejora técnica del control y el pase`, `Tercer hombre`.

### Destinos candidatos existentes en el manifiesto

Inicio de juego y Organización ofensiva. Posicionamiento pertenece a la taxonomía auditada, pero aún no aparece como destino utilizado.

### Problema semántico

Colocación puede significar postura técnica o posicionamiento colectivo; el nombre aislado no lo determina.

### Interpretación

En RP7 describe una rueda sin rotación que reproduce posiciones y conexiones del inicio de juego. El contenido apunta a posicionamiento estructural, no a colocación corporal o técnica de golpeo.

### Opciones

- A. Unificar con Posicionamiento.
- B. Integrarlo en Inicio de juego.
- C. Reubicar la estructura posicional como contexto.

### Recomendación

Unificar con Posicionamiento dentro de Modelo y organización colectiva, manteniendo Inicio de juego como objetivo adicional del ejercicio.

**Confianza provisional: MEDIA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Conservación de balón

### Uso actual

- Frecuencia del manifiesto: **58 ejercicios**.
- Ejercicios distintos afectados: **58**.
- Relaciones totales: **91**.
- Roles: `general` (1), `ofensivo` (54), `principal` (14), `secundario` (22).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 1 | Rondo 3 vs 1 | Conservacion de balón | `ofensivo` |
| 2 | Rondo 5 vs 2 | Conservación de balón | `secundario` |
| 2 | Rondo 5 vs 2 | Conservacion de balón | `ofensivo` |
| 3 | Rondo 4 vs 1 + Progresión | Conservación de balón | `secundario` |
| 3 | Rondo 4 vs 1 + Progresión | Conservacion de balón | `ofensivo` |
| 4 | Rondo 3 vs 1 + Progresión | Conservacion de balón | `ofensivo` |
| 5 | Rondo 8 vs 4 | Conservacion de balón | `ofensivo` |
| 6 | Rondo 4 vs 4 + 3 Comodines | Conservacion de balón | `ofensivo` |
| 7 | Rondo 4 vs 1 + 1 Interior | Conservación de balón | `secundario` |
| 7 | Rondo 4 vs 1 + 1 Interior | Conservacion de balón | `ofensivo` |
| 8 | Rondo 4 vs 1 | Conservación de balón | `principal` |
| 8 | Rondo 4 vs 1 | Conservacion de balón | `ofensivo` |
| 9 | Rondo 5 vs 2 en triángulo | Conservacion de balón | `ofensivo` |
| 10 | Rondo 6 vs 2 por parejas | Conservacion de balón | `ofensivo` |
| 11 | Rondo 4 vs 1 (4 Grupos) | Conservación de balón | `secundario` |
| 11 | Rondo 4 vs 1 (4 Grupos) | Conservacion de balón | `ofensivo` |
| 12 | Rondo 3 vs 3 + 3 Comodines | Conservación de balón | `secundario` |
| 12 | Rondo 3 vs 3 + 3 Comodines | Conservacion de balón | `ofensivo` |
| 13 | Rondo 4 vs 2 + 1 Interior | Conservación de balón | `secundario` |
| 13 | Rondo 4 vs 2 + 1 Interior | Conservación de balón | `ofensivo` |
| 14 | Rondo 4 vs 1 (Doble) | Conservación de balón | `secundario` |
| 14 | Rondo 4 vs 1 (Doble) | Conversación de balón | `ofensivo` |
| 15 | Rondo 4 vs 3 + 1 Comodín (Doble) | Convervación de balon | `ofensivo` |
| 16 | Rondo 4 vs 4 + 2 Comodines | Conservación de balón | `principal` |
| 16 | Rondo 4 vs 4 + 2 Comodines | Conservación de balón | `ofensivo` |
| 17 | Rondo 4 vs 2 + Progresión | Conservación de balón | `ofensivo` |
| 18 | Rondo 6 vs 2 | Conservación de balón | `secundario` |
| 19 | Rondo 3 vs 3 + 4 Comodines | Conservación de balón | `secundario` |
| 19 | Rondo 3 vs 3 + 4 Comodines | Conservacion de balón | `ofensivo` |
| 34 | Ataque/Defensa Juego real | Conservación de balón | `principal` |
| 34 | Ataque/Defensa Juego real | Conservación de balón | `ofensivo` |
| 35 | Ataque/Defensa Inicio juego | Conservación de balón | `secundario` |
| 36 | Ataque/Defensa Ocupación | Conservación de balón | `secundario` |
| 36 | Ataque/Defensa Ocupación | Conservación de balón | `ofensivo` |
| 37 | Ataque/Defensa Ocupación Carriles Exteriores | Conservación de balón | `secundario` |
| 37 | Ataque/Defensa Ocupación Carriles Exteriores | Conservación de balón | `ofensivo` |
| 48 | Circuito Resistencia Aeróbica + Posesión 4 vs 4 | Conservación de balón | `general` |
| 66 | Juego de Posesión 4 vs 4 Inicio Saque de puerta | Conservación de balón | `secundario` |
| 66 | Juego de Posesión 4 vs 4 Inicio Saque de puerta | Conservación de balón | `ofensivo` |
| 67 | Juego de Posesión 7 vs 7 sobre portería central | Conservación de balón | `principal` |
| 67 | Juego de Posesión 7 vs 7 sobre portería central | Conservación de balón | `ofensivo` |
| 68 | Juego de Posesión 8 vs 4 | Conservación de balón | `principal` |
| 68 | Juego de Posesión 8 vs 4 | Conservación de Balón | `ofensivo` |
| 69 | Juego de Posesión 4 vs 4 + 2 Comodines + Ataque | Conservación de balón | `principal` |
| 69 | Juego de Posesión 4 vs 4 + 2 Comodines + Ataque | Conservación de balón | `ofensivo` |
| 70 | Juego de Posesión 6 vs 6 + 1 Comodín Interior | Conservación de balón | `principal` |
| 70 | Juego de Posesión 6 vs 6 + 1 Comodín Interior | Conservación de Balón | `ofensivo` |
| 71 | Juego de Posesión 6 vs 6 con la mano | Conservación de Balón | `ofensivo` |
| 72 | Juego de Posesión Presión en campo contrario | Conservación de balón | `ofensivo` |
| 73 | Juego de Posesión en Hexágono | Conservación de balón | `principal` |
| 73 | Juego de Posesión en Hexágono | Conservación de balón | `ofensivo` |
| 74 | Juego de Posesión 3 equipos | Conservación de balón | `secundario` |
| 74 | Juego de Posesión 3 equipos | Conservación de balón | `ofensivo` |
| 75 | Juego de Posesión 6 vs 6 + 2 Comodines | Conservación de balón | `ofensivo` |
| 76 | Juego de Posesión 4 vs 4 + 1 Comodín | Conservación de balón | `ofensivo` |
| 77 | Juego de Posesión 3 vs 3 + 4 Comodines | Conservación de balón | `secundario` |
| 77 | Juego de Posesión 3 vs 3 + 4 Comodines | Conservación de Balón | `ofensivo` |
| 78 | Juego de Posesión 2 vs 2 + 2 Comodines | Conservación de balón | `secundario` |
| 78 | Juego de Posesión 2 vs 2 + 2 Comodines | Conservación de Balón | `ofensivo` |
| 79 | Juego de Posesión 4 vs 4 + 2 Comodines | Conservación de balón | `principal` |
| 79 | Juego de Posesión 4 vs 4 + 2 Comodines | Conservación de balón | `ofensivo` |
| 80 | Juego de Posesión 5 vs 5 + 2 Comodines | Conservación de balón | `principal` |
| 80 | Juego de Posesión 5 vs 5 + 2 Comodines | Conservación de balón | `ofensivo` |
| 81 | Juego de Posesión 5 vs 5 + 2 Comodines Exteriores | Conservación de balón | `principal` |
| 81 | Juego de Posesión 5 vs 5 + 2 Comodines Exteriores | Conservación de Balón | `ofensivo` |
| 82 | Juego de Posición táctico 10 vs 10 | Conservación de balón | `principal` |
| 84 | Juego de Posición 6 vs 6 Zona de Iniciación | Conservación de balón | `secundario` |
| 84 | Juego de Posición 6 vs 6 Zona de Iniciación | Conservación de balón | `ofensivo` |
| 85 | Juego de posición en Doble área | Conservación de balón | `ofensivo` |
| 86 | Juego de Posición Presión en campo contrario | Conservación de balón | `secundario` |
| 86 | Juego de Posición Presión en campo contrario | Conservación de Balón | `ofensivo` |
| 87 | Juego de Posición 8 vs 4 Inicio Juego | Conservación de balón | `secundario` |
| 87 | Juego de Posición 8 vs 4 Inicio Juego | Conservación de balón | `ofensivo` |
| 88 | Juego de Posición Pasa Línea | Conservación de balón | `ofensivo` |
| 89 | Juego de Posición 5 vs 5 + 2 Comodines | Conservación de balón | `ofensivo` |
| 91 | Juego de Posición 8 vs 5 | Conservación de Balón | `ofensivo` |
| 92 | Juego de Posición en Doble área II | Conservación de balón | `ofensivo` |
| 94 | Juego de Posición 8 vs 8 Duelos Posicionales | Conservación de balón | `ofensivo` |
| 95 | Partido Condicionado 10 vs 10 | Conservación de balón | `secundario` |
| 95 | Partido Condicionado 10 vs 10 | Conservación de Balón | `ofensivo` |
| 96 | Partido Condicionado 11 vs 11 | Conservación de balón | `secundario` |
| 96 | Partido Condicionado 11 vs 11 | Conservación de Balón | `ofensivo` |
| 97 | Partido Condicionado 3 zonas | Conservación de Balón | `ofensivo` |
| 98 | Partido Condicionado Zonas laterales | Conservación de balón | `principal` |
| 98 | Partido Condicionado Zonas laterales | Conservación de balón | `ofensivo` |
| 99 | Partido Condicionado Organización Ofensiva | Conservación de balón | `secundario` |
| 99 | Partido Condicionado Organización Ofensiva | Conservación de balón | `ofensivo` |
| 100 | Partido Condicionado 4 Carriles | Conservación de Balón | `ofensivo` |
| 111 | Juego del Baloncesto | Conservación de balón | `principal` |
| 111 | Juego del Baloncesto | Conservacion de balón | `ofensivo` |
| 113 | Juego del Baloncesto en alturas | Conservacion de balón | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`1 vs 1`, `Amplitud`, `Aplicación de los movimientos del sistema (1-4-2-3-1)`, `Aplicación del sistema 1-4-4-2`, `Apoyos`, `Apoyos constantes`, `Asignación de marcas`, `Ataque por centro lateral`, `Ayudas`, `Ayudas defensivas`, `Balón aéreo`, `Basculaciones`, `Buscar líneas de pase`, `Buscar líneas de pase (sobre todo interiores)`, `Buscar pases interiores`, `Cambio de chip`, `Cambio de chip y desplazamiento`, `Cambio de dirección`, `Cambio de orientación`, `Cerrar líneas de pase`, `Cerrar líneas de pase interiores`, `Comunicación`, `Coordinación`, `Crear líneas de pase`, `Dejar de cara`, `Desmarque de ruptura`, `Disputa`, `En caso de robo, generar un 3 vs 2 contra miniporterías`, `Equilibrio`, `Escalonamiento`, `Evitar pases interiores`, `Finalización`, `Inicio de juego`, `Interceptación`, `Juego aéreo`, `Juego directo`, `Juego real`, `Jugar por fuera`, `Lograr llevar el balón de extremo a extremo`, `Líneas de pase`, `Líneas de pases interiores`, `Marcajes`, `Marcajes y basculaciones`, `Marcas y coberturas`, `Mejora técnica del control y el pase`, `Movilidad`, `Movilidad sin balón`, `Ocupación de los carriles exteriores`, `Ocupación racional`, `Organización defensiva`, `Organización ofensiva`, `Orientación de la presión`, `Pases interiores`, `Posesión`, `Presión`, `Presión alta`, `Presión en campo contrario`, `Pressing`, `Pressing tras pérdida`, `Progresión`, `Recuperación de balón y juego al más alejado`, `Regate`, `Repliegue`, `Resistencia aeróbica`, `Robar y progresar`, `Robo y cambio de zona`, `Robo y juego`, `Robo y juego fuera`, `Sacar de zona`, `Sacar de zona tras robo`, `Salir jugando`, `Si hay robo, juego a una pareja de fuera`, `Si hay robo, juego al lado contrario`, `Si robo, juego al triángulo contrario`, `Superar línea defensiva`, `Tapar pases interiores`, `Tercer hombre`, `Toma de decisiones`, `Trabajo de coordinación`, `Trabajo de propiocepción`, `Trabajo de resistencia aeróbica`, `Transiciones`, `Vigilancias`.

### Destinos candidatos existentes en el manifiesto

No tiene destino directo mientras se resuelve su relación con Posesión. El manifiesto sí contiene objetivos complementarios como Apoyo, Pase interior, Creación de líneas de pase y Progresión.

### Problema semántico

Puede confundirse con Posesión, pero su uso masivo exige comprobar si Posesión aporta una diferencia real o es una etiqueta duplicada.

### Interpretación

Los 58 ejercicios, principalmente rondos y juegos de posesión, repiten consignas de mantener, circular y encadenar pases. Funciona como principio ofensivo estable; sus 91 relaciones se deben a que frecuentemente aparece a la vez como principal/secundario y ofensivo/general.

### Opciones

- A. Mantener Conservación de balón y absorber Posesión.
- B. Mantener ambos y definir una frontera metodológica explícita.
- C. Dividir conservación, circulación y posesión en conceptos distintos.

### Recomendación

Mantener Conservación de balón como objetivo independiente y usarlo como candidato preferente para Posesión. La evidencia es consistente y transversal.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Desmarque de ruptura

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `ofensivo` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 69 | Juego de Posesión 4 vs 4 + 2 Comodines + Ataque | Desmarque de ruptura | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Cerrar líneas de pase`, `Conservación de balón`, `Crear líneas de pase`, `Líneas de pase`.

### Destinos candidatos existentes en el manifiesto

Ataque al espacio tras la línea defensiva y Superación de línea defensiva. No tiene destino directo mientras se decide su relación con Desmarque.

### Problema semántico

Debe comprobarse si es un subtipo suficientemente específico para no ser absorbido por Desmarque.

### Interpretación

En JPS4, después de cinco pases, se exige literalmente un desmarque de ruptura hacia portería para atacar rápido. El comportamiento es concreto y distinto de los movimientos variados de las ABP.

### Opciones

- A. Mantener Desmarque de ruptura independiente.
- B. Unificar con Desmarque.
- C. Unificar con Ataque al espacio tras la línea defensiva.

### Recomendación

Mantener Desmarque de ruptura como objetivo independiente. El único uso está explícitamente definido y no es un desmarque genérico.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Desmarques

### Uso actual

- Frecuencia del manifiesto: **6 ejercicios**.
- Ejercicios distintos afectados: **6**.
- Relaciones totales: **9**.
- Roles: `ofensivo` (6), `principal` (3).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 40 | Ataque/Defensa Transición y Repliegue | Desmarques | `ofensivo` |
| 101 | ABP Corner Ofensivo 1 | Desmarques | `principal` |
| 101 | ABP Corner Ofensivo 1 | Desmarques | `ofensivo` |
| 102 | ABP Corner Ofensivo 2 | Desmarques | `principal` |
| 102 | ABP Corner Ofensivo 2 | Desmarques | `ofensivo` |
| 103 | ABP Corner Ofensivo 3 | Desmarques | `principal` |
| 103 | ABP Corner Ofensivo 3 | Desmarques | `ofensivo` |
| 107 | ABP Falta lateral | Desmarques | `ofensivo` |
| 108 | ABP Falta Frontal | Desmarques | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Anticipación`, `Despeje`, `Despeje orientado`, `Dividir`, `Finalización`, `Interceptación`, `Marcajes`, `Remate de cabeza`, `Repliegue`, `Temporización`.

### Destinos candidatos existentes en el manifiesto

Ataque al espacio tras la línea defensiva y Superación de línea defensiva. Desmarque permanece sin destino aprobado.

### Problema semántico

Debe decidirse si el desmarque genérico se mantiene separado del subtipo Desmarque de ruptura.

### Interpretación

Cinco de los seis ejercicios son acciones a balón parado con cruces, apariciones cortas, movimientos a palos y frontal; AD7 también contiene un movimiento ofensivo de transición. No todos son rupturas, por lo que el concepto general conserva valor.

### Opciones

- A. Normalizar a Desmarque y mantenerlo independiente.
- B. Dividir cada movimiento por tipo de desmarque.
- C. Unificar todos con Desmarque de ruptura.

### Recomendación

Normalizar a Desmarque y mantenerlo separado de Desmarque de ruptura. Los movimientos de ABP demuestran que el término general es necesario.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Dividir

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `ofensivo` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 40 | Ataque/Defensa Transición y Repliegue | Dividir | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Desmarques`, `Interceptación`, `Repliegue`, `Temporización`.

### Destinos candidatos existentes en el manifiesto

Progresión y Temporización defensiva. Fijar o dividir al rival está en la taxonomía auditada, pero todavía no aparece como destino del manifiesto.

### Problema semántico

El verbo aislado no identifica quién divide a quién ni mediante qué conducta ofensiva.

### Interpretación

En AD7 aparece durante una transición con inferioridad ofensiva 2 contra 3 y defensores que temporizan. Es compatible con fijar o dividir rivales, pero el desarrollo no utiliza la palabra ni explica el mecanismo.

### Opciones

- A. Normalizar como Fijar o dividir al rival.
- B. Integrar en Progresión.
- C. Mantenerlo como principio propio.
- D. Retirarlo si no era una consigna intencional.

### Recomendación

Usar Fijar o dividir al rival únicamente si el entrenador confirma esa intención para AD7; mientras tanto mantener pendiente.

**Confianza provisional: MEDIA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Escalonamiento

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `defensivo` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 88 | Juego de Posición Pasa Línea | Escalonamiento | `defensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Basculaciones`, `Conservación de balón`, `Crear líneas de pase`, `Interceptación`, `Líneas de pase`.

### Destinos candidatos existentes en el manifiesto

Basculación defensiva, Interceptación, Organización defensiva y Cierre de líneas de pase.

### Problema semántico

La taxonomía auditada contemplaba Escalonamiento ofensivo, pero el único uso real es inequívocamente defensivo.

### Interpretación

JPC7 divide al equipo en dos líneas de tres; el bloque defensor se organiza, bascula, tapa líneas de pase y debe mantener un buen escalonamiento. Describe profundidad y relación entre líneas defensivas.

### Opciones

- A. Crear Escalonamiento defensivo como objetivo independiente.
- B. Integrarlo en Organización defensiva.
- C. Unificar con Basculación defensiva.

### Recomendación

Normalizar como Escalonamiento defensivo y mantenerlo independiente. No convertirlo en Escalonamiento ofensivo.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Juego

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `general` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 32 | Rueda de pase inicio juego | juego | `general` |

### Otros objetivos que aparecen en esos ejercicios

`Comunicación`, `Control orientado`, `Inicio`, `Inicio de juego`, `Mejora técnica del control, el pase y la conducción`, `Pared`, `Técnica`.

### Destinos candidatos existentes en el manifiesto

Inicio de juego, Técnica general, Control orientado y Pared.

### Problema semántico

Es un término incompleto y demasiado general, además de coexistir con Inicio e Inicio de juego en el mismo ejercicio.

### Interpretación

Solo aparece en RP13, una rueda titulada inicio de juego. La secuencia reproduce conexiones de salida y ya contiene Inicio de juego como principal. Juego no aporta una clasificación independiente recuperable.

### Opciones

- A. Unificar con Inicio de juego.
- B. Reubicarlo como texto contextual.
- C. Retirarlo del filtro conservando la relación original.

### Recomendación

Unificar con Inicio de juego y deduplicar únicamente la proyección V2 del ejercicio, sin borrar la relación original.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Juego aéreo

### Uso actual

- Frecuencia del manifiesto: **4 ejercicios**.
- Ejercicios distintos afectados: **4**.
- Relaciones totales: **5**.
- Roles: `defensivo` (4), `ofensivo` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 65 | ABP Defensa Faltas laterales | Juego Aéreo | `ofensivo` |
| 65 | ABP Defensa Faltas laterales | Juego Aéreo | `defensivo` |
| 85 | Juego de posición en Doble área | Juego Aéreo | `defensivo` |
| 98 | Partido Condicionado Zonas laterales | Juego Áereo | `defensivo` |
| 104 | ABP Corner Defensivo Marcaje | Juego Áereo | `defensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Amplitud`, `Ataque por centro lateral`, `Basculaciones`, `Conservación de balón`, `Despeje`, `Despeje orientado`, `Finalización`, `Marcajes`, `Marcajes y basculaciones`, `Marcas`, `Regate`.

### Destinos candidatos existentes en el manifiesto

Defensa de centros laterales, Despeje, Despeje orientado, Finalización y Marcaje. No tiene todavía destino directo aprobado.

### Problema semántico

Debe separarse del contexto Balón aéreo y de la acción técnica Remate de cabeza sin perder su dimensión de duelo aéreo.

### Interpretación

Los cuatro ejercicios trabajan faltas laterales, centros, córneres, despejes, marcajes y defensa del centro. Existe un patrón aéreo real y transversal, más amplio que rematar de cabeza.

### Opciones

- A. Mantener Juego aéreo como objetivo independiente.
- B. Dividirlo en duelo aéreo ofensivo y defensivo.
- C. Sustituirlo por Despeje, Defensa de centros y Remate de cabeza según ejercicio.

### Recomendación

Mantener Juego aéreo como objetivo independiente y complementario de las acciones específicas. No unificarlo con Remate de cabeza.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Movilidad

### Uso actual

- Frecuencia del manifiesto: **4 ejercicios**.
- Ejercicios distintos afectados: **4**.
- Relaciones totales: **6**.
- Roles: `ofensivo` (4), `principal` (1), `secundario` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 18 | Rondo 6 vs 2 | Movilidad | `ofensivo` |
| 71 | Juego de Posesión 6 vs 6 con la mano | Movilidad | `principal` |
| 71 | Juego de Posesión 6 vs 6 con la mano | Movilidad | `ofensivo` |
| 111 | Juego del Baloncesto | Movilidad | `secundario` |
| 111 | Juego del Baloncesto | Movilidad | `ofensivo` |
| 113 | Juego del Baloncesto en alturas | Movilidad | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Apoyos`, `Basculaciones`, `Cerrar líneas de pase`, `Comunicación`, `Conservación de balón`, `Crear líneas de pase`, `Equilibrio`, `Interceptación`, `Pases interiores`.

### Destinos candidatos existentes en el manifiesto

Apoyo y Creación de líneas de pase. Movilidad sin balón sigue pendiente y no aparece todavía como destino aprobado.

### Problema semántico

El nombre no indica fase ni relación con el balón, pero los cuatro ejercicios permiten comprobar su uso real.

### Interpretación

En JPS6, J3 y J5 se prohíbe avanzar con balón y se exige jugar y moverse; en R18 acompaña la creación de líneas de pase y los pases interiores. Los usos observados son movilidad ofensiva sin balón.

### Opciones

- A. Unificar con Movilidad sin balón.
- B. Crear Movilidad ofensiva como concepto más amplio.
- C. Reemplazar por Apoyo o Creación de líneas de pase según ejercicio.

### Recomendación

Unificar provisionalmente con Movilidad sin balón. Los cuatro contextos apuntan a movimiento posterior al pase o para ofrecer línea de pase.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Movilidad sin balón

### Uso actual

- Frecuencia del manifiesto: **2 ejercicios**.
- Ejercicios distintos afectados: **2**.
- Relaciones totales: **2**.
- Roles: `ofensivo` (2).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 1 | Rondo 3 vs 1 | Movilidad sin balón. | `ofensivo` |
| 4 | Rondo 3 vs 1 + Progresión | Movilidad sin balón | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Apoyos`, `Cerrar líneas de pase`, `Conservación de balón`, `Crear líneas de pase`, `Líneas de pase`, `Mejora técnica del control y el pase`, `Pressing`, `Progresión`, `Robar y progresar`.

### Destinos candidatos existentes en el manifiesto

No tiene destino asignado todavía. Entre los destinos ya presentes están Apoyo y Creación de líneas de pase; el candidato directo Movilidad sin balón permanece pendiente.

### Problema semántico

Se solapa nominalmente con Movilidad, pero es más específico y no debe fusionarse solo por semejanza léxica.

### Interpretación

En los dos rondos se exige reposicionarse continuamente alrededor del balón para ofrecer apoyos próximos y sostener la superioridad. El contenido confirma movimiento ofensivo sin balón, no movilidad física genérica.

### Opciones

- A. Mantener Movilidad sin balón como objetivo independiente.
- B. Integrarlo en un objetivo más amplio Movilidad ofensiva.
- C. Sustituirlo por Apoyo y/o Creación de líneas de pase en cada ejercicio.

### Recomendación

Mantener Movilidad sin balón como objetivo independiente. Es explícito en ambos desarrollos y aporta más precisión que Movilidad.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Posesión

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `general` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 48 | Circuito Resistencia Aeróbica + Posesión 4 vs 4 | POSESIÓN | `general` |

### Otros objetivos que aparecen en esos ejercicios

`Conservación de balón`, `Coordinación`, `Crear líneas de pase`, `Resistencia aeróbica`, `Trabajo de coordinación`, `Trabajo de propiocepción`, `Trabajo de resistencia aeróbica`.

### Destinos candidatos existentes en el manifiesto

No existe todavía un destino Posesión o Conservación de balón aprobado; ambos términos siguen en revisión.

### Problema semántico

Solo aparece una vez y exactamente en el mismo ejercicio que Conservación de balón, sin una función diferenciada.

### Interpretación

CT8 combina un circuito aeróbico con un juego 4 contra 4 denominado posesión. El ejercicio ya está relacionado con Conservación de balón y Crear líneas de pase; Posesión no añade una consigna diferente.

### Opciones

- A. Unificar con Conservación de balón.
- B. Mantener Posesión como formato de tarea.
- C. Conservarlo como objetivo diferente con una definición metodológica nueva.

### Recomendación

Unificar con Conservación de balón. En el único uso real es una etiqueta redundante del mismo bloque de tarea.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Presión alta

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `defensivo` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 6 | Rondo 4 vs 4 + 3 Comodines | Presion Alta | `defensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Buscar líneas de pase (sobre todo interiores)`, `Cerrar líneas de pase interiores`, `Conservación de balón`, `Lograr llevar el balón de extremo a extremo`, `Líneas de pase`, `Pases interiores`, `Recuperación de balón y juego al más alejado`.

### Destinos candidatos existentes en el manifiesto

Presión, Orientación de la presión, Cierre de líneas de pase interiores y Presión tras pérdida.

### Problema semántico

Solo aparece una vez y el desarrollo del ejercicio no describe de forma explícita altura, bloque ni zona de presión.

### Interpretación

En R6 figura como objetivo defensivo junto al cierre de líneas interiores, pero el texto desarrolla principalmente circulación ofensiva y limitaciones zonales. No hay evidencia textual suficiente para distinguir presión alta de presión en campo rival.

### Opciones

- A. Mantener Presión alta si el entrenador confirma el propósito.
- B. Unificar con Presión.
- C. Sustituir por Cierre de líneas de pase interiores.
- D. Corregir la clasificación específica de R6.

### Recomendación

Mantener pendiente y pedir confirmación sobre R6. El nombre por sí solo no justifica una categoría diferenciada.

**Confianza provisional: BAJA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Presión en campo contrario

### Uso actual

- Frecuencia del manifiesto: **2 ejercicios**.
- Ejercicios distintos afectados: **2**.
- Relaciones totales: **2**.
- Roles: `defensivo` (2).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 72 | Juego de Posesión Presión en campo contrario | Presión en campo contrario | `defensivo` |
| 86 | Juego de Posición Presión en campo contrario | Presión en campo contrario | `defensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Cambio de dirección`, `Cambio de orientación`, `Conservación de balón`, `Interceptación`, `Presión`, `Sacar de zona`.

### Destinos candidatos existentes en el manifiesto

Presión, Orientación de la presión, Cierre de líneas de pase y Presión tras pérdida. Presión en campo rival aún no aparece como destino utilizado.

### Problema semántico

Debe fijarse la denominación y comprobar su diferencia respecto a Presión alta.

### Interpretación

Los dos juegos sitúan expresamente a los defensores presionando en campo contrario después de un cambio o pérdida, con compañeros cerrando líneas o evitando el pase largo. La localización espacial está confirmada.

### Opciones

- A. Normalizar como Presión en campo rival y mantenerlo independiente.
- B. Unificar con Presión alta.
- C. Unificar con Presión dejando la zona como contexto.

### Recomendación

Normalizar como Presión en campo rival y mantenerlo separado de Presión alta hasta que esta última sea confirmada. Aquí la zona está explícita en ambos ejercicios.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Remate de cabeza

### Uso actual

- Frecuencia del manifiesto: **4 ejercicios**.
- Ejercicios distintos afectados: **4**.
- Relaciones totales: **4**.
- Roles: `general` (1), `ofensivo` (3).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 101 | ABP Corner Ofensivo 1 | Remate de Cabeza | `ofensivo` |
| 102 | ABP Corner Ofensivo 2 | Remate de Cabeza | `ofensivo` |
| 103 | ABP Corner Ofensivo 3 | Remate de Cabeza | `ofensivo` |
| 112 | Juego del Fútbol Tenis | Remate de cabeza | `general` |

### Otros objetivos que aparecen en esos ejercicios

`Activación`, `Anticipación`, `Comunicación`, `Desmarques`, `Despeje orientado`, `Finalización`, `Trabajo técnico`, `Técnica`.

### Destinos candidatos existentes en el manifiesto

Finalización, Juego aéreo, Ataque mediante centro lateral y Técnica general.

### Problema semántico

Es una acción técnica válida, pero los desarrollos asociados no confirman de forma uniforme que la finalización deba ejecutarse con la cabeza.

### Interpretación

Tres ejercicios son córneres ofensivos con centros y finalización, aunque no siempre especifican superficie de contacto. J4 es fútbol tenis y tampoco menciona remate de cabeza en sus reglas. La etiqueta original sugiere intención, pero el texto no basta para los cuatro casos.

### Opciones

- A. Mantener Remate de cabeza en los cuatro ejercicios.
- B. Mantenerlo solo en ejercicios confirmados por el entrenador.
- C. Sustituirlo por Finalización o Juego aéreo donde no sea obligatorio.
- D. Tratarlo como variante técnica.

### Recomendación

Revisar los cuatro ejercicios individualmente y mantener Remate de cabeza únicamente donde sea una ejecución exigida, no solo posible.

**Confianza provisional: MEDIA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Sacar de zona

### Uso actual

- Frecuencia del manifiesto: **6 ejercicios**.
- Ejercicios distintos afectados: **6**.
- Relaciones totales: **8**.
- Roles: `defensivo` (2), `ofensivo` (3), `principal` (2), `secundario` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 5 | Rondo 8 vs 4 | Sacar de zona | `ofensivo` |
| 17 | Rondo 4 vs 2 + Progresión | Sacar de zona | `principal` |
| 72 | Juego de Posesión Presión en campo contrario | Sacar de zona | `secundario` |
| 72 | Juego de Posesión Presión en campo contrario | Sacar de zona | `defensivo` |
| 73 | Juego de Posesión en Hexágono | Sacar de zona | `ofensivo` |
| 75 | Juego de Posesión 6 vs 6 + 2 Comodines | Sacar de zona | `principal` |
| 75 | Juego de Posesión 6 vs 6 + 2 Comodines | Sacar de zona | `defensivo` |
| 76 | Juego de Posesión 4 vs 4 + 1 Comodín | Sacar de zona | `ofensivo` |

### Otros objetivos que aparecen en esos ejercicios

`Amplitud`, `Basculaciones`, `Cambio de dirección`, `Cambio de orientación`, `Cerrar líneas de pase`, `Conservación de balón`, `Crear líneas de pase`, `Interceptación`, `Líneas de pase`, `Ocupación racional`, `Orientación de la presión`, `Presión`, `Presión en campo contrario`, `Pressing`, `Pressing tras pérdida`, `Progresión`, `Robo y cambio de zona`, `Sacar de zona tras robo`.

### Destinos candidatos existentes en el manifiesto

Salida de zona tras recuperación, Juego exterior tras recuperación, Cambio de orientación, Cambio de orientación tras recuperación y Progresión.

### Problema semántico

La misma etiqueta describe sacar al rival de una zona, mover el balón fuera y salir de una zona después de recuperar. Un mapeo global perdería el matiz de varios ejercicios.

### Interpretación

En R5 se relaciona con mover la posesión y desplazar al defensor; en R17, JPS7, JPS10 y JPS11 aparece ligado al robo y a salir o jugar fuera; en JPS8 forma parte del cambio hacia apoyos exteriores. No existe un significado único para sus seis ejercicios.

### Opciones

- A. Mantener Sacar de zona como objetivo genérico.
- B. Asignar un destino distinto por ejercicio.
- C. Dividir globalmente en objetivos ofensivos y transicionales.
- D. Conservar zona de salida como contexto.

### Recomendación

Resolver por relación y no por nombre global: usar Salida de zona tras recuperación o Juego exterior tras recuperación cuando hay robo, y revisar por separado los usos ofensivos.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Transiciones

### Uso actual

- Frecuencia del manifiesto: **1 ejercicios**.
- Ejercicios distintos afectados: **1**.
- Relaciones totales: **1**.
- Roles: `secundario` (1).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 89 | Juego de Posición 5 vs 5 + 2 Comodines | Transiciones | `secundario` |

### Otros objetivos que aparecen en esos ejercicios

`Cambio de orientación`, `Conservación de balón`, `Organización defensiva`, `Organización ofensiva`, `Orientación de la presión`.

### Destinos candidatos existentes en el manifiesto

Contraataque tras recuperación, Cambio de orientación tras recuperación, Juego tras recuperación, Progresión tras recuperación y Recuperación.

### Problema semántico

El plural es demasiado general, aunque el único ejercicio ofrece contexto suficiente para concretarlo.

### Interpretación

En JPC8, tras recuperar en campo propio se exige avanzar rápidamente al campo contrario y finalizar. El uso corresponde a una transición ofensiva/contraataque, no a transiciones genéricas en ambas direcciones.

### Opciones

- A. Mantener Transiciones como paraguas.
- B. Unificar con Contraataque tras recuperación.
- C. Dividir en recuperación, progresión y finalización.

### Recomendación

Unificar con Contraataque tras recuperación. El desarrollo define dirección, momento y finalidad con suficiente claridad.

**Confianza provisional: ALTA.**

### Decisión del entrenador

**PENDIENTE**

## Objetivo: Técnica

### Uso actual

- Frecuencia del manifiesto: **15 ejercicios**.
- Ejercicios distintos afectados: **15**.
- Relaciones totales: **15**.
- Roles: `principal` (2), `secundario` (13).

### Ejercicios donde aparece

| ID | Ejercicio | Objetivo original | Rol |
|---:|---|---|---|
| 20 | Rueda de pase tercer hombre en línea | Técnica | `secundario` |
| 31 | Rueda de pase pared | Técnica | `secundario` |
| 32 | Rueda de pase inicio juego | Técnica | `secundario` |
| 33 | Rueda de pase Calentamiento | Técnica | `principal` |
| 46 | Circuito Fuerza Resistencia II | Técnica | `secundario` |
| 54 | Circuito Resistencia Aeróbica + Centro y Remate | Técnica | `secundario` |
| 55 | Circuito Resistencia Aeróbica + Centro y Remate II | Técnica | `secundario` |
| 56 | Circuito Resistencia Aeróbica por parejas | Técnica | `secundario` |
| 59 | Circuito de Finalización 3 porterías | Técnica | `secundario` |
| 60 | Acción combinada Centro lateral | Técnica | `secundario` |
| 61 | Acción combinada con 2 delanteros | Técnica | `secundario` |
| 62 | Acción combinada con 2 delanteros II | Técnica | `secundario` |
| 63 | Acción combinada con 2 delanteros III | Técnica | `secundario` |
| 64 | Acción combinada con 1 delantero | Técnica | `secundario` |
| 112 | Juego del Fútbol Tenis | Técnica | `principal` |

### Otros objetivos que aparecen en esos ejercicios

`Activación`, `Balón de cara`, `Comunicación`, `Control orientado`, `Coordinación`, `Finalización`, `Fuerza resistencia`, `Inicio`, `Inicio de juego`, `Juego`, `Mejora técnica del control y el pase`, `Mejora técnica del control y el tiro`, `Mejora técnica del control, el pase y la conducción`, `Mejora técnica del pase`, `Pared`, `Puntería`, `Remate de cabeza`, `Resistencia aeróbica`, `Tercer hombre`, `Trabajo coordinativo`, `Trabajo de fuerza resistencia`, `Trabajo de propiocepción`, `Trabajo técnico`.

### Destinos candidatos existentes en el manifiesto

Técnica general, Control, Pase, Conducción, Tiro, Finalización, Regate y Precisión de finalización.

### Problema semántico

Es una etiqueta paraguas aplicada a 15 ejercicios con contenidos técnicos muy diferentes y, en la mayoría, ya existen objetivos específicos.

### Interpretación

Aparece en ruedas de pase, circuitos, acciones combinadas y fútbol tenis. Cubre pase, control, conducción, centro, remate y coordinación; no representa una acción única. En numerosos casos es secundaria frente a objetivos técnicos detallados.

### Opciones

- A. Unificar con Técnica general como objetivo paraguas.
- B. Retirarla cuando ya existen objetivos técnicos específicos.
- C. Sustituirla por asignaciones concretas ejercicio por ejercicio.

### Recomendación

Unificar con Técnica general solo como paraguas y conservar todos los objetivos técnicos específicos. Antes de activar el filtro, comprobar si puede omitirse en ejercicios ya cubiertos con precisión.

**Confianza provisional: MEDIA.**

### Decisión del entrenador

**PENDIENTE**

## Tabla resumen

| Objetivo | Frecuencia | Recomendación | Confianza | Decisión entrenador |
|---|---:|---|---|---|
| 1 vs 1 | 1 | Unificar denominación en Duelo 1 contra 1 | ALTA | PENDIENTE |
| Acumulación de gente | 1 | Unificar en Atraer y liberar espacio | ALTA | PENDIENTE |
| Agrupar gente | 1 | Unificar en Atraer y liberar espacio | ALTA | PENDIENTE |
| Asignación de tareas | 1 | Reubicar como contexto de roles y reglas | ALTA | PENDIENTE |
| Ayudas | 1 | Decisión específica sobre AD2 | BAJA | PENDIENTE |
| Ayudas defensivas | 1 | Confirmar si significa Cobertura defensiva | BAJA | PENDIENTE |
| Balón aéreo | 1 | Reubicar como contexto y confirmar JPS1 | BAJA | PENDIENTE |
| Cambio de chip | 3 | Dividir por ejercicio en transiciones concretas | ALTA | PENDIENTE |
| Cambio de chip y desplazamiento | 1 | Unificar con Presión tras pérdida | ALTA | PENDIENTE |
| Colocación | 1 | Unificar con Posicionamiento | MEDIA | PENDIENTE |
| Conservación de balón | 58 | Mantener; candidato canónico frente a Posesión | ALTA | PENDIENTE |
| Desmarque de ruptura | 1 | Mantener Desmarque de ruptura | ALTA | PENDIENTE |
| Desmarques | 6 | Unificar plural en Desmarque; mantener separado de ruptura | ALTA | PENDIENTE |
| Dividir | 1 | Confirmar Fijar o dividir al rival en AD7 | MEDIA | PENDIENTE |
| Escalonamiento | 1 | Unificar denominación en Escalonamiento defensivo | ALTA | PENDIENTE |
| Juego | 1 | Unificar con Inicio de juego | ALTA | PENDIENTE |
| Juego aéreo | 4 | Mantener Juego aéreo independiente | ALTA | PENDIENTE |
| Movilidad | 4 | Unificar con Movilidad sin balón | ALTA | PENDIENTE |
| Movilidad sin balón | 2 | Mantener Movilidad sin balón | ALTA | PENDIENTE |
| Posesión | 1 | Unificar con Conservación de balón | ALTA | PENDIENTE |
| Presión alta | 1 | Confirmar el propósito real de R6 | BAJA | PENDIENTE |
| Presión en campo contrario | 2 | Unificar denominación en Presión en campo rival | ALTA | PENDIENTE |
| Remate de cabeza | 4 | Decidir por ejercicio según ejecución exigida | MEDIA | PENDIENTE |
| Sacar de zona | 6 | Dividir por ejercicio según fase | ALTA | PENDIENTE |
| Transiciones | 1 | Unificar con Contraataque tras recuperación | ALTA | PENDIENTE |
| Técnica | 15 | Unificar con Técnica general, sin sustituir objetivos específicos | MEDIA | PENDIENTE |

## Clasificación provisional de los 26 casos

### 1. Probablemente mantener

- Conservación de balón
- Desmarque de ruptura
- Juego aéreo
- Movilidad sin balón

### 2. Probablemente unificar

- 1 vs 1
- Acumulación de gente
- Agrupar gente
- Cambio de chip y desplazamiento
- Colocación
- Desmarques
- Escalonamiento
- Juego
- Movilidad
- Posesión
- Presión en campo contrario
- Transiciones
- Técnica

### 3. Probablemente dividir

- Cambio de chip
- Sacar de zona

### 4. Probablemente reubicar como contexto/formato

- Asignación de tareas
- Balón aéreo

### 5. Requiere decisión específica del entrenador

- Ayudas
- Ayudas defensivas
- Dividir
- Presión alta
- Remate de cabeza

## Casos que podrían pasar a MANTENER con confianza alta

El análisis del contenido real aporta evidencia suficiente para proponer que estos conceptos permanezcan independientes. La decisión formal continúa pendiente:

- **Conservación de balón**: Mantener; candidato canónico frente a Posesión.
- **Desmarque de ruptura**: Mantener Desmarque de ruptura.
- **Juego aéreo**: Mantener Juego aéreo independiente.
- **Movilidad sin balón**: Mantener Movilidad sin balón.

## Estado de validación

- Objetivos `REVISAR` analizados: **26 de 26**.
- Todos incluyen frecuencia, relaciones, roles y relaciones originales.
- Todas las decisiones del entrenador permanecen en **PENDIENTE**.
- Este informe no modifica ni activa la taxonomía V2.

