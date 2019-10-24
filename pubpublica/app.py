import os
import json
import random
import logging

from systemd import journal

from flask import Flask, render_template, make_response
from flask import request
from flask.logging import default_handler
from flask_caching import Cache

from pubpublica import util

# we setup logging before creating the flask app so it uses this
# logging configuration.

# we configure the root log so other modules will also use this
# configuration.

root_log = logging.getLogger()
root_log.setLevel(logging.DEBUG)

log_format = "%(asctime)s - [%(levelname)s]: %(message)s " ""
formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

# the stream handler pipes the output to stdout/stderr, which is in
# turn handles by uwsgi, and put into a corresponding rotating logfile
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# also log things to the systemd journal
journald_handler = journal.JournalHandler(SYSLOG_IDENTIFIER="pubpublica")

root_log.addHandler(stream_handler)
root_log.addHandler(journald_handler)

app = Flask(__name__)

flask_config = util.load_json(".flask")
if flask_config:
    app.logger.info("loaded flask config from .flask")
    app.config.update(flask_config)

pubpublica_config = util.load_json(".pubpublica")
if pubpublica_config:
    app.logger.info("loaded pubpublica config from .pubpublica")

cache_config = util.load_json(".redis")
if cache_config:
    app.logger.info("loaded cache config from .redis")

cache = Cache(config=cache_config)
cache.init_app(app)


@app.route("/")
@cache.cached(timeout=300)
def index():
    app.logger.info("Generating INDEX for cache.")

    pubs = []
    path = pubpublica_config.get("PUBLICATIONS_PATH")
    if path:
        pubs = util.get_publications(path)

    ctx = {"PUBLICATIONS": pubs}
    ctx.update(pubpublica_config)

    return render_template("index.html", ctx=ctx)


@app.route("/rss")
@cache.cached(timeout=500)
def rss():
    pubs = []
    path = pubpublica_config.get("PUBLICATIONS_PATH")
    if path:
        pubs = util.get_publications(path)

    # TODO: sort publications by latest

    pubs = util.rss_convert(pubs)

    ctx = {"PUBLICATIONS": pubs}
    ctx.update(pubpublica_config)

    response = make_response(render_template("rss.xml", ctx=ctx))
    response.headers["Content-Type"] = "application/xml"
    return response
