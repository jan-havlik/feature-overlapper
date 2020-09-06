import datetime
import logging
import os
import time
from io import StringIO

from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, abort, Response
from werkzeug.utils import secure_filename
  
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
  
from app.file_validator import validate_files, get_ncbi
from feature_overlapper.annotation_loader import AnnotationLoader
from feature_overlapper.palindrome_loader import PalindromeLoader
from feature_overlapper.aggregator import Aggregator
from feature_overlapper.main import compare_results, zip_results
from feature_overlapper.util import _COMPARISON_DIR

@app.route("/") 
def welcome_page(): 
    return render_template('index.html', year=datetime.datetime.now().year)

@app.route("/scripts/feature-overlapper", methods=['GET', 'POST'])
def feature_overlapper():

    if request.method == 'POST':

        palindrome_files = request.files.getlist('palindromeFiles')
        feature_files = request.files.getlist('featureFiles')
        pal_err_msg = ""
        feat_err_msg = ""

        # for a check if there is some missing
        feat_ncbis = dict()
        pal_ncbis = dict()

        ploader = PalindromeLoader()


        # load both files to tmp folder
        for feat_file in feature_files:
            if not validate_files(feat_file.filename, "txt"):
                feat_err_msg += f"Invalid file format for feature file {feat_file.filename}\n correct format is for example NC_1234_ft.txt\n"
            else:
                filename = secure_filename(feat_file.filename)
                feat_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                feat_ncbis[get_ncbi(filename)] = feat_file

        for pal_file in palindrome_files:
            if not validate_files(pal_file.filename, "csv"):
                pal_err_msg += f"Invalid file format for palindrome file {pal_file.filename}\n correct format is for example NC_1234_palindromes.csv\n"
            else:
                filename = secure_filename(pal_file.filename)
                pal_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                pal_ncbis[get_ncbi(filename)] = pal_file

        # add only matching files (with same NCBI id for palindromes and features)
        common_features = [feat_file for feat_ncbi, feat_file in feat_ncbis.items() for pal_ncbi in pal_ncbis.keys() if feat_ncbi == pal_ncbi]
        # TODO: add notice about invalid (non-matching) files

        if len(pal_err_msg) > 1 or len(feat_err_msg) > 1:
            app.logger.error(pal_err_msg)
            app.logger.error(feat_err_msg)
            return render_template('feature_overlapper.html', pal_err_msg=pal_err_msg, feat_err_msg=feat_err_msg)
        elif common_features == []:
            return render_template('feature_overlapper.html', pal_err_msg="No matching NCBI ID!")

        # no errors, run again
        for merge in common_features:
            fn = merge.filename.split("/")[-1]
            _NCBI_ID = "NC_" + fn.split("_")[1]

            af = AnnotationLoader()
            af.load(app.config['UPLOAD_FOLDER'] + f"/{_NCBI_ID}_ft.txt")

            pf = PalindromeLoader()
            pf.load(app.config['UPLOAD_FOLDER'] + f"/{_NCBI_ID}_palindromes.csv")

            compare_results(af.return_annotations(), pf.return_palindromes(), _NCBI_ID)

        # aggregate CSVs
        aggregator = Aggregator()
        aggregator.load_csv(_COMPARISON_DIR)

        # store to zip
        zip_results(unlink=True)

        return send_from_directory(app.config["UPLOAD_FOLDER"], filename="results.zip", as_attachment=True)

    return render_template('feature_overlapper.html')
