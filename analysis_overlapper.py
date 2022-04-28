import numpy as np
import pandas as pd

from utils import _DIRS

import matplotlib
import matplotlib.pyplot as plt

import pyfastx

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

    df_agg = (
        df.groupby(["Start_x", "End_x"])
        .agg({"Overlap": ["max", "count"]})
        .reset_index()
    )
    # flatten multiindex
    df_agg.columns = ["_".join(a) for a in df_agg.columns.to_flat_index()]
    df_agg["Middle_x"] = ((df_agg["Start_x_"] + df_agg["End_x_"]) // 2).astype(np.int32)

    # Excel output
    writer = pd.ExcelWriter(
        _DIRS["comparison"] / f"{ncbi}_{first}_{second}.xlsx", engine="xlsxwriter"
    )
    df.to_excel(writer, sheet_name=f"{first.capitalize()} to {second.capitalize()}", index=False)
    df_agg.to_excel(writer, sheet_name=f"{first.capitalize()} to {second.capitalize()} GROUPED", index=False)
    writer.save()
    
    # load features
    df_feat = pd.read_excel(_DIRS["comparison"] / f"{ncbi}.xlsx", f"Feature to {first}s")
    df_feat.drop_duplicates(subset=["Feature start", "Feature end"], keep="last", inplace=True)  # remove features on the same interval
    
    df_feat.drop(df_feat[df_feat[f"{first.capitalize()}s count"] < 1].index, inplace=True) # remove features with 0 overlap !!!
    df_agg.drop(df_agg[df_agg[f"Overlap_count"] < 1].index, inplace=True) # remove 0 analysis overlap !!!
    
    df_feat.to_csv(_DIRS["comparison"] / f"raw_{ncbi}_feature.csv")
    df_agg.to_csv(_DIRS["comparison"] / f"raw_{ncbi}_agg.csv")
    
    if df_agg.empty or df_feat.empty:
        print(f"{ncbi} has empty dataframe!")
        return

    # FIRST GRAPH -> Overlap between analyses
    
    df_best_regions = df_agg.loc[df_agg["Overlap_count"] >= 0]
    x = df_best_regions["Middle_x"]
    width = 10000  # the width of the bars
    
    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width/2, round(df_best_regions["Overlap_max"] * 100), width, label='Overlap max coverage [%]')
    rects2 = ax.bar(x + width/2, df_best_regions["Overlap_count"], width, label='Overlap region count [N]')
    ax.set_ylabel('Overlap')
    ax.set_xlabel('Sequence length [N]')
    ax.set_title(f'{first.capitalize()} to {second.capitalize()} max coverage to occurence ratio [{ncbi}]')
    ax.legend()
    ax.set_xlim(x.min() - width, x.max() + width)
    plt.xticks(np.arange(0, x.max()+width, 100000))
    
    figure = plt.gcf()
    figure.set_size_inches(19.2, 10.8)
    plt.savefig(f"./comparison/{ncbi}_analysis.png", dpi=600, format='png', bbox_inches='tight')
    
    # SECOND GRAPH -> HEATMAPS
    seq_len = pyfastx.Fasta(f"./sequences/{ncbi}.fasta").size  # TODO: via API

    one_percent = seq_len / 100
    heatmap_analysis = []
    heatmap_features = []

    for i in range(0,100):
        relative_start = int(i * one_percent)
        relative_end = int(relative_start + 1 + one_percent)
        heatmap_analysis.append(len(df_agg.loc[(df_agg['Overlap_count'] > 0) & (df_agg['Start_x_'] >= relative_start) & (df_agg['End_x_'] <= relative_end)]))
        heatmap_features.append(len(df_feat.loc[(df_feat['Rloops count'] > 0) & (df_feat['Feature start'] >= relative_start) & (df_feat['Feature end'] <= relative_end)]))
        plt.rcParams["figure.figsize"] = 5,2

    x = np.array([i for i in range(0,100)])
    y1 = np.array(heatmap_analysis)
    y2 = np.array(heatmap_features)

    fig, (ax, ax1) = plt.subplots(nrows=2, sharex=True)

    extent = [x[0]-(x[1]-x[0])/2., x[-1]+(x[1]-x[0])/2.,0,1]

    pos_ax = ax.imshow(y1[np.newaxis,:], cmap="plasma", aspect="auto", extent=extent)
    fig.colorbar(pos_ax, ax=ax)
    
    pos_ax1 = ax1.imshow(y2[np.newaxis,:], cmap="plasma", aspect="auto", extent=extent)
    fig.colorbar(pos_ax1, ax=ax1)
    
    
    ax.set_yticks([])
    ax.set_xlim(extent[0], extent[1])
    ax1.set_yticks([])
    ax1.set_xlim(extent[0], extent[1])
    
    
    ax.set_title(f'Overlap count for {second.capitalize()}s and {first.capitalize()}s [{ncbi}]')
    ax1.set_title(f'Overlap count for {first.capitalize()}s and annotations [{ncbi}]')
    
    ax.set_xlabel('Sequence length [N]')
    ax.set_ylabel('Overlap count [N]')
    ax1.set_xlabel('Sequence length [N]')
    ax1.set_ylabel('Overlap count [N]')

    plt.tight_layout()
    figure = plt.gcf()
    figure.set_size_inches(8, 6)
    plt.savefig(f"./comparison/{ncbi}_count.png", dpi=600, format='png', bbox_inches='tight')
