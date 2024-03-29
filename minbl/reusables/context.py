"""
This file provides a context needed for the rest of the app to function.
This includes, providing a database, and the desired app configuration.
"""

import os
import sqlite3

if not os.environ.get('MINBL_SQLITE_FILE'):
    print("This app uses an sqlite3 database. You need to EXPORT a location of the database file to MINBL_SQLITE_FILE")
    raise SystemExit

SQLITE_FILE = os.environ.get('MINBL_SQLITE_FILE')

db_connection = sqlite3.connect(SQLITE_FILE, check_same_thread=False)
db_cursor = db_connection.cursor()
db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS "users" (
            "id"    TEXT NOT NULL,
            "email"    TEXT,
            "username"    TEXT NOT NULL UNIQUE,
            "display_name"    TEXT NOT NULL,
            "permissions"    INTEGER NOT NULL,
            "email_is_public"    INTEGER NOT NULL
        )
""")
db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS "session_tokens" (
            "user_id"    TEXT NOT NULL,
            "token_id"    TEXT NOT NULL,
            "token"    TEXT NOT NULL,
            "timestamp"    INTEGER NOT NULL,
            "expiry_timestamp"    INTEGER NOT NULL,
            "user_agent"    TEXT NOT NULL,
            "ip_address"    INTEGER NOT NULL,
            "is_ipv6"    INTEGER NOT NULL
        )
""")
db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS "totp_seeds" (
            "user_id"    TEXT NOT NULL,
            "seed"    TEXT NOT NULL,
            "enabled"    INTEGER NOT NULL
        )
""")
db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS "user_passwords" (
            "user_id"    TEXT NOT NULL,
            "password_hash"    TEXT NOT NULL,
            "password_salt"    TEXT NOT NULL
        )
""")
db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS "blog_posts" (
            "id"    TEXT NOT NULL,
            "author_id"    TEXT NOT NULL,
            "title"    TEXT NOT NULL,
            "timestamp"    INTEGER NOT NULL,
            "privacy"    INTEGER NOT NULL,
            "unlisted"    INTEGER NOT NULL,
            "preview"    TEXT NOT NULL,
            "contents"    TEXT NOT NULL,
            "custom_url"    TEXT NOT NULL,
            "last_edit_timestamp"    INTEGER,
            "category"    TEXT,
            "tags"    TEXT,
            "cover_image_url"    TEXT
        )
""")
db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS "blog_post_attachments" (
            "post_id"    TEXT NOT NULL,
            "url"    TEXT NOT NULL,
            "type"    INTEGER NOT NULL
        )
""")
db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS "app_configuration" (
            "setting"    TEXT NOT NULL,
            "value"    TEXT NOT NULL
        )
""")
db_connection.commit()

website_context = {}

user_context_list = tuple(db_cursor.execute(
    "SELECT value FROM app_configuration WHERE setting = ?", ["title"])
)

if user_context_list:
    website_context["title"] = user_context_list[0][0]
else:
    website_context["title"] = "minbl"


