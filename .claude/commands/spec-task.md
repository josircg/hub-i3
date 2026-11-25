---
description: Executa uma tarefa de uma spec do Kiro (.kiro/specs/<feature>/)
argument-hint: <feature> [número ou título da tarefa]
---

Execute uma tarefa da spec indicada em `$ARGUMENTS`.

1. O primeiro argumento é o nome da pasta em `.kiro/specs/`. O restante, se
   houver, identifica a tarefa (número ou título). Se a pasta não existir,
   liste `.kiro/specs/` e pergunte qual usar.
2. Leia `.kiro/specs/<feature>/requirements.md`, `design.md` e `tasks.md`.
3. Se nenhuma tarefa foi indicada, escolha a primeira sem `- [x]` e informe
   qual é. Não execute mais de uma tarefa por chamada.
4. Implemente só o que a tarefa pede, seguindo o `design.md` e as convenções do
   `CLAUDE.md`. Se o design estiver ambíguo ou conflitar com o código, pare e
   pergunte.
5. Verifique, a partir de `src/`, na ordem: `python manage.py check`, depois
   `python manage.py makemigrations --check --dry-run`, depois os testes do app
   afetado, se existirem. Se mudou strings traduzíveis, siga a regra de
   traduções do `django.md`. Nunca rode `migrate` em produção.
6. Se tudo passou, marque a tarefa com `- [x]` em `tasks.md`, sem alterar o
   resto do arquivo.
7. Reporte o que mudou e o resultado das verificações. Não faça commit.
