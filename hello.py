from flask import Flask, request, url_for, render_template
from flask import make_response, redirect
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from uuid import uuid4
import json
import psycopg2
from urlparse import urlparse, urljoin

with open("postgres_auth", 'r') as reader:
    auth = json.load(reader)
conn = psycopg2.connect(**auth)

app = Flask(__name__)

"""Takes a username and a password string, returns a Tuple:
        SessionID, NotificationString
    Session is null on error.
"""

def new_session(user, password):
    with conn.cursor() as cur:
        cur.execute("""SELECT password FROM users
                WHERE username=%s""",
                (user,))
        query = cur.fetchone()
        if query is None:
            return (None, 'Invalid username or password')
        else:
            if bcrypt.verify(password,query[0]):
                session_id = str(uuid4())
                cur.execute("""INSERT
                        INTO sessions (id, login)
                        VALUES (%s, (
                            SELECT id
                            FROM users
                            WHERE username=%s))""",
                    (session_id, user))
                conn.commit()
                return (session_id, "%s is logged in!" % (user,))
            else:
                return (None, 'Invalid username or password')

"""Takes a dict with username and sessionID string, returns a Tuple:
        Username, DescriptionString
    If session not valid, username is null
"""
def verify_session(cookie):
    user = cookie.get('user')
    session = cookie.get('session')
    print user," ", session

    if (user == None) or (session == None):
        return (None,"Cookie contains no valid session")

    with conn.cursor() as cur:
        cur.execute("""SELECT users.username
                FROM sessions JOIN users
                ON sessions.login = users.id
                WHERE sessions.id = %s""",
                (session,))
        query = cur.fetchone()
        if query is None:
            return (None, 'User session invalid')
        elif query[0] != user:
            return (None, 'User session is invalid')
        else:
            return (user, '%s is logged in!' % (user,))

def add_prediction():
    pass

@app.route('/predictions', methods=['GET', 'POST'])
def getpredictions():
    if request.method == 'POST':
        return "How did you even get here? SHOO."
    user, string = verify_session(request.cookies)
    if user == None:
        return string
    else:
        with conn.cursor() as cur:
            cur.execute("""SELECT array_to_json(array_agg(row_to_json(t)))
                FROM (
                    SELECT statement,
                           smalltext,
                           created
                    FROM predictions JOIN users
                        ON users.id = predictions.created_by
                    WHERE users.username = %s
                    ) t""", (user,))
            query = cur.fetchone()[0]
            query = json.dumps(query)
        return query


# self-explanatory, it tunes the app to accept the '/' address
# it looks like it just takes the next definitions to be the related function.
@app.route('/')
def index():
    return render_template("predictions.html")

# # obviously have to fix this later
# @app.route('/new',methods=['GET','POST'])
# def new_prediction():
#      = verify_session(request)
#     if not session_ok:
#         return redirect(url_for('login_page'))
#     # add some javascript to verify/automake the upload date
#     if request.method == 'POST':
#         if request.form['statement'] != u'':
#             with conn.cursor() as cur:
#                 cur.execute("""insert into predictions (created_by,
#                     datecreated, statement, smalltext) values
#                     ((SELECT id FROM users WHERE username = %s)
#                         , %s, %s, %s)""",
#                     (   username,
#                         datetime.utcnow(),
#                         request.form['statement'],
#                         request.form['smalltext']))
#                 try:
#                     date = datetime.strptime(
#                             request.form['expectresolved'], "%Y-%m-%d")
#                 except ValueError:
#                     date = timedelta(days=7) + datetime.utcnow()
# 
#                 cur.execute("""update predictions set expectresolved = %s where
#                                 statement = %s""",
#                             (date, request.form['statement']))
#         return redirect(url_for('index'))
#     #try moving to the add_prediction whatever.

# need to find someway to autocreate
# teh first bet, no?

#     session = request.cookies.get('session')
#     if not session:
#         return redirect(url_for('login_page'))
#     else:
#         return render_template("new_predict.html")

@app.route('/login', methods=['GET','POST'])
def login_page():
    if request.method == 'POST':
        session, resultstr = new_session(request.form['username'],request.form['password'])
        if session == None:
            return render_template("login.html", msg=resultstr)
        expiration = timedelta(minutes=20) + datetime.utcnow()
        htmresp = make_response(render_template('login.html',msg=resultstr))
        htmresp.set_cookie('session',session,expires=expiration)
        htmresp.set_cookie('user',request.form['username'])
        return htmresp
    return render_template("login.html")

@app.route('/logout')
def logout():
    session = request.cookies.get('session')
    if session != None:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions where id = %s",
                    (session,))
    return render_template("login.html",msg='You are logged out!')

# -------
# ------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
    conn.commit()
    conn.close()

def test_login():
    with app.test_client() as tester:
        resp = tester.post("/login",
            data=dict(
                username="testuser",
                password="pass1"),
            follow_redirects=True)

        assert resp.status_code == 200
        assert "you are logged in!" in resp.get_data() 
        resp = tester.post("/login",
            data=dict(
                username="notauser",
                password=""),
            follow_redirects=True)
        assert resp.status_code == 200
        assert 'Invalid username or password' in resp.get_data()
        resp = tester.post("/login",
            data=dict(
                username="testuser",
                password="wrong pass"),
            follow_redirects=True)
        assert resp.status_code == 200
        assert 'Invalid username or password' in resp.get_data()
        resp = tester.get("/logout")
        assert resp.status_code == 200
        assert "you are logged out!" in resp.get_data()


def test_newpred():
    with app.test_client() as tester:
        resp = tester.post("/login",
            data=dict(
                username="testuser",
                password="pass1"),
            follow_redirects=True)
        assert resp.status_code == 200
        from random import randint
        randtext="test input " + str(randint(-99999,99999))
        resp = tester.post("/new",
            data=dict(
                statement=randtext,
                smalltext="",
                expecteddate="2015-12-25"),
            follow_redirects=True)
        assert resp.status_code == 200
        assert randtext in resp.get_data()



# make sure the table kicks out old sessions regularlike
# use the login page to create a session
    # write test for test user session
# use prediction page to make new prediction
    # write test for new prediction
    # note: give predictions privacy levels
    # me only, logged-in only, link only, public
# make a predictions display page
    # write test for display page
# make a new bet page
# link predictions display to bets option
    # write test for bets page
# make a new bet with new bet page
    # write test for new bet


# new user page
# user profile page
# home page queries for highest thing
# graphs page
# -------
# to get static files in dev, make a static folder
# and reference static in a url_for
# print "static file url: " + url_for('static', filename='example.txt')
# TODO: make this work

# -------

# interesting... just this simple little script tries to load 
# /favicon.ico HTTP/1.1

#
# If you have debug disabled or trust the users on your network, you can make
# the server publicly available simply by changing the call of the run() method
# to look like this:
#     app.run(host='0.0.0.0')
# "

