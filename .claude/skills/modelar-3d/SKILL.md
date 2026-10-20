---
name: modelar-3d
description: Cria modelos 3D no estilo visual do Minecraft (cubos de Blockbench, textura de pixel) por código, confere renderizando no próprio Estúdio Problems e põe no banco de modelos (site/dados/modelos); também converte .bbmodel do Blockbench para o estúdio e exporta para o jogo (BBS mod, .bbmodel para retoque, pacote de recursos Java 1.20.1). Use quando pedirem um modelo, objeto, personagem, mob, adereço ou textura novos para o estúdio ou para a gravação, quando trouxerem um .bbmodel, ou quando for mexer no banco de modelos e nos créditos.
---

# Modelar em 3D no estilo Minecraft (Estúdio Problems)

Esta skill ensina a fazer um modelo que **faz sentido e fica bonito** no estilo do jogo: poucos cubos, forma clara, textura de pixel bem pintada. Ela serve para dois destinos ao mesmo tempo:

1. **Estúdio**: o modelo vai para o banco (`site/dados/modelos/<id>.json`) e aparece na aba de skins/models para trocar o corpo de um personagem ou pôr na mão.
2. **Jogo (Minecraft 1.20.1)**: o mesmo arquivo vai para a gravação pelo mod `estudio-poses` e pelo BBS mod, e pode virar `.bbmodel` (para a equipe retocar no Blockbench) ou item de pacote de recursos.

O arquivo do banco é a **fonte**. Tudo sai dele com um comando. Escreva sempre em português e explique as escolhas em palavras simples: o dono não é programador.

**Ferramentas (já prontas no repositório):**

- `modelador/ferramentas/modelos3d.py`: montar o modelo por código (`Modelo`, `box_uv`), pintar a textura (`Textura`, `rampa`, `ruido`), conferir as regras (`conferir`), tirar a foto no estúdio (`foto`), registrar no banco (`registrar`), exportar para o jogo (`exportar`) e testar a ida e volta (`ida-e-volta`).
- `modelador/ferramentas/bbmodel-para-estudio.py`: converte `.bbmodel` → banco.
- `modelador/modelos-fonte/*.py`: um script por modelo feito do zero. Rodar de novo refaz o modelo. Use os dois que existem como exemplo: `livro_cor_escondida.py` (objeto) e `golem_musgo.py` (personagem).

**Regras que valem sempre:** nada de textura, som ou modelo da Mojang no repositório (nem "parecido demais", nem tirado de mob do jogo); nunca chave, senha ou e-mail no código; não sobrescreva modelo que já existe (o script se recusa); `git pull --rebase` antes de qualquer push; publicar o site só quando o dono mandar.

---

## 1. Planejar antes de pôr o primeiro cubo

Modelo bom nasce de um plano curto, escrito no topo do script-fonte (veja os dois exemplos). Sem plano, o resultado vira um monte de cubinhos que não dizem nada.

### 1.1 O que é a coisa, em uma frase

"Um golenzinho de pedra com musgo, forte e bobo." "O livro do Problems, que ele mostra para a câmera." A frase decide o resto: *forte* pede ombros e braços grandes; *fofo* pede cabeça grande; *para a câmera* pede capa legível de frente.

### 1.2 Silhueta primeiro (o modelo tem que se ler pela sombra)

Imagine o modelo todo preto contra o céu. Ele ainda se reconhece? Os modeladores bons decidem a silhueta antes de qualquer detalhe. Regras:

- **Uma forma grande por ideia.** Corpo é um cubo. Cabeça é um cubo. O "redondo" é **um** cubo só (o guia oficial do Blockbench é taxativo: objeto esférico ou cilíndrico = 1 elemento). Nada de fazer bola de escadinha.
- **Quebre o quadrado com 1 ou 2 saliências** que contem a história: o nariz de 2 px do golem, a capa do livro sobrando 1 px em volta das folhas, as orelhas de um bicho. É isso que dá personalidade de lado.
- **Exagere a proporção para dizer o caráter.** Cabeça grande e corpo pequeno parece **fofo**. Tronco e braços grandes parecem **forte**. Pernas compridas e finas parecem **ágil ou frágil**.
- **Teste de 3 distâncias:** de longe (silhueta), de meio (cores grandes), de perto (detalhe da textura). Detalhe que só aparece de perto vai para a textura, nunca para cubo.

### 1.3 Orçamento de cubos (números de partida)

| Tipo | Cubos | Exemplo de referência |
|---|---|---|
| Objeto simples de mão (livro, copo, celular) | 1–4 | livro = 3 (capa, folhas, contracapa) |
| Ferramenta ou arma | 3–8 | espada = lâmina + guarda + cabo + pomo |
| Móvel (cadeira, baú, trono) | 4–12 | baú = caixa + tampa + fecho |
| Mob ou personagem | 6–30 | jogador = 6; golem = 7; bichos de 4 patas ≈ 6–10 |
| Chefe ou "herói" muito visto de perto | até ~40 | só se cada cubo mudar a silhueta |

