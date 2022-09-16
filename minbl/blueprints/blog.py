"""
This file provides endpoints for everything blog related
"""
import time

from flask import Blueprint, request, make_response, redirect, url_for, render_template

from minbl.reusables.context import db_cursor
from minbl.reusables.context import db_connection
from minbl.reusables.context import website_context
from minbl.reusables.user_validation import get_user_context

from minbl.classes.BlogPost import *
from minbl.classes.BlogPostAuthor import *
from minbl.classes.BlogPostPreview import *

blog = Blueprint("blog", __name__)


@blog.route('/', methods=['GET', 'POST'])
@blog.route('/rss', methods=['GET', 'POST'], endpoint="rss")
def index():
    """
    This endpoint provides the index page, which is a listing of the recent blog posts

    :return: html render of the recent blog posts
    """

    user_context = get_user_context()
    if user_context:
        user_permissions = user_context.permissions
    else:
        user_permissions = 1

    lookup_sql_binds = [user_permissions]
    lookup_conditions_str = "WHERE privacy <= ? AND unlisted = 0 "

    if request.args.get('author_id') and str(request.args.get('author_id')).isdigit():
        author_id = request.args.get('author_id')
        lookup_conditions_str += "AND author_id = ?"
        lookup_sql_binds.append(author_id)

    post_db_lookup = tuple(db_cursor.execute("SELECT id, author_id, title, timestamp, preview "
                                             "FROM blog_posts "
                                             f"{lookup_conditions_str} "
                                             "ORDER BY timestamp DESC", lookup_sql_binds))

    blog_posts = []
    for post in post_db_lookup:
        current_post = BlogPostPreview(post)
        current_post_author = tuple(
            db_cursor.execute("SELECT id, display_name FROM users WHERE id = ?", [current_post.author_id]))
        current_post.author = BlogPostAuthor(current_post_author[0])
        blog_posts.append(current_post)

    if request.endpoint == "blog.rss":
        rss_xml = render_template(
            "post_listing.rss",
            WEBSITE_CONTEXT=website_context,
            USER_CONTEXT=user_context,
            BLOG_POSTS=blog_posts,
            request=request
        )
        response = make_response(rss_xml)
        response.headers['Content-Type'] = 'application/rss+xml'
    else:
        normal_template = render_template(
            "post_listing.html",
            WEBSITE_CONTEXT=website_context,
            USER_CONTEXT=user_context,
            BLOG_POSTS=blog_posts
        )
        response = make_response(normal_template)
    return response


@blog.route('/post_maker_form')
def post_maker_form():
    """
    This endpoint provides a blog post form to a user, to be filled up and submitted

    :return: html render of a blog post form
    """

    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))

    return render_template("post_maker_form.html", WEBSITE_CONTEXT=website_context, USER_CONTEXT=user_context)


@blog.route('/make_post', methods=['POST'])
def make_post():
    """
    This endpoint handles the POST data submitted through post_maker_form.
    It will process user input and properly insert it into the database.

    :return: a redirect to an endpoint used to view the newly made post
    """

    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))

    if request.method == 'POST':
        post_title = request.form['post_title']
        post_privacy = request.form['post_privacy']
        post_unlisted = request.form['post_unlisted']
        post_preview = request.form['post_preview']
        post_contents = request.form['post_contents']

        db_cursor.execute("INSERT INTO blog_posts (author_id, title, timestamp, privacy, unlisted, preview, contents) "
                          "VALUES (?, ?, ?, ?, ?, ?, ?) -- RETURNING id",
                          [user_context.id, post_title, int(time.time()),
                           post_privacy, post_unlisted, post_preview, post_contents])
        db_connection.commit()

        # RETURNING SQL statement does not work so I have to do this
        post_id = tuple(db_cursor.execute("SELECT id FROM blog_posts "
                                          "WHERE author_id = ? AND title = ? AND timestamp = ? "
                                          "AND privacy = ? AND unlisted = ? AND preview = ? AND contents = ?",
                                          [user_context.id, post_title, int(time.time()),
                                           post_privacy, post_unlisted, post_preview, post_contents]))

        resp = make_response(redirect(url_for("blog.post_view", post_id=int(post_id[0][0]))))

        return resp


@blog.route('/post_view/<post_id>')
def post_view(post_id):
    """
    This endpoint reads the database and renders an html page containing the specified blog post.

    :param post_id: ID of the blog post
    :return: An html page render containing the blog post
    """

    user_context = get_user_context()
    if user_context:
        user_permissions = user_context.permissions
    else:
        user_permissions = 1

    post_db_lookup = tuple(db_cursor.execute("SELECT id, author_id, title, timestamp, privacy, unlisted, contents "
                                             "FROM blog_posts "
                                             "WHERE id = ? AND privacy <= ? ", [post_id, user_permissions]))
    if not post_db_lookup:
        return make_response(redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

    blog_post = BlogPost(post_db_lookup[0])
    blog_post_author = tuple(
        db_cursor.execute("SELECT id, display_name FROM users WHERE id = ?", [blog_post.author_id]))
    blog_post.author = BlogPostAuthor(blog_post_author[0])

    return render_template(
        "post_view.html",
        WEBSITE_CONTEXT=website_context,
        USER_CONTEXT=user_context,
        BLOG_POST=blog_post
    )
