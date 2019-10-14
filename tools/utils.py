import sys
from termcolor import colored


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
