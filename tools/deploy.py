import os
import sys
import json
import datetime
import getpass
import tarfile
import hashlib

from pypass import PasswordStore

import invoke
from invoke.context import Context
import fabric
from fabric import Config, Connection
from fabrikant import fs, system, access
from fabrikant.apps import git, systemd, apt

from config import config

import log
import util
from util import Guard, GuardWarning

pwstore = PasswordStore()


def build_context(c):
    with Guard("· gathering build information..."):
        context = config.get("DEPLOY") or {}
        context.update(config.get("PROVISION", {}))
        context.update(config.get("BUILD", {}))

        root = os.getcwd()
        context.update({"ROOT": root})

        version = util.version()
        context.update({"LOCAL_VERSION": version})

        commit = git.latest_commit_hash(c, ".")
        context.update({"COMMIT_HASH": commit})
        context.update({"SHORT_COMMIT_HASH": commit[:7]})

        timestamp = util.timestamp()
        context.update({"TIMESTAMP": timestamp})

        return context


def check_git(c, context):
    with Guard("· checking git repo..."):
        root = context.get("ROOT")
        dirty = git.is_dirty(c, root)

        if dirty is None:
            raise GuardWarning(f"{root} is not a repository")

        if dirty:
            raise GuardWarning("repository is dirty")


def check_versions(c, context):
    with Guard("· checking versions..."):
        remote_path = context.get("APP_PATH")
        remote_ver_path = os.path.join(remote_path, "__version__.py")
        remote_ver = fs.read_file(c, remote_ver_path)

        if not remote_ver:
            raise GuardWarning("unable to retrieve deployed version")

        context.update({"REMOTE_VERSION": remote_ver})

        local_ver = context.get("LOCAL_VERSION")
        if not util.version_newer(local_ver, remote_ver):
            raise Exception(f"{local_ver} is older or equal to deployed {remote_ver}")


def check_dependencies(c, context):
    with Guard("· checking dependencies..."):
        deps = context.get("DEPENDENCIES") or []
        for dep in deps:
            if not apt.is_installed(c, dep):
                raise Exception(f"{dep} is not installed.")


def pack_project(c, context):
    def tar_filter(info):
        if "__pycache__" in info.name:
            return None
        return info

    with Guard("· packing..."):
        includes = context.get("INCLUDES") or []
        commit = context.get("SHORT_COMMIT_HASH")
        version = context.get("LOCAL_VERSION")
        artifact = f"build/pubpublica-{version}-{commit}.tar.gz"
        with tarfile.open(artifact, "w:gz") as tar:
            for f in includes:
                tar.add(f, filter=tar_filter)

        context.update({"ARTIFACT": artifact})

        md5 = hashlib.md5()
        block_size = 65536
        with open(artifact, "rb") as f:
            while True:
                data = f.read(block_size)

                if not data:
                    break

                md5.update(data)

        context.update({"ARTIFACT_MD5": md5.hexdigest()})


def transfer_project(c, context):
    # TODO: copy over app package
    with Guard("· transferring..."):
        pass


def unpack_project(c, context):
    # TODO: unpack app package
    with Guard("· unpacking..."):
        pass


def restart_service(c, service):
    with Guard(f"· restarting {service} service..."):
        # systemd.restart(c, service, sudo=True)
        pass


def setup_flask(c, context):
    # TODO: merge with setup_pubpublica?
    print("setting up flask")

    with Guard("· building config files..."):
        cfg = config.get("FLASK") or {}

        path = cfg.get("FLASK_SECRET_KEY_PATH")
        if path:
            pw = pwstore.get_decrypted_password(path).strip()
            cfg.update({"FLASK_SECRET_KEY": pw})
            cfg.pop("FLASK_SECRET_KEY_PATH", None)

        config_path = context.get("LOCAL_CONFIG_PATH")
        flask_template = os.path.join(config_path, ".flask")
        flask_config = util.template(flask_template, cfg)

    with Guard("· writing config files..."):
        pass


