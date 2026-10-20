#!/usr/bin/env python3
"""Monta a cópia do Blockbench (versão web) que roda dentro do Modelador.

  python3 blockbench/montar.py <pasta do Blockbench já compilado (npm run build-web)> blockbench/app

- copia só o que a versão web precisa para rodar (index.html, dist/, css/, font/, assets/, lib/, lang/, themes/, content/, ícones, manifesto, licença);
- troca as imagens de referência que imitam o jogo (jogador, zumbi, suporte de armadura, HUD, inventário…) pela imagem neutra
  "missing.png" do próprio Blockbench: regra da equipe, nada de textura da Mojang no repositório;
- põe o plugin "Banco do Estúdio" (blockbench/banco-estudio.js) dentro da página;
- escreve ORIGEM.md com a versão, o link do código-fonte e o que foi mudado (exigência da GPL-3.0).
"""
import os, shutil, subprocess, sys, datetime

SRC, DST = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
AQUI = os.path.dirname(os.path.abspath(__file__))
PASTAS = ["dist", "css", "font", "assets", "lib", "lang", "themes", "content", "icons"]
ARQS = ["index.html", "favicon.png", "icon.png", "icon_full.png", "icon_maskable.png", "manifest.webmanifest", "LICENSE.MD"]
DO_JOGO = ["armor_stand.png", "crafting_table.png", "flower_pot.png", "fox.png", "hud.png", "inventory_full.png",
           "inventory_nine.png", "item_frame.png", "oak_shelf.png", "player_skin.png", "zombie.png"]

if not os.path.exists(os.path.join(SRC, "dist", "bundle.js")):
    sys.exit("falta dist/bundle.js: rode npm run build-web no Blockbench antes")
if os.path.exists(DST):
    shutil.rmtree(DST)
os.makedirs(DST)
for p in PASTAS:
    if os.path.isdir(os.path.join(SRC, p)):
        shutil.copytree(os.path.join(SRC, p), os.path.join(DST, p), ignore=shutil.ignore_patterns("*.map", "esbuild-metafile.json"))
for a in ARQS:
    if os.path.exists(os.path.join(SRC, a)):
        shutil.copy2(os.path.join(SRC, a), os.path.join(DST, a))
trocadas = []
for a in DO_JOGO:
    f = os.path.join(DST, "assets", a)
    if os.path.exists(f):
        shutil.copy2(os.path.join(DST, "assets", "missing.png"), f)
        trocadas.append(a)
shutil.copy2(os.path.join(AQUI, "banco-estudio.js"), os.path.join(DST, "banco-estudio.js"))
# estatística de uso do autor (instalação nova, usuário recorrente, atualização, plugin instalado): desligada na nossa cópia
bundle = os.path.join(DST, "dist", "bundle.js")
bj = open(bundle, encoding="utf-8").read()
n_est = bj.count("https://blckbn.ch/api/event/")
bj = bj.replace("https://blckbn.ch/api/event/", "./sem-estatistica/")
open(bundle, "w", encoding="utf-8").write(bj)
h = open(os.path.join(DST, "index.html"), encoding="utf-8").read()
if "banco-estudio.js" not in h:
    h = h.replace("</body>", '\t<script src="banco-estudio.js"></script>\n</body>', 1)
    # porteiro do login com Google do site novo (problemsbloxcreate-lab.github.io); no site antigo do estúdio o arquivo não existe
    h = h.replace("<head>", '<head>\n\t<script src="/estudio-login.js"></script>', 1)
    h = h.replace("<title>Blockbench</title>", "<title>Blockbench · Modelador do Estúdio Problems</title>", 1)
if "estudio-conta.js" not in h:
    h = h.replace("<title>", '<!-- botão da conta do Estúdio Problems (foto, nome, Minha conta, menu, sair) no canto da barra do Blockbench -->\n\t<style>body .ep-conta.solto{top:2px;right:8px}body .ep-conta.solto .ep-conta-btn{width:26px;height:26px;font-size:12px}body .ep-conta.solto .ep-conta-pop{top:32px}body .ep-conta.solto .ep-conta-menu{height:26px!important;font-size:12.5px!important;padding:0 10px 0 8px!important;color:#e9ebef}body .ep-conta.solto .ep-conta-espaco{width:26px;height:26px}a[href="https://blockbench.net/downloads"]{display:none!important}</style>\n\t<script src="/estudio-conta.js" defer></script>' + "\n\t<title>", 1)
open(os.path.join(DST, "index.html"), "w", encoding="utf-8").write(h)
try:
    rev = subprocess.run(["git", "-C", SRC, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
except Exception:
    rev = "?"
ver = ""
try:
    import json
    ver = json.load(open(os.path.join(SRC, "package.json")))["version"]
except Exception:
    pass
open(os.path.join(DST, "ORIGEM.md"), "w", encoding="utf-8").write(f"""# Blockbench (versão web) dentro do Modelador

Este é o Blockbench {ver}, de JannisX11 e colaboradores, licença **GPL-3.0** (texto completo em LICENSE.MD).
Código-fonte original: https://github.com/JannisX11/blockbench (commit {rev}).
Montado em {datetime.date.today().isoformat()} por `blockbench/montar.py` do repositório https://github.com/problemsbloxcreate-lab/modelador,
que guarda também o script de montagem e o plugin.

O que foi mudado em relação ao original:
- compilado com `npm run build-web` e copiado só o que a versão web usa;
- estas imagens de referência que imitam o Minecraft foram trocadas pela imagem neutra missing.png do próprio Blockbench: {", ".join(trocadas) or "nenhuma"};
- a estatística de uso que o Blockbench manda para o servidor do autor (blckbn.ch/api/event/…, {n_est} chamadas) foi desligada;
- a página carrega o plugin `banco-estudio.js` (licença MIT), que liga o Blockbench ao banco de modelos do Estúdio Problems;
- o título da página.
""")
tam = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(DST) for f in fs)
print(f"ok: {DST} · {tam/1048576:.1f} MB · imagens trocadas: {len(trocadas)} · estatística desligada: {n_est}")
