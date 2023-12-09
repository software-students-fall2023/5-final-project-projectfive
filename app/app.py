from os import path, environ
from base64 import b64decode
from flask import Flask, render_template, request, redirect
from flask_login import (
    login_required,
    login_user,
    logout_user,
    current_user,
    LoginManager,
)
import pymongo

TFs = {
    "True": True,
    "true": True,
    "1": True,
    "False": False,
    "false": False,
    "0": False,
}


def shouldDebug() -> bool:
    if environ.get("DEBUG") in TFs:
        return TFs[environ.get("DEBUG")]
    else:
        raise ValueError("Unknown value for DEBUG environment variable.")


DB = None

template_dir = path.abspath("./templates")
static_dir = path.abspath("./static")

login_manager = LoginManager()
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = environ.get(b64decode(bytes(environ.get("FLASK_SECRET_KEY"), "utf-8")))
login_manager.init_app(app)


def main():
    global DB
    client = pymongo.MongoClient(
        f"mongodb://{environ.get('MONGO_USERNAME')}:{environ.get('MONGO_PASSWORD')}@mongo"
    )
    DB = client["DB"]
    app.run(host="0.0.0.0", port=80, debug=shouldDebug())


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to login page.
    Triggered by @login_required decorator."""
    # TODO: Make login template with extra hyperlink to register user.
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Invites users to login or click a button
    to go to the account registration page."""
    # TODO: Implement login functionality
    return 501


@app.route("/")
@login_required
def index():
    # TODO: Define variables for rendering index.html
    return render_template("index.html")
