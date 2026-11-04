Tutorial de Instalação de um servidor do Hub I3 para ambiente de produção:

Caminhos usados abaixo (ajuste ao seu servidor): aplicação em `/var/webapp/hub-i3`,
usuário `webapp`, gunicorn escutando em `127.0.0.1:5000`.

1) Instalação do NGINX e pacotes do sistema (logado como root) e configuração do timezone:

````
apt-get install -y nginx build-essential libssl-dev python3-dev libxml2-dev git libfreetype6 libfreetype6-dev libpq-dev libjpeg-dev zlib1g-dev gettext gdal-bin libgdal-dev
dpkg-reconfigure tzdata
````

(`gettext` é exigido pelo `compilemessages`; `gdal-bin`/`libgdal-dev` pelo GeoDjango.)

2) Criação do usuário webapp e permissões de uso (logado como root)

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

3) Criação da chave pública para enviar para o gitlab

````
su - webapp
ssh-keygen -N ''
cd .ssh
cat id_rsa.pub
````

4) Ainda logado como webapp, instalar o `uv` (ele gerencia o virtualenv e o Python 3.10):

````
curl -LsSf https://astral.sh/uv/install.sh | sh
````

5) Clonar o repositório (Não é necessário nenhuma senha pois a chave já foi incluída no gitlab)

````
cd /var/webapp
git clone git@git.ibict.br:cgti/hub-i3.git
cd hub-i3
mkdir logs
````

6) Instalar as bibliotecas do python. Isso cria `/var/webapp/hub-i3/.venv` com as
versões exatas do `uv.lock`, sem as ferramentas de desenvolvimento, e instala o
`gunicorn` (grupo `prod`):

```
uv sync --frozen --no-dev --group prod
```

O projeto já aponta para `eucs_platform.settings.production` por padrão (ver
`src/manage.py` e `src/eucs_platform/wsgi.py`).

7) Novamente logado como root/sudo, configurar o NGINX

* copiar o arquivo nginx.conf alterando os parâmetros necessários

```
cp docs/nginx.conf /etc/nginx/sites-enabled/hub-i3.conf
```

* para testar se a configuração foi bem sucedida, executar: `nginx -t`
* para aplicar os ajustes: `sudo systemctl restart nginx`

8) PostgreSQL (Logado como superuser)
 
O Banco de Dados utiliza PostGIS [*], assim algumas instruções extras devem ser executadas: 

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

Teste de Conexão no postgres (já logado como webapp):

```
psql -h localhost -U eucitizenscience_usr hub_i3
```

9) Copiar o `local.env`, configurar o banco e testar a conexão e o Django:

```
cd /var/webapp/hub-i3/src
cp eucs_platform/settings/local.sample.reference.env eucs_platform/settings/local.env
uv run --no-sync manage.py dbshell
uv run --no-sync manage.py check
```

10) Criar as tabelas, compilar as traduções e coletar os arquivos estáticos:

```
uv run --no-sync manage.py migrate
uv run --no-sync manage.py compilemessages
uv run --no-sync manage.py collectstatic --noinput
```

11) Configurar o serviço que executa o gunicorn (logado como root/sudo).

Recomendado: **systemd**, usando o modelo `docs/hub_i3.service`. Ajuste usuário,
caminhos, porta e workers se necessário:

```
cp docs/hub_i3.service /etc/systemd/system/hub_i3.service
systemctl daemon-reload
systemctl enable --now hub_i3
systemctl status hub_i3
```

Alternativa: **Supervisor** (`apt-get install -y supervisor`), usando `docs/supervisor.conf`:

```
cp docs/supervisor.conf /etc/supervisor/conf.d/hub-i3.conf
supervisorctl reread && supervisorctl update
```

12) Cron jobs. O `django_cron` só executa quando o `runcrons` é chamado, então
agende-o (como webapp, `crontab -e`):

```
*/5 * * * * cd /var/webapp/hub-i3/src && /var/webapp/hub-i3/.venv/bin/python manage.py runcrons >> /var/webapp/hub-i3/logs/cron.log 2>&1
```

## Atualização de uma instalação existente

Logado como webapp:

```
cd /var/webapp/hub-i3
git pull
uv sync --frozen --no-dev --group prod
cd src
uv run --no-sync manage.py compilemessages
uv run --no-sync manage.py collectstatic --noinput
# somente após backup do banco e revisão das novas migrations:
uv run --no-sync manage.py migrate
```

Depois reinicie o serviço como root/sudo: `systemctl restart hub_i3`
(ou `supervisorctl restart hub-i3` se usar o Supervisor).
