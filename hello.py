from flask import Flask

# using flask.pocoo.org/docs/0.10/quickstart
# alright, first order of business:
# "
# if you are using a single module (as in this example), you should use
# __name__ because depending on if it's started as application or imported as
# module the name will be different ('__main__' versus the actual import name)
# "

app = Flask(__name__)

@app.route('/createuser', methods=[GET])
def createuser(












# self-explanatory, it tunes the app to accept the '/' address
# it looks like it just takes the next definitions to be the related function.
@app.route('/')
def index():
    return 'Index Page'

# -------
@app.route('/hello')

def hello_world():
    return 'Hello World!'

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

@app.route('/login', methods=['GET','POST']) # by default, only GET
def login():
    if request.method == 'POST':
        #do_the_login()
        return 'YOU IS LOGGED IN NOW'
    else:
        #show_the_login_form()
        return 'LOGIN PLZ'


# -------
from flask import url_for

with app.test_request_context(): # wut TODO
    print url_for('index')
#     print url_for('hello', next='/')
    print url_for('show_profile', username='hamnox')
    print url_for('hello', name='John Doe')

# this will build the hardcode URL fors you.
# returns:
# /
# /hello?next=/
# /user/hamnox











# ------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)


# -------
# to get static files in dev, make a static folder
# and reference static in a url_for
print "static file url: " + url_for('static', filename='example.txt')
# TODO: make this work

# -------

# interesting... just this simple little script tries to load 
# /favicon.ico HTTP/1.1

# "
# If you have debug disabled or trust the users on your network, you can make
# the server publicly available simply by changing the call of the run() method
# to look like this:
#     app.run(host='0.0.0.0')
# "
