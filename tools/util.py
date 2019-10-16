import sys

import getpass
from termcolor import colored
from fabric import Config, Connection

from jinja2 import Template

import log


def timestamp():
    return datetime.datetime.utcnow().isoformat()


def template(file, config={}):
    contents = ""
    with open(file, "r") as f:
        contents = f.read()

    template = Template(contents)
    return template.render(config)


def connect(host, sudo=False):
    config = Config()

    settings = {"hide": True, "warn": True}
    config["sudo"].update(settings)
    config["run"].update(settings)

    if sudo:
        sudo_pass = getpass.getpass("sudo password: ")
        config["sudo"].update({"password": sudo_pass})

    c = Connection(host, config=config)

    return c


def print_json(j):
    print(json.dumps(j, indent=4))


class Guard:
    def __init__(self, str):
        self.str = str

    def __enter__(self):
        sys.stdout.write(self.str)
        sys.stdout.flush()

    def __exit__(self, type, value, traceback):
        if not (type and value and traceback):
            log.success("DONE")
        else:
            log.error("FAILED")
        sys.stdout.flush()