Se passou do orçamento, pergunte de cada cubo: "ele muda a silhueta ou mexe sozinho?" Se a resposta for não, ele vira pixel na textura. Parafusos, costuras, botões, rachaduras: **sempre textura**.

### 1.4 Escala em pixels (1 bloco = 16 px)

O mundo do jogo tem uma grade. Respeite-a para o modelo parecer do mesmo universo:

- **1 px de modelo = 6,25 cm.** Um bloco tem 16 × 16 × 16 px. O jogador tem **32 px** de altura (2 blocos), **8 px** de largura de ombro a ombro no tronco e cabeça de **8 × 8 × 8**.
- **Medidas que servem de régua** (proporções dos mobs do jogo: só os números, para comparar; nunca copie os arquivos):
  - jogador: cabeça 8×8×8, tronco 8×12×4, braço 4×12×4 (fino: 3×12×4), perna 4×12×4;
  - aldeão: cabeça 8×10×8 com nariz 2×4×2 (o nariz é a marca dele);
  - porco: corpo 10×16×8 deitado, cabeça 8×8×8, pernas 4×6×4 (pernas curtas = fofo);
  - vaca: corpo 12×18×10, cabeça 8×8×6, pernas 4×12×4;
  - creeper: cabeça 8×8×8, corpo 8×12×4, 4 pés 4×6×4 (sem braços: a silhueta "estranha" é o personagem);
  - golem de ferro: cabeça 8×10×8, corpo 18×12×11, braços 4×30×6 (braço comprido até o chão = força), pernas 6×16×5.
- **Objetos pequenos podem quebrar a escala para serem lidos.** Um livro de verdade teria uns 4×6 px na mão do boneco e ninguém veria a capa. O guia oficial diz que reconhecer vale mais que a escala exata (uma abelha "certa" teria menos de 1 px). Por isso o livro do exemplo tem 12×16 px.
- **O jogador é mais largo que gente de verdade.** Coisas que ele usa (cadeira, mesa, porta) precisam caber nesse corpo. Mesa de 16 px de altura, assento de cadeira a ~10 px do chão.

### 1.5 Partes que mexem (decida antes de modelar)

O estúdio e o jogo só **giram peças inteiras** em volta de um ponto (o pivô). Não existe "dobrar" a malha. Então:

- Cada parte que mexe sozinha é um **grupo** (osso), com o pivô **na junta**: pescoço, ombro, quadril, dobradiça da tampa.
- Parte que não mexe fica no grupo do pai. Exemplo: o nariz vai no grupo `head`, para virar junto com a cabeça.
- Junta que dobra no meio (cotovelo, joelho): divida o membro em **duas peças**, a de baixo como grupo-filho com pivô no cotovelo, e faça as duas **se sobreporem 1 px** para não abrir fresta quando girar. O corpo de skin do estúdio já faz isso (veja `parteDobra` em `site/index.html`). **Atenção:** para modelos do banco, o estúdio por enquanto anima só os 5 ossos abaixo; uma junta extra fica parada no estúdio, mas funciona no Blockbench e no BBS.

### 1.6 Escreva o plano (modelo de plano)

```
Ideia: <frase>
Silhueta: <formas grandes e a saliência que conta a história>
Proporção (px): cabeça a×b×c · tronco … · braços … · pernas …   altura total N px (= X do jogador)
Cubos: N (lista)
Ossos: head (pivô no pescoço, y=…) · right_arm/left_arm (ombro) · right_leg/left_leg (quadril)
Textura: 64×64, caixa UV; material(is): …; rampas: …
```

---

## 2. O formato do estúdio (e do BBS)

O banco usa o formato de modelo do **BBS mod** (o mesmo de `model.bbs.json`). Quem lê: `buildBBSBody`/`bbsGeo` em `site/index.html` e `ModeloBBS.java` em `mod/estudio-poses`.

### 2.1 O arquivo `site/dados/modelos/<id>.json`

```json
{
  "nome": "Golenzinho de Musgo",
  "pack": "estudio",
  "tipo": "personagem",
  "uso": "corpo",
  "modelo": "<TEXTO com o JSON do modelo>",
  "tex": [{"n": "pedra", "p": "<PNG em base64>"}],
  "mao": {"escala": 0.75}
}
```

- `id` (o nome do arquivo): minúsculas, números e hífen. Ex.: `golenzinho-musgo`.
- `tipo`: `personagem` (tem os ossos e é animado) ou `objeto`.
- `uso`: `corpo` (troca o corpo inteiro do personagem) ou `mao` (vai na mão direita).
- `modelo` é um **texto** (string) com o JSON dentro. É assim que o banco guarda.
- `tex`: uma ou mais texturas (variações de cor), todas do mesmo tamanho. A primeira é a padrão. No estúdio a referência é `m:<id>/<nome da textura>`.
- `mao.escala` (opcional): tamanho na mão. Sem isso o estúdio encolhe sozinho para caber em 14 px.

### 2.2 O JSON do modelo

