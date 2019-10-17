import os
import sys
import json
import datetime
import getpass
import tarfile

from pypass import PasswordStore

import invoke
from invoke.context import Context
import fabric
from fabric import Config, Connection
from fabrikant import fs, info, environment
from fabrikant.apps import git, systemd, apt

from config import config

import log
import util
from util import Guard

pwstore = PasswordStore()


def build_context(c):
    with Guard("· gathering build information..."):
        context = config.get("DEPLOY") or {}
        context.update(config.get("BUILD", {}))

        version = util.version()
        context.update({"VERSION": version})

        commit = git.latest_commit_hash(c, ".")
        context.update({"COMMIT_HASH": commit})

        timestamp = util.timestamp()
        context.update({"TIMESTAMP": timestamp})

        return context


def check_dependencies(c, context):
    with Guard("· checking dependencies..."):
        deps = context.get("DEPENDENCIES")
        for dep in deps:
            installed = apt.is_installed(c, dep)
            if not installed:
                raise Exception(f"{dep} is not installed.")


def pack_project(c, context):
    def tar_filter(info):
        if "__pycache__" in info.name:
            return None
        return info

    with Guard("· packing..."):
        commit = context.get("COMMIT_HASH")[:7]
        artifact = f"build/pubpublica-{commit}.tar.gz"
        with tarfile.open(artifact, "w:gz") as tar:
            for f in [
                "__version__.py",
                "requirements.txt",
                "pubpublica.ini",
                "wsgi.py",
                "publications/",
                "pubpublica/",
            ]:
                tar.add(f, filter=tar_filter)

        context.update({"ARTIFACT": artifact})


def transfer_project(c, context):
    with Guard("· transferring..."):
        pass

def unpack_project(c, context):
    with Guard("· unpacking..."):
        pass


def restart_service(c, service):
    with Guard(f"· restarting {service} service..."):
        pass


def setup_flask(c, context):
    with Guard(f"· setting up flask..."):
        cfg = config.get("FLASK")

        path = cfg.get("FLASK_SECRET_KEY_PATH")
        if path:
            pw = pwstore.get_decrypted_password(path).strip()
            cfg.update({"FLASK_SECRET_KEY": pw})
            cfg.pop("FLASK_SECRET_KEY_PATH", None)

        path = context.get("LOCAL_CONFIG_PATH")
        flask_template = os.path.join(path, ".flask")
        flask_config = util.template(flask_template, cfg)


def setup_redis(c, context):
    with Guard(f"· setting up redis..."):
        cfg = config.get("REDIS")

        path = cfg.get("REDIS_PASSWORD_PATH")
        if path:
            pw = pwstore.get_decrypted_password(path).strip()
            cfg.update({"REDIS_PASSWORD": pw})
            cfg.pop("REDIS_PASSWORD_PATH", None)

        path = context.get("LOCAL_CONFIG_PATH")
        redis_template = os.path.join(path, ".redis")
        redis_config = util.template(redis_template, cfg)


def setup_pubpublica_access(c, context):
    # create pubpublica user
    # create pubpublica group
    # add user to group
    with Guard("· changing owners, groups, and modes..."):
        pass


def setup_pubpublica_virtualenv(c, context):
    with Guard("· making virtual environment..."):
        pass


def setup_pubpublica(c, context):
    with Guard(f"· setting up pubpublica..."):
        pubpublica = config.get("PUBPUBLICA") or {}

        context = {**context, **pubpublica}

        config_path = context.get("LOCAL_CONFIG_PATH")
        pubpublica_template = os.path.join(config_path, ".pubpublica")
        pubpublica_config = util.template(pubpublica_template, context)

        print()
        print("· writing config files...")
        setup_pubpublica_access(c, context)
        print("· creating links...")
        setup_pubpublica_virtualenv(c, context)


def pre_deploy(c, context):
    print("PRE DEPLOY")
    context.update({"DEPLOY_START_TIME": util.timestamp()})
    check_dependencies(c, context)


def deploy(c, context):
    print("DEPLOY")
    pack_project(c, context)
    transfer_project(c, context)
    unpack_project(c, context)

    setup_pubpublica(c, context)
    setup_flask(c, context)
    setup_redis(c, context)


def post_deploy(c, context):
    print("POST DEPLOY")
    # systemd.enable(c, "pubpublica")
    # systemd.start(c, "pubpublica")
    # systemd.enable(c, "nginx")
    # systemd.start(c, "nginx")
    context.update({"DEPLOY_END_TIME": util.timestamp()})


def main(host):
    try:
        local = Context()
        c = util.connect(host)

        context = build_context(local)

        pre_deploy(c, context)
        deploy(c, context)
        post_deploy(c, context)

        util.print_json(context)

        log.success("deployment complete")
    except KeyboardInterrupt:
        pass
    except Exception as err:
        print(err)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python deploy.py <host>")
        sys.exit(1)

    host = sys.argv[1]
    main(host)
