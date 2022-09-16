#!/usr/bin/env python3
"""
This file stitches the whole flask app together
"""

from flask import Flask, url_for, redirect

from minbl.reusables.context import db_connection
from minbl.reusables.context import website_context
from minbl.reusables.user_validation import get_user_context

from minbl.blueprints.administration import administration
from minbl.blueprints.blog import blog
from minbl.blueprints.user_management import user_management

app = Flask(__name__)
app.register_blueprint(administration)
app.register_blueprint(blog)
app.register_blueprint(user_management)


@app.route('/server_shutdown')
def server_shutdown():
    """
    This endpoint provides the website administrator a way to
    safely commit database changes before shutting the app down

    :return: if logged in, the string response if success, if not logged in, a redirect to the login form
    """

    user_context = get_user_context()
    if not user_context:
        return redirect(url_for("user_management.login_form"))
    if not user_context.permissions >= 9:
        return "you do not have permissions to perform this action"

    db_connection.commit()
    db_connection.close()
    return "server ready for shutdown"
