# Hub I3 Installation for developers

## Requirements

    sudo apt install python3-pip libpq-dev gettext python-is-python3 libjpeg-dev zlib1g-dev gdal-bin libgdal-dev

Install `uv` (dependency and virtualenv manager used by this project):

    curl -LsSf https://astral.sh/uv/install.sh | sh

## Configure postgres

1) If you are going to install postgresql in the app server:

   ```
   sudo apt install postgresql postgis postgresql-12-postgis-3
   ```

Or for postgresql 14 or superior:

   ```
   sudo apt install postgresql postgis
   ```
   

2) Open psql console:
```
create database eucitizenscience;
create user eucitizenscience_usr with password 'XXX';
grant all on database eucitizenscience to eucitizenscience_usr;
\connect eucitizenscience;
create extension postgis;
```
## Python Installation

1) In source directory:

```
git clone git@git.ibict.br:cgti/hub-i3.git
cd hub-i3
uv sync
cd src
cp eucs_platform/settings/local.sample.reference.env eucs_platform/settings/local.env
```

`uv sync` creates the `.venv` (Python 3.10.19, downloaded automatically by uv
if not present) and installs runtime + the `dev` dependency group (debug
toolbar, flake8, pre-commit, etc.), without `gunicorn`.

2) Edit local.env with database and email configuration and test your configuration

```
uv run manage.py check
```

3) Install flake8 pre-commit hook (optional) to check PEP8 before commit. 
Run `pre-commit install` to set up the git hook scripts (see .pre-commit-config.yaml):

```
uv run pre-commit install
```

To commit without flake8 verification just run `commit` with `--no-verify` flag:

```
git commit -m "feat: pre-commit hooks" --no-verify
```

4) To install a empty database, run: 

```
uv run manage.py migrate
uv run manage.py loaddata projects/fixtures/topics.json
uv run manage.py loaddata projects/fixtures/status.json
uv run manage.py loaddata projects/fixtures/participationtasks.json
uv run manage.py loaddata projects/fixtures/geographicextend.json
uv run manage.py loaddata resources/fixtures/categories.json
uv run manage.py loaddata resources/fixtures/themes.json
uv run manage.py loaddata organisations/fixtures/organisation_types.json
```

5) To restore a existing database:

```
psql < base.sql
uv run manage.py migrate
```

## Launch
```
uv run manage.py runserver
```

## Cron jobs commands [4]
```
uv run manage.py runcrons
```

## Config crontab
```
crontab -e
*/5 * * * * cd your-project-path/src && your-project-path/.venv/bin/python manage.py runcrons > your-log-path/cronjob.log 2>&1
```

Calling the `.venv` interpreter directly avoids `uv` having to be on cron's `PATH`.

[1]: https://eu-citizen.science/
[2]: https://www.python.org/
[3]: https://www.djangoproject.com/
[4]: https://pypi.org/project/django-crontab/ 
[5]: https://flake8.pycqa.org/en/latest/user/using-hooks.html
[6]: https://pre-commit.com/#pre-commit-configyaml---hooks
