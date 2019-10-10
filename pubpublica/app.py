from flask import Flask
from flask import request

app = Flask(__name__)


@app.route("/")
def hello():
    return "hello world!"


@app.route("/search/")
def search():
    tags = request.args.get("tags").split()
    for tag in tags:
        print(tag)

    return f"tags: {tags}!"
