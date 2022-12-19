"""
This file provides endpoints for everything blog related
"""
import time
import uuid
import re
import markdown2
from feedgen.feed import FeedGenerator
from urllib.parse import urlparse


from flask import Blueprint, request, make_response, redirect, url_for, render_template

from minbl.reusables.context import db_cursor
from minbl.reusables.context import db_connection
from minbl.reusables.context import website_context
from minbl.reusables.user_validation import get_user_context

from minbl.classes.BlogPost import *
from minbl.classes.BlogPostAuthor import *
from minbl.classes.BlogPostDeletedAuthor import *

blog = Blueprint("blog", __name__)


@blog.route('/', methods=['GET', 'POST'])
@blog.route('/rss', methods=['GET', 'POST'], endpoint="rss_deprecated")
@blog.route('/rss.xml', methods=['GET', 'POST'], endpoint="rss")
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
    lookup_conditions_str = "WHERE privacy <= ? "
    if not user_permissions >= 5:
        lookup_conditions_str += "AND unlisted = 0 "

    if request.args.get('author_id'):
        author_id = request.args.get('author_id')
        lookup_conditions_str += "AND author_id = ?"
        lookup_sql_binds.append(author_id)

    post_db_lookup = tuple(db_cursor.execute("SELECT id, author_id, title, timestamp, "
                                             "privacy, unlisted, preview, contents, custom_url, "
                                             "last_edit_timestamp, category, tags, cover_image_url "
                                             "FROM blog_posts "
                                             f"{lookup_conditions_str} "
                                             "ORDER BY timestamp DESC", lookup_sql_binds))

    blog_posts = []
    for post in post_db_lookup:
        current_post = BlogPost(post)
        current_post_author = tuple(
            db_cursor.execute("SELECT id, email, username, display_name, email_is_public FROM users WHERE id = ?",
                              [current_post.author_id]))
        if current_post_author:
            current_post.author = BlogPostAuthor(current_post_author[0])
        else:
            current_post.author = BlogPostDeletedAuthor(current_post.author_id)
        blog_posts.append(current_post)

    if request.endpoint == "blog.rss" or request.endpoint == "blog.rss_deprecated":
        feed = FeedGenerator()
        feed.title(website_context["title"])
        feed.description("In cases of constant automated scrapers, avoid scraping more than once per few hours.")
        feed.link(href=request.host_url)
        url_parsed = urlparse(request.base_url)

        for blog_post in blog_posts:
            feed_entry = feed.add_entry()
            feed_entry.title(blog_post.title)
            if blog_post.author.email_is_public:
                author_email = blog_post.author.email
            else:
                author_email = blog_post.author_id + "@" + url_parsed.hostname
            feed_entry.author(name=blog_post.author.display_name, email=author_email)
            feed_entry.description(blog_post.preview)
            feed_entry.pubDate(blog_post.timestamp_utc)
            feed_entry.link(href=url_for("blog.custom_url", post_id=blog_post.custom_url, _external=True))
            feed_entry.guid(url_for("blog.post_view", post_id=blog_post.post_id, _external=True), permalink=True)

        response = make_response(feed.rss_str())
        response.headers.set("Content-Type", "application/rss+xml")
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
    if not user_context.permissions >= 5:
        return "you do not have permissions to perform this action"

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
    if not user_context.permissions >= 5:
        return "you do not have permissions to perform this action"

    if request.method == 'POST':
        post_title = request.form['post_title']
        post_privacy = request.form['post_privacy']
        post_unlisted = request.form['post_unlisted']
        category = request.form['category']
        tags = request.form['tags']
        cover_image_url = request.form['cover_image_url']
        post_preview = request.form['post_preview']
        post_contents = request.form['post_contents']
        posix_timestamp = int(time.time())
        date_string = datetime.date(datetime.fromtimestamp(posix_timestamp, timezone.utc)).isoformat()

        post_id = uuid.uuid4()
        custom_url = date_string + "-" + re.sub(r'[^a-zA-Z0-9- ]', '', post_title).replace(" ", "-")

        db_cursor.execute("INSERT INTO blog_posts (id, author_id, title, timestamp, "
                          "privacy, unlisted, preview, contents, custom_url, "
                          "last_edit_timestamp, category, tags, cover_image_url) "
                          "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          [str(post_id), user_context.id, post_title, posix_timestamp,
                           post_privacy, post_unlisted, post_preview, post_contents, custom_url,
                           posix_timestamp, category, tags, cover_image_url])
        db_connection.commit()

        resp = make_response(redirect(url_for("blog.custom_url", post_id=custom_url)))

        return resp


