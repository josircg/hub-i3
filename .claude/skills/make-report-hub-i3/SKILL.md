---
name: make-report-hub-i3
description: Transforma o contexto da conversa em um relatório HTML standalone com a identidade visual do Hub I3 (Bootstrap 5, Poppins/Inter, Bootstrap Icons, marca vermelho/verde/amarelo). Use no projeto Hub I3 quando o usuário pedir "gerar relatório", "make report", "exportar conversa como HTML", ou quiser documentar o resultado de uma sessão.
argument-hint: "[nome-do-arquivo]"
---

# Skill: make-report-hub-i3 (Hub I3)

Gere um relatório HTML standalone a partir do contexto desta conversa, seguindo rigorosamente o **Design System do Hub I3** documentado em `.claude/DESIGN.md`.

> Este skill usa a identidade visual do Hub I3 (marca vermelho/verde/amarelo, Poppins/Inter, Bootstrap Icons). A fonte da verdade dos tokens é `.claude/DESIGN.md`.

---

## Passo 1 — Extrair do contexto da conversa

Analise toda a conversa e identifique:

| Campo | O que extrair |
|-------|---------------|
| `TITULO` | Assunto principal (ex: "Melhorias de Performance · Projetos vs Recursos") |
| `SUBTITULO_NAVBAR` | Categoria do relatório (ex: "Relatório de Melhorias", "Análise de Dependências", "Investigação de Bug") |
| `BADGE_NAVBAR` | Referência curta: chamado, branch, projeto ou "Claude Code" |
| `EYEBROW` | Contexto de uma linha (branch, chamado, módulo) |
| `META_DATA` | Data da conversa |
| `META_REFS` | Arquivos/módulos principais envolvidos (se houver) |
| `SECOES` | Lista de blocos de conteúdo (ver abaixo) |
| `ARQUIVOS_MODIFICADOS` | Tabela de arquivos se houve mudanças de código |

### Como estruturar as seções

Cada seção corresponde a um tema, decisão ou mudança relevante da conversa. Para cada seção:

- **Título** — o que foi feito/decidido
- **Número/label** — "Contexto", "Melhoria 1", "Análise", "Decisão 1", etc.
- **Cor do ícone** — `vermelho` (marca/informativo principal), `verde` (resultado positivo/implementado), `amarelo` (atenção/mudança de comportamento), `azul` (investigação/secundário)
- **Ícone Bootstrap Icons** — escolha o mais semântico:
  - Contexto/problema: `exclamation-circle`, `x-circle`, `search`
  - Backend/lógica: `lightning`, `hash`, `database`, `hdd-stack`
  - Frontend/UI: `sliders`, `display`, `layout-text-window`
  - Integração/fluxo: `arrow-repeat`, `link-45deg`, `diagram-3`
  - Arquivo/código: `git`, `file-text`, `code-slash`
  - Próximos passos: `arrow-right`, `check2-square`, `flag`
- **Conteúdo** — use os componentes disponíveis (cards, callouts, tabelas, métricas, steps, code blocks) conforme o conteúdo real da conversa

---

## Passo 2 — Criar o diretório de destino

Execute via Bash antes de gravar o arquivo (relatórios ficam **dentro do projeto**):

```bash
mkdir -p ".claude/docs/reports"
```

---

## Passo 3 — Determinar o nome do arquivo

- Se um argumento foi passado ao invocar a skill, use-o como nome base (sem extensão)
- Caso contrário, derive do `TITULO`: lowercase, remova acentos, substitua espaços e pontos por hífen, remova caracteres especiais
- Exemplo: "Melhorias · Projetos vs Recursos" → `melhorias-projetos-vs-recursos`
- Nome final: `.claude/docs/reports/{nome}.html`

---

## Passo 4 — Gerar o arquivo HTML

