# Feature overlapper

Script used to overlap palindrome analyses with given feature files.

## Environment

This module uses `python3` with help of these following libraries:

- `numpy`
- `pandas`
- `xlsxwriter`
= `openpyxl`

All dependant libs are listed in the `requirements.txt` file. To install them, use the following command:

```
python3 -m pip install -r requirements.txt
```

## The script

The script merges palindrome analysis files in the `palindromes` folder with annotations from NCBI in the `features` folder.

The result is stored in `comparison` folder as detailed format in `{ncbi_id}.txt` file or in excel file `{ncbi_id}.xlsx`. The excel file has 2 worksheets, 
one detailed for every feature and the second in a form of merged results. Finally there is a `overall.xlsx` file which cointains merged data from every feature alltogether.

The graphic output for comparison is **only available when comparing two analysis together**. The graphical overlap will be made between the analysis and with a feature table aswell.

## !important notice

Because of optimalisation, `{ncbi_id}.xlsx` files already present in `comparison` directory **will not be analysed and processed again**. This enables users to stop the analysis and
continue where they stopped whenever they need to.

## Usage

You can run the script as follows:

+ `python3 main.py -c rloop`, which overlaps all available analysis files in `features` directory with those in `rloops` directory, or
+ `python3 main.py -i <ncbi-id> -c g4 rloop`, which runs the analysis only for the selected ncbi and overlaps g-quadruplexes with r-loops.

Single analysis name for the `--cmp` argument always overlaps with features.

## Troubleshooting

If any problem occurs, try deleting everything in the `results` folder and then run the command again.
