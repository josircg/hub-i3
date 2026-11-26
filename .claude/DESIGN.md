# Design System — Hub I3

Este documento define as diretrizes visuais, de UX e de componentes que devem ser seguidas ao gerar ou modificar **telas, templates HTML, CSS, JavaScript e qualquer elemento de UI/UX** na plataforma Hub I3 (HUB 3I).

**Resumo:** o Hub I3 usa **Bootstrap 5**, fontes **Poppins + Inter**, **Bootstrap Icons** e marca **vermelho/verde/amarelo** (`--df-red #C8102E`, `--df-green #009739`, `--df-yellow #FFCD00`).

> **Estado de migração de marca (leia antes de mexer em CSS).** O Hub I3 é fork da CÍVIS, cuja marca era rosa `#AE4A74`. A camada de tokens (`eu-citizen_science.css`) **já foi migrada**: os nomes `--pink1…--pink9` foram mantidos por compatibilidade, mas seus valores agora são a escala do **vermelho** `--df-red`. Já o `style.css` (componentes de dossiê, tags, cards de status) **ainda usa `#AE4A74` e tons rosados fixos (hardcoded)**. Ao criar CSS novo, use sempre os tokens (`var(--pink5)` etc.), nunca o hex rosa; ao tocar em regras antigas do `style.css`, prefira trocar o hex por token só se isso fizer parte da tarefa (não refatore de passagem).

---

## Stack e Fundação

- **Framework CSS:** Bootstrap 5.0.2 (via CDN) — `src/templates/base.html`
- **Tipografia:** Poppins (headings + corpo) e Inter (texto de UI/componentes), via Google Fonts; Lato também é carregada
- **Ícones:** Bootstrap Icons (`<i class="bi bi-..."></i>`, via CDN)
- **CSS do projeto:** `src/static/site/css/eu-citizen_science.css` (tokens, escala de marca, `.btn-pink*`, `.text-pink*`, `.bg-pink*`), `src/static/site/css/style.css` (componentes de dossiê/cards) e `src/static/site/css/style_home.css` (home). Também existem `forms.css`, `bootstrap.css` local e CSS legado `style_11_01_2021.css`.
- Todos os componentes são complementares ao Bootstrap 5 — não reinvente o que o framework já oferece.

---

## Tipografia

**Família primária:** Poppins  
**Família de UI:** Inter (texto de componentes, ex. títulos de cards de palavra-chave)  
**CSS Stack:** `'Poppins', sans-serif` (corpo e headings); `'Inter', sans-serif` (UI)

### Pesos disponíveis

100 · 200 · 300 · 400 · 500 · 600 · 700 · 800 · 900 (utilitários `.fw-100` … `.fw-900`)

### Hierarquia semântica

| Papel    | Tamanho / Line-height | Peso | Família  | Uso                                  |
|----------|-----------------------|------|----------|--------------------------------------|
| H1 / H3  | —                     | 600  | Poppins  | Cabeçalhos principais e de seção     |
| H2       | 24px / 1.30           | 600  | Poppins  | Títulos de módulo (ex. dossiê)       |
| H4 / H5  | —                     | 400  | Poppins  | Subtítulos                           |
| BODY     | 16px / 1.50           | 400  | Poppins  | Texto de conteúdo                    |
| UI TITLE | 16px                  | 600  | Inter    | Títulos de card / componente         |
| SMALL    | 14px                  | 400/500 | Inter | Tags, metadados, legendas            |
| CAPTION  | 12px                  | 500  | Inter    | Rótulos em maiúsculas, contadores    |

---

## Paleta de Cores e Tokens CSS

### Marca — bandeira (`eu-citizen_science.css`)

| Token              | Hex       | Uso                                         |
|--------------------|-----------|---------------------------------------------|
| `--df-red`         | `#C8102E` | Vermelho de marca (base da escala `--pink*`) |
| `--df-red-dark`    | `#8C0B21` | Vermelho escuro                              |
| `--df-yellow`      | `#FFCD00` | Amarelo de destaque                          |
| `--df-green`       | `#009739` | Verde de marca (também `--darkGreen`, `--darkBlue`) |
| `--df-green-dark`  | `#006B2D` | Verde escuro (`--darkGreen2`, `--darkBlue2`) |
| `--df-white`       | `#FFFFFF` | Branco                                       |