def setup_redis(c, context):
    # TODO: copy over redis settings
    print("setting up redis")

    with Guard("· building config files..."):
        cfg = config.get("REDIS") or {}

        path = cfg.get("REDIS_PASSWORD_PATH")
        if path:
            pw = pwstore.get_decrypted_password(path).strip()
            cfg.update({"REDIS_PASSWORD": pw})
            cfg.pop("REDIS_PASSWORD_PATH", None)

        config_path = context.get("LOCAL_CONFIG_PATH")
        redis_template = os.path.join(config_path, ".redis")
        redis_config = util.template(redis_template, cfg)

    with Guard("· writing config files..."):
        pass


def setup_nginx(c, context):
    # TODO: copy over nginx settings
    print("setting up nginx")

    with Guard("· building config files..."):
        cfg = config.get("NGINX") or {}

        config_path = context.get("LOCAL_CONFIG_PATH")
        nginx_template = os.path.join(config_path, ".nginx")
        nginx_config = util.template(nginx_template, cfg)

    with Guard("· writing config files..."):
        pass


def setup_pubpublica_access(c, context):
    # TODO: create user and group
    with Guard("· creating user and group..."):
        # create pubpublica user
        # create pubpublica group
        # add user to group
        pass

    # TODO: own app files
    with Guard("· changing owner, group, and mode..."):
        app = context.get("APP_PATH")

        if not app:
            raise Exception("Dont know where the app is located")

        user = context.get("USER")
        if user:
            pass
            # chg = fs.change_owner(c, app, recursive=True)

            # if not chg:
            #     raise Exception(f"failed to own {app}")

        group = context.get("GROUP")
        if group:
            pass
            # chg = fs.change_owner(c, app, recursive=True)

            # if not chg:
            #     raise Exception(f"failed to own {app}")


def setup_pubpublica_virtualenv(c, context):
    # TODO: create venv
    with Guard("· making virtual environment..."):
        pass


def setup_pubpublica(c, context):
    print("setting up pubpublica")

    with Guard("· building config files..."):
        pubpublica = config.get("PUBPUBLICA") or {}

        context = {**context, **pubpublica}

        config_path = context.get("LOCAL_CONFIG_PATH")
        pubpublica_template = os.path.join(config_path, ".pubpublica")
        pubpublica_config = util.template(pubpublica_template, context)

    with Guard("· writing config files..."):
        pass

    setup_pubpublica_access(c, context)

    with Guard("· creating links..."):
        pass

    setup_pubpublica_virtualenv(c, context)


def pre_deploy(c, local, context):
    print("PRE DEPLOY")
    context.update({"DEPLOY_START_TIME": util.timestamp()})
    check_git(local, context)
    check_versions(c, context)
    check_dependencies(c, context)
    if not systemd.stop(c, "pubpublica", sudo=True):
        log.error("failed to stop the pubpublica servce")


def deploy(c, context):
    print("DEPLOY")
    pack_project(c, context)
    transfer_project(c, context)
    unpack_project(c, context)

    setup_pubpublica(c, context)
    setup_flask(c, context)
    setup_redis(c, context)
    setup_nginx(c, context)


def post_deploy(c, context):
    print("POST DEPLOY")
    if not systemd.start(c, "pubpublica", sudo=True):
        log.error("failed to start the pubpublica servce")

    restart_service("redis")
    restart_service("nginx")

    context.update({"DEPLOY_END_TIME": util.timestamp()})


def main(host):
    try:
        local = Context()
        c = util.connect(host, sudo=True)

        context = build_context(local)

        pre_deploy(c, local, context)
        deploy(c, context)
        post_deploy(c, context)

        util.print_json(context)

        log.success("deployment complete")
    except KeyboardInterrupt:
        pass
    except Exception as err:
        log.error(err)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python deploy.py <host>")
        sys.exit(1)

    host = sys.argv[1]
    main(host)
