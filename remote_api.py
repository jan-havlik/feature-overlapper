import json
import time

import requests
from tenacity import retry, stop_after_attempt

from lambdas import ncbi_to_feature, ncbi_to_sequence
from utils import _DIRS


class Remote:
    """
    class for API connections and file downloads
    """

    def __init__(self, ncbi: str):
        self.ncbi = ncbi
        self.ncbi_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.analyser_base_url = "https://bioinformatics.ibp.cz/"

    def get_sequence(self):
        r = requests.get(
            f"{self.ncbi_base_url}efetch.fcgi?db=nuccore&id={self.ncbi}&rettype=fasta&retmode=text"
        )

        with open(ncbi_to_sequence(self.ncbi), "w") as out:
            out.write(r.text)

    @retry(stop=stop_after_attempt(3))
    def get_annotation_file(self):

        if not ncbi_to_sequence(self.ncbi).is_file():
            self.get_sequence()

        r = requests.get(
            f"{self.ncbi_base_url}efetch.fcgi?db=nuccore&id={self.ncbi}&rettype=ft&retmode=text"
        )
        with open(ncbi_to_feature(self.ncbi), "w") as out:
            out.write(r.text)
        return True

    @retry(stop=stop_after_attempt(3))
    def get_analysis(self, type: str):

        if not ncbi_to_sequence(self.ncbi).is_file():
            self.get_sequence()

        host_token = requests.post(f"{self.analyser_base_url}api/jwt").text
        headers = {"Authorization": host_token, "Content-Type": "application/json"}

        data = json.dumps(
            {
                "circular": True,
                "ncbis": [
                    {
                        "circular": True,
                        "name": self.ncbi,
                        "ncbiId": self.ncbi,
                        "tags": ["overlapper"],
                        "type": "DNA",
                    }
                ],
                "tags": ["overlapper"],
                "type": "DNA",
            }
        )

        # upload sequence
        r_seq = requests.post(
            f"{self.analyser_base_url}/api/sequence/import/ncbi",
            data=data,
            headers=headers,
        )
        seq_id = str(r_seq.json()["items"][0]["id"])

        analyse_map = {
            "rloop": {
                "url": "api/analyse/rloopr",
                "data": json.dumps(
                    {"rizModel": [0], "sequence": seq_id, "tags": ["overlapper"]}
                ),
            },
            "g4": {
                "url": "api/analyse/g4hunter",
                "data": json.dumps(
                    {
                        "sequence": seq_id,
                        "tags": ["overlapper"],
                        "threshold": 1.1,
                        "windowSize": 25,
                    }
                ),
            },
            "palindrome": {
                "url": "api/analyse/palindrome",
                "data": json.dumps(
                    {
                        "dinucleotide": True,
                        "mismatches": "0,1",
                        "sequences": [seq_id],
                        "size": "6-30",
                        "spacer": "0-10",
                        "stabilityModel": "NN_MODEL_STABILITY",
                        "tags": ["overlapper"],
                    }
                ),
            },
        }

        if type != "rloop":
            print(
                f"Sorry, the DNA Analyser website supports only automated R-loop processing.\n For the {type} analysis, you have to process and download the files yourself at: {self.analyser_base_url}"
            )
            exit(0)

        ra = requests.post(
            f'{self.analyser_base_url}/{analyse_map[type]["url"]}',
            data=analyse_map[type]["data"],
            headers=headers,
        )
        batch_id = str(ra.json()["payload"]["id"])

        tick = 0
        while True:
            result = requests.get(
                f'{self.analyser_base_url}/{analyse_map[type]["url"]}/{batch_id}/analysis',
                headers=headers,
            )
            if result.json()["batch"]["status"] == "FINISH":
                file_request = requests.get(
                    f'{self.analyser_base_url}/{analyse_map[type]["url"]}/{batch_id}/rloopr.csv',
                    headers=headers,
                )
                with open(_DIRS["rloop"] / f"{self.ncbi}_rloop.csv", "w") as out:
                    out.write(file_request.text)
                    return True
            elif tick == 300:
                # 5 minutes passed, let's go
                print(
                    "Waiting for analysis to complete was over 5 minutes, please try again later"
                )
            else:
                tick += 1
                print("Waiting for an analysis to finish...")
                time.sleep(1)
