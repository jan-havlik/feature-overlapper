import argparse
from pathlib import Path

from analysis_overlapper import overlap_analysis_files
from feature import process_feature_file
from lambdas import (
    feature_to_ncbi,
    ncbi_to_feature,
    ncbi_to_palindrome,
    ncbi_to_sequence,
    palindrome_to_ncbi,
)
from out import aggregate_palindromes, palindrome_stats, stats
from utils import _DIRS, check_dirs

if __name__ == "__main__":

    # process cmd args
    parser = argparse.ArgumentParser(
        description="Overlap palindromes with given features.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ncbi",
        "-i",
        type=str,
        nargs="+",
        help="Specify one or more NCBI IDs to analyse from folder.",
    )
    parser.add_argument(
        "--cmp",
        "-c",
        type=str,
        nargs="+",
        default=["palindrome"],
        choices=["palindrome", "g4", "rloop"],
        help="""\
        Specify comparison method to use. Usage examples:
            --cmp palindrome ... compares palindrome analyses to features
            --cmp rloop,palindrome ... compares rloop analyses to palindromes
            -c g4 ... compares g4hunter analyses to features
        """,
    )
    args = parser.parse_args()

    # create dirs if they do not exist
    check_dirs(_DIRS)

    if len(args.cmp) == 2 and args.ncbi:
        for ncbi in args.ncbi:
            overlap_analysis_files(args.cmp[0], args.cmp[1], ncbi)
    else:
        analysis = args.cmp[0]
        
        iter_object = (
            _DIRS["features"].iterdir()
            if args.ncbi is None
            else [ncbi_to_feature(x) for x in args.ncbi]
        )
        dirnum = len(list(_DIRS["features"].glob("*.txt")))

        # go annotation after annotation in annotations directory
        for ix, annotation_file in enumerate(iter_object, start=1):
            # convert in case of an object

            ncbi = feature_to_ncbi(annotation_file)
            analysis_file = _DIRS[analysis] / f"{ncbi}_{analysis}.csv"

            if not annotation_file.is_file():
                print(f"Feature file {annotation_file} doesn't exist! Skipping...")
                continue
            if not analysis_file.is_file():
                print(
                    f"Feature file {annotation_file} doesn't have matching {analysis} file in `{analysis}` folder! Skipping..."
                )
                continue

            print(f"=== Analysing batch {ncbi} ... ({ix} / {len(iter_object)}) ===")
            if len(list(_DIRS["comparison"].glob(f"{ncbi}.xlsx"))) > 0:
                print(
                    f"\tFeature {ncbi} already processed in comparison folder. Skipping..."
                )
                continue
            features = process_feature_file(ncbi, analysis=analysis)
            palindrome_stats(features, ncbi) if analysis == "palindrome" else stats(features, ncbi, analysis)

        if analysis == "palindrome":
            # aggregate files togehtehr only in case of palindrome analysis
            aggregate_palindromes()