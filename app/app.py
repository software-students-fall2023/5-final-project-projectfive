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

from bson.objectid import ObjectId
oidtob62 = lambda oid: base62.encodebytes(oid.binary)
b62tooid = lambda b62: ObjectId(base62.decodebytes(b62).hex())

import base62
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
        elif not user:
            abort(401, "User not found")
        else:
            abort(401, "Incorrect password")


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
    # Find all plans with the flag "delete_me" set to True (cleans up interrupted sessions)
    DB.plans.delete_many({"username": current_user.username, "delete_me": True})
    vars = {"username": current_user.username}
    vars["plans"] = DB.plans.find({"username": current_user.username, "draft": False})
    vars["drafts"] = DB.plans.find({"username": current_user.username, "draft": True})
    for key in vars.keys():
        for item in vars[key]:
            item["id"] = oidtob62(item["_id"])
    return render_template("index.html", **vars)

@app.route("/plan/<plan_id>")
@login_required
def plan(plan_id):
    """View a plan."""
    plan = DB.plans.find_one({"_id": b62tooid(plan_id)})
    if not plan:
        abort(404, "Plan not found")
    if plan["private"] and plan["username"] != current_user.username:
        abort(403, "Plan is private")
    return render_template("plan.html", **plan)

@app.route("/create_plan", methods=["GET"])
@login_required
def create_plan():
    """Page to create a new plan."""
    if request.method == "GET":
        return render_template("create_plan.html")

@app.route("/submit_plan", methods=["POST"])
@login_required
def submit_plan():
    """Submit plan and redirect to settings of plan."""
    if request.method == "POST":
        name = request.form.get("name")
        content = request.form.get("content")
        draft = request.form.get("draft") == "Yes"
        if not name:
            abort(400, "Missing name")
        if not content:
            abort(400, "Missing content")
        if draft:
            oid = DB.plans.insert_one(
                {
                    "username": current_user.username,
                    "name": name,
                    "content": content,
                    "draft": True,
                    "private": False,
                    "delete_me": False,
                }
            ).inserted_id
            return redirect("/")
        oid = DB.plans.insert_one(
            {
                "username": current_user.username,
                "name": name,
                "content": content,
                "draft": False,
                "private": False,
                "delete_me": True,
            }
        ).inserted_id
        return redirect(f"/settings/{oidtob62(oid)}")

@app.route("/settings/<plan_id>", methods=["GET", "POST"])
@login_required
def settings(plan_id):
    """Settings page for a plan."""
    plan = DB.plans.find_one({"_id": b62tooid(plan_id)})
    if not plan:
        abort(404, "Plan not found")
    if plan["username"] != current_user.username:
        abort(403, "You do not own this plan")
    if request.method == "GET":
        return render_template("settings.html", **plan)
    if request.method == "POST":
        private = request.form.get("private") == "Yes"
        locked = request.form.get("locked") == "Yes"
        DB.plans.update_one(
            {"_id": b62tooid(plan_id)},
            {"$set": {"private": private, "locked": locked}},
        )
        if locked:
            # Need to get lock duration from user
            return redirect(f"/set_lock/{plan_id}")
        else:
            # Plan is finalized
            DB.plan.update_one({"_id": b62tooid(plan_id)}, {"$set": {"delete_me": False}})