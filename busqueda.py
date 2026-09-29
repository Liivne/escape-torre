# Fuente: https://www.redblobgames.com/pathfinding/a-star/implementation.py (Red Blob Games, Apache 2.0)
# greedy_best_first_search: https://www.redblobgames.com/pathfinding/a-star/introduction.html (Red Blob Games)
from __future__ import annotations

import collections
import heapq


class Queue[Element]:
    def __init__(self):
        self.elements = collections.deque[Element]()

    def empty(self) -> bool:
        return not self.elements

    def put(self, element: Element):
        self.elements.append(element)

    def get(self) -> Element:
        return self.elements.popleft()


class PriorityQueue[Element]:
    def __init__(self):
        self.elements: list[tuple[float, Element]] = []

    def empty(self) -> bool:
        return not self.elements

    def put(self, element: Element, priority: float):
        heapq.heappush(self.elements, (priority, element))

    def get(self) -> Element:
        return heapq.heappop(self.elements)[1]


def reconstruct_path[Location](
                     came_from: dict[Location, Location],
                     start: Location, goal: Location
      ) -> list[Location]:

    current: Location = goal
    path: list[Location] = []
    if goal not in came_from:
        return []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path


def heuristic(a: GridLocation, b: GridLocation) -> float:
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)


def breadth_first_search[Location](graph: Graph[Location], start: Location, goal: Location):
    frontier = Queue[Location]()
    frontier.put(start)
    came_from: dict[Location, Location] = {}
    came_from[start] = start

    while not frontier.empty():
        current: Location = frontier.get()

        if current == goal:
            break

        for next in graph.neighbors(current):
            if next not in came_from:
                frontier.put(next)
                came_from[next] = current

    return came_from


def dijkstra_search[Location](graph: WeightedGraph[Location], start: Location, goal: Location):
    frontier = PriorityQueue[Location]()
    frontier.put(start, 0)
    came_from: dict[Location, Location] = {}
    cost_so_far: dict[Location, float] = {}
    came_from[start] = start
    cost_so_far[start] = 0

    while not frontier.empty():
        current: Location = frontier.get()

        if current == goal:
            break

        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost
                frontier.put(next, priority)
                came_from[next] = current

    return came_from, cost_so_far


def a_star_search[Location](graph: WeightedGraph[Location], start: Location, goal: Location):
    frontier = PriorityQueue[Location]()
    frontier.put(start, 0)
    came_from: dict[Location, Location] = {}
    cost_so_far: dict[Location, float] = {}
    came_from[start] = start
    cost_so_far[start] = 0

    while not frontier.empty():
        current: Location = frontier.get()

        if current == goal:
            break

        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(next, goal)
                frontier.put(next, priority)
                came_from[next] = current

    return came_from, cost_so_far


def greedy_best_first_search[Location](graph: Graph[Location], start: Location, goal: Location):
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from: dict[Location, Location] = dict()
    came_from[start] = None

    while not frontier.empty():
        current = frontier.get()

        if current == goal:
            break

        for next in graph.neighbors(current):
            if next not in came_from:
                priority = heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current

    return came_from


ALGORITMOS = {
    "bfs": breadth_first_search,
    "ucs": dijkstra_search,
    "astar": a_star_search,
    "greedy": greedy_best_first_search,
}
