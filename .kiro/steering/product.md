# Produto — Hub I3

Contexto de produto e domínio: o *porquê* do sistema. Para *onde* o código
está, ver `#structure`; para stack e ambiente, ver `#django`.

## O que é

**Hub I3** (HUB 3I) é uma plataforma web para registro e divulgação de
iniciativas e projetos de **Ciência Cidadã na América Latina**. Reúne, num único
lugar, as organizações, projetos, plataformas, recursos, eventos e notícias
ligados ao tema.

É um **fork do EU-Citizen.Science platform** (`eucs_platform` — o nome do pacote
Django foi preservado por compatibilidade), adaptado e mantido no contexto do
**IBICT / Civis**. É **software livre**, com repositório público.

- Plataforma Civis (IBICT): https://civis.ibict.br/
- Projeto de origem (EU-Citizen.Science): https://eu-citizen.science/

> **Rebranding em andamento.** A marca foi migrada de versões anteriores para
> "HUB 3I". Nomes de módulos Django (`eucs_platform`) e identificadores de
> configuração foram **preservados** por compatibilidade; alguns textos, artes e
> e-mails antigos ainda podem aparecer (ver `REBRANDING_NOTES.md`). `SITE_NAME`
> em settings é `'HUB 3I'`.

## Origem e governança

- Fork do EU-Citizen.Science, mantido no IBICT/Civis.
- Contexto acadêmico/sem fins lucrativos: decisões devem favorecer acesso
  aberto à informação, baixo custo operacional e sustentabilidade do projeto.

## Melhorias sobre o EU-Citizen.Science (do README)

- Múltiplos editores podem editar um mesmo projeto.
- Controles administrativos aprimorados.
- Ferramentas de tradução aprimoradas.
- Gestão de newsletter.

## Conceitos de domínio

- **Organização** (`organisations`): entidade que atua em ciência cidadã,
  georreferenciada (mapa) e associada a áreas/temas.
- **Projeto / Plataforma** (`projects`, `platforms`): iniciativas de ciência
  cidadã / pesquisa, com localização geográfica, organizações responsáveis e
  conteúdo traduzível.
- **Recurso / Recurso de treinamento** (`resources`): publicações e materiais,
  categorizados, podendo ser vinculados a projetos, organizações e autores.
- **Conteúdo editorial** (`blog`, `pages`, `events`, `digest`, `dossiers`):
  notícias, páginas institucionais, eventos, boletins periódicos e dossiês.

## Princípios de produto (guiam decisões de implementação)

- **Conteúdo é submetido pela comunidade e moderado.** A maioria dos tipos de
  conteúdo (organizações, projetos, plataformas, recursos, eventos) passa por
  aprovação antes de aparecer publicamente. Flags `approved`/`hidden`/`featured`
  são centrais. Ao criar features de listagem, por padrão **só** mostre conteúdo
  aprovado e não oculto (há managers `approved_*` para isso).
- **Multi-idioma de verdade.** Idioma padrão **pt-br**, com **es** e **en**.
  Textos de conteúdo de domínio são traduzíveis via o framework de tradução
  genérica (`utilities.AbstractTranslatedModel`/`Translation`), não só i18n de
  template. Ao adicionar conteúdo visível ao usuário, considere os três idiomas.
- **Foco na América Latina / Brasil.** Fuso `America/Sao_Paulo`, idioma primário
  pt-br, centro do mapa na América do Sul (`LEAFLET_CONFIG['DEFAULT_CENTER']`).
  Decisões de UX e dados assumem contexto latino-americano/brasileiro, ainda que
  o sistema seja multilíngue.
- **Acesso aberto.** Projeto livre e público; evite acoplar a serviços pagos ou
  proprietários quando houver alternativa aberta equivalente.

## O que NÃO é

- Não é uma rede social; o foco é catálogo de informação curada + conteúdo
  editorial.
