import csv
import pathlib

class Aggregator:

    """
    Aggregates data from CSV files with the suffix _summary.
    Used to create overall summary of all features for given set of
    analysed sequences
    """

    def __init__(self, suffix="_merged"):
        self.suffix = suffix
        self.headers = None
        self.data = {}
        self.path = "./"

    def load_csv(self, path):
        files = list(path.glob(f'**/*{self.suffix}.csv'))
        self.path = path

        for f in files:
            with open(f, newline='') as sumfile:
                reader = csv.reader(sumfile, delimiter=',')

                headers = next(reader)
                if not self.headers:
                    self.headers = headers

                for row in reader: # continue from 2nd row
                    self.process(row)

        self.aggregate()
        self.to_csv()

    def process(self, row):
        """
        Checks if feature exists. if so, update values, otherwise insert.
        Adds values of feature in case of updating.
        """

        feature_name = row[0]
        feature_stats = row[1:]

        # feature name
        if feature_name not in self.data.keys():
            self.data[feature_name] = feature_stats
        else:
            self.data[feature_name] = [float(x) + float(y) for x, y in zip(self.data[feature_name], feature_stats)]


    def aggregate(self):
        # aggregates percentual data by number of features and formats the output

        for feat, stats in self.data.items():
            int_data = list(map(int, stats[:5]))
            float_data = [float(x) / int_data[0] for x in stats[6:]]
            self.data[feat] = int_data + float_data

    def to_csv(self):
        with open(self.path / 'overall_summary.csv', 'w') as out:
            outwriter = csv.writer(out, delimiter=',')
            outwriter.writerow(self.headers)

            for feat, stats in self.data.items():
                outwriter.writerow([feat] + stats)

            print(f"Overall statistics are stored in file: \n\t{self.path / 'overall_summary.csv'}")

            

    