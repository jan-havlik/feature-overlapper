import pandas as pd
import xlsxwriter

from utils import _DIRS


def palindrome_stats(features, ncbi):

    txt = open(_DIRS["results"] / f"{ncbi}.txt", "w")

    workbook = xlsxwriter.Workbook(
        _DIRS["results"] / f"{ncbi}.xlsx", {"nan_inf_to_errors": True}
    )
    ws_solo = workbook.add_worksheet("Feature to palindromes")
    ws_merged = workbook.add_worksheet("Merged features")
    bold = workbook.add_format({"bold": True})

    ws_solo.set_column(0, 0, 10)
    ws_solo.set_column(1, 1, 40)
    ws_solo.set_column(2, 4, 15)
    ws_solo.set_column(4, 8, 23)
    ws_solo.set_column(8, 16, 50)

    ws_merged.set_column(0, 6, 23)
    ws_merged.set_column(6, 15, 50)

    # add headers for xlsx file
    headers_solo = {
        "A1": "Feature",
        "B1": "Info",
        "C1": "Feature start",
        "D1": "Feature end",
        "E1": "Feature size",
        "F1": "Palindromes count",
        "G1": "Palindromes count 8+",
        "H1": "Palindromes count 10+",
        "I1": "Palindromes count 12+",
        "J1": "Average coverage all IRs - merged overlapping IRs",
        "K1": "Average coverage all IRs - non-overlapping IRs",
        "L1": "Average coverage IR 8+ - merged overlapping IRs",
        "M1": "Average coverage IR 8+ - non-overlapping IRs",
        "N1": "Average coverage IR 10+ - merged overlapping IRs",
        "O1": "Average coverage IR 10+ - non-overlapping IRs",
        "P1": "Average coverage IR 12+ - merged overlapping IRs",
        "Q1": "Average coverage IR 12+ - non-overlapping IRs",
    }
    headers_merged = {
        "A1": "Feature",
        "B1": "Feature count",
        "C1": "Total feature length",
        "D1": "Palindromes count all",
        "E1": "Palindromes count 8+",
        "F1": "Palindromes count 10+",
        "G1": "Palindromes count 12+",
        "H1": "Average coverage all IRs - merged overlapping IRs",
        "I1": "Average coverage all IRs - non-overlapping IRs",
        "J1": "Average coverage IR 8+ - merged overlapping IRs",
        "K1": "Average coverage IR 8+ - non-overlapping IRs",
        "L1": "Average coverage IR 10+ - merged overlapping IRs",
        "M1": "Average coverage IR 10+ - non-overlapping IRs",
        "N1": "Average coverage IR 12+ - merged overlapping IRs",
        "O1": "Average coverage IR 12+ - non-overlapping IRs",
    }
    for index, name in headers_solo.items():
        ws_solo.write(index, name, bold)

    for index, name in headers_merged.items():
        ws_merged.write(index, name, bold)

    merged_feature_data = {}

    # General statisctics
    txt.write(f"ANNOTATION STATISTICS: {ncbi}\n")
    txt.write(f"==================\n\n")

    for rownum, feat in enumerate(features, start=1):
        txt.write(f"Feature: {feat.start} - {feat.end} ({feat.type})\n")

        # xlsx feature info
        ws_solo.write(rownum, 0, feat.type)
        ws_solo.write(rownum, 1, feat.info)
        ws_solo.write(rownum, 2, feat.start)
        ws_solo.write(rownum, 3, feat.end)
        ws_solo.write(rownum, 4, feat.end - feat.start)

        # non-overlapping
        txt.write("\t<palindromes>	<palindrome-to-feature-ratio>\n")
        if feat.intervals is not None:

            # xlsx palindrome info

            p_all_cov_non = feat.intervals["coverage"]
            p8_cov_non = feat.intervals.loc[feat.intervals["len"] >= 8]["coverage"]
            p10_cov_non = feat.intervals.loc[feat.intervals["len"] >= 10]["coverage"]
            p12_cov_non = feat.intervals.loc[feat.intervals["len"] >= 12]["coverage"]

            ws_solo.write(rownum, 5, p_all_cov_non.count())
            ws_solo.write(rownum, 6, p8_cov_non.count())
            ws_solo.write(rownum, 7, p10_cov_non.count())
            ws_solo.write(rownum, 8, p12_cov_non.count())

            ws_solo.write(
                rownum, 10, p_all_cov_non.mean() if not p_all_cov_non.empty else 0.0
            )
            ws_solo.write(
                rownum, 12, p8_cov_non.mean() if not p8_cov_non.empty else 0.0
            )
            ws_solo.write(
                rownum, 14, p10_cov_non.mean() if not p10_cov_non.empty else 0.0
            )
            ws_solo.write(
                rownum, 16, p12_cov_non.mean() if not p12_cov_non.empty else 0.0
            )

            for _, row in feat.intervals.iterrows():
                txt.write(
                    "\t%d - %d\t%.2f%%\n" % (row["start"], row["end"], row["coverage"])
                )

            txt.write(f"\n  Palindromes in this feature: {p_all_cov_non.count()}\n")
            txt.write(
                f"  Total palindrome to feature ratio in this feature: {feat.intervals['coverage'].sum():.2f}%\n\n"
            )

        # merged-overlap
        txt.write("\t<palindromes>	<palindrome-to-feature-ratio> (merged-overlap)\n")
        if feat.merged_intervals is not None:

            p_all_cov = feat.merged_intervals["coverage"]
            p8_cov = feat.merged_intervals.loc[feat.merged_intervals["len"] >= 8][
                "coverage"
            ]
            p10_cov = feat.merged_intervals.loc[feat.merged_intervals["len"] >= 10][
                "coverage"
            ]
            p12_cov = feat.merged_intervals.loc[feat.merged_intervals["len"] >= 12][
                "coverage"
            ]

            ws_solo.write(rownum, 9, p_all_cov.mean() if not p_all_cov.empty else 0.0)
            ws_solo.write(rownum, 11, p8_cov.mean() if not p8_cov.empty else 0.0)
            ws_solo.write(rownum, 13, p10_cov.mean() if not p10_cov.empty else 0.0)
            ws_solo.write(rownum, 15, p12_cov.mean() if not p12_cov.empty else 0.0)

            for _, row in feat.merged_intervals.iterrows():
                txt.write(
                    "\t%d - %d\t%.2f%%\n" % (row["start"], row["end"], row["coverage"])
                )

            txt.write(
                f"\n  Palindromes in this feature: {feat.merged_intervals['start'].count()} (merged-overlap)\n"
            )
            txt.write(
                f"  Total palindrome to feature ratio in this feature: {feat.merged_intervals['coverage'].sum():.2f}% (merged-overlap)\n\n"
            )

            if feat.type in merged_feature_data:
                # skip 1st - feature name
                merged_feature_data[feat.type][1] += 1  # cnt
                merged_feature_data[feat.type][2] += feat.end - feat.start  # len
                merged_feature_data[feat.type][
                    3
                ] += p_all_cov_non.count()  # all palindromes
                merged_feature_data[feat.type][
                    4
                ] += p8_cov_non.count()  # p8 palindromes
                merged_feature_data[feat.type][
                    5
                ] += p10_cov_non.count()  # p10 palindromes
                merged_feature_data[feat.type][
                    6
                ] += p12_cov_non.count()  # p12 palindromes
                merged_feature_data[feat.type][7] = (
                    merged_feature_data[feat.type][7] + p_all_cov_non.mean()
                    if not p_all_cov_non.empty
                    else 0.0
                ) / 2
                merged_feature_data[feat.type][8] = (
                    merged_feature_data[feat.type][8] + p_all_cov.mean()
                    if not p_all_cov.empty
                    else 0.0
                ) / 2
                merged_feature_data[feat.type][9] = (
                    merged_feature_data[feat.type][9] + p8_cov_non.mean()
                    if not p8_cov_non.empty
                    else 0.0
                ) / 2
                merged_feature_data[feat.type][10] = (
                    merged_feature_data[feat.type][10] + p8_cov.mean()
                    if not p8_cov.empty
                    else 0.0
                ) / 2
                merged_feature_data[feat.type][11] = (
                    merged_feature_data[feat.type][11] + p10_cov_non.mean()
                    if not p10_cov_non.empty
                    else 0.0
                ) / 2
                merged_feature_data[feat.type][12] = (
                    merged_feature_data[feat.type][12] + p10_cov.mean()
                    if not p10_cov.empty
                    else 0.0
                ) / 2
                merged_feature_data[feat.type][13] = (
                    merged_feature_data[feat.type][13] + p12_cov_non.mean()
                    if not p12_cov_non.empty
                    else 0.0
                ) / 2
                merged_feature_data[feat.type][14] = (
                    merged_feature_data[feat.type][14] + p12_cov.mean()
                    if not p12_cov.empty
                    else 0.0
                ) / 2
            else:
                merged_feature_data[feat.type] = [
                    feat.type,
                    1,
                    (feat.end - feat.start),
                    p_all_cov_non.count(),
                    p8_cov_non.count(),
                    p10_cov_non.count(),
                    p12_cov_non.count(),
                    p_all_cov_non.mean() if not p_all_cov_non.empty else 0.0,
                    p_all_cov.mean() if not p_all_cov.empty else 0.0,
                    p8_cov_non.mean() if not p8_cov_non.empty else 0.0,
                    p8_cov.mean() if not p8_cov.empty else 0.0,
                    p10_cov_non.mean() if not p10_cov_non.empty else 0.0,
                    p10_cov.mean() if not p10_cov.empty else 0.0,
                    p12_cov_non.mean() if not p12_cov_non.empty else 0.0,
                    p12_cov.mean() if not p12_cov.empty else 0.0,
                ]

    xlsx_row_cnt = 1
    for row in merged_feature_data.values():
        for ix, col in enumerate(row):
            ws_merged.write(xlsx_row_cnt, ix, col)
        xlsx_row_cnt += 1

    txt.close()
    workbook.close()


