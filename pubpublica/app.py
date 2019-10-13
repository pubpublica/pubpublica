import os
import json
import random

from flask import Flask, render_template, make_response
from flask import request
from flask_caching import Cache

from pubpublica import utils

app = Flask(__name__)
app.config.update(utils.load_secrets(".pubpublica"))
app.config.update(utils.load_secrets(".flask_secrets"))

cache_config = {}
cache_config.update(utils.load_secrets(".redis_secrets"))

cache = Cache(config=cache_config)
cache.init_app(app)


@app.route("/")
@cache.cached(timeout=60)
def index():
    ctx = app.config.get("pubpublica")

    pubs = utils.get_publications(ctx.get("PUBLICATIONS_PATH"))
    ctx.update({"publications": pubs})

    return render_template("index.html", ctx=ctx)


@app.route("/rss")
@cache.cached(timeout=500)
def rss():
    ctx = app.config.get("pubpublica")

    pubs = utils.get_publications(ctx.get("PUBLICATIONS_PATH"))
    pubs = utils.rss_convert(pubs)

    ctx.update({"publications": pubs})

    response = make_response(render_template("rss.xml", ctx=ctx))
    response.headers["Content-Type"] = "application/xml"
    return response


def get_query_args(query):
    args = request.args.get(query)
    return args.split() if args else []


@app.route("/c/")
def custom():
    tags = get_query_args("tags")
    return f"tags: {tags}!"
