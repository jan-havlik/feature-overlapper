from feature_overlapper.util import get_seq_len, get_palindrome_count, get_palindrome_coverage


class TxtWriter:

    def __init__(self, file):
        self.file = file

    def print_general_stats(self, ncbi_id, totals):

        seq_len = get_seq_len(ncbi_id)
        
        # total palindrome len to seq len 
        palindromes_to_seq = "%.2f" % (100 * (len(totals["palindromes"]) / seq_len))
        palindromes_to_seq_mo = "%.2f" % (100 * (len(totals["palindromes_merged"]) / seq_len))
        
        self.file.write("*******************\n")
        self.file.write(f"GENERAL STATISTICS: {ncbi_id}\n")
        self.file.write(f"\tPalindromes to sequence length ratio: {palindromes_to_seq}%\n")
        self.file.write(f"\tPalindromes to sequence length ratio (merged overlap): {palindromes_to_seq_mo}%\n")


        # total features len to seq len 
        features_to_seq = "%.2f" % (100 * (len(totals["features"]) / seq_len))

        self.file.write(f"\tFeatures to sequence length ratio: {features_to_seq}%\n")

        # how many nucleotides in inverse repetitions are the same for each feature
        palindromes_to_features_perc = "%.2f" % (100 * (len(list(totals["palindromes"] & totals["features"]))*1.0 / len(totals["features"])*1.0))
        palindromes_to_features_perc_mo = "%.2f" % (100 * (len(list(totals["palindromes_merged"] & totals["features"]))*1.0 / len(totals["features"])*1.0))

        self.file.write(f"\tPalindromes to features ratio: {palindromes_to_features_perc}%\n")
        self.file.write(f"\tPalindromes to features ratio (merged overlap): {palindromes_to_features_perc_mo}%\n")
        self.file.write("*******************\n\n")


    def print_feature_stats(self, feature):


        self.file.write(f"FEATURE STATISTICS: {feature.ncbi_id}\n")
        self.file.write(f"==================")

        feat_out = "\n\nFeature: %d - %d (%s)\n\t<palindromes>\t<palindrome-to-feature-ratio>\n" % (feature.start, feature.end, feature.type)
        feat_out_mo = "\n\t<palindromes>\t<palindrome-to-feature-ratio> (merged overlap)\n"

        p_str = ""
        p_mo_str = ""
        for p in feature.palindromes:

            if p.merged:
                p_mo_str += "\t%d - %d\t%.2f%%\n" % (p.start, p.end, p.coverage * 100.0)
            else:
                p_str += "\t%d - %d\t%.2f%%\n" % (p.start, p.end, p.coverage * 100.0)


        if p_str != "":
            self.file.write("\n**************************")
            self.file.write(feat_out + p_str+"\n")
            self.file.write("  Palindomes in this feature: %d\n" % (feature.palindrome_count(merged=False)))

            self.file.write("  Total palindrome to feature ratio in this feature: %.2f%%\n" % (feature.sum_ratio(merged=False)))

        if p_mo_str != "":
            self.file.write(feat_out_mo + p_mo_str+"\n")
            self.file.write("  Palindomes in this feature (merged overlap): %d\n" % (feature.palindrome_count(merged=True)))

            self.file.write("  Total palindrome to feature ratio in this feature (merged overlap): %.2f%%\n\n" % (feature.sum_ratio(merged=True)))


class CsvWriter:

    def __init__(self):

        self.CSV_HEADERS = [
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
            "Average coverage IR 12+ - non-overlapping IRs"
        ]


    def write_headers(self, writer):
        writer.writerow(self.CSV_HEADERS)


    def print_features_csv(self, writer, feat, summarized_features):
        row = [
            feat.type,
            feat.info,
            feat.start,
            feat.end,
            abs(feat.end - feat.start),
            get_palindrome_count(feat.palindromes, 0),
            get_palindrome_count(feat.palindromes, 8),
            get_palindrome_count(feat.palindromes, 10),
            get_palindrome_count(feat.palindromes, 12),
            get_palindrome_coverage(feat.type, feat.palindromes, 0),
            get_palindrome_coverage(feat.type, feat.palindromes, 0, True),
            get_palindrome_coverage(feat.type, feat.palindromes, 8),
            get_palindrome_coverage(feat.type, feat.palindromes, 8, True),
            get_palindrome_coverage(feat.type, feat.palindromes, 10),
            get_palindrome_coverage(feat.type, feat.palindromes, 10, True),
            get_palindrome_coverage(feat.type, feat.palindromes, 12),
            get_palindrome_coverage(feat.type, feat.palindromes, 12, True)
        ]

        writer.writerow(row)

        # summary stats
        if feat.type in summarized_features.keys(): # update stats         
            summarized_features[feat.type]["Feature count"] += 1

            for col in list(summarized_features[feat.type].values())[2:]:
                for i in range(4, len(row)): # skip feat information
                    col += row[i]
        else: # new feature
            summarized_features[feat.type] = {
                "Feature": feat.type,
                "Feature count":  1,
                "Total feature length":  row[3],
                "Palindromes count all":  row[4],
                "Palindromes count 8+":  row[5],
                "Palindromes count 10+":  row[6],
                "Palindromes count 12+":  row[7],
                "Average coverage all IRs - merged overlapping IRs":  row[8],
                "Average coverage all IRs - non-overlapping IRs":  row[9],
                "Average coverage IR 8+ - merged overlapping IRs":  row[10],
                "Average coverage IR 8+ - non-overlapping IRs":  row[11],
                "Average coverage IR 10+ - merged overlapping IRs":  row[12],
                "Average coverage IR 10+ - non-overlapping IRs":  row[13],
                "Average coverage IR 12+ - merged overlapping IRs":  row[14],
                "Average coverage IR 12+ - non-overlapping IRs":  row[15]
            }


    def print_summary_csv(self, writer, summarized_features):

        header = True
        for sum_feat in summarized_features.values():

            if header:
                writer.writerow(sum_feat.keys())
                header = False

            writer.writerow(sum_feat.values())


