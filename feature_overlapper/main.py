from os.path import basename

import csv
import copy
import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile

from feature_overlapper.annotation_loader import AnnotationLoader
from feature_overlapper.palindrome_loader import PalindromeLoader, Palindrome
from feature_overlapper.aggregator import Aggregator
from feature_overlapper.output import TxtWriter, CsvWriter
from feature_overlapper.util import (
    _COMPARISON_DIR,
    _PALINDROMES_DIR,
    _FEATURES_DIR,
    _SUMMARY_DIR
)


def rearrange_overlapping_palindromes(pals):
    """
    correct palindrome results in case some of them are overlapping

    e.g.

    Feature: 25488 - 25685 (CDS)
    <palindromes> <palindrome-to-feature-ratio>
    25517 - 25537 10.15%
    25521 - 25537 8.12%
    25546 - 25566 10.15%
    25548 - 25562 7.11%
    25552 - 25574 11.17%
    25590 - 25616 13.20%
    25647 - 25663 8.12%
    25651 - 25671 10.15%

    these palindromes transform into:

    25517-25537 10.15%
    25546-25574 14.21%
    25590-25616 13.20%
    25647-25671 12.18%
    """

    non_overlapping = []

    # take initial reference values, palindromes are sorted
    final_start = pals[0].start
    final_end = pals[0].end
    final_len = pals[0].length

    for palindrome in pals:
        
        if final_end < palindrome.start:
            non_overlapping.append(Palindrome(start=final_start, end=final_end, length=final_len, merged=True))
            final_start = palindrome.start

        final_end = palindrome.end
        final_len = palindrome.length

    return non_overlapping

def zip_results(unlink=False):

    zip_file = zipfile.ZipFile('/tmp/results.zip', 'w')

    for f in Path(_COMPARISON_DIR).iterdir():
        zip_file.write(f, basename(f))
        
        if unlink:
        # removes files after processing, useful for server calls
            f.unlink()
    
    zip_file.close()
    return zip_file


def compare_results(features, palindromes, ncbi_id):

    Path(_COMPARISON_DIR).mkdir(parents=True, exist_ok=True) # /comparison
    Path(_SUMMARY_DIR).mkdir(parents=True, exist_ok=True) # /seq_summary

    # file handlers
    result_file = open(_COMPARISON_DIR / f'{ncbi_id}_palindrome_to_feature.txt', 'w')

    feature_csv = open(_COMPARISON_DIR / f'{ncbi_id}_feature_palindromes.csv', 'w')
    feature_writer = csv.writer(feature_csv, delimiter=',')
    feature_reader = csv.reader(feature_csv, delimiter=',')


    merged_csv = open(_COMPARISON_DIR / f'{ncbi_id}_merged.csv', 'w')
    merged_writer = csv.writer(merged_csv, delimiter=',')

    # used for length ratio
    # actually stores range of unique (set) positions of each palindrome and feature
    totals = {
        "features": set(),
        "palindromes": set(),
        "palindromes_merged": set()
    }

    # palindromes where overlap is merged
    palindromes_merged_overlap = rearrange_overlapping_palindromes(palindromes)

    print(f" === Analysing batch {ncbi_id} === ")
    
    # load data!
    for f in features:

        totals["features"] = {*totals["features"], *f.range}

        for p in palindromes:
            totals["palindromes"] = {*totals["palindromes"], *p.range}
            f.add_palindrome(p)   
        
        for p_mo in palindromes_merged_overlap:
            totals["palindromes_merged"] = {*totals["palindromes_merged"], *p_mo.range}    
            f.add_palindrome(p_mo)

        print(f"Processed feature {f.type} ({f.start} - {f.end}) with {len(f.palindromes)} palindromes.")

    # let the printing begin!
    # we loop through features again ... it's ugly, but it's for the sake of order of data in the file

    txt_writer = TxtWriter(result_file)
    csv_writer = CsvWriter()

    summarized_features = {}

    print("\n *** Beginning file export *** ")

    txt_writer.print_general_stats(ncbi_id, totals)
    csv_writer.write_headers(feature_writer)
    for f in features:
        txt_writer.print_feature_stats(f)
        csv_writer.print_features_csv(feature_writer, f, summarized_features)

    print("Succesfully stored feature info into following files: ")
    print(f"\t{result_file.name}\n\t{feature_csv.name}\n")
    print(f"Merged features are stored in file: \n\t{merged_csv.name}\n\n")
    
    csv_writer.print_summary_csv(merged_writer, summarized_features)

    # teardown
    result_file.close()
    feature_csv.close()
    merged_csv.close()


def main():

    """
    iterates over every file in selected directories and matches them
    together by NCBI id
    """
    _NCBI_ID = None

    # init environment, create default folders if they do not exist
    Path(_FEATURES_DIR).mkdir(parents=True, exist_ok=True) # /features
    Path(_PALINDROMES_DIR).mkdir(parents=True, exist_ok=True) # /palindromes
    Path(_COMPARISON_DIR).mkdir(parents=True, exist_ok=True) # /comparison
    Path(_SUMMARY_DIR).mkdir(parents=True, exist_ok=True) # /seq_summary

    pathlist_annotations = Path(_FEATURES_DIR).glob('**/*_ft.txt')
    for path_obj in pathlist_annotations:
        path = str(path_obj.as_posix()) # ensure slash format

        # get filename - should be always at pos1
        fn = path.split("/")[1]
        # and then get a ncbi id
        try:
            _NCBI_ID = "NC_" + fn.split("_")[1]
        except IndexError:
            print(f"Invalid feature file: {fn}")
            exit(1)

        af = AnnotationLoader()
        af.load(_FEATURES_DIR / f"{_NCBI_ID}_ft.txt")

        pf = PalindromeLoader()
        pf.load(_PALINDROMES_DIR / f"{_NCBI_ID}_palindromes.csv")

        compare_results(af.return_annotations(), pf.return_palindromes(), _NCBI_ID)

    # create overall summary file
    aggregator = Aggregator()
    aggregator.load_csv(_COMPARISON_DIR)


if __name__ == "__main__":
    main()
