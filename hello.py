from flask import Flask, request, make_response
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from uuid import uuid4
import json
import psycopg2

with open("postgres_auth", 'r') as reader:
    auth = json.load(reader)
conn = psycopg2.connect(**auth)

# using flask.pocoo.org/docs/0.10/quickstart
# alright, first order of business:
# "
# if you are using a single module (as in this example), you should use
# __name__ because depending on if it's started as application or imported as
# module the name will be different ('__main__' versus the actual import name)
# "

app = Flask(__name__)

# @app.route('/createuser', methods=['GET', 'POST'])
# def newuserpage():
#     if request.method=='GET':            
# #    else:
#             return render_template('newuserpage')
#     # need to make a user making page
#     )
 
@app.route('/predictions', methods=['GET', 'POST'])
def getpredictions():
    if request.method == 'POST':
        return "How did you even get here? SHOO."
    # here want to select by resolved status?
    with conn.cursor() as cur:
#        cur.execute("""SELECT statement, smalltext, datecreated,
#            initial_bet FROM predictions""")
        cur.execute("""SELECT array_to_json(array_agg(row_to_json(t)))
            FROM ( SELECT statement, smalltext, datecreated,
            initial_bet FROM predictions ) t""")
        query = cur.fetchone()[0]
        query = json.dumps(query)
    return query


# self-explanatory, it tunes the app to accept the '/' address
# it looks like it just takes the next definitions to be the related function.
@app.route('/')
def index():
    return render_template("predictions.html")

@app.route('/login', methods=['GET','POST'])
def login_page():
    error = None
    if request.method == 'POST':
        try:
            login(request.form['username'],request.form['password'])
            return "you are logged in!"
        except ValueError as e:
            return str(e)
    return '''
        <form action="/login" method="POST">
        <input type="text" name="username" value="%s"><br />
        <input type="password" name="password"><br />
        <input type="submit" value="Submit"></form>
        ''' % (request.cookies.get('username'))

def login(user, password):
    with conn.cursor() as cur:
        cur.execute("""SELECT password FROM users
                WHERE username=%s""",
                (user,))
        query = cur.fetchone()
        if query is None:
            raise ValueError('Invalid username or password')
        else:
            if bcrypt.verify(password,query[0]):
                session_id = str(uuid4())
                expiration = timedelta(minutes=20) + datetime.utcnow()
                cur.execute("""INSERT INTO sessions (session_id,
                    valid_user, expiration) values (%s, (SELECT id FROM
                    users WHERE username=%s), %s)""",
                    (session_id, user, expiration))
                conn.commit()
                htmresp = make_response(render_template("hello.html"))
                htmresp.set_cookie('session',session_id,expires=expiration)
                htmresp.set_cookie('user',user)
            else:
                raise ValueError('Invalid username or password')
            #request.form['password'] not in 

@app.route('/logout')
def logout():
    pass
# -------
# to render from a template, create a Jinja2 template and put it
# in the 'templates' folder
from flask import render_template
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)
# -------
# wouldn't want to forget variables! stick then in angle brackets

@app.route('/user/<username>')
def show_profile(username):
    return 'User %s' % username

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # make the variable be an int.
    # float and path also work, where path accepts slashes
    return 'Post %d' % post_id


# -------
# from flask import url_for
#
# with app.test_request_context(): # wut TODO
#     print url_for('index')
# #     print url_for('hello', next='/')
#     print url_for('show_profile', username='hamnox')
#     print url_for('hello', name='John Doe')
# 
# this will build the hardcode URL fors you.
# returns:
# /
# /hello?next=/
# /user/hamnox

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

        



# create a test user
    # write test for test user login
# make sure the table kicks out old sessions regularlike
# use the login page to create a session
    # write test for test user session
# make a new prediction page
    # write test for prediction page
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
