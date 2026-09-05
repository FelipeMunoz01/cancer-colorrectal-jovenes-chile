"""
Utilidad para generar gráficos de LÍNEA animados en el tiempo (GIF), con un
trazo tipo cometa: una estela que se desvanece hacia atrás y un halo
luminoso en la punta, en vez de barras que crecen desde cero. Pensado para
series temporales cortas (pocos años) donde lo interesante es la forma de la
curva y, al comparar dos series, la brecha que se abre entre ambas.

Reutiliza la paleta y el tema oscuro de animacion_barras.py para mantener
consistencia visual entre los GIFs del proyecto.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from animacion_barras import BG, FG, GRID, ease_out, _extender_hold_final


def _base_ax(ax, titulo, ylabel, x, xmin, xmax, ymin, ymax):
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xticks(x)
    ax.set_xticklabels([str(int(v)) for v in x])
    ax.set_title(titulo, fontsize=15, pad=14, loc="left", color=FG)
    ax.set_ylabel(ylabel, fontsize=10, color="#b5b8d0")
    ax.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.5)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(left=False)


def _dibujar_cometa(ax, xs, ys, color, largo_estela=60, ancho=2.6):
    """Dibuja la curva ya recorrida con una estela que se desvanece hacia
    atrás y un halo brillante en la punta (el tramo más reciente)."""
    n = len(xs)
    if n > 1:
        ax.plot(xs, ys, color=color, linewidth=ancho, alpha=0.28, solid_capstyle="round")
        i0 = max(0, n - largo_estela)
        seg_x, seg_y = xs[i0:], ys[i0:]
        m = len(seg_x)
        for i in range(m - 1):
            a = (i + 1) / m
            ax.plot(seg_x[i:i + 2], seg_y[i:i + 2], color=color, linewidth=ancho,
                     alpha=0.35 + 0.65 * a, solid_capstyle="round")
    if n:
        tip_x, tip_y = xs[-1], ys[-1]
        for r, a in [(420, 0.05), (230, 0.10), (95, 0.20)]:
            ax.scatter([tip_x], [tip_y], s=r, color=color, alpha=a, linewidths=0, zorder=4)
        ax.scatter([tip_x], [tip_y], s=42, color=BG, alpha=1, zorder=5,
                    edgecolors=color, linewidths=1.8)


def crear_gif_linea_tiempo(x, y, titulo, ylabel, salida, color="#FF6B6B",
                            figsize=(9, 6), fps=30, dur_dibujo_s=2.3, hold_s=3.0,
                            sufijo="", decimales=1, zona_sombra=None,
                            etiqueta_sombra=None, relleno=True):
    """Línea única que se traza en el tiempo con efecto cometa. Las etiquetas
    de valor van apareciendo en cada año a medida que la curva pasa por él."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n_dibujo = int(dur_dibujo_s * fps)
    n_hold = int(hold_s * fps)
    x_dense = np.linspace(x.min(), x.max(), 500)
    y_dense = np.interp(x_dense, x, y)
    ymax = y.max() * 1.28
    ymin = min(0, y.min() * 0.85)

    fig, ax = plt.subplots(figsize=figsize)

    def animate(frame):
        ax.clear()
        t = ease_out(min(frame / n_dibujo, 1))
        cur_x = x.min() + t * (x.max() - x.min())
        mask = x_dense <= cur_x + 1e-9
        xs, ys = x_dense[mask], y_dense[mask]

        if zona_sombra:
            ax.axvspan(*zona_sombra, color="#ffffff", alpha=0.045, zorder=0)

        if relleno and len(xs) > 1:
            ax.fill_between(xs, ys, ymin, color=color, alpha=0.08, zorder=1)

        _dibujar_cometa(ax, xs, ys, color)

        for xi, yi in zip(x, y):
            if xi <= cur_x + 1e-6:
                ax.scatter([xi], [yi], s=40, color=BG, edgecolors=color, linewidths=1.6, zorder=4)
                ax.text(xi, yi + ymax * 0.045, f"{yi:.{decimales}f}{sufijo}", ha="center",
                        fontsize=9, color=FG, fontweight="bold")

        if zona_sombra and etiqueta_sombra and cur_x >= zona_sombra[1]:
            ax.text(sum(zona_sombra) / 2, ymin + (ymax - ymin) * 0.04, etiqueta_sombra,
                    ha="center", fontsize=7.5, color="#8388a8", style="italic")

        _base_ax(ax, titulo, ylabel, x, x.min() - 0.3, x.max() + 0.3, ymin, ymax)
        fig.tight_layout()

    anim = animation.FuncAnimation(fig, animate, frames=n_dibujo + n_hold, interval=1000 / fps, repeat=True)
    anim.save(salida, writer=animation.PillowWriter(fps=fps))
    plt.close(fig)
    _extender_hold_final(salida, ms_hold=2800, ms_frame=int(1000 / fps))


