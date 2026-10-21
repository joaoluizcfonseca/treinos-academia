<p align="center">
  <img src="docs/banner.png" alt="Treinos até o verão: app de treino feito por Knz" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/HTML%20%2B%20CSS%20%2B%20JS-sem%20depend%C3%AAncias-D97F00?style=flat-square" alt="HTML, CSS e JS sem dependências">
  <img src="https://img.shields.io/badge/testes-Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white" alt="Testes com Playwright">
  <img src="https://img.shields.io/badge/feito%20por-Knz-141414?style=flat-square" alt="Feito por Knz">
</p>

<p align="center">
  App de treino pra acompanhar academia e corrida até o verão.<br>
  Um arquivo HTML só: instala no celular e funciona sem internet.<br>
  <b><a href="https://joaoluizcfonseca.github.io/treinos-academia/">Abrir o app</a></b>
</p>

---

## Telas

| Hoje | Pesos | Progresso | Calendário |
|:---:|:---:|:---:|:---:|
| <img src="docs/tela-hoje.png" width="200" alt="Treino do dia com os exercícios e os pesos"> | <img src="docs/tela-pesos.png" width="200" alt="Pesos de cada exercício, com o gráfico de evolução aberto"> | <img src="docs/tela-progresso.png" width="200" alt="Painel geral: números do verão e gráficos de treinos, km, peso e força por semana"> | <img src="docs/tela-calendario.png" width="200" alt="Calendário até o verão"> |

### Visuais

| Maré (padrão) | Anilha | Caderno | Original |
|:---:|:---:|:---:|:---:|
| <img src="docs/visual-mare.png" width="200" alt="Visual Maré: claro, cor de mar, com o sol andando no horizonte até o verão"> | <img src="docs/visual-anilha.png" width="200" alt="Visual Anilha: piso de academia, letra condensada e o contador do verão desenhado como anilha"> | <img src="docs/visual-caderno.png" width="200" alt="Visual Caderno: folha pautada com margem e os números escritos à caneta"> | <img src="docs/visual-original.png" width="200" alt="Visual original: preto, letra larga e a cor do nível"> |

### Retrospectiva do verão

| Treinos | Treino favorito | Corridas | Resumo |
|:---:|:---:|:---:|:---:|
| <img src="docs/retro-treinos.png" width="200" alt="Quantas vezes treinou, com o calendário do verão inteiro"> | <img src="docs/retro-treino-favorito.png" width="200" alt="O treino mais feito e os que vieram depois"> | <img src="docs/retro-corridas.png" width="200" alt="Quilômetros corridos e cada corrida do verão"> | <img src="docs/retro-resumo.png" width="200" alt="Resumo do verão pra tirar print"> |

<p align="center"><sub>As telas usam dados de exemplo, no visual padrão (Maré). Claro ou escuro segue o celular, e tem um botão pra trocar.</sub></p>

## O que ele faz

