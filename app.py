#!/usr/bin/env python3

import os
import sys
import subprocess
import datetime

from flask import Flask, render_template, request, redirect, url_for, make_response

import logging
from logging.handlers import RotatingFileHandler

# Setup logging


import sentry_sdk
from sentry_sdk.integrations.flask import (
    FlaskIntegration,
)  # delete this if not using sentry.io

# from markupsafe import escape
import pymongo
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# load credentials and configuration options from .env file
# if you do not yet have a file named .env, make one based on the template in env.example
load_dotenv(override=True)  # take environment variables from .env.

# initialize Sentry for help debugging... this requires an account on sentrio.io
# you will need to set the SENTRY_DSN environment variable to the value provided by Sentry
# delete this if not using sentry.io
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    # enable_tracing=True,  # If you need tracing, you can keep this option
    traces_sample_rate=1.0,
    integrations=[FlaskIntegration()],
    send_default_pii=True,
)

# instantiate the app using sentry for debugging
app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['user_data']
def setup_logging():
    # Create a file handler object
    handler = RotatingFileHandler('flask_app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)

    # Create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handlers to the logger
    app.logger.addHandler(handler)

# Call setup_logging in your main function or before starting the app
setup_logging()
class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username


@login_manager.user_loader
def load_user(user_id):
    if user_id in db.list_collection_names():
        user = User(user_id)  # Pass the username to the User object
        return user

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username not in db.list_collection_names():
            db.create_collection(username)
            users_coll = db[username]
            users_coll.insert_one({
                'username': username,
                'password': bcrypt.generate_password_hash(password).decode('utf-8')
            })
            return redirect(url_for('login'))
        else:
            return 'Username already exists!'

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users_coll = db[username]
        user_data = users_coll.find_one({'username': username})
        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user = User(username)  # Pass the username when creating the User object
            login_user(user)
            return redirect(url_for('home'))  # Redirect to the home route after login
        else:
            return 'Invalid username or password!'

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return 'Welcome to the dashboard!'

# # turn on debugging if in development mode
# app.debug = True if os.getenv("FLASK_ENV", "development") == "development" else False

# try to connect to the database, and quit if it doesn't work
try:
    cxn = pymongo.MongoClient(os.getenv("MONGO_URI"))
    db = cxn[os.getenv("MONGO_DBNAME")]  # store a reference to the selected database


    cxn.admin.command("ping")  # The ping command is cheap and does not require auth.
    print(" * Connected to MongoDB!")  # if we get here, the connection worked!
except ConnectionFailure as e:
    print(" * MongoDB connection error:", e)  # debug
    sentry_sdk.capture_exception(e)  # send the error to sentry.io. delete if not using
    sys.exit(1)  # this is a catastrophic error, so no reason to continue to live


# set up the routes
@app.route("/delete_all", methods=["POST"])
def delete_all():
    """
    Route for POST requests to delete all documents from the database collection.
    """
    # Delete all documents from the collection
    db.workouts.delete_many({})

    # Redirect to the read route or any other route as needed
    return redirect(url_for("read"))


@app.route("/")
def home():
    username = current_user.username if current_user.is_authenticated else None
    return render_template('index.html', username=username)




@app.route("/read")
def read():
    docs = db.workouts.find({}).sort("date", pymongo.DESCENDING)
    docs = list(db.workouts.find({}).sort("date", pymongo.DESCENDING))
    app.logger.info(f"Documents fetched: {docs}")
    return render_template("read.html", docs=docs)


# @app.route("/create")
# def create():
#     """
#     Route for GET requests to the create page.
#     Displays a form users can fill out to create a new document.
#     """
#     return render_template("create.html")  # render the create template

@app.route("/read_database")
def read_database():
    # Retrieve all documents from the collection
    docs = db.workouts.find({})
    
    # Print out the contents of each document
    for doc in docs:
        print("Document:", doc)
    return "Check the console for database contents."
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        date = request.form["date"]
        body_part = request.form["body_part"]
        exercise = request.form["exercise"]
        reps = request.form["reps"]
        weight = request.form["weight"]
        print("Date:", date)
        print("Body Part:", body_part)
        print("Exercise:", exercise)
        
        # Check if a document for the day already exists in the database
        workout = db.workouts.find_one({"date": date})

        if workout:
            # Check if the body part already exists in the workouts list
            existing_body_part = db.workouts.find_one({"date": date, "workouts.body_part": body_part})
            if existing_body_part:
                # Check if the exercise already exists for the body part
                existing_exercise = db.workouts.find_one({"date": date, "workouts.body_part": body_part, "workouts.exercises.name": exercise})
                if existing_exercise:
                    # Update the existing exercise with reps and weight
                    db.workouts.update_one(
                        {"date": date, "workouts.body_part": body_part, "workouts.exercises.name": exercise},
                        {"$push": {"workouts.$.exercises.$[elem].sets": {"reps": reps, "weight": weight}}},
                        array_filters=[{"elem.name": exercise}]
                    )
                else:
                    # Create a new exercise with reps and weight
                    db.workouts.update_one(
                        {"date": date, "workouts.body_part": body_part},
                        {"$push": {"workouts.$.exercises": {"name": exercise, "sets": [{"reps": reps, "weight": weight}]}}},
                    )
            else:
                # Create a new body part with the exercise
                db.workouts.update_one(
                    {"date": date},
                    {"$push": {"workouts": {"body_part": body_part, "exercises": [{"name": exercise, "sets": [{"reps": reps, "weight": weight}]}]}}},
                )
        else:
            # Create a new document for the day and insert the exercise
            db.workouts.insert_one({
                "date": date,
                "workouts": [{"body_part": body_part, "exercises": [{"name": exercise, "sets": [{"reps": reps, "weight": weight}]}]}]
            })
        
        return redirect(url_for("read"))
    
    return render_template("create.html")
@app.route("/edit/<mongoid>")
def edit(mongoid):
        doc = db.workouts.find_one({"_id": ObjectId(mongoid)})
        return render_template("edit.html", doc=doc)
    
@app.route("/edit/<mongoid>", methods=["POST"])
def edit_post(mongoid):
    try:
        if request.method == "POST":
            # Extract form data
            date = request.form["date"]
            body_part = request.form["body_part"]
            exercise = request.form["exercise"]
            reps = request.form["reps"]
            weight = request.form["weight"]

            # Update the document in the database
            result = db.workouts.update_one(
                {"_id": ObjectId(mongoid)},
                {
                    "$set": {
                        "date": date,
                        "workouts.0.body_part": body_part,
                        "workouts.0.exercises.0.name": exercise,
                        "workouts.0.exercises.0.sets.0.reps": reps,
                        "workouts.0.exercises.0.sets.0.weight": weight
                    }
                }
            )

            app.logger.info("Update result:", result.raw_result)

            return redirect(url_for("read"))
    except Exception as e:
        app.logger.error("Error in edit_post route:", exc_info=True)
        return str(e), 500


from flask import request

@app.route("/delete/<mongoid>", methods=["POST", "DELETE"])
def delete(mongoid):
    """
    Route for POST and DELETE requests to delete a record from the database.

    Parameters:
    mongoid (str): The MongoDB ObjectId of the record to be deleted.
    """
    if request.method in ["POST", "DELETE"]:
        db.workouts.delete_one({"_id": ObjectId(mongoid)})
        return redirect(url_for("read"))
    else:
        return "Method not allowed", 405


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    GitHub can be configured such that each time a push is made to a repository, GitHub will make a request to a particular web URL... this is called a webhook.
    This function is set up such that if the /webhook route is requested, Python will execute a git pull command from the command line to update this app's codebase.
    You will need to configure your own repository to have a webhook that requests this route in GitHub's settings.
    Note that this webhook does do any verification that the request is coming from GitHub... this should be added in a production environment.
    """
    # run a git pull command
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    pull_output = process.communicate()[0]
    # pull_output = str(pull_output).strip() # remove whitespace
    process = subprocess.Popen(["chmod", "a+x", "flask.cgi"], stdout=subprocess.PIPE)
    chmod_output = process.communicate()[0]
    # send a success response
    response = make_response(f"output: {pull_output}", 200)
    response.mimetype = "text/plain"
    return response


@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template("error.html", error=e)  # render the edit template


# run the app
if __name__ == "__main__":
    # logging.basicConfig(filename="./flask_error.log", level=logging.DEBUG)
    app.run(load_dotenv=True)
