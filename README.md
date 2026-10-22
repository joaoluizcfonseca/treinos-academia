<p align="center">
  <img src="docs/banner.png" alt="Treinos até o verão: app pessoal de treino" width="100%">
</p>

<p align="center">
  App de treino de uso pessoal para acompanhar academia e corrida até o verão.<br>
  Um único arquivo HTML que se instala no celular e funciona sem internet.
</p>

<p align="center">
  <img alt="Projeto de uso pessoal" src="https://img.shields.io/badge/projeto-uso%20pessoal-0D3B4F?style=flat-square">
  <img alt="PWA que funciona offline" src="https://img.shields.io/badge/PWA-funciona%20offline-D97F00?style=flat-square">
  <img alt="HTML, CSS e JavaScript sem dependências" src="https://img.shields.io/badge/HTML%20%2B%20CSS%20%2B%20JS-sem%20depend%C3%AAncias-23949D?style=flat-square">
  <img alt="131 testes com Playwright" src="https://img.shields.io/badge/testes-131%20com%20Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white">
</p>

<p align="center">
  <a href="https://joaoluizcfonseca.github.io/treinos-academia/"><b>Abrir o app</b></a> &nbsp;|&nbsp;
  <a href="#telas">Telas</a> &nbsp;|&nbsp;
  <a href="#funcionalidades">Funcionalidades</a> &nbsp;|&nbsp;
  <a href="#como-funciona">Como funciona</a> &nbsp;|&nbsp;
  <a href="#testes">Testes</a>
</p>

> [!NOTE]
> **Projeto de uso pessoal.** Este é o app que eu uso para registrar os meus treinos. Ele foi feito sob medida para a minha rotina (plano de treino, metas e feriados) e não é um produto: não tem contas, servidor nem suporte para outras pessoas. O código está público para consulta.

## Telas

| Hoje | Pesos | Progresso | Calendário |
|:---:|:---:|:---:|:---:|
| <img src="docs/tela-hoje.png" width="200" alt="Treino do dia com os exercícios e os pesos"> | <img src="docs/tela-pesos.png" width="200" alt="Pesos de cada exercício, com o gráfico de evolução aberto"> | <img src="docs/tela-progresso.png" width="200" alt="Painel geral com os números e os gráficos semanais"> | <img src="docs/tela-calendario.png" width="200" alt="Calendário até o verão"> |

<p align="center"><sub>Telas com dados de exemplo, no visual padrão (Maré).</sub></p>

## Funcionalidades

### Treino

- **Treino do dia:** os exercícios com o peso da última vez já preenchido. Um toque em *Terminei o treino* registra tudo, sem marcar série por série.
- **Pesos por exercício:** histórico, recordes e gráfico de evolução. A puxada guarda um peso para cada pegada.
- **Montar o treino:** criar exercício novo (ou escolher um que já existe, com os pesos dele), marcar os dias em que ele entra, mudar séries e repetições, reordenar e excluir, com desfazer. A mudança vale a partir do dia em que foi feita: os treinos que já passaram continuam contando como foram.
- **Sugestão de carga:** quando o peso de um exercício se repete três vezes seguidas, o app sugere subir.
- **Treinos esquecidos:** dias da semana sem registro aparecem no topo, com o treino mais provável, para marcar com um toque.
- **Primeira barra fixa:** o tempo pendurado na barra entra em todos os treinos da semana, com meta e evolução até tentar a primeira barra.

| Montar o treino | Novo exercício |
|:---:|:---:|
| <img src="docs/tela-montar.png" width="200" alt="Treino aberto para editar: subir, descer, mudar séries e excluir cada exercício"> | <img src="docs/tela-novo-exercicio.png" width="200" alt="Folha de novo exercício com nome, dias, séries, repetições, tipo e músculo"> |

### Progresso

- **Painel geral:** treinos, sequência, corrida, peso, força e nível, com gráficos semanais na mesma escala de tempo.
- **Treinos por ano:** um quadradinho por dia, ano por ano, como o gráfico de contribuições do GitHub. Quanto mais forte a cor, mais peso levantado no dia; tocar ou arrastar o dedo mostra o treino de cada dia.
- **Detalhes:** evolução das cargas, séries por músculo, corridas (distância, tempo e ritmo) e peso corporal com a meta de proteína.
- **Calendário** até o verão, com feriados, para marcar ou corrigir qualquer dia.
- **Nível e conquistas**, incluindo conquistas secretas.

<p align="center"><img src="docs/treinos-por-ano.png" width="390" alt="Treinos por ano: a grade do ano com os dias de treino coloridos de setembro a dezembro"></p>

### Retrospectivas

- **Do verão:** no dia 21/12 ela abre sozinha, em histórias de tela cheia no estilo das retrospectivas dos apps de música: treinos, toneladas levantadas, treino favorito, evolução das cargas, corridas, maior sequência, nível e perfil de treino. Termina num cartão para compartilhar.
- **De cada mês:** uma por mês, com aviso nos primeiros dias do mês seguinte.

| Treinos | Treino favorito | Corridas | Resumo |
|:---:|:---:|:---:|:---:|
| <img src="docs/retro-treinos.png" width="200" alt="Quantas vezes treinou, com o calendário do verão inteiro"> | <img src="docs/retro-treino-favorito.png" width="200" alt="O treino mais feito e os que vieram depois"> | <img src="docs/retro-corridas.png" width="200" alt="Quilômetros corridos e cada corrida do verão"> | <img src="docs/retro-resumo.png" width="200" alt="Cartão de resumo do verão"> |

