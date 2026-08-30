"""Genera las 6 figuras estáticas del notebook en figuras/estaticas/.
Separado del notebook para poder iterar rápido; el notebook importa las
mismas funciones de analisis_utils y vuelve a generar los mismos gráficos
in situ (así el notebook queda reproducible sin depender de este script)."""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analisis_utils as au
from estilo_graficos import aplicar_estilo, PALETA

PROYECTO = str(Path(__file__).resolve().parent.parent)
SALIDA = f"{PROYECTO}/figuras/estaticas"
Path(SALIDA).mkdir(parents=True, exist_ok=True)
aplicar_estilo()

df, pop = au.cargar_datos()
tasas = au.tasas_por_anio(df, pop)


def fig_01_tendencia_tasas():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    for ax, grupo, color, titulo in zip(
        axes, ["menor o igual a 50", "mayor a 50"], [PALETA[0], PALETA[3]],
        ["Personas de 50 años o menos", "Personas mayores de 50 años"]
    ):
        sub = tasas[tasas.grupo_edad == grupo].sort_values("anio")
        ax.plot(sub.anio, sub.tasa_por_100k, marker="o", color=color, linewidth=2.4, markersize=6)
        ax.fill_between(sub.anio, sub.tasa_por_100k, alpha=0.12, color=color)
        ax.set_title(titulo)
        ax.set_ylabel("casos por 100.000 habitantes")
        ax.set_ylim(0, sub.tasa_por_100k.max() * 1.25)
        ax.set_xticks(sub.anio)
        ax.axvspan(2019.5, 2020.5, color="#999999", alpha=0.12)
    fig.suptitle("Cáncer colorrectal (C18-C20): tasa de admisiones por 100.000 habitantes, 2019-2024",
                 fontsize=12.5, fontweight="bold", y=1.02)
    fig.text(0.5, -0.02, "franja gris = 2020, caída de hospitalizaciones electivas por la pandemia",
              ha="center", fontsize=8.5, color="#777777")
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/01_tendencia_tasas.png", bbox_inches="tight")
    plt.close(fig)


def fig_02_indice_crecimiento():
    idx = au.indice_base_2019(tasas)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for grupo, color in zip(["menor o igual a 50", "mayor a 50"], [PALETA[0], PALETA[3]]):
        sub = idx[idx.grupo_edad == grupo].sort_values("anio")
        ax.plot(sub.anio, sub.indice, marker="o", color=color, linewidth=2.4, markersize=6,
                label="50 años o menos" if "menor" in grupo else "Mayores de 50")
    ax.axhline(100, color="#999999", linewidth=1, linestyle="--")
    ax.set_title("Velocidad de crecimiento comparada (tasa indexada, 2019 = 100)")
    ax.set_ylabel("índice (2019 = 100)")
    ax.set_xticks(sorted(idx.anio.unique()))
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/02_indice_crecimiento.png", bbox_inches="tight")
    plt.close(fig)


