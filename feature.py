import numpy as np
import pandas as pd

from lambdas import ncbi_to_feature, ncbi_to_palindrome


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

        self.non_o_palindromes = None
        self.o_palindromes = None

    
    def set_info(self, *args):
        if len(args) == 1:
            self.info += f"{args[0].strip()}, "
        else:
            self.info += f"{args[0]} ({args[1].strip()}), "




def process_feature_file(ncbi):
    pd.options.mode.chained_assignment = None
    """
    Opens both feature and palindrome file and processes one annotation after another
    """

    ft = open(ncbi_to_feature(ncbi), 'r')
    next(ft)

    annotation = None

    pal_df = pd.read_csv(
        ncbi_to_palindrome(ncbi),
        usecols=['Position', 'Length', 'Spacer length'],
        dtype={'Position': np.int32, 'Length': np.int16, 'Spacer length': np.int16}
    )
    pal_df = pal_df.rename(columns={'Position': 'start'})
    pal_df["start"] += 1 # features are indexed from 1 :()
    pal_df["end"] = (pal_df["start"] + 2 * pal_df["Length"] + pal_df["Spacer length"])
    pal_df["middle"] = ((pal_df["start"] + pal_df["end"]) / 2).astype(np.int32)
    pal_df["len"] = pal_df["Length"]

    pal_df = pal_df.drop(columns=['Spacer length'])

    annotations = []

    for ft_line in ft:
        split = [x.strip('<>\n') for x in ft_line.split('\t')]
        splitlen = len(split)

        if splitlen in (2, 3): # new annotation

            if splitlen == 2:  # uses type from previous annotation
                split.append(annotation.type)

            if annotation: # print to csv file BUT REMEBER TO WRITE ALSO THE LAST ONE IN EOF PART
                annotations.append(process_palindrome(pal_df, annotation))

            annotation = Annotation(
                start=int(split[0]),
                end=int(split[1]),
                type=split[2]
            )

        elif splitlen == 4:
            annotation.set_info(split[3])
        elif splitlen == 5:
            annotation.set_info(split[3], split[4])
        elif splitlen == 1:
            # EOF
            annotations.append(process_palindrome(pal_df, annotation))
            break

    ft.close()
    return annotations


def process_palindrome(pal_df, annotation):

    # if the middle of the palindrome is still inside annotation, we include that palindrome
    df = pal_df.loc[(pal_df['middle'] >= annotation.start) & (pal_df['middle'] <= annotation.end)]
    if len(df > 0):

        # calculate coverage for non-overlapping palindromes
        diff = annotation.end - annotation.start
        
        # normalise start/end positions for overlap, but keep original start/end values for output
        # when we have shorter annotation than last palindrome, we need to count the overlap only for
        # the length of the annotation
        df["cov_end"] = df["end"].apply(lambda col: annotation.end if col > annotation.end else col)
        df["cov_start"] = df["start"].apply(lambda col: annotation.start if annotation.start > col else col)

        df["coverage"] =  (df.loc[:, "cov_end"] - df.loc[:, "cov_start"]) / diff * 100.0
        annotation.non_o_palindromes = df

        # new dataframe
        df["overlap_group"] = (df["start"] > df["end"].shift()).cumsum()
        overlap_df = df.groupby("overlap_group").agg({"start":"min", "end": "max"})

        # calculate cov for overlapping palindromes
        # same normalisation process
        overlap_df["cov_end"] = overlap_df["end"].apply(lambda col: annotation.end if col > annotation.end else col)
        overlap_df["cov_start"] = overlap_df["start"].apply(lambda col: annotation.start if annotation.start > col else col)

        overlap_df["len"] = (overlap_df.loc[:, "cov_end"] - overlap_df.loc[:, "cov_start"])
        overlap_df["coverage"] = overlap_df["len"] / diff * 100.0
        annotation.o_palindromes = overlap_df

    return annotation