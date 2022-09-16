# this project is still under development and should not be used in production at this point in time

# minbl
minbl is a blog software focused on being minimal, made in Flask.
+ loads instantly
+ no javascript
+ no bootstrap
+ no react
+ no bullshit

### isn't using python against minimalism? python is bloat!
using python allows me to write minimal amount of code to get the job done. 
regardless of how inefficient python itself is, because my code is very minimal, it gets the job done.  
using python also lowers the barrier of entry of anyone being able to customize this app.

### installation
just install this as a pip package  
`python3 -m pip install git+https://github.com/Kyuunex/minbl.git` 
then make an apache conf that looks something like this
```bash
<VirtualHost *:443>
ServerAdmin webmaster@your-domain.com
ServerName blog.your-domain.com

SSLEngine on
SSLCertificateFile /ssl/cloudflare/your-domain.com.pem
SSLCertificateKeyFile /ssl/cloudflare/your-domain.com.key

WSGIScriptAlias / /var/www/minbl/minblloader.wsgi

LogLevel warn
ErrorLog ${APACHE_LOG_DIR}/error.log
CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>

```
and make a wsgi file that looks something like this
```python
#!/usr/bin/env python3

import os
import sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/blog/")
os.environ["MINBL_SQLITE_FILE"] = "/var/www/blog_database/minbl.sqlite3"

from minbl import app as application

```