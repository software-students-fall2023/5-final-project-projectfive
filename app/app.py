"""Main application file for the Flask app."""

from os import path, environ
from sys import stderr
from base64 import b64decode
from flask import Flask, abort, render_template, request, redirect
from flask_login import (
    login_required,
    login_user,
    logout_user,
    current_user,
    LoginManager,
    UserMixin,
)
import pymongo
import argon2

Hasher = argon2.PasswordHasher().from_parameters(argon2.profiles.RFC_9106_LOW_MEMORY)

TFs = {
    "True": True,
    "true": True,
    "1": True,
    "False": False,
    "false": False,
    "0": False,
}


def should_debug() -> bool:
    """Returns True if the DEBUG environment variable is set to a truthy value."""
    try:
        return TFs[environ.get("DEBUG")]
    except KeyError:
        print("Unknown value for DEBUG environment variable.", file=stderr)


DB = None

template_dir = path.abspath("./templates")
static_dir = path.abspath("./static")

login_manager = LoginManager()
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = environ.get(b64decode(bytes(environ.get("FLASK_SECRET_KEY"), "utf-8")))
login_manager.init_app(app)


def main():
    """Connect to DB and run app."""
    global DB
    client = pymongo.MongoClient(
        f"mongodb://{environ.get('MONGO_USERNAME')}:{environ.get('MONGO_PASSWORD')}@mongo"
    )
    DB = client["DB"]
    # SECURITY: Production will use SSL. This is only for development.
    app.run(host="0.0.0.0", port=80, debug=should_debug())


class User(UserMixin):
    """User class for flask_login."""

    def __init__(self, username, pwhash):
        self.username = username
        self.pwhash = pwhash

    def get_id(self):
        # NOTE: This is a string, not an ObjectId, usernames are guaranteed unique
        return self.username


@login_manager.user_loader
def load_user(username):
    """Load user from DB."""
    user = DB.users.find_one({"username": username})
    if user:
        return User(user["username"], user["pwhash"])
    else:
        return None


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to login page.
    Triggered by @login_required decorator."""
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Invites users to login or click a button
    to go to the account registration page."""
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            abort(400, "Missing username or password")  # bad request
        user = DB.users.find_one({"username": username})
        if user and Hasher.verify(user["pwhash"], password):
            login_user(User(username, user["pwhash"]))
            return redirect("/")
        else:
            abort(401)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Invites users to register an account."""
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            abort(400, "Missing username or password")
        elif DB.users.find_one({"username": username}):
            abort(409, "Username already taken")
        else:
            DB.users.insert_one({"username": username, "pwhash": Hasher.hash(password)})
            return redirect("/login")


@app.route("/logout")
@login_required
def logout():
    """Logs out the user."""
    logout_user()
    return redirect("/login")


@app.route("/")
@login_required
def index():
    """Homepage, gives options to choose a plan/draft or create a new plan"""
    # TODO: Define variables for rendering index.html
    return render_template("index.html")
