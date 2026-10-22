#!/usr/bin/env python3
"""Blockbench sem tela: o robô (ou o Claude no chat) modela, pinta e anima DENTRO do Blockbench (a nossa cópia em
blockbench/app), num navegador invisível, e vê o resultado em fotos a cada etapa.

  python3 modelador/ferramentas/bbsemtela.py receita.js --saida PASTA [--abrir modelo.bbmodel] [--etapa "silhueta"]
          [--referencia ref1.jpg --referencia ref2.jpg] [--animacoes] [--sem-fotos]

  receita.js = corpo de uma função async que usa BBA (ferramentas/bb-ajudante.js) e o Blockbench (Cube, Group, Texture…).
               Sem --abrir, a receita começa com BBA.novo(...). Com --abrir, continua o modelo salvo (etapa seguinte).
  Saída em PASTA:
    modelo.bbmodel       o modelo depois da receita (abre no Blockbench e entra no banco com bbmodel-para-estudio.py)
    fotos/*.png          frente, 3/4, lado, costas, cima, baixo (renderizadas pelo próprio Blockbench)
    folha.png            as fotos lado a lado (+ as imagens de referência, se houver) com o nome da etapa
    anim-<nome>.png      (com --animacoes) quadros de cada animação numa tira, e anim-<nome>.gif animado
    info.json            cubos, ossos, textura, animações, tamanho em pixels, erros
Exemplo de receita: modelador/modelos-fonte/exemplo-receita.js
"""
import argparse, base64, functools, http.server, io, json, os, sys, threading

AQUI = os.path.dirname(os.path.abspath(__file__))
APP = os.path.normpath(os.path.join(AQUI, "..", "blockbench", "app"))

ANGULOS = [  # nome, direção da câmera a partir do centro (frente do modelo = norte = -z)
    ("frente", (0, 0.12, -1)), ("3-4", (-0.75, 0.42, -0.85)), ("lado", (-1, 0.1, 0)),
    ("costas", (0, 0.12, 1)), ("3-4-costas", (0.75, 0.42, 0.85)), ("cima", (0.25, 1.4, -0.35)),
]

JS_FOTO = r"""async (dir)=>{
 const P=Preview.selected; const b=new THREE.Box3(); Cube.all.forEach(c=>{if(!c.visibility)return;c.mesh&&b.expandByObject(c.mesh);});
 if(b.isEmpty()) b.set(new THREE.Vector3(-8,0,-8),new THREE.Vector3(8,16,8));
 const c=b.getCenter(new THREE.Vector3()), s=b.getSize(new THREE.Vector3()), r=Math.max(8,s.length()/2);
 P.setProjectionMode(false); P.setFOV(30);
 const d=new THREE.Vector3(...dir).normalize(), dist=r/Math.sin(15*Math.PI/180)*1.02;
 P.camera.position.copy(c).addScaledVector(d,dist); P.controls.target.copy(c); P.camera.lookAt(c); P.controls.update&&P.controls.update();
 P.render(); return P.canvas.toDataURL('image/png');}"""


def servidor(pasta):
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Q, directory=pasta)
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s.server_address[1]


