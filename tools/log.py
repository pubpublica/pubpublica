from termcolor import colored


def success(s):
    print(colored(s, "green"))


def warning(s):
    print(colored(s, "yellow"))


def error(s):
    print(colored(s, "red"))
