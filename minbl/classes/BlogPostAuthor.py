class BlogPostAuthor:
    def __init__(self, post_db_lookup):
        self.id = post_db_lookup[0]
        self.email = post_db_lookup[1]
        self.username = post_db_lookup[2]
        self.display_name = post_db_lookup[3]
        self.email_is_public = post_db_lookup[4]
