Tutorial for install Hub I3 on a production server:

Paths used below (adjust to your server): application in `/var/webapp/hub-i3`,
user `webapp`, gunicorn listening on `127.0.0.1:5000`.

1) Install NGINX and system packages (logged as root):

````
apt-get install -y nginx build-essential libssl-dev python3-dev libxml2-dev git libfreetype6 libfreetype6-dev libpq-dev libjpeg-dev zlib1g-dev gettext gdal-bin libgdal-dev
dpkg-reconfigure tzdata
````

(`gettext` is required by `compilemessages`; `gdal-bin`/`libgdal-dev` by GeoDjango.)

2) Create webapp user and permissions (logged as root)

````
adduser  --gecos "" webapp
usermod -a -G www-data webapp
cd /var
mkdir webapp
chown root:www-data webapp
chmod g+ws webapp
cd /etc/nginx/
sudo chown root:www-data sites-enabled
sudo chown root:www-data sites-available
sudo chmod 775 sites-*
sudo chown root:www-data /var/log/nginx
sudo chmod 775 /var/log/nginx
````

3) Log in as webapp and create a public key. Add it to gitlab/github:

````
su - webapp
ssh-keygen -N ''
cd .ssh
cat id_rsa.pub
````

4) Logged as webapp, install `uv` (it manages the virtualenv and Python 3.10):

````
curl -LsSf https://astral.sh/uv/install.sh | sh
````

5) Clone the repository (If git asks for a password, then step (3) didn't work well)

````
cd /var/webapp
git clone git@git.ibict.br:cgti/hub-i3.git
cd hub-i3
mkdir logs
````

6) Install the dependencies. This creates `/var/webapp/hub-i3/.venv` using exactly
the versions in `uv.lock`, without the dev tools, and installs `gunicorn` (group `prod`):

```
uv sync --frozen --no-dev --group prod
```

The project is already configured to use `eucs_platform.settings.production`
by default (see `src/manage.py` and `src/eucs_platform/wsgi.py`).

7) Log in again as root/sudo to configure NGINX

* copy template nginx.conf and change the site parameters (domain, port, path, etc)

```
cp docs/nginx.conf /etc/nginx/sites-enabled/hub-i3.conf
```

* to test if your new config is ok, run `nginx -t`
* to apply the new config: `sudo systemctl restart nginx`
 
8) PostgreSQL (Logged as root)
 
The database uses PostGIS [*], so some extra instructions are required:

```
sudo apt install postgis postgresql-12-postgis-3 postgresql-12-postgis-3-scripts
```
[*] https://www.vultr.com/docs/install-the-postgis-extension-for-postgresql-on-ubuntu-linux/

```
su - postgres psql ou sudo -u postgres psql
create user eucitizenscience_usr with encrypted password 'mypass';
create database hub_i3 with owner=eucitizenscience_usr;
\connect hub_i3;
create extension postgis;
GRANT ALL on public.spatial_ref_sys TO eucitizenscience_usr;
```

Log in as webapp and test postgres connection:

```
psql -h localhost -U eucitizenscience_usr hub_i3
```

9) Copy `src/eucs_platform/settings/local.sample.reference.env` to `local.env`,
apply your new PostgreSQL database and test the connection:

```
cd /var/webapp/hub-i3/src
cp eucs_platform/settings/local.sample.reference.env eucs_platform/settings/local.env
uv run --no-sync manage.py dbshell
```

10) Test also the django configuration:

```
uv run --no-sync manage.py check
```

11) Import your database or create an empty instance and then apply the model
update, compile the translations and collect the static files:

```
uv run --no-sync manage.py migrate
uv run --no-sync manage.py compilemessages
uv run --no-sync manage.py collectstatic --noinput
```

12) Configure the service that runs gunicorn (logged as root/sudo).

Recommended: **systemd**, using the `docs/hub_i3.service` template. Adjust the
user, paths, port and workers if needed:

```
cp docs/hub_i3.service /etc/systemd/system/hub_i3.service
systemctl daemon-reload
systemctl enable --now hub_i3
systemctl status hub_i3
```

Alternative: **Supervisor** (`apt-get install -y supervisor`), using `docs/supervisor.conf`:

```
cp docs/supervisor.conf /etc/supervisor/conf.d/hub-i3.conf
supervisorctl reread && supervisorctl update
```

13) Cron jobs. `django_cron` only runs when `runcrons` is called, so schedule it
(as webapp, `crontab -e`):

```
*/5 * * * * cd /var/webapp/hub-i3/src && /var/webapp/hub-i3/.venv/bin/python manage.py runcrons >> /var/webapp/hub-i3/logs/cron.log 2>&1
```

14) Finally, test your site on browser and be happy!

## Updating an existing installation

Logged as webapp:

```
cd /var/webapp/hub-i3
git pull
uv sync --frozen --no-dev --group prod
cd src
uv run --no-sync manage.py compilemessages
uv run --no-sync manage.py collectstatic --noinput
# only after backing up the database and reviewing the new migrations:
uv run --no-sync manage.py migrate
```

Then restart the service as root/sudo: `systemctl restart hub_i3`
(or `supervisorctl restart hub-i3` if you use Supervisor).
