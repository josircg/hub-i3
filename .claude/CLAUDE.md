# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

**Hub I3 (HUB 3I)** é uma plataforma web (Django) do IBICT que agrega conteúdo associado a políticas públicas — organizações, projetos, plataformas, recursos (incluindo recursos de treinamento), eventos, notícias (blog) e dossiês — com moderação editorial, tradução de conteúdo de domínio, mapas georreferenciados, boletins/newsletters e API REST. Ver `README.md`.

É um fork da [CÍVIS](https://civis.ibict.br/), que por sua vez é fork da [EU-Citizen.Science platform](https://eu-citizen.science/). **Rebranding em andamento:** o nome do pacote Django (`eucs_platform`) e identificadores de configuração foram preservados por compatibilidade; ainda podem aparecer textos, artes e e-mails antigos (ver `REBRANDING_NOTES.md`). `SITE_NAME` é `'HUB 3I'`. Não renomeie `eucs_platform` nem identificadores herdados.

O projeto Django (`eucs_platform`) e todos os apps vivem em `src/`. **Rode os comandos a partir de `src/`.**

Contexto adicional de produto e estrutura (mapa dos apps, models, rotas) está em `.kiro/steering/` (`product.md`, `structure.md`, `django.md`). Consulte antes de ler o código em detalhe.

## Comandos

O ambiente é gerenciado com **uv** (`pyproject.toml` + `uv.lock`; Python 3.14; venv em `.venv` na raiz do repositório; Django 5.2 LTS, faixa `>=5.2,<5.3`; driver PostgreSQL `psycopg` 3).

```bash
uv sync                              # cria .venv e instala runtime + grupo dev (na raiz do repositório)
cd src

uv run manage.py runserver           # ATENÇÃO: usa settings.production por padrão (ver Configuração)
uv run manage.py migrate
uv run manage.py check
uv run manage.py makemigrations --check --dry-run   # detecta drift entre models e migrations
uv run manage.py runcrons            # executa os CRON_CLASSES (django-cron)

# Testes (test runner do Django) — hoje só existe profiles/tests.py
uv run manage.py test                # toda a suíte
uv run manage.py test profiles       # um app

# Lint (ruff; config em [tool.ruff] no pyproject.toml — line-length=120)
uv run ruff check                    # lint (E, W, F, I, PL)
uv run ruff check --fix              # aplica correções automáticas (inclui ordenação de imports)

# Traduções (LANGUAGE_CODE = pt-br; também en, es)
./translate.sh                       # makemessages --all, utilities/clean.py e compilemessages (via uv run)
```

`pre-commit install` ativa o hook do ruff (`.pre-commit-config.yaml`); para commitar pulando o lint: `git commit --no-verify`. Não há `fabfile.py` neste repositório (o `fabric` está no grupo `dev`, mas sem uso). Não há busca Haystack/Whoosh nem fórum django-machina neste projeto — não procure por `rebuild_index` nem `machina_apps/`.

Deploy em produção: gunicorn (`docs/hub_i3.service`, systemd) atrás de nginx (`docs/install-nginx*.md`; também há `docs/supervisor.conf`). O app é WSGI (`eucs_platform/wsgi.py`) — não usar workers ASGI. **Nunca rode `migrate` em banco de produção sem confirmar com o usuário.**

## Configuração

- Settings em `src/eucs_platform/settings/`: `base.py` (comum) é estendido por `production.py`. O `development.py` é um arquivo **customizado, local e não versionado** (está no `.gitignore`), criado pelo desenvolvedor: **se existir, use-o** em todo comando `manage.py` (`check`, `makemigrations`, `spectacular`, `runserver`…) com `DJANGO_SETTINGS_MODULE=eucs_platform.settings.development`. Sem ele, `manage.py` e `wsgi.py` usam `production` por padrão.
- Configuração sensível (banco, e-mail, chaves, credenciais `VISAO_*`, `FEATURED_MGT`) vem de variáveis de ambiente lidas por `django-environ` a partir de `eucs_platform/settings/local.env`. Copie de `local.sample.reference.env` e edite. **Esse arquivo não é versionado**, e não é relido a quente: alterações exigem reiniciar o servidor.
- Banco: **PostgreSQL + PostGIS** (engine `django.contrib.gis.db.backends.postgis`); requer GDAL/GEOS e a extensão `postgis`. `base.py` tem bloco específico para Windows (`OSGEO4W`). Passo a passo de instalação do banco e das fixtures iniciais em `docs/install-dev.md`.
- O `CRON_CLASSES` base inclui `projects.cron.UpdateVisaoCronJob`, `utilities.cron.CleanExpiredCaptchaCronJob` e `utilities.cron.ClearSessions`; `production.py` acrescenta `contact.cron.SendNewsLetterCronJob` e `accounts.cron.SendNotConfirmedUsersCronJob`.

## Arquitetura

Apps separados por domínio em `src/`, cada um com models/views/urls/admin/templates próprios. Ver `.kiro/steering/structure.md` para o detalhamento. Principais:

- **Domínio**: `organisations`, `projects` (app mais complexo — cadastro, moderação, tradução, editores/convites, integração Visão), `platforms`, `resources`, `dossiers`, `authors`, `events`, `blog`, `digest` (newsletter), `contact`, `pages`.
- **Conta/usuário**: `accounts` e `profiles` sobre `django-authtools` (modelo de usuário por e-mail).
- **Transversal**: `utilities` (tradução genérica via `AbstractTranslatedModel`/`Translation`, `Keyword`, crons, API) e `formats` (formatos de data/número por locale).
- **`eucs_platform/`**: o projeto Django. Contém `settings/`, `urls.py` raiz, `visao.py` (integração com o mapa Visão do IBICT, usada por `projects`), `oidc_provider_settings.py`, `sitemaps.py`, `dashboard.py` (admin-tools), `context_processors.py`, `views.py` (home e páginas institucionais).
- **API / Auth externa**: Django REST Framework + Djoser; o projeto atua como **OpenID Connect provider** (`django-oidc-provider`) e expõe OAuth2 (`django-oauth-toolkit`). Docs de API via `drf-spectacular` (`/schema/`, `/swagger/`, `/redoc/`, só GET e só para logados; valide com `uv run manage.py spectacular --validate`). Subpackages `api/` por app.
- **Moderação**: a maioria dos conteúdos (organizações, projetos, plataformas, recursos, eventos) passa por aprovação. Flags `approved`/`hidden`/`featured` são centrais; em listagens públicas mostre **só** conteúdo aprovado e não oculto (use os managers `approved_*`).

Convenções transversais: formulários com `crispy-forms` (bootstrap3); editores ricos com `django-ckeditor` (`CKEditorWidget`, configs `default` e `frontpage`; o `django-summernote` foi removido); mapas com `django-leaflet` + `geopy`; tarefas agendadas em `CRON_CLASSES` (django-cron); seleção assíncrona com `django-select2`; proteção anti-spam com `django-simple-captcha` e `django-honeypot`. Templates ficam em `src/templates/` (raiz) além das pastas por app.

## Padrões de código

**Consistência acima de tudo.** Ao modificar código existente, siga o estilo e a nomenclatura já usados no arquivo. Não refatore código alheio "de passagem": se notar algo a melhorar, comente ao final da resposta em vez de alterar. Em conflito entre estas regras e o código existente, priorize o código existente e sinalize a inconsistência.

### Idioma, nomes e estilo

- **Código em inglês**: nomes de classes, variáveis, funções, módulos e docstrings. Mensagens voltadas ao usuário final (templates, strings traduzíveis) usam o sistema de traduções do Django (`{% trans %}`, `gettext`).
- `snake_case` para variáveis, funções, métodos, módulos, arquivos, tabelas, colunas e campos de model; `PascalCase` para classes; `UPPER_SNAKE_CASE` para constantes de módulo.
- PEP 8 com **linha até 120 caracteres** (o ruff aplica: `uv run ruff check`).
- **Aspas simples** em strings inline; **aspas duplas** em strings multilinha e em todas as docstrings (`"""..."""`). Se a string contiver aspas simples, use duplas para evitar escape.
- **Nunca** adicione o cabeçalho `# coding: utf-8` (resquício do Python 2); ao editar um arquivo que o tenha, remova-o.

### Imports

Sem `import *`. A ordem e o agrupamento (stdlib → terceiros → locais) são aplicados pelo ruff (regra `I`): rode `uv run ruff check --fix` depois de editar.

### Clean code (com bom senso, não como dogma)

- Nomes revelam intenção (`days_until_due`, não `d`). Uma função faz uma coisa: se a descrição pede "e", são duas funções.
- Funções curtas: idealmente até ~20 linhas; acima de 40, considere extrair.
- Comentários explicam o *porquê*, não o *quê*. Nada de comentário óbvio.
- DRY com moderação: duplicação é melhor que abstração errada; só extraia quando o padrão estiver claro (regra do 3).
- Prefira *early return* a `if`s profundamente aninhados. Números mágicos viram constantes (`MAX_ATTEMPTS = 3`).

### Type hints

Opcionais. Se o arquivo já usa type hints, mantenha o padrão nas funções novas dele. Ao adicionar hints a uma função, hinte **todos** os parâmetros e o retorno, nunca pela metade.

### Docstrings

- **Obrigatórias** em toda classe e função/método público de código novo. Em casos simples, uma linha basta.
- Estilo reST: primeira linha curta no **imperativo** (`Return...`, não `This function returns...`), depois `:param`, `:return` e `:raises` quando aplicável.
- Não documente o óbvio: se o nome do parâmetro já se explica (`project_id`), não escreva `:param project_id: id do projeto`.

```python
def get_visible_projects(language):
    """Return the approved and visible projects translated to a language.

    :param language: language code, e.g. ``pt-br``
    :return: queryset of projects
    :raises ValueError: if the language is not supported
    """
```

### Estrutura de app

- **`managers.py`**: todo `QuerySet`/`Manager` customizado mora aqui (já existe em vários apps), nunca em `models.py`. Em código novo, a lógica de filtro e consulta fica nos QuerySets (ex.: `Project.objects.approved()`); as views chamam métodos do QuerySet e não montam filtros diretamente.
- **`api/`**: subpackage dedicado quando o app expõe REST. Não misture views HTML e views de API no mesmo `views.py`.
- **`tests/`**: pasta com `__init__.py` e um arquivo por módulo testado (`test_models.py`, `test_views.py`, `test_managers.py`). Hoje só existe `profiles/tests.py`; código novo segue a convenção.
- **`apps.py`**: o settings já define `DEFAULT_AUTO_FIELD = "django.db.models.AutoField"`, então não declare `default_auto_field` no `AppConfig` de app novo. `dossiers/apps.py` e `pages/apps.py` usam `BigAutoField` por legado: não os altere.
- Não crie camadas extras (`services.py`, `selectors.py`) sem pedido explícito.

### Ao gerar código

- Antes de criar um padrão novo, procure no projeto um similar e siga-o. Se houver mais de um para o mesmo problema, **pergunte** qual é o atual e qual é legado.
- **Não introduza dependências novas** sem sinalizar explicitamente; declare-as em `pyproject.toml`/`uv.lock`.
- Inclua a docstring obrigatória em view, manager ou model novo, mesmo que simples.
- Diante de ambiguidade (idioma, estrutura, requisito não especificado, vários padrões possíveis, decisão de design não óbvia), **pergunte antes** de prosseguir com suposições silenciosas.

## Design System e UI

Ao criar ou alterar telas, templates HTML, CSS ou JavaScript, siga **`.claude/DESIGN.md`** (Bootstrap 5, fontes Poppins/Inter, Bootstrap Icons, marca Hub I3). **Não o leia em tarefas só de backend** (models, managers, migrations, serializers, lógica sem renderização). Para relatórios HTML da sessão, use a skill `make-report-hub-i3`.

## Git, commits e PRs

### Branches e PRs

- Remote `origin`: `git@github.com:josircg/hub-i3.git`. **`main`** é a produção; **`develop`** é a integração e recebe merge das branches de trabalho **sem PR**.
- Antes de implementar, confira a branch atual (`git branch --show-current`). Se não houver branch para a task, pergunte se deve criá-la.
- Branch nova parte da `main` e o nome **deve ser `release_NNN`** (`NNN` é o número do prefixo dos commits, ex.: `release_27` → `27: ...`).
- Nunca implemente direto na `main` nem em branch de outra task.
- A PR aponta para a `main` e só é aberta depois que o usuário validar a feature.

### Migrations

- **Nunca rode `makemigrations` nem `migrate`** sem pedido explícito. Alterar um model **não** autoriza gerar ou aplicar a migration: informe que ela é necessária, diga qual app está envolvido e aguarde o pedido. `makemigrations --check --dry-run` (só leitura) continua liberado.
- Quando pedido, rode **sempre para um app** (`makemigrations <app>`, `migrate <app>`); se o app não foi informado, pergunte. Sem argumento o comando varre todos os apps.
- Não adicione nem commite arquivos de migration sem pedido. Nunca rode `migrate` em banco de produção sem confirmar.

### Commits

Formato:

```
NNN: <descrição>

- <detalhe da alteração>
- <detalhe da alteração>
```

- `NNN` vem do nome da branch (`release_27` → `27: ...`). Se a branch não tiver número e o usuário não informou um, pergunte; se ele não quiser, siga sem prefixo.
- Use a descrição dada pelo usuário; se não houver, derive-a do diff e só pergunte se a intenção não ficar clara. Nunca invente.
- Subject e linhas da descrição com **no máximo 72 caracteres**; subject no imperativo, claro e em alto nível; descrição em tópicos com as mudanças principais, sem detalhes técnicos desnecessários.
- Mostre a mensagem e **execute o commit só depois que o usuário validar**.
- **Nunca** adicione linhas `Co-Authored-By` nas mensagens de commit ou descrições de PR, nem qualquer assinatura de ferramenta (ex.: `Generated with Claude Code`). A mensagem contém só o conteúdo da task.
- Torne a branch explícita no push (`git push origin <branch>`).
