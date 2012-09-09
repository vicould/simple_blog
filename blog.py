"""
This app implements a fully functional blog, giving access to a collection of
pages and individual entries, but also to a way to post new entries.
"""
from flask import abort
from flask import flash
from flask import Flask
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

import bcrypt
from contextlib import closing
import datetime
import json
import sqlite3

from blog_exceptions import DatabaseException

# configuration
DATABASE = 'entries.db'
DEBUG = True
SECRET_KEY = (
'secret mon cul'
)

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


@app.errorhandler(401)
def not_authorized(error):
    """Handles the 401"""
    return (
            render_template(
                '401.html',
                error=error,
                logged_in=session.get('logged_in')
                ),
            401
            )


@app.errorhandler(404)
def page_not_found(error):
    """Handles the 404"""
    return (
            render_template(
                '404.html',
                error=error,
                logged_in=session.get('logged_in')
                ),
            404
            )


@app.route('/')
def list_articles():
    """Basic root view, showing all the articles for the blog"""
    cursor = g.db.execute(
            'select id, title, date_posted, content, cat_name from articles'
            ' order by date_posted desc'
            )
    articles = [
            prepare_article_excerpt(article)
            for article in cursor.fetchall()
            ]
    return render_template(
            'home.html',
            articles=articles,
            logged_in=session.get('logged_in')
            )


@app.route('/login/', methods=['GET', 'POST'])
def login():
    """View allowing the author to login, and modify the content then"""
    if session.get('logged_in'):
        return redirect(url_for('list_articles'))
    form_error = None
    if request.method == 'POST':
        username = request.form.get('username')
        original_hashed_pass = g.db.execute(
                'select hash from authors where name = ?',
                (username,)
                ).fetchone()
        if original_hashed_pass:
            original_hashed_pass = original_hashed_pass[0]
            password = request.form.get('password')
            if (bcrypt.hashpw(password, original_hashed_pass) ==
                    original_hashed_pass):
                session['logged_in'] = True
                return redirect(url_for('list_articles'))
        app.logger.info('bad credentials')
        form_error = 'Wrong username or password'
    return render_template(
            'login.html',
            form_error=form_error,
            logged_in=session.get('logged_in')
            )


@app.route('/logout/', methods=['GET'])
def logout():
    """Logging out the user"""
    if session.get('logged_in'):
        del session['logged_in']
    return redirect(url_for('list_articles'))


def prepare_article_excerpt(article_instance):
    """
    Converts a row of the database in a dictionary containing the article
    details for use as an excerpt in the templates.
    The article is truncated.
    """
    return {
            'id': article_instance[0],
            'title': article_instance[1],
            'date_posted': article_instance[2],
            'readable_date': datetime.datetime.strptime(
                article_instance[2], '%Y-%m-%d %H:%M:%S'
                ).strftime('%B %d, %Y'),
            'content': ' '.join(article_instance[3].split(' ', 30)[:30]),
            'category': article_instance[4]
            }


def prepare_article_full(article_instance):
    """
    Converts a row of the database in a dictionary containing the articles
    details for use in the templates as full article.
    """
    return {
            'id': article_instance[0],
            'title': article_instance[1],
            'date_posted': article_instance[2],
            'readable_date': datetime.datetime.strptime(
                article_instance[2], '%Y-%m-%d %H:%M:%S'
                ).strftime('%B %d, %Y'),
            'content': article_instance[3],
            'category': article_instance[4]
            }


def save_category(category_name):
    """
    Saves a category to the database.
    Raises an exception if the category failed to be saved.
    """
    g.db.execute(
            'insert into categories (\'name\') values (?)',
            (category_name,)
            )
    g.db.commit()

    category_instance = g.db.execute(
            'select name from categories where name = ?',
            (category_name,)
            ).fetchone()
    if not category_instance:
        # error, the category could not be saved
        error_message = (
                'Failed to create category,'
                ' something is wrong with the database'
                )
        app.logger.error(error_message)
        app.logger.error('Saving category %s failed', category_name)
        raise DatabaseException(error_message)


def save_article(title, content, category_name):
    """
    Saves an article in the database, and returns its id.
    Raises an exception if the article failed to be saved.
    """
    date_posted = datetime.datetime.utcnow().strftime(
            '%Y-%m-%d %H:%M:%S'
            )
    g.db.execute(
            'insert into articles'
            ' (title, content, cat_name, date_posted)'
            ' values (?, ?, ?, ?)',
            (title, content, category_name, date_posted)
            )
    g.db.commit()
    article_instance = g.db.execute(
            'select id from articles where title = ?',
            (title,)
            ).fetchone()
    if not article_instance:
        error_message = 'Unable to save the post to the database'
        app.logger.error(error_message)
        app.logger.error('The title was %s', title)
        raise DatabaseException(error_message)

    return article_instance[0]



@app.route('/entries/new/', methods=['GET', 'POST'])
def add_article():
    """View to create a new entry"""
    if not session.get('logged_in'):
        return abort(401)
    form_errors = {}
    article = None
    if request.method == 'POST':
        # goes through the form to create a new entry, after validation
        title = request.form.get('title', None)
        category = request.form.get('category', None)
        content = request.form.get('content', None)
        if not title:
            form_errors['title'] = 'Please fill the title'
        if not category:
            category = request.form.get('new_category', None)
            try:
                save_category(category)
            except sqlite3.IntegrityError:
                # the category is already present in the db, nothing to change
                # then
                pass
            if not category:
                form_errors['category'] = 'Please fill the category'
        if not content:
            form_errors['content'] = 'Please write your article!'
        if not form_errors:
            try:
                article_id = save_article(title, content, category)
                return redirect(url_for('view_article', article_id=article_id))
            except DatabaseException as exc:
                flash(exc.message)
        article = {
                'title': title,
                'content': content,
                'category': category
                }

    cursor = g.db.execute('select name from categories')
    categories = [category_row[0] for category_row in cursor.fetchall()]
    return render_template('article_edition.html',
            article=article,
            categories=categories,
            form_errors=form_errors,
            logged_in=session.get('logged_in')
            )


@app.route('/entries/<int:article_id>/')
def view_article(article_id):
    """View to read an article"""
    cursor = g.db.execute(
            'select id, title, date_posted, content, cat_name'
            ' from articles where id = ?',
            (article_id,)
            )
    article = cursor.fetchone()
    if not article:
        # no matching article in the db, 404
        abort(404)
    else:
        article_detail = prepare_article_full(article)
        return render_template(
                'article.html',
                article=article_detail,
                logged_in=session.get('logged_in')
                )


@app.route('/entries/<int:article_id>/edit/', methods=['GET', 'POST'])
def edit_article(article_id):
    """View to edit an article"""
    if not session.get('logged_in'):
        abort(401)
    cursor = g.db.execute(
            'select date_posted from articles where id = ?',
            (article_id,)
            )
    article = cursor.fetchone()
    if not article:
        # no matching article in the db, 404
        abort(404)
    form_errors = {}
    if request.method == 'POST':
        title = request.form.get('title', None)
        category = request.form.get('category', None)
        content = request.form.get('content', None)
        if not title:
            form_errors['title'] = 'Please fill the title'
        if not category:
            category = request.form.get('new_category', None)
            try:
                save_category(category)
            except sqlite3.IntegrityError:
                # the category is already present in the db, nothing to change
                # then
                pass
            if not category:
                form_errors['category'] = 'Please fill the category'
        if not content:
            form_errors['content'] = 'Please write your article!'
        if not form_errors:
            g.db.execute(
                    'update articles set title = ?, content = ?, cat_name = ?'
                    ' where id = ?',
                    (title, content, category, article_id)
                    )
            g.db.commit()
            return redirect(url_for('view_article', article_id=article_id))
        article_detail = prepare_article_full(
                (article_id, title, article[0], content, category)
                )
    else:
        cursor = g.db.execute(
                'select id, title, date_posted, content, cat_name'
                ' from articles where id = ?',
                (article_id,)
                )
        article = cursor.fetchone()
        article_detail = prepare_article_full(
                article
                )
    cursor = g.db.execute('select name from categories')
    categories = [category_row[0] for category_row in cursor.fetchall()]
    return render_template(
            'article_edition.html',
            article=article_detail,
            categories=categories,
            form_errors=form_errors,
            editing=True,
            logged_in=session.get('logged_in')
            )