### Escala de marca primária — `--pink1…--pink9` (nome legado, valores em vermelho)

| Token      | Hex       | Uso principal                                   |
|------------|-----------|-------------------------------------------------|
| `--pink1`  | `#F9E0E5` | Fundo de tags/pills, superfícies suaves de marca |
| `--pink2`  | `#F1ADB7` | Tints claros                                    |
| `--pink3`  | `#E56F82` | Tints médios                                    |
| `--pink4`  | `#D73450` | Estados intermediários                          |
| **`--pink5`** | **`var(--df-red)` = `#C8102E`** | **Cor primária de marca:** links, ícones, títulos de destaque |
| `--pink6`  | `#A70D26` | Botões primários (`.btn-pink6`), links de formulário |
| `--pink7`  | `#8C0B21` | Hover de `.btn-pink6`; texto sobre fundo claro de marca |
| `--pink8`  | `#640A1B` | Tom muito escuro                                |
| `--pink9`  | `#4A0714` | Contraste máximo de marca                       |

Utilitários `.text-pink1`…`.text-pink9` e `.bg-pink1`…`.bg-pink9`; botões `.btn-pink2`, `.btn-pink4`, `.btn-pink6`. **Os nomes "pink" são herança da CÍVIS — não os renomeie** (centenas de usos nos templates); o valor é que é vermelho.

### Acento e cores auxiliares (nomes legados da CÍVIS, valores já migrados)

| Token         | Hex       | Uso                              |
|---------------|-----------|----------------------------------|
| `--orange`    | `#FF8C00` | Alertas, destaques               |
| `--red`       | `#DD3D4C` | Erros, ações destrutivas         |
| `--lightBlue` | `#FFD84D` | Acento amarelo (nome legado; não é azul) |
| `--darkBlue`  | `var(--df-green)` | Acento verde (nome legado; não é azul) |
| `--darkGreen` | `var(--df-green)` | Acento verde                     |
| `--lightGreen`| `#FFF3BF` | Amarelo claro (nome legado)      |
| `--wood`      | `#494A42` | Neutro quente                    |
| `--palid`     | `#FFE680` | Amarelo suave (nome legado)      |

### Neutros / Superfícies / Texto (escala Untitled-UI)

| Nome             | Hex       | Uso                              |
|------------------|-----------|----------------------------------|
| Texto título     | `#344054` | Títulos e texto primário         |
| Texto corpo      | `#667085` | Corpo e texto secundário         |
| Borda            | `#98A2B3` | Bordas de cards e accordions     |
| Superfície       | `#F2F4F7` | Fundo de blocos (ex. keyword)    |
| Divisor          | `#D2D2D2` | Linhas separadoras               |
| Branco           | `#ffffff` | Background de página, navbar     |
| Preto            | `#000000` | Contraste máximo                 |

### Estados semânticos — cards de status (`style.css`)

> O estado ERRO ainda usa o ícone rosa `#AE4A74` herdado da CÍVIS (hardcoded). Ao criar novos usos, prefira `--pink5` para o ícone.

| Estado   | Fundo     | Borda     | Ícone/Círculo |
|----------|-----------|-----------|---------------|
| ATENÇÃO  | `#FFFBE9` | `#FFEA7B` | `#AA8F00`     |
| SUCESSO  | `#E4FFF2` | `#95FFCC` | `#0A9552`     |
| ERRO     | `#FFF8FB` | `#FFCCE0` | `#AE4A74`     |
| INFO     | `#F1F8FF` | `#C3DFFF` | `#3C97FF`     |

---

## Grid e Layout

- **Colunas:** 12 (padrão Bootstrap 5)
- **Container:** `container` / `container-fluid` do Bootstrap
- **Conteúdo centralizado**, largura máxima conforme breakpoints do Bootstrap

### Breakpoints (Bootstrap 5)

