"""
Funciones de cálculo reutilizadas por el notebook principal y por
generar_gifs.py. No genera gráficos, solo tablas (DataFrames/Series) a partir
de data/crc_admisiones.parquet y data/poblacion_nacional_edad_anio.parquet.
"""
from pathlib import Path

import pandas as pd

PROYECTO = str(Path(__file__).resolve().parent.parent)


def cargar_datos():
    df = pd.read_parquet(f"{PROYECTO}/data/crc_admisiones.parquet")
    pop = pd.read_parquet(f"{PROYECTO}/data/poblacion_nacional_edad_anio.parquet")
    pop["año"] = pop["año"].astype(int)
    pop["grupo_edad"] = pop["edad"].apply(lambda e: "menor o igual a 50" if e <= 50 else "mayor a 50")
    pop_grupo = pop.groupby(["año", "grupo_edad"])["población"].sum().reset_index()
    return df, pop_grupo


def crc(df):
    """Solo cáncer colorrectal invasor (C18-C20), el foco del análisis."""
    return df[df.categoria_clinica == "cancer_colorrectal"].copy()


def tasas_por_anio(df, pop_grupo):
    """Casos y tasa por 100.000 habitantes de CRC, por año y grupo de edad."""
    casos = crc(df).groupby(["anio", "grupo_edad"]).size().reset_index(name="casos")
    m = casos.merge(pop_grupo, left_on=["anio", "grupo_edad"], right_on=["año", "grupo_edad"])
    m["tasa_por_100k"] = m["casos"] / m["población"] * 100000
    return m.drop(columns="año").sort_values(["grupo_edad", "anio"])


def cagr(valor_inicial, valor_final, años):
    return (valor_final / valor_inicial) ** (1 / años) - 1


def resumen_crecimiento(tasas):
    """CAGR y variación total 2019->2024 y 2021->2024 (este último evita el
    quiebre de 2020, cuando cayeron las hospitalizaciones electivas por la
    pandemia y eso infla artificialmente cualquier comparación que use 2019
    o 2020 como línea base)."""
    filas = []
    for g in tasas.grupo_edad.unique():
        sub = tasas[tasas.grupo_edad == g].set_index("anio")["tasa_por_100k"]
        filas.append({
            "grupo_edad": g,
            "tasa_2019": sub[2019], "tasa_2021": sub[2021], "tasa_2024": sub[2024],
            "cagr_2019_2024": cagr(sub[2019], sub[2024], 5),
            "cambio_total_2019_2024": sub[2024] / sub[2019] - 1,
            "cagr_2021_2024": cagr(sub[2021], sub[2024], 3),
            "cambio_total_2021_2024": sub[2024] / sub[2021] - 1,
        })
    return pd.DataFrame(filas)


def indice_base_2019(tasas):
    """Tasa indexada a 2019 = 100, para comparar la velocidad de crecimiento
    de ambos grupos en una misma escala."""
    out = tasas.copy()
    base = out[out.anio == 2019].set_index("grupo_edad")["tasa_por_100k"]
    out["indice"] = out.apply(lambda r: 100 * r.tasa_por_100k / base[r.grupo_edad], axis=1)
    return out


def distribucion_edad_jovenes(df):
    jov = crc(df)[crc(df).grupo_edad == "menor o igual a 50"].copy()
    jov["tramo5"] = (jov["edad"] // 5 * 5).astype(int)
    return jov["tramo5"].value_counts().sort_index()


def por_subsitio(df):
    return crc(df).groupby("grupo_edad")["diagnostico1_categoria"].value_counts(normalize=True).unstack()


def por_tipo_ingreso(df):
    d = crc(df)
    d = d[d.tipo_ingreso.isin(["URGENCIA", "PROGRAMADA"])]
    return d.groupby("grupo_edad")["tipo_ingreso"].value_counts(normalize=True).unstack()


def por_sexo(df):
    return crc(df).groupby("grupo_edad")["sexo"].value_counts(normalize=True).unstack()


def letalidad_por_anio(df):
    d = crc(df).copy()
    d["fallecido"] = (d["tipo_alta"] == "FALLECIDO").astype(int)
    return d.groupby(["anio", "grupo_edad"])["fallecido"].mean().unstack()


def polipos_in_situ_vs_invasor_jovenes(df):
    """Compara la evolución de cáncer invasor con pólipos/carcinoma in situ,
    solo en el grupo joven, para ver si el aumento viene acompañado de más
    detección temprana o es solo el cáncer invasor el que sube."""
    jov = df[df.grupo_edad == "menor o igual a 50"]
    invasor = jov[jov.categoria_clinica == "cancer_colorrectal"].groupby("anio").size()
    temprano = jov[jov.categoria_clinica.isin(["polipo_adenomatoso", "carcinoma_in_situ"])].groupby("anio").size()
    out = pd.DataFrame({"cancer_invasor": invasor, "polipo_o_in_situ": temprano}).fillna(0)
    for col in out.columns:
        out[f"indice_{col}"] = 100 * out[col] / out[col].iloc[0]
    return out


def hospitales_por_anio(df):
    return crc(df).groupby("anio")["cod_hospital"].nunique()
