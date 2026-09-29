import argparse
import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mapas import MAPAS

ORDEN = ("bfs", "ucs", "astar", "greedy", "genetico")
ETIQUETAS = {"bfs": "BFS", "ucs": "UCS", "astar": "A*", "greedy": "Greedy", "genetico": "Genético"}
COLORES = {"bfs": "#2a78d6", "ucs": "#eb6834", "astar": "#1baf7a", "greedy": "#eda100", "genetico": "#e87ba4"}
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRILLA = "#e4e3df"
NOMBRES_MAPA = {"1": "Mapa 1: cuello de botella", "2": "Mapa 2: laberinto", "3": "Mapa 3: abierto"}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.edgecolor": TINTA_SECUNDARIA,
    "axes.labelcolor": TINTA,
    "xtick.color": TINTA_SECUNDARIA,
    "ytick.color": TINTA_SECUNDARIA,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRILLA,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "pdf.fonttype": 42,
    "savefig.bbox": "tight",
})


def leer(ruta):
    datos = {}
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            d = datos.setdefault((fila["mapa"], fila["algoritmo"]), {"superv": [], "despeje": [], "expandidos": []})
            d["superv"].append(float(fila["supervivencia"]))
            d["expandidos"].append(float(fila["expandidos"]))
            if fila["tiempo_despeje"]:
                d["despeje"].append(float(fila["tiempo_despeje"]))
    return datos


def paneles(n=3, alto=2.5):
    fig, ejes = plt.subplots(1, n, figsize=(6.3, alto), sharey=True)
    return fig, ejes


def guardar(fig, carpeta, nombre):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(carpeta, f"{nombre}.{ext}"), dpi=300)
    plt.close(fig)


def eje_algoritmos(ax, algoritmos):
    ax.set_xticks(range(len(algoritmos)))
    ax.set_xticklabels([ETIQUETAS[a] for a in algoritmos], rotation=35, ha="right", rotation_mode="anchor")
    ax.tick_params(axis="x", length=0)


def supervivencia(datos, carpeta):
    fig, ejes = paneles()
    for ax, mapa in zip(ejes, MAPAS):
        algs = [a for a in ORDEN if (mapa, a) in datos]
        for i, a in enumerate(algs):
            v = np.array(datos[(mapa, a)]["superv"]) * 100
            media = v.mean()
            ic = 1.96 * v.std(ddof=1) / np.sqrt(len(v)) if len(v) > 1 else 0
            ax.bar(i, media, width=0.7, color=COLORES[a], edgecolor="white", linewidth=1)
            ax.errorbar(i, media, yerr=ic, color=TINTA, capsize=2.5, linewidth=0.9)
        eje_algoritmos(ax, algs)
        ax.set_title(NOMBRES_MAPA[mapa], color=TINTA)
        ax.set_ylim(0, 105)
    ejes[0].set_ylabel("Supervivencia media (%)")
    guardar(fig, carpeta, "supervivencia")


def despeje(datos, carpeta):
    fig, ejes = paneles(alto=2.7)
    for ax, mapa in zip(ejes, MAPAS):
        algs = [a for a in ORDEN if (mapa, a) in datos and datos[(mapa, a)]["despeje"]]
        caja = ax.boxplot(
            [datos[(mapa, a)]["despeje"] for a in algs],
            positions=range(len(algs)),
            widths=0.6,
            patch_artist=True,
            medianprops={"color": TINTA, "linewidth": 1.2},
            whiskerprops={"color": TINTA_SECUNDARIA, "linewidth": 0.8},
            capprops={"color": TINTA_SECUNDARIA, "linewidth": 0.8},
            flierprops={"marker": "o", "markersize": 2.5, "markerfacecolor": TINTA_SECUNDARIA, "markeredgewidth": 0, "alpha": 0.6},
        )
        for parche, a in zip(caja["boxes"], algs):
            parche.set_facecolor(COLORES[a])
            parche.set_edgecolor(TINTA_SECUNDARIA)
            parche.set_linewidth(0.8)
        eje_algoritmos(ax, algs)
        ax.set_title(NOMBRES_MAPA[mapa], color=TINTA)
    ejes[0].set_ylabel("Tiempo de despeje (turnos)")
    guardar(fig, carpeta, "tiempo_despeje")


def expandidos(datos, carpeta):
    fig, ejes = paneles()
    for ax, mapa in zip(ejes, MAPAS):
        algs = [a for a in ORDEN if a != "genetico" and (mapa, a) in datos]
        for i, a in enumerate(algs):
            media = np.mean(datos[(mapa, a)]["expandidos"])
            ax.bar(i, media, width=0.7, color=COLORES[a], edgecolor="white", linewidth=1)
            ax.text(i, media * 1.08, f"{media / 1000:.0f}k", ha="center", va="bottom", fontsize=7, color=TINTA)
        eje_algoritmos(ax, algs)
        ax.set_title(NOMBRES_MAPA[mapa], color=TINTA)
        ax.set_yscale("log")
    ejes[0].set_ylabel("Nodos expandidos por corrida\n(media, escala log.)")
    guardar(fig, carpeta, "nodos_expandidos")