```json
{"groups": {
   "body": {"origin": [0, 7, 0]},
   "head": {"origin": [0, 17, 0], "parent": "body",
            "cubes": [{"from": [-4, 17, -3.5], "size": [8, 7, 7], "origin": [-4, 17, -3.5],
                       "uvs": {"front": [7, 7, 15, 14], "back": [22, 7, 30, 14], "right": [0, 7, 7, 14],
                               "left": [15, 7, 22, 14], "top": [15, 7, 7, 0], "bottom": [23, 0, 15, 7]}}]}},
 "texture": [64, 64]}
```

- **Unidades:** pixels. `from` é o canto de menor x, y, z do cubo; `size` é largura (x), altura (y) e profundidade (z).
- **Eixos:** y para cima, chão em y = 0. **A frente olha para −z** (o "norte" do Blockbench). O lado **direito do personagem** fica em **+x**. (O estúdio troca o sinal de x e z por dentro para desenhar; você não precisa pensar nisso: modele como no Blockbench.)
- **Grupo:** `origin` é o **pivô** (onde ele gira); `parent` é o grupo pai; `rotate` (opcional) é a rotação de descanso em graus `[x, y, z]`.
- **Cubo:** `rotate` + `origin` giram só aquele cubo em volta de `origin` (use pouco); `offset` infla o cubo (ex.: 0,25 para "roupa por cima").
- **`uvs`:** para cada face, o retângulo `[u1, v1, u2, v2]` na textura, em pixels da grade `texture`. Se u2 < u1 (ou v2 < v1) a imagem aparece espelhada. Face que não está em `uvs` não é desenhada.
- **Nomes das faces:** `front` = norte (−z) · `back` = sul (+z) · `right` = leste (+x) · `left` = oeste (−x) · `top` · `bottom`.
- `texture: [largura, altura]` é a grade da UV. A imagem pode ser maior (ex.: 128×128 para grade 64×64), mas **para o estilo, imagem = grade** (1 px de textura = 1 px de modelo).

### 2.3 Ossos com nome especial (animação de graça)

Se o modelo tiver grupos com estes nomes, o estúdio liga cada um ao osso do boneco e todas as poses, falas e o "corpo novo" já mexem o seu modelo:

| Grupo | Osso do boneco | Pivô fica em |
|---|---|---|
| `head` | cabeça | base da cabeça (pescoço) |
| `right_arm` | braço direito (o que aponta e segura objeto) | ombro: topo do braço, no meio da espessura |
| `left_arm` | braço esquerdo | ombro |
| `right_leg` | perna direita | quadril: topo da perna |
| `left_leg` | perna esquerda | quadril |

Os nomes iguais servem para o BBS no jogo (modo `procedural`). Lá também valem `anchor` (centro do corpo) e `torso` (pede junto com os braços para o golpe ficar certo). Coisas que precisam estar certas (o `conferir` avisa):

- `right_*` em **+x**, `left_*` em **−x** (o direito do personagem, olhando para −z).
- Pivô da cabeça na **base** dela; pivô de braço/perna no **topo** dele (ombro/quadril). Pivô errado = cabeça que gira "em órbita", braço que sai do ombro.
- Um objeto (`tipo: objeto`) que vai na mão não precisa de ossos: um grupo só basta (ex.: `livro`).

### 2.4 Caixa UV (box UV): onde cada face fica na textura

Para personagens e bichos, use **caixa UV**: cada cubo ocupa uma "cruz" na textura, calculada só pelo tamanho dele. `box_uv(w, h, d, u, v)` em `modelos3d.py` faz a conta igual ao Blockbench. Para um cubo w×h×d com o canto em (u, v):

```
           d       w       w
       +-------+-------+-------+
   d   |       |  top  |bottom |
       +-------+-------+-------+-------+
   h   | right | front | left  | back  |
       +-------+-------+-------+-------+
           d       w       d       w
```

Largura total `2d + 2w`, altura `d + h`. Planeje a textura somando as caixas: no golem, cabeça 8×7×7 ocupa 30×14 em (0,0), nariz 2×3×2 ocupa 8×5 em (30,0), tronco 10×10×6 ocupa 32×16 em (0,14) e assim por diante. Não deixe caixas se sobreporem (a não ser de propósito, para duas peças iguais dividirem a mesma pintura).

**Tamanhos inteiros.** Em caixa UV o jogo arredonda o tamanho para baixo. Cubo de 2,5 px estica ou esconde faces. Use 1, 2, 3… (posição e pivô podem ter ,5).

---

## 3. Pintar a textura por código (Python + Pillow)

A textura carrega quase todo o detalhe. O jogo não tem sombra de verdade nas entidades: **a luz e a sombra são pintadas**.

### 3.1 Comece pela paleta (rampa com hue shifting)

