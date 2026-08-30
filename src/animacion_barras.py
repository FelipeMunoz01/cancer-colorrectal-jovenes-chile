"""
Utilidad reutilizable para generar gráficos de barras animados (GIF) con estilo
oscuro moderno, pensados para compartir en redes sociales (LinkedIn, etc.).

Uso típico en otro proyecto:

    from animacion_barras import crear_gif_barras_horizontal, crear_gif_barras_vertical

    crear_gif_barras_horizontal(
        labels=["Región A", "Región B", "Región C"],
        values=[45.2, 30.1, 78.9],
        titulo="Mi gráfico",
        xlabel="% de algo",
        salida="mi_grafico.gif",
    )

No depende de pandas ni de ningún dataset: solo recibe listas/arrays de
etiquetas y valores ya calculados.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ---------------------------------------------------------------- paleta / tema
BG = "#0f1220"
FG = "#f5f5fa"
GRID = "#2a2e45"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "text.color": FG,
    "axes.labelcolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "axes.edgecolor": GRID,
    "font.family": "DejaVu Sans",
    "font.weight": "bold",
})


def ease_out(t):
    """Curva de easing: rápido al inicio, se frena al llegar al final."""
    return 1 - (1 - t) ** 3


def grad_colors(n, c1, c2):
    """Genera n colores interpolados entre dos colores hex (para degradados en las barras)."""
    c1 = np.array([int(c1[i:i + 2], 16) for i in (1, 3, 5)])
    c2 = np.array([int(c2[i:i + 2], 16) for i in (1, 3, 5)])
    return ["#%02x%02x%02x" % tuple((c1 + (c2 - c1) * i / max(n - 1, 1)).astype(int)) for i in range(n)]


def _extender_hold_final(path, ms_hold=2800, ms_frame=40):
    """Reescribe el GIF para que el último frame (resultado final) quede
    congelado más tiempo en pantalla, en vez de solo unos milisegundos."""
    from PIL import Image, ImageSequence
    im = Image.open(path)
    frames = [f.copy() for f in ImageSequence.Iterator(im)]
    n = len(frames)
    duraciones = [ms_hold if i == n - 1 else ms_frame for i in range(n)]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=duraciones, loop=0, disposal=2)


def crear_gif_barras_horizontal(labels, values, titulo, xlabel, salida,
                                 color_inicio="#FF6B6B", color_fin="#00D2B4",
                                 linea_referencia=None, etiqueta_referencia=None,
                                 figsize=(9, 7), n_frames=40, hold_frames=18, fps=22):
    """Barras horizontales que 'crecen' desde 0 hasta su valor final.

    linea_referencia: valor opcional (ej. promedio nacional) para dibujar una
    línea punteada vertical una vez termina la animación.
    """
    values = np.asarray(values, dtype=float)
    colors = grad_colors(len(values), color_inicio, color_fin)
    fig, ax = plt.subplots(figsize=figsize)

    def animate(frame):
        ax.clear()
        t = ease_out(min(frame / n_frames, 1))
        current = values * t
        ax.barh(labels, current, color=colors, height=0.65)
        ax.set_xlim(0, max(values) * 1.18)
        ax.set_title(titulo, fontsize=15, pad=14, loc="left", color=FG)
        ax.set_xlabel(xlabel, fontsize=10, color="#b5b8d0")
        ax.grid(axis="x", color=GRID, linewidth=0.6, alpha=0.6)
        ax.set_axisbelow(True)
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(left=False)
        if t >= 0.98 and linea_referencia is not None:
            ax.axvline(linea_referencia, color=FG, linestyle=(0, (4, 3)), linewidth=1.2, alpha=0.8)
            if etiqueta_referencia:
                ax.text(linea_referencia + max(values) * 0.015, 0.3, etiqueta_referencia,
                         fontsize=8.5, color="#b5b8d0")
        for i, v in enumerate(current):
            if v > max(values) * 0.03:
                ax.text(v + max(values) * 0.015, i, f"{v:.0f}%", va="center", fontsize=8.5,
                         color=FG, fontweight="bold", alpha=min(1, t * 1.5))
        fig.tight_layout()

    anim = animation.FuncAnimation(fig, animate, frames=n_frames + hold_frames, interval=45, repeat=True)
    anim.save(salida, writer=animation.PillowWriter(fps=fps))
    plt.close(fig)
    _extender_hold_final(salida)


def crear_gif_barras_vertical(labels, values, titulo, ylabel, salida, colors=None,
                               figsize=(6, 6), n_frames=40, hold_frames=18, fps=22,
                               formato_valor="{:.2f}"):
    """Barras verticales que 'crecen' desde 0 hasta su valor final (ideal para
    comparar 2-4 categorías, ej. 'con vs sin' algo)."""
    values = np.asarray(values, dtype=float)
    if colors is None:
        colors = grad_colors(len(values), "#6C5CE7", "#00D2B4")
    fig, ax = plt.subplots(figsize=figsize)

    def animate(frame):
        ax.clear()
        t = ease_out(min(frame / n_frames, 1))
        current = values * t
        ax.bar(labels, current, color=colors, width=0.55)
        ax.set_ylim(0, max(values) * 1.3)
        ax.set_title(titulo, fontsize=13.5, pad=14, color=FG)
        ax.set_ylabel(ylabel, fontsize=9.5, color="#b5b8d0")
        ax.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.6)
        ax.set_axisbelow(True)
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(left=False)
        for i, v in enumerate(current):
            if v > max(values) * 0.02:
                ax.text(i, v + max(values) * 0.03, formato_valor.format(v), ha="center", fontsize=13,
                         color=FG, fontweight="bold", alpha=min(1, t * 1.5))
        fig.tight_layout()

    anim = animation.FuncAnimation(fig, animate, frames=n_frames + hold_frames, interval=45, repeat=True)
    anim.save(salida, writer=animation.PillowWriter(fps=fps))
    plt.close(fig)
    _extender_hold_final(salida)
