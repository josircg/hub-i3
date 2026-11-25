# Hub I3

Este arquivo existe para o Claude Code. A fonte única de contexto do projeto é
a pasta `.kiro/` (usada pelo Kiro). **Não duplique conteúdo aqui**: edite os
arquivos de `.kiro/`.

## Contexto do projeto (steering)

@.kiro/steering/product.md
@.kiro/steering/structure.md
@.kiro/steering/django.md
@.kiro/steering/django-spec-template.md

> Os cabeçalhos `inclusion:` (front-matter) e a sintaxe `#[[file:...]]` dos
> arquivos de steering são recursos do Kiro. O Claude Code os ignora; trate os
> arquivos acima como sempre carregados.

## Specs

- As specs ficam em `.kiro/specs/<feature>/` (`requirements.md`, `design.md`,
  `tasks.md`). Não crie specs em outro lugar.
- Para features não-triviais, siga o template `django-spec-template.md`.
- Antes de implementar uma feature com spec, leia os três arquivos dela.
- Ao concluir uma tarefa, marque-a em `tasks.md` com `- [x]`. Não altere a
  estrutura dos arquivos.
