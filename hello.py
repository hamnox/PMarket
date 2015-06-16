from flask import Flask, request, url_for, render_template
from flask import make_response, redirect
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from uuid import uuid4
import simplejson as json
import psycopg2
from urlparse import urlparse, urljoin
# from flask_sslify import SSLify

with open("postgres_auth", 'r') as reader:
    auth = json.load(reader)
conn = psycopg2.connect(**auth)

app = Flask(__name__)
# sslify = SSLify(app)

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
    return (None, 'How did you even get this result?')

@app.route('/predictions',methods=['GET'])
def get_predictions():
    if request.method == 'POST':
        return "How did you even get here? SHOO."
    user, string = verify_session(request.cookies)
    if user == None:
        return string
    else:
        with conn.cursor() as cur:
            cur.execute("""
                    SELECT statement,
                           smalltext,
                           username,
                           bet_users,
                           bet_credence
                    FROM predictions JOIN users
                        on users.id = predictions.created_by
                        LEFT JOIN ( SELECT max(bets.prediction) as bet_pred,
                                array_agg(users.username) as bet_users,
                                array_agg(bets.credence) as bet_credence,
                                    array_agg(bets.created::varchar) as bet_dates
                            FROM bets JOIN users
                            ON bets.created_by = users.id
                            GROUP BY bets.prediction
                            ORDER BY bet_credence) as bet_agger
                        ON bet_pred = predictions.id
                    WHERE users.username = %s
                        OR predictions.private != true
                    """, (user,))
            # someday, deal with datetime strings on our end
            query = [["Statement", "Description","Created By","Bets"]]
            result = list(cur.fetchall())
            for i, row in enumerate(result):
                result[i] = list(row)
                if result[i][3] is None:
                    pass
                else:
                    result[i][3] = zip(row[3],row[4])
                result[i].pop(4)
            query.extend(result)
            query = json.dumps(query)
        return query

@app.route('/', methods=['GET','POST'])
@app.route('/api/1/', methods=['GET','POST'])
def predplusbets():
    user, string = verify_session(request.cookies)
    if user == None:
        return render_template("login.html",msg=string)
    else:
        with conn.cursor() as cur:
            cur.execute("""
                    SELECT statement,
                           smalltext,
                           username,
                           predictions.id,
                           predictions.created
                    FROM predictions JOIN users
                        on users.id = predictions.created_by
                    WHERE users.username = %s
                        OR predictions.private != true
                    """, (user,))
            pd_table = {'header': ['Statement',
                                    'Description',
                                    'Created By',
                                    'Bets',
                                    'Created'],
                        'body': list(cur.fetchall())}

        return render_template('pd.html',
                pd_table=pd_table,
                submit_url=url_for('bets_page'),
                submit_type="POST",
                submit_col=4)


