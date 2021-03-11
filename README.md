# Prerequisities

- `python version >= 3.6`
- `pathlib, xml and urllib.requests` should be part of standard library already

# Usage

Script starts processing data by running the `main.py` file as:
```
python3 main.py
```

Script has no command line arguments, it relies on the following directory structure:

## Features

Features should be places in the `features` directory. Each feature has to have specific name:
```
<ncbi_id>_ft.txt
```
e.g. `NC_001451_ft.txt`.

## Palindrome analyzes

Palindrome analysis should be placed in the `palindromes` directory. Each analysis has to have specific name:
```
<ncbi_id>_palindrome.csv
```
e.g. `NC_001451_palindromes.csv`.

# Processing

The script will match every feature (in `features` directory) file by given NCBI ID to analyzes (in `palindromes` directory) and compares them.

Results will be stored in `comparison` directory again according to the NCBI ID.
