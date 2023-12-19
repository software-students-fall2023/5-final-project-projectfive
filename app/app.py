"""Main application file for the Flask app."""

from os import path, environ
from sys import stderr
import datetime
from base64 import b64decode
import base62
from pymongo import MongoClient
import argon2
from re import match

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
login_manager = LoginManager()
template_dir = path.abspath("./templates")
static_dir = path.abspath("./static")
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = b64decode(environ.get("FLASK_SECRET_KEY"))
login_manager.init_app(app)


def main():
    """Connect to DB and run app."""
    global DB
    client = MongoClient(
        f"mongodb://{environ.get('MONGO_USERNAME')}:{environ.get('MONGO_PASSWORD')}@mongo?authSource=admin"
    )
    DB = client["DB"]
    print(client, DB)
    app.run(
        host="0.0.0.0",
        port=80,
        #ssl_context=("certs/cert.pem", "certs/privkey.pem"),
    )


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


# @app.route("/login", methods=["GET", "POST"])
# def login():
#     """Invites users to login or click a button
#     to go to the account registration page."""
#     if request.method == "GET":
#         return render_template("login.html")
#     if request.method == "POST":
#         username = request.form.get("username")
#         password = request.form.get("password")
#         if not username or not password:
#             abort(400, "Missing username or password")  # bad request
#         user = DB.users.find_one({"username": username})
#         if user and Hasher.verify(user["pwhash"], password):
#             login_user(User(username, user["pwhash"]))
#             return redirect("/")
#         elif not user:
#             abort(401, "User not found")
#         else:
#             abort(401, "Incorrect password")
@app.route("/login", methods=["GET", "POST"])
def login():
    """Invites users to login or click a button
    to go to the account registration page."""
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username_in_form = request.form.get("username")
        password_in_form = request.form.get("password")
        if not username_in_form or not password_in_form:
            abort(400, "Missing username or password")  # bad request
        user_found = DB.users.find_one({"username": username_in_form})
        try:
            if user_found and Hasher.verify(user_found["pwhash"], password_in_form):
                login_user(User(username_in_form, user_found["pwhash"]))
                return redirect("/")
            elif not user_found:
                abort(401, "User not found")
            else:
                abort(500, "Unknown error")
        except argon2.exceptions.VerifyMismatchError:
            abort(401, "Incorrect password")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Accessible from index.html.
    Allows users to change their password."""
    if request.method == "GET":
        return render_template("change_password.html")
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        if not old_password or not new_password:
            abort(400, "Missing old or new password")
        try:
            Hasher.verify(current_user.pwhash, old_password)
        except argon2.exceptions.VerifyMismatchError:
            abort(401, "Incorrect password")
        DB.users.update_one(
            {"username": current_user.username},
            {"$set": {"pwhash": Hasher.hash(new_password)}},
        )
        return redirect("/logout")


pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

@app.route("/register", methods=["GET", "POST"])
def register():
    """Accessible from login.html.
    Invites users to register an account."""
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            abort(400, "Missing username or password")
        elif not match(pattern, username):
            abort(400, "Username must be email")
        elif DB.users.find_one({"username": username}):
            abort(409, "Username already taken")
        else:
            DB.users.insert_one({"username": username, "pwhash": Hasher.hash(password)})
            return redirect("/login")


@app.route("/logout")
@login_required
def logout():
    """Accessible from index.html.
    Logs out the user."""
    logout_user()
    return redirect("/login")

@app.route("/")
@login_required
def index():
    """Homepage, gives options to choose a plan/draft or create a new plan"""
    # Find all plans with the flag "delete_me" set to True (cleans up interrupted sessions)
    DB.plans.delete_many({"username": current_user.username, "delete_me": True})
    params = {"username": current_user.username}
    params["plans"] = list(DB.plans.find(
        {"username": current_user.username, "draft": False}
    ).sort("created", -1))
    params["drafts"] = list(DB.plans.find(
        {"username": current_user.username, "draft": True}
    ).sort("created", -1))
    for plan_type in ("plans", "drafts"):
        for plan in params[plan_type]:
            plan["id"] = oidtob62(plan["_id"])
    return render_template("index.html", **params)


@app.route("/plan/<plan_id>")
@login_required
def view_plan(plan_id):
    """Accessible from index.html, or after certain actions.
    Views a plan if possible
    If plan is a draft, a button to edit the draft is shown.
    If plan is a draft, unlocked, or reached the unlock time, show a delete button."""
    plan = DB.plans.find_one({"_id": b62tooid(plan_id)})    
    if not plan:
        abort(404, "Plan not found")
    plan["id"] = plan_id
    if plan["private"] and plan["username"] != current_user.username:
        abort(403, "Plan is private")
    if plan["locked"] and datetime.datetime.now() < plan["unlock_at"]:
        unlock_time = plan["unlock_at"].strftime("%Y-%m-%d %H:%M:%S")
        plan["content"] = f"This plan is locked until {unlock_time}"
    return render_template("plan.html", **plan)

@app.route("/delete_plan/<plan_id>")
@login_required
def delete_plan(plan_id):
    """Delete a plan."""
    plan = DB.plans.find_one({"_id": b62tooid(plan_id)})
    if not plan:
        abort(404, "Plan not found")
    plan["id"] = plan_id
    if plan["username"] != current_user.username:
        abort(403, "You do not own this plan")
    if plan["draft"] or not plan["locked"] or (plan["locked"] and
        datetime.datetime.now() > plan["unlock_at"]):
        # Plan is eligible for deletion
        DB.plans.delete_one({"_id": b62tooid(plan_id)})
    return redirect("/")

@app.route("/create_plan", methods=["GET"])
@login_required
def create_plan():
    """Accessible from index.html.
    Page to create a new plan."""
    if request.method == "GET":
        return render_template("create_plan.html")

@app.route("/edit_plan/<plan_id>")
@login_required
def edit_plan(plan_id):
    """Accessible from plan.html.
    Edit a draft plan."""
    plan = DB.plans.find_one({"_id": b62tooid(plan_id)})
    if not plan:
        abort(404, "Plan not found")
    plan["id"] = plan_id
    if plan["username"] != current_user.username:
        abort(403, "You do not own this plan")
    if not plan["draft"]:
        abort(400, "This is not a draft plan")
    return render_template("edit_plan.html", **plan)

@app.route("/save_draft", methods=["POST"])
@login_required
def save_draft():
    """Updates existing draft with new draft data (does not create new one).
    Reached from edit_plan.html"""
    name = request.form.get("name")
    content = request.form.get("content")
    if not name:
        abort(400, "Missing name")
    if not content:
        abort(400, "Missing content")
    DB.plans.update_one(
        {"_id": b62tooid(request.form.get("id"))},
        {"$set": {"name": name, "content": content}},
    )
    return redirect("/")

@app.route("/finalize_draft", methods=["POST"])
@login_required
def finalize_draft():
    """Accessible via "save as file" button on edit_plan.html.
    Turns a draft into a published plan. Creation time is set when finalized."""
    name = request.form.get("name")
    content = request.form.get("content")
    if not name:
        abort(400, "Missing name")
    if not content:
        abort(400, "Missing content")
    DB.plans.update_one(
        {"_id": b62tooid(request.form.get("id"))},
        {"$set": {"name": name, "content": content}},
    )
    return redirect(f"/settings/{request.form.get('id')}")

@app.route("/submit_plan", methods=["POST"])
@login_required
def submit_plan():
    """Accessible via "save as file" button on create_plan.html.
    Submit plan and redirect to settings of plan."""
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
                "created": datetime.datetime.now(),
                "draft": True,
                "locked": False,
                "private": False,
                "delete_me": False,
            }
        ).inserted_id
        return redirect(f"/plan/{oidtob62(oid)}")
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
    plan["id"] = plan_id
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
            DB.plans.update_one(
                {"_id": b62tooid(plan_id)},
                {"$set": {
                    "locked": False, 
                    "delete_me": False, 
                    "created": datetime.datetime.now(),
                    "draft": False,
                }},
            )
        return redirect("/")

@app.route("/set_lock/<plan_id>", methods=["GET", "POST"])
@login_required
def set_lock(plan_id):
    """Page to set lock duration."""
    plan = DB.plans.find_one({"_id": b62tooid(plan_id)})
    if not plan:
        abort(404, "Plan not found")
    if plan["username"] != current_user.username:
        abort(403, "You do not own this plan")
    plan["id"] = plan_id
    if request.method == "GET":
        return render_template("set_lock.html", **plan)
    if request.method == "POST":
        # In days
        duration = request.form.get("duration")
        if not duration:
            abort(400, "Missing duration")
        timenow = datetime.datetime.now()
        duration = datetime.timedelta(days=int(duration))
        # Plan is finalized
        DB.plans.update_one(
            {"_id": b62tooid(plan_id)},
            {"$set": {
                "locked": True,
                "duration": duration.days,
                "created": timenow,
                "unlock_at": timenow + duration,
                "draft": False,
                "delete_me": False,
            }},
        )
        return redirect("/")

if __name__ == "__main__":
    main()