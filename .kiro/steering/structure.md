# Estrutura da Aplicação — Hub I3

Mapa dos apps e do projeto `eucs_platform`. Reflete o código real em `../../src`
(revisado em 2026-11-03). Use como referência de "onde as coisas estão" antes de
ler o código em detalhe.

> Stack, comandos e armadilhas de ambiente ficam em `#django`. Produto e domínio
> em `#product`. Este arquivo cobre **estrutura**: apps, responsabilidades,
> models, rotas e dependências.

## Projeto `eucs_platform`

O projeto Django fica em `../../src/eucs_platform` (nome herdado do fork
EU-Citizen.Science; preservado por compatibilidade). Não é um app de domínio — é
a "cola": settings, urls raiz, views da home, dashboard do admin e utilitários.

- `settings/` — `base.py` (comum, lê `local.env`), `development.py`,
  `production.py`. `manage.py` usa **production** como default.
- `urls.py` — urls raiz (ver "Roteamento" abaixo). Define a API "CÍVIS API"
  (drf-yasg) e o admin com título "Cívis Administração".
- `views.py` — views da home e páginas institucionais (function-based). A
  `home` agrega conteúdo de quase todos os apps.
- `dashboard.py` — dashboards customizados do `django-admin-tools`.
- `cron.py` — cron jobs (`django_cron`).
- `context_processors.py`, `logger.py`, `oidc_provider_settings.py`,
  `sitemaps.py`, `utils.py`, `visao.py` (integração "Visão"/geoserver IBICT,
  usada por `projects`), `wsgi.py`.

## Apps locais

Todos em `../../src`. Ordem aproximada de dependência (folha → raiz):
`utilities`, `authors` → `organisations` → `platforms`/`projects` →
`resources` → `blog`/`events`/`digest`/`dossiers`/`contact`/`pages`/`profiles`.
Além desses, há o módulo **`formats`**.

### Núcleo de domínio

- **organisations** — organizações atuantes em ciência cidadã (cadastro,
  moderação, permissões de edição, mapa leaflet). Models: `Organisation`
  (PointField GIS + lat/long Decimal, FK `orgType`, `creator`, `approved`),
  `OrganisationType` (traduzível), `OrganisationPermission`. Views FBV + DRF em
  `api/`. Consumido por `platforms`, `projects`, `resources`, `profiles`,
  `dossiers`.

- **projects** — projetos de ciência cidadã / iniciativas. **App mais
  complexo**: cadastro, moderação, destaque, tradução de conteúdo, permissões/
  convites de editores, estatísticas, download. Models principais: `Project`
  (MultiPolygonField GIS, M2M `organisation`/`keywords`/`editors`/..., FK
  `mainOrganisation`, `status`), além de `Status`/`Topic`/`ParticipationTask`
  (traduzíveis), `Keyword`, `FundingBody`, `ProjectPermission`,
  `FollowedProjects`. Views FBV + DRF em `api/` (ViewSets via `DefaultRouter`).
  Depende de `organisations`, `utilities`. Management command:
  `populate_visao`. Cron `UpdateVisaoCronJob`. Mapa leaflet em
  `project.html`/`project_form.html`.

- **platforms** — plataformas de ciência cidadã. Cadastro/moderação com tradução
  de conteúdo. Views FBV + DRF em `api/`. Depende de `organisations`.

- **resources** — recursos e **recursos de treinamento** (publicações,
  materiais) com categorias/temas/audiência, bookmarks, agrupamentos curados,
  moderação e download. Models: `Resource` (M2M `authors`/`organisation`/
  `project`/`keywords`/`theme`, FK `category`, flag `isTrainingResource`),
  `TrainingResource` (herança), `Theme`/`Audience`/`Category` (traduzíveis),
  `ResourceGroup`, `BookmarkedResources`, `ResourcePermission`. Views FBV +
  DRF em `api/`. Depende de `authors`, `organisations`, `projects`,
  `utilities`.

- **authors** — catálogo simples de autores de recursos. Model único: `Author`.
  **Sem views/urls** (app só de dados). Consumido por `resources`.

### Conteúdo e comunicação

- **blog** — notícias/posts do portal. Model: `Post` (slug, FK `author`→user,
  `sticky`, `status`). View CBV `PostList` + FBV `post_detail`. Templatetags em
  `my_tags.py`.

- **dossiers** — **coleções curadas** que agregam conteúdo de vários apps em
  torno de um tema. Models: `Dossier` (título/resumo/descrição traduzíveis,
  `status` Draft/Published/Not Published, imagem, M2M `keywords`→
  `utilities.Keyword`, M2M `organisations`→`organisations.Organisation`, M2M
  `users`, FK opcional `post`→`blog.Post`),
  `DossierCurator` (curadores), `DossierObject` (itens via **GenericForeignKey**
  — blog, resources, projects, etc., com `order`, `approved` por item e
  `creator`), `DossierTranslation` (tradução própria do dossiê). Views CBV + FBV.
  Tem `signals.py`, `managers.py` (querysets com `with_translations()`).
  Depende de `blog`, `organisations`, `resources`, `projects`, `utilities`.

- **events** — eventos (criação, edição, moderação, destaque, listagem
  ongoing/upcoming). Model: `Event` (FK `creator`, datas, `approved`,
  `featured`). Manager com `ongoing_events()`/`upcoming_events()` (usados na
  home). Views FBV. Tem `signals.py`.

