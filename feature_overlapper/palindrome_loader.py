import csv
import re

class PalindromeLoader:

    def __init__(self):
        self.palindromes = []

    def load(self, path):
        with open(path, newline='') as csv_f:
            reader = csv.reader(csv_f, delimiter=',', quotechar='|')
            next(reader) # skip header
            for row in reader:

                start = int(row[1].strip('"'))
                # calculate end position of inverse repetition
                # length * 2 + spacer
                end = start + (int(row[2].strip('"')) * 2 + int(row[3].strip('"')))

                # length of the palindrome taken as the first number. e.g. 6-0-1 -> len is 6
                length = int(row[0].strip('"').split('-')[0])

                self.palindromes.append(Palindrome(start, end, length))

    def return_palindromes(self):
        return self.palindromes



class Palindrome:

    def __init__(self, start, end, length, merged=False):
        self.start = start
        self.end = end
        self.length = length
        self.coverage = 0.0
        self.range = set(range(self.start, self.end))
        self.merged = merged


    def set_coverage(self, coverage):
        # later after detection
        self.coverage = coverage

    