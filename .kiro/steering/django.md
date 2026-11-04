# Contexto do Projeto — Hub I3

**Hub I3** (HUB 3I) é uma plataforma web para registro e divulgação de
iniciativas e projetos de **Ciência Cidadã na América Latina**, fork do
EU-Citizen.Science (`eucs_platform`), mantida no contexto do IBICT/Civis. Para o
*porquê* do produto, ver `#product`; para a estrutura de apps, ver `#structure`.

## Stack confirmada

- **Python**: 3.x (venv). O `.travis.yml` legado aponta 3.6.9, mas o alvo atual
  é mais recente; confirme a versão do venv local antes de assumir.
- **Django**: < 4.0 — o pin fica em `../../requirements/base.txt` (`django<4.0`).
  NÃO subir para 4.x sem uma migração planejada.
- **Banco**: PostgreSQL com **PostGIS** (engine
  `django.contrib.gis.db.backends.postgis`, via `psycopg2-binary`), com GIS
  (`django.contrib.gis`, `django-leaflet`).
- **Localização/Tradução**: `translate.sh` (ver seção "Traduções").

## Dependências e ambientes (pip / requirements)

A gestão de dependências é feita com **pip + arquivos `requirements/*.txt`**
(não há `pyproject.toml` nem `uv.lock` no repositório).

- `../../requirements/base.txt` — runtime comum a todos os ambientes (Django,
  DRF, leaflet, etc.).
- `../../requirements/development.txt` — `-r base.txt` + ferramentas de dev
  (`django-debug-toolbar`, `flake8`, `pre-commit`, `fabric`, `werkzeug`).
- `../../requirements/production.txt` — `-r base.txt` + `gunicorn` e
  `django[argon2]`.
- `../../requirements.txt` (raiz) — `-r requirements/development.txt` + extras
  (`pytz`, `six`, `invoke`, `werkzeug`). É o alvo usado pelo CI (`.travis.yml`:
  `pip3 install -r requirements.txt`).

Instalação típica (dev):

```
pip install -r requirements.txt
```

Instalação em produção:

```
pip install -r requirements/production.txt
```

> **Intenção futura (ainda NÃO implementada):** há interesse em migrar a gestão
> de dependências para **`uv`** (`pyproject.toml` + `uv.lock`, com grupos
> `dev`/`prod`). Hoje isso **não existe** no repositório — a fonte canônica são
> os `requirements/*.txt`. Só trate o fluxo `uv` como real quando o
> `pyproject.toml` existir de fato.

## Módulos de settings

Os settings ficam em `../../src/eucs_platform/settings`:

- `base.py` — configuração comum a todos os ambientes; lê o `local.env` via
  `django-environ`.
- `development.py` — herda de `base`, adiciona debug toolbar, logging, etc.
- `production.py` — herda de `base`, template cacheado, Argon2 como password
  hasher, logging em arquivo, e estende `CRON_CLASSES` com
  `SendNewsLetterCronJob` e `SendNotConfirmedUsersCronJob`.
- `local.env` — variáveis de ambiente (SECRET_KEY, banco, SMTP, chaves de API,
  `VISAO_*`). **NÃO é versionado** (git-ignored); há `local.sample.env` /
  `local.sample.reference.env` de referência.

**IMPORTANTE — settings padrão:** o `manage.py` usa
`eucs_platform.settings.production` como default (o comentário no arquivo diz
"development" mas o código seta production). Ou seja, rodar
`python manage.py runserver` sem exportar `DJANGO_SETTINGS_MODULE` carrega
**production**, não development. Para rodar em development, exporte:

```
DJANGO_SETTINGS_MODULE=eucs_platform.settings.development python manage.py <cmd>
```

## Como rodar comandos

Todo o código fica em `../../src`. Comandos de `manage.py` rodam a partir de `src/`.

```
cd src
python manage.py check
```

### Comandos de verificação (sempre nesta ordem após mudanças)

1. `python manage.py check` — valida configuração e apps.
2. `python manage.py makemigrations --check --dry-run` — garante que o modelo em
   código bate com as migrations. Se acusar mudanças, há drift.
3. Testes do app afetado (quando existirem).
4. **Traduções** — ao alterar strings traduzíveis (templates, `_()`/`gettext`,
   `verbose_name`), rodar o `translate.sh` (ver abaixo). O passo que ativa as
   traduções é o `compilemessages` (gera os `.mo`).

### Testes

A suíte é mínima — hoje só `profiles/tests.py` tem conteúdo (é o que o CI roda:
`python manage.py test profiles`). Ao criar testes, use o runner padrão do
Django (`python manage.py test <app>`).

### Traduções

Idiomas: **pt-br** (padrão), **es**, **en**. As mensagens de template/código
(`gettext`/`_()`/`verbose_name`) vivem em `src/locale/<lang>/LC_MESSAGES/`
(`django.po` fonte → `django.mo` compilado). O `.mo` é o que o Django carrega em
runtime; **editar o `.po` sem compilar não muda nada no site**.

Use o script `../../src/translate.sh`, que roda os passos na ordem certa a
partir de `../../src`:

1. `manage.py makemessages --all --no-location` — extrai strings para os `.po`.
2. `utilities/clean.py` — limpeza dos `.po`.
3. `manage.py compilemessages` — compila os `.po` em `.mo` (ativa as traduções).

```
cd src
bash translate.sh
```

