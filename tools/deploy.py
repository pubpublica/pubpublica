import os
import sys
import json
from datetime import datetime
import getpass
import tarfile
import hashlib

from pypass import PasswordStore

import click
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

# TODO: replace with libpass
PASS = PasswordStore()


def build_context(c):
    with Guard("· gathering build information..."):
        context = config.get("DEPLOY") or {}
        context.update(config.get("PROVISION", {}))
        context.update(config.get("BUILD", {}))

        root = os.getcwd()
        context.update({"LOCAL_ROOT": root})

        version = util.version()
        context.update({"LOCAL_VERSION": version})

        commit = git.latest_commit_hash(c, ".")
        context.update({"COMMIT_HASH": commit})
        context.update({"SHORT_COMMIT_HASH": commit[:7]})

        timestamp = util.timestamp()
        context.update({"TIMESTAMP": timestamp})

        return context


def check_local_git_repo(c, context):
    with Guard("· checking git repo..."):
        root = context.get("LOCAL_ROOT")
        dirty = git.is_dirty(c, root)

        if dirty is None:
            raise GuardWarning(f"{root} is not a repository")

        if dirty:
            raise GuardWarning("repository is dirty")


def check_versions(c, context):
    with Guard("· checking versions..."):
        app_path = context.get("APP_PATH")
        remote_ver_file = os.path.join(app_path, "__version__.py")
        v_remote = fs.read_file(c, remote_ver_file)

        if not v_remote:
            raise GuardWarning("unable to retrieve deployed version")

        context.update({"REMOTE_VERSION": v_remote})

        v_local = context.get("LOCAL_VERSION")
        if not util.version_newer(v_local, v_remote):
            raise GuardWarning(f"{v_local} is older or equal to deployed {v_remote}")


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

        artifact_dir = "build/"
        artifact_file = f"pubpublica-{version}-{commit}.tar.gz"
        artifact_path = os.path.join(artifact_dir, artifact_file)

        with tarfile.open(artifact_path, "w:gz") as tar:
            for f in includes:
                tar.add(f, filter=tar_filter)

        context.update({"ARTIFACT_FILE": artifact_file})
        context.update({"ARTIFACT_LOCAL_PATH": artifact_path})

        md5 = hashlib.md5()
        block_size = 65536
        with open(artifact_path, "rb") as f:
            # while data := f.read(block_size): md5.update(data)
            while True:
                data = f.read(block_size)

                if not data:
                    break

                md5.update(data)

        context.update({"ARTIFACT_MD5": md5.hexdigest()})


def transfer_project(c, context):
    with Guard("· transferring..."):
        aftifact_file = context.get("ARTIFACT_FILE")
        artifact = context.get("ARTIFACT_LOCAL_PATH")

        app_path = context.get("APP_PATH")
        if not app_path:
            raise Exception("application has no remote path")

        if artifact and os.path.isfile(artifact):
            # if transfer fails, an exception is raised
            c.put(artifact, remote=app_path)
            return True

        artifact_remote_path = os.path.join(app_path, artifact_file)
        context.update({"ARTIFACT_REMOTE_PATH": artifact_remote_path})


def unpack_project(c, context):
    with Guard("· unpacking..."):
        app_path = context.get("APP_PATH")
        artifact = context.get("ARTIFACT_FILE")
        artifact_path = os.path.join(app_path, artifact)
        cmd = f"cd {app_path} && tar -xzf {artifact}"
        unpack = c.run(cmd, hide=True, warn=True)

        if not unpack.ok:
            raise Exception(f"failed to unpack project: {unpack.stderr}")

        if not fs.remove(c, artifact_path):
            raise GuardWarning("failed to remove artifact after unpacking")


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
            pw = PASS.get_decrypted_password(path).strip()
            cfg.update({"FLASK_SECRET_KEY": pw})
            cfg.pop("FLASK_SECRET_KEY_PATH", None)

        config_path = context.get("LOCAL_CONFIG_PATH")
        flask_template = os.path.join(config_path, ".flask")
        flask_config = util.template(flask_template, cfg)

    with Guard("· writing config files..."):
        pass


