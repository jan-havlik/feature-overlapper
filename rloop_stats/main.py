import requests
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from waiting import wait, TimeoutExpired
# python3 -m pip install waiting
# it is an exponential waiting library used for passive waiting until the given predicate is True

ncbi_id = "NG_047107.1"
name = "NRXN2"
host = "https://bioinformatika.pef.mendelu.cz"
headers = {'Content-Type': 'application/json'}

# used as lambda expression for exponential waiting predicate
def wait_for_analysis(analysis_id, headers):
  analysis = requests.get("https://bioinformatika.pef.mendelu.cz/api/analyse/rloopr/"+ analysis_id +"/analysis", headers=headers, verify=False)
  print(analysis.json())
  return analysis.json()["batch"]["status"] == "FINISH"

# used as lambda expression for exponential waiting predicate
def wait_for_sequence(seq_id, headers):
  print(f"Waiting for sequence {seq_id}")
  analysis = requests.get(f"https://bioinformatika.pef.mendelu.cz/api/sequence/{seq_id}", headers=headers, verify=False)
  
  if analysis.json().get("batch").get("status", "") == "FAILED":
    raise RuntimeError

  return analysis.json().get("batch").get("status", "") == "FINISH"

def login_to_analyser(username, password):

    # Get jwt token (api token) with login
    resp = requests.put('https://bioinformatika.pef.mendelu.cz/api/jwt',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'login': username,
            'password': password
        })
    , verify=False) # dev has invalid cert

    return resp

def import_sequence(seq_name, ncbi_id, jwt_token):

  # add authorization key to headers
  headers["Authorization"] = jwt_token

  # Import Human chromozome Y (NC_000024)
  sequence = {
    "circular": True,
    "ncbis": [
      {
        "circular": True,
        "name": seq_name,
        "ncbiId": ncbi_id,
        "tags": [
          "rloop",
          "api"
        ],
        "type": "DNA"
      }
    ],
    "tags": [
      "rloop",
      "api"
    ],
    "type": "DNA"
  }

  request = requests.post(
      'https://bioinformatika.pef.mendelu.cz/api/sequence/import/ncbi',
      data=json.dumps(sequence),
      headers=headers,
      verify=False
  )

  if request.status_code != 201:
      return None

  json_request = request.json()
  sequence_id = json_request["items"][0]["id"]

  return sequence_id

  try:
    predicate = lambda : json_request["batches"] == {}
    wait(predicate, sleep_seconds=(1, 100))
  except TimeoutExpired:
    print("Timeout for sequence upload exceeded.")
    exit(1)

