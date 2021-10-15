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


def validate_user_credentials(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    db_query = tuple(db_cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?",
                                       [username, hashed_password]))
    if db_query:
        return int(db_query[0][0])

    return None


def validate_session(session_token):
    id_db = tuple(db_cursor.execute("SELECT user_id FROM session_tokens WHERE token = ?", [session_token]))
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
