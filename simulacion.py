import random
from collections import Counter
from dataclasses import dataclass, field

from busqueda import ALGORITMOS, reconstruct_path
from entorno import PERSONA, Entorno


@dataclass
class Parametros:
    alfa: float = 2.0
    lambda_flujo: float = 0.25
    beta_fuego: float = 2.0
    paciencia: int = 2
    t_max: int = 300


def penalizacion(ocupacion, capacidad, alfa):
    return alfa * (max(ocupacion, 0) / capacidad) ** 2


@dataclass
class Agente:
    id: int
    pos: tuple
    plan: list = field(default_factory=list)
    retardo: int = 0
    estado: str = "activo"
    t_salida: int | None = None
    bloqueado: int = 0


@dataclass
class ResultadoSimulacion:
    total: int
    evacuados: int
    bajas: int
    tiempo_despeje: int | None
    tiempos: list
    expandidos: int

    @property
    def supervivencia(self):
        return self.evacuados / self.total


class Simulacion:
    def __init__(self, mapa, planificador, semilla, parametros=None, foco=None):
        self.rng = random.Random(semilla)
        self.entorno = Entorno(mapa, self.rng, foco=foco)
        self.p = parametros or Parametros()
        self.planificador = planificador
        self.agentes = [Agente(i, pos) for i, pos in enumerate(mapa.celdas(PERSONA))]
        self.ocupacion = Counter(a.pos for a in self.agentes)
        self.flujo = Counter()
        self.t = 0
        self.expandidos = 0
        self.fuego_cambio = False

    def activos(self):
        return [a for a in self.agentes if a.estado == "activo"]

    def costo(self, agente):
        e = self.entorno

        def c(p, q):
            if q == e.salida:
                return 1.0
            ocupacion = self.ocupacion[q] - (q == agente.pos) + self.p.lambda_flujo * self.flujo[q]
            return (
                1.0
                + penalizacion(ocupacion, e.capacidad(q), self.p.alfa)
                + self.p.beta_fuego * e.peligro(q)
            )

        return c

    def asignar_plan(self, agente, plan):
        self.flujo.subtract(agente.plan)
        agente.plan = list(plan)
        self.flujo.update(agente.plan)

    def replanificar(self, agente):
        self.asignar_plan(agente, [])
        self.asignar_plan(agente, self.planificador.planificar(self, agente))
        agente.bloqueado = 0
        if not agente.plan:
            self._retirar(agente, "baja")

    def _necesita_plan(self, agente):
        if not agente.plan:
            return True
        if any(q in self.entorno.fuego for q in agente.plan):
            return True
        if self.fuego_cambio and self.planificador.replanifica_por_fuego:
            return True
        return (
            self.planificador.replanifica_por_bloqueo
            and agente.bloqueado >= self.p.paciencia
        )

    def _por_cercania(self):
        return sorted(self.activos(), key=lambda a: self.entorno.h(a.pos))

    def _retirar(self, agente, estado):
        self.ocupacion[agente.pos] -= 1
        self.asignar_plan(agente, [])
        agente.estado = estado

    def _mover(self, agente):
        if self.t <= agente.retardo or not agente.plan:
            return
        e = self.entorno
        sig = agente.plan[0]
        if sig in e.fuego:
            agente.bloqueado += 1
        elif sig == e.salida:
            agente.t_salida = self.t
            self._retirar(agente, "evacuado")
        elif self.ocupacion[sig] < e.capacidad(sig):
            self.ocupacion[agente.pos] -= 1
            self.ocupacion[sig] += 1
            agente.pos = sig
            agente.plan.pop(0)
            self.flujo[sig] -= 1
            agente.bloqueado = 0
        else:
            agente.bloqueado += 1

    def paso(self):
        self.t += 1
        for agente in self._por_cercania():
            if self.t > agente.retardo and self._necesita_plan(agente):
                self.replanificar(agente)
        self.fuego_cambio = False
        for agente in self._por_cercania():
            self._mover(agente)
        if self.entorno.propagar(self.t):
            self.fuego_cambio = True
            for agente in self.activos():
                if agente.pos in self.entorno.fuego:
                    self._retirar(agente, "baja")

    def ejecutar(self):
        self.planificador.preparar(self)
        for agente in self._por_cercania():
            self.replanificar(agente)
        while self.activos() and self.t < self.p.t_max:
            self.paso()
        for agente in self.activos():
            self._retirar(agente, "baja")
        tiempos = [a.t_salida for a in self.agentes if a.estado == "evacuado"]
        return ResultadoSimulacion(
            total=len(self.agentes),
            evacuados=len(tiempos),
            bajas=len(self.agentes) - len(tiempos),
            tiempo_despeje=max(tiempos) if tiempos else None,
            tiempos=tiempos,
            expandidos=self.expandidos,
        )


class Grafo:
    def __init__(self, entorno, costo):
        self.entorno = entorno
        self.costo = costo
        self.expandidos = 0

    def neighbors(self, p):
        self.expandidos += 1
        return list(self.entorno.vecinos(p))

    def cost(self, a, b):
        return self.costo(a, b)


def buscar(nombre, grafo, inicio, meta):
    salida = ALGORITMOS[nombre](grafo, inicio, meta)
    came_from = salida[0] if isinstance(salida, tuple) else salida
    return reconstruct_path(came_from, inicio, meta)


class PlanificadorBusqueda:
    replanifica_por_bloqueo = True
    replanifica_por_fuego = True

    def __init__(self, nombre):
        self.nombre = nombre

    def preparar(self, sim):
        pass

    def planificar(self, sim, agente):
        e = sim.entorno
        grafo = Grafo(e, sim.costo(agente))
        camino = buscar(self.nombre, grafo, agente.pos, e.salida)
        sim.expandidos += grafo.expandidos
        return camino[1:]
