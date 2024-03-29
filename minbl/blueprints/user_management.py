from flask import Blueprint, request, make_response, redirect, url_for, render_template

import hashlib
import ipaddress
import time
import pyotp
import uuid
from datetime import datetime, timezone

from minbl.reusables.rng import get_random_string
from minbl.reusables.iptools import ip_decode
from minbl.reusables.context import db_cursor
from minbl.reusables.context import db_connection
from minbl.reusables.context import website_context
from minbl.reusables.user_validation import get_user_context
from minbl.reusables.user_validation import validate_user_credentials

user_management = Blueprint("user_management", __name__)


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

    is_anyone_registered = tuple(db_cursor.execute("SELECT id FROM users"))
    is_registration_enabled = tuple(db_cursor.execute(
        "SELECT value FROM app_configuration WHERE setting = ?", ["allow_registration"])
    )
    allow_registration = True
    if not is_registration_enabled:
        if is_anyone_registered:
            allow_registration = False

    return render_template("login_form.html", WEBSITE_CONTEXT=website_context, ALLOW_REGISTRATION=allow_registration)


@user_management.route('/account_recovery_form')
def account_recovery_form():
    user_context = get_user_context()
    if user_context:
        return redirect(url_for("blog.index"))

    return render_template("account_recovery_form.html", WEBSITE_CONTEXT=website_context)


@user_management.route('/totp_enable_form')
def totp_enable_form():
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("blog.index"))

    totp_already_enabled = tuple(db_cursor.execute("SELECT enabled FROM totp_seeds WHERE user_id = ?",
                                                   [str(user_context.id)]))
    if totp_already_enabled:
        return render_template(
            "account_settings.html",
            WEBSITE_CONTEXT=website_context,
            USER_CONTEXT=user_context,
            NOTICE_MESSAGE="TOTP is already enabled for this account!",
            ALERT_TYPE="alert-info"
        )

    totp_seed = pyotp.random_base32()

    return render_template(
        "totp_enable_form.html",
        WEBSITE_CONTEXT=website_context,
        USER_CONTEXT=user_context,
        GENERATED_TOTP_SEED=totp_seed
    )


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
        otp = request.form['generated_code']
        user_id = validate_user_credentials(username, password, otp=otp)
        if not user_id:
            return render_template(
                "login_form.html",
                WEBSITE_CONTEXT=website_context,
                NOTICE_MESSAGE="wrong password",
                ALERT_TYPE="alert-danger"
            )

        new_session_token = get_random_string(32)
        resp = make_response(redirect(url_for("blog.index")))

        if bool(request.form.get('remember_me', 0)):
            cookie_age = 34560000
            expiry_timestamp = int(time.time()) + cookie_age
        else:
            cookie_age = None
            expiry_timestamp = int(time.time()) + 172800

        resp.set_cookie('session_token', new_session_token, max_age=cookie_age)

        hashed_token = hashlib.sha256(new_session_token.encode()).hexdigest()
        client_ip_address_is_ipv6, client_ip_address_int = ip_decode(request)
        token_id = uuid.uuid4()

        db_cursor.execute("INSERT INTO session_tokens VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          [str(user_id), str(token_id), hashed_token,
                           int(time.time()), expiry_timestamp, str(request.user_agent.string),
                           int(client_ip_address_int), int(client_ip_address_is_ipv6)])
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

        password_salt = get_random_string(32)

        hashed_password = hashlib.sha256((password + password_salt).encode()).hexdigest()

        if not is_anyone_registered:
            perms_to_give = 9
        else:
            perms_to_give = 2

        username_already_taken = tuple(db_cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE",
                                                         [username.lower()]))

        if username_already_taken:
            return "the username is already taken!"

        user_id = uuid.uuid4()

        db_cursor.execute("INSERT INTO users (id, email, username, display_name, permissions, email_is_public) "
                          "VALUES (?, ?, ?, ?, ?, ?)",
                          [str(user_id), str(email), str(username), str(display_name), perms_to_give, 0])
        db_connection.commit()

        db_cursor.execute("INSERT INTO user_passwords (user_id, password_hash, password_salt) VALUES (?, ?, ?)",
                          [str(user_id), str(hashed_password), password_salt])
        db_connection.commit()

        new_session_token = get_random_string(32)
        resp = make_response(redirect(url_for("blog.index")))
        resp.set_cookie('session_token', new_session_token, max_age=34560000)
        token_id = uuid.uuid4()
        expiry_timestamp = int(time.time()) + 34560000
        hashed_token = hashlib.sha256(new_session_token.encode()).hexdigest()
        # todo fix
        client_ip_address_is_ipv6, client_ip_address_int = ip_decode(request)
        db_cursor.execute("INSERT INTO session_tokens VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          [str(user_id), str(token_id), hashed_token,
                           int(time.time()), expiry_timestamp, str(request.user_agent.string),
                           int(client_ip_address_int), int(client_ip_address_is_ipv6)])
        db_connection.commit()
        return resp


@user_management.route('/account_recovery_attempt', methods=['POST'])
def account_recovery_attempt():
    return make_response(redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))


