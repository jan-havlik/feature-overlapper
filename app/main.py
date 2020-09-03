import datetime
import logging
import os

from io import StringIO

from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
  
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
  
from app.file_validator import validate_files
from feature_overlapper.annotation_loader import AnnotationLoader

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

        aloader = AnnotationLoader()


        for pal_file in palindrome_files:
            if not validate_files(pal_file.filename, "csv"):
                pal_err_msg += f"Invalid file format for palindrome file {pal_file.filename}\n correct format is for example NC_1234_palindromes.csv\n"


        for feat_file in feature_files:
            if not validate_files(feat_file.filename, "txt"):
                feat_err_msg += f"Invalid file format for feature file {feat_file.filename}\n correct format is for example NC_1234_ft.txt\n"
            else:
                filename = secure_filename(feat_file.filename)
                feat_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                app.logger.info(feat_file)
                app.logger.info(send_from_directory(app.config['UPLOAD_FOLDER'], filename))
                #app.logger.info(send_from_directory(app.config['UPLOAD_FOLDER'], filename).response.file)

                #aloader.load(StringIO(send_from_directory(app.config['UPLOAD_FOLDER'], filename).response.file.name))


        if len(pal_err_msg) > 1 or len(feat_err_msg) > 1:
            app.logger.error(pal_err_msg)
            app.logger.error(feat_err_msg)
            return render_template('script.html', pal_err_msg=pal_err_msg, feat_err_msg=feat_err_msg)

        #app.logger.info(aloader.return_annotations())
            


    return render_template('script.html')