### Visuais

Quatro visuais, cada um com tema claro e escuro e a própria escala de cores por nível. A escolha fica salva no aparelho.

| Maré (padrão) | Anilha | Caderno | Original |
|:---:|:---:|:---:|:---:|
| <img src="docs/visual-mare.png" width="200" alt="Visual Maré: cor de mar, com o sol andando no horizonte até o verão"> | <img src="docs/visual-anilha.png" width="200" alt="Visual Anilha: piso de academia e o contador desenhado como uma anilha"> | <img src="docs/visual-caderno.png" width="200" alt="Visual Caderno: folha pautada e números escritos à caneta"> | <img src="docs/visual-original.png" width="200" alt="Visual Original: preto, letra larga e a cor do nível"> |

### Sem internet

Instalado na tela inicial, o app abre e salva sem conexão. Os dados ficam no aparelho, com exportação e importação de backup em **Progresso → Backup**, e o app lembra de exportar um backup uma vez por semana.

## Como funciona

- **Um arquivo só.** O `index.html` contém o HTML, o CSS, o JavaScript e os dados, num JSON em `<script id="state">`. Não tem build, framework nem dependências.
- **App instalado (GitHub Pages).** Os dados ficam no `localStorage` do aparelho. O service worker (`sw.js`) guarda o app na primeira visita, abre a partir dele com ou sem sinal e baixa as atualizações em segundo plano.
- **No claude.ai.** O app publica uma nova versão de si mesmo a cada alteração, com os dados embutidos. Se a publicação falhar, nada trava: o que foi anotado fica no aparelho e é enviado no próximo toque.
- **Sem perda de dados.** Anotações feitas sobre uma versão antiga são mescladas na nova, e se o dia virar com o app aberto, ele espera terminar a digitação antes de atualizar a tela.

<details>
<summary><b>Formato dos dados</b></summary>

| Chave | Conteúdo |
|---|---|
| `logs` | dia → treino feito |
| `runs` | dia → `{km, min}` da corrida |
| `ex` | dia → treino escolhido e pegada da puxada |
| `loads` | exercício → `{dia: valor}` em kg (no tempo pendurado, em segundos) |
| `weight` | dia → peso corporal em kg |
| `plan` | dia da mudança → treino → exercícios (o plano montado no app; cada dia usa o que valia nele) |
| `hr`, `sec` | histórico usado no nível e nas conquistas |
| `supp`, `chal`, `flash`, `habits` | dados de funções antigas, apenas preservados |
| `rev` | versão dos dados, incrementada a cada salvamento |

</details>

### Estrutura do repositório

```
.
├── index.html             o app inteiro: HTML, CSS, JavaScript e dados
├── manifest.webmanifest   instalação na tela inicial (nome, ícone e cores)
├── sw.js                  service worker: funcionamento sem internet
├── icons/                 ícones do app
├── fonts/                 fontes do app (SIL Open Font License 1.1)
├── docs/                  imagens deste README
├── tests/                 testes de ponta a ponta (pytest + Playwright)
└── requirements-dev.txt   dependências dos testes
```

## Instalação

1. Abra **[joaoluizcfonseca.github.io/treinos-academia](https://joaoluizcfonseca.github.io/treinos-academia/)** no celular, com internet.
2. Instale na tela inicial:
   - **iPhone (Safari):** botão de compartilhar → **Adicionar à Tela de Início**.
   - **Android (Chrome):** menu **⋮** → **Instalar app**.
3. Para trazer dados de outro aparelho: **Progresso → Backup → Importar backup**.

No computador, basta abrir o `index.html` no navegador.

## Testes

São 131 testes de ponta a ponta com [pytest](https://pytest.org) e [Playwright](https://playwright.dev/python/), que abrem o app num navegador de verdade:

```bash
pip install -r requirements-dev.txt
playwright install chromium
pytest
```

Eles cobrem:

- **Treino:** do começo ao fim, com pesos, pegadas, sugestão de carga, treinos esquecidos e desmarcar sem deixar dados para trás.
- **Cálculos:** sequência, nível, séries por músculo, painel geral e evolução das cargas.
- **Montar o treino:** exercício novo e já existente, dias, séries, ordem, excluir com desfazer, o histórico intacto e telas pequenas.
- **Treinos por ano:** o tom de cada dia pelo peso levantado, toque, arrasto e setas, vários anos e a mesma conta da retrospectiva.
- **Retrospectivas:** verão inteiro simulado, prévia, retrospectiva de cada mês, navegação das histórias e o app depois do verão.
- **Visuais:** os quatro, nos dois temas, em telas a partir de 320 px, com contraste legível sobre a cor do nível.
- **Salvamento:** versões novas, conflitos, falhas de publicação e telas que não conseguem salvar, sem nunca travar os campos.
- **Sem internet:** abrir e salvar com o servidor desligado, fontes incluídas, backup de ida e volta e o lembrete semanal de backup.

## Licença

Projeto pessoal, sem licença de uso: todos os direitos reservados. As fontes em `fonts/` (Archivo, Bricolage Grotesque e Kalam) são distribuídas sob a [SIL Open Font License 1.1](fonts/OFL-Archivo.txt).

---

<p align="center">Feito por <b>João Candaten</b> 🇧🇷</p>
