"""Genera los GIFs animados (estilo oscuro, para LinkedIn) a partir de los
mismos números calculados en analisis_utils. Usa animacion_lineas.py: los
cuatro GIFs son gráficos de línea en el tiempo (no barras), porque son series
temporales cortas y lo que importa es la forma de la curva y la brecha entre
grupos, no un ranking estático."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analisis_utils as au
from animacion_lineas import crear_gif_linea_tiempo, crear_gif_lineas_comparadas

PROYECTO = str(Path(__file__).resolve().parent.parent)
SALIDA = f"{PROYECTO}/figuras/animadas"
Path(SALIDA).mkdir(parents=True, exist_ok=True)

df, pop = au.cargar_datos()
tasas = au.tasas_por_anio(df, pop)


def gif_01_tasa_jovenes():
    sub = tasas[tasas.grupo_edad == "menor o igual a 50"].sort_values("anio")
    crear_gif_linea_tiempo(
        x=sub.anio.values,
        y=sub.tasa_por_100k.values,
        titulo="Cáncer colorrectal en personas ≤50 años\ncasos por 100.000 habitantes, Chile",
        ylabel="casos por 100.000 habitantes",
        salida=f"{SALIDA}/gif_01_tasa_jovenes.gif",
        color="#FF6B6B",
        decimales=1,
        zona_sombra=(2019.5, 2020.5),
        etiqueta_sombra="2020: caída de hospitalizaciones electivas por la pandemia",
    )


def gif_02_indice_comparado():
    idx = au.indice_base_2019(tasas)
    piv = idx.pivot(index="anio", columns="grupo_edad", values="indice")
    crear_gif_lineas_comparadas(
        x=piv.index.values,
        series={
            "Personas ≤50 años": piv["menor o igual a 50"].values,
            "Personas >50 años": piv["mayor a 50"].values,
        },
        titulo="Velocidad de crecimiento de la tasa de cáncer colorrectal\níndice 2019 = 100",
        ylabel="índice (2019 = 100)",
        salida=f"{SALIDA}/gif_02_indice_comparado.gif",
        colores=["#FF6B6B", "#6C5CE7"],
        decimales=0,
        sombrear_gap=True,
        etiqueta_gap="crece casi el doble\nde rápido en jóvenes",
    )


def gif_03_ubicacion_tumor_tiempo():
    sub = au.subsitio_por_anio(df)
    crear_gif_lineas_comparadas(
        x=sub.index.values,
        series={
            "Recto, ≤50 años": sub["menor o igual a 50"].values,
            "Recto, >50 años": sub["mayor a 50"].values,
        },
        titulo="¿Dónde aparece el tumor?\n% de casos ubicados en el recto (vs. colon)",
        ylabel="% de las admisiones por cáncer colorrectal",
        salida=f"{SALIDA}/gif_03_ubicacion_tumor.gif",
        colores=["#FF6B6B", "#6C5CE7"],
        sufijo="%",
        decimales=0,
    )


def gif_04_invasor_vs_pesquisa():
    comp = au.polipos_in_situ_vs_invasor_jovenes(df)
    crear_gif_lineas_comparadas(
        x=comp.index.values,
        series={
            "Cáncer invasor": comp["indice_cancer_invasor"].values,
            "Pólipos / in situ": comp["indice_polipo_o_in_situ"].values,
        },
        titulo="En personas ≤50 años, 2019 -> 2024:\n¿mejor pesquisa o más cáncer?",
        ylabel="índice (2019 = 100)",
        salida=f"{SALIDA}/gif_04_invasor_vs_pesquisa.gif",
        colores=["#FF6B6B", "#00D2B4"],
        decimales=0,
        sombrear_gap=True,
        etiqueta_gap="si subieran juntas sería\nmejor pesquisa; no es el caso",
    )


if __name__ == "__main__":
    gif_01_tasa_jovenes()
    gif_02_indice_comparado()
    gif_03_ubicacion_tumor_tiempo()
    gif_04_invasor_vs_pesquisa()
    print("GIFs guardados en", SALIDA)
