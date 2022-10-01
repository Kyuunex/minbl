from datetime import datetime, timezone, timedelta


class BlogPost:
    def __init__(self, post_db_lookup):
        self.post_id = post_db_lookup[0]
        self.author_id = post_db_lookup[1]
        self.title = post_db_lookup[2]
        self.timestamp = post_db_lookup[3]
        self.privacy = post_db_lookup[4]
        self.unlisted = post_db_lookup[5]
        self.preview = post_db_lookup[6]
        self.contents = post_db_lookup[7]
        self.timestamp_utc = datetime.fromtimestamp(self.timestamp, timezone.utc)
        self.custom_url = post_db_lookup[8]
        self.last_edit_timestamp = post_db_lookup[9]
        if self.last_edit_timestamp:
            self.last_edit_timestamp_utc = datetime.fromtimestamp(self.last_edit_timestamp, timezone.utc)
        else:
            self.last_edit_timestamp_utc = self.timestamp_utc
        self.category = post_db_lookup[10]
        self.tags = post_db_lookup[11]
        self.cover_image_url = post_db_lookup[12]
        self.expiration_time_utc = self.last_edit_timestamp_utc + timedelta(hours=175320)
        self.author = None
