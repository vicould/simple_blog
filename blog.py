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

from contextlib import closing
import datetime
import sqlite3

from blog_exceptions import DatabaseException

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


@app.errorhandler(404)
def page_not_found(error):
    """Handles the 404"""
    return render_template('404.html', error=error), 404


@app.route('/')
def list_articles():
    """Basic root view, showing all the articles for the blog"""
    cursor = g.db.execute(
            'select title, date_posted, content, cat_name from articles'
            ' order by date_posted'
            )
    articles = [{
        'title': row[0],
        'date_posted': row[1],
        'readable_date': datetime.datetime.strptime(
            row[1], '%Y-%m-%d %H:%M:%S'
            ).strftime('%B %d, %Y'),
        'content': row[2],
        'category': row[3]
        }
        for row in cursor.fetchall()
        ]
    return render_template('home.html', articles=articles)


def prepare_article_detail(article_instance):
    """
    Converts a row of the database in a dictionary containing the articles
    details for use in the templates
    """
    return {
            'title': article_instance[0],
            'date_posted': article_instance[1],
            'readable_date': datetime.datetime.strptime(
                article_instance[1], '%Y-%m-%d %H:%M:%S'
                ).strftime('%B %d, %Y'),
            'content': article_instance[2],
            'category': article_instance[3]
            }


def save_category(category_name):
    """
    Saves a category to the database.
    Raises an exception if the category failed to be saved.
    """
    try:
        g.db.execute(
                'insert into categories (\'name\') values ?',
                (category_name)
                )
        g.db.commit()
    except sqlite3.IntegrityError:
        error_message = 'Category {} already present in the database'.format(
                category_name
        )
        app.logger.error(error_message)
        raise DatabaseException(error_message)

    category_instance = g.db.execute(
            'select id from categories where name = ?',
            [category_name]
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
    category_instance = g.db.execute(
            'select name from categories where name = ?',
            (category_name)
            ).fetchone()
    if not category_instance:
        # saves the category in the database, raises an exception if there is an
        # issue
        save_category(category_name)

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
            (title)
            ).fetchone()
    if not article_instance:
        error_message = 'Unable to save the post to the database'
        app.logger.error(error_message)
        app.logger.error('The title was %s', title)
        raise DatabaseException(error_message)

    return article_instance[0]



@app.route('/entry/add/')
def add_article():
    """View to create a new entry"""
    if not session.get('logged_in'):
        return abort(401)
    if request.method == 'POST':
        form_errors = {}
        # goes through the form to create a new entry, after validation
        title = request.form.get('title', None)
        category = request.form.get('category', None)
        content = request.form.get('content', None)
        if not title:
            form_errors['title'] = 'Please fill the title'
        if not category:
            form_errors['category'] = 'Please fill the category'
        if not content:
            form_errors['content'] = 'Please write your article!'
        if not form_errors:
            try:
                article_id = save_article(title, content, category)
                return redirect(url_for('view_article', article_id))
            except DatabaseException as exc:
                flash(exc.message)

    return render_template('article_edition.html', form_errors=form_errors)


@app.route('/entry/<int:article_id>/')
def view_article(article_id):
    """View to read an article"""
    cursor = g.db.execute(
            'select title, date_posted, content, cat_name'
            ' from articles where id = ?',
            [article_id]
            )
    article = cursor.fetchone()
    if not article:
        # no matching article in the db, 404
        abort(404)
    else:
        article_detail = prepare_article_detail(article)
        return render_template('article.html', article=article_detail)


@app.route('/entry/<int:article_id>/edit/', methods=['POST'])
def edit_article(article_id):
    """View to edit an article"""
    if not session['logged_in']:
        abort(401)
    cursor = g.db.execute(
            'select date_posted from articles where id = ?',
            (article_id)
            )
    article = cursor.fetchone()
    if not article:
        # no matching article in the db, 404
        abort(404)
    form_errors = {}
    title = request.form.get('title', None)
    category = request.form.get('category', None)
    content = request.form.get('content', None)
    if not title:
        form_errors['title'] = 'Please fill the title'
    if not category:
        form_errors['category'] = 'Please fill the category'
    if not content:
        form_errors['content'] = 'Please write your article!'
    if not form_errors:
        g.db.execute(
                'update articles set (title, content, category)'
                ' = (?, ?, ?) where id = ?',
                (title, content, category, article_id)
                )
        flash('Article succesfully modified!')
    article_detail = prepare_article_detail(
            (title, article[0], content, category)
            )
    return render_template(
            'article_edition.html',
            article=article_detail,
            form_errors=form_errors,
            editing=True
            )


@app.route('/category/')
def list_categories():
    """View to list all categories"""
    cursor = g.db.execute(
            'select name from categories order by name'
            )
    categories = cursor.fetchall()
    per_category_recent_articles = {
            category[0]: [
                prepare_article_detail(article)
                for article in g.db.execute(
                    'select title, date_posted, content from articles'
                    ' where cat_name = ? order by date_posted',
                    (category[0])
                    ).fetchmany(size=2)
                ]
            for category in categories
            }
    return render_template(
            'categories.html',
            categories=per_category_recent_articles
            )


@app.route('/category/new/')
def add_category():
    """View to create a new category"""
    if not session['logged_in']:
        abort(401)
    if request.method == 'POST':
        form_errors = {}
        name = request.form.get('name', '')
        if not name:
            form_errors['name'] = 'Please fill the name of the category'
        if not form_errors:
            try:
                save_category(name)
                return redirect(url_for('list_categories'))
            except DatabaseException as exc:
                flash(exc.message)
    return render_template(
            'category_edition.html',
            form_errors=form_errors
            )


@app.route('/category/<string:category_name>/')
def view_category(category_name):
    """View to list all the articles under that category"""
    category_cursor = g.db.execute(
            'select name from categories where name = ?',
            (category_name)
            )
    if not category_cursor.fetchall():
        abort(404)
    cursor = g.db.execute(
            'select title, date_posted, content from articles'
            ' where cat_name = ? order by date_posted',
            (category_name)
            )
    articles = [
            prepare_article_detail(article)
            for article in cursor.fetchall()
            ]

    return render_template(
            'category_articles.html',
            articles=articles
            )


@app.route('/category/<string:category_name>/edit/', methods=['POST'])
def edit_category(category_name):
    """View to edit a specific category"""
    if not session['logged_in']:
        abort(401)
    form_errors = {}
    new_name = request.form.get('name', '')
    if not new_name:
        form_errors['name'] = 'Please fill the name of the category'
    if not form_errors:
        g.db.execute(
                'update categories set name = ?'
                ' where name = ?',
                (new_name, category_name)
                )
        flash('Category modified')
    cursor = g.db.execute(
            'select title, date_posted, content from articles'
            ' where cat_name = ? order by date_posted',
            (category_name)
            )
    articles = [
            prepare_article_detail(article)
            for article in cursor.fetchall()
            ]
    return render_template(
            'category_articles.html',
            articles=articles,
            form_errors=form_errors
            )


if __name__ == '__main__':
    app.run()

