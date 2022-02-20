import pyotp
from flask import request

import hashlib

from minbl.reusables.context import db_cursor


class CurrentUser:
    # TODO: detect user timezone and put it here
    def __init__(self, user_context_list):
        self.id = int(user_context_list[0])
        self.email = str(user_context_list[1])
        self.username = str(user_context_list[2])
        self.display_name = str(user_context_list[3])
        self.permissions = int(user_context_list[4])


def validate_user_credentials(username, password, otp=None):
    user_id = tuple(db_cursor.execute("SELECT id FROM users WHERE username = ?", [username]))
    if not user_id:
        return None

    password_salt_db = tuple(db_cursor.execute("SELECT password_salt FROM user_passwords WHERE user_id = ?",
                                               [user_id[0][0]]))
    if not password_salt_db:
        # This should never happen
        return None

    user_totp_seed = tuple(db_cursor.execute("SELECT seed FROM totp_seeds WHERE user_id = ? AND enabled = 1",
                                             [user_id[0][0]]))
    if user_totp_seed:
        totp = pyotp.TOTP(user_totp_seed[0][0])
        if not totp.verify(str(otp)):
            return None

    password_salt = password_salt_db[0][0]

    hashed_password = hashlib.sha256((password+password_salt).encode()).hexdigest()

    db_query = tuple(db_cursor.execute("SELECT user_id FROM user_passwords WHERE user_id = ? AND password_hash = ?",
                                       [user_id[0][0], hashed_password]))
    if db_query:
        return int(db_query[0][0])

    return None


def validate_session(session_token):
    hashed_token = hashlib.sha256(session_token.encode()).hexdigest()

    id_db = tuple(db_cursor.execute("SELECT user_id FROM session_tokens WHERE token = ?", [hashed_token]))
    if id_db:
        return int(id_db[0][0])
    else:
        return None


def is_successfully_logged_in():
    if 'session_token' in request.cookies:
        user_id = validate_session(request.cookies['session_token'])
        if user_id:
            return user_id
    return None


def get_user_context():
    if 'session_token' in request.cookies:
        user_id = validate_session(request.cookies['session_token'])
        if user_id:
            user_context_list = tuple(db_cursor.execute(
                "SELECT id, email, username, display_name, permissions FROM users WHERE id = ?",
                [user_id])
            )
            if user_context_list:
                return CurrentUser(user_context_list[0])
    return None
