from pathlib import Path

_DIRS = {
    "features": Path("./features/"),
    "comparison": Path("./comparison/"),
    "palindrome": Path("./palindromes/"),
    "sequences": Path("./sequences/"),
    "rloop": Path("./rloops/"),
    "g4": Path("./g4s/"),
}

_CSV_HEADERS = [
    "Feature",
    "Info",
    "Feature start",
    "Feature end",
    "Feature size",
    "Palindromes count",
    "Palindromes count 8+",
    "Palindromes count 10+",
    "Palindromes count 12+",
    "Average coverage all IRs - merged overlapping IRs",
    "Average coverage all IRs - non-overlapping IRs",
    "Average coverage IR 8+ - merged overlapping IRs",
    "Average coverage IR 8+ - non-overlapping IRs",
    "Average coverage IR 10+ - merged overlapping IRs",
    "Average coverage IR 10+ - non-overlapping IRs",
    "Average coverage IR 12+ - merged overlapping IRs",
    "Average coverage IR 12+ - non-overlapping IRs",
]


def check_dirs(dirs):
    """
    checks if dirs exist and creates them ifnot
    """
    for dir in dirs.values():
        if not dir.exists() or not dir.is_dir():
            dir.mkdir()
