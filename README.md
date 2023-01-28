# minbl
minbl is a modern looking blog software focused on being simple, made in Flask.

### installation
just install this as a pip package  
`python3 -m pip install git+https://github.com/Kyuunex/minbl.git`  
then make an apache conf that looks something like this
```bash
<IfModule mod_ssl.c>
    <VirtualHost *:443>
        ServerName blog.your-domain.com
        ServerAdmin webmaster@your-domain.com

        WSGIScriptAlias / /var/www/minbl/minblloader.wsgi

        SSLEngine on

        SSLCertificateFile /root/ssl/cloudflare/your-domain.com.pem
        SSLCertificateKeyFile /root/ssl/cloudflare/your-domain.com.key

        LogLevel warn
        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined
    </VirtualHost>
</IfModule>
```
and make a wsgi file that looks something like this
```python
#!/usr/bin/env python3

import os
import sys
import logging

logging.basicConfig(stream=sys.stderr)
os.environ["MINBL_SQLITE_FILE"] = "/var/www/blog_database/minbl.sqlite3"
# the path above has to be writable

from minbl import app as application

```
