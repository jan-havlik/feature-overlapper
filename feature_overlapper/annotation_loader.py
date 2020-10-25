import copy

from io import StringIO

class AnnotationLoader:

    def __init__(self):
        self.ncbi = "" # ncbi id
        self.annotations = []
        
    def load(self, path, file=None):
        
        if file:
            af = file
        else:
            af = open(path, 'r')

        try:
            # get ncbi id from the first line
            self.ncbi = af.readline().split('|')[1]
        except IndexError:
            print("No NCBI ID defined in the first line of the file.")

        info_line = ""
        # file processing
        for line in af:

            splitted = [x.strip('<>') for x in line.split('\t')]
            complementary = False

            if splitted[0] == '':
                
                if len(splitted) >= 5:
                    info_line += f"{splitted[3]} ({splitted[4].strip()}), "
                else:
                    info_line += f"{splitted[3].strip()}, "
                
                continue
            
            try: # feature position
                start,end = int(splitted[0]), int(splitted[1])
                if start > end:
                    # analyse complementary strand
                    start, end = end, start
                    complementary = True

                type = splitted[2].strip() if len(splitted) > 2 else type
                """
                There might be a situation, where we have same feature defined on multiple places in sequence.
                e.g.:

                529	12354	CDS
                12354	20417
                                product	ORF1ab polyprotein
                                product	frameshift product
                                protein_id	ref|NP_066134.1|
                                evidence	experimental 
                
                that's why we cannot use tabs to determine loci identification
                """
                annotation = Annotation(
                    start=start,
                    end=end,
                    complementary=complementary,
                    type=type,
                    info=str(info_line),
                    ncbi_id=self.ncbi
                )
                self.annotations.append(annotation)
                info_line = ""
            except ValueError:
                # some garbage
                pass
            except IndexError:
                af.close()
                break # EOF
        af.close()

    def return_annotations(self):
        return self.annotations


class Annotation:
    def __init__(self, start, end, complementary, type, info, ncbi_id):
        self.start = start
        self.end = end
        self.complementary = complementary
        self.type = type
        self.info = info
        self.range = set(range(self.start, self.end))
        self.ncbi_id = ncbi_id # id which annotation belongs to
        self.palindromes = []

    def add_palindrome(self, palindrome):

        """
        adds a deep copy of palindrome to given feature
        if the feature contains the palindrome coordinates
        """

        if not palindrome.range.isdisjoint(self.range): # no need to build the set
                
                # add palindrome to the feature
                # notice! here is a deep copy mechanism, because we need to
                # set ratio for the feature (without it, we could overwrite palindrome objects)
                pal_cp = copy.deepcopy(palindrome)
                pal_cp.set_coverage(len(pal_cp.range & self.range) / len(self.range))
                self.palindromes.append(pal_cp)

    def palindrome_count(self, merged=False):
        pals = [x for x in self.palindromes if x.merged == merged]
        return len(pals)
        

    def sum_ratio(self, merged=False):
        pals = [x for x in self.palindromes if x.merged == merged]
        return sum([p.coverage * 100.0 for p in pals], 0.0)