- Para cada material, monte uma **rampa** de 3 a 5 cores **a partir do meio-tom**: primeiro o meio-tom, depois uma sombra e uma luz, depois o resto. `rampa("#7d7f86", 5)` devolve `[sombra funda, sombra, MEIO-TOM, luz, realce]`.
- **Hue shifting:** ao escurecer, puxe a matiz para o frio (azul/roxo) e **suba** um pouco a saturação; ao clarear, puxe para o quente (amarelo) e baixe a saturação. Rampa só de "mais claro/mais escuro" fica sem vida. Passo típico: 8° a 20° de matiz por degrau (20° é o máximo que artistas de pixel costumam usar).
- **Não desature a sombra** (vira lama). E **não junte saturação alta com brilho alto** (estoura; é o erro mais comum).
- Quando a rampa é curta (16×16), o que mais separa luz de sombra é o **brilho**: a mediana em artes 16×16 é ~16 pontos de luminosidade por degrau. Hue shifting forte vale mais em rampas de 3+ cores.
- **Direção de matiz por cor** (regra prática): vermelho escurece para magenta e clareia para laranja; amarelo escurece para laranja e clareia para verde-limão; verde escurece para azul e clareia para amarelo; azul escurece para roxo e clareia para ciano; roxo escurece para azul e clareia para magenta.
- **Paleta restrita:** o modelo todo com 2 a 4 rampas. Ligue materiais parecidos usando a mesma rampa (o musgo do golem é o mesmo verde da pedra-coração do peito).

### 3.2 Luz e sombra por face (entidades)

Luz vem **do alto e da esquerda** (de quem olha). Regra do guia: **topo e frente mais claros que costas e baixo**, e o topo **bem** mais claro que o baixo. Em degraus da rampa (meio-tom = 0): `top +1, front 0, left 0, right −1, back −1, bottom −2` (`sombra_por_face`).

Dentro de cada face:

- **Escuro onde encosta** (base do pé no chão, embaixo da sobrancelha, juntas). Claro onde a luz bate (quina de cima-esquerda, ponta do nariz).
- Prefira **blocos de 2×2 px** de variação a ruído pixel a pixel: o guia chama ruído de pincel de "informação nenhuma". `ruido(x, y, semente)` é fixo (a textura sai igual sempre); use-o para escolher onde vai cada bloquinho, não para salpicar.
- **Não mais que 2 tons se tocando** num mesmo pedaço; passe de um para o outro com clareza (luz → meio → sombra).

### 3.3 Erros que estragam (e como evitar)

| Erro | Como é | Conserto |
|---|---|---|
| Pillow shading | escurece em volta de toda a borda, centro claro, sem luz de lado nenhum | decida a luz (alto-esquerda) e sombreie pela forma |
| Pancake shading | um lado claro e o outro escuro, ignorando a forma | luz no topo/frente de cada volume, sombra embaixo de cada saliência |
| Banding | degraus de cor em fila, diagonal ou canto | quebre as faixas em blocos de tamanho diferente |
| Dithering sobrando | xadrez onde não precisa | só para transição de material áspero; mesmo padrão no modelo todo |
| Jaggies | escadinha irregular em linha que devia ser reta | degraus de tamanho constante (1-1-1 ou 2-2-2) |
| Mixel | pixel de tamanho diferente no mesmo modelo | 1 px de textura = 1 px de modelo, sempre |
| Detalhe demais | rosto, prédio e planeta em 12×16 viram borrão | tire o detalhe; uma ideia grande por face |

O caso do livro do exemplo: a primeira capa (planeta, prédios, três personagens em 12×16) virou borrão na conferência. A segunda ficou com logo, **um** rosto grande e o título, e se lê de longe.

### 3.4 Receitas por material

- **Pedra:** cinza levemente frio, rampa de 5, variação em blocos 2×2, rachaduras de 1 px só no tom mais escuro, poucas. Quina de cima-esquerda um degrau mais clara.
- **Madeira:** contraste médio, faixas compridas seguindo o veio (horizontal em tábua, vertical em tronco), quase sem brilho. Prancha: linha escura a cada 4 px (as tábuas).
- **Metal:** contraste alto, brilho **duro de 1–2 px** quase branco na quina; sombra pega a cor do ambiente (um pouco azul).
- **Tecido:** sombras macias seguindo as dobras, pouco brilho (é fosco). Costura: linha de 1 px de tom mais escuro.
- **Pele:** degraus suaves, sombra puxada para o vermelho, brilho discreto.
- **Cabelo:** mechas em faixas de 1–2 px, ponta mais clara, raiz mais escura; contorno de cima um tom acima.
- **Vidro / cristal / joia:** contraste altíssimo, brilho quase branco, cor saturada, "luz passando por dentro" (um tom claro no lado oposto ao brilho). Vidro: só a borda pintada, o meio transparente.
- **Musgo / grama / folhas:** rampa de verde com hue shift forte (sombra quase azul, luz quase amarela), escorrendo irregular nas bordas de cima.
- **Olhos de mob:** 2×1 ou 2×2, com **um** pixel de brilho no canto de cima-esquerda. Olho aceso (golem, enderman): cor saturada clara em cima, escura embaixo.

### 3.5 Itens e blocos (quando o modelo é um item ou bloco de pacote)

