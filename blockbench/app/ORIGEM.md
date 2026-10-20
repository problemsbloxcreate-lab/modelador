# Blockbench (versão web) dentro do Modelador

Este é o Blockbench 5.2.2, de JannisX11 e colaboradores, licença **GPL-3.0** (texto completo em LICENSE.MD).
Código-fonte original: https://github.com/JannisX11/blockbench (commit a1a464c0358c9f223fb2b3f8a21930fa26812e43).
Montado em 2026-10-20 por `blockbench/montar.py` do repositório https://github.com/problemsbloxcreate-lab/modelador,
que guarda também o script de montagem e o plugin.

O que foi mudado em relação ao original:
- compilado com `npm run build-web` e copiado só o que a versão web usa;
- estas imagens de referência que imitam o Minecraft foram trocadas pela imagem neutra missing.png do próprio Blockbench: armor_stand.png, crafting_table.png, flower_pot.png, fox.png, hud.png, inventory_full.png, inventory_nine.png, item_frame.png, oak_shelf.png, player_skin.png, zombie.png;
- a página carrega o plugin `banco-estudio.js` (licença MIT), que liga o Blockbench ao banco de modelos do Estúdio Problems;
- o título da página.
