import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from pathlib import Path

_COMPARISON_DIR = Path("./comparison/")
_PALINDROME_RES_DIR = Path("./palindromes/")
_FEATURES_RES_DIR = Path("./features/")
_SEQ_SUMMARY_DIR = Path("./seq_summary/")


def get_seq_len(ncbi_id):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={ncbi_id}&rettype=fasta&retmode=xml"
    request = Request(url)
    res = urlopen(request)

    if res.status > 200:
        print(f"Request to NCBI server failed due to {res.status}:{res.reason}")
        exit(1)
    
    with open(_SEQ_SUMMARY_DIR / f'{ncbi_id}.xml', 'w') as f: 
        f.write(res.read().decode('ascii'))

    root = ET.parse(_SEQ_SUMMARY_DIR / f'{ncbi_id}.xml').getroot()
    return int(root.find("./TSeq/TSeq_length").text) * 1.0


def get_palindrome_count(palindromes, category, merged=False):

    """
    returns statistics about palindromes for given feature
    accroidng to category

    for example:
        category=6 returns count of 6+ palindromes
    """
    count = 0
    for p in palindromes:

        if p.length >= int(category) and (merged == p.merged):
            count += 1
    
    return count


def get_palindrome_coverage(fname, palindromes, category, merged=False):

    """
    returns statistics about palindromes for given feature
    accroidng to category

    for example:
        category=6 returns coverage of 6+ palindromes
        category=0 returns coverage of all palindromes
    """
    coverage = 0.0
    for p in palindromes:

        if p.length >= int(category) and (merged == p.merged):
            coverage += p.coverage

    return coverage / 100.0