def fig_03_perfil_jovenes():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    dist = au.distribucion_edad_jovenes(df)
    axes[0].bar([f"{int(t)}-{int(t)+4}" for t in dist.index], dist.values,
                color=PALETA[0])
    axes[0].set_title("Casos de cáncer colorrectal ≤50 años, por tramo etario")
    axes[0].set_ylabel("admisiones (2019-2024)")
    axes[0].tick_params(axis="x", rotation=45)

    sexo = au.por_sexo(df) * 100
    x = np.arange(2)
    width = 0.35
    for i, (grupo, color) in enumerate(zip(["menor o igual a 50", "mayor a 50"], [PALETA[0], PALETA[3]])):
        vals = [sexo.loc[grupo, "HOMBRE"], sexo.loc[grupo, "MUJER"]]
        axes[1].bar(x + i * width, vals, width, color=color,
                    label="50 años o menos" if "menor" in grupo else "Mayores de 50")
    axes[1].set_xticks(x + width / 2)
    axes[1].set_xticklabels(["Hombre", "Mujer"])
    axes[1].set_ylabel("% de las admisiones")
    axes[1].set_title("Distribución por sexo")
    axes[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/03_perfil_jovenes.png", bbox_inches="tight")
    plt.close(fig)


def fig_04_presentacion_clinica():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    ingreso = au.por_tipo_ingreso(df) * 100
    x = np.arange(2)
    width = 0.35
    for i, (grupo, color) in enumerate(zip(["menor o igual a 50", "mayor a 50"], [PALETA[0], PALETA[3]])):
        vals = [ingreso.loc[grupo, "URGENCIA"], ingreso.loc[grupo, "PROGRAMADA"]]
        axes[0].bar(x + i * width, vals, width, color=color,
                    label="50 años o menos" if "menor" in grupo else "Mayores de 50")
    axes[0].set_xticks(x + width / 2)
    axes[0].set_xticklabels(["Ingreso de urgencia", "Ingreso programado"])
    axes[0].set_ylabel("% de las admisiones")
    axes[0].set_title("Forma de llegada al hospital")
    axes[0].legend(frameon=False)

    sub = au.por_subsitio(df) * 100
    etiquetas = {"C18": "Colon", "C19": "Unión rectosigmoidea", "C20": "Recto"}
    x = np.arange(3)
    for i, (grupo, color) in enumerate(zip(["menor o igual a 50", "mayor a 50"], [PALETA[0], PALETA[3]])):
        vals = [sub.loc[grupo, c] for c in ["C18", "C19", "C20"]]
        axes[1].bar(x + i * width, vals, width, color=color,
                    label="50 años o menos" if "menor" in grupo else "Mayores de 50")
    axes[1].set_xticks(x + width / 2)
    axes[1].set_xticklabels([etiquetas[c] for c in ["C18", "C19", "C20"]])
    axes[1].set_ylabel("% de las admisiones")
    axes[1].set_title("Ubicación anatómica del tumor")
    axes[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/04_presentacion_clinica.png", bbox_inches="tight")
    plt.close(fig)


def fig_05_letalidad():
    let = au.letalidad_por_anio(df) * 100
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for grupo, color in zip(["menor o igual a 50", "mayor a 50"], [PALETA[0], PALETA[3]]):
        ax.plot(let.index, let[grupo], marker="o", color=color, linewidth=2.4, markersize=6,
                label="50 años o menos" if "menor" in grupo else "Mayores de 50")
    ax.set_title("Letalidad intrahospitalaria (% de admisiones que terminan en fallecimiento)")
    ax.set_ylabel("% fallecidos durante la hospitalización")
    ax.set_xticks(sorted(let.index))
    ax.legend(frameon=False, loc="center right")
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/05_letalidad.png", bbox_inches="tight")
    plt.close(fig)


def fig_06_invasor_vs_pesquisa():
    comp = au.polipos_in_situ_vs_invasor_jovenes(df)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(comp.index, comp["indice_cancer_invasor"], marker="o", color=PALETA[3],
             linewidth=2.4, markersize=6, label="Cáncer colorrectal invasor")
    ax.plot(comp.index, comp["indice_polipo_o_in_situ"], marker="o", color=PALETA[4],
             linewidth=2.4, markersize=6, label="Pólipos / carcinoma in situ")
    ax.axhline(100, color="#999999", linewidth=1, linestyle="--")
    ax.set_title("En personas ≤50 años: ¿sube el cáncer invasor o solo la pesquisa temprana?")
    ax.set_ylabel("índice (2019 = 100)")
    ax.set_xticks(comp.index)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/06_invasor_vs_pesquisa.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_01_tendencia_tasas()
    fig_02_indice_crecimiento()
    fig_03_perfil_jovenes()
    fig_04_presentacion_clinica()
    fig_05_letalidad()
    fig_06_invasor_vs_pesquisa()
    print("Figuras guardadas en", SALIDA)
