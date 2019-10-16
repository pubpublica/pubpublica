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
from fabrikant import fs, info
from fabrikant.apps import git

from config import config
from pubpublica.util import load_json

import log
import util
from util import Guard

pwstore = PasswordStore()


def gather_local_build_info(c):
    with Guard("· gathering build information..."):
        cfg = {}

        commit = git.latest_commit_hash(c, ".")
        cfg.update({"COMMIT_HASH": commit})

        timestamp = datetime.datetime.utcnow().isoformat()
        cfg.update({"TIMESTAMP": timestamp})

        config_path = config.get("LOCAL_CONFIG_PATH")
        template = os.path.join(config_path, ".pubpublica")
        build_info = util.template(template, cfg)

        return json.loads(build_info)


def pack_project(c, build_info):
    def tar_filter(info):
        if "__pycache__" in info.name:
            return None

        return info

    with Guard("· packing..."):
        commit = build_info.get("commit")[:7]
        with tarfile.open(f"build/pubpublica-{commit}.tar.gz", "w:gz") as tar:
            for f in [
                "requirements.txt",
                "pubpublica.ini",
                "wsgi.py",
                "publications/",
                "pubpublica/",
            ]:
                tar.add(f, filter=tar_filter)


def unpack_project(c):
    with Guard("· unpacking..."):
        pass


def restart_service(c, service):
    with Guard(f"· restarting {service} service..."):
        pass


def setup_flask(c):
    with Guard(f"· setting up flask..."):
        cfg = config.get("FLASK")

        path = cfg.get("FLASK_SECRET_KEY_PATH")
        if path:
            pw = pwstore.get_decrypted_password(path).strip()
            cfg.update({"FLASK_SECRET_KEY": pw})
            cfg.pop("FLASK_SECRET_KEY_PATH", None)

        path = config.get("LOCAL_CONFIG_PATH")
        flask_template = os.path.join(path, ".flask")
        flask_config = util.template(flask_template, cfg)


def setup_redis(c):
    with Guard(f"· setting up redis..."):
        cfg = config.get("REDIS")

        path = cfg.get("REDIS_PASSWORD_PATH")
        if path:
            pw = pwstore.get_decrypted_password(path).strip()
            cfg.update({"REDIS_PASSWORD": pw})
            cfg.pop("REDIS_PASSWORD_PATH", None)

        path = config.get("LOCAL_CONFIG_PATH")
        redis_template = os.path.join(path, ".redis")
        redis_config = util.template(redis_template, cfg)


def pre_deploy(c, build_info):
    print("PRE DEPLOY")
    print("· checking dependencies...")


def deploy(c, build_info):
    print("DEPLOY")
    pack_project(c, build_info)
    print("· transferring...")
    unpack_project(c)
    print("· writing config files...")
    print("· changing owners, groups, and modes...")
    print("· creating links...")
    print("· making virtual environment...")
    print("· installing app dependencies...")
    setup_flask(c)
    setup_redis(c)


def post_deploy(c, build_info):
    print("POST DEPLOY")
    restart_service(c, "nginx")
    restart_service(c, "pubpublica")


def main(host):
    try:
        local = Context()
        c = util.connect(host)

        build_info = gather_local_build_info(local)
        pre_deploy(c, build_info)
        deploy(c, build_info)
        post_deploy(c, build_info)

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
