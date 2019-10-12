import os
import sys
import json

import requests


def main():
    if len(sys.argv) < 1:
        print("usage: python check_links.py /path/to/dir")

    print("checking links...")

    cwd = os.getcwd()
    path = sys.argv[1]
    dir = os.path.join(cwd, path)

    files = []
    for _, _, fs in os.walk(dir):
        for f in fs:
            files.append(os.path.join(dir, f))

    down = []

    for file in files:
        print(file)
        with open(file, "r") as f:
            j = json.load(f)

            links = []
            if j.get("sitelink"):
                links.append(j["sitelink"])
            if j.get("directlink"):
                links.append(j["directlink"])
            if j.get("summarylink"):
                links.append(j["summarylink"])

            for link in links:
                try:
                    r = requests.head(link)

                    code = r.status_code

                    if code == 404:
                        down.append(link)

                    print(f"{code}: {link}")
                except requests.ConnectionError:
                    print("failed to connect")
                    down.append(link)

        if down:
            print("\nDOWN LINKS:")
            for d in down:
                print(d)


if __name__ == "__main__":
    main()
