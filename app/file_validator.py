from app.main import app 

import re

ALLOWED_FILES = {
    "txt": re.compile("NC_\d.+\.?\d.*_ft\.txt"),
    "csv": re.compile("NC_\d.+\.?\d.*_palindromes\.csv")
}

def validate_files(filename, ftype):
    
    if ftype in ALLOWED_FILES.keys():

        if ALLOWED_FILES[ftype].match(filename):
            return True
    
    return False

def get_ncbi(filename):
    return filename.split("_")[1]