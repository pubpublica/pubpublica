import os
import sys
import json

import getpass
from paramiko.config import SSHConfig
from fabric import Config, Connection

from termcolor import colored


def is_service_active(c, service):
    status = c.run(f"systemctl is-active {service}")
    return status.exited == 0 and status.stdout.strip() == "active"


def service_status(c, service):
    activity = ""

    if is_service_active(c, service):
        activity = colored("active", "green")
    else:
        activity = colored("inactive", "red")

    return f"{service}: {activity}"


def ufw_status(c):
    ufw_service = is_service_active(c, "ufw")
    ufw_enabled = c.sudo("sudo ufw status | grep -qw active").exited == 0

    ufw_on = colored("active", "green") if ufw_service else colored("inactive", "red")
    ufw_fw = colored("online", "green") if ufw_enabled else colored("offline", "red")

    return f"{ufw_on} + {ufw_fw}"


def avg_cpu_load(c):
    def color_load(load):
        fload = float(load)
        if fload < 0.25:
            return load
        elif fload < 0.50:
            return colored(load, "green")
        elif fload < 0.75:
            return colored(load, "yellow")
        else:
            return colored(load, "red")

    load_avg = c.run("cat /proc/loadavg | cut -d' ' -f1-3").stdout.strip()
    loads = [color_load(l) for l in load_avg.split()]
    return " ".join(loads)


def memory_load(c):
    def color_mem(free, total):
        free = int(free)
        total = int(total)

        if free / total < 0.25:
            return colored(f"{free}mb / {total}mb")
        if free / total < 0.50:
            return colored(f"{free}mb / {total}mb", "green")
        if free / total < 0.75:
            return colored(f"{free}mb / {total}mb", "yellow")
        else:
            return colored(f"{free}mb / {total}mb", "red")

    mem = c.run("free -m | sed -n 2p | awk '{print $3 \" \" $2}'").stdout.strip()
    mems = mem.split()

    return color_mem(mems[0], mems[1])


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
    config = Config()

    settings = {"hide": True, "warn": True}
    config["sudo"].update(settings)
    config["run"].update(settings)

    sudo_pass = getpass.getpass("sudo password: ")
    config["sudo"].update({"password": sudo_pass})

    c = Connection(host, config=config)

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