def crear_gif_lineas_comparadas(x, series, titulo, ylabel, salida, colores=None,
                                 figsize=(9, 6), fps=30, dur_dibujo_s=2.4, hold_s=3.4,
                                 sufijo="", decimales=0, sombrear_gap=False,
                                 etiqueta_gap=None):
    """Varias líneas (dict nombre -> valores) que se trazan en paralelo, cada
    una con su propio efecto cometa y una etiqueta con nombre + valor
    siguiendo la punta. Con sombrear_gap=True (pensado para 2 series) resalta
    al final el área entre ambas, para hacer evidente la brecha que se abre."""
    x = np.asarray(x, dtype=float)
    nombres = list(series.keys())
    if colores is None:
        colores = ["#FF6B6B", "#6C5CE7", "#00D2B4", "#E8A33D"][:len(nombres)]
    n_dibujo = int(dur_dibujo_s * fps)
    n_hold = int(hold_s * fps)

    x_dense = np.linspace(x.min(), x.max(), 500)
    dense = {k: np.interp(x_dense, x, np.asarray(v, dtype=float)) for k, v in series.items()}
    todos_y = np.concatenate([np.asarray(v, dtype=float) for v in series.values()])
    ymax = todos_y.max() * 1.22
    ymin = min(0, todos_y.min() * 0.9)

    fig, ax = plt.subplots(figsize=figsize)

    def animate(frame):
        ax.clear()
        t = ease_out(min(frame / n_dibujo, 1))
        cur_x = x.min() + t * (x.max() - x.min())
        mask = x_dense <= cur_x + 1e-9
        xs = x_dense[mask]

        for nombre, color in zip(nombres, colores):
            ys = dense[nombre][mask]
            _dibujar_cometa(ax, xs, ys, color)
            if len(xs):
                val_actual = np.interp(cur_x, x, series[nombre])
                ax.text(xs[-1] + (x.max() - x.min()) * 0.02, ys[-1],
                        f"{nombre}  {val_actual:.{decimales}f}{sufijo}",
                        va="center", fontsize=9.5, color=color, fontweight="bold")

        if sombrear_gap and len(nombres) >= 2 and t > 0.55 and len(xs) > 1:
            a1 = dense[nombres[0]][mask]
            a2 = dense[nombres[1]][mask]
            alpha_gap = min(1, (t - 0.55) / 0.45) * 0.16
            ax.fill_between(xs, a1, a2, color="#ffffff", alpha=alpha_gap, zorder=0)
            if etiqueta_gap and t >= 0.98:
                xi_idx = int(len(xs) * 0.5)
                xi, yi = xs[xi_idx], (a1[xi_idx] + a2[xi_idx]) / 2
                ax.text(xi, yi, etiqueta_gap, ha="center", fontsize=8.5, color="#c7cae0", style="italic")

        _base_ax(ax, titulo, ylabel, x, x.min() - 0.3, x.max() + 1.6, ymin, ymax)
        fig.tight_layout()

    anim = animation.FuncAnimation(fig, animate, frames=n_dibujo + n_hold, interval=1000 / fps, repeat=True)
    anim.save(salida, writer=animation.PillowWriter(fps=fps))
    plt.close(fig)
    _extender_hold_final(salida, ms_hold=2900, ms_frame=int(1000 / fps))
