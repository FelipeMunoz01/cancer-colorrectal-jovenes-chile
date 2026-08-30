"""Estilo compartido para los gráficos estáticos del notebook (tema claro,
igual al usado en proyecto3, para mantener consistencia visual del portafolio)."""
import matplotlib.pyplot as plt

PALETA = ["#3B4CC0", "#6DA34D", "#E8A33D", "#C25B5B", "#7A5CB0", "#3D9BA8"]
GRIS = "#4a4a4a"


def aplicar_estilo():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.grid": True,
        "grid.color": "#dcdcdc",
        "grid.linewidth": 0.7,
        "axes.axisbelow": True,
        "axes.edgecolor": "#bbbbbb",
        "axes.labelcolor": GRIS,
        "text.color": "#222222",
        "xtick.color": GRIS,
        "ytick.color": GRIS,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "figure.dpi": 130,
        "savefig.dpi": 130,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