@app.route('/categories/')
def list_categories():
    """View to list all categories"""
    cursor = g.db.execute(
            'select name from categories order by name'
            )
    categories = cursor.fetchall()
    per_category_recent_articles = {
            category[0]: [
                prepare_article_excerpt(article)
                for article in g.db.execute(
                    'select id, title, date_posted, content, cat_name'
                    ' from articles where cat_name = ?'
                    ' order by date_posted desc',
                    (category[0],)
                    ).fetchmany(size=2)
                ]
            for category in categories
            }
    return render_template(
            'categories.html',
            categories=per_category_recent_articles,
            logged_in=session.get('logged_in')
            )


@app.route('/categories/new/', methods=['GET', 'POST'])
def add_category():
    """View to create a new category"""
    if not session.get('logged_in'):
        abort(401)
    form_errors = {}
    if request.method == 'POST':
        name = request.form.get('name', '')
        if not name:
            form_errors['name'] = 'Please fill the name of the category'
        if not form_errors:
            try:
                save_category(name)
                return redirect(url_for('list_categories'))
            except DatabaseException as exc:
                flash(exc.message)
            except sqlite3.IntegrityError:
                form_errors['name'] = 'Name already taken'
    return render_template(
            'category_edition.html',
            form_errors=form_errors,
            logged_in=session.get('logged_in')
            )


@app.route('/categories/<category_name>/')
def view_category(category_name):
    """View to list all the articles under that category"""
    category_cursor = g.db.execute(
            'select name from categories where name = ?',
            (category_name,)
            )
    if not category_cursor.fetchall():
        abort(404)
    cursor = g.db.execute(
            'select id, title, date_posted, content, cat_name'
            ' from articles where cat_name = ? '
            'order by date_posted desc',
            (category_name,)
            )
    articles = [
            prepare_article_excerpt(article)
            for article in cursor.fetchall()
            ]

    return render_template(
            'category_articles.html',
            category=category_name,
            articles=articles,
            logged_in=session.get('logged_in')
            )


@app.route('/categories/<category_name>/edit/', methods=['POST'])
def edit_category(category_name):
    """View to edit a specific category"""
    if not session.get('logged_in'):
        abort(401)
    form_errors = {}
    new_name = request.form.get('name', '')
    if new_name == '':
        form_errors['name'] = 'Please fill the name of the category'
        return (
                json.dumps(form_errors),
                400,
                {'Content-type': 'application/json'}
                )
    cat_check = g.db.execute(
            'select name from categories where name = ?',
            (new_name,),
            ).fetchone()
    if cat_check:
        form_errors['duplicate'] = True
        return (
                json.dumps(form_errors),
                409,
                {'Content-type': 'application/json'}
                )
    g.db.execute(
            'update categories set name = ?'
            ' where name = ?',
            (new_name, category_name)
            )
    g.db.execute(
            'update articles set cat_name = ?'
            ' where cat_name = ?',
            (new_name, category_name)
            )
    g.db.commit()
    return (
            json.dumps({
                'new_location': url_for('view_category', category_name=new_name)
                }),
            200,
            {'Content-type': 'application/json'}
            )



if __name__ == '__main__':
    app.run()
