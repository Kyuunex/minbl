from datetime import datetime, timezone


class BlogPostPreview:
    def __init__(self, post_db_lookup):
        self.post_id = post_db_lookup[0]
        self.author_id = post_db_lookup[1]
        self.title = post_db_lookup[2]
        self.timestamp = post_db_lookup[3]
        self.preview = post_db_lookup[4]
        self.timestamp_utc = datetime.fromtimestamp(self.timestamp, timezone.utc)
        self.custom_url = post_db_lookup[5]
        self.author = None
