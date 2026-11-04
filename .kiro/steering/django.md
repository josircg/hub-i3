# Contexto do Projeto — Hub I3

**Hub I3** (HUB 3I) é uma plataforma web para registro e divulgação de
iniciativas e projetos de **Ciência Cidadã na América Latina**, fork do
EU-Citizen.Science (`eucs_platform`), mantida no contexto do IBICT/Civis. Para o
*porquê* do produto, ver `#product`; para a estrutura de apps, ver `#structure`.

## Stack confirmada

- **Python**: 3.10.19 (`requires-python = ">=3.10,<3.11"`). O `.travis.yml`
  legado aponta 3.6.9 e está defasado.
- **Django**: < 4.0 — o pin fica em `../../pyproject.toml` (`django<4.0`).
  NÃO subir para 4.x sem uma migração planejada.
- **Banco**: PostgreSQL com **PostGIS** (engine
  `django.contrib.gis.db.backends.postgis`, via `psycopg2-binary`), com GIS
  (`django.contrib.gis`, `django-leaflet`).
- **Localização/Tradução**: `translate.sh` (ver seção "Traduções").

## Dependências e ambientes (uv)

A gestão de dependências é feita com **`uv`**: `../../pyproject.toml` +
`../../uv.lock`, com `package = false` e Python `>=3.10,<3.11` (3.10.19).

- `[project].dependencies` — runtime comum a todos os ambientes (Django, DRF,
  leaflet, etc.), com os mesmos pins dos antigos `requirements/base.txt`, mais
  `setuptools<81` (ver "Dívida técnica").
- `[dependency-groups].dev` — ferramentas de dev (`django-debug-toolbar`,
  `flake8`, `pre-commit`, `fabric`, `werkzeug`, `pytz`, `six`, `invoke`, etc.).
- `[dependency-groups].prod` — **só produção**: `gunicorn` e `django[argon2]`.
  Não é instalado por padrão. Dependência só de produção entra aqui
  (`uv add --group prod <pacote>`), nunca em `[project].dependencies`.
- `../../requirements/*.txt` e `../../requirements.txt` — **legado** (pip),
  mantidos apenas por compatibilidade com o CI antigo (`.travis.yml`). A fonte
  canônica é o `pyproject.toml`; os `.txt` não são mais atualizados em paralelo
  a cada mudança de dependência, exceto a remoção do fórum.

Instalação:

```
uv sync                 # dev: runtime + grupo dev (sem gunicorn)
uv sync --group prod    # servidor: adiciona o gunicorn ao .venv
```

Execução de comandos Django (a partir de `src/`):

```
uv run manage.py check
```

Após editar o `pyproject.toml`, regenere o lock com `uv lock` (na raiz).

## Módulos de settings

Os settings ficam em `../../src/eucs_platform/settings`:

- `base.py` — configuração comum a todos os ambientes; lê o `local.env` via
  `django-environ`.
- `production.py` — herda de `base`, template cacheado, Argon2 como password
  hasher, logging em arquivo, e estende `CRON_CLASSES` com
  `SendNewsLetterCronJob` e `SendNotConfirmedUsersCronJob`.
- `local.env` — variáveis de ambiente (SECRET_KEY, banco, SMTP, chaves de API,
  `VISAO_*`). **NÃO é versionado** (git-ignored); há `local.sample.env` /
  `local.sample.reference.env` de referência.

**IMPORTANTE — settings:** hoje só existem `base.py` e `production.py` (não há
`development.py`). O `manage.py` usa `eucs_platform.settings.production` como
default (o comentário no arquivo diz "development", mas o código seta
production). Portanto todo comando `manage.py` carrega **production**; controle
o comportamento (ex.: `DEBUG`) pelo `local.env`.

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

- **`django<4.0`** (`../../pyproject.toml`): migrar para Django 4.x é um
  projeto à parte (mexe em várias dependências, ver abaixo).
- **`django-rest-swagger` (2.2.0)**: pacote morto, provavelmente incompatível
  com Django 4. Candidato a remoção/substituição por `drf-yasg` na migração.
- **Pin `setuptools<81`** (`../../pyproject.toml`): `drf-yasg 1.21.7` e
  `django-countries 7.5.1` ainda importam `pkg_resources` (o `django-authtools`
  já foi para 2.1.0 e não depende mais dele),
  removido do setuptools 81+. Com `uv` o `setuptools` não vem por padrão, então
  ele foi adicionado ao runtime. Remover o pin está acoplado à migração Django
  4.x.
- **`requirements/*.txt` legados** ainda existem ao lado do `pyproject.toml`;
  remover quando o CI deixar de usá-los.

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
