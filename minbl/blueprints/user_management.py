from flask import Blueprint, request, make_response, redirect, url_for, render_template

import hashlib
import string
import random

from minbl.reusables.context import db_cursor
from minbl.reusables.context import db_connection
from minbl.reusables.context import website_context
from minbl.reusables.user_validation import get_user_context
from minbl.reusables.user_validation import validate_user_credentials

user_management = Blueprint("user_management", __name__)


def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


@user_management.route('/my_profile')
def my_profile():
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))
    else:
        return redirect(url_for("user_management.profile", user_id=user_context.id))


@user_management.route('/account_settings')
def account_settings():
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))
    else:
        return render_template("account_settings.html", WEBSITE_CONTEXT=website_context, USER_CONTEXT=user_context)


@user_management.route('/login_form')
def login_form():
    user_context = get_user_context()
    if user_context:
        return redirect(url_for("blog.index"))

    return render_template("login_form.html", WEBSITE_CONTEXT=website_context)


@user_management.route('/registration_form')
def registration_form():
    is_anyone_registered = tuple(db_cursor.execute("SELECT id FROM users"))
    is_registration_enabled = tuple(db_cursor.execute(
        "SELECT value FROM app_configuration WHERE setting = ?", ["allow_registration"])
    )

    if not is_registration_enabled:
        if is_anyone_registered:
            return make_response(redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

    user_context = get_user_context()
    if user_context:
        return redirect(url_for("blog.index"))

    return render_template("registration_form.html", WEBSITE_CONTEXT=website_context)


@user_management.route('/login_attempt', methods=['POST'])
def login_attempt():
    if get_user_context():
        return redirect(url_for("blog.index"))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_id = validate_user_credentials(username, password)
        if not user_id:
            return "wrong pass"

        new_session_token = get_random_string(32)
        resp = make_response(redirect(url_for("blog.index")))
        resp.set_cookie('session_token', new_session_token)
        db_cursor.execute("INSERT INTO session_tokens VALUES (?, ?)", [int(user_id), new_session_token])
        db_connection.commit()
        return resp


@user_management.route('/registration_attempt', methods=['POST'])
def registration_attempt():
    is_anyone_registered = tuple(db_cursor.execute("SELECT id FROM users"))
    is_registration_enabled = tuple(db_cursor.execute(
        "SELECT value FROM app_configuration WHERE setting = ?", ["allow_registration"])
    )

    if not is_registration_enabled:
        if is_anyone_registered:
            return make_response(redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

    if get_user_context():
        return redirect(url_for("blog.index"))

    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        display_name = request.form['display_name']

        password = request.form['password']
        repeat_password = request.form['repeat_password']

        if not password == repeat_password:
            return "passwords don't match"

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if not is_anyone_registered:
            perms_to_give = 9
        else:
            perms_to_give = 2

        username_already_taken = tuple(db_cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE",
                                                         [username.lower()]))

        if username_already_taken:
            return "the username is already taken!"

        db_cursor.execute("INSERT INTO users (email, username, password, display_name, permissions) "
                          "VALUES (?, ?, ?, ?, ?)",
                          [str(email), str(username), str(hashed_password), str(display_name), perms_to_give])
        db_connection.commit()

        # RETURNING SQL statement does not work so I have to do this
        user_id = tuple(db_cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?",
                                          [str(username), str(hashed_password)]))

        new_session_token = get_random_string(32)
        resp = make_response(redirect(url_for("blog.index")))
        resp.set_cookie('session_token', new_session_token)
        db_cursor.execute("INSERT INTO session_tokens VALUES (?, ?)", [int(user_id[0][0]), new_session_token])
        db_connection.commit()
        return resp


@user_management.route('/profile/<user_id>')
def profile(user_id):
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))

    if not user_id.isdigit():
        return make_response(redirect("https://www.youtube.com/watch?v=o-YBDTqX_ZU"))

    info_db = tuple(db_cursor.execute("SELECT * FROM users WHERE id = ?", [user_id]))
    return render_template("profile.html", WEBSITE_CONTEXT=website_context, info=info_db[0], USER_CONTEXT=user_context)


@user_management.route('/logout')
def logout():
    if not get_user_context():
        return redirect(url_for("user_management.login_form"))

    resp = make_response(redirect(url_for("user_management.login_form")))
    resp.set_cookie('session_token', '', expires=0)
    db_cursor.execute("DELETE FROM session_tokens WHERE token = ?", [request.cookies['session_token']])
    db_connection.commit()
    return resp