@app.route('/pd_bets', methods=['POST'])
def bets_page():
    user, string = verify_session(request.cookies)
    if user == None:
        return render_template("login.html",msg=string)
    else:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT resolved, private,
                        username,
                        statement,
                        smalltext,
                        created, due,
                        result
                FROM predictions JOIN users
                    ON users.id = predictions.created_by
                WHERE predictions.id = %s""",
                (int(request.form["Bets"]),))

            result = cur.fetchone()
            (pd_resolved, pd_privacy, pd_user, pd_statement) = result[0:4]
            if pd_user != user and pd_privacy:
                abort(401)

            prefix = """Prediction: %s<br />
                Created By: %s<br />""" % (pd_user, pd_statement)

            (pd_desc, pd_created, pd_due, pd_result) = result[4:]
            if pd_created is not None:
                prefix = prefix + "Created: " + str(pd_created) + "<br />"
            if pd_desc is not None:
                if pd_desc != "":
                    prefix = prefix + "Description: " + str(pd_desc) +"<br />"

            cur.execute("""
                SELECT  users.username,
                        bets.credence,
                        bets.created
                FROM bets JOIN users
                ON bets.created_by = users.id
                WHERE bets.prediction = %s""",
                (int(request.form["Bets"]),))

            pd_table = {'header': ['User',
                                    'Bet',
                                    'Bet Date'],
                        'body': list(cur.fetchall())}

            if pd_resolved:
                prefix = prefix + "Completed " + str(pd_resolved) + "<br />"
                prefix = prefix + "Result: " + str(pd_result) +".<br />"
                postfix = "Market Closed."
            else:
                if pd_due is not None:
                    prefix = prefix + "Resolution Due: " + str(pd_due) + "<br />"
                postfix="""<br /><div id="bet_submit"><form action=%s method="POST">
                        Credence: <input type="text" name="credence">
                        <input type="submit"></form></div>
                        """ % url_for('bets_page')

            if not pd_privacy:
                prefix = prefix + "<br />This prediction is public.</br >"
            prefix = prefix + "<br />"


        return render_template('pd.html',
                display_title=pd_statement,
                pd_table=pd_table,
                prefix=prefix,
                postfix=postfix)

@app.route('/addbets',methods=['POST'])
def add_bet():
    pass


@app.route('/bets', methods=['GET'])
def get_bets():
    if request.method == 'POST':
        return "How did you even get here? SHOO."
    user, string = verify_session(request.cookies)
    if user == None:
        return string
    else:
        with conn.cursor() as cur:
            cur.execute("""
                    SELECT max(pd.statement),
                            max(pd.username),
                            array_agg(users.username),
                            array_agg(bets.credence)
                    FROM bets JOIN users
                        ON bets.created_by = users.id
                        JOIN (
                            SELECT predictions.id,
                                statement, username
                            FROM predictions
                            JOIN users
                            ON created_by = users.id
                            ) pd
                        ON bets.prediction = pd.id
                    WHERE bets.prediction in (
                        SELECT bets.prediction
                        FROM bets JOIN users
                        ON bets.created_by = users.id
                        WHERE users.username = %s
                            )
                    GROUP BY bets.prediction
                    """, (user,))
            query = [["Statement","Created By","Bets"]]
            result = list(cur.fetchall())
            for i, row in enumerate(result):
                result[i] = list(row)
                if result[i][2] is None:
                    pass
                else:
                    result[i][2] = zip(row[2],row[3])
                result[i].pop(3)
            query.extend(result)
            query = json.dumps(query)
        return query

@app.route('/new',methods=['GET','POST'])
def add_prediction():
    #TODO: privacy checkbox
    if request.method == 'POST':
        user, string = verify_session(request.cookies)
        if user == None:
            return 'Error'

        with conn.cursor() as cur:
            try:
                date = datetime.strptime(
                        request.form['expectresolved'], "%Y-%m-%d")
            except ValueError as e:
                return 'Error'

            cur.execute("""insert into
                    predictions (created_by,
                        statement, smalltext, due)
                    values ((
                        SELECT id
                        FROM users
                        WHERE username = %s)
                    , %s, %s, %s)""",
                  #  RETURNING predictions.id""",
                (user,
                request.form['statement'],
                request.form['smalltext'], date))
            return 'Valid'
    else:
        user, string = verify_session(request.cookies)
        if user == None:
            return render_template("login.html",msg=string)
        else:
            return render_template("new_predict.html")

    #try moving to the add_prediction whatever.

# need to find someway to autocreate
# teh first bet, no?

@app.route('/login', methods=['GET','POST'])
def login_page():
    if request.method == 'POST':
        session, resultstr = new_session(request.form['username'],request.form['password'])
        if session == None:
            prevsession = request.cookies.get('session')
            if prevsession != None:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM sessions where id = %s",
                            (prevsession,))
            return render_template("login.html", msg=resultstr)
        expiration = timedelta(minutes=60) + datetime.utcnow()
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

# ------------------------------
def on_exit():
    conn.commit()
    conn.close()

import atexit
atexit.register(on_exit)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)




def test_login():
    with app.test_client() as tester:
        resp = tester.post("/login",
            data=dict(
                username="testuser",
                password="pass1"))
        assert resp.status_code == 200
        assert "testuser is logged in!" in resp.get_data()

        resp = tester.post("/login",
            data=dict(
                username="notauser",
                password=""))
        assert resp.status_code == 200
        assert 'Invalid username or password' in resp.get_data()

        resp = tester.post("/login",
            data=dict(
                username="testuser",
                password="wrong pass"))
        assert resp.status_code == 200
        assert 'Invalid username or password' in resp.get_data()

        resp = tester.get("/logout")
        assert resp.status_code == 200
        assert "You are logged out!" in resp.get_data()


def test_newpred():
    with app.test_client() as tester:
        resp = tester.post("/login",
            data=dict(
                username="testuser",
                password="pass1"))
        assert resp.status_code == 200

        from random import randint
        randtext="test input " + str(randint(-99999,99999))
        resp = tester.post("/new",
            data=dict(
                statement=randtext,
                smalltext="",
                expectresolved="2015-12-25"),
            follow_redirects=True)
        assert resp.status_code == 200
        assert "User Predictions" in resp.get_data()

        resp = tester.get("/predictions")
        assert resp.status_code == 200
        assert randtext in resp.get_data()

def test_bets():
    assert false

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

