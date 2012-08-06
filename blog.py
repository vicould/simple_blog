"""
This app implements a fully functional blog, giving access to a collection of
pages and individual entries, but also to a way to post new entries.
"""
from flask import Flask
from flask import g
from flask import render_template
from flask import request
from flask import session

from contextlib import closing
import datetime
import sqlite3

# configuration
DATABASE = 'entries.db'
DEBUG = True
SECRET_KEY = (
'\x89?P\xda\xedVW)b\x12\xe2H\xb6\xbal\x9c\x90\xaa\x0f\x1d\xa1c\xc4\x1d'
)
USERNAME = 'admin'
PASSWORD = 'Admin0812!'

app = Flask(__name__)
app.config.from_object(__name__)


def init_db():
    """Creates the database"""
    with closing(connect_db()) as database:
        with app.open_resource('schema.sql') as script:
            database.cursor().executescript(script.read())
        database.commit()


def connect_db():
    """Initializes the connection to the database"""
    return sqlite3.connect(app.config['DATABASE'])


@app.before_request
def before_request():
    """Function called before responding to a request"""
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    """Function called after a request is handled, even if there was an
    exception."""
    g.db.close()


@app.route('/')
def list_articles():
    """Basic root view, showing all the articles for the blog"""
    cursor = g.db.execute(
            ''.join([
                'select title, date_posted, content,',
                ' categories.name from articles',
                ' join categories on cat_id = categories.id'
                ])
            )
    articles = [dict(
        title=row[0],
        date_posted=row[1],
        readable_date=datetime.datetime.strptime(
            row[1], '%Y-%m-%d %H:%M:%S'
            ).strftime('%B %d, %Y'),
        content=row[2],
        categories=row[3]
        )
        for row in cursor.fetchall()
        ]
    return render_template('home.html', articles=articles)


@app.route('/entry/add/')
def add_article():
    """View to create a new entry"""
    return ''


@app.route('/entry/<int:article_id>/')
def view_article(article_id):
    """View to read an article"""
    return ''


@app.route('/entry/<int:article_id>/edit/')
def edit_article(article_id):
    """View to edit an article"""
    return ''


@app.route('/category/')
def list_categories():
    """View to list all categories"""
    return ''


@app.route('/category/new/')
def add_category():
    """View to create a new category"""
    return ''


@app.route('/category/<string:category_name/')
def view_category(category_name):
    """View to list all the articles under that category"""
    return ''


@app.route('/category/<string:category_name/edit/')
def edit_category(category_name):
    """View to edit a specific category"""
    return ''


if __name__ == '__main__':
    app.run()

