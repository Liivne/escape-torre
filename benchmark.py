import argparse
import csv
import json
import os
import time
from multiprocessing import Pool

from genetico import ParametrosAG, PlanificadorGenetico
from mapas import MAPAS
from simulacion import PlanificadorBusqueda, Simulacion

ALGORITMOS = ("genetico", "bfs", "ucs", "astar", "greedy")
CAMPOS = ("mapa", "algoritmo", "semilla", "total", "evacuados", "supervivencia", "tiempo_despeje", "expandidos", "segundos")


def correr(tarea):
    clave, nombre, semilla = tarea
    inicio = time.perf_counter()
    if nombre == "genetico":
        planificador = PlanificadorGenetico(ParametrosAG(), semilla)
    else:
        planificador = PlanificadorBusqueda(nombre)
    r = Simulacion(MAPAS[clave], planificador, semilla).ejecutar()
    fila = {
        "mapa": clave,
        "algoritmo": nombre,
        "semilla": semilla,
        "total": r.total,
        "evacuados": r.evacuados,
        "supervivencia": r.supervivencia,
        "tiempo_despeje": "" if r.tiempo_despeje is None else r.tiempo_despeje,
        "expandidos": r.expandidos,
        "segundos": round(time.perf_counter() - inicio, 3),
    }
    historial = getattr(planificador, "historial", None)
    return fila, historial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iteraciones", type=int, default=200)
    parser.add_argument("--iteraciones-genetico", type=int, default=80)
    parser.add_argument("--procesos", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--salida", default="resultados")
    args = parser.parse_args()
    os.makedirs(args.salida, exist_ok=True)

    tareas = [
        (m, a, s)
        for a in ALGORITMOS
        for m in MAPAS
        for s in range(args.iteraciones_genetico if a == "genetico" else args.iteraciones)
    ]
    historiales = {m: [] for m in MAPAS}
    inicio = time.perf_counter()
    with open(os.path.join(args.salida, "corridas.csv"), "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        with Pool(args.procesos) as pool:
            for i, (fila, historial) in enumerate(pool.imap_unordered(correr, tareas), 1):
                escritor.writerow(fila)
                f.flush()
                if historial:
                    historiales[fila["mapa"]].append(historial)
                if i % 100 == 0 or i == len(tareas):
                    print(f"{i}/{len(tareas)} corridas  {time.perf_counter() - inicio:.0f} s", flush=True)
    with open(os.path.join(args.salida, "historial_genetico.json"), "w", encoding="utf-8") as f:
        json.dump(historiales, f)


if __name__ == "__main__":
    main()
