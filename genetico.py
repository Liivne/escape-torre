# Implementación propia; las rutas candidatas usan a_star_search de Red Blob Games (ver busqueda.py).
import random
from collections import Counter
from dataclasses import dataclass
from statistics import mean

from simulacion import Grafo, PlanificadorBusqueda, Simulacion, buscar


@dataclass
class ParametrosAG:
    poblacion: int = 20
    generaciones: int = 15
    p_cruce: float = 0.9
    p_mutacion: float = 0.1
    torneo: int = 3
    elite: int = 2
    retardo_max: int = 8
    penalizaciones: tuple = (0.0, 1.0, 3.0, 6.0)
    escenarios: int = 1


def rutas_candidatas(entorno, origen, penalizaciones, beta_fuego):
    rutas = []
    uso = Counter()
    for w in penalizaciones:
        def costo(p, q, w=w):
            return 1.0 + w * uso[q] + beta_fuego * entorno.peligro(q)

        camino = buscar("astar", Grafo(entorno, costo), origen, entorno.salida)
        if not camino:
            break
        ruta = camino[1:]
        if ruta not in rutas:
            rutas.append(ruta)
        uso.update(ruta[:-1])
    return rutas or [[]]


def aptitud(resultado, t_max):
    despeje = resultado.tiempo_despeje if resultado.tiempo_despeje is not None else t_max
    promedio = mean(resultado.tiempos) if resultado.tiempos else t_max
    return 1000.0 * resultado.evacuados - despeje - 0.1 * promedio


class AlgoritmoGenetico:
    def __init__(self, parametros, rng):
        self.p = parametros
        self.rng = rng

    def _aleatorio(self, n_rutas):
        return tuple(
            (self.rng.randrange(n), self.rng.randint(0, self.p.retardo_max // 2))
            for n in n_rutas
        )

    def _torneo(self, poblacion, valores):
        elegidos = self.rng.sample(range(len(poblacion)), self.p.torneo)
        return poblacion[max(elegidos, key=lambda i: valores[i])]

    def _cruzar(self, a, b):
        if self.rng.random() >= self.p.p_cruce:
            return a, b
        hijo1, hijo2 = [], []
        for ga, gb in zip(a, b):
            if self.rng.random() < 0.5:
                ga, gb = gb, ga
            hijo1.append(ga)
            hijo2.append(gb)
        return tuple(hijo1), tuple(hijo2)

    def _mutar(self, cromosoma, n_rutas):
        genes = []
        for (ruta, retardo), n in zip(cromosoma, n_rutas):
            if self.rng.random() < self.p.p_mutacion:
                if n > 1 and self.rng.random() < 0.5:
                    ruta = self.rng.choice([i for i in range(n) if i != ruta])
                else:
                    retardo = min(self.p.retardo_max, max(0, retardo + self.rng.choice((-2, -1, 1, 2))))
            genes.append((ruta, retardo))
        return tuple(genes)

    def optimizar(self, evaluar, n_rutas):
        cache = {}

        def f(c):
            if c not in cache:
                cache[c] = evaluar(c)
            return cache[c]

        poblacion = [tuple((0, 0) for _ in n_rutas)]
        while len(poblacion) < self.p.poblacion:
            poblacion.append(self._aleatorio(n_rutas))
        historial = []
        for _ in range(self.p.generaciones):
            valores = [f(c) for c in poblacion]
            historial.append(max(valores))
            ranking = sorted(range(len(poblacion)), key=lambda i: valores[i], reverse=True)
            nueva = [poblacion[i] for i in ranking[: self.p.elite]]
            while len(nueva) < self.p.poblacion:
                a = self._torneo(poblacion, valores)
                b = self._torneo(poblacion, valores)
                for hijo in self._cruzar(a, b):
                    if len(nueva) < self.p.poblacion:
                        nueva.append(self._mutar(hijo, n_rutas))
            poblacion = nueva
        valores = [f(c) for c in poblacion]
        mejor = max(range(len(poblacion)), key=lambda i: valores[i])
        historial.append(valores[mejor])
        return poblacion[mejor], historial


class PlanificadorFijo:
    replanifica_por_bloqueo = False
    replanifica_por_fuego = False

    def __init__(self, rutas=None, cromosoma=None):
        self.rutas = rutas
        self.cromosoma = cromosoma
        self.respaldo = PlanificadorBusqueda("astar")
        self.entregados = set()

    def preparar(self, sim):
        for agente, (_, retardo) in zip(sim.agentes, self.cromosoma):
            agente.retardo = retardo

    def planificar(self, sim, agente):
        if agente.id not in self.entregados:
            self.entregados.add(agente.id)
            ruta = self.rutas[agente.id][self.cromosoma[agente.id][0]]
            if ruta and not any(q in sim.entorno.fuego for q in ruta):
                return list(ruta)
        return self.respaldo.planificar(sim, agente)


class PlanificadorGenetico(PlanificadorFijo):
    def __init__(self, parametros=None, semilla=0):
        super().__init__()
        self.pag = parametros or ParametrosAG()
        self.semilla = semilla
        self.historial = []

    def preparar(self, sim):
        rng = random.Random(self.semilla)
        e = sim.entorno
        (foco,) = e.fuego
        self.rutas = [
            rutas_candidatas(e, a.pos, self.pag.penalizaciones, sim.p.beta_fuego)
            for a in sim.agentes
        ]
        escenarios = [rng.randrange(2**31) for _ in range(self.pag.escenarios)]

        def evaluar(cromosoma):
            return mean(
                aptitud(
                    Simulacion(e.mapa, PlanificadorFijo(self.rutas, cromosoma), s, sim.p, foco=foco).ejecutar(),
                    sim.p.t_max,
                )
                for s in escenarios
            )

        ag = AlgoritmoGenetico(self.pag, rng)
        self.cromosoma, self.historial = ag.optimizar(evaluar, [len(r) for r in self.rutas])
        super().preparar(sim)
