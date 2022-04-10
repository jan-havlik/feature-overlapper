import numpy as np
import pandas as pd

from utils import _DIRS


def overlap_analysis_files(first, second, ncbi):
    print(f"Comparing analyses {first} x {second} for {ncbi}")

    first_data = pd.read_csv(
        _DIRS[first] / f"{ncbi}_{first}.csv",
        usecols=["POSITION", "LENGTH"],
        dtype={"POSITION": np.int32, "LENGTH": np.int16},
        sep="\t",
    )

    second_data = pd.read_csv(
        _DIRS[second] / f"{ncbi}_{second}.csv",
        usecols=["POSITION", "LENGTH"],
        dtype={"POSITION": np.int32, "LENGTH": np.int16},
        sep="\t",
    )

    first_data["Start_x"] = first_data["POSITION"]
    first_data["End_x"] = first_data["Start_x"] + first_data["LENGTH"]
    first_data["NCBI_ID"] = ncbi

    second_data["Start_y"] = second_data["POSITION"]
    second_data["End_y"] = second_data["Start_y"] + second_data["LENGTH"]
    second_data["NCBI_ID"] = ncbi
    second_data["Middle_y"] = ((second_data["Start_y"] + second_data["End_y"]) // 2).astype(
        np.int32
    )

    first_data = first_data.drop(columns=["POSITION", "LENGTH"])
    second_data = second_data.drop(columns=["POSITION", "LENGTH"])

    df = pd.merge(first_data, second_data, on="NCBI_ID")
    df = df.drop(columns=["NCBI_ID"])

    # include second analysis where its middle is still in the first analysis
    df = df.loc[
        (df["Middle_y"] >= df["Start_x"]) & (df["Middle_y"] <= df["End_x"])
    ].sort_values(by=["Start_x"])

    # cut the intervals to match
    df.loc[df["Start_y"] < df["Start_x"], "Start_y"] = df["Start_x"]
    df.loc[df["End_y"] > df["End_x"], "End_y"] = df["End_x"]

    df["Overlap"] = (df["End_y"] - df["Start_y"]) / (df["End_x"] - df["Start_x"])
    total1 = df["End_y"] - df["Start_y"]
    total2 = df["End_x"] - df["Start_x"]

    df_agg = (
        df.groupby(["Start_x", "End_x"])
        .agg({"Overlap": ["sum", "count"]})
        .reset_index()
    )
    # flatten multiindex
    df_agg.columns = ["_".join(a) for a in df_agg.columns.to_flat_index()]

    # Excel output
    writer = pd.ExcelWriter(
        _DIRS["comparison"] / f"{ncbi}_{first}_{second}.xlsx", engine="xlsxwriter"
    )
    df.to_excel(writer, sheet_name=f"{first.capitalize()} to {second.capitalize()}", index=False)
    df_agg.to_excel(writer, sheet_name=f"{first.capitalize()} to {second.capitalize()} GROUPED", index=False)
    writer.save()