def setup_redis(c, context):
    print("setting up redis")

    cfg = config.get("REDIS") or {}
    if not cfg:
        log.warning("unable to locate redis config")

    local_config_path = context.get("LOCAL_CONFIG_PATH")
    if not os.path.isdir(local_config_path):
        raise Exception(f"local config path {local_config_path} does not exist")

    app_path = context.get("APP_PATH")
    if not app_path:
        raise Exception("dont know where the app is located")

    config_file = cfg.get("REDIS_CONFIG_FILE")
    if not config_file:
        raise Exception("dont know where the redis config file is located")

    config_file_path = os.path.join(app_path, config_file)

    with Guard("· building config files..."):
        password_path = cfg.get("REDIS_PASSWORD_PATH")
        if password_path:
            pw = PASS.get_decrypted_password(password_path).strip()
            cfg.update({"REDIS_PASSWORD": pw})
            cfg.pop("REDIS_PASSWORD_PATH", None)

        redis_template = os.path.join(local_config_path, config_file)
        rendered_config = util.template(redis_template, cfg)

    with Guard("· writing config files..."):
        config_string = json.dumps(rendered_config, indent=4)
        tmpfile = config_file_path + ".new"
        fs.overwrite_file(c, config_string, tmpfile, sudo=True)
        fs.move(c, tmpfile, config_file_path, sudo=True)

    with Guard("· setting permissions..."):
        user = context.get("USER")
        if user:
            if not access.change_owner(c, config_file_path, user, sudo=True):
                raise Exception(f"failed to own {config_file}")

        group = context.get("GROUP")
        if group:
            if not access.change_group(c, config_file_path, group, sudo=True):
                raise Exception(f"failed to change group of {config_file} to")


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
        pass
        # create pubpublica user
        # create pubpublica group
        # add user to group

    with Guard("· changing owner, group, and mode..."):
        app_path = context.get("APP_PATH")
        config_file = context.get("PUBPUBLICA_CONFIG_FILE")
        config_file_path = os.path.join(app_path, config_file)

        # TODO: own all app files

        user = context.get("USER")
        if user:
            if not access.change_owner(c, config_file_path, user, sudo=True):
                raise Exception(f"failed to change owner of {config_file}")

        group = context.get("GROUP")
        if group:
            if not access.change_group(c, config_file_path, group, sudo=True):
                raise Exception(f"failed to change group of {config_file} to")


def setup_pubpublica_virtualenv(c, context):
    # TODO: create venv
    # with Guard("· creating virtual environment..."):

    with Guard("· updating virtual environment..."):
        cd_dir = "cd pubpublica/"
        activate_venv = ". venv/bin/activate"
        pip_install = "pip install -r requirements.txt"
        cmd = " && ".join([cd_dir, activate_venv, pip_install])

        ret = c.run(cmd, hide=True, warn=True)
        if not ret.ok:
            raise GuardWarning(f"failed to update the virtual environment: {ret}")


def setup_pubpublica(c, context):
    print("setting up pubpublica")

    cfg = config.get("PUBPUBLICA") or {}
    if not cfg:
        log.warning("unable to locate pubpublica config")

    ctx = {**context, **cfg}

    local_config_path = context.get("LOCAL_CONFIG_PATH")
    if not os.path.isdir(local_config_path):
        raise Exception(f"local config path {local_config_path} does not exist")

    app_path = context.get("APP_PATH")
    if not app_path:
        raise Exception("dont know where the app is located")

    config_file = cfg.get("PUBPUBLICA_CONFIG_FILE")
    if not config_file:
        raise Exception("dont know where the config_file is located")

    config_file_path = os.path.join(app_path, config_file)

    with Guard("· building config files..."):
        template_path = os.path.join(local_config_path, config_file)
        rendered_config = util.template(template_path, ctx)

    with Guard("· writing config files..."):
        config_string = json.dumps(rendered_config, indent=4)
        tmpfile = config_file_path + ".new"
        fs.overwrite_file(c, config_string, tmpfile, sudo=True)
        fs.move(c, tmpfile, config_file_path, sudo=True)

    setup_pubpublica_access(c, ctx)

    with Guard("· creating links..."):
        pass

    setup_pubpublica_virtualenv(c, ctx)


def pre_deploy(c, local, context):
    print("PRE DEPLOY")
    context.update({"DEPLOY_START_TIME": util.timestamp()})
    check_local_git_repo(local, context)
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

    # TODO: only restart services whoose config has changed
    restart_service(c, "redis")
    restart_service(c, "nginx")

    context.update({"DEPLOY_END_TIME": util.timestamp()})


def main(host):
    try:
        local = Context()
        c = util.connect(host, sudo=True)

        context = build_context(local)

        # TODO: validate context with jsonschema

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
