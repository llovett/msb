import datetime
import functools
import os
import sys

from flask import (
    Flask, render_template, session, request,
    redirect, url_for)
from pymongo_odm.errors import ValidationError

from common import salted_hash
from models import User, Post

# Secret key used to encrypt session cookies.
SECRET_KEY = os.getenv('MSB_SECRET_KEY')


app = Flask(__name__)
app.secret_key = SECRET_KEY


def logged_in(func):
    """Decorator that redirects to login page if a user is not logged in."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper


@logged_in
@app.route('/posts/new', methods=['GET', 'POST'])
def create_post():
    if request.method == 'GET':
        return render_template('new_post.html')
    else:
        print(request.form)
        if request.form['date']:
            post_date = datetime.strptime(request.form['date'], '%m/%d/%y')
        else:
            post_date = datetime.datetime.now()
        try:
            Post(title=request.form['title'],
                 date=post_date,
                 body=request.form['content'],
                 author=session['user']['email']).save()
        except ValidationError as exc:
            return render_template('new_post.html', errors=exc.message)
        return 'Your post has been saved.'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Return login form.
        return render_template('login.html')
    else:
        # Login.
        email, password = request.form['email'], request.form['password']
        logged_in = User.valid_user(email, password)
        if logged_in:
            # Store user in the session.
            session['user'] = logged_in.as_dict()
            return 'Success! Your handle is {}'.format(logged_in.handle)
        else:
            return render_template(
                'login.html', error='Bad email or password.')


@app.route('/')
def index():
    return render_template('index.html', posts=Post.objects.all())


def create_user(email, handle, password):
    # Hash and salt the password.
    password = salted_hash(password)
    User(email=email, handle=handle, password=password).save(force_insert=True)


def main():
    # If run with arguments, create a user.
    if len(sys.argv) > 1:
        try:
            # TODO: python 3.
            email, handle, password = map(unicode, sys.argv[1:])
        except ValueError:
            print('USAGE: python main.py <email> <handle> <password>')
        else:
            # Could raise an Exception.
            create_user(email, handle, password)
    # Otherwise run application in debug mode.
    else:
        app.run(debug=True)


if __name__ == '__main__':
    main()