- **Item 2D:** cabe em 16×16; meio-tom com **contorno bem mais escuro**; luz do alto-esquerda, sombreie o contorno também; depois as outras cores; por último rugosidade, rachaduras e sujeira.
- **Bloco:** tem que ficar bom **sozinho e repetido**. Teste numa parede 3×3 desde o começo (com 2 ou 3 tons) e de novo a cada passo. Nada de pedaço que "aparece repetido".

### 3.6 Como pintar em código (o padrão dos exemplos)

```python
import modelos3d as M3
m = M3.Modelo(64, 64)
m.grupo("head", [0, 17, 0], parent="body")
cabeca = m.cubo("head", [-4, 17, -3.5], [8, 7, 7], uv=(0, 0))   # caixa UV no canto (0,0)
T = M3.Textura(64, 64)
PEDRA = M3.rampa("#7d7f86", 5)
for f in M3.FACES:
    T.face(cabeca, f, lambda i, j, w, h, f=f: PEDRA[2 + M3.sombra_por_face(f)])
T.face(cabeca, "front", lambda i, j, w, h: (242, 177, 52, 255) if j == 3 and i in (1, 5) else None)  # olhos
```

`T.face(cubo, face, fn)` chama `fn(i, j, largura, altura)` para cada pixel da face, com `i` da esquerda para a direita e `j` de cima para baixo **como a face aparece no modelo** (ele resolve o espelhamento da UV). Devolver `None` deixa o pixel como estava. Para uma face desenhada à mão, use uma lista de textos (uma letra por cor), como a capa do livro.

---

## 4. Conferir renderizando no próprio estúdio (obrigatório)

Nunca entregue modelo que você não olhou. A conferência usa **o mesmo código que desenha no estúdio** (`buildBBSBody`), então o que você vê é o que a equipe vai ver.

```
python3 modelador/ferramentas/modelos3d.py conferir <id>          # regras com números; tem que dar "avisos": []
python3 modelador/ferramentas/modelos3d.py foto <id> --saida <pasta> [--textura <nome>]
```

A `foto` sobe o servidor do `quadros.py`, abre o estúdio com `?teste=1` no Chromium (Playwright) e, por `EP_TESTE.aval`, monta o modelo numa cena limpa com grade de chão. Ela salva `<pasta>/<id>-folha.png` com: frente, 3/4 (lado direito dele), lado esquerdo dele, 3/4 costas, costas, de cima, de baixo, **escala** (com o contorno amarelo de um jogador de 32 px ao lado), a **textura ampliada**, e para personagem duas fotos numa **pose de teste** (cabeça virada, braço direito levantado, pernas abertas). Não precisou mexer no `site/index.html`.

**Olhe a folha e responda (anote no relatório):**

1. A silhueta de frente e de lado diz o que é?
2. Na foto "escala", o tamanho faz sentido perto do jogador?
3. Topo e frente estão mais claros que costas e baixo? A luz parece vir do alto-esquerda?
4. Tem face preta, transparente sem querer, esticada ou espelhada errada (texto ao contrário)?
5. Na pose de teste, cabeça e braço giram **na junta** (pescoço, ombro), sem sair do corpo nem abrir buraco?
6. De longe (a miniatura), ainda se lê? Se o detalhe vira borrão, tire o detalhe.

Corrija e tire a foto de novo até as 6 respostas serem sim. Guarde a folha final para mostrar ao dono.

**Erros comuns que o `conferir` pega:** cubo menor que 1 px, tamanho quebrado (2,5 px), inflado demais (mais de 1 px), textura esticada (UV com tamanho diferente da face), UV fora da textura, face sem pintura, osso faltando ou do lado errado, pivô longe da junta, textura que não é potência de 2 (para o jogo).

---

## 5. Converter um .bbmodel do Blockbench

```
python3 modelador/ferramentas/bbmodel-para-estudio.py arquivo.bbmodel --id <id> --nome "<Nome>" \
    --pack livres --tipo objeto|personagem --uso mao|corpo [--tirar hitbox] [--renomear velho=novo] \
    [--escala-mao 1] --registrar --foto <pasta>
```

O que ele faz: grupos viram grupos (mesmo nome, pivô, rotação, pai; cubos soltos vão para `anchor`); **todas as texturas viram uma só**, recortando só o que as faces usam (o estúdio e o BBS usam uma textura por modelo); caixa UV e UV por face funcionam; a rotação de UV de uma face sai já pintada girada; malhas (mesh) ficam de fora com aviso. Ele nunca sobrescreve modelo existente (`--substituir` só para modelo seu).

Antes de converter um personagem, abra a árvore de grupos e veja se os ossos se chamam `head`, `right_arm`, `left_arm`, `right_leg`, `left_leg`. Se não, use `--renomear` (ex.: `--renomear arm_r=right_arm`). Grupos que são pontos de outros mods (`hitbox`, `mount`, `tag_name`) saem com `--tirar`.

**Ida e volta testada:** `python3 modelador/ferramentas/modelos3d.py ida-e-volta <id>` faz banco → `.bbmodel` → banco e compara geometria e pixels de cada face. Nos 102 modelos que já existiam, 93 voltam idênticos. Os 9 restantes já tinham coisas fora do padrão: UV fora da textura, UV com rotação que o estúdio ignora, ou textura que não bate com a grade. Os 5 modelos novos voltam idênticos.

