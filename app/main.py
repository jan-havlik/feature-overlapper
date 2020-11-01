import datetime
import logging
import os
import time
from io import StringIO
from zipfile import ZipFile
from waiting import wait, TimeoutExpired
import requests

from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, abort, Response
from werkzeug.utils import secure_filename
from rq import Queue, get_current_job
from rq.job import Job
from rq.registry import StartedJobRegistry

  
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['EXAMPLES_FOLDER'] = './examples'

from app.worker import conn
from app.file_validator import validate_files, get_ncbi
from feature_overlapper.annotation_loader import AnnotationLoader
from feature_overlapper.palindrome_loader import PalindromeLoader
from feature_overlapper.aggregator import Aggregator
from feature_overlapper.main import compare_results, zip_results, aggregate_and_zip
from feature_overlapper.util import _COMPARISON_DIR

from rloop_stats.main import login_to_analyser, import_sequence, wait_for_sequence, start_rloop_analysis

@app.route("/") 
def welcome_page(): 
    return render_template('index.html', year=datetime.datetime.now().year)

@app.route("/example/feature-overlapper")
def feature_overlapper_example_files():

    return send_from_directory(app.config["EXAMPLES_FOLDER"], filename="feature_overlapper.zip", as_attachment=True)

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

        # redis queue
        q = Queue(connection=conn)


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

            q.enqueue(compare_results, af.return_annotations(), pf.return_palindromes(), _NCBI_ID)
        
        return render_template('feature_overlapper.html')

    return render_template('feature_overlapper.html')


@app.route("/jobs-done", methods=['GET'])
def get_current_job():
    registry = StartedJobRegistry('default', connection=conn)
    running_job_ids = registry.get_job_ids()
    jobs = Job.fetch_many(running_job_ids, connection=conn)

    for job in jobs:
        print('Job %s: %s - %s' % (job.id, job.func_name, job.is_finished))


    if(not job.is_finished):
        return "Not yet ready", 202
    else:
        aggregate_and_zip()
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename="results.zip", as_attachment=True)


@app.route("/scripts/rloop-stats", methods=['GET', 'POST'])
def rloop_stats():

    if request.method == 'POST':

        login = request.form["rloopStatsEmail"]
        pwd = request.form["rloopStatsPassword"]
        ref_seq = request.form["rloopStatsRefSeq"]

        login_response = login_to_analyser(login, pwd)
        app.logger.info(login_response)
        
        if login_response.status_code != 201:
            return render_template('rloop_stats.html', err_msg="DNA Analyser authentization failed.")

        jwt_token = login_response.text

        # store sequence on DNA analyser web
        seq_id = import_sequence(f"Bioscripts_{ref_seq}", ref_seq, jwt_token)

        if not seq_id:
            return render_template('rloop_stats.html', err_msg="Sequence was not imported (bad RefSeq?).")

        app.logger.info(seq_id)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': jwt_token
        }

        seq_created_predicate = lambda : wait_for_sequence(seq_id, headers)
        try:
            wait(seq_created_predicate, sleep_seconds=(1, 100))
        except RuntimeError:
            return render_template('rloop_stats.html', err_msg=f"Sequence with RefSeq {ref_seq} import FAILED.")
        except TimeoutExpired:
            return render_template('rloop_stats.html', err_msg="Timeout while waiting for sequence import (100 s)")
        except AttributeError:
            pass # already exists

        app.logger.info(f"Sequence {seq_id} imported succesfully.")

        stats, img = start_rloop_analysis(seq_id, headers)
      
        return render_template('rloop_stats.html', stats=stats, filename=img)


    return render_template('rloop_stats.html')

@app.route("/files/graph/<filename>")
def graph_download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename=filename, as_attachment=True)
