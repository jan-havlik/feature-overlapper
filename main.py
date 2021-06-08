import argparse

from pathlib import Path

from lambdas import (feature_to_ncbi, palindrome_to_ncbi, ncbi_to_feature, ncbi_to_palindrome)
from utils import check_dirs, _DIRS
from feature import process_feature_file
from out import stats, aggregate_analysis

import cProfile
from pstats import Stats, SortKey

if __name__ == '__main__':


    # process cmd args
    parser = argparse.ArgumentParser(description='Overlap palindromes with given features.')
    parser.add_argument('--ncbi', '-i', type=str, nargs='+', help='Specify one or more NCBI IDs to analyse from folder.')
    parser.add_argument("--profile", action="store_true", help="Generate profile file for snakeviz (ADVANCED USAGE)")
    args = parser.parse_args()

    def _run():
        # create dirs if they do not exist
        check_dirs(_DIRS)

        iter_object = _DIRS["features"].iterdir() if args.ncbi is None else [ncbi_to_feature(x) for x in args.ncbi]
        dirnum = len(list(_DIRS["features"].glob('*.txt')))

        # go annotation after annotation in annotations directory
        for ix, annotation_file in enumerate(iter_object, start=1):
            # convert in case of an object

            ncbi = feature_to_ncbi(annotation_file)
            palindrome_file = ncbi_to_palindrome(ncbi)
            
            if not annotation_file.is_file():
                print(f"Feature file {annotation_file} doesn't exist! Skipping...")
                continue
            if not palindrome_file.is_file():
                print(f"Feature file {annotation_file} doesn't have matching palindrome file in `palindromes` folder! Skipping...")
                continue
            
            print(f"\t=== Analysing batch {ncbi} ... ({ix} / {dirnum}) ===")
            try:
                if len(list(_DIRS["comparison"].glob(f"{ncbi}.xlsx"))) > 0:
                    print(f"\tFeature {ncbi} already processed in comparison folder. Skipping...")
                    continue
                features = process_feature_file(ncbi)
                stats(features, ncbi)
            except Exception as exc:
                with open(_DIRS["comparison"] / f"{ncbi}.err", "w") as err:
                    err.write(str(exc))

        aggregate_analysis()
    
    if args.profile:
        
        profile = cProfile.Profile()
        profile.enable()
        _run()
        profile.disable()

        with open('profiling_stats.txt', 'w') as stream:
            stats = Stats(profile, stream=stream)
            stats.strip_dirs()
            stats.sort_stats('time')
            stats.dump_stats('.prof_stats')
            stats.print_stats()
    else:
        _run()