def folha(fotos, refs, titulo, saida):
    from PIL import Image, ImageDraw, ImageFont
    try:
        F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except Exception:
        F = ImageFont.load_default()
    L = 300
    ims = [(n, Image.open(io.BytesIO(b)).convert("RGB")) for n, b in fotos]
    ims = [(n, im.resize((L, int(im.height * L / im.width)))) for n, im in ims]
    rf = []
    for p in refs:
        try:
            im = Image.open(p).convert("RGB"); im.thumbnail((L, L)); rf.append(("referência", im))
        except Exception:
            pass
    cel = rf + ims
    H = max(im.height for _, im in cel) + 30
    cols = min(4, len(cel)); lin = (len(cel) + cols - 1) // cols
    out = Image.new("RGB", (cols * L, lin * H + 40), "#16181c"); g = ImageDraw.Draw(out)
    g.text((10, 10), titulo, fill="#ffd400", font=F)
    for i, (n, im) in enumerate(cel):
        x, y = (i % cols) * L, 40 + (i // cols) * H
        out.paste(im, (x, y + 26)); g.text((x + 8, y + 4), n, fill="#7bd88f" if n == "referência" else "#d6d9df", font=F)
    out.save(saida)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("receita", nargs="?", help="arquivo .js (corpo de função async usando BBA)")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--abrir", help=".bbmodel para continuar")
    ap.add_argument("--etapa", default="")
    ap.add_argument("--referencia", action="append", default=[])
    ap.add_argument("--animacoes", action="store_true", help="tira quadros de cada animação (tira + gif)")
    ap.add_argument("--quadros", type=int, default=8)
    ap.add_argument("--sem-fotos", action="store_true")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.saida, "fotos"), exist_ok=True)
    if not os.path.exists(os.path.join(APP, "dist", "bundle.js")):
        sys.exit("falta o Blockbench montado em blockbench/app (Action 'Montar o Blockbench do Modelador')")
    receita = open(a.receita, encoding="utf-8").read() if a.receita else ""
    ajud = open(os.path.join(AQUI, "bb-ajudante.js"), encoding="utf-8").read()
    porta = servidor(APP)
    from playwright.sync_api import sync_playwright
    info = {"erros": []}
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        pg = b.new_page(viewport={"width": 1400, "height": 900})
        pg.on("pageerror", lambda e: info["erros"].append(str(e)[:300]))
        local = f"http://127.0.0.1:{porta}/"

        def rota(r):
            u = r.request.url
            if u.startswith(local) and not u.endswith("/estudio-login.js") and not u.endswith("/estudio-conta.js"):
                return r.continue_()
            if u.endswith(".js"):
                return r.fulfill(status=200, content_type="text/javascript", body="")
            return r.abort()
        pg.route("**/*", rota)
        pg.goto(local)
        pg.wait_for_function("window.Blockbench&&Blockbench.setup_successful", timeout=90000)
        pg.wait_for_timeout(1200)
        pg.add_script_tag(content=ajud)
        if a.abrir:
            txt = open(a.abrir, encoding="utf-8").read()
            pg.evaluate("t=>{loadModelFile({path:'modelo.bbmodel',name:'modelo.bbmodel',content:t});}", txt)
            pg.wait_for_timeout(1500)
            pg.evaluate("()=>{const t=Texture.all[0];if(t)window.__tex=t;}")
        if receita:
            r = pg.evaluate("async c=>{try{const f=new (Object.getPrototypeOf(async function(){}).constructor)('BBA',c);await f(window.BBA);return {ok:true};}catch(e){return {ok:false,erro:String(e&&e.stack||e).slice(0,1500)};}}", receita)
            if not r.get("ok"):
                info["erros"].append("receita: " + r.get("erro", ""))
        pg.evaluate("()=>{try{Canvas.updateAll();}catch(e){}}")
        pg.wait_for_timeout(500)
        info.update(pg.evaluate("()=>{try{return BBA.info();}catch(e){return {erro_info:String(e)};}}"))
        bb = pg.evaluate("()=>BBA.salvar()")
        open(os.path.join(a.saida, "modelo.bbmodel"), "w", encoding="utf-8").write(bb)
        fotos = []
        if not a.sem_fotos:
            pg.evaluate("()=>{try{Modes.options.edit.select();}catch(e){}}")
            for nome, d in ANGULOS:
                url = pg.evaluate(JS_FOTO, list(d))
                dados = base64.b64decode(url.split(",", 1)[1])
                open(os.path.join(a.saida, "fotos", nome + ".png"), "wb").write(dados)
                fotos.append((nome, dados))
            folha(fotos, a.referencia, (a.etapa + " · " if a.etapa else "") + f"{info.get('cubos', '?')} cubos · {', '.join(info.get('textura', [])) or 'sem textura'}",
                  os.path.join(a.saida, "folha.png"))
        if a.animacoes and info.get("animacoes"):
            from PIL import Image
            pg.evaluate("()=>{try{Modes.options.animate.select();}catch(e){}}")
            info["quadros"] = {}
            for an in info["animacoes"]:
                ims = []
                n = max(2, a.quadros)
                for i in range(n):
                    t = an["dur"] * i / n
                    pg.evaluate("([nome,t])=>{const a=Animation.all.find(x=>x.name===nome);a.select();Timeline.setTime(t);Animator.preview();}", [an["nome"], t])
                    url = pg.evaluate(JS_FOTO, [-0.75, 0.42, -0.85])
                    ims.append(Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).convert("RGB"))
                L = 260; ims = [im.resize((L, int(im.height * L / im.width))) for im in ims]
                tira = Image.new("RGB", (L * len(ims), ims[0].height), "#16181c")
                for i, im in enumerate(ims):
                    tira.paste(im, (i * L, 0))
                seguro = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in an["nome"])
                tira.save(os.path.join(a.saida, f"anim-{seguro}.png"))
                ims[0].save(os.path.join(a.saida, f"anim-{seguro}.gif"), save_all=True, append_images=ims[1:], duration=int(an["dur"] * 1000 / n), loop=0)
                info["quadros"][an["nome"]] = f"anim-{seguro}.png"
            pg.evaluate("()=>{try{Modes.options.edit.select();}catch(e){}}")
        b.close()
    json.dump(info, open(os.path.join(a.saida, "info.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