def aggregate_palindromes():
    print("*****\nAggregating all xlsx files into the overall.xlsx file.")
    df = pd.concat(
        (
            pd.read_excel(file, sheet_name=1)
            for file in _DIRS["results"].glob("NC_*.xlsx")
        )
    )

    df_sum = df[
        [
            "Feature",
            "Feature count",
            "Total feature length",
            "Palindromes count all",
            "Palindromes count 8+",
            "Palindromes count 10+",
            "Palindromes count 12+",
        ]
    ]

    df_mean = df[
        [
            "Feature",
            "Average coverage all IRs - merged overlapping IRs",
            "Average coverage all IRs - non-overlapping IRs",
            "Average coverage IR 8+ - merged overlapping IRs",
            "Average coverage IR 8+ - non-overlapping IRs",
            "Average coverage IR 10+ - merged overlapping IRs",
            "Average coverage IR 10+ - non-overlapping IRs",
            "Average coverage IR 12+ - merged overlapping IRs",
            "Average coverage IR 12+ - non-overlapping IRs",
        ]
    ]

    df_sum = df_sum.groupby(by="Feature", as_index=False).sum()
    df_mean = df_mean.groupby(by="Feature", as_index=False).mean()
    df_mean = df_mean.drop(["Feature"], axis=1)

    workbook = xlsxwriter.Workbook(
        _DIRS["results"] / f"overall.xlsx", {"nan_inf_to_errors": True}
    )
    ws = workbook.add_worksheet("Overall feature statistics")

    headers = {
        "A1": "Feature",
        "B1": "Feature count",
        "C1": "Total feature length",
        "D1": "Palindromes count all",
        "E1": "Palindromes count 8+",
        "F1": "Palindromes count 10+",
        "G1": "Palindromes count 12+",
        "H1": "Average coverage all IRs - merged overlapping IRs",
        "I1": "Average coverage all IRs - non-overlapping IRs",
        "J1": "Average coverage IR 8+ - merged overlapping IRs",
        "K1": "Average coverage IR 8+ - non-overlapping IRs",
        "L1": "Average coverage IR 10+ - merged overlapping IRs",
        "M1": "Average coverage IR 10+ - non-overlapping IRs",
        "N1": "Average coverage IR 12+ - merged overlapping IRs",
        "O1": "Average coverage IR 12+ - non-overlapping IRs",
    }
    bold = workbook.add_format({"bold": True})

    ws.set_column(0, 6, 23)
    ws.set_column(6, 15, 50)

    for index, name in headers.items():
        ws.write(index, name, bold)

    # insert aggregated values
    print("----------------------------")
    for ir, row in enumerate(df_sum.values, start=1):
        for ic, col in enumerate(row):
            ws.write(ir, ic, col)  # sum stats

    for ir, row in enumerate(df_mean.values, start=1):
        for ic, col in enumerate(row):
            ws.write(ir, ic + df_sum.shape[1], col)  # mean stats

    workbook.close()


