"""
Extrae desde las bases GRD públicas de Chile (2019-2024) todas las admisiones
con diagnóstico de cáncer colorrectal (CIE-10 C18, C19, C20), y guarda un
parquet chico por año en data/por_anio/.

Los .txt crudos (varios GB por año) no se copian a este repositorio. Se leen
directamente desde la ruta indicada en GRD_DIR, o si no se define, desde la
carpeta "bases de datos GRD" de proyecto5 (misma fuente, ya materializada
localmente en este equipo):

    export GRD_DIR="/ruta/a/bases de datos GRD"

QUÉ SE CONSIDERA CÁNCER COLORRECTAL, Y QUÉ SE EXTRAE ADEMÁS
-------------------------------------------------------------
El análisis principal usa CIE-10 C18 (colon), C19 (unión rectosigmoidea) y
C20 (recto): es la definición estándar de "cáncer colorrectal" en la
literatura de "early-onset colorectal cancer" (antes de los 50 años).

Se extraen además, como categorías separadas y NO se suman al total de
cáncer colorrectal invasor:
  - C21 (ano y conducto anal): anatómicamente vecino, pero con un perfil de
    causa distinto (asociado a VPH), así que se reporta aparte.
  - D01.0-D01.3 (carcinoma in situ de colon/recto/ano): lesión pre-invasora.
  - D12.6 (pólipos adenomatosos del colon): condición benigna con riesgo de
    transformar a cáncer.

Separar estas categorías, en vez de sumarlas todas a "cáncer de colon", sirve
para responder una pregunta distinta a la incidencia: si el aumento de casos
en jóvenes viene acompañado de más diagnóstico de pólipos/in situ (señal de
más tamizaje y detección temprana) o si es solo el cáncer invasor el que sube.

Se filtra por DIAGNOSTICO1 (motivo principal del egreso) para quedarnos con
admisiones en que el cáncer colorrectal fue la razón de la hospitalización,
no una comorbilidad mencionada de paso entre los 34 diagnósticos secundarios
(alguien hospitalizado por una fractura que además tiene antecedente de
cáncer de colon no debería contar como un caso "nuevo" en el análisis).

GRD es un registro de EGRESOS HOSPITALARIOS, no un registro poblacional de
cáncer: mide personas hospitalizadas con ese diagnóstico principal, no
incidencia real (alguien con diagnóstico y tratamiento ambulatorio, sin
hospitalización, no aparece). Además cubre mayoritariamente la red pública
(FONASA) y clínicas en convenio, no censa el 100% de las atenciones privadas.
Esto se documenta en el README como limitación central del análisis.
"""

import os
from pathlib import Path

import duckdb

PROYECTO = str(Path(__file__).resolve().parent.parent)
PROYECTO5 = str(Path(PROYECTO).parent / "proyecto5")
RUTAS_BASE = [
    os.environ.get("GRD_DIR", ""),
    f"{PROYECTO}/bases de datos GRD",
    f"{PROYECTO5}/bases de datos GRD",
]
DIR_POR_ANIO = f"{PROYECTO}/data/por_anio"
SALIDA = f"{PROYECTO}/data/crc_admisiones.parquet"

# encoding detectado por archivo: el DEIS cambió de formato entre años
# (mismo hallazgo empírico que proyecto5/src/extract_data.py)
ARCHIVOS = [
    ("GRD_PUBLICO_2019.txt", "utf-8", 2019),
    ("GRD_PUBLICO_2020.txt", "utf-8", 2020),
    ("GRD_PUBLICO_2021.txt", "utf-8", 2021),
    ("GRD_PUBLICO_EXTERNO_2022.txt", "utf-16", 2022),
    ("GRD_PUBLICO_2023.txt", "utf-16", 2023),
    ("GRD_PUBLICO_2024.txt", "latin-1", 2024),
]

DIAG_COLS = ["DIAGNOSTICO1"] + [f"DIAGNOSTICO{i}" for i in range(2, 36)]