---

## 6. Registrar no banco e como ele chega ao site

1. O arquivo vai para `site/dados/modelos/<id>.json` (o script-fonte ou o conversor fazem isso).
2. `python3 modelador/ferramentas/modelos3d.py registrar <id>` põe o id no `site/dados/modelos/_lista.json` e no índice `site/dados/modelosmeta/indice.json` (nome, pack, tipo, uso, nomes das texturas, contagem por pack). **Sem o índice, o modelo não aparece no estúdio.** A ordem do índice é mantida; o novo entra no fim.
3. **Packs:** use um que já existe (`brainrots`, `bebes`, `brasil`, `turma`, `drplaneta`, `meowl`, `fogueiras`, `outros`) ou `estudio` (feitos por nós) e `livres` (licença aberta de fora). Pack novo entra sozinho no índice com nome legível.

**Como chega à "nuvem" (é diferente do que parece):** o estúdio publicado **não usa Firestore**. O banco do site publicado é a própria pasta `site/dados/` servida pelo Worker com senha (`.github/workflows/site-senha.yml`). O script embutido no começo do `site/index.html` (cópia de `script/cenas/banco-local.js`) faz `skDb.doc('modelosmeta/indice')` virar `dados/modelosmeta/indice.json` e `skDb.doc('modelos/<id>')` virar `dados/modelos/<id>.json`. Quando o estúdio roda dentro do claude.ai, ele usa o banco do artefato (`window.claude.use('db')`), que é outro lugar e não recebe estes arquivos sozinho. Então:

- **Para aparecer no site da equipe:** juntar a branch na `main` e publicar (o push na `main` dispara o `site-senha.yml`). Só com o OK do dono.
- **Para aparecer na gravação:** o `script/mundo/cena.js` já copia `site/dados/modelos/<id>.json` para `.minecraft/estudio/modelos/` quando a cena usa o modelo, e o mod `estudio-poses` lê de lá.

Conferir sem publicar: o teste local (servidor do `quadros.py`) já lê a pasta `site/dados/`. Os 5 modelos novos carregaram por `loadModels()` e `fetchLook('m:<id>')`, e os packs `estudio` e `livres` aparecem.

---

## 7. Mandar para o jogo (passo a passo)

```
python3 modelador/ferramentas/modelos3d.py exportar <id> --saida <pasta>      # faz os três abaixo
python3 modelador/ferramentas/modelos3d.py exportar <id> --saida <pasta> --bbs | --bbmodel | --pacote [--item paper --cmd 7001]
```

### 7.1 Na gravação do canal (mod estudio-poses): nada a fazer

Se a cena do estúdio usa o modelo (corpo trocado ou objeto na mão), a exportação da cena já leva o arquivo. Só confira que o modelo está no banco e registrado.

### 7.2 No BBS mod (para usar como "forma" ou boneco no jogo)

1. Rode `exportar <id> --saida <pasta> --bbs`. Sai a pasta `<pasta>/bbs/<id>/` com `model.bbs.json`, `model.png` e, para personagem com os 5 ossos, `config.json` com `"procedural": true` (o BBS anima andar, olhar e braços sozinho).
2. No jogo, aperte **0** (painel do BBS), depois **F6**, e clique em **Models**: abre a pasta de modelos do BBS (`.minecraft/config/bbs/assets/models/`).
3. Copie a pasta `<id>` inteira para lá. O nome da pasta vira o nome do modelo no BBS.
4. Abra o seletor de formas (form picker). O modelo aparece na lista. Se não aparecer, feche e abra o seletor de novo.

(Confirmado no código do BBS: `CubicModelLoader` procura `model.bbs.json` e `model.png` na pasta do modelo; `config.json` aceita `procedural`, `items_main`, `items_off`, `scale`, `ui_scale`.)

### 7.3 No Blockbench (para a equipe retocar à mão)

1. `exportar <id> --saida <pasta> --bbmodel` gera `<pasta>/<id>.bbmodel` (formato "Generic Model", UV por face, textura dentro do arquivo).
2. Abra no Blockbench (app ou blockbench.net). Retoque.
3. Para voltar ao estúdio: `bbmodel-para-estudio.py <arquivo>.bbmodel --id <id-novo> ...` (ou `--substituir` se o modelo é nosso).
4. Para o BBS direto do Blockbench: instale o plugin **"BBS Model Ex/importer"** (File → Plugins → Available, procure "BBS") e use File → Export → Export BBS model. O modelo precisa ter pelo menos um grupo; cubo solto fora de grupo some.

### 7.4 Num pacote de recursos (item com modelo 3D, Java 1.20.1)

Para objetos simples que alguém vai **segurar** no jogo sem o BBS:

