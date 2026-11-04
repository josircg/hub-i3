# Requisitos — Hub I3 (HUB 3I / Cívis)

## Contexto

O **Hub I3 (HUB 3I)** é uma plataforma web para **registro e divulgação de iniciativas e projetos de Ciência Cidadã na América Latina**. É um *fork* do [EU-Citizen.Science](https://eu-citizen.science/) (`eucs_platform`), mantido no contexto do **IBICT/Civis**. É **software livre** e **multilíngue**, tendo o **português do Brasil (`pt-br`) como idioma padrão**, além de **espanhol (`es`)** e **inglês (`en`)** (ver `TRANSLATED_LANGUAGES` em `eucs_platform/settings/base.py`).

O sistema é construído em **Django** (código em `src/`, projeto `eucs_platform`) e agrega diferentes tipos de conteúdo de ciência cidadã — organizações, projetos, plataformas, recursos (incluindo recursos de treinamento), eventos, notícias (blog) e dossiês — com moderação editorial, tradução de conteúdo de domínio, mapas georreferenciados, boletins/newsletters e uma API REST ("CÍVIS API").

Este documento descreve **o que o sistema faz hoje**, derivado diretamente do código-fonte (models, views, urls, middleware e settings). Itens cujo comportamento não pôde ser confirmado apenas pela leitura dos arquivos lidos estão marcados com **(a confirmar)**.

> Observação de marca: no código, o título do admin e vários textos de e-mail/API usam o nome **"Cívis"** (ex.: `admin.site.site_header = "Cívis Administração"`, API `CÍVIS API`). Trata-se da mesma plataforma aqui chamada Hub I3.

---

## User Stories

### Requisito 1 — Autenticação e ciclo de vida da conta
**User Story:** Como visitante, quero criar uma conta, ativá-la por e-mail e gerenciar meu acesso (login, logout, troca e redefinição de senha, exclusão), para participar da plataforma com segurança.

#### Critérios de Aceitação (EARS)
1. QUANDO um visitante submete o formulário de cadastro (`signup`) O SISTEMA DEVE criar o usuário com `is_active = False`, gravar no perfil o ORCID e o idioma informados e enviar um e-mail de ativação (`send_new_user_email`), exibindo a página de confirmação de e-mail.
2. SE o visitante marcou a opção de newsletter no cadastro ENTÃO O SISTEMA DEVE inscrever o nome e e-mail informados como assinante (`Subscriber.objects.subscribe(..., valid=True)`).
3. QUANDO o usuário acessa o link de ativação (`activate/<uidb64>/<token>/`) com token válido O SISTEMA DEVE marcar `is_active = True`, autenticar o usuário, enviar o e-mail de boas-vindas (exceto quando o parâmetro `reactivate` está presente) e executar eventual `ActivationTask` pendente associada ao e-mail.
4. QUANDO o login é bem-sucedido O SISTEMA DEVE ativar o idioma do perfil do usuário e, se "lembrar-me" estiver marcado, estender a expiração da sessão (padrão 30 dias, `KEEP_LOGGED_DURATION`).
5. QUANDO o usuário solicita redefinição de senha O SISTEMA DEVE enviar e-mail de reset no idioma ativo com link válido; e SE o usuário reconfirma senha mas a conta está inativa ENTÃO O SISTEMA DEVE reenviar o e-mail de ativação em vez de autenticar.
6. QUANDO o usuário solicita exclusão da conta (`delete`) O SISTEMA DEVE remover o `User` e redirecionar para a home; QUANDO troca a senha com sucesso O SISTEMA DEVE deslogá-lo e exigir novo login.

### Requisito 2 — Proteção contra força bruta no login
**User Story:** Como administrador, quero bloquear tentativas repetidas de login malsucedidas, para proteger as contas contra ataques de força bruta.

#### Critérios de Aceitação (EARS)
1. ENQUANTO há requisições `POST` para a URL de login O SISTEMA DEVE contar as tentativas por IP (chave de cache `bf_attempts_<ip>`, obtendo o IP de `HTTP_X_FORWARDED_FOR` quando presente).
2. QUANDO o número de tentativas atinge `BRUTE_FORCE_THRESHOLD` O SISTEMA DEVE desativar a conta (`is_active = False`) do usuário informado e redirecionar para a URL de login.
3. QUANDO uma conta é bloqueada por excesso de tentativas O SISTEMA DEVE enviar ao usuário um e-mail de redefinição de senha com token e registrar a ação no log (`log_message`).
4. SE a conta bloqueada já estava inativa ENTÃO O SISTEMA DEVE registrar uma exceção/aviso para os administradores em vez de reenviar o e-mail.
5. ENQUANTO o contador está ativo O SISTEMA DEVE expirá-lo após `BRUTE_FORCE_TIMEOUT`.

### Requisito 3 — Perfil do usuário e área "me"
**User Story:** Como usuário autenticado, quero manter meu perfil e acessar minha área pessoal (submissões, favoritos, permissões, estatísticas, dossiês), para gerenciar minha presença e conteúdos na plataforma.

#### Critérios de Aceitação (EARS)
1. QUANDO o usuário acessa `users/me/` e sub-rotas O SISTEMA DEVE exibir suas submissões, favoritos (bookmarks), recursos, projetos seguidos, organizações, permissões de projeto, estatísticas (`my_stats`) e dossiês (`my_dossiers`).
2. O perfil DEVE armazenar foto, título, bio, áreas de interesse, ORCID, Lattes ID, idioma preferido, país e organizações associadas.
3. SE o campo ORCID for preenchido com valor inválido ENTÃO O SISTEMA DEVE recusar o salvamento (`validate_orcid` lança `ValidationError`).
4. ENQUANTO `profileVisible` for `False` (padrão) O SISTEMA DEVE manter o perfil fora da listagem pública de membros; QUANDO `profileVisible` for `True` O SISTEMA DEVE listar o usuário como membro visível (ex.: em organizações).
5. QUANDO o usuário altera suas preferências de privacidade (`updatePrivacy`) O SISTEMA DEVE persistir `profileVisible`, `contentVisible` e a inscrição no digest.
6. QUANDO um visitante acessa `users/<slug>/` O SISTEMA DEVE exibir o perfil público via `slug` (UUID), e `users/` DEVE oferecer busca de usuários.

### Requisito 4 — Organizações de ciência cidadã
**User Story:** Como usuário autenticado, quero cadastrar e editar organizações georreferenciadas, para que apareçam na plataforma após moderação e possam ser associadas a projetos e recursos.

#### Critérios de Aceitação (EARS)
1. QUANDO um usuário autenticado submete uma nova organização O SISTEMA DEVE salvá-la, registrar log e enviar e-mails de confirmação ao autor e de notificação à equipe (Cívis) no idioma do administrador.
2. SE o criador for membro da equipe (`is_staff`) ao criar a organização ENTÃO O SISTEMA DEVE aprová-la automaticamente (`approved = True`); caso contrário a organização permanece pendente de moderação.
3. ENQUANTO uma organização não estiver aprovada O SISTEMA DEVE ocultá-la do público; apenas o criador, cooperadores (`OrganisationPermission`) e `is_staff` podem visualizá-la e editá-la.
4. QUANDO o criador ou um usuário `is_staff` define cooperadores (`allowUserOrganisation`) O SISTEMA DEVE substituir as permissões existentes pelo conjunto de e-mails informado.
5. QUANDO um usuário `is_staff` aprova/reprova uma organização (`approve_organisation`) O SISTEMA DEVE atualizar `approved`, registrar log e redirecionar para o admin.
6. SE houver projetos associados à organização ENTÃO O SISTEMA DEVE impedir sua exclusão (`ProtectedError`) e exibir mensagem de erro.
7. A organização DEVE guardar coordenadas (`location` como `PointField`, além de `latitude`/`longitude`) e país, para exibição em mapa.

### Requisito 5 — Projetos de ciência cidadã
**User Story:** Como submetedor de conteúdo, quero cadastrar projetos de ciência cidadã com metadados ricos, localização e imagens, para divulgá-los após moderação e acompanhar seu engajamento.

#### Critérios de Aceitação (EARS)
1. QUANDO um usuário autenticado salva um projeto (`saveProjectAjax`) O SISTEMA DEVE validar o formulário, processar até três imagens, persistir o projeto e, em criação, enviar e-mail de confirmação ao autor e de notificação à equipe.
2. SE o criador for `is_staff` na criação ENTÃO O SISTEMA DEVE aprovar o projeto automaticamente (`approved = True`); caso contrário fica pendente (`approved = None`).
3. ENQUANTO um projeto não estiver aprovado ou estiver `hidden` O SISTEMA DEVE ocultá-lo do público na listagem (`projects`) e na página de detalhe, exceto para quem tem permissão de edição; QUANDO o usuário for `is_staff` O SISTEMA DEVE permitir filtrar por `approved`/`notApproved`/`notYetModerated`.
4. QUANDO um visitante não-staff acessa a página de um projeto O SISTEMA DEVE incrementar `totalAccesses`, registrar o primeiro acesso e atualizar as estatísticas diárias (`Stats`).
5. QUANDO um usuário autenticado curte (`like_project_ajax`) ou segue (`setFollowedProject`) um projeto O SISTEMA DEVE alternar o registro (`Likes`/`FollowedProjects`), ajustar contadores e estatísticas diárias, e no "seguir" enviar e-mail ao criador no idioma dele.
6. QUANDO o criador (ou alguém com permissão) convida um editor (`project_invite`) O SISTEMA DEVE enviar e-mail de convite; para e-mail já registrado cria `ProjectPermission` (aceito ao acessar `project_invitation`), e para e-mail não registrado cria uma `ActivationTask` a executar na ativação da conta.
7. QUANDO um usuário `is_staff` aprova (`approve_project`), oculta (`setHidden`) ou destaca (`setFeatured`) um projeto O SISTEMA DEVE atualizar os campos correspondentes e registrar log; e SOMENTE superusuários podem excluir projetos (`deleteProject`).
8. QUANDO qualquer usuário aciona `downloadProjects` O SISTEMA DEVE exportar os projetos aprovados com coordenadas em CSV (formato de camada compatível com a integração "Visão").

### Requisito 6 — Plataformas de ciência cidadã
**User Story:** Como submetedor de conteúdo, quero cadastrar plataformas de ciência cidadã com abrangência geográfica e países, para divulgá-las após ativação/moderação.

#### Critérios de Aceitação (EARS)
1. QUANDO um usuário autenticado salva uma plataforma (`savePlatformAjax`) O SISTEMA DEVE persistir nome, URL, descrição, extensão geográfica (`geoExtend`), países (`countries`), palavras-chave, organizações e imagens (logo e imagem de perfil).
2. SE o criador for `is_staff` na criação ENTÃO O SISTEMA DEVE ativar a plataforma automaticamente (`active = creator.is_staff`); caso contrário `active = False`.
3. ENQUANTO `active` for `False` O SISTEMA DEVE mantê-la fora da listagem pública (a home filtra `active=True`).
4. QUANDO o usuário edita (`editPlatform`) ou exclui (`deletePlatformAjax`) uma plataforma O SISTEMA DEVE aplicar as regras de permissão do app. **(a confirmar — regra exata de quem pode editar/excluir; não foi lido `platforms/views.py`.)**
5. O conteúdo de domínio de plataforma (ex.: extensão geográfica) DEVE ser traduzível via o framework de tradução genérica (`AbstractTranslatedModel`).

### Requisito 7 — Recursos e recursos de treinamento
**User Story:** Como submetedor de conteúdo, quero cadastrar recursos e recursos de treinamento classificados por categoria, tema e público, para que sejam encontrados, favoritados e agrupados após moderação.

#### Critérios de Aceitação (EARS)
1. QUANDO um usuário autenticado salva um recurso (`saveResourceAjax` / `newResource` / `newTrainingResource`) O SISTEMA DEVE distinguir recursos comuns de recursos de treinamento pela flag `isTrainingResource` (definida como `True` pelo proxy `TrainingResource`).
2. SE o criador for `is_staff` na criação ENTÃO O SISTEMA DEVE aprovar o recurso automaticamente; caso contrário fica pendente (`approved = None`).
3. ENQUANTO um recurso não estiver aprovado ou estiver `hidden` O SISTEMA DEVE ocultá-lo das listagens públicas (a home usa `approved_resources()` e `approved_training_resources()`).
4. QUANDO um usuário autenticado marca um recurso como favorito (`bookmarkResource`) O SISTEMA DEVE criar/remover `BookmarkedResources` para aquele usuário.
5. QUANDO um usuário `is_staff` aprova (`approve_resource`), destaca (`setFeaturedResource`), oculta (`setHiddenResource`) ou define como treinamento (`setTrainingResource`) O SISTEMA DEVE atualizar os campos correspondentes.
6. O SISTEMA DEVE permitir agrupar recursos em grupos curados (`ResourceGroup`/`ResourcesGrouped`), exibidos na página "curated", e exportar recursos (`downloadResources`).
7. O recurso DEVE poder referenciar autores (`authors.Author`), organizações e projetos associados.

### Requisito 8 — Blog / Notícias
**User Story:** Como visitante, quero ler notícias e posts publicados, para me informar sobre a plataforma e a ciência cidadã.

#### Critérios de Aceitação (EARS)
1. QUANDO um visitante acessa `blog` O SISTEMA DEVE listar os posts (ordenados por data de criação descendente) e `blog/<ano>/<mês>/<dia>/<slug>/` DEVE exibir o detalhe do post.
2. ENQUANTO o `status` do post não for `PUBLISHED` O SISTEMA DEVE tratá-lo como não publicado (`published` é `True` apenas quando `status == PUBLISHED`). **(a confirmar — filtro exato aplicado na listagem pública; não foi lido `blog/views.py`.)**
3. QUANDO um post tem `sticky` definido O SISTEMA DEVE priorizá-lo conforme a escolha de fixação (`PostSticky`).
4. O post DEVE ter título e slug únicos e poder ter múltiplos autores (`authors`), expondo `authors_names` que ignora o nome placeholder "Empty user".

### Requisito 9 — Dossiês (coleções curadas)
**User Story:** Como curador, quero montar dossiês que agregam conteúdos de vários apps e moderar os itens indicados, para publicar coleções temáticas com tradução própria.

#### Critérios de Aceitação (EARS)
1. O dossiê DEVE agregar itens de diferentes apps (projetos, recursos, eventos, posts de blog) via `DossierObject` com `GenericForeignKey`, mantendo a unicidade por (dossiê, tipo de conteúdo, objeto).
2. ENQUANTO o `status` do dossiê for `DRAFT` ou `INACTIVE` O SISTEMA DEVE mantê-lo fora da visão pública; QUANDO `status` for `ACTIVE` (Publicado) O SISTEMA DEVE exibi-lo (`get_approved_dossier` usado nas buscas de projetos/eventos).
3. QUANDO um usuário indica um conteúdo a um dossiê (ex.: via `_save_and_indicate` em projetos/eventos, ou `dossier_select`) O SISTEMA DEVE criar um `DossierObject` com `approved = None` (não moderado), que só aparece no dossiê quando `approved = True`.
4. ENQUANTO um `DossierObject` não estiver aprovado O SISTEMA DEVE desabilitá-lo/ocultá-lo sem excluí-lo, permitindo nova avaliação do item.
5. O dossiê DEVE ter curadores (`DossierCurator`), podendo vincular um post de "call to action", organizações parceiras e colaboradores.
6. O conteúdo do dossiê (título, resumo, descrição) DEVE ser traduzível via `DossierTranslation` por idioma, exposto de forma transparente por `translated_data`.

### Requisito 10 — Eventos
**User Story:** Como submetedor de conteúdo, quero cadastrar eventos com datas e modalidade, para divulgá-los após moderação e vê-los listados por período (em andamento, futuros, passados).

#### Critérios de Aceitação (EARS)
1. QUANDO um usuário autenticado cria um evento (`new_event`) O SISTEMA DEVE persistir título, descrição, local, datas, modalidade (`EventMode`), idioma e enviar e-mails de confirmação ao autor e notificação à equipe.
2. SE o criador for `is_staff` na criação ENTÃO O SISTEMA DEVE aprovar o evento automaticamente; caso contrário fica pendente (`approved = None`).
3. ENQUANTO o usuário não for `is_staff` O SISTEMA DEVE listar apenas eventos aprovados (`approved_events()`); QUANDO filtra por período O SISTEMA DEVE separar eventos ongoing, upcoming e past.
4. QUANDO um usuário `is_staff` aprova (`approve_event`) ou destaca (`setFeaturedEvent`) um evento O SISTEMA DEVE atualizar os campos e registrar log.
5. QUANDO o criador ou um `is_staff` exclui um evento (`deleteEvent`) O SISTEMA DEVE removê-lo; usuários sem permissão são redirecionados para a listagem.
6. O evento DEVE poder ser indicado a um dossiê (`_save_and_indicate`).

### Requisito 11 — Newsletter, assinantes e contato
**User Story:** Como administrador, quero gerenciar assinantes e enviar newsletters, e como visitante quero entrar em contato e me inscrever/descadastrar, para manter a comunicação com a comunidade.

#### Critérios de Aceitação (EARS)
1. QUANDO um visitante se inscreve (`subscribe`) O SISTEMA DEVE criar um `Subscriber` e enviar e-mail de confirmação (`confirm_email/<token>/<id>`), marcando-o como válido ao confirmar.
2. QUANDO um assinante acessa o link de descadastro (`unsubscribe/<token>/<id>`) O SISTEMA DEVE processar o opt-out usando o `secret()` derivado da `SECRET_KEY` e do id.
3. QUANDO um administrador renderiza uma newsletter (`render`) O SISTEMA DEVE montar o HTML a partir do template conforme o tipo (assinantes ou todos os usuários Cívis), incluindo eventos em andamento/futuros e projetos aprovados recentes.
4. QUANDO uma newsletter é enviada (`send`) O SISTEMA DEVE personalizar o conteúdo por assinante, incluir cabeçalho `List-Unsubscribe` e um pixel de rastreamento (`load_image`), e atualizar contadores de envio/leitura.
5. ENQUANTO a newsletter estiver em estado `DRAFT`/`READY`/`QUEUED` O SISTEMA DEVE refletir seu `status` até `SENT` ou `ERROR`; o envio em lote é acionável pelo comando de gestão `send_newsletter`.
6. QUANDO um visitante usa o formulário de contato (`contact`) O SISTEMA DEVE processar o envio; e o formulário de contato ao submetedor (`submitter_contact/<group>/<pk>`) DEVE permitir contatar o autor de um conteúdo.
7. O SISTEMA DEVE permitir importar assinantes por CSV (`import_subscriber_csv`).

### Requisito 12 — Páginas institucionais e navegação de nível raiz
**User Story:** Como visitante, quero acessar a página inicial agregadora e páginas institucionais, para conhecer a plataforma e suas regras.

#### Critérios de Aceitação (EARS)
1. QUANDO um visitante acessa a home O SISTEMA DEVE agregar, paginados, projetos aprovados, recursos e recursos de treinamento aprovados, organizações aprovadas, plataformas ativas e eventos (ongoing + upcoming), além de contadores de usuários e totais.
2. O SISTEMA DEVE servir páginas institucionais fixas por rota: `about`, `imprint`, `terms`, `privacy`, `guide`, `criteria`, `moderation`, `moderation_quality_criteria`, `translations`, `development`.
3. QUANDO há páginas dinâmicas por slug O SISTEMA DEVE resolvê-las via app `pages` (`<slug>/`, catch-all ao final das URLs) por idioma, com unicidade (slug, idioma).
4. QUANDO `USE_GUIDE` estiver configurado O SISTEMA DEVE redirecionar `guide` para o arquivo estático do idioma ativo; caso contrário renderizar o template de guia.
5. O SISTEMA DEVE expor `sitemap.xml` e `robots.txt`, e páginas de erro (`403`, `500`) e `coming_soon`.
6. O conteúdo de `Page`/`Section`/`Article` DEVE herdar o idioma do pai (seção herda da página; artigo herda da seção).

### Requisito 13 — Busca global e autocomplete
**User Story:** Como visitante, quero buscar conteúdo em toda a plataforma a partir de uma caixa única, para encontrar projetos, recursos, organizações, plataformas, eventos e usuários.

#### Critérios de Aceitação (EARS)
1. QUANDO um usuário digita na busca (`home_autocomplete`) O SISTEMA DEVE executar full-text search sobre o índice `SearchIndex` e retornar resultados em JSON.
2. ENQUANTO o usuário não for `is_staff` O SISTEMA DEVE restringir os resultados a itens marcados como públicos (`is_public`); QUANDO for `is_staff` O SISTEMA DEVE incluir itens não públicos.
3. O SISTEMA DEVE manter um índice tipado por conteúdo (`SearchIndexType`: project, resource, training, organisation, platform, profile, event, blog) e, atualmente, excluir `blog` do autocomplete global.
4. QUANDO uma listagem (projetos, recursos, organizações, eventos) recebe `keywords` O SISTEMA DEVE filtrar por IDs retornados do `SearchIndex` para o tipo correspondente.
5. O texto indexado DEVE ser normalizado (sem HTML e sem acentuação, via `unidecode`) ao ser gravado (`add_searchindex_text`).

### Requisito 14 — API REST (CÍVIS API) e integrações de identidade
**User Story:** Como integrador/sistema externo, quero consumir e submeter conteúdo via API REST autenticada e autorizar aplicações via OAuth2/OIDC, para integrar o Hub I3 com outros sistemas.

#### Critérios de Aceitação (EARS)
1. O SISTEMA DEVE expor APIs DRF para projetos (`/api/projects/`, detalhe, criação, tradução e viewsets de topic/status/participationTask), além de organisations, platforms e resources (cada app com seu `api/urls`).
2. QUANDO um cliente autentica via djoser (`/api/auth/`) por token ou sessão O SISTEMA DEVE emitir/validar as credenciais; e a documentação (`/swagger/`, `/redoc/`) DEVE exigir login (`login_required`).
3. ENQUANTO o esquema OpenAPI é servido (`CÍVIS API`, drf-yasg) O SISTEMA DEVE tratá-lo como não público, exigindo usuário autenticado (`IsAuthenticated`).
4. O SISTEMA DEVE oferecer provedor OAuth2 (`/o/`, oauth2_provider) e OpenID Connect (`/openid/`, oidc_provider).
5. O SISTEMA DEVE suportar renderização de respostas de API em CSV (renderer no app `utilities`). **(a confirmar — quais endpoints habilitam o CSV renderer.)**

### Requisito 15 — Integração "Visão" / Geoserver (mapas de projetos)
**User Story:** Como administrador, quero integrar os projetos georreferenciados ao serviço "Visão"/Geoserver, para exibir e comparar iniciativas em mapas temáticos.

#### Critérios de Aceitação (EARS)
1. SE `VISAO_USERNAME` estiver configurado ENTÃO O SISTEMA DEVE montar na home os endpoints de visualização por grupo/camada e os tópicos de projeto com `external_url`; caso contrário O SISTEMA DEVE omitir esses elementos.
2. QUANDO um projeto aprovado com latitude/longitude é salvo e `VISAO_USERNAME` está configurado O SISTEMA DEVE marcar os tópicos relacionados como `updated = False` para resincronização. **(a confirmar — o envio efetivo ao Visão no `save` está comentado no código; a exclusão (`delete`) chama `visao.delete_project`.)**
3. QUANDO um administrador aciona `test_visao` O SISTEMA DEVE tentar autenticar no serviço e reportar sucesso ou falha.

### Requisito 16 — Moderação transversal de conteúdo
**User Story:** Como moderador/admin, quero aprovar, ocultar e destacar conteúdos, para garantir que o público veja apenas material revisado e priorizar itens em destaque.

#### Critérios de Aceitação (EARS)
1. ENQUANTO um conteúdo (organisations, projects, platforms, resources, events) não estiver aprovado O SISTEMA DEVE mantê-lo invisível ao público, usando managers "approved_*"/filtros de `approved=True`.
2. QUANDO o criador do conteúdo é `is_staff` na criação O SISTEMA DEVE aprovar/ativar automaticamente o item.
3. SE um conteúdo estiver `hidden` ENTÃO O SISTEMA DEVE ocultá-lo mesmo que aprovado (projetos e recursos possuem flag `hidden`).
4. QUANDO um item é marcado como `featured` O SISTEMA DEVE priorizá-lo na ordenação das listagens e na home.
5. SOMENTE usuários `is_staff` DEVEM poder aprovar/ocultar/destacar; ações de aprovação/moderação DEVEM registrar log (`log_message`).
6. ENQUANTO itens de dossiê não forem aprovados O SISTEMA DEVE moderá-los por item (`DossierObject.approved`), independentemente da aprovação do conteúdo original.

### Requisito 17 — Multi-idioma (i18n de interface e tradução de conteúdo)
**User Story:** Como usuário, quero navegar e ler conteúdos em pt-br, es ou en, para usar a plataforma no meu idioma.

#### Critérios de Aceitação (EARS)
1. O SISTEMA DEVE operar com `pt-br` como idioma padrão (`LANGUAGE_CODE = "pt-br"`) e oferecer `es` e `en` como idiomas traduzíveis (`TRANSLATED_LANGUAGES`).
2. QUANDO um usuário autenticado troca o idioma (`set_language`) O SISTEMA DEVE persistir o idioma no perfil; para visitantes anônimos O SISTEMA DEVE gravar preferência via cookie/sessão (`set_language_preference`).
3. O SISTEMA DEVE traduzir conteúdo de domínio (tipos/tópicos/temas/status etc.) via o framework genérico (`Translation` + `AbstractTranslatedModel` por `ContentType`), expondo `translated_text` nas listagens.
4. QUANDO um usuário submete tradução de projeto (`submitProjectTranslation`) O SISTEMA DEVE gravar `TranslatedProject` por idioma; dossiês usam `DossierTranslation`.
5. QUANDO o detalhe de um projeto é aberto O SISTEMA DEVE indicar se há tradução no idioma ativo (`hasTranslation`).

### Requisito 18 — Mapas / GIS
**User Story:** Como visitante, quero ver organizações e projetos em mapas, para localizar iniciativas geograficamente.

#### Critérios de Aceitação (EARS)
1. O SISTEMA DEVE armazenar a localização de organizações como `PointField` e a localização de projetos como `MultiPolygonField` (`projectGeographicLocation`), além de latitude/longitude.
2. QUANDO uma página com mapa é renderizada O SISTEMA DEVE exibir os pontos/áreas client-side via django-leaflet. **(a confirmar — renderização nos templates; verificado via models e contexto das views.)**
3. QUANDO `downloadProjects` é acionado O SISTEMA DEVE exportar coordenadas dos projetos aprovados em CSV para uso em camadas de mapa.
4. O SISTEMA DEVE permitir filtrar projetos e organizações por país.

### Requisito 19 — Digest (boletim agregador)
**User Story:** Como administrador, quero montar e enviar digests periódicos agregando conteúdos recentes, e como usuário quero optar por recebê-los.

#### Critérios de Aceitação (EARS)
1. O SISTEMA DEVE permitir montar um `Digest` definindo o período (`dateOrg`/`dateEnd`) e quais tipos incluir (posts, eventos, organizações, projetos, recursos, treinamentos).
2. QUANDO um digest é gerado O SISTEMA DEVE calcular e armazenar as contagens por tipo (`nPosts`, `nEvents`, ...) e marcar `sent` ao ser enviado.
3. QUANDO um usuário acessa `showDigests`/`showDigest/<pk>` O SISTEMA DEVE listar e exibir os digests. **(a confirmar — visibilidade pública vs. restrita; não lido `digest/views.py`.)**
4. ENQUANTO `profile.digest` for `True` O SISTEMA DEVE considerar o usuário como inscrito no boletim.

### Requisito 20 — Infraestrutura de manutenção (crons/limpeza)
**User Story:** Como operador, quero rotinas automáticas de limpeza, para manter o banco saudável.

#### Critérios de Aceitação (EARS)
1. O SISTEMA DEVE prover crons utilitários para limpeza (ex.: captcha e sessões). **(a confirmar — nomes e agendamento exatos; `utilities` descrito como biblioteca interna, crons não lidos em detalhe.)**
2. O SISTEMA DEVE manter `Keyword` normalizada em minúsculas e única (lowercase no `save`/`validate_unique`).

---

## Fora de escopo

- **Não é uma rede social**: não há feed social, mensagens diretas entre usuários, seguir pessoas ou curtir perfis; o "seguir" e "curtir" aplicam-se a projetos, e "favoritar" a recursos.
- **Não trata de doenças raras** nem de **políticas públicas do DF** — qualquer vestígio desses temas herdado de forks/documentação deve ser ignorado.
- **Não é um e-commerce** nem processa pagamentos.
- Não é uma ferramenta de edição colaborativa em tempo real; a colaboração é por permissões/convites de editores, não edição simultânea.
- Não implementa coleta de dados de campo da ciência cidadã em si (não é um app de surveys/observações); registra e divulga iniciativas, recursos e eventos.
- Itens marcados **(a confirmar)** ao longo do documento representam comportamentos cujo detalhe não foi validado apenas com os arquivos lidos.

## Papéis / atores (glossário)

- **Visitante anônimo**: usuário não autenticado; vê apenas conteúdo aprovado/ativo e não oculto; pode buscar, navegar, inscrever-se em newsletter e usar o formulário de contato.
- **Usuário autenticado**: possui conta ativa e `Profile`; pode submeter conteúdo, favoritar recursos, curtir/seguir projetos e gerenciar sua área "me".
- **Submetedor de conteúdo**: usuário autenticado que cria organizações, projetos, plataformas, recursos ou eventos; torna-se `creator` do item.
- **Editor / colaborador**: usuário com permissão de edição em um projeto (`ProjectPermission`), organização (`OrganisationPermission`) ou recurso (`ResourcePermission`), geralmente via convite aceito.
- **Curador (dossiês)**: usuário vinculado a um dossiê (`DossierCurator`) que seleciona e modera os itens (`DossierObject`) agregados.
- **Moderador / admin (`is_staff`)**: membro da equipe; aprova/reprova, oculta e destaca conteúdos, e tem conteúdo próprio aprovado automaticamente.
- **Superusuário**: administrador com acesso total; única categoria autorizada a excluir projetos (`deleteProject`).
- **Assinante (`Subscriber`)**: pessoa inscrita para receber newsletters, com fluxo de confirmação e descadastro, independente de ter conta.
- **Integrador / sistema externo**: consumidor da CÍVIS API via token/sessão, OAuth2 ou OIDC.
