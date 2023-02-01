from pathlib import Path

from utils import _DIRS

# lambdas for conversion
feature_to_ncbi = lambda x: x.name.strip("_ft.txt")
palindrome_to_ncbi = lambda x: x.name.strip("_palindromes.csv")
ncbi_to_feature = lambda x: _DIRS["features"] / f"{x}.txt"
ncbi_to_palindrome = lambda x: _DIRS["palindromes"] / f"{x}_palindromes.csv"
ncbi_to_sequence = lambda x: _DIRS["sequences"] / f"{x}.fasta"