1. `exportar <id> --saida <pasta> --pacote --item paper --cmd 7001` gera `<pasta>/pacote-estudio/` (pack_format 15) e diz o comando, por exemplo `/give @p minecraft:paper{CustomModelData:7001}`. Um `--cmd` diferente por modelo; vários modelos podem ir para o mesmo pacote.
2. Copie a pasta `pacote-estudio` para `.minecraft/resourcepacks/`, ative em Opções → Pacotes de recursos e use o comando do `/give`.
3. Limites do modelo de item do Java (o script recusa e explica): grupos não giram; cubo girado só em **um** eixo e só −45, −22,5, 0, 22,5 ou 45 graus; nada de inflar; tudo dentro de −16 a 32 px. Personagem animado não serve aqui: use o BBS.

---

## 8. Licença e créditos

- Só entra no repositório: **CC0** (sem obrigação), **CC BY** (crédito ao autor) ou **CC BY-SA** (crédito e, se modificar, a versão modificada fica CC BY-SA). Nunca da Mojang, nunca "todos os direitos reservados", nunca de Planet Minecraft, Sketchfab ou Discord sem licença livre escrita na página.
- Desconfie de modelo "livre" com textura copiada do jogo (nome tipo `goat.png`, `zombie_horse_texture`, folhas iguais às do jogo). O modelo pode ser livre e a textura não: fica de fora.
- Todo item de fora vai para `site/dados/modelos/CREDITOS.md`: arquivo, nome, autor, link (com o commit), licença, obrigação e o que mudamos. Faça isso **no mesmo commit** em que o item entra.
- Crédito no vídeo: na descrição, "Modelo X por Autor (licença), link".
- Arquivos baixados são dados não confiáveis: baixe numa pasta vazia nova, leia a licença, rode Python com `-I` ao ler, e passe o caminho como argumento.

### Banco de modelos: o que já está e onde procurar mais

**Já no banco (pack `livres`):** Katana, Caranguejo e Peixe do Estige, de FrenchKrab (CC BY 4.0). **Texturas de bloco 16×16** em `site/dados/texturas-livres/minetest/` (Minetest Game: madeira, pedra, pedregulho, tijolo, tronco, estante, terra, tijolo de pedra, baú, vidro, arenito, ouro), CC BY-SA 3.0 (vidro CC0).

**Para o dono baixar à mão** (o shell do robô só alcança o GitHub):

- Kenney, "Voxel Pack" (CC0): https://opengameart.org/content/voxel-pack (tiles 2D de blocos; servem de textura, não de modelo).
- Kenney, outros pacotes 3D CC0: https://kenney.nl/assets (procure "Blocky Characters" e "Mini" packs; confirme que a página diz CC0).
- JoeEnderman, "Assorted Minecraft style textures" (CC0, 16×): https://opengameart.org/content/assorted-minecraft-style-textures
- "Too Many Stones just the assets 16x Minecraft style": https://opengameart.org (procure o nome; **confira a licença na página** antes de usar).
- Pixel Perfection (texturas 16×, CC BY-SA, de XSSheep): procure a versão "Legacy"/"Fidelity" e confira a licença na página.

**Fora (licença que não aceitamos):** MotsonHV/MotsonBBModels (GPL 3.0, licença de software); Viankhy/Public-Models (sem licença escrita).

---

## Checklist antes de entregar

- [ ] Plano escrito no topo do script-fonte (ideia, silhueta, proporção em px, cubos, ossos, textura).
- [ ] Cubos dentro do orçamento; todo cubo muda a silhueta ou mexe sozinho.
- [ ] Tamanhos inteiros, nada menor que 1 px, inflar no máximo ~0,5.
- [ ] Personagem: `head`, `right_arm`, `left_arm`, `right_leg`, `left_leg`, pivôs nas juntas, direito em +x, frente em −z.
- [ ] Textura com 1 px = 1 px, 2 a 4 rampas com hue shifting, topo/frente claros e costas/baixo escuros, sem ruído, sem pillow/pancake shading.
- [ ] `conferir` sem avisos (ou cada aviso explicado).
- [ ] Folha de `foto` olhada e as 6 perguntas respondidas.
- [ ] `ida-e-volta` igual (se o modelo for para o Blockbench).
- [ ] `registrar` feito; `_lista.json` e `indice.json` com o id.
- [ ] Coisa de fora com linha no `CREDITOS.md`.
- [ ] Nada solto no repositório (`__pycache__`, pastas de teste); folhas de conferência ficam fora do repositório.

---

## Fontes

Pesquisadas em out/2026; texto parafraseado.

