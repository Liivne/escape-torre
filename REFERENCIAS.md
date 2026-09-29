# Referencias

## Código tomado de terceros

Todo el código de terceros está en `busqueda.py` y proviene de **Red Blob Games** (Amit Patel). Fecha de consulta: 28-09-2026.

### `implementation.py` de Red Blob Games

- **URL:** https://www.redblobgames.com/pathfinding/a-star/implementation.py
- **Explicación del autor:** https://www.redblobgames.com/pathfinding/a-star/implementation.html
- **Licencia:** Apache 2.0. El encabezado del archivo original dice:
  > Copyright 2014 Red Blob Games <redblobgames@gmail.com>
  > Feel free to use this code in your own projects, including commercial projects
  > License: Apache v2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>

| Función en `busqueda.py` | Uso en la tarea | Modificaciones |
|---|---|---|
| `Queue` | Frontera FIFO de BFS | Ninguna |
| `PriorityQueue` | Frontera de UCS, A* y Greedy | Ninguna |
| `reconstruct_path` | Arma el camino desde `came_from` | Se quitaron los comentarios. El original agradece a Jaiden Mispy (@m1sp) por esta versión |
| `heuristic` | Distancia Manhattan de A* y Greedy | Ninguna |
| `breadth_first_search` | **BFS** (búsqueda no informada) | Ninguna |
| `dijkstra_search` | **UCS / Dijkstra** (búsqueda no informada) | Ninguna |
| `a_star_search` | **A\*** (búsqueda informada) | Ninguna |

No se copiaron las clases de ejemplo del original (`SquareGrid`, `GridWithWeights`, `draw_grid`, etc.), porque el grafo lo pone el entorno propio de la tarea.

### Página de introducción de Red Blob Games

- **URL:** https://www.redblobgames.com/pathfinding/a-star/introduction.html, sección *Heuristic search*
- **Licencia:** la página no declara una licencia de software; solo indica "Copyright © Red Blob Games".

| Función en `busqueda.py` | Uso en la tarea | Modificaciones |
|---|---|---|
| `greedy_best_first_search` | **Greedy Best-First** (búsqueda informada) | En la página el código aparece como un fragmento suelto. Se envolvió en una función con la misma firma que las demás, `(graph, start, goal)`, que retorna `came_from`. El cuerpo es el original |

### Cómo se conecta con el resto del proyecto

Las funciones tomadas no se modificaron. Se adaptaron a la tarea desde afuera, en `simulacion.py`, con código propio:

- **`Grafo`** entrega la interfaz que espera el original: `neighbors(p)` y `cost(a, b)`.
  - `neighbors` devuelve las celdas vecinas transitables (sin muro ni fuego) y cuenta los nodos expandidos.
  - `cost` aplica el costo penalizado por congestión y por cercanía al fuego.
- **`buscar`** llama a la función elegida. Si retorna `(came_from, cost_so_far)`, se queda solo con `came_from`, y luego arma el camino con `reconstruct_path`.

## Código propio del grupo

Estos archivos son implementación propia: `entorno.py`, `simulacion.py`, `genetico.py`, `mapas.py` y `main.py`.

El algoritmo genético de `genetico.py` es implementación propia, como exige el enunciado. Su única dependencia de código de terceros es `a_star_search`, que se usa para generar las rutas candidatas de cada agente.

## Uso de IA generativa

El código propio y la integración del código de Red Blob Games se hicieron con asistencia de **Claude (Anthropic), modelo Claude Opus 5.5**, en septiembre de 2026, a partir de las especificaciones del grupo:

- algoritmos por implementar;
- estructura del cromosoma: ruta candidata y retardo de salida por agente;
- heurística Manhattan;
- fuego modelado en el costo y no en la heurística.
