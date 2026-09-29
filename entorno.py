from collections import deque
from dataclasses import dataclass

MURO = "#"
SALIDA = "S"
PERSONA = "P"
FOCO = "F"
MOVIMIENTOS = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass(frozen=True)
class Mapa:
    nombre: str
    filas: tuple
    k_fuego: int
    p_fuego: float
    capacidad: int

    @property
    def alto(self):
        return len(self.filas)

    @property
    def ancho(self):
        return len(self.filas[0])

    def celdas(self, simbolo):
        return [
            (f, c)
            for f, fila in enumerate(self.filas)
            for c, s in enumerate(fila)
            if s == simbolo
        ]


class Entorno:
    def __init__(self, mapa, rng, radio_fuego=3, foco=None):
        self.mapa = mapa
        self.rng = rng
        self.radio_fuego = radio_fuego
        self.muros = frozenset(mapa.celdas(MURO))
        (self.salida,) = mapa.celdas(SALIDA)
        self.fuego = {foco if foco is not None else rng.choice(mapa.celdas(FOCO))}
        self._capacidad = {}
        self._actualizar_distancias()

    def capacidad(self, p):
        if p not in self._capacidad:
            angosta = sum(1 for _ in self.adyacentes(p)) <= 2
            self._capacidad[p] = 1 if angosta else self.mapa.capacidad
        return self._capacidad[p]

    def dentro(self, p):
        return 0 <= p[0] < self.mapa.alto and 0 <= p[1] < self.mapa.ancho

    def adyacentes(self, p):
        for df, dc in MOVIMIENTOS:
            q = (p[0] + df, p[1] + dc)
            if self.dentro(q) and q not in self.muros:
                yield q

    def transitable(self, p):
        return self.dentro(p) and p not in self.muros and p not in self.fuego

    def vecinos(self, p):
        for q in self.adyacentes(p):
            if q not in self.fuego:
                yield q

    def h(self, p):
        return abs(p[0] - self.salida[0]) + abs(p[1] - self.salida[1])

    def peligro(self, p):
        d = self.distancia_fuego.get(p)
        if d is None:
            return 0
        return self.radio_fuego + 1 - d

    def propagar(self, t):
        if t % self.mapa.k_fuego != 0:
            return False
        nuevas = {
            q
            for f in self.fuego
            for q in self.adyacentes(f)
            if q not in self.fuego
            and q != self.salida
            and self.rng.random() < self.mapa.p_fuego
        }
        if not nuevas:
            return False
        self.fuego |= nuevas
        self._actualizar_distancias()
        return True

    def _actualizar_distancias(self):
        distancia = {f: 0 for f in self.fuego}
        cola = deque(self.fuego)
        while cola:
            p = cola.popleft()
            if distancia[p] == self.radio_fuego:
                continue
            for q in self.adyacentes(p):
                if q not in distancia:
                    distancia[q] = distancia[p] + 1
                    cola.append(q)
        self.distancia_fuego = distancia