# prefijos CIE-10 de cáncer colorrectal invasor (análisis principal)
PREFIJOS_CRC = ["C18", "C19", "C20"]

# categorías relacionadas, extraídas aparte (ver docstring del módulo)
PREFIJOS_ANO = ["C21"]
PREFIJOS_IN_SITU = ["D01.0", "D01.1", "D01.2", "D01.3"]
PREFIJOS_POLIPOS = ["D12.6"]

# todo lo que se extrae de las bases GRD, sea cual sea la categoría final
PREFIJOS_TODOS = PREFIJOS_CRC + PREFIJOS_ANO + PREFIJOS_IN_SITU + PREFIJOS_POLIPOS


def categoria_clinica_sql() -> str:
    """Clasifica DIAGNOSTICO1 en una de las 4 categorías, en SQL."""
    crc = "|".join(PREFIJOS_CRC)
    ano = "|".join(PREFIJOS_ANO)
    in_situ = "|".join(p.replace(".", "\\.") for p in PREFIJOS_IN_SITU)
    polipos = "|".join(p.replace(".", "\\.") for p in PREFIJOS_POLIPOS)
    return f"""
        CASE
            WHEN regexp_matches(DIAGNOSTICO1, '^({crc})') THEN 'cancer_colorrectal'
            WHEN regexp_matches(DIAGNOSTICO1, '^({ano})') THEN 'cancer_ano'
            WHEN regexp_matches(DIAGNOSTICO1, '^({in_situ})') THEN 'carcinoma_in_situ'
            WHEN regexp_matches(DIAGNOSTICO1, '^({polipos})') THEN 'polipo_adenomatoso'
        END
    """


def fecha(col: str) -> str:
    """Parsea fechas en YYYY-MM-DD (mayoría de años) o DD-MM-YYYY (2023)."""
    return (
        f"COALESCE("
        f"TRY_CAST({col} AS DATE), "
        f"TRY_STRPTIME({col}::VARCHAR, '%Y-%m-%d')::DATE, "
        f"TRY_STRPTIME({col}::VARCHAR, '%d-%m-%Y')::DATE"
        f")"
    )


def edad_sql() -> str:
    """Años cumplidos al ingreso (no date_diff('year', ...), que cuenta
    cruces de 1 de enero en vez de cumpleaños)."""
    return f"date_part('year', age({fecha('FECHA_INGRESO')}, {fecha('FECHA_NACIMIENTO')}))"


def id_paciente_sql(anio: int) -> str:
    """El identificador de paciente encriptado cambió de nombre de columna
    en 2024 (CIP_ENCRIPTADO -> ID_BENEFICIARIO). El salto de encriptación
    probablemente también cambió entre años, así que este id solo sirve
    para deduplicar DENTRO de un mismo año, nunca para seguir a una misma
    persona a través de los años."""
    return "ID_BENEFICIARIO" if anio == 2024 else "CIP_ENCRIPTADO"


def condicion_diag1_relevante() -> str:
    patron = "|".join(p.replace(".", "\\.") for p in PREFIJOS_TODOS)
    return f"regexp_matches(DIAGNOSTICO1, '^({patron})')"


