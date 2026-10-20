# Modelador · Estúdio Problems

Modelos 3D no estilo do Minecraft (cubos + textura de pixel) para os vídeos do canal Problems: para usar no **Estúdio Problems** e para levar ao **jogo** (mod BBS, Blockbench e resource pack 1.20.1).

- **Skill** `.claude/skills/modelar-3d/SKILL.md`: como planejar, montar, pintar, conferir e exportar um modelo (baseada em pesquisa e, em parte, nas skills de jasonjgardner/blockbench-mcp-project, Apache-2.0; fontes no fim da skill).
- **Ferramentas** `ferramentas/`: `modelos3d.py` (montar por código, conferir, fotografar no estúdio, registrar no banco, exportar `.bbmodel` / BBS / resource pack, ida e volta) e `bbmodel-para-estudio.py` (traz um modelo do Blockbench para o banco).
- **Fontes dos modelos** `modelos-fonte/`: scripts que refazem cada modelo feito do zero.
- **Página** `index.html` (na raiz): o Modelador (início, banco em 3D, pedir modelo ao robô, fila de pedidos). Abre pelo menu do Estúdio Problems em `/modelador/`.

As ferramentas usam o desenho do próprio estúdio para fotografar, então rodam com o estúdio ao lado: de dentro do repositório `estudio-problems` (com este repo clonado em `./modelador`, como o robô faz) ou com `ESTUDIO=/caminho/do/estudio-problems`.

O banco de modelos (incluindo os personagens da equipe) fica no repositório do estúdio, que é privado. Este repositório é público: nada de senha, chave ou arquivo da Mojang aqui.

## Onde fica no ar

- **Site novo** (menu com login do Google): https://problemsbloxcreate-lab.github.io/modelador/ — publicado pela Action `pages.yml` deste repositório (uma vez só: Settings → Pages → Source: **GitHub Actions**). A página e o Blockbench carregam o porteiro `/estudio-login.js` do menu. Os modelos vêm do banco PRIVADO pelo servidor da equipe (rota `/modelos/dados`, senha da equipe).
- **Site do estúdio** (Cloudflare, senha do estúdio): `<estúdio>/modelador/`, cópia em `site/modelador/` do repositório do estúdio, lendo direto de `site/dados/`.
