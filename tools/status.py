import os
import sys
import json
import getpass

from paramiko.config import SSHConfig
from fabric import Config, Connection
from termcolor import colored

import util
from util import Guard


def color_by_predicate(pred, true, false):
    if pred:
        return colored(true, "green")
    else:
        return colored(false, "red")


def color_by_range(val, s, low=0.25, mid=0.50, high=0.75):
    f = float(val)
    if f < 0.25:
        return s
    elif f < 0.50:
        return colored(s, "green")
    elif f < 0.75:
        return colored(s, "yellow")
    else:
        return colored(s, "red")


def is_service_active(c, service):
    status = c.run(f"systemctl is-active {service}")
    return status.exited == 0 and status.stdout.strip() == "active"


def service_status(c, service):
    activity = ""

    active = is_service_active(c, service)
    activity = color_by_predicate(active, "active", "inactive")
    return f"{service}: {activity}"


def ufw_status(c):
    ufw_service = is_service_active(c, "ufw")
    ufw_enabled = c.sudo("sudo ufw status | grep -qw active").exited == 0

    ufw_on = color_by_predicate(ufw_service, "active", "inactive")
    ufw_fw = color_by_predicate(ufw_enabled, "enabled", "disabled")

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

    return color_by_range(float(free / total), f"{free}mb / {total}mb")


def pubpublica_version(c):
    date = c.run("cd pubpublica && git log --format='%ai' -n 1").stdout.strip()
    commit = c.run("cd pubpublica && git log --format='%H' -n 1").stdout.strip()[:7]
    msg = c.run("cd pubpublica && git log --format='%B' -n 1").stdout.strip()
    tags = c.run("cd pubpublica && git tag -l --points-at HEAD").stdout.strip()
    tags = f"({tags}) " if tags else ""
    return f'[{date}] {colored(commit, "yellow")} {tags}- "{msg}"'


def is_online(c, host):
    config = SSHConfig()
    with open("/home/jens/.ssh/config", "r") as f:
        config.parse(f)

    host_map = config.lookup(host)

    if not host_map:
        print(f"could not find {host} in ssh config")
        return False

    ip = host_map.get("hostname")
    ping = c.local(f"ping -c 1 {ip}")

    is_online = ping.exited == 0

    if is_online:
        print(f"{host}: " + colored("online", "green"))
    else:
        print(f"{host}: " + colored("offline", "red"))

    return is_online


def main(host):
    c = util.connect(host, True)

    print("----------")
    online = is_online(c, host)
    if not online:
        sys.exit(1)

    print("----------")
    print(c.run("uname -a").stdout.strip())
    print("----------")

    load_avg = avg_cpu_load(c)
    print(f"load average: {load_avg}")

    mem_load = memory_load(c)
    print(f"memory load: {mem_load}")

    print("----------")
    print(service_status(c, "nginx"))
    print(service_status(c, "pubpublica"))
    print("----------")
    print("ufw: " + ufw_status(c))
    print(service_status(c, "fail2ban"))
    print("----------")
    ver = pubpublica_version(c)
    print(f"version: {ver}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: status.py <host>")
        sys.exit(1)

    host = sys.argv[1]

    main(host)
