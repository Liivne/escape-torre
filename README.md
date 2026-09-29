# Tarea 1: Escape de la Torre

Simulación de evacuación multiagente en una grilla con propagación de fuego y congestión en pasillos. Se comparan cinco estrategias de navegación:

| Paradigma | Algoritmo | Clave en la línea de comandos |
|---|---|---|
| Búsqueda no informada | Búsqueda en anchura (BFS) | `bfs` |
| Búsqueda no informada | Costo uniforme (UCS / Dijkstra) | `ucs` |
| Búsqueda informada | A* con distancia Manhattan | `astar` |
| Búsqueda informada | Greedy Best-First con distancia Manhattan | `greedy` |
| Optimización bioinspirada | Algoritmo genético (implementación propia) | `genetico` |

## Requisitos

- **Python 3.12 o superior.** El código de búsqueda usa la sintaxis de genéricos `def f[T](...)`. Se probó con Python 3.14.
- **Simulación y benchmark:** solo biblioteca estándar.
- **Gráficos:** `matplotlib` y `numpy`.

```bash
pip install -r requirements.txt
```

## Estructura

| Archivo | Contenido |
|---|---|
| `busqueda.py` | BFS, UCS, A* y Greedy, tomados de Red Blob Games (ver `REFERENCIAS.md`) |
| `genetico.py` | Algoritmo genético: cromosoma = (ruta candidata, retardo de salida) por agente |
| `entorno.py` | Grilla, muros, salida, fuego y capacidad de cada celda |
| `simulacion.py` | Bucle de turnos: movimiento, congestión, replanificación, propagación del fuego y bajas |
| `mapas.py` | Los tres mapas y sus parámetros de fuego |
| `main.py` | Benchmark secuencial con tabla por consola |
| `benchmark.py` | Benchmark en paralelo que guarda los resultados crudos en CSV |
| `graficos.py` | Genera las figuras (PDF/PNG) y la tabla LaTeX a partir del CSV |
| `REFERENCIAS.md` | Origen del código de terceros, licencias y declaración de uso de IA |

## Cómo ejecutar

Todos los comandos se ejecutan desde la carpeta del proyecto.

### 1. Prueba rápida por consola

Corre los algoritmos pedidos y muestra, por mapa, la supervivencia, el tiempo de despeje (media, desviación, mínimo y máximo) y los nodos expandidos:

```bash
python main.py --iteraciones 20
```

Opciones:

| Opción | Valor por defecto | Descripción |
|---|---|---|
| `--mapas` | `1 2 3` | Mapas a evaluar |
| `--algoritmos` | todos | Subconjunto de `bfs ucs astar greedy genetico` |
| `--iteraciones` | `200` | Iteraciones por combinación de mapa y algoritmo |
| `--poblacion` | `20` | Tamaño de población del algoritmo genético |
| `--generaciones` | `15` | Generaciones del algoritmo genético |

Ejemplo, solo A* y BFS en el Mapa 1:

```bash
python main.py --mapas 1 --algoritmos bfs astar --iteraciones 50
```

### 2. Benchmark completo

```bash
python benchmark.py --iteraciones 200 --iteraciones-genetico 80
```

- **Paralelismo:** usa todos los núcleos menos uno. Se cambia con `--procesos N`.
- **`resultados/corridas.csv`:** una fila por corrida, con mapa, algoritmo, semilla, total de agentes, evacuados, supervivencia, tiempo de despeje, nodos expandidos y segundos.
- **`resultados/historial_genetico.json`:** la aptitud del mejor individuo en cada generación.
- **Iteraciones del genético:** van por separado porque cada corrida simula miles de evacuaciones para evaluar la aptitud. El enunciado exige un mínimo de 80.

La semilla `s` fija el foco inicial del fuego y su propagación. Con la misma semilla, todos los algoritmos enfrentan exactamente el mismo incendio, así que la comparación es pareada.

### 3. Gráficos y tabla para LaTeX

```bash
python graficos.py
```

Lee `resultados/` y escribe en `figuras/`:

- `supervivencia.pdf`: supervivencia media con intervalo de confianza del 95 %.
- `tiempo_despeje.pdf`: distribución del tiempo de despeje (boxplot).
- `nodos_expandidos.pdf`: costo computacional de las búsquedas.
- `convergencia_genetico.pdf`: mejora de aptitud por generación.
- `tabla_resultados.tex`: tabla con n, supervivencia, media, desviación estándar, mínimo y máximo. Requiere `\usepackage{booktabs}`.
- `figuras.tex`: los entornos `figure` listos para `\input{figuras/figuras.tex}`. Requiere `\usepackage{graphicx}`.

Cada figura también se guarda en PNG a 300 dpi.

## Mapas

| Símbolo | Significado |
|---|---|
| `#` | Muro |
| `.` | Celda libre |
| `P` | Posición inicial de una persona |
| `S` | Salida (única por piso) |
| `F` | Posible foco inicial del fuego (se sortea uno por semilla) |

| Mapa | Descripción | Personas | Fuego |
|---|---|---|---|
| 1 | Cuello de botella: un salón que desemboca en tres pasillos angostos | 34 | se propaga cada turno, p = 0,5 |
| 2 | Laberinto corporativo: salas conectadas por puertas y pasillos ciegos | 44 | cada 2 turnos, p = 0,6 |
| 3 | Dispersión abierta: pocos muros, múltiples rutas | 29 | cada turno, p = 0,5 |

Reglas de la simulación:

- **Movimiento:** ortogonal o esperar.
- **Capacidad:** las celdas de pasillo (dos o menos vecinos libres) admiten 1 persona y el resto 2.
- **Costo de moverse a una celda:** `1 + α·(ocupación/capacidad)² + β·peligro_fuego`. Como el costo mínimo es 1, la distancia Manhattan sigue siendo admisible para A*.
- **Fuego:** cada `k` turnos se propaga a las celdas vecinas con probabilidad `p`. Una persona alcanzada por el fuego, o que se queda sin camino a la salida, cuenta como baja.