| Sigla | Largura mínima |
|-------|---------------|
| XS    | < 576px       |
| SM    | ≥ 576px       |
| MD    | ≥ 768px       |
| LG    | ≥ 992px       |
| XL    | ≥ 1200px      |
| XXL   | ≥ 1400px      |

### Navbar

- `navbar navbar-light navbar-expand-lg sticky-top bg-white`
- Background **branco**; logo Hub I3 à esquerda (`site/img/logos/hub-i3.png`, `width=220`, carregado com `lazyload`). Há também `hub3i.svg` e variantes para rodapé (`hub-i3-footer-variant.png`)
- Colapsa para menu hamburguer abaixo de LG

### Footer

- Estrutura em `src/templates/_footer.html`: faixa `header-footer` + `content-footer` com texto claro (`text-light`/`text-white`) sobre fundo escuro; logos institucionais (IBICT, MCTI, INCC, RBCC, RICAP) em versões brancas em `site/img/logos/`
- Sem imagens decorativas; os parceiros removidos do rodapé não devem ser reintroduzidos sem pedido

---

## Espaçamento

Use as utilities de espaçamento do Bootstrap 5 (`m-*`, `p-*`, `g-*`). Valores recorrentes no CSS do projeto: **4 · 8 · 16 · 20 · 24 · 30 · 40px**. Prefira a escala do Bootstrap; não invente valores intermediários arbitrários.

### Border-radius

| Nível | Valor    | Uso                              |
|-------|----------|----------------------------------|
| MD    | 8px      | Cards, botões (`.btn-pink6`, padrão Bootstrap), banners |
| LG    | 16px     | Containers maiores, tags (`.keyword-tag`) |
| FULL  | 99px / 100% | Pills, círculos, avatares, contadores |

---

## Elevação, Sombras e Bordas

### Bordas

- `1px solid #98A2B3` — cards, accordions
- `1px solid #D2D2D2` — divisores e espaçadores de banner
- `1px solid var(--pink5)` — estados ativos e destaques de marca (o legado em `style.css` ainda usa `#AE4A74`)
- Cards de status usam borda da cor do estado (ver tabela de estados)

### Sombras

- Sombras neutras e discretas; o significado é carregado pela **cor**, não pela sombra
- **Sem gradientes, `backdrop-blur` ou texturas** — superfícies opacas e planas

---

## Componentes

### Botões

| Variante        | Estilo                                                    | Uso                       |
|-----------------|-----------------------------------------------------------|---------------------------|
| `.btn.btn-pink6` | Preenchido: fundo `--pink6` (`#A70D26`), texto branco, sem `box-shadow` no foco | **Ação principal de marca** (salvar, enviar, CTAs — ver `_save_zone.html`, `home.html`) |
| `.btn-pink6:hover` | Escurece para `--pink7` (`#8C0B21`)                     | Hover da ação principal   |
| `.btn-pink4` / `.btn-pink2` | Variantes mais claras da escala (hover sobe um degrau) | Ações secundárias/terciárias |
| Bootstrap btns  | `btn-primary`, `btn-outline-*` etc. quando aplicável      | Ações utilitárias         |

> **Não use `.btn-civis`.** Essa classe não existe mais: a regra em `style.css` virou `.btn-HUB 3I` por um find/replace do rebranding e é um seletor inválido (com espaço), sem nenhum uso nos templates. Corrigir isso é uma tarefa à parte; não "conserte" de passagem.

**Interações:** hover escurece/preenche com a cor de marca; transições rápidas e propositais.

---

### Tags e Badges

- Formato pill (`border-radius: 16px` ou `99px`)
- `.keyword-tag`: no `style.css` atual, fundo `#EFDBE3` + texto `#AE4A74` (rosa legado, **ainda não migrado**); a intenção de design é `--pink1` + `--pink5`. Peso 500, 14px
- `.posts-number-tag`: pill branco, texto `#344054`, ícone em `#AE4A74` (rosa legado; intenção: `--pink5`)
- Comunicam estado/categoria sempre por **cor + texto** (nunca cor isolada)

---

### Cards

