import numpy as np
import pandas as pd

from utils import _DIRS


class Annotation:
    def __init__(self, start, end, type):

        self.complementary = True if start > end else False
        if self.complementary:
            start, end = end, start

        self.start = start
        self.end = end
        self.type = type
        self.len = self.end - self.start

        self.info = ""

        self.intervals = None
        self.merged_intervals = None

    def set_info(self, *args):
        if len(args) == 1:
            self.info += f"{args[0].strip()}, "
        else:
            self.info += f"{args[0]} ({args[1].strip()}), "


def process_feature_file(ncbi: str, analysis: str = "palindrome"):
    pd.options.mode.chained_assignment = None
    """
    Opens both feature and analysis file and processes one annotation after another
    """

    ft = open(_DIRS["features"] / f"{ncbi}_ft.txt", "r")
    next(ft)

    annotation = None
    
    analysis_map = {
        "palindrome": {
            "cols": {"Position": np.int32, "Length": np.int16, "Spacer length": np.int16},
            "to_drop": ["Spacer length"],
        },
        "g4": {
            "cols": {"POSITION": np.int32, "LENGTH": np.int16},
            "to_drop": ["LENGTH"],
        },
        "rloop": {
            "cols": {"POSITION": np.int32, "LENGTH": np.int16},
            "to_drop": ["LENGTH"],
        }
    }
    analysis_df = pd.read_csv(
        _DIRS[analysis] / f"{ncbi}_{analysis}.csv",
        delimiter='\t',
        usecols=list(analysis_map[analysis]["cols"].keys()),
        dtype=analysis_map[analysis]["cols"]
    )

    analysis_df = analysis_df.rename(columns={"Position" if analysis=="palindrome" else "POSITION": "start"})
    analysis_df["start"] += 1  # features are indexed from 1 :()

    # palindrome has different end position calculation
    if analysis=="palindrome":
        analysis_df["end"] = analysis_df["start"] + 2 * analysis_df["Length"] + analysis_df["Spacer length"]
    else:
        analysis_df["end"] = analysis_df["start"] + analysis_df["LENGTH"]

    analysis_df["middle"] = ((analysis_df["start"] + analysis_df["end"]) / 2).astype(np.int32)
    analysis_df["len"] = analysis_df["Length" if analysis=="palindrome" else "LENGTH"]

    analysis_df = analysis_df.drop(columns=analysis_map[analysis]["to_drop"])

    annotations = []
    
    for ft_line in ft:
        split = [x.strip("<>\n") for x in ft_line.split("\t")]
        splitlen = len(split)

        if splitlen in (2, 3):  # new annotation

            if splitlen == 2:  # uses type from previous annotation
                split.append(annotation.type)

            if annotation:  # print to csv file BUT REMEBER TO WRITE ALSO THE LAST ONE IN EOF PART
                annotations.append(process(analysis_df, annotation))

            annotation = Annotation(start=int(split[0]), end=int(split[1]), type=split[2])

        elif splitlen == 4:
            annotation.set_info(split[3])
        elif splitlen == 5:
            annotation.set_info(split[3], split[4])
        elif splitlen == 1:
            # EOF
            annotations.append(process(analysis_df, annotation))
            break

    ft.close()
    return annotations


def process(df: pd.DataFrame, annotation: Annotation):
    """Processes one annotation.
       Finds overlapping analyses for given annotation.

    Args:
        df (pd.DataFrame): _description_
        annotation (Annotation): _description_
    """

    # if the middle of the palindrome is still inside annotation, we include that palindrome
    df = df.loc[
        (df["middle"] >= annotation.start) & (df["middle"] <= annotation.end)
    ]
    if len(df > 0):

        # calculate coverage for non-overlapping palindromes
        diff = annotation.end - annotation.start

        # normalise start/end positions for overlap, but keep original start/end values for output
        # when we have shorter annotation than last palindrome, we need to count the overlap only for
        # the length of the annotation
        df["cov_end"] = df["end"].apply(
            lambda col: annotation.end if col > annotation.end else col
        )
        df["cov_start"] = df["start"].apply(
            lambda col: annotation.start if annotation.start > col else col
        )

        df["coverage"] = (df.loc[:, "cov_end"] - df.loc[:, "cov_start"]) / diff * 100.0
        annotation.intervals = df

        # new dataframe
        df["overlap_group"] = (df["start"] > df["end"].shift()).cumsum()
        merged_df = df.groupby("overlap_group").agg({"start": "min", "end": "max"})

        # calculate cov for overlapping palindromes
        # same normalisation process
        merged_df["cov_end"] = merged_df["end"].apply(
            lambda col: annotation.end if col > annotation.end else col
        )
        merged_df["cov_start"] = merged_df["start"].apply(
            lambda col: annotation.start if annotation.start > col else col
        )

        merged_df["len"] = (
            merged_df.loc[:, "cov_end"] - merged_df.loc[:, "cov_start"]
        )
        merged_df["coverage"] = merged_df["len"] / diff * 100.0
        annotation.merged_intervals = merged_df

    return annotation
