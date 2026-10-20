# Modelador · Estúdio Problems

Modelos 3D no estilo do Minecraft (cubos + textura de pixel) para os vídeos do canal Problems: para usar no **Estúdio Problems** e para levar ao **jogo** (mod BBS, Blockbench e resource pack 1.20.1).

- **Skill** `.claude/skills/modelar-3d/SKILL.md`: como planejar, montar, pintar, conferir e exportar um modelo (baseada em pesquisa e, em parte, nas skills de jasonjgardner/blockbench-mcp-project, Apache-2.0; fontes no fim da skill).
- **Ferramentas** `ferramentas/`: `modelos3d.py` (montar por código, conferir, fotografar no estúdio, registrar no banco, exportar `.bbmodel` / BBS / resource pack, ida e volta) e `bbmodel-para-estudio.py` (traz um modelo do Blockbench para o banco).
- **Fontes dos modelos** `modelos-fonte/`: scripts que refazem cada modelo feito do zero.
- **Página** `pagina/index.html`: a aba 🧊 Modelador (banco em 3D, pedir modelo ao robô, fila de pedidos). Publicada como `site/modelador/` no estúdio.

As ferramentas usam o desenho do próprio estúdio para fotografar, então rodam com o estúdio ao lado: de dentro do repositório `estudio-problems` (com este repo clonado em `./modelador`, como o robô faz) ou com `ESTUDIO=/caminho/do/estudio-problems`.

O banco de modelos (incluindo os personagens da equipe) fica no repositório do estúdio, que é privado. Este repositório é público: nada de senha, chave ou arquivo da Mojang aqui.
