import os
import json
import random

from flask import Flask, render_template, make_response
from flask import request
from flask_caching import Cache

from pubpublica import util

from config import config

app = Flask(__name__)
app.config.update(util.load_json(".flask"))
app.config.update({"pubpublica": util.load_json(".pubpublica")})

cache_config = {}
cache_config.update(util.load_json(".redis"))
cache = Cache(config=cache_config)
cache.init_app(app)


@app.route("/")
@cache.cached(timeout=300)
def index():
    ctx = app.config.get("pubpublica") or {}

    pubs = []
    path = ctx.get("PUBLICATIONS_PATH")
    if path:
        pubs = util.get_publications(path)

    ctx.update({"PUBLICATIONS": pubs})

    return render_template("index.html", ctx=ctx)


@app.route("/rss")
@cache.cached(timeout=500)
def rss():
    ctx = app.config.get("pubpublica") or {}

    pubs = []
    path = ctx.get("PUBLICATIONS_PATH")
    if path:
        pubs = util.get_publications(path)

    pubs = util.rss_convert(pubs)

    ctx.update({"PUBLICATIONS": pubs})

    response = make_response(render_template("rss.xml", ctx=ctx))
    response.headers["Content-Type"] = "application/xml"
    return response
