import os
import sys

import requests

import log
import util


def check_link(url):
    try:
        r = requests.head(url, allow_redirects=True)
        return r.status_code
    except requests.ConnectionError:
        return None


def check(path):
    cwd = os.getcwd()
    dir = os.path.join(cwd, path)

    files = []
    for _, _, fs in os.walk(dir):
        for f in fs:
            files.append(os.path.join(dir, f))

    items = {}
    for file in files:
        item = util.template(file)

        links = []
        for l in ["sitelink", "directlink", "summarylink"]:
            if item.get(l):
                links.append(item.get(l))

        items.update({file: links})

    exit_code = 0
    for file, links in items.items():
        print()
        print(file)
        for link in links:
            code = check_link(link)

            if not code:
                log.error(f"XXX: {link}")
                exit_code += 1
            elif code == 404:
                log.error(f"{code}: {link}")
                exit_code += 1
            else:
                print(f"{code}: {link}")

    sys.exit(exit_code)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python check_links.py /path/to/dir")
        sys.exit(1)

    path = sys.argv[1]
    check(path)