@user_management.route('/enable_totp', methods=['POST'])
def enable_totp():
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))
    if request.method == 'POST':
        totp_seed = request.form['totp_seed']
        generated_code = request.form['generated_code']
        totp = pyotp.TOTP(totp_seed)
        if not totp.verify(str(generated_code)):
            return render_template(
                "account_settings.html",
                WEBSITE_CONTEXT=website_context,
                USER_CONTEXT=user_context,
                NOTICE_MESSAGE="incorrect 6 digit code",
                ALERT_TYPE="alert-danger"
            )
        db_cursor.execute("INSERT INTO totp_seeds VALUES (?, ?, 1)", [str(user_context.id), totp_seed])
        db_connection.commit()
        return render_template(
                "account_settings.html",
                WEBSITE_CONTEXT=website_context,
                USER_CONTEXT=user_context,
                NOTICE_MESSAGE="success",
                ALERT_TYPE="alert-success"
            )
    return render_template(
        "account_settings.html",
        WEBSITE_CONTEXT=website_context,
        USER_CONTEXT=user_context,
        NOTICE_MESSAGE="invalid use of the endpoint",
        ALERT_TYPE="alert-danger"
    )


@user_management.route('/profile/<user_id>')
def profile(user_id):
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))

    info_db = tuple(db_cursor.execute("SELECT id, email, username, display_name, permissions, email_is_public "
                                      "FROM users WHERE id = ?",
                                      [user_id]))
    return render_template("profile.html", WEBSITE_CONTEXT=website_context, info=info_db[0], USER_CONTEXT=user_context)


@user_management.route('/logout')
def logout():
    if not get_user_context():
        return redirect(url_for("user_management.login_form"))

    resp = make_response(redirect(url_for("user_management.login_form")))
    resp.set_cookie('session_token', '', max_age=34560000)

    hashed_token = hashlib.sha256((request.cookies['session_token']).encode()).hexdigest()

    db_cursor.execute("DELETE FROM session_tokens WHERE token = ?", [hashed_token])
    db_connection.commit()
    return resp


@user_management.route('/session_listing')
def session_listing_page():
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))

    session_listing = tuple(db_cursor.execute("SELECT token, timestamp, user_agent, ip_address, is_ipv6, "
                                              "token_id, expiry_timestamp "
                                              "FROM session_tokens WHERE user_id = ?"
                                              "ORDER BY timestamp DESC", [user_context.id]))

    return render_template(
        "session_listing.html",
        WEBSITE_CONTEXT=website_context,
        USER_CONTEXT=user_context,
        SESSION_LISTING=session_listing,
        datetime=datetime,
        ipaddress=ipaddress,
        timezone=timezone
    )


@user_management.route('/destroy_session_token', methods=['GET'])
def destroy_session_token():
    if not get_user_context():
        return redirect(url_for("user_management.login_form"))

    resp = make_response(redirect(url_for("user_management.session_listing_page")))

    token_id = request.args.get('token_id')

    db_cursor.execute("DELETE FROM session_tokens WHERE token_id = ?", [token_id])
    db_connection.commit()
    return resp


@user_management.route('/change_password_form')
def change_password_form():
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))

    return render_template("password_change_form.html", WEBSITE_CONTEXT=website_context, USER_CONTEXT=user_context)


@user_management.route('/change_password_attempt', methods=['POST'])
def change_password_attempt():
    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))

    old_password = request.form['old_password']
    new_password = request.form['new_password']
    repeat_new_password = request.form['repeat_new_password']
    otp = request.form['generated_code']

    if not new_password == repeat_new_password:
        return render_template(
            "account_settings.html",
            WEBSITE_CONTEXT=website_context,
            USER_CONTEXT=user_context,
            NOTICE_MESSAGE="passwords don't match",
            ALERT_TYPE="alert-danger"
        )

    # validate old password

    old_password_salt_db = tuple(db_cursor.execute("SELECT password_salt FROM user_passwords WHERE user_id = ?",
                                                   [user_context.id]))
    if not old_password_salt_db:
        # This should never happen
        return "this should never happen error"

    user_totp_seed = tuple(db_cursor.execute("SELECT seed FROM totp_seeds WHERE user_id = ? AND enabled = 1",
                                             [user_context.id]))
    if user_totp_seed:
        totp = pyotp.TOTP(user_totp_seed[0][0])
        if not totp.verify(str(otp)):
            return render_template(
                "account_settings.html",
                WEBSITE_CONTEXT=website_context,
                USER_CONTEXT=user_context,
                NOTICE_MESSAGE="totp is enabled for this account but not supplied or correct",
                ALERT_TYPE="alert-danger"
            )

    old_password_salt = old_password_salt_db[0][0]

    old_hashed_password = hashlib.sha256((old_password + old_password_salt).encode()).hexdigest()

    db_query = tuple(db_cursor.execute("SELECT user_id FROM user_passwords WHERE user_id = ? AND password_hash = ?",
                                       [user_context.id, old_hashed_password]))
    if not db_query:
        return render_template(
            "account_settings.html",
            WEBSITE_CONTEXT=website_context,
            USER_CONTEXT=user_context,
            NOTICE_MESSAGE="old password incorrect",
            ALERT_TYPE="alert-danger"
        )

    db_cursor.execute("DELETE FROM user_passwords WHERE user_id = ? AND password_hash = ? AND password_salt = ?",
                      [str(user_context.id), str(old_hashed_password), old_password_salt])

    # generate new password hash
    new_password_salt = get_random_string(32)

    new_hashed_password = hashlib.sha256((new_password + new_password_salt).encode()).hexdigest()

    db_cursor.execute("INSERT INTO user_passwords (user_id, password_hash, password_salt) VALUES (?, ?, ?)",
                      [str(user_context.id), str(new_hashed_password), new_password_salt])
    db_connection.commit()

    return render_template(
        "account_settings.html",
        WEBSITE_CONTEXT=website_context,
        USER_CONTEXT=user_context,
        NOTICE_MESSAGE="password changed successfully",
        ALERT_TYPE="alert-success"
    )