def stats(features, ncbi, analysis: str):

    txt = open(_DIRS["results"] / f"{ncbi}.txt", "w")

    workbook = xlsxwriter.Workbook(
        _DIRS["results"] / f"{ncbi}.xlsx", {"nan_inf_to_errors": True}
    )
    ws_solo = workbook.add_worksheet(f"Feature to {analysis}s")
    ws_merged = workbook.add_worksheet("Merged features")
    bold = workbook.add_format({"bold": True})

    ws_solo.set_column(0, 0, 10)
    ws_solo.set_column(1, 1, 40)
    ws_solo.set_column(2, 4, 15)
    ws_solo.set_column(4, 8, 23)
    ws_solo.set_column(8, 16, 50)

    ws_merged.set_column(0, 6, 23)
    ws_merged.set_column(6, 15, 50)

    # add headers for xlsx file
    headers_solo = {
        "A1": "Feature",
        "B1": "Info",
        "C1": "Feature start",
        "D1": "Feature end",
        "E1": "Feature size",
        "F1": f"{analysis.capitalize()}s count",
        "G1": f"Average coverage all {analysis.capitalize()}s - overlapping",
        "H1": f"Average coverage all {analysis.capitalize()}s - non-overlapping",
        "I1": f"Overall coverage of {analysis.capitalize()}s - overlapping",
        "J1": f"Overall coverage of {analysis.capitalize()}s - non-overlapping",
    }
    headers_merged = {
        "A1": "Feature",
        "B1": "Feature count",
        "C1": "Total feature length",
        "D1": f"{analysis.capitalize()}s count",
        "E1": f"Average coverage all {analysis.capitalize()}s - overlapping",
        "F1": f"Average coverage all {analysis.capitalize()}s - non-overlapping",
    }
    for index, name in headers_solo.items():
        ws_solo.write(index, name, bold)

    for index, name in headers_merged.items():
        ws_merged.write(index, name, bold)

    merged_feature_data = {}

    # General statisctics
    txt.write(f"ANNOTATION STATISTICS: {ncbi}\n")
    txt.write(f"==================\n\n")

    for rownum, feat in enumerate(features, start=1):
        txt.write(f"Feature: {feat.start} - {feat.end} ({feat.type})\n")

        # xlsx feature info
        ws_solo.write(rownum, 0, feat.type)
        ws_solo.write(rownum, 1, feat.info)
        ws_solo.write(rownum, 2, feat.start)
        ws_solo.write(rownum, 3, feat.end)
        ws_solo.write(rownum, 4, feat.end - feat.start)

        # non-overlapping
        txt.write(f"\t<{analysis}s>	<{analysis}-to-feature-ratio>\n")
        if feat.intervals is not None:

            # xlsx palindrome info

            p_all_cov_non = feat.intervals["coverage"]

            ws_solo.write(rownum, 5, p_all_cov_non.count())
            ws_solo.write(rownum, 7, p_all_cov_non.mean())

            for _, row in feat.intervals.iterrows():
                txt.write(
                    "\t%d - %d\t%.2f%%\n" % (row["start"], row["end"], row["coverage"])
                )

            txt.write(
                f"\n  {analysis.capitalize()}s in this feature: {p_all_cov_non.count()}\n"
            )

            # coverage of all R-loops in given feature (number of common R-loop nucleotides / annotation length)
            analysis_to_feature_coverage = (
                (feat.intervals["cov_end"].max() - feat.intervals["cov_start"].min())
                * 100
                / feat.len
            )
            txt.write(
                f"  Total {analysis} to feature ratio in this feature: {analysis_to_feature_coverage:.2f}%\n\n"
            )
            ws_solo.write(rownum, 9, analysis_to_feature_coverage)
        else:  # null values
            ws_solo.write(rownum, 5, 0)
            ws_solo.write(rownum, 7, 0.0)
            ws_solo.write(rownum, 9, 0.0)

        # merged-overlap
        txt.write(f"\t<{analysis}s>	<{analysis}-to-feature-ratio> (merged-overlap)\n")
        if feat.merged_intervals is not None:

            p_all_cov = feat.merged_intervals["coverage"]

            ws_solo.write(rownum, 6, p_all_cov.mean())

            for _, row in feat.merged_intervals.iterrows():
                txt.write(
                    "\t%d - %d\t%.2f%%\n" % (row["start"], row["end"], row["coverage"])
                )

            txt.write(
                f"\n  {analysis.capitalize()}s in this feature: {feat.merged_intervals['start'].count()} (merged-overlap)\n"
            )

            # coverage of all R-loops in given feature (number of common R-loop nucleotides / annotation length)
            analysis_to_feature_coverage_merged = (
                (
                    feat.merged_intervals["cov_end"].max()
                    - feat.merged_intervals["cov_start"].min()
                )
                * 100
                / feat.len
            )
            txt.write(
                f"  Total {analysis} to feature ratio in this feature: {analysis_to_feature_coverage_merged:.2f}% (merged-overlap)\n\n"
            )
            ws_solo.write(rownum, 8, analysis_to_feature_coverage_merged)

            if feat.type in merged_feature_data:
                # skip 1st - feature name
                merged_feature_data[feat.type][1] += 1  # cnt
                merged_feature_data[feat.type][2] += feat.end - feat.start  # len
                merged_feature_data[feat.type][
                    3
                ] += p_all_cov_non.count()  # all palindromes

                merged_feature_data[feat.type][4] = (
                    merged_feature_data[feat.type][4] + p_all_cov_non.mean()
                    if not p_all_cov_non.empty
                    else 0.0
                ) / 2
                merged_feature_data[feat.type][5] = (
                    merged_feature_data[feat.type][5] + p_all_cov.mean()
                    if not p_all_cov.empty
                    else 0.0
                ) / 2
            else:
                merged_feature_data[feat.type] = [
                    feat.type,
                    1,
                    (feat.end - feat.start),
                    p_all_cov_non.count(),
                    p_all_cov_non.mean() if not p_all_cov_non.empty else 0.0,
                    p_all_cov.mean() if not p_all_cov.empty else 0.0,
                ]
        else:  # null values
            ws_solo.write(rownum, 6, 0.0)
            ws_solo.write(rownum, 8, 0.0)

    xlsx_row_cnt = 1
    for row in merged_feature_data.values():
        for ix, col in enumerate(row):
            ws_merged.write(xlsx_row_cnt, ix, col)
        xlsx_row_cnt += 1

    txt.close()
    workbook.close()