- 🏋️ **Treino do dia:** a lista de exercícios com o peso de cada um, já preenchido com o da última vez. Terminou, é um toque em **Terminei o treino**, sem marcar série por série. Se você anotou pesos e ainda não marcou o treino, o app lembra.
- ⏪ **Esqueceu de marcar?** Os dias de treino da última semana que ficaram sem marcar aparecem no Hoje, com o treino mais provável (pelo que tem de peso anotado no dia). Um toque em **Treinei** e a sequência volta. Marcou o treino errado hoje? **Trocar o treino** muda sem desmarcar.
- ⬆️ **Subir carga:** quando o peso de um exercício fica igual 3 vezes seguidas, o app sugere subir. Ao terminar, mostra em quais exercícios a carga subiu.
- 🔁 **Pegadas:** a puxada guarda um peso pra cada pegada (aberta, fechada, triângulo e supinada).
- 📒 **Pesos por treino:** a lista de todos os exercícios com o peso atual, a evolução e os recordes.
- 📊 **Gráfico de evolução:** na aba Pesos, tocar no nome do exercício abre um gráfico com todos os pesos anotados. Tocar no gráfico mostra o peso de cada dia, e a lista completa fica logo abaixo.
- 🧗 **Caminho até a primeira barra:** pendurar na barra fecha o treino de segunda a sexta, e você anota quantos segundos aguentou. O Progresso mostra a meta (30 s pendurado), a evolução e quando já dá pra tentar a primeira barra.
- 🧭 **Painel geral:** no topo do Progresso, os números principais (treinos, sequência, corrida, peso, força e nível) e quatro gráficos com as mesmas semanas no eixo: treinos por semana (com a meta de 5), km corridos, peso do corpo e força. Tocar numa semana marca ela nos quatro e mostra os valores; também tem a tabela.
- 💪 **Evolução das cargas:** todos os exercícios com peso anotado, do primeiro registro ao atual, do que mais subiu pro que menos. Tocar abre o gráfico na aba Pesos.
- 📈 **Progresso:** resumo da semana, séries por músculo (pelo plano dos treinos marcados), corridas, peso do corpo com a meta de proteína pelo seu peso, nível e conquistas. A pesagem é uma vez por semana, sempre na mesma balança e no mesmo horário.
- 🗓️ **Calendário:** todos os dias até o verão. Tocando num dia, dá pra marcar ou tirar treino e corrida (com distância e tempo).
- 🌞 **Retrospectiva do verão:** no dia 21/12 ela abre sozinha, em histórias de tela cheia, no estilo das retrospectivas de fim de ano dos apps de música. São uns 15 slides: quantas vezes treinou (com o calendário do verão inteiro), séries e toneladas levantadas, treino favorito, dia favorito, músculo que mais trabalhou, onde mais ficou forte, caminho até a primeira barra, corridas, maior sequência, peso do corpo, nível e um perfil de treino. No fim, um resumo pra tirar print. Antes de 21/12 dá pra ver a prévia no Progresso, com a projeção de quantos treinos dá pra fazer até lá.
- 📅 **Retrospectiva de cada mês:** no Progresso tem uma por mês. Nos 3 primeiros dias do mês, o Hoje avisa que a do mês anterior saiu.
- ▶️ **Histórias:** toque na direita avança, na esquerda volta, segurar pausa; no computador, setas e Esc. Quem pede menos movimento no celular vê tudo sem animação e avança no toque.
- 🎨 **Visuais:** o app abre na **Maré** e tem mais três pra escolher no fim do Progresso, cada um com tema claro e escuro e a própria escada de cores de nível. **Maré**: claro, cor de mar, com um sol que anda no horizonte até o verão. **Anilha**: piso de academia, letra condensada e o contador desenhado como anilha, na cor do nível. **Caderno**: folha pautada com margem, títulos com marca-texto e o que você anota escrito à caneta; no escuro, vira lousa (e as cores de nível viram giz). **Original**: o primeiro visual do app, preto e com letra larga. As miniaturas da escolha já mostram o seu número, o seu sol e a cor do seu nível. A retrospectiva tem o visual dela e fica igual em todos. A escolha fica salva no celular.
- 📲 **Funciona sem internet:** pelo GitHub Pages, o app se instala na tela inicial do celular e abre e salva sem sinal, com backup pra exportar e importar os dados.
- 🏖️ **Depois do verão:** o app continua. O cabeçalho conta os dias de verão, o calendário segue semana a semana e os feriados vão até maio de 2027.

## Como usar

### No celular, sem internet

