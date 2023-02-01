import argparse
from pathlib import Path

from analysis_overlapper import overlap_analysis_files
from feature import overlap_with_annotations
from lambdas import (
    feature_to_ncbi,
    ncbi_to_feature,
    ncbi_to_palindrome,
    ncbi_to_sequence,
    palindrome_to_ncbi,
)
from out import aggregate_palindromes, palindrome_stats, stats
from remote_api import Remote
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
        help="Specify one or more NCBI IDs to analyse from folder. If the file doesn't exist in folder, it will be downloaded and analysed",
    )
    parser.add_argument(
        "--cmp",
        "-c",
        type=str,
        nargs="+",
        required=True,
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
        # compare two analyses
        for ncbi in args.ncbi:
            overlap_analysis_files(args.cmp[0], args.cmp[1], ncbi)
    else:
        overlap_with_annotations(args.cmp[0], args.ncbi)
