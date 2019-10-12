import os
import json
import random

from flask import Flask, render_template, make_response
from flask import request

from pubpublica import utils

app = Flask(__name__)


@app.route("/")
def index():
    pubs = utils.get_publications("pubpublica/publications/")

    ctx = {"publications": pubs}
    return render_template("index.html", ctx=ctx)


@app.route("/rss")
def rss():
    pubs = utils.get_publications("pubpublica/publications/")
    pubs = utils.rss_convert(pubs)
    ctx = {"publications": pubs}

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