- Fundo branco · `border-radius: 8px` · borda `1px solid #98A2B3`
- Padding base 16px · margem inferior ~20px
- Título em weight 600 (`#344054`), corpo em `#667085`
- **Cards de status** (`.card-yellow`/`.card-green`/`.card-red`/`.card-blue`): fundo + borda da cor do estado, com `.circle` (ícone em pill) na cor de ícone correspondente
- Sem imagens decorativas

---

### Accordions (padrão dossiê)

- Item: borda `1px solid #98A2B3`, `radius 8px`, fundo transparente, texto `#667085`
- Botão: texto de marca (`--pink5`; legado `#AE4A74` em `style.css`) weight 600; sem `box-shadow` no estado aberto

---

### Tabelas

- Cabeçalho em maiúsculas sobre superfície clara (`#F2F4F7`)
- Divisores de linha discretos (`#D2D2D2` / `#dee2e6`)
- Hover sutil de linha; sem cores fortes no corpo

---

### Alertas / Callouts

Formato de texto: `<Tipo>: <Fato>.` — dois-pontos seguido de frase declarativa.

| Tipo     | Fundo     | Texto/Ícone |
|----------|-----------|-------------|
| Sucesso  | `#E4FFF2` | `#0A9552`   |
| Atenção  | `#FFFBE9` | `#AA8F00`   |
| Erro     | `#FFF8FB` | `--pink5` (legado `#AE4A74`) |
| Info     | `#F1F8FF` | `#3C97FF`   |

Sempre precedidos por ícone à esquerda (Bootstrap Icons).

---

### Formulários

- Usam `crispy-forms` (pacote `crispy_bootstrap3`, ver convenções do projeto) com `forms.css`
- Inputs com `border-radius` do Bootstrap; foco com realce de marca quando aplicável
- Campos de texto rico usam `CKEditorWidget` (`django-ckeditor`) com as configs `default` (admin) e `frontpage` (formulários públicos) de `CKEDITOR_CONFIGS`; o Summernote foi removido
- Layout responsivo: 1 coluna no mobile, múltiplas colunas a partir de MD

---

## Iconografia (Bootstrap Icons)

- **Biblioteca:** Bootstrap Icons (`<i class="bi bi-nome"></i>`), carregada via CDN no `base.html`
- **Cor:** herda `currentColor`; para marca, use `var(--pink5)`
- Os templates ainda carregam **Font Awesome 5** (`use.fontawesome.com`, no fim do `base.html`) por herança; em código novo use Bootstrap Icons
- **Sem emoji** — estado é comunicado por ícone + tag/badge + cor; nunca por emoji
- Separador recomendado: ponto médio `·`

---

## Animação e Movimento

### Filosofia

Conservadora: transições rápidas e propositais. Sem bounce, overshoot ou parallax.

### Regras de hover

- Links e botões de marca: transição de cor/fundo suave (ex. `.btn-pink6` → escurece para `--pink7`)
- `.dossier-card-title a`: cor `#667085` → cor de marca no hover (legado `#AE4A74`)
- Sem efeitos lúdicos

---

## Princípios Gerais

1. **Marca com propósito:** o vermelho `--pink5` (`#C8102E`) aparece em botões, links, ícones e destaques; verde (`--df-green`) e amarelo (`--df-yellow`) completam a assinatura visual do Hub I3. Nunca use o rosa `#AE4A74` (CÍVIS) em código novo.
2. **Hierarquia via neutros Untitled-UI:** `#344054` (título) → `#667085` (corpo) → `#98A2B3` (borda) estruturam a hierarquia de texto e superfície.
3. **Superfícies planas:** sem gradientes, blur, texturas ou imagens decorativas.
4. **Bootstrap primeiro:** use os componentes e utilities do Bootstrap 5; o CSS do projeto apenas complementa.
5. **Semântica acessível:** estado sempre comunicado por ícone (Bootstrap Icons) + tag/badge + cor em conjunto — nunca por cor isolada.
6. **Movimento conservador:** transições rápidas e intencionais.
7. **Consistência acima de tudo:** ao alterar telas, siga os tokens e classes já definidos (`--pink*`, `.btn-pink6`, `.keyword-tag`, `.card-*`) em vez de inventar novos.
