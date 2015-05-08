from flask import Flask, request, url_for
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
                htmresp = make_response("you are logged in!")
                htmresp.set_cookie('session',session_id,expires=expiration)
                htmresp.set_cookie('user',user)
                return htmresp
            else:
                raise ValueError('Invalid username or password')
            #request.form['password'] not in 

def verify_session(request_obj):
    return ('testuser',True)

def add_prediction():
    pass

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

# obviously have to fix this later
@app.route('/new',methods=['GET','POST'])
def new_prediction():
    username, session_ok = verify_session(request)
    if not session_ok:
        return redirect(url_for('login_page'))
    # add some javascript to verify/automake the upload date
    if request.method == 'POST':
        if request.form['statement'] != u'':
            with conn.cursor() as cur:
                cur.execute("""insert into predictions (created_by,
                    datecreated, statement, smalltext) values
                    ((SELECT id FROM users WHERE username = %s)
                        , %s, %s, %s)""",
                    (   username,
                        datetime.utcnow(),
                        request.form['statement'],
                        request.form['smalltext']))
                try:
                    date = datetime.strptime(
                            request.form['expectresolved'], "%Y-%m-%d")
                except ValueError:
                    date = timedelta(days=7) + datetime.utcnow()

                cur.execute("""update predictions set expectresolved = %s where
                                statement = %s""",
                            (date, request.form['statement']))
        return redirect(url_for('index'))
    #try moving to the add_prediction whatever.

# need to find someway to autocreate
# teh first bet, no?

    session = request.cookies.get('session')
    if not session:
        return redirect(url_for('login_page'))
    else:
        return render_template("new_predict.html")

@app.route('/login', methods=['GET','POST'])
def login_page():
    error = None
    nextlink = get_redirect_target()
    if request.method == 'POST':
        try:
            resp = login(request.form['username'],request.form['password'])
            conn.commit()
            return redirect(nextlink)
        except ValueError as e:
            return str(e)
    return '''<form action="/login" method="POST">
        username: <input type="text" name="username" value="%s"><br />
        password: <input type="password" name="password"><br />
        <input type="hidden" name="next" value={{ next or ''}}>
        <input type="submit" value="Submit"></form>''' % (request.cookies.get('username'))

def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netlocapp.route('/logout')

@app.route('/logout')
def logout():
    session = request.cookies.get('session')
    if session:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions where session_id = %s",
                    (session,))
    return "you are logged out!"

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
        resp = tester.get("/logout")
        assert resp.status_code == 200
        assert "you are logged out!"

        



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
