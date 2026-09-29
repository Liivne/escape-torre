import argparse
from statistics import mean, stdev

from genetico import ParametrosAG, PlanificadorGenetico
from mapas import MAPAS
from simulacion import PlanificadorBusqueda, Simulacion

NOMBRES = ("bfs", "ucs", "astar", "greedy", "genetico")


def planificador(nombre, semilla, pag):
    if nombre == "genetico":
        return PlanificadorGenetico(pag, semilla)
    return PlanificadorBusqueda(nombre)


def experimento(mapa, nombre, iteraciones, pag):
    resultados = [
        Simulacion(mapa, planificador(nombre, s, pag), s).ejecutar()
        for s in range(iteraciones)
    ]
    despejes = [r.tiempo_despeje for r in resultados if r.tiempo_despeje is not None]
    return {
        "supervivencia": mean(r.supervivencia for r in resultados),
        "media": mean(despejes) if despejes else None,
        "desv": stdev(despejes) if len(despejes) > 1 else None,
        "min": min(despejes) if despejes else None,
        "max": max(despejes) if despejes else None,
        "expandidos": mean(r.expandidos for r in resultados),
    }


def fmt(x, dec=1):
    return "sin dato" if x is None else f"{x:.{dec}f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapas", nargs="+", default=list(MAPAS))
    parser.add_argument("--algoritmos", nargs="+", default=list(NOMBRES), choices=NOMBRES)
    parser.add_argument("--iteraciones", type=int, default=200)
    parser.add_argument("--poblacion", type=int, default=ParametrosAG.poblacion)
    parser.add_argument("--generaciones", type=int, default=ParametrosAG.generaciones)
    args = parser.parse_args()
    pag = ParametrosAG(poblacion=args.poblacion, generaciones=args.generaciones)

    print(f"{'mapa':<32}{'algoritmo':<10}{'superv.':>9}{'media':>8}{'desv':>8}{'min':>6}{'max':>6}{'expand.':>10}")
    for clave in args.mapas:
        mapa = MAPAS[clave]
        for nombre in args.algoritmos:
            m = experimento(mapa, nombre, args.iteraciones, pag)
            print(
                f"{mapa.nombre:<32}{nombre:<10}{m['supervivencia']:>9.1%}"
                f"{fmt(m['media']):>8}{fmt(m['desv']):>8}{fmt(m['min'], 0):>6}{fmt(m['max'], 0):>6}"
                f"{m['expandidos']:>10.0f}",
                flush=True,
            )


if __name__ == "__main__":
    main()
