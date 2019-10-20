import os
import json
import random

from flask import Flask, render_template, make_response
from flask import request
from flask_caching import Cache

from pubpublica import util

app = Flask(__name__)

flask_config = util.load_json(".flask")
if flask_config:
    print("loaded flask config from .flask")
    app.config.update(flask_config)

pubpublica_config = util.load_json(".pubpublica")
if pubpublica_config:
    print("loaded pubpublica config from .pubpublica")

cache_config = util.load_json(".redis")
if cache_config:
    print("loaded cache config from .redis")

cache = Cache(config=cache_config)
cache.init_app(app)


@app.route("/")
@cache.cached(timeout=300)
def index():
    pubs = []
    path = pubpublica_config.get("PUBLICATIONS_PATH")
    if path:
        pubs = util.get_publications(path)

    ctx = {"PUBLICATIONS": pubs}

    return render_template("index.html", ctx=ctx)


@app.route("/rss")
@cache.cached(timeout=500)
def rss():
    pubs = []
    path = pubpublica_config.get("PUBLICATIONS_PATH")
    if path:
        pubs = util.get_publications(path)

    pubs = util.rss_convert(pubs)

    ctx = {"PUBLICATIONS": pubs}

    response = make_response(render_template("rss.xml", ctx=ctx))
    response.headers["Content-Type"] = "application/xml"
    return response