Use a ferramenta Write para criar o arquivo. O HTML deve seguir **exatamente** a estrutura e o CSS abaixo. Não invente tokens, classes ou valores fora deste template (todos os hex correspondem a `.claude/DESIGN.md`).

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{TITULO} · HUB 3I</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css" />
  <style>
    :root {
      /* Marca — escala Hub I3 (nome --pink legado, valores em vermelho) */
      --pink1: #F9E0E5;
      --pink2: #F1ADB7;
      --pink3: #E56F82;
      --pink4: #D73450;
      --pink5: #C8102E;
      --pink6: #A70D26;
      --pink7: #8C0B21;
      --pink8: #640A1B;
      --pink9: #4A0714;
      /* Acento */
      --orange: #FF8C00;
      --red:    #DD3D4C;
      /* Neutros / texto (Untitled-UI) */
      --fg-1:     #344054;
      --fg-2:     #667085;
      --fg-3:     #98A2B3;
      --surface:  #F2F4F7;
      --divider:  #D2D2D2;
      /* Status */
      --warn-bg: #FFFBE9; --warn-bd: #FFEA7B; --warn-fg: #AA8F00;
      --ok-bg:   #E4FFF2; --ok-bd:   #95FFCC; --ok-fg:   #0A9552;
      --err-bg:  #FFF8FB; --err-bd:  #FFCCE0; --err-fg:  #C8102E;
      --info-bg: #F1F8FF; --info-bd: #C3DFFF; --info-fg: #3C97FF;
      /* Tipografia */
      --font-body: 'Poppins', sans-serif;
      --font-ui:   'Inter', sans-serif;
      /* Espaçamento */
      --space-1: 4px;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-5: 24px;
      /* Border-radius */
      --radius-md:   8px;
      --radius-lg:   16px;
      --radius-full: 99px;
      /* Sombras (neutras) */
      --shadow-sm: 0 1px 3px rgba(16,24,40,0.08), 0 1px 2px rgba(16,24,40,0.05);
      --shadow-md: 0 4px 6px rgba(16,24,40,0.07), 0 2px 4px rgba(16,24,40,0.05);
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--font-body);
      font-size: 16px;
      line-height: 1.5;
      color: var(--fg-1);
      background: var(--surface);
    }

    /* ── Navbar (branca, marca vermelha) ── */
    .navbar {
      height: 56px;
      background: #fff;
      border-bottom: 1px solid var(--divider);
      position: sticky;
      top: 0;
      z-index: 100;
      display: flex;
      align-items: center;
      padding: 0 var(--space-5);
      gap: var(--space-4);
    }
    .navbar__brand { font-family: var(--font-body); font-size: 15px; font-weight: 700; color: var(--pink5); letter-spacing: 0.01em; }
    .navbar__sep   { color: var(--fg-3); font-size: 18px; }
    .navbar__sub   { font-family: var(--font-ui); font-size: 13px; font-weight: 500; color: var(--fg-2); }
    .navbar__badge {
      margin-left: auto;
      font-family: var(--font-ui);
      background: var(--pink1);
      color: var(--pink5);
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      padding: 3px 10px;
      border-radius: var(--radius-full);
    }

    /* ── Layout ── */
    .page-wrapper { max-width: 900px; margin: 0 auto; padding: 48px var(--space-5) 80px; }

    /* ── Hero ── */
    .hero { margin-bottom: 48px; }
    .hero__eyebrow {
      font-family: var(--font-ui);
      font-size: 11px; font-weight: 500; letter-spacing: 0.08em;
      text-transform: uppercase; color: var(--fg-3);
      margin-bottom: var(--space-3);
      display: flex; align-items: center; gap: var(--space-2);
    }
    .hero__title {
      font-size: 32px; font-weight: 600; line-height: 1.15;
      color: var(--fg-1); margin-bottom: var(--space-3);
    }
    .hero__title span { color: var(--pink5); }
    .hero__meta {
      font-family: var(--font-ui);
      font-size: 13px; color: var(--fg-3);
      display: flex; gap: var(--space-4); flex-wrap: wrap;
    }
    .hero__meta-item { display: flex; align-items: center; gap: var(--space-2); }

    /* ── Section ── */
    .section { margin-bottom: 48px; }
    .section__header {
      display: flex; align-items: center; gap: var(--space-3);
      margin-bottom: var(--space-5);
      padding-bottom: var(--space-4);
      border-bottom: 1px solid var(--divider);
    }
    .section__icon {
      width: 36px; height: 36px;
      background: var(--surface);
      border-radius: var(--radius-md);
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
      font-size: 18px;
    }
    .section__icon--vermelho { background: var(--pink1);  color: var(--pink5); }
    .section__icon--verde   { background: var(--ok-bg);  color: var(--ok-fg); }
    .section__icon--amarelo { background: var(--warn-bg); color: var(--warn-fg); }
    .section__icon--azul    { background: var(--info-bg); color: var(--info-fg); }
    .section__title  { font-size: 20px; font-weight: 600; line-height: 1.3; color: var(--fg-1); }
    .section__number { font-family: var(--font-ui); font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--fg-3); }

    /* ── Card ── */
    .card {
      background: #fff; border: 1px solid var(--fg-3);
      border-radius: var(--radius-md); box-shadow: var(--shadow-sm);
      padding: var(--space-4) var(--space-5); margin-bottom: var(--space-4);
    }
    .card__label {
      font-family: var(--font-ui);
      font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
      text-transform: uppercase; margin-bottom: var(--space-3);
      display: flex; align-items: center; gap: var(--space-2);
    }
    .card__label--erro    { color: var(--err-fg); }
    .card__label--sucesso { color: var(--ok-fg); }
    .card__label--info    { color: var(--info-fg); }
    .card__label--marca   { color: var(--pink5); }
    .card__body { font-size: 15px; color: var(--fg-2); line-height: 1.6; }
    .card__body p + p { margin-top: var(--space-3); }
    .card__body ul { padding-left: 20px; margin-top: var(--space-2); }
    .card__body li { margin-bottom: var(--space-1); }

    /* ── Callout ── */
    .callout {
      border-radius: var(--radius-md);
      border: 1px solid transparent;
      padding: var(--space-3) var(--space-4);
      margin-bottom: var(--space-4);
      display: flex; gap: var(--space-3); align-items: flex-start;
      font-size: 14px; line-height: 1.5;
    }
    .callout i { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
    .callout--erro    { background: var(--err-bg);  border-color: var(--err-bd);  color: var(--err-fg); }
    .callout--sucesso { background: var(--ok-bg);   border-color: var(--ok-bd);   color: var(--ok-fg); }
    .callout--info    { background: var(--info-bg); border-color: var(--info-bd); color: var(--info-fg); }
    .callout--atencao { background: var(--warn-bg); border-color: var(--warn-bd); color: var(--warn-fg); }
    .callout__text { flex: 1; }
    .callout__title { font-weight: 600; margin-bottom: var(--space-1); }

    /* ── Badge ── */
    .badge-tag {
      display: inline-flex; align-items: center; gap: var(--space-1);
      font-family: var(--font-ui);
      padding: 2px 10px; border-radius: var(--radius-full);
      font-size: 11px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
    }
    .badge-tag i { font-size: 11px; }
    .badge-tag--implementado { background: var(--ok-bg);   color: var(--ok-fg); }
    .badge-tag--backend      { background: var(--info-bg); color: var(--info-fg); }
    .badge-tag--frontend     { background: var(--pink1);   color: var(--pink5); }
    .badge-tag--neutro       { background: var(--surface); color: var(--fg-2); }

    /* ── Code block ── */
    pre {
      background: #4A0714; color: #F9E0E5;
      border-radius: var(--radius-md);
      padding: var(--space-4) var(--space-5);
      font-size: 13px; line-height: 1.6;
      overflow-x: auto; margin: var(--space-3) 0;
      font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace;
    }
    code {
      background: var(--surface); color: var(--pink5);
      padding: 1px 6px; border-radius: 4px;
      font-size: 13px;
      font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
    }
    pre code { background: none; color: inherit; padding: 0; border-radius: 0; font-size: inherit; }
    .kw  { color: #F1ADB7; }
    .fn  { color: #f0c674; }
    .st  { color: #95d0a8; }
    .cm  { color: #a88; font-style: italic; }
    .py  { color: #9ed0e7; }

    /* ── Table ── */
    .table-wrap { border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--fg-3); margin-bottom: var(--space-4); }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    thead tr { background: var(--surface); }
    thead th {
      padding: var(--space-3) var(--space-4); text-align: left;
      font-family: var(--font-ui);
      font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
      text-transform: uppercase; color: var(--fg-3);
      border-bottom: 1px solid var(--divider);
    }
    tbody td {
      padding: var(--space-3) var(--space-4);
      border-bottom: 1px solid var(--divider);
      color: var(--fg-2); vertical-align: top;
    }
    tbody tr:last-child td { border-bottom: none; }
    tbody tr:hover { background: var(--pink1); }

    /* ── Metrics ── */
    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--space-4); margin-bottom: var(--space-4); }
    .metric {
      background: #fff; border: 1px solid var(--fg-3);
      border-radius: var(--radius-md); box-shadow: var(--shadow-sm);
      padding: var(--space-4); text-align: center;
    }
    .metric__value { font-size: 32px; font-weight: 700; line-height: 1; color: var(--pink5); margin-bottom: var(--space-2); }
    .metric__label { font-family: var(--font-ui); font-size: 12px; font-weight: 500; color: var(--fg-3); text-transform: uppercase; letter-spacing: 0.05em; }

    /* ── Flow steps ── */
    .flow { display: flex; flex-direction: column; gap: var(--space-3); margin-bottom: var(--space-4); }
    .flow__step { display: flex; gap: var(--space-3); align-items: flex-start; }
    .flow__num {
      width: 24px; height: 24px;
      background: var(--pink5); color: #fff;
      border-radius: var(--radius-full);
      font-family: var(--font-ui);
      font-size: 11px; font-weight: 700;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; margin-top: 2px;
    }
    .flow__text { font-size: 14px; color: var(--fg-2); line-height: 1.5; }
    .flow__text strong { color: var(--fg-1); font-weight: 600; }

    /* ── Divider ── */
    hr { border: none; border-top: 1px solid var(--divider); margin: var(--space-5) 0; }

    /* ── Footer ── */
    footer {
      background: var(--pink9);
      color: rgba(255,255,255,0.5);
      font-family: var(--font-ui);
      font-size: 12px; padding: var(--space-5); text-align: center;
    }
    footer span { color: var(--pink3); }
  </style>
</head>
<body>

<!-- ── Navbar ── -->
<nav class="navbar">
  <span class="navbar__brand">HUB 3I</span>
  <span class="navbar__sep">·</span>
  <span class="navbar__sub">{SUBTITULO_NAVBAR}</span>
  <span class="navbar__badge">{BADGE_NAVBAR}</span>
</nav>

<div class="page-wrapper">

  <!-- ── Hero ── -->
  <header class="hero">
    <div class="hero__eyebrow">
      <i class="bi bi-file-text"></i>
      {EYEBROW}
    </div>
    <h1 class="hero__title">{TITULO_PARTE_1} <span>{TITULO_PARTE_2}</span></h1>
    <div class="hero__meta">
      <span class="hero__meta-item"><i class="bi bi-calendar"></i> {META_DATA}</span>
      <!-- adicione mais hero__meta-item conforme disponível (branch, módulo, etc.) -->
    </div>
  </header>

  <!-- ── Seções geradas a partir do conteúdo da conversa ── -->
  <!-- Repita o bloco abaixo para cada seção identificada -->
  <section class="section">
    <div class="section__header">
      <div class="section__icon section__icon--{vermelho|verde|amarelo|azul}">
        <i class="bi bi-{icone}"></i>
      </div>
      <div>
        <div class="section__number">{NUMERO_OU_LABEL} &nbsp;·&nbsp; <span class="badge-tag badge-tag--{backend|frontend|implementado}">{BADGE_TEXT}</span></div>
        <h2 class="section__title">{TITULO_SECAO}</h2>
      </div>
    </div>

    <!-- Use os componentes abaixo conforme o conteúdo real: -->

    <!-- Callout para problema/erro/aviso/resultado: -->
    <div class="callout callout--{erro|sucesso|info|atencao}">
      <i class="bi bi-{icone}"></i>
      <div class="callout__text">
        <div class="callout__title">{TIPO}: {FATO}.</div>
        {DESCRICAO}
      </div>
    </div>

    <!-- Card para explicações, contexto, soluções: -->
    <div class="card">
      <div class="card__label card__label--{marca|info|sucesso|erro}"><i class="bi bi-{icone}"></i> {LABEL}</div>
      <div class="card__body">
        <p>{CONTEUDO}</p>
      </div>
    </div>

    <!-- Métricas antes/depois (use quando houver números comparativos): -->
    <div class="metrics">
      <div class="metric">
        <div class="metric__value" style="color:var(--err-fg)">{VALOR_ANTES}</div>
        <div class="metric__label">{LABEL_ANTES}</div>
      </div>
      <div class="metric">
        <div class="metric__value" style="color:var(--ok-fg)">{VALOR_DEPOIS}</div>
        <div class="metric__label">{LABEL_DEPOIS}</div>
      </div>
    </div>

    <!-- Steps numerados (para processos/sequências): -->
    <div class="flow">
      <div class="flow__step">
        <div class="flow__num">1</div>
        <div class="flow__text"><strong>{PASSO}</strong> — {DESCRICAO}</div>
      </div>
    </div>

    <!-- Code block (para trechos de código relevantes): -->
    <pre><code>{CODIGO_COM_CLASSES_DE_HIGHLIGHT}</code></pre>

    <!-- Tabela (para comparativos, listas estruturadas): -->
    <div class="table-wrap">
      <table>
        <thead><tr><th>{COL1}</th><th>{COL2}</th></tr></thead>
        <tbody>
          <tr><td>{VALOR1}</td><td>{VALOR2}</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- ── Arquivos modificados (incluir apenas se houve mudanças de código) ── -->
  <section class="section">
    <div class="section__header">
      <div class="section__icon section__icon--vermelho">
        <i class="bi bi-git"></i>
      </div>
      <div>
        <div class="section__number">Resumo</div>
        <h2 class="section__title">Arquivos modificados</h2>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Arquivo</th><th>Tipo</th><th>Mudança</th></tr></thead>
        <tbody>
          <tr>
            <td><code>{CAMINHO}</code></td>
            <td><span class="badge-tag badge-tag--{backend|frontend}">{TIPO}</span></td>
            <td>{DESCRICAO_MUDANCA}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

</div><!-- /page-wrapper -->

<footer>
  HUB 3I · <span>{BADGE_NAVBAR}</span> · {META_DATA} · Claude Code
</footer>

</body>
</html>
```

---

## Passo 5 — Retornar o resultado

Após gravar o arquivo, informe ao usuário:

```
Relatório gerado: {CAMINHO_COMPLETO}
```

Se quiser visualizar, abra com: `xdg-open {CAMINHO_COMPLETO}` ou arraste o arquivo para o browser.

---

## Mapa de ícones (Bootstrap Icons)

Use sempre classes `bi bi-*` (Bootstrap Icons). Equivalências úteis:

| Semântica            | Classe Bootstrap Icons          |
|----------------------|---------------------------------|
| Problema/alerta      | `bi-exclamation-circle`         |
| Erro/cancelado       | `bi-x-circle`                   |
| Investigação/busca   | `bi-search`                     |
| Backend/lógica       | `bi-lightning`, `bi-hash`, `bi-database`, `bi-hdd-stack` |
| Frontend/UI          | `bi-sliders`, `bi-display`, `bi-layout-text-window` |
| Integração/fluxo     | `bi-arrow-repeat`, `bi-link-45deg`, `bi-diagram-3` |
| Arquivo/código       | `bi-git`, `bi-file-text`, `bi-code-slash` |
| Próximos passos      | `bi-arrow-right`, `bi-check2-square`, `bi-flag` |
| Data                 | `bi-calendar`                   |
| Sucesso              | `bi-check-circle`               |

---

## Regras obrigatórias do Design System (Hub I3)

- **Nunca** invente tokens CSS fora dos definidos no `:root` acima (todos espelham `.claude/DESIGN.md`)
- **Nunca** use gradientes, `backdrop-blur`, texturas ou imagens decorativas
- **Nunca** use emojis — estado é comunicado por ícone Bootstrap Icons + badge + cor
- **Nunca** use Feather Icons — este projeto usa **Bootstrap Icons** (`bi bi-*`)
- **Cor de marca:** vermelho `#C8102E` (`--pink5`) para ações, links, ícones e destaques
- **Tipografia:** Poppins (corpo/títulos) + Inter (rótulos, metadados, UI)
- **Espaçamento** apenas nos valores da escala: 4/8/12/16/24px
- **Border-radius** apenas: 8/16/99px
- **Sombras** sempre neutras (cinza-azulado dessaturado) — nunca coloridas
- **`max-width: 900px`** no `.page-wrapper`
- **Hover de tabela:** `var(--pink1)` (`#F9E0E5`) — nunca outra cor
- **Saída:** sempre em `.claude/docs/reports/` (dentro do projeto)
- Separador permitido: ponto médio `·`
- Callout sempre no formato `<Tipo>: <Fato>.` — dois-pontos seguido de frase declarativa