- **digest** — boletim/agregador de conteúdo periódico. Views FBV. Incluído na
  raiz com prefixo vazio.

- **contact** — contato, inscrição de assinantes e envio/gestão de newsletters.
  Models: `Subscriber`, `Newsletter` (FK `blog`→`blog.Post`, FK
  `featured_resource`→`resources.Resource`). Views FBV (+1 CBV
  `NewsletterList`). Management command: `send_newsletter`. Cron
  `SendNewsLetterCronJob` (só produção). Depende de `blog`, `resources`.

- **pages** — páginas institucionais por slug. Incluído **por último** na raiz
  (catch-all). Views CBV.

### Usuário e conta

- **accounts** — autenticação e ciclo de vida da conta (login, logout, signup,
  ativação por e-mail, reset de senha, exclusão). Model: `ActivationTask`.
  Middleware `BruteForceProtectionMiddleware`. Views CBV sobre `authtools`/
  `braces` + classes de e-mail `djoser`. Rotas sob `app_name = "accounts"`.
  Cron `SendNotConfirmedUsersCronJob` (só produção).

- **profiles** — perfil público/privado do usuário, área "me" (submissões,
  bookmarks, permissões de projeto, privacidade) e equipe. Models:
  `Profile`/`BaseProfile` (OneToOne user, M2M `interestAreas`/`organisation`),
  `InterestArea`. Views CBV + FBV. **Incluído com prefixo `users/`**. Único app
  com `tests.py` de conteúdo (é o que o CI roda). Tem `signals.py`.

### Infraestrutura interna

- **utilities** — utilitários transversais. Framework de **tradução genérica**
  via ContentType: `Translation` + `AbstractTranslatedModel` (base abstrata
  usada por organisations, projects, resources, platforms). Também `Keyword`
  (usado por projects e dossiers), `renderers.CSVRenderer` (DRF),
  `inspectors.SwaggerAutoSchema`, ações de admin, limpeza de arquivos
  (`clean.py`), templatetags compartilhadas, crons (`CleanExpiredCaptcha`,
  `ClearSessions`). **Sem views/urls** — é biblioteca interna. Tem `signals.py`.

- **formats** — módulo de formatos locais do Django (`FORMAT_MODULE_PATH =
  'formats'`), com `pt_BR/` (formatação de data/número pt-BR). Não é app de
  domínio.

> **Nota:** não existe app `diseases`. Versões anteriores da documentação
> citavam-no por engano.

## Roteamento (urls raiz — `eucs_platform/urls.py`)

- A home (`/`) está sob `i18n_patterns`.
- Maioria dos apps incluída com **prefixo vazio** (`path("", include(...))`):
  contact, accounts, organisations, projects, resources, blog, events, digest,
  platforms, **dossiers** e **pages por último** (catch-all por slug).
- Exceção: **profiles** sob `users/`.
- Views raiz: `home` (`/`), `all/`, `curated/`, `country_list/`, `imprint/`,
  `terms/`, `privacy/`, `guide/`, `moderation/`, `criteria/`,
  `moderation_quality_criteria`, `translations/`, `development/`, `about/`,
  `setlanguage/`, `home_autocomplete/`.
- Integrações na raiz: `admin/`, `admin_tools/`, `select2/`, `captcha/`,
  `summernote/`, `ckeditor/`, `o/` (oauth2), `openid/`
  (oidc), `api-auth/`, `api/auth/` (djoser + authtoken), `swagger`/`redoc`
  (drf-yasg, login-only), `i18n/`, `sitemap.xml`, `robots.txt`, páginas de erro
  (`500/`, `403/`, `coming_soon/`).

## Convenções

- **Views**: site principal usa **function-based (FBV)**; `accounts`,
  `profiles`, `blog` (lista), `pages`, `dossiers` usam **class-based (CBV)** em
  parte; as subpastas `api/` usam **DRF** (APIView + ViewSet + `DefaultRouter`).
- **Traduções de conteúdo**: via `utilities.AbstractTranslatedModel` /
  `Translation` (GenericForeignKey/ContentType). `dossiers` tem seu próprio
  `DossierTranslation`. Não é i18n de template.
- **GIS**: PostGIS. `PointField` em `organisations`, `MultiPolygonField` em
  `projects`, com `latitude`/`longitude` Decimal espelhados.
- **Mapas**: **100% django-leaflet client-side** via `{% leaflet_map %}` nos
  templates de `organisations` e `projects`. Config em `LEAFLET_CONFIG`
  (`base.py`). Não há mapa server-side neste repositório.
- **Moderação**: vários models têm `approved`/`hidden`/`featured`; a home só
  mostra conteúdo aprovado/não oculto (managers `approved_*`). `DossierObject`
  tem `approved` por item.
- **Autocomplete**: cada app grande expõe um helper `get<App>Autocomplete`
  consumido por `home_autocomplete`.

## Onde encontrar coisas (quick map)

- `signals.py`: events, organisations, projects, resources, profiles, dossiers,
  utilities.
- `api/` (DRF): organisations, platforms, projects, resources.
- `management/commands/`: contact (`send_newsletter`), projects
  (`populate_visao`).
- `templatetags/`: utilities, projects, blog, organisations, dossiers.
- `fixtures/`: projects (`topics`, `status`), resources (`categories`,
  `themes`, `audiences`).
- Testes: só `profiles/tests.py` (rodado pelo CI).
