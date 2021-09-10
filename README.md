# Metabase matview

[Metabase](https://www.metabase.com/) is a tool to query and visualise data in databases.
This tool allows 'converting' a Metabase question to a materialized view, so that questions
that take a long time to run can be cached, also when used [in another question](https://www.metabase.com/docs/latest/users-guide/referencing-saved-questions-in-queries.html).

Ultimately this may be [solved within Metabase](https://github.com/metabase/metabase/issues/5596),
in the meantime this tool hopes to provide a workaround.

![screenshot of app](screenshot-1.png)
![screenshot of materialized Metabase question](screenshot-2.png)

## Install

Deployment can be done in several ways, depending on your needs. This section describes
how to put Metabase and this application on the same host, so that the Metabase session
cookie can be used for authentication. It assumes that Metabase is
[running as a service on Debian/Ubuntu](https://www.metabase.com/docs/latest/operations-guide/running-metabase-on-debian.html)
with nginx as a reverse proxy.

### Dependencies

Make sure you have Python 3. Then you need to install the dependencies. It's best to
install dependencies using the package manager, so do that when possible (assuming
Debian/Ubuntu here):

```sh
apt install python3 python3-pip python3-requests
```

Some packages may not have up-to-date versions in the system repositories, install
additional dependencies from the [`requirements.txt`](requirements.txt) file:

```sh
pip3 install -r requirements.txt
```

### Flask App

First this app needs to be installed as a service on the same host as Metabase. There
are [different options](https://flask.palletsprojects.com/en/2.0.x/deploying/),
we'll use [gunicorn](https://gunicorn.org/). First install this app and gunicorn:

```sh
apt install gunicorn3
useradd -m -s /usr/sbin/nologin gunicorn
git clone https://github.com/q-m/metabase-matview.git /home/gunicorn/metabase-matview
```

Then create a systemd service to have it running always, as [described here](https://docs.gunicorn.org/en/stable/deploy.html#systemd).

Create `/etc/systemd/system/gunicorn.service`:

```systemd
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
Type=notify
User=wsgi
Group=wsgi
RuntimeDirectory=gunicorn
WorkingDirectory=/home/gunicorn/metabase-matview
EnvironmentFile=/etc/default/gunicorn
ExecStart=/usr/bin/gunicorn -w 2 server:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/gunicorn.socket`:

```systemd
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock
# socket needs to be accessible by nginx (systemd passes it to gunicorn)
SocketUser=www-data
SocketMode=600

[Install]
WantedBy=sockets.target
```

Finally create a file with configuration variables in `/etc/default/gunicorn`:

```sh
METABASE_URL=https://metabase.example.com/
METABASE_DATABASE_ID=1
DATABASE_URL=postgres://user:pass@host/db
```

Then start it:

```sh
systemctl enable --now gunicorn.socket
```

### nginx

Then in your `server` section in `/etc/nginx/sites-enabled/default` (or perhaps `/etc/nginx/nginx.conf`).

```nginx
server {
  # ...

  # add this location
  location /matview {
    proxy_pass http://unix://run/gunicorn.sock
    proxy_redirect off;
  }

  # you should already have something like this for Metabase
  location / {
    proxy_pass http://localhost:3000/;
    proxy_redirect off;
  }
}
```

## Use

Make sure you are logged into Metabase.
Then visit https://metabase.example.com/matview (with the proper domain name you're using).
Click _Add question_ and enter a question ID to materialize.
Don't forget to _Refresh_ when you need updated data.

## Limitations

- Only native SQL queries are supported.
- Questions with filters or references to other questions don't work.
- Currently only one database is supported.
- Need to refresh manually.

## License

This project is licensed under the [GPL v3 or later](LICENSE.md).