def start_rloop_analysis(seq_id, headers):
  # proceed with R-loop-R analysis, setup the parameters
  rloopr = {
      "rizModel": [0],
      "sequence": seq_id,
      "tags": [
          "rloop", 
          "api"
      ]
  }

  # Initialize the analysis
  request = requests.post(
      'https://bioinformatika.pef.mendelu.cz/api/analyse/rloopr',
      data=json.dumps(rloopr),
      headers=headers,
      verify=False
  )
  analysis_id = request.json()["payload"]["id"]

  try: # waiting for the analysis batch to finish
    predicate = lambda : wait_for_analysis(analysis_id, headers)
    wait(predicate, sleep_seconds=(1, 100))
  except TimeoutExpired:
    print("Timeout for sequence upload exceeded.")
    exit(1)


  finished = requests.get("https://bioinformatika.pef.mendelu.cz/api/analyse/rloopr/"+ analysis_id +"/analysis", headers=headers, verify=False)

  data = requests.get("https://bioinformatika.pef.mendelu.cz/api/analyse/rloopr/"+ analysis_id +"/rloopr.csv", headers=headers, verify=False)

  rows = data.text.split("\n")
  parsed = []
  for row in rows:
    stripped_row = row.replace('"', "")
    parsed.append(stripped_row.split("\t"))

  parsed = parsed[1:-1]

  df = pd.DataFrame(parsed, columns =['id', 'Start', 'End', 'Riz', 'RizG', 'Linker', 'Rez', 'Model', 'Strand', 'RloopG', '3G', '4G', '5G'])

  # type casting
  df["RizG"] = df["RizG"].astype(float)
  df["RloopG"] = df["RloopG"].astype(float)
  df["3G"] = df["3G"].astype(float)
  df["4G"] = df["4G"].astype(float)
  df["5G"] = df["5G"].astype(float)

  df["Start"] = df["Start"].astype(int)
  df["End"] = df["Start"] + df["End"].astype(int) # it is actuallt length


  statistics = {
    "analysis_name": "",
    "analysis_start": 0,
    "analysis_end": 0,
    "analysis_total": 0,
    "RizG": {
      "avg": 0.0,
      "max": 0.0,
      "min": 0.0
    },
    "RloopG": {
      "avg": 0.0,
      "max": 0.0,
      "min": 0.0
    },
    "3G": {
      "avg": 0,
      "max": 0,
      "min": 0,
      "sum": 0
    },
    "4G": {
      "avg": 0,
      "max": 0,
      "min": 0,
      "sum": 0
    },
    "5G": {
      "avg": 0,
      "max": 0,
      "min": 0,
      "sum": 0
    }
  }

  statistics["analysis_name"] = df.iloc[0]["id"]
  statistics["analysis_start"] = df.iloc[0]["Start"]

  statistics["analysis_end"] = df.iloc[-1]["End"] # extra newline at the end
  statistics["analysis_total"] = len(df)
  statistics["RizG"]["avg"] = "{:.2}".format(df["RizG"].mean())
  statistics["RizG"]["max"] = "{:.2}".format(df["RizG"].max())
  statistics["RizG"]["min"] = "{:.2}".format(df["RizG"].min())

  statistics["RloopG"]["avg"] = "{:.2}".format(df["RloopG"].mean())
  statistics["RloopG"]["max"] = "{:.2}".format(df["RloopG"].max())
  statistics["RloopG"]["min"] = "{:.2}".format(df["RloopG"].min())

  statistics["3G"]["avg"] = int(df["3G"].mean())
  statistics["3G"]["max"] = int(df["3G"].max())
  statistics["3G"]["min"] = int(df["3G"].min())
  statistics["3G"]["sum"] = int(df["3G"].sum())

  statistics["4G"]["avg"] = int(df["4G"].mean())
  statistics["4G"]["max"] = int(df["4G"].max())
  statistics["4G"]["min"] = int(df["4G"].min())
  statistics["4G"]["sum"] = int(df["4G"].sum())

  statistics["5G"]["avg"] = int(df["5G"].mean())
  statistics["5G"]["max"] = int(df["5G"].max())
  statistics["5G"]["min"] = int(df["5G"].min())
  statistics["5G"]["sum"] = int(df["5G"].sum())

  # get sequence info
  seq = requests.get("https://bioinformatika.pef.mendelu.cz/api/analyse/rloopr/"+ analysis_id + "/analysis", headers=headers, verify=False)
  sequence_id = seq.json()["payload"]["sequenceId"]
  seq_title = seq.json()["payload"]["title"]

  seq_data = seq = requests.get("https://bioinformatika.pef.mendelu.cz/api/sequence/"+ sequence_id, headers=headers, verify=False)
  seq_len = seq_data.json()["payload"]["length"]
  one_percent = seq_len / 100

  heatmap = []


  for i in range(0,100):
    relative_start = int(i * one_percent)
    relative_end = int(relative_start + 1 + one_percent)
    heatmap.append(len(df.loc[(df['Start'] >= relative_start) & (df['End'] <= relative_end)]))

  hist_df = pd.DataFrame(np.array(heatmap), columns=["R-loop count"])
  plt.rcParams["figure.figsize"] = 5,2

  x = np.array([i for i in range(0,100)])
  y = np.array(heatmap)

  fig, (ax,ax2) = plt.subplots(nrows=2, sharex=True)

  extent = [x[0]-(x[1]-x[0])/2., x[-1]+(x[1]-x[0])/2.,0,1]
  ax.imshow(y[np.newaxis,:], cmap="plasma", aspect="auto", extent=extent)
  ax.set_yticks([])
  ax.set_xlim(extent[0], extent[1])

  ax2.plot(x,y)
  plt.xlabel("Délka sekvence [%]")
  plt.ylabel("Počet R-loop [N]")
  plt.title(seq_title)

  plt.tight_layout()
  plt.savefig(f'/tmp/{seq_title}.png')

  return (statistics, f'{seq_title}.png')
