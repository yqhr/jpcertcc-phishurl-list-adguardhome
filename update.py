import io
import os
import re
import csv
import json
import zipfile
import requests
from pprint import pprint


script_basename = os.path.basename(__file__)
script_dirname = os.path.dirname(__file__)
output_dirname = script_dirname
blacklist_name = "config-block.json"
local_adblock_name = "temp_adblock.txt"
output_block_json = os.path.join(output_dirname, blacklist_name)
output_local_adblock_txt = os.path.join(output_dirname, local_adblock_name)


def get_csv_files() -> list:
    url = "https://github.com/JPCERTCC/phishurl-list/archive/refs/heads/main.zip"
    r = requests.get(url)
    content = r.content
    with zipfile.ZipFile(io.BytesIO(content)) as f:
        csv_paths = [l for l in f.namelist() if ".csv" in l]
        csv_files = [f.read(csv) for csv in csv_paths]
    return csv_files

def read_csv_files_as_dict(file_content: bytes) -> list:
    with io.StringIO(file_content.decode("utf-8")) as f:
        reader = csv.DictReader(f)
        return [r for r in reader]

def generate_url_list() -> set:
    L = list()
    csv_files = get_csv_files()
    for c in csv_files:
        L += read_csv_files_as_dict(c)
    return {d["URL"] for d in L}

def generate_adblock_list() -> list:
    result = list()
    pat = re.compile(r"^[:h]?ttp[|s]?[\[:\]|:|\/]+(.*)$")
    for line in generate_url_list():
        m = re.match(pat, line)
        if m:
            obj = m.groups()[0]
            if obj[-1] == "/":
                obj = obj[:-1]
            result += ["||{0}^".format(obj)]
    return result

def write_to_json():
    L = sorted(generate_adblock_list())
    with open(output_local_adblock_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    sources = [{"source": output_local_adblock_txt, "type": "adblock", "transformations": ["Validate"]}]
    json_data = {
        "name": "JPCERTCC-phishurl-list",
        "description": "ref: https://github.com/JPCERTCC/phishurl-list/",
        "sources": sources,
        "transformations": ["RemoveComments", "Deduplicate"],
        "exclusions": []
    }
    with open(output_block_json, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=3)

def main():
    write_to_json()


if __name__ == "__main__":
    main()
