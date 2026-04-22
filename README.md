# ENTROPIA v1.0

Sistema de mesa para um RPG próprio, inspirado visualmente em [crisordemparanormal.com](https://crisordemparanormal.com).

Aplicativo desktop em Python + Tkinter, pensado para uso na mesa: uma parte para **jogadores** (ficha de personagem, armamentos) e uma parte só para o **mestre** (escudo do mestre, rolagem de dados, bestiário), com o objetivo futuro de sincronizar rolagens em rede para que o mestre veja tudo o que os jogadores rolam.

> *"O Caos Sempre Reina."*

---

## Estado atual

- **Tela de login** completa.
- **Tela principal** maximizada, abre após login (mesmo layout para Mestre e Jogador por enquanto).
- **Lista de personagens do usuário** em cards, na parte central da tela principal. Cada usuário só vê os personagens que ele mesmo criou.
- **Criação de personagem** acessível pelo botão "Novo Personagem" no canto superior direito da tela principal.

### O que a tela de login já faz

- Fundo preto, tema escuro minimalista.
- **Fade-in** suave ao abrir o programa (título + campos aparecem gradualmente).
- Três campos: **Usuário**, **Senha**, **Palavra-chave**.
- Campos sem "caixa" — apenas uma linha fina embaixo que acende em roxo ao focar.
- Fonte Segoe UI Light (limpa, sem serifa).
- Login tolerante:
  - **Usuário** compara ignorando maiúsculas/minúsculas e espaços extras.
  - **Palavra-chave** também ignora maiúsculas/minúsculas.
  - **Senha** continua sensível (maiúsculas e minúsculas importam).
- Mensagens de erro específicas: indicam se o problema foi o usuário, a senha ou a palavra-chave.
- Ao logar com sucesso, mostra uma mensagem com o papel (Mestre ou Jogador) e fecha — a próxima etapa será abrir a tela correspondente.

---

### Tela principal — abas

A tela principal tem duas abas no topo:

- **Personagens** — lista de cards (descrita abaixo).
- **Rolador** — rolador de dados configurável da sessão (descrito mais abaixo).

#### Aba Personagens

- Cabeçalho com a contagem de personagens do usuário à esquerda e o botão roxo **Novo Personagem** à direita.
- Cards em grade de 3 colunas, cada um com:
  - **Foto** do personagem (thumbnail à esquerda; cards sem foto ficam só com o texto).
  - **Nome** em destaque.
  - **Nível de LC** abaixo do nome (`LC N`, ou `Sem LC` se o campo não tiver sido preenchido).
  - **Data de criação** em roxo (`Registrado em DD/MM/AA`).
  - **×** no canto superior direito (apenas para o dono da ficha) — exclui o personagem com confirmação.
  - Botão roxo **Acessar Ficha** no canto inferior direito — abre a ficha em modo de edição quando o usuário é o dono.
- **Filtro por dono**: cada **jogador** só vê os personagens onde `criado_por` bate com seu login (comparação ignorando maiúsculas/minúsculas). AMÍLIA nunca vê os personagens de DANTE, e vice-versa.
- **Visão do Mestre**: usuários com `papel = "mestre"` **veem todas as fichas** de todos os jogadores (e de outros mestres), com o nome do dono em destaque (`jogador: NOME`) nos cards alheios. O Mestre também pode editar e excluir qualquer ficha.
- A lista atualiza automaticamente assim que um novo personagem é salvo.

#### Aba Rolador

Rolador de dados configurável (sessão local, sem persistência em disco):

- **qtd** (1–100) **d** **lados** (≥ 2) com **modificador** opcional (positivo ou negativo, ex: `-3`).
- Botão **Rolar** (ou tecla Enter) sorteia cada dado individualmente, soma e aplica o modificador.
- Painel "última rolagem" mostra a expressão (ex: `4d20+6`), o total em destaque e o detalhe das rolagens individuais.
- **Histórico da sessão** abaixo, lista até 50 entradas; botão **Limpar** zera. O histórico não persiste entre execuções.

#### Aba Bestiário  *(somente Mestre)*

Visível apenas para usuários com `papel = "mestre"`. Lista compartilhada entre mestres, salva em `bestiario.json` (chave `monstros`). Botão **+ Adicionar monstro** cria uma entrada editável inline com:

- **Imagem** — quadrado à esquerda do card. Clicar abre o navegador de arquivos (PNG, JPG, GIF, BMP, WebP); a imagem é redimensionada e copiada para `imagens/` (mesmo sistema das fichas de personagem).
- **nome** e **descrição** — texto livre.
- **VIDA** e **ENERGIA** — cada uma com setas ◀ ▶ para ajustar o valor atual durante o combate e campos editáveis de `atual / máxima`. O atual é sempre mantido em `0 ≤ atual ≤ máxima`.
- **×** pede confirmação e remove o monstro.

Toda edição é **auto-salva** imediatamente em `bestiario.json` — útil durante o combate para não perder o HP do monstro em caso de fechamento acidental.

### Tela de ficha (criação / edição)

A ficha é organizada em **duas abas**: **Personagem** (atributos básicos) e **Inventário** (armas + itens normais).

#### Aba Personagem

Campos:
1. **Imagem** — clique no quadrado abre o navegador de arquivos (PNG, JPG, GIF, BMP, WebP). A imagem é redimensionada e encaixada no quadrado.
2. **Nome**
3. **Idade**
4. **Nascimento** — formato DD / MM / AA.
5. **Data de cristalização** — formato DD / MM / AA.
6. **Nível de LC** — 11 botões (LC 0 a LC 10), o selecionado fica roxo. Mudar o LC **recalcula automaticamente** as máximas de Vida e Energia.
7. **Vida** — barra vermelha com display `atual/máxima`. Começa em **15** no LC 0 e cresce **+15 por LC**. Setas ◀ ▶ para ajustar a vida atual.
8. **Energia** — barra azul, mesmo sistema da vida. Começa em **18** no LC 0 e cresce **+12 por LC**.
9. **Sanidade** — barra roxa, vai de **0% a 150%**, começa em **100%**.
10. **Atributos** — seis atributos (AGILIDADE, CRISTAL, FORÇA, INTELIGÊNCIA, PRESENÇA, VITALIDADE), todos começam em 0 e ajustáveis com `−` / `+`.
    - **PRESENÇA** soma **+4** à energia máxima por ponto.
    - **VITALIDADE** soma **+5** à vida máxima por ponto.
11. **Descrição / Histórico** — área de texto livre para anotações sobre o personagem.

#### Aba Inventário

Dividida em duas seções dentro da mesma aba:

**Armas** — botão **+ Adicionar arma** cria uma entrada editável inline com:

- **nome**
- **tipo** — dropdown com `Pistola`, `Rifle`, `Faca`, `Grimorio`, `Outro`.
- **dano** — texto livre em notação de dados: `1d6` (1 dado de 6 lados), `2d6+3`, etc.
- **munição** — só aparece para `Pistola` e `Rifle`. Setas ◀ ▶ ajustam a munição atual; campos editáveis para `atual / máxima`. Trocar o tipo para uma arma branca remove o campo automaticamente.
- **descrição** — campo livre.

**Itens** — botão **+ Adicionar item** cria uma entrada com:

- **tipo** — dropdown com `Municao`, `Cura`, `Consumivel`, `Equipamento`, `Outro`.
- **nome** — livre (ex: "Pente .45", "Kit médico").
- **qtd** — número inteiro ≥ 0.
- **descrição** — livre.

Cada arma e cada item tem um **×** que remove a entrada. Tudo é salvo junto com o personagem (chaves `armamentos` e `itens` no JSON) ao clicar em **Salvar**.

Personagens salvos em `personagens.json` e imagens copiadas para `imagens/` (estrutura pensada para virar facilmente uma fonte servida via HTTP/WebSocket no futuro). Cada personagem guarda quem o criou (`criado_por`) e a data de criação (`criado_em`, formato `DD/MM/AA`), que são usados para filtrar a lista e exibir o selo "Registrado em".

### Editar / excluir personagem

- **Acessar Ficha** (no card do personagem) abre a mesma tela da criação no modo de edição quando o usuário logado é o criador da ficha — todos os campos vêm pré-preenchidos e o botão Salvar atualiza o personagem existente em vez de criar um novo.
- **×** no canto superior direito do card pede confirmação e exclui o personagem do `personagens.json`.

---

## Como rodar

Requer **Python 3.8+** (Tkinter já vem incluído).

```bash
pip install -r requirements.txt
python entropia.py
```

O app roda em **dois modos**, controlados pelo `app.json`:

- **`local`** (padrão): lê/escreve `personagens.json`, `bestiario.json` e `imagens/` na mesma pasta. Cada máquina tem seus dados, sem rede.
- **`remoto`**: fala com `servidor.py` via HTTP. Para jogar em grupo, o Mestre hospeda `servidor.py` num VPS e os jogadores apontam `app.json` para o URL. Ver [README_DEPLOY.md](README_DEPLOY.md).

Exemplo de `app.json` em modo remoto:

```json
{
  "modo": "remoto",
  "servidor_url": "https://entropia.seudominio.com"
}
```

---

## Como gerar o `.exe` para distribuir aos jogadores

Para os amigos que não têm Python nem VSCode, basta empacotar o cliente em um único `.exe` com PyInstaller. O arquivo [entropia.spec](entropia.spec) já está configurado.

```bash
venv\Scripts\pip.exe install pyinstaller
venv\Scripts\pyinstaller.exe entropia.spec --clean --noconfirm
```

Saída: `dist\Entropia.exe` (~21 MB, arquivo único, sem console).

O `app.json` do repositório é **embutido como template**. Na primeira execução do `.exe`, `persistencia.py` detecta `sys.frozen` e copia esse template para a pasta ao lado do executável — é ali que o token de login e as preferências do usuário passam a ser salvas entre execuções. Basta distribuir o `Entropia.exe` sozinho; cada jogador ganha o seu próprio `app.json` local no primeiro boot.

Para atualizar o URL do servidor (ou qualquer default) de forma persistente, edite o `app.json` do repositório **antes** de rodar o build.

---

## Como adicionar novos logins

Abra [entropia.py](entropia.py) e edite o dicionário `USUARIOS` no topo do arquivo. Cada entrada tem a forma:

```python
"nome_de_usuario": {
    "senha": "senha_do_usuario",
    "palavra_chave": "palavra_chave_secreta",
    "papel": "mestre",   # ou "jogador"
},
```

- `papel` = `"mestre"` → acesso à tela do Mestre (futura).
- `papel` = `"jogador"` → acesso apenas à ficha e armamentos (futuro).

Não precisa mexer em mais nada — salvar o arquivo já é o suficiente.

---

## Stack

- **Linguagem:** Python 3
- **Interface:** Tkinter (biblioteca padrão, sem dependências externas)
- **Plataforma atual:** Desktop (Windows testado). Tkinter é multiplataforma, então deve rodar em macOS/Linux também.

Escolha consciente: começar com Tkinter porque é zero-dependências, arquivo único, fácil de editar. Quando a parte de rede entrar em cena, podemos adicionar `socket`/`websockets` ou migrar o frontend para algo web (Electron, PyWebView) se fizer sentido.

---

## Estrutura do projeto

```
ENTROPIA/
├── entropia.py         # cliente Tkinter (login + tela principal + ficha + bestiário + rolador)
├── persistencia.py     # camada de I/O: dispacha local ↔ remoto com base em app.json
├── servidor.py         # servidor HTTP Flask (modo remoto) — roda no VPS do Mestre
├── requirements.txt    # pillow (cliente) + flask/gunicorn/bcrypt (servidor) + requests
├── app.json            # config do cliente: {modo: "local"|"remoto", servidor_url, token}
├── personagens.json    # modo local: personagens
├── bestiario.json      # modo local: monstros do Mestre
├── imagens/            # modo local: imagens dos personagens e monstros
├── imagens_cache/      # modo remoto: cache de imagens baixadas do servidor
├── entropia.spec       # config do PyInstaller (gera dist/Entropia.exe)
├── README.md
└── README_DEPLOY.md    # passo-a-passo pra subir servidor.py no VPS
```

---

## Roadmap

Ordem sugerida para construir o resto:

1. **Tela do Jogador** — aba Personagem (ficha completa ao clicar em "Acessar Ficha")
   - ✅ Sistema de vida (HP), energia, sanidade, atributos.
   - ✅ Edição da ficha pelo criador.
   - ✅ Exclusão da ficha pelo criador.
   - Campo livre de descrição/histórico.
2. **Tela do Jogador** — aba Armamentos
   - Inventário (pistolas, facas, grimórios etc.).
   - Dano, tipo, munição, descrição.
3. **Tela do Mestre** — escudo do mestre
   - ✅ Rolador de dados configurável (qualquer dN, quantos quiser, com modificador). _Hoje aberto a todos; quando virar rede, virá pro escudo do Mestre._
   - ✅ Bestiário — cadastro rápido de criaturas com HP e Energia (aba visível apenas para o Mestre).
   - Log de rolagens.
   - ✅ Visão panorâmica: o Mestre enxerga os personagens de **todos** os jogadores (quebrando o filtro por dono).
4. **Rede / servidor** — jogar em tempo real com os amigos
   - Trocar `carregar_personagens` / `salvar_personagem` por chamadas HTTP a um servidor Flask hospedado (Render, Fly.io, Railway — planos gratuitos resolvem).
   - Endpoints previstos: `GET /personagens`, `POST /personagens`, `GET/POST /imagens/…`.
   - Atualização ao vivo: polling a cada 3–5s no começo, WebSocket quando entrarem as rolagens de dado.
   - Mestre recebe todas as rolagens em tempo real.
5. **Persistência**
   - Salvar fichas de personagem e bestiário em arquivo (JSON) — hoje já feito para personagens; estender para o resto.

---

## Histórico de decisões

- **Python + Tkinter** em vez de Electron/web: menor atrito pra começar, arquivo único, o usuário consegue editar o código pra adicionar logins sem infraestrutura.
- **Tema escuro com destaque roxo** (`#44008c`): coerente com a inspiração visual de Ordem Paranormal.
- **Login comparativo tolerante**: usuário e palavra-chave são `casefold`-comparados para evitar frustração na mesa, mas a senha permanece exata.
- **Minimalismo**: fontes sem serifa e sem negrito, campos sem molduras — só uma linha de base que acende no foco.
- **Lista filtrada por dono**: cada personagem carrega `criado_por` no JSON e a tela principal só mostra os que batem com o usuário logado. O Mestre também é filtrado por enquanto — quando a visão panorâmica do Mestre entrar no roadmap (passo 4), basta pular esse filtro para quem tem `papel == "mestre"`.