@blog.route('/post_view/<post_id>')
@blog.route('/p/<post_id>', endpoint="custom_url")
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

    if request.endpoint == "blog.custom_url":
        post_db_lookup = tuple(db_cursor.execute("SELECT id, author_id, title, timestamp, "
                                                 "privacy, unlisted, preview, contents, custom_url, "
                                                 "last_edit_timestamp, category, tags, cover_image_url "
                                                 "FROM blog_posts "
                                                 "WHERE custom_url = ? AND privacy <= ? ", [post_id, user_permissions]))
    else:
        post_db_lookup = tuple(db_cursor.execute("SELECT id, author_id, title, timestamp, "
                                                 "privacy, unlisted, preview, contents, custom_url, "
                                                 "last_edit_timestamp, category, tags, cover_image_url "
                                                 "FROM blog_posts "
                                                 "WHERE id = ? AND privacy <= ? ", [post_id, user_permissions]))
    if not post_db_lookup:
        return make_response(redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

    blog_post = BlogPost(post_db_lookup[0])
    blog_post_author = tuple(
        db_cursor.execute("SELECT id, email, username, display_name, email_is_public FROM users WHERE id = ?",
                          [blog_post.author_id]))
    if blog_post_author:
        blog_post.author = BlogPostAuthor(blog_post_author[0])
    else:
        blog_post.author = BlogPostDeletedAuthor(blog_post.author_id)

    classesDict = {"table": "table table-striped"}

    extras = {
        "tables": None,
        "html-classes": classesDict,
        "target-blank-links": None,
        "fenced-code-blocks": None
    }

    return render_template(
        "post_view.html",
        WEBSITE_CONTEXT=website_context,
        USER_CONTEXT=user_context,
        BLOG_POST=blog_post,
        USER_PERMISSIONS=user_permissions,
        markdown2=markdown2,
        markdown_extras=extras
    )


@blog.route('/post_edit_form/<post_id>')
def post_edit_form(post_id):
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))
    if not user_context.permissions >= 5:
        return "you do not have permissions to perform this action"
    user_permissions = user_context.permissions

    post_db_lookup = tuple(db_cursor.execute("SELECT id, author_id, title, timestamp, "
                                             "privacy, unlisted, preview, contents, custom_url, "
                                             "last_edit_timestamp, category, tags, cover_image_url "
                                             "FROM blog_posts "
                                             "WHERE id = ? AND privacy <= ? ", [post_id, user_permissions]))

    if not post_db_lookup:
        return make_response(redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

    blog_post = BlogPost(post_db_lookup[0])

    return render_template(
        "post_edit_form.html",
        WEBSITE_CONTEXT=website_context,
        USER_CONTEXT=user_context,
        BLOG_POST=blog_post
    )


@blog.route('/delete_post/<post_id>')
def delete_post(post_id):
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))
    if not user_context.permissions >= 5:
        return "you do not have permissions to perform this action"

    db_cursor.execute("DELETE FROM blog_posts WHERE id = ?", [post_id])

    return redirect(url_for("blog.index"))


@blog.route('/edit_post/<post_id>', methods=['POST'])
def edit_post(post_id):
    """
    This endpoint handles the POST data submitted through post_maker_form.
    It will process user input and properly insert it into the database.

    :return: a redirect to an endpoint used to view the newly made post
    """

    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))
    if not user_context.permissions >= 5:
        return "you do not have permissions to perform this action"

    if request.method == 'POST':
        post_title = request.form['post_title']
        post_privacy = request.form['post_privacy']
        post_unlisted = request.form['post_unlisted']
        category = request.form['category']
        tags = request.form['tags']
        cover_image_url = request.form['cover_image_url']
        post_preview = request.form['post_preview']
        post_contents = request.form['post_contents']
        posix_timestamp = int(time.time())

        custom_url = request.form['custom_url']

        db_cursor.execute("UPDATE blog_posts "
                          "SET title = ?, privacy = ?, unlisted = ?, preview = ?, contents = ?, custom_url = ?, "
                          "last_edit_timestamp = ?, category = ?, tags = ?, cover_image_url = ? "
                          "WHERE id = ?",
                          [post_title, post_privacy, post_unlisted, post_preview, post_contents,
                           custom_url, posix_timestamp, category, tags, cover_image_url, post_id])
        db_connection.commit()

        resp = make_response(redirect(url_for("blog.custom_url", post_id=custom_url)))

        return resp
