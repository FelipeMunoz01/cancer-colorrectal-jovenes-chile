"""
Descarga el archivo oficial de estimaciones y proyecciones de población del
INE (base Censo 2017, a nivel comunal) y lo agrega a totales nacionales por
edad simple y año, para usar como denominador de las tasas por 100.000
habitantes del análisis.

Fuente única: INE, "Estimaciones y proyecciones de población" (base 2017),
cuadro comunal 2002-2035. No depende de ningún repositorio de terceros: el
archivo se descarga directo del INE y se agrega acá mismo.

    https://www.ine.gob.cl/docs/default-source/proyecciones-de-poblacion/
    cuadros-estadisticos/base-2017/estimaciones-y-proyecciones-2002-2035-comunas.xlsx

El cuadro trae una fila por región/provincia/comuna/sexo/edad simple (0 a 80,
"80" es el tramo abierto "80 años o más"), con una columna de población por
cada año 2002-2035. Acá solo se usan los años 2019-2024 y se suma sobre
región, comuna y sexo para quedarnos con el total país por edad y año.
"""
import os
import urllib.request
from pathlib import Path

import pandas as pd

PROYECTO = str(Path(__file__).resolve().parent.parent)
URL_INE = (
    "https://www.ine.gob.cl/docs/default-source/proyecciones-de-poblacion/"
    "cuadros-estadisticos/base-2017/estimaciones-y-proyecciones-2002-2035-comunas.xlsx"
)
CACHE_XLSX = f"{PROYECTO}/data/estimaciones-y-proyecciones-2002-2035-comunas.xlsx"
SALIDA = f"{PROYECTO}/data/poblacion_nacional_edad_anio.parquet"
ANIOS = [2019, 2020, 2021, 2022, 2023, 2024]


def descargar_si_falta():
    if os.path.exists(CACHE_XLSX):
        print(f"Ya está descargado: {CACHE_XLSX}")
        return
    print(f"Descargando {URL_INE} ...")
    urllib.request.urlretrieve(URL_INE, CACHE_XLSX)
    print(f"Guardado en {CACHE_XLSX}")


def main():
    descargar_si_falta()

    cols_anio = {anio: f"Poblacion {anio}" for anio in ANIOS}
    df = pd.read_excel(
        CACHE_XLSX,
        sheet_name="Est. y Proy. de Pob. Comunal",
        usecols=["Edad"] + list(cols_anio.values()),
        engine="openpyxl",
    )

    largo = df.melt(id_vars="Edad", value_vars=list(cols_anio.values()),
                     var_name="anio_col", value_name="población")
    largo["año"] = largo["anio_col"].str.replace("Poblacion ", "", regex=False).astype(int)
    nacional = (
        largo.groupby(["año", "Edad"])["población"].sum()
        .reset_index()
        .rename(columns={"Edad": "edad"})
        .sort_values(["año", "edad"])
    )

    nacional.to_parquet(SALIDA, index=False)
    print(f"\nGuardado en {SALIDA} ({len(nacional)} filas)")
    for anio in ANIOS:
        total = nacional[nacional.año == anio]["población"].sum()
        print(f"  {anio}: {total:,.0f} habitantes")


if __name__ == "__main__":
    main()