1. Ative o GitHub Pages em **Settings → Pages → Branch `main` → `/ (root)` → Save**. Em um minuto o app fica em **[joaoluizcfonseca.github.io/treinos-academia](https://joaoluizcfonseca.github.io/treinos-academia/)** (num fork, troque pelo seu usuário e o nome do repositório).
2. Abra esse link no celular, com internet, e instale:
   - **iPhone (Safari):** botão de compartilhar → **Adicionar à Tela de Início**.
   - **Android (Chrome):** menu **⋮** → **Instalar app** (ou **Adicionar à tela inicial**).
3. Pronto: o app abre pelo ícone e funciona sem internet. Quando tiver sinal, ele baixa a versão nova sozinho, que entra na próxima vez que abrir.

Já tem dados de outro lugar? No app instalado, vá em **Progresso → Backup → Importar backup** e escolha o arquivo `.json`.

### No computador

Abra o `index.html` no navegador. Não tem nada pra instalar.

## Onde ficam os dados

- **No app instalado** (GitHub Pages), os dados ficam só no celular, em `localStorage`. Em **Progresso → Backup** dá pra exportar um arquivo com tudo e importar de volta, em outro celular ou depois de reinstalar. Importar num app vazio traz tudo; num app com dados, entra só o que falta, sem apagar nada.
- **No claude.ai**, o app salva a si mesmo: cada mudança publica uma versão nova da página com os dados dentro, num JSON em `<script id="state">`.

Este repositório vem com os dados vazios.

### Sem internet, como funciona

O `index.html` é o mesmo nos dois lugares. Fora do claude.ai, ele liga sozinho o que o app instalado precisa:

| Arquivo | Pra que serve |
|---|---|
| `manifest.webmanifest` | Nome, ícone e cores do app na tela inicial |
| `sw.js` | Service worker: guarda o app na primeira visita e abre dele depois, com ou sem sinal |
| `icons/` | Ícone do app (o sol no caminho até o verão) |
| `fonts/` | As fontes do app (Archivo, Bricolage Grotesque e Kalam, licença SIL OFL 1.1), pra não depender do Google Fonts |

<details>
<summary><b>Formato dos dados</b></summary>

| Chave | Conteúdo |
|---|---|
| `logs` | dia → treino feito |
| `runs` | dia → `{km, min}` da corrida |
| `ex` | dia → treino escolhido e pegada da puxada |
| `loads` | exercício → `{dia: valor}`: kg; no pendurar, segundos (e repetições nas negativas antigas) |
| `weight` | dia → peso do corpo em kg |
| `hr`, `sec` | histórico usado no XP e nas conquistas |
| `supp`, `chal`, `flash`, `habits` | dados de funções que saíram do app, só guardados |
| `rev` | versão dos dados, sobe a cada salvamento |

</details>

## Como o código está organizado

Tudo fica em `index.html`, porque o app se reescreve inteiro pra salvar:

| Parte | O que tem |
|---|---|
| `<style id="app-style">` | Estilos, divididos por tela (Hoje, Pesos, Progresso, Calendário). Cores em variáveis no `:root`, tema claro em `[data-theme="light"]` |
| `<script id="state">` | Os dados salvos (JSON) |
| `<script id="app-script">` | O app: plano de treino, cálculos de sequência e XP, telas, retrospectivas, eventos e salvamento |

As retrospectivas saem de uma função só (`recap`), que calcula os números de qualquer período: o verão inteiro ou um mês. Os slides são montados a partir desses números, e os que ficariam vazios (sem corrida, sem pesagem) não aparecem.

Cada toque atualiza o estado e redesenha a tela. Mudanças rápidas, como os pesos, ficam primeiro no celular e são publicadas juntas numa pausa, pra página não recarregar no meio do treino.

Se o dia vira com o app aberto, ele atualiza sozinho pra mostrar o dia novo, mas espera quem está digitando um peso ou vendo uma retrospectiva; o que foi digitado fica no dia em que foi feito.

Se sair uma versão nova antes de publicar (outro aparelho salvou, ou o app foi atualizado), o que estava só no celular entra na versão nova em vez de se perder. Se a tela não consegue publicar (aberta só pra ver, ou o salvamento não carregou), nada trava: o app avisa no topo, segue guardando tudo no celular e manda pro app no primeiro toque quando abrir de novo. Falha passageira na publicação ganha uma segunda tentativa. Com uma retrospectiva aberta, a publicação espera ela fechar, pra página não recarregar no meio.

## Testes

Testes de ponta a ponta com [Playwright](https://playwright.dev/python/), que abrem o app num navegador de verdade:

```bash
pip install -r requirements-dev.txt
playwright install chromium
pytest
```

Eles cobrem:

- todas as abas em quatro dias diferentes (semana fechada, sábado, domingo e feriado) e nos dois temas;
- o app vazio e todos os botões;
- um treino do começo ao fim, com os pesos e um toque pra terminar;
- o peso passando de um treino pro outro e as pegadas com pesos separados;
- os avisos: subir carga, carga que subiu e treino não marcado;
- os dias que ficaram sem marcar: marcar com um toque, escolher outro treino, dispensar o aviso, fim de semana só com peso anotado e nada de aviso pra quem parou de treinar;
- a folha do dia no calendário: distância da corrida e ela cabendo em celular baixo;
- o app sem marcação de suplementos, com a meta de proteína no Progresso;
- trocar o treino de hoje depois de marcado;
- o gráfico de evolução: abrir, tocar num dia e fechar;
- a barra: pendurar todo dia útil, segundos com a unidade certa, a meta, a linha da meta e valor inválido;
- o painel geral: números, os quatro gráficos, tocar e usar as setas pra trocar de semana e o que aparece quando falta corrida ou pesagem;
- a evolução das cargas, abrindo o gráfico do exercício na aba Pesos;
- desmarcar um treino sem deixar peso sobrando;
- a tela em celulares pequenos, a partir de 320 px;
- o app se salvando e abrindo de novo com os mesmos dados, sem perder anotação quando sai uma versão nova, com uma nova tentativa quando a publicação falha e sem erro no conflito;
- uma tela que não consegue salvar: os campos nunca travam, o aviso aparece em todas as abas, tudo fica no celular e vai pro app no primeiro toque depois;
- o app instalado: abre e salva sem internet (com o servidor desligado), as fontes vêm junto, exportar e importar backup, arquivo que não é backup recusado, e nada disso aparece dentro do claude.ai;
- o texto em cima da cor do nível com o melhor contraste nos dois temas;
- a retrospectiva do verão com um verão inteiro inventado: abre sozinha em 21/12 uma vez só, com os números certos e sem texto quebrado;
- a prévia antes de 21/12, a retrospectiva vazia e a de cada mês, com o aviso nos 3 primeiros dias do mês;
- as histórias: passar sozinho, toque pra avançar e voltar, segurar pra pausar e as setas do teclado;
- tudo cabendo num celular de 320 px, nos dois temas;
- o app depois do verão: dias de verão no cabeçalho, calendário continuando e sem projeção de peso;
- Natal e Ano-Novo como feriado;
- os visuais: o app abrindo na Maré, escolher outro (inclusive o original), continuar escolhido depois de abrir de novo e todas as abas de cada um num celular de 320 px nos dois temas, com o texto em cima da cor do nível legível;
- a retrospectiva igual em todos os visuais, tela por tela;
- subir de nível mostrando a cor nova, com o nome certo pro tema (caneta ou giz no Caderno);
- a virada do dia com o app aberto: espera terminar de digitar, guarda o peso no dia certo e depois mostra o dia novo.

---

<p align="center">Feito por <b>Knz</b> 🇧🇷</p>