def convergencia(ruta, carpeta):
    with open(ruta, encoding="utf-8") as f:
        historiales = json.load(f)
    fig, ejes = plt.subplots(1, 3, figsize=(6.3, 2.4))
    for ax, mapa in zip(ejes, MAPAS):
        h = np.array(historiales.get(mapa, []), dtype=float)
        if not len(h):
            continue
        h = h - h[:, :1]
        gen = np.arange(h.shape[1])
        q1, q3 = np.percentile(h, [25, 75], axis=0)
        ax.fill_between(gen, q1, q3, color=COLORES["genetico"], alpha=0.25, linewidth=0, label="Rango intercuartil")
        ax.plot(gen, h.mean(axis=0), color=COLORES["genetico"], linewidth=2, label="Media")
        ax.set_title(NOMBRES_MAPA[mapa], color=TINTA)
        ax.set_xlabel("Generación")
        ax.grid(axis="both")
    ejes[0].set_ylabel("Mejora de aptitud del mejor\nindividuo respecto a gen. 0")
    ejes[-1].legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout()
    guardar(fig, carpeta, "convergencia_genetico")


def tabla(datos, carpeta):
    lineas = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Resultados del benchmark por mapa y algoritmo. $n$: iteraciones. Tiempo de despeje en turnos, sobre las corridas con al menos un sobreviviente.}",
        r"\label{tab:resultados}",
        r"\begin{tabular}{llrrrrrr}",
        r"\toprule",
        r"Mapa & Algoritmo & $n$ & Superv. (\%) & Media & Desv. est. & Mín. & Máx. \\",
        r"\midrule",
    ]
    for j, mapa in enumerate(MAPAS):
        algs = [a for a in ORDEN if (mapa, a) in datos]
        for i, a in enumerate(algs):
            d = datos[(mapa, a)]
            t = np.array(d["despeje"])
            nombre = NOMBRES_MAPA[mapa].split(":")[0] if i == 0 else ""
            celdas = [str(len(d["superv"])), f"{100 * np.mean(d['superv']):.1f}"]
            if len(t):
                celdas += [f"{t.mean():.1f}", f"{t.std(ddof=1):.1f}" if len(t) > 1 else "--", f"{t.min():.0f}", f"{t.max():.0f}"]
            else:
                celdas += ["--"] * 4
            lineas.append(f"{nombre} & {ETIQUETAS[a]} & " + " & ".join(celdas) + r" \\")
        if j < len(MAPAS) - 1:
            lineas.append(r"\midrule")
    lineas += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    with open(os.path.join(carpeta, "tabla_resultados.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


FIGURAS = (
    ("supervivencia", "Tasa de supervivencia media por mapa y algoritmo. Las barras de error indican el intervalo de confianza del 95\\,\\% de la media."),
    ("tiempo_despeje", "Distribución del tiempo de despeje (turnos hasta que evacúa el último sobreviviente) por mapa y algoritmo."),
    ("nodos_expandidos", "Nodos expandidos por corrida de simulación (media, escala logarítmica), sumando todas las replanificaciones. No incluye el algoritmo genético, cuyo costo está en las simulaciones de evaluación de aptitud."),
    ("convergencia_genetico", "Convergencia del algoritmo genético: mejora de la aptitud del mejor individuo respecto a la generación inicial."),
)


def figuras_tex(carpeta):
    bloques = []
    for nombre, leyenda in FIGURAS:
        if os.path.exists(os.path.join(carpeta, f"{nombre}.pdf")):
            bloques.append("\n".join([
                r"\begin{figure}[htbp]",
                r"\centering",
                rf"\includegraphics[width=\textwidth]{{figuras/{nombre}.pdf}}",
                rf"\caption{{{leyenda}}}",
                rf"\label{{fig:{nombre}}}",
                r"\end{figure}",
            ]))
    with open(os.path.join(carpeta, "figuras.tex"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(bloques) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entrada", default="resultados")
    parser.add_argument("--salida", default="figuras")
    args = parser.parse_args()
    os.makedirs(args.salida, exist_ok=True)
    datos = leer(os.path.join(args.entrada, "corridas.csv"))
    supervivencia(datos, args.salida)
    despeje(datos, args.salida)
    expandidos(datos, args.salida)
    tabla(datos, args.salida)
    ruta_hist = os.path.join(args.entrada, "historial_genetico.json")
    if os.path.exists(ruta_hist):
        convergencia(ruta_hist, args.salida)
    figuras_tex(args.salida)


if __name__ == "__main__":
    main()
