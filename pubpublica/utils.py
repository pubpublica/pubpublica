import os
import json
import datetime


def get_publication_files(path):
    cwd = os.getcwd()
    pubdir = os.path.join(cwd, path)

    files = []
    for _, _, fs in os.walk(pubdir):
        for f in fs:
            files.append(os.path.join(pubdir, f))

    return files


def validate_pub_file(file):
    if not os.path.exists(file):
        print("invalid pub file: does not exist")
        return False

    if not os.path.isfile(file):
        print("invalid pub file: is not a file")
        return False

    if not file.endswith(".json"):
        print("invalid pub file: is not a json file")
        return False

    j = {}
    with open(file, "r") as f:
        j = json.load(f)

    if not (
        j.get("title") and j.get("date") and j.get("authors") and j.get("description")
    ):
        print("invalid pub file: invalid structure")
        return False

    return True


def load_pub(file):
    if not validate_pub_file(file):
        return None

    pub = {}
    with open(file, "r") as f:
        return json.load(f)


def get_publications(path):
    files = get_publication_files(path)
    pubs = [load_pub(f) for f in files]
    pubs = [p for p in pubs if p]
    return pubs


def rss_convert(publications):
    return publications