def main():
    os.makedirs(DIR_POR_ANIO, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA threads=4")

    for archivo, encoding, anio in ARCHIVOS:
        parquet_anio = f"{DIR_POR_ANIO}/{anio}.parquet"
        if os.path.exists(parquet_anio):
            print(f"{anio}: ya procesado ({parquet_anio}), se omite.")
            continue

        ruta = next((f"{b}/{archivo}" for b in RUTAS_BASE if b and os.path.exists(f"{b}/{archivo}")), None)
        if ruta is None:
            print(f"{anio}: {archivo} no está disponible en ninguna ruta. Se omite por ahora.")
            continue

        print(f"Procesando {archivo} ({encoding})...")
        edad = edad_sql()
        id_paciente = id_paciente_sql(anio)
        query = f"""
            WITH base AS (
                SELECT *, {edad} AS _edad
                FROM read_csv(
                    '{ruta}',
                    delim='|', header=true, quote='', encoding='{encoding}',
                    sample_size=200000, ignore_errors=true
                )
                WHERE FECHA_NACIMIENTO IS NOT NULL AND FECHA_INGRESO IS NOT NULL
                  AND DIAGNOSTICO1 IS NOT NULL
                  AND _edad BETWEEN 0 AND 110
                  AND ({condicion_diag1_relevante()})
            )
            SELECT
                {anio} AS anio,
                {id_paciente} AS id_paciente,
                COD_HOSPITAL AS cod_hospital,
                SERVICIO_SALUD AS servicio_salud,
                SEXO AS sexo,
                _edad AS edad,
                CASE WHEN _edad <= 50 THEN 'menor o igual a 50' ELSE 'mayor a 50' END AS grupo_edad,
                LEAST(CAST(_edad / 10 AS INTEGER) * 10, 90) AS tramo_edad_10,
                ({categoria_clinica_sql()}) AS categoria_clinica,
                month({fecha('FECHA_INGRESO')}) AS mes_ingreso,
                PREVISION AS prevision,
                TIPO_PROCEDENCIA AS tipo_procedencia,
                TIPO_INGRESO AS tipo_ingreso,
                DIAGNOSTICO1 AS diagnostico1_subcodigo,
                SUBSTR(DIAGNOSTICO1, 1, 3) AS diagnostico1_categoria,
                TIPOALTA AS tipo_alta,
                IR_29301_SEVERIDAD AS severidad_grd,
                IR_29301_MORTALIDAD AS mortalidad_grd,
                IR_29301_PESO AS peso_grd
            FROM base
        """
        con.execute(f"COPY ({query}) TO '{parquet_anio}' (FORMAT PARQUET)")
        n = con.execute(f"SELECT count(*) FROM read_parquet('{parquet_anio}')").fetchone()[0]
        print(f"  {n:,} admisiones con diagnóstico principal CRC -> {parquet_anio}")

    disponibles = sorted(f for f in os.listdir(DIR_POR_ANIO) if f.endswith(".parquet"))
    if not disponibles:
        print("No hay ningún año procesado todavía.")
        return

    anios_faltantes = {str(anio) for _, _, anio in ARCHIVOS} - {f.replace(".parquet", "") for f in disponibles}
    if anios_faltantes:
        print(f"\nAdvertencia: faltan por procesar los años {sorted(anios_faltantes)}.")

    con.execute(f"CREATE OR REPLACE TABLE crc AS SELECT * FROM read_parquet('{DIR_POR_ANIO}/*.parquet')")
    total = con.execute("SELECT count(*) FROM crc").fetchone()[0]
    print(f"\nTotal admisiones extraídas ({len(disponibles)} años): {total:,}")
    por_cat = con.execute(
        "SELECT categoria_clinica, count(*) FROM crc GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall()
    for cat, n in por_cat:
        print(f"  {cat}: {n:,}")
    crc_total = con.execute("SELECT count(*) FROM crc WHERE categoria_clinica = 'cancer_colorrectal'").fetchone()[0]
    crc_jovenes = con.execute(
        "SELECT count(*) FROM crc WHERE categoria_clinica = 'cancer_colorrectal' AND grupo_edad = 'menor o igual a 50'"
    ).fetchone()[0]
    print(f"\nDe ellas, cáncer colorrectal (C18-C20): {crc_total:,}")
    print(f"En personas de 50 años o menos: {crc_jovenes:,} ({100*crc_jovenes/crc_total:.1f}%)")

    con.execute(f"COPY crc TO '{SALIDA}' (FORMAT PARQUET)")
    print(f"\nGuardado en {SALIDA}")


if __name__ == "__main__":
    main()
