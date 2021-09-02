class BlogPostAuthor:
    def __init__(self, post_db_lookup):
        self.id = post_db_lookup[0]
        self.display_name = post_db_lookup[1]