**Requisito de sistema — GNU gettext:** `makemessages`/`compilemessages`
dependem dos binários do `gettext` do SO (`msgfmt`, `msguniq`, `xgettext`), que
**não** vêm pelo pip. Instale no SO (uma vez por máquina):

```
# Debian/Ubuntu:
sudo apt-get update && sudo apt-get install -y gettext
```

**Dev vs. deploy:** os `.mo` são **git-ignored** (`*.mo` no `../../.gitignore`),
então precisam ser gerados onde a app roda.
- **Desenvolvimento**: rode o `translate.sh` completo ao alterar texto visível;
  revise os `.po` (traduza `es`/`en`) e rode de novo.
- **Deploy/servidor**: rode apenas `python manage.py compilemessages` sobre os
  `.po` versionados — **não** rode o `translate.sh` inteiro (o `makemessages`
  reescreveria os `.po`). Exige o `gettext` instalado no servidor.

## Apps locais

Ver `#structure` (`.kiro/steering/structure.md`) para o mapa detalhado. A lista
real em `INSTALLED_APPS` inclui: `profiles`, `accounts`, `projects`,
`resources`, `digest`, `dossiers`, `platforms`, `blog`, `authors`, `contact`,
`events`, `pages`, `organisations`, `utilities`, além do módulo de formatos locais
(`formats`, via `FORMAT_MODULE_PATH`). `eucs_platform` é o projeto (settings,
urls, views raiz, dashboard do admin).

> **Nota:** não existe app `diseases` neste repositório. Versões anteriores da
> documentação citavam esse app por engano.

## Bibliotecas e integrações relevantes

- **Autenticação**: modelo de usuário customizado via `django-authtools`
  (`AUTH_USER_MODEL = "authtools.User"`). Proteção contra brute force via
  `accounts.middleware.BruteForceProtectionMiddleware` (`BRUTE_FORCE_THRESHOLD`,
  `BRUTE_FORCE_TIMEOUT`).
- **Admin**: `django-admin-tools` (dashboard customizado em
  `eucs_platform/dashboard.py`). No Windows (`os.name == 'nt'`) o `admin_tools`
  é removido do `INSTALLED_APPS` em runtime.
- **API/REST**: `djangorestframework`, `django-rest-swagger` (pacote morto),
  `drf-yasg`. Auth via token/sessão. OAuth/OIDC via `django-oauth-toolkit` e
  `django-oidc-provider`.
- **Mapas**: usa **apenas django-leaflet** (client-side). `LEAFLET_CONFIG` em
  `base.py` (centro em `(-15.125159, -57.636719)`, zoom 3 — visão América do
  Sul), usado via `{% leaflet_map %}` nas páginas de organização/projeto.
- **Editores de texto**: `django-ckeditor` (+ `ckeditor_uploader`) e
  `django-summernote`.
- **Integração Visão**: `eucs_platform/visao.py` (geoserver IBICT), configurada
  por envs `VISAO_*`; consumida por `projects` (cron `UpdateVisaoCronJob`,
  command `populate_visao`).
- **Outros**: `django-countries` (`CountryField`, com override de `FK` →
  "Falkland Islands"), `django-crispy-forms` + `crispy-bootstrap3`,
  `django-simple-captcha`, `django-honeypot`, `django-cookie-law`,
  `django-cleanup`, `django-select2`, `django-cron`.

## Dívida técnica conhecida

- **`django<4.0`** (`../../requirements/base.txt`): migrar para Django 4.x é um
  projeto à parte (mexe em várias dependências, ver abaixo).
- **`django-rest-swagger` (2.2.0)**: pacote morto, provavelmente incompatível
  com Django 4. Candidato a remoção/substituição por `drf-yasg` na migração.
- **Intenção de migrar para `uv`** (ver acima) — ainda não iniciada.

## Armadilhas de ambiente

- Todo o projeto está em `../../src`. Comandos de `manage.py` rodam a partir dali.
- O `runserver` default carrega **production** settings (ver acima).
- O `local.env` não é lido a quente: alterações nele exigem **reiniciar** o
  `runserver` (o autoreload do Django reage a `.py`, não a `.env`).
- **Drift de migrations**: edições em models sem rodar `makemigrations` deixam o
  schema em código divergente das migrations. Sempre rode
  `makemigrations --check --dry-run`.
- **GDAL/GEOS no Windows**: `base.py` tem bloco específico que configura
  `OSGEO4W` quando `os.name == 'nt'`.

## Remote git

- Repositório: `github.com/josircg/hubi3` (remote `origin`).
- **`master`**: branch de produção e padrão. Protegida: mudanças por PR com 1
  aprovação.
- **`dev`**: branch de integração, criada a partir da `master`. Protegida: PR
  com 1 aprovação, sem exclusão e sem force push.
- **Novas branches devem partir do `dev`**, e as PRs devem ter o `dev` como base:

  ```
  git fetch origin
  git switch -c issueNNN origin/dev
  ```

- O `dev` é levado para a `master` nas publicações. Hotfixes diretos na `master`
  devem ser levados de volta ao `dev` logo em seguida.

## Fluxo de trabalho com specs

Para features não-triviais, use o template de spec deste projeto:
`#django-spec-template` (em `.kiro/steering/django-spec-template.md`).

Nunca aplique `migrate` em banco de produção sem o usuário confirmar.
