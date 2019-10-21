import os
import sys
import json
import getpass

import click
from paramiko.config import SSHConfig
from fabric import Config, Connection
from fabrikant import fs, system, access
from fabrikant.apps import git, systemd, ufw

from termcolor import colored

import log
import util
from util import Guard
from config import config


def green(s):
    return colored(s, "green", attrs=["bold"])


def yellow(s):
    return colored(s, "yellow", attrs=["bold"])


def red(s):
    return colored(s, "red", attrs=["bold"])


def build_context(c):
    ctx = {}
    ctx.update(config.get("DEPLOY"))
    ctx.pop("INCLUDES", None)
    ctx.pop("SOCKET_PATH", None)

    return ctx


def gather_info(c, ctx):
    app_path = ctx.get("APP_PATH")
    deployed_id_file = ctx.get("DEPLOYED_ID_FILE")

    remote_id_file = os.path.join(app_path, deployed_id_file)
    deployed_id = fs.read_file(c, remote_id_file)

    print(f"deployed id: {yellow(deployed_id)}")
    ctx.update({"DEPLOYED_ID": deployed_id})

    deployed_path = os.path.join(app_path, deployed_id)
    ctx.update({"DEPLOYED_PATH": deployed_path})


def color_by_predicate(pred, true, false):
    if pred:
        return green(true)
    else:
        return red(false)


def color_by_range(val, s, low=0.25, mid=0.50, high=0.75):
    f = float(val)
    if f < 0.25:
        return s
    elif f < 0.50:
        return green(s)
    elif f < 0.75:
        return yellow(s)
    else:
        return red(s)


def service_status(c, service):
    activity = green("active") if systemd.is_active(c, service) else red("inactive")
    return f"{service}: {activity}"


def ufw_status(c):
    ufw_on = green("active") if systemd.is_active(c, "ufw") else red("inactive")
    ufw_fw = green("enabled") if ufw.enabled(c, sudo=True) else red("disabled")

    return f"{ufw_on} + {ufw_fw}"


def avg_cpu_load(c):
    load_avg = c.run("cat /proc/loadavg | cut -d' ' -f1-3").stdout.strip()
    loads = [color_by_range(l, l) for l in load_avg.split()]
    return " ".join(loads)


def memory_load(c):
    mem = c.run("free -m | sed -n 2p | awk '{print $3 \" \" $2}'").stdout.strip()
    mem = mem.split()

    free = int(mem[0])
    total = int(mem[1])

    pct = int((free / total) * 100.0)

    return color_by_range(float(free / total), f"{free}mb / {total}mb ({pct}%)")


@click.command()
@click.argument("host")
def entry(host):

    try:
        c = util.connect(host, True)

        ctx = build_context(c)

        gather_info(c, ctx)

        print("----------")
        print(c.run("uname -a").stdout.strip())
        print("----------")

        load_avg = avg_cpu_load(c)
        print(f"load average: {load_avg}")

        mem_load = memory_load(c)
        print(f"memory load: {mem_load}")

        print("----------")
        print(service_status(c, "nginx"))
        print(service_status(c, "redis"))
        print(service_status(c, "pubpublica"))
        print("----------")
        print("ufw: " + ufw_status(c))
        print(service_status(c, "fail2ban"))
    except KeyboardInterrupt:
        pass
    except Exception as err:
        print(err)


if __name__ == "__main__":
    entry()