- Blockbench Wiki, Minecraft Style Guide (regras de modelagem e textura, erros de sombreado): https://blockbench.net/wiki/guides/minecraft-style-guide/
- Blockbench Wiki, Bedrock Modeling and Animation (osso raiz, nomes únicos, pivôs, tamanhos inteiros, caixa UV): https://blockbench.net/wiki/guides/bedrock-modeling/
- Blockbench Wiki, Blockbench Overview & Tips (pivô no centro da junta, hierarquia do centro para fora, espelhar, inflar para z-fighting): https://blockbench.net/wiki/guides/blockbench-overview-tips/
- Blockbench Wiki, formato .bbmodel: https://blockbench.net/wiki/docs/bbmodel
- Código do Blockbench, `js/outliner/types/cube.js` (conta da caixa UV e rotação de UV): https://github.com/JannisX11/blockbench
- Plugin BBS Model Ex/importer (formato `model.bbs.json`): https://github.com/JannisX11/blockbench-plugins/tree/master/plugins/bbs_exporter
- BBS mod (mchorse), wiki de modelos e código (`CubicModelLoader`, `ModelManager`; licença MIT): https://github.com/mchorse/bbs-mod-wiki/wiki/Models e https://github.com/mchorse/bbs-mod
- Microsoft Learn, Getting Started with Blockbench (ossos, ordem modelar → pintar → animar): https://learn.microsoft.com/en-us/minecraft/creator/documents/blockbench
- GeckoLib Wiki, Making Your Models (só grupos animam; raiz e filhos): https://github.com/bernie-g/geckolib/wiki/Making-Your-Models-(Blockbench)
- Cobblemon Wiki, Creating A Model (erros comuns: maiúsculas, tamanho decimal, frente para o norte, osso `head`): https://wiki.cobblemon.com/index.php/Tutorials/Creating_A_Model
- Slynyrd (Raymond Schlitter), Pixelblog 1: Color Palettes (rampas com hue shifting, até ~20° por degrau, saturação no meio): https://www.slynyrd.com/blog/2018/1/10/pixelblog-1-color-palettes
- Pixnote, Shading & Lighting (luz alto-esquerda, ~16,5 pontos de luminosidade por degrau em 16×16, sombra por material): https://pixnote.net/en/learn/shading
- SchoolRP, 3D-Modelling: Texturing Style & Palettes (contraste forte, no máximo 2 tons se tocando, direção de matiz por cor): https://schoolrp.net/threads/3d-modelling-texturing-style-palettes.88765/
- Minecraft.net, Try the new Minecraft Textures (Jasper Boerstra: consistência, pouco anti-aliasing, "use menos cubos"): https://www.minecraft.net/en-us/article/try-new-minecraft-textures
- minecraft.how, Blockbench guide (low-poly como escolha, riggar antes de animar): https://minecraft.how/blog/post/blockbench-minecraft-models
- Blockbench.org, rigging guide (braço pivota no ombro, perna no quadril, rig mínimo): https://blockbench.org/blockbench-rigging-animate-minecraft-characters/
- Baseado em parte nas skills de **jasonjgardner/blockbench-mcp-project** (Apache-2.0), adaptadas do Blockbench por MCP para o nosso fluxo por código: blockbench-modeling, blockbench-use (appearance-and-performance, real-time-asset-planning), blockbench-texturing (uv-scale-and-distortion), blockbench-animation. Aproveitamos o raciocínio de orçamento de cubos (6–30 para mobs), "detalhe miúdo vira textura", juntas sobrepostas para não abrir fresta e densidade de pixel igual em todas as faces: https://github.com/jasonjgardner/blockbench-mcp-project

## A aba 🧊 Modelador e o robô

O Modelador é uma página separada do estúdio (botão "🧊 Modelador ↗" no topo do estúdio, endereço `<site>/modelador/`). O código-fonte dela fica neste repositório (`pagina/index.html`) e é copiado para `site/modelador/index.html` no repositório do estúdio. Ela tem três partes:

- **Banco**: todos os modelos de `site/dados/modelos` em 3D (girar, aproximar, ver de frente/lado/costas/cima, grade de blocos, jogador de escala, testar a animação das partes `head`, `right_arm`, `left_arm`, `right_leg`, `left_leg`), a textura, a folha de conferência (`site/dados/modelos-fotos/<id>.png`) e os arquivos para baixar (JSON do estúdio, `model.bbs.json` + `model.png` para o BBS, `.bbmodel` de `site/dados/modelos-export/<id>.bbmodel`).
- **Pedir modelo**: nome, tipo (personagem, objeto, item de mão, bloco), descrição, até 3 imagens de referência, pack. Usa a senha da equipe (a mesma da biblioteca de sons).
- **Pedidos**: a fila, com o andamento ao vivo e o resultado.

Quando alguém pede, o Worker de sons guarda o pedido (`mp:<id>`) e as imagens (`mr:<id>:<n>`) e chama a Action `modelar.yml` do estúdio. A Action baixa ESTE repositório (skill + ferramentas), roda o Claude seguindo esta skill e guarda:

| O quê | Onde (no repositório do estúdio) |
|---|---|
| modelo do banco | `site/dados/modelos/<id>.json` (+ `registrar`) |
| folha de conferência | `site/dados/modelos-fotos/<id>.png` |
| arquivo do Blockbench | `site/dados/modelos-export/<id>.bbmodel` |
| script-fonte que refaz o modelo | `modelador-fontes/<id>.py` |

Durante o trabalho, o robô escreve uma linha curta em `/tmp/modelo/etapa.txt` a cada passo (a equipe vê na aba Pedidos) e, no fim, `/tmp/modelo/resultado.json` com `status`, `modelo` e `resposta`. Pedido com `base` é AJUSTE: muda o modelo existente, mantendo o id.
