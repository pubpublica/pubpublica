import sys

import getpass
from termcolor import colored
from fabric import Config, Connection


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


class Guard:
    def __init__(self, str):
        self.str = str

    def __enter__(self):
        sys.stdout.write(self.str)

    def __exit__(self, type, value, traceback):
        if not (type and value and traceback):
            print(colored("DONE", "green"))
        else:
            print(colored("FAILED", "red"))
