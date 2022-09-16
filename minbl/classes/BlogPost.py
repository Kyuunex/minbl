from datetime import datetime


class BlogPost:
    def __init__(self, post_db_lookup):
        self.post_id = post_db_lookup[0]
        self.author_id = post_db_lookup[1]
        self.title = post_db_lookup[2]
        self.timestamp = post_db_lookup[3]
        self.privacy = post_db_lookup[4]
        self.unlisted = post_db_lookup[5]
        self.contents = post_db_lookup[6]
        self.timestamp_utc = str(datetime.fromtimestamp(self.timestamp))