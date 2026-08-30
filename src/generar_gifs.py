"""Genera los GIFs animados (estilo oscuro, para LinkedIn) a partir de los
mismos números calculados en analisis_utils. Reutiliza animacion_barras.py
(módulo copiado de proyecto3, sin cambios)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analisis_utils as au
from animacion_barras import crear_gif_barras_horizontal, crear_gif_barras_vertical

PROYECTO = str(Path(__file__).resolve().parent.parent)
SALIDA = f"{PROYECTO}/figuras/animadas"
Path(SALIDA).mkdir(parents=True, exist_ok=True)

df, pop = au.cargar_datos()
tasas = au.tasas_por_anio(df, pop)


def gif_01_tasa_jovenes():
    sub = tasas[tasas.grupo_edad == "menor o igual a 50"].sort_values("anio")
    crear_gif_barras_vertical(
        labels=[str(a) for a in sub.anio],
        values=sub.tasa_por_100k.values,
        titulo="Cáncer colorrectal en personas ≤50 años\ncasos por 100.000 habitantes, Chile",
        ylabel="casos por 100.000 habitantes",
        salida=f"{SALIDA}/gif_01_tasa_jovenes.gif",
        colors=["#6C5CE7"] * 5 + ["#00D2B4"],
        formato_valor="{:.1f}",
    )


def gif_02_crecimiento_comparado():
    resumen = au.resumen_crecimiento(tasas)
    resumen = resumen.set_index("grupo_edad")
    crear_gif_barras_horizontal(
        labels=["Personas de 50 años o menos", "Personas mayores de 50 años"],
        values=[
            100 * resumen.loc["menor o igual a 50", "cambio_total_2019_2024"],
            100 * resumen.loc["mayor a 50", "cambio_total_2019_2024"],
        ],
        titulo="Crecimiento de la tasa de cáncer colorrectal\n2019 -> 2024",
        xlabel="% de aumento en la tasa por 100.000 habitantes",
        salida=f"{SALIDA}/gif_02_crecimiento_comparado.gif",
        color_inicio="#FF6B6B", color_fin="#6C5CE7",
    )


def gif_03_ubicacion_tumor():
    sub = au.por_subsitio(df) * 100
    crear_gif_barras_horizontal(
        labels=["Recto - personas ≤50 años", "Recto - personas mayores de 50",
                "Colon - personas ≤50 años", "Colon - personas mayores de 50"],
        values=[
            sub.loc["menor o igual a 50", "C20"],
            sub.loc["mayor a 50", "C20"],
            sub.loc["menor o igual a 50", "C18"],
            sub.loc["mayor a 50", "C18"],
        ],
        titulo="¿Dónde aparece el tumor?",
        xlabel="% de las admisiones por cáncer colorrectal",
        salida=f"{SALIDA}/gif_03_ubicacion_tumor.gif",
        color_inicio="#00D2B4", color_fin="#6C5CE7",
    )


def gif_04_invasor_vs_pesquisa():
    # el módulo de barras solo anima valores positivos creciendo desde 0, así
    # que se grafica la MAGNITUD del cambio y el signo va en la etiqueta.
    comp = au.polipos_in_situ_vs_invasor_jovenes(df)
    cambio_invasor = 100 * (comp["cancer_invasor"].iloc[-1] / comp["cancer_invasor"].iloc[0] - 1)
    cambio_pesquisa = 100 * (comp["polipo_o_in_situ"].iloc[-1] / comp["polipo_o_in_situ"].iloc[0] - 1)
    crear_gif_barras_vertical(
        labels=[f"Cáncer invasor (C18-C20)\n{cambio_invasor:+.0f}%",
                f"Pólipos / carcinoma in situ\n{cambio_pesquisa:+.0f}%"],
        values=[abs(cambio_invasor), abs(cambio_pesquisa)],
        titulo="En personas ≤50 años, 2019 -> 2024:\n¿qué diagnóstico aumentó?",
        ylabel="magnitud del cambio (%)",
        salida=f"{SALIDA}/gif_04_invasor_vs_pesquisa.gif",
        colors=["#FF6B6B", "#00D2B4"],
        formato_valor="{:.0f}%",
    )


if __name__ == "__main__":
    gif_01_tasa_jovenes()
    gif_02_crecimiento_comparado()
    gif_03_ubicacion_tumor()
    gif_04_invasor_vs_pesquisa()
    print("GIFs guardados en", SALIDA)
