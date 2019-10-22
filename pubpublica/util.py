import os
import json
import datetime
import logging

log = logging.getLogger(__name__)


def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except Exception as err:
        log.warning(f"failed to load JSON from {file}")
        return {}


def get_publication_files(path):
    cwd = os.getcwd()
    pubdir = os.path.join(cwd, path)

    files = []
    for _, _, fs in os.walk(pubdir):
        log.debug("publication files:")
        for f in fs:
            log.debug(f)
            files.append(os.path.join(pubdir, f))

    return files


def validate_pub_file(file):
    if not os.path.exists(file):
        log.error("invalid pub file: does not exist")
        return False

    if not os.path.isfile(file):
        log.error("invalid pub file: is not a file")
        return False

    if not file.endswith(".json"):
        log.error("invalid pub file: is not a json file")
        return False

    with open(file, "r") as f:
        j = json.load(f)

    if not (
        j.get("title") and j.get("date") and j.get("authors") and j.get("description")
    ):
        log.error("invalid pub file: invalid structure")
        return False

    return True


def load_pub(file):
    if not validate_pub_file(file):
        return None

    with open(file, "r") as f:
        return json.load(f)


def get_publications(path):
    files = get_publication_files(path)

    pubs = [load_pub(f) for f in files]
    pubs = [p for p in pubs if p]

    return pubs


def rss_convert(publications):
    return publications
