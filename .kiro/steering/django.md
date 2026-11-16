# Contexto do Projeto — Hub I3

**Hub I3** (HUB 3I) é uma plataforma web para registro e divulgação de
iniciativas e projetos de **Ciência Cidadã na América Latina**, fork do
EU-Citizen.Science (`eucs_platform`), mantida no contexto do IBICT/Civis. Para o
*porquê* do produto, ver `#product`; para a estrutura de apps, ver `#structure`.

## Stack confirmada

- **Python**: 3.14 (`requires-python = ">=3.14,<3.15"`).
- **Django**: 5.2 LTS — a faixa fica em `../../pyproject.toml`
  (`django[argon2]>=5.2,<5.3`).
- **Banco**: PostgreSQL com **PostGIS** (engine
  `django.contrib.gis.db.backends.postgis`, via `psycopg` 3), com GIS
  (`django.contrib.gis`, `django-leaflet`).
- **Localização/Tradução**: `translate.sh` (ver seção "Traduções").

## Dependências e ambientes (uv)

A gestão de dependências é feita com **`uv`**: `../../pyproject.toml` +
`../../uv.lock`, com `package = false` e Python `>=3.14,<3.15`.

- `[project].dependencies` — runtime comum a todos os ambientes (Django, DRF,
  leaflet, etc.), com versões mínimas (`>=`); o `uv.lock` fixa as versões exatas.
  O `django-cron` vem do fork `jorenham` via `[tool.uv.sources]`.
- `[dependency-groups].dev` — ferramentas de dev (`django-debug-toolbar`,
  `ruff`, `pre-commit`, `fabric`, `werkzeug`).
- `[dependency-groups].prod` — **só produção**: `gunicorn`.
  Não é instalado por padrão. Dependência só de produção entra aqui
  (`uv add --group prod <pacote>`), nunca em `[project].dependencies`.
- Os antigos `requirements/*.txt` e `requirements.txt` (pip) foram removidos; a fonte
  única de dependências é o `pyproject.toml` (+ `uv.lock`).

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

**IMPORTANTE — settings:** o repositório versiona só `base.py` e `production.py`.
O `development.py` é um arquivo customizado e local (git-ignored), criado por cada
desenvolvedor: se existir, use-o via
`DJANGO_SETTINGS_MODULE=eucs_platform.settings.development`. O `manage.py` usa
`eucs_platform.settings.production` como default (o comentário no arquivo diz
"development", mas o código seta production). Sem o `development.py`, todo comando
`manage.py` carrega **production**; controle o comportamento (ex.: `DEBUG`) pelo
`local.env`.

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
- **API/REST**: `djangorestframework`, `drf-spectacular` (OpenAPI em
  `/schema/`, `/swagger/` e `/redoc/`, só GET e só para logados). Auth via token/sessão. OAuth/OIDC via `django-oauth-toolkit` e
  `django-oidc-provider`.
- **Mapas**: usa **apenas django-leaflet** (client-side). `LEAFLET_CONFIG` em
  `base.py` (centro em `(-15.125159, -57.636719)`, zoom 3 — visão América do
  Sul), usado via `{% leaflet_map %}` nas páginas de organização/projeto.
- **Editores de texto**: `django-ckeditor` (+ `ckeditor_uploader`).
- **Integração Visão**: `eucs_platform/visao.py` (geoserver IBICT), configurada
  por envs `VISAO_*`; consumida por `projects` (cron `UpdateVisaoCronJob`,
  command `populate_visao`).
- **Outros**: `django-countries` (`CountryField`, com override de `FK` →
  "Falkland Islands"), `django-crispy-forms` + `crispy-bootstrap3`,
  `django-simple-captcha`, `django-honeypot`, `django-cookie-law`,
  `django-cleanup`, `django-select2`, `django-cron`.

## Dívida técnica conhecida

- **`django-ckeditor<6.7`** (`../../pyproject.toml`): faixa limitada no `pyproject.toml`; revisar a cada
  atualização do Django.
- **Documentação da API**: `manage.py spectacular --validate` ainda aponta o campo GIS
  `projects.Project.projectGeographicLocation` (documentado como `string`), dois `OrganisationSerializer` com o
  mesmo nome (em `projects/api` e `organisations/api`) e nomes duplicados de enum (`CountriesEnum`, `InLanguageEnum`).
- **GDAL do sistema**: com GDAL < 3.9 o `check` mostra o aviso `gis.W001`.

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

- Repositório: `github.com/josircg/hub-i3` (remote `origin`).
- **`main`**: branch de produção e padrão.
- **`develop`**: branch de integração. Recebe merge direto das branches `release_NNN`,
  **sem PR**.
- **Novas branches partem da `main`** e o nome **deve ser `release_NNN`** (`NNN` é o número
  usado como prefixo dos commits, ex.: `27: ...`):

  ```
  git fetch origin
  git switch -c release_NNN origin/main
  ```

- A **PR é aberta para a `main`** só depois que o usuário validar a feature.

## Fluxo de trabalho com specs

Para features não-triviais, use o template de spec deste projeto:
`#django-spec-template` (em `.kiro/steering/django-spec-template.md`).

Nunca aplique `migrate` em banco de produção sem o usuário confirmar.
