# all the imports
#import sqlite3
import datetime
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify

from pymongo import Connection

from bson.json_util import dumps
from bson.objectid import ObjectId

# configuration
# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
  return Connection().NBDatabase

def init_db():
  '''
  create collections:
    users: id ID location {latitude longitude}
    questions: id title detail tag user date location {latitude longitude}
    answers: id question username content date rate
  '''
  pass

def get_location():
  return (int(request.args.get('latitude',110)), int(request.args.get('longitude',38)))


def update_user(username,latitude,longitude):
  user = g.db.users.find_one({"ID": username})
  if user == None:
    user = {"ID": username,"location":[latitude,longitude]}
    print(user)
    g.db.users.insert(user)
    print(user)
  else:
    user["location"] = [latitude,longitude]

@app.before_request
def before_request():
  g.db = connect_db()

@app.route('/')
def index():
  print url_for("questions")
  return redirect(url_for("questions"))

@app.route('/questions')
def questions():
  lat,lon = get_location()
  entries = g.db.questions.find({"location": {"$near": [lat,lon]}}).limit(10)
  r = dumps(entries)
  return r

@app.route('/users')
def list_users():
  lat,lon = get_location()
  users = g.db.users.find({"location": {"$near":[lat,lon]}}).limit(10)
  return dumps(users)

@app.route('/adduser', methods=['POST'])
def add_user():
  #if not session.get('logged_in'):
  #    abort(401)
  username = request.form["username"]
  lat = int(request.form["latitude"])
  lon = int(request.form["longitude"])
  update_user(username,latitude,longitude)
  #flash('New entry was successfully posted')
  return redirect(url_for('list_users',latitude=lat,longitude=lon))


@app.route('/q/<question_id>')
def get_question(question_id):
  q = g.db.questions.find_one({"_id": ObjectId(question_id)})
  if q == None:
    abort(404)
  else:
    answers = g.db.answers.find({"question": question_id}).sort("rate")
    r = {
        "question": q,
        "answers": answers
        }
    return dumps(r)

@app.route('/ask', methods=['POST'])
def post_question():
  fields = ["username","title","detail","tag"]
  question = {}
  for field in fields:
    question[field] = request.form[field]
  print question
  question["date"] = datetime.datetime.now()
  question["location"] = [int(request.form["latitude"]), int(request.form["longitude"])]
  print question
  question_id = g.db.questions.insert(question)
  return dumps({"status":"ok","question_id": str(question_id)})

@app.route('/reply/<question_id>', methods=['POST'])
def reply(question_id):
  q = g.db.questions.find_one({"_id": ObjectId(question_id)})
  if q == None:
    abort(404)
  username = request.form['username']
  content = request.form['content']
  date = datetime.datetime.now()
  rate = 0
  answer = {
      "username":username,
      "question":question_id,
      "date": date,
      "rate": rate,
      "content": content
      }
  answer_id = g.db.answers.insert(answer)
  return dumps({"status":"ok","answer_id": str(answer_id)})

@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  if request.method == 'POST':
    if request.form['username'] != app.config['USERNAME']:
        error = 'Invalid username'
    elif request.form['password'] != app.config['PASSWORD']:
        error = 'Invalid password'
    else:
      session['logged_in'] = True
      flash('You were logged in')
      return redirect(url_for('show_entries'))
  return render_template('login.html', error=error)

@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  flash('You were logged out')
  return redirect(url_for('questions'))

if __name__ == "__main__":
  app.debug = True
  app.run(host='0.0.0.0')
