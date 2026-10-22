#!/usr/bin/env python3
"""Modelos 3D no estilo Minecraft para o Estúdio Problems (e para o jogo).

Um arquivo do banco (site/dados/modelos/<id>.json) é a FONTE de verdade. Ele usa o formato de modelo do BBS
(groups/origin/rotate/parent/cubes/uvs), que o estúdio desenha e o mod estudio-poses lê no jogo.
Daqui saem os outros destinos:

  python3 modelador/ferramentas/modelos3d.py conferir  <id|arquivo.json>              regras numéricas da skill modelar-3d
  python3 modelador/ferramentas/modelos3d.py foto      <id|arquivo.json> [--saida P]  folha de conferência renderizada NO estúdio
  python3 modelador/ferramentas/modelos3d.py registrar <id>                           põe no _lista.json e no índice (modelosmeta)
  python3 modelador/ferramentas/modelos3d.py exportar  <id|arquivo.json> --saida P [--bbmodel] [--bbs] [--pacote] [--item paper --cmd 7001]
  python3 modelador/ferramentas/modelos3d.py ida-e-volta <id|arquivo.json>          estúdio → .bbmodel → estúdio dá o mesmo modelo?

  .bbmodel (Blockbench) → estúdio: modelador/ferramentas/bbmodel-para-estudio.py

Eixos e unidades (iguais ao Blockbench e ao BBS): 1 pixel = 1 unidade, 1 bloco = 16. y para cima, chão em y = 0.
A FRENTE do modelo olha para -z (o "norte" do Blockbench). O lado DIREITO do personagem fica em +x.
Nomes de faces: front = north (-z), back = south (+z), right = east (+x), left = west (-x), top = up, bottom = down.
UV em pixels da textura ([u1, v1, u2, v2]); "texture": [largura, altura] da textura.
"""
import argparse, base64, colorsys, copy, io, json, math, os, re, sys, uuid as _uuid

def _acha_estudio():
    """Onde está o Estúdio Problems (o banco de modelos e o desenho do estúdio moram lá).
    Ordem: variável ESTUDIO; uma pasta acima que tenha site/index.html (o modelador clonado DENTRO do estúdio, como faz o robô);
    ../estudio-problems ao lado do modelador."""
    if os.environ.get("ESTUDIO"):
        return os.path.abspath(os.environ["ESTUDIO"])
    aqui = os.path.dirname(os.path.abspath(__file__))
    for base in (os.getcwd(), aqui):
        d = base
        for _ in range(5):
            if os.path.exists(os.path.join(d, "site", "index.html")) and os.path.exists(os.path.join(d, "script", "cenas", "quadros.py")):
                return d
            d = os.path.dirname(d)
    vizinho = os.path.normpath(os.path.join(aqui, "..", "..", "estudio-problems"))
    if os.path.exists(os.path.join(vizinho, "site", "index.html")):
        return vizinho
    sys.exit("Não achei o Estúdio Problems: rode de dentro dele ou diga onde está com ESTUDIO=/caminho/do/estudio-problems")


RAIZ = _acha_estudio()
BANCO = os.path.join(RAIZ, "site", "dados", "modelos")
INDICE = os.path.join(RAIZ, "site", "dados", "modelosmeta", "indice.json")
FACES = ("front", "back", "right", "left", "top", "bottom")
BB2EST = {"north": "front", "south": "back", "east": "right", "west": "left", "up": "top", "down": "bottom"}
EST2BB = {v: k for k, v in BB2EST.items()}
NOMES_PACK = {"livres": "Livres (licença aberta)", "estudio": "Feitos no estúdio"}
OSSOS = ("head", "right_arm", "left_arm", "right_leg", "left_leg")


# ---------------------------------------------------------------- montar um modelo por código
def box_uv(w, h, d, u=0, v=0, espelho=False):
    """Caixa UV (box UV) do Blockbench/Minecraft para um cubo w×h×d com o canto da caixa em (u, v).
    Desenho na textura (largura 2d+2w, altura d+h):   [   ][top][bot]
                                                       [rgt][frt][lft][bck]
    (right = east = +x, que é o lado direito do personagem). Mesma conta de Blockbench cube.js updateUV."""
    w, h, d = math.floor(w), math.floor(h), math.floor(d)
    L = {"east": ([0, d], [d, h]), "west": ([d + w, d], [d, h]), "up": ([d + w, d], [-w, -d]),
         "down": ([d + 2 * w, 0], [-w, d]), "south": ([2 * d + w, d], [w, h]), "north": ([d, d], [w, h])}
    if espelho:
        L = {k: ([f[0] + s[0], f[1]], [-s[0], s[1]]) for k, (f, s) in L.items()}
        L["east"], L["west"] = L["west"], L["east"]
    return {BB2EST[k]: [f[0] + u, f[1] + v, f[0] + s[0] + u, f[1] + s[1] + v] for k, (f, s) in L.items()}


class Modelo:
    """Modelo do estúdio montado por código. Grupos = ossos (giram em volta de origin). Cubos em coordenadas do modelo."""

    def __init__(self, largura=64, altura=64):
        self.groups, self.texture = {}, [largura, altura]

    def grupo(self, nome, origin, parent=None, rotate=None):
        g = {"origin": [float(x) for x in origin]}
        if parent:
            g["parent"] = parent
        if rotate and any(rotate):
            g["rotate"] = [float(x) for x in rotate]
        self.groups[nome] = g
        return g

    def cubo(self, grupo, de, tam, uv=None, uvs=None, inflar=0, rotate=None, origin=None, espelho=False, sem=()):
        """de = canto de baixo (x, y, z); tam = (w, h, d). uv=(u, v) usa caixa UV; uvs={face:[u1,v1,u2,v2]} para faces livres.
        sem = faces sem desenho (ex.: ("bottom",) num plano)."""
        c = {"origin": [float(x) for x in (origin or de)], "from": [float(x) for x in de], "size": [float(x) for x in tam]}
        if inflar:
            c["offset"] = float(inflar)
        if rotate and any(rotate):
            c["rotate"] = [float(x) for x in rotate]
        if uvs is None:
            uvs = box_uv(*tam, *(uv or (0, 0)), espelho=espelho)
        c["uvs"] = {k: [float(x) for x in v] for k, v in uvs.items() if k not in sem}
        self.groups[grupo].setdefault("cubes", []).append(c)
        return c

    def json(self):
        return {"groups": self.groups, "texture": self.texture}


# ---------------------------------------------------------------- cor e pintura (Pillow)
def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rampa(base, n=5, passo_luz=0.13, giro=0.035, sat=0.06):
    """Rampa de cores com hue shifting a partir do MEIO-TOM (base) — índice n//2 é a base.
    Para o escuro: menos luz, mais saturação, matiz puxada para azul/roxo (fria). Para o claro: mais luz, menos
    saturação, matiz puxada para amarelo (quente). passo_luz ≈ 0,13 (13 pontos de 100) por degrau; giro 0,035 ≈ 12°."""
    r, g, b = [x / 255 for x in (hexrgb(base) if isinstance(base, str) else base[:3])]
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    out, meio = [], n // 2

    def puxa(hue, alvo, f):  # gira a matiz na direção do alvo pelo caminho mais curto
        dlt = ((alvo - hue + 0.5) % 1.0) - 0.5
        return (hue + max(-abs(f), min(abs(f), dlt))) % 1.0

    for i in range(n):
        k = i - meio  # <0 escuro, >0 claro
        l2 = max(0.03, min(0.97, ll + k * passo_luz))
        s2 = max(0.0, min(1.0, ss - k * sat))
        h2 = puxa(hh, 0.70 if k < 0 else 0.15, giro * abs(k)) if k else hh
        r2, g2, b2 = colorsys.hls_to_rgb(h2, l2, s2)
        out.append((round(r2 * 255), round(g2 * 255), round(b2 * 255), 255))
    return out


def ruido(x, y, semente=0):
    """número fixo 0..1 por pixel (sem aleatório de verdade: a textura sai igual toda vez)."""
    n = (x * 374761393 + y * 668265263 + semente * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


class Textura:
    """Textura pintada pixel a pixel. Use os retângulos das faces (cubo['uvs']) para saber onde pintar."""

    def __init__(self, largura, altura):
        from PIL import Image
        self.img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
        self.px = self.img.load()

    def ponto(self, x, y, cor):
        if 0 <= x < self.img.width and 0 <= y < self.img.height:
            self.px[x, y] = tuple(cor) if len(cor) == 4 else tuple(cor) + (255,)

    def ret(self, x0, y0, x1, y1, cor):  # x1/y1 de fora (como range)
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.ponto(x, y, cor)

    @staticmethod
    def caixa(uv):
        """retângulo [x0, y0, x1, y1] (pixels, x1/y1 de fora) e se a face está espelhada em u/v."""
        u1, v1, u2, v2 = uv[:4]
        return [int(min(u1, u2)), int(min(v1, v2)), int(max(u1, u2)), int(max(v1, v2))], u2 < u1, v2 < v1

    def face(self, cubo, nome, fn):
        """chama fn(i, j, w, h) para cada pixel da face (i da esquerda para a direita e j de cima para baixo,
        como a face aparece no modelo) e pinta o que fn devolver (None = não mexe)."""
        if nome not in cubo.get("uvs", {}):
            return
        (x0, y0, x1, y1), fu, fv = self.caixa(cubo["uvs"][nome])
        w, h = x1 - x0, y1 - y0
        for j in range(h):
            for i in range(w):
                c = fn(i, j, w, h)
                if c is not None:
                    self.ponto(x0 + (w - 1 - i if fu else i), y0 + (h - 1 - j if fv else j), c)

    def png(self):
        b = io.BytesIO()
        self.img.save(b, "PNG", optimize=True)
        return b.getvalue()


def sombra_por_face(nome):
    """degrau da rampa para cada face (luz de cima e da frente-esquerda): topo +1, frente 0, lados -1/0, costas e baixo -1/-2."""
    return {"top": 1, "front": 0, "left": 0, "right": -1, "back": -1, "bottom": -2}[nome]


# ---------------------------------------------------------------- arquivos do banco
def ler(alvo):
    """aceita id do banco ou caminho de arquivo; devolve (dados, caminho)."""
    p = alvo if os.path.exists(alvo) else os.path.join(BANCO, alvo + ".json")
    with open(p, encoding="utf-8") as f:
        return json.load(f), p


def montar_arquivo(modelo, nome, pack, tipo, uso, texturas, mao=None, animacoes=None):
    """arquivo do banco: modelo vai como TEXTO JSON (é assim que o banco guarda); texturas = [(nome, bytes_png)]."""
    d = {"nome": nome, "pack": pack, "tipo": tipo, "uso": uso,
         "modelo": json.dumps(modelo, ensure_ascii=False, separators=(",", ":")),
         "tex": [{"n": n, "p": base64.b64encode(p).decode()} for n, p in texturas]}
    if mao:
        d["mao"] = mao
    if animacoes:
        d["animacoes"] = animacoes  # fora do "modelo" (o estúdio antigo continua lendo o modelo igual)
    return d


def salvar(id_, d, substituir=False):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,80}", id_):
        sys.exit(f"id inválido: {id_} (use letras minúsculas, números e hífen)")
    p = os.path.join(BANCO, id_ + ".json")
    if os.path.exists(p) and not substituir:
        sys.exit(f"{p} já existe: não sobrescrevo (use outro id ou --substituir se for um modelo SEU)")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    return p


def registrar(id_):
    """põe o id no _lista.json e no índice (modelosmeta/indice.json), que é o que a aba de skins/models lê primeiro.
    Sem o índice, o modelo NÃO aparece no estúdio."""
    d, _ = ler(id_)
    lp = os.path.join(BANCO, "_lista.json")
    lista = json.load(open(lp, encoding="utf-8"))
    if id_ not in lista:
        lista.append(id_)
        lista.sort()
        json.dump(lista, open(lp, "w", encoding="utf-8"), ensure_ascii=False)
    idx = json.load(open(INDICE, encoding="utf-8"))
    it = {"id": id_, "nome": d["nome"], "pack": d.get("pack", "outros"), "tex": [t["n"] for t in d.get("tex", [])],
          **({"anims": [x["nome"] for x in d["animacoes"]]} if d.get("animacoes") else {}),
          "tipo": d.get("tipo", "objeto"), "uso": d.get("uso", "mao")}
    if d.get("mao"):
        it["mao"] = d["mao"]
    # mantém a ordem que já existe (mudança mínima no arquivo); um modelo novo entra no fim, um que já existia fica no lugar
    ids = [x["id"] for x in idx["itens"]]
    if id_ in ids:
        idx["itens"][ids.index(id_)] = it
    else:
        idx["itens"].append(it)
    conta = {}
    for x in idx["itens"]:
        conta[x["pack"]] = conta.get(x["pack"], 0) + 1
    packs = {p["id"]: p for p in idx["packs"]}
    for pid, n in conta.items():
        if pid not in packs:
            packs[pid] = {"id": pid, "n": n, "nome": NOMES_PACK.get(pid, pid.capitalize())}
            idx["packs"].append(packs[pid])
        packs[pid]["n"] = n
    with open(INDICE, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    print(f"registrado: {id_} (pack {it['pack']}, {len(idx['itens'])} modelos no índice)")


# ---------------------------------------------------------------- conferir (regras numéricas)
def conferir(d):
    """devolve (avisos, números). Avisos = coisas a corrigir antes de entregar."""
    from PIL import Image
    M = json.loads(d["modelo"]) if isinstance(d["modelo"], str) else d["modelo"]
    G, (tw, th) = M["groups"], M.get("texture", [64, 64])
    av, cubos = [], [(g, c) for g, x in G.items() for c in x.get("cubes", [])]
    img = Image.open(io.BytesIO(base64.b64decode(d["tex"][0]["p"]))).convert("RGBA") if d.get("tex") else None
    if not d.get("tex"):
        av.append("sem textura")
    kx, ky = (img.width / tw, img.height / th) if img else (1, 1)
    eixos = {"front": (0, 1), "back": (0, 1), "right": (2, 1), "left": (2, 1), "top": (0, 2), "bottom": (0, 2)}
    estica, fora, transp, frac = 0, 0, 0, 0
    for g, c in cubos:
        s = c["size"]
        for a in s:
            if 0 < a < 1:
                av.append(f"{g}: cubo com lado de {a} px (menor que 1 px = 'mixel'; use 1 px ou um plano de lado 0)")
        if any(abs(a - round(a)) > 1e-6 for a in s):
            frac += 1
        if abs(c.get("offset", 0)) > 1.01:
            av.append(f"{g}: inflado demais ({c['offset']} px; o guia aceita só um pouco, ex.: 0,25 a 0,5 para 'roupa')")
        for f, uv in c.get("uvs", {}).items():
            a, b = eixos[f]
            if s[a] == 0 or s[b] == 0 or uv[0] == uv[2] or uv[1] == uv[3]:
                continue  # face de espessura zero não aparece; UV achatada = cor única de propósito
            du, dv = abs(uv[2] - uv[0]) * kx, abs(uv[3] - uv[1]) * ky
            if abs(du / s[a] - dv / s[b]) > 0.02 or abs(du / s[a] - 1) > 0.02:
                estica += 1
            if min(uv[0], uv[2]) < 0 or min(uv[1], uv[3]) < 0 or max(uv[0], uv[2]) > tw + 1e-6 or max(uv[1], uv[3]) > th + 1e-6:
                fora += 1
            elif img and 0 not in s:
                x0, x1 = sorted((uv[0] * kx, uv[2] * kx))
                y0, y1 = sorted((uv[1] * ky, uv[3] * ky))
                vazio = sum(1 for y in range(int(y0), int(math.ceil(y1))) for x in range(int(x0), int(math.ceil(x1))) if img.getpixel((min(x, img.width - 1), min(y, img.height - 1)))[3] == 0)
                if vazio == (int(math.ceil(x1)) - int(x0)) * (int(math.ceil(y1)) - int(y0)):
                    transp += 1
    if frac:
        av.append(f"{frac} cubo(s) de tamanho fracionado (ex.: 2,5 px): a grade de pixels fica torta; use tamanhos inteiros")
    if estica:
        av.append(f"{estica} face(s) com textura esticada ou encolhida (regra: 1 px de textura = 1 px de modelo)")
    if fora:
        av.append(f"{fora} face(s) com UV fora da textura")
    if transp:
        av.append(f"{transp} face(s) de cubo cheio totalmente transparentes (esqueceu de pintar? em plano, ok)")
    nomes = set(G)
    for g, x in G.items():
        if x.get("parent") and x["parent"] not in G:
            av.append(f"{g}: pai '{x['parent']}' não existe")
    if d.get("tipo") == "personagem":
        falta = [o for o in OSSOS if o not in nomes]
        if falta:
            av.append("personagem sem os ossos " + ", ".join(falta) + " (sem eles a pose do estúdio não mexe essas partes)")
        for o in OSSOS:
            if o not in G or not G[o].get("cubes"):
                continue
            ys = [c["from"][1] for c in G[o]["cubes"]] + [c["from"][1] + c["size"][1] for c in G[o]["cubes"]]
            xs = [c["from"][0] + c["size"][0] / 2 for c in G[o]["cubes"]]
            oy = G[o]["origin"][1]
            if o == "head" and abs(oy - min(ys)) > 1.01:
                av.append(f"head: pivô em y={oy}, mas o pescoço (base da cabeça) está em y={min(ys)} (a cabeça vai girar fora do lugar)")
            if o != "head" and abs(oy - max(ys)) > 2.01:
                av.append(f"{o}: pivô em y={oy}, mas o topo (ombro/quadril) está em y={max(ys)} (gira fora da junta)")
            lado = 1 if o.startswith("right") else -1 if o.startswith("left") else 0
            if lado and sum(xs) / len(xs) * lado < 0:
                av.append(f"{o}: está do lado errado (o direito do personagem fica em +x quando ele olha para -z)")
    if img and (img.width & (img.width - 1) or img.height & (img.height - 1)):
        av.append(f"textura {img.width}×{img.height} não é potência de 2 (o estúdio aceita; para o jogo/pacote prefira 16, 32, 64, 128)")
    num = {"grupos": len(G), "cubos": len(cubos), "textura": [img.width, img.height] if img else None, "uv": [tw, th],
           "altura_px": round(max((c["from"][1] + c["size"][1] for _, c in cubos), default=0) - min((c["from"][1] for _, c in cubos), default=0), 2),
           "largura_px": round(max((c["from"][0] + c["size"][0] for _, c in cubos), default=0) - min((c["from"][0] for _, c in cubos), default=0), 2)}
    return av, num


# ---------------------------------------------------------------- .bbmodel (Blockbench) ↔ estúdio
def _png_de_fonte(src):
    if not src or not src.startswith("data:"):
        return None
    return base64.b64decode(src.split(",", 1)[1])


def de_bbmodel(bb, avisos=None):
    """.bbmodel → (modelo do estúdio, png). Junta todas as texturas numa só (o estúdio e o BBS usam UMA por modelo),
    desfaz a rotação de UV (o estúdio não lê o 5º número) pintando a face já girada, e põe os cubos soltos no grupo 'anchor'."""
    from PIL import Image
    av = avisos if avisos is not None else []
    meta = bb.get("meta", {})
    res = bb.get("resolution") or {"width": 16, "height": 16}
    texs = []
    for t in bb.get("textures", []):
        b = _png_de_fonte(t.get("source"))
        if b is None:
            av.append(f"textura '{t.get('name')}' sem imagem embutida (salve o .bbmodel com as texturas dentro)")
            texs.append(None)
            continue
        im = Image.open(io.BytesIO(b)).convert("RGBA")
        uw, uh = t.get("uv_width") or res["width"], t.get("uv_height") or res["height"]
        texs.append({"img": im, "kx": im.width / uw, "ky": im.height / uh, "id": t.get("uuid"), "nome": t.get("name")})
    porid = {t["id"]: i for i, t in enumerate(texs) if t and t.get("id")}
    els = {e["uuid"]: e for e in bb.get("elements", [])}
    # UV que cai no meio de um pixel (textura menor que a grade de UV): amplia a imagem (sem borrar) até a UV cair inteira
    usos = {}
    for e in els.values():
        for f in (e.get("faces") or {}).values():
            tx = f.get("texture")
            ti = porid.get(tx, tx) if isinstance(tx, str) else tx
            if isinstance(ti, int) and ti < len(texs) and texs[ti] and f.get("uv"):
                usos.setdefault(ti, []).extend(f["uv"][:4])
    for ti, vs in usos.items():
        t = texs[ti]
        for k in (1, 2, 4, 8, 16):
            if all(abs(v * t["kx"] * k - round(v * t["kx"] * k)) < 0.02 and abs(v * t["ky"] * k - round(v * t["ky"] * k)) < 0.02 for v in vs):
                break
        else:
            k = 1
            av.append(f"textura '{t['nome']}': a UV não bate com a grade de pixels; o recorte foi aproximado")
        if k > 1:
            t["img"] = t["img"].resize((t["img"].width * k, t["img"].height * k), Image.NEAREST)
            t["kx"], t["ky"] = t["kx"] * k, t["ky"] * k
    gdef = {g["uuid"]: g for g in bb.get("groups", []) or []}  # formato 5.0: dados dos grupos fora do outliner

    # 1) pedaços de textura que cada face usa → atlas
    pedacos, chave, achatado = [], {}, []

    def pedaco(ti, uv, rot):
        t = texs[ti]
        x0, x1 = sorted((uv[0] * t["kx"], uv[2] * t["kx"]))
        y0, y1 = sorted((uv[1] * t["ky"], uv[3] * t["ky"]))
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        zu, zv = x1 == x0, y1 == y0  # face de UV "achatada" (uma linha/coluna só): guarda 1 px e devolve achatada
        x1, y1 = max(x1, x0 + 1), max(y1, y0 + 1)
        k = (ti, x0, y0, x1, y1, uv[2] < uv[0], uv[3] < uv[1], rot % 360, zu, zv)
        if k not in chave:
            im = t["img"].crop((x0, y0, x1, y1))
            if uv[2] < uv[0]:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            if uv[3] < uv[1]:
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            # Blockbench gira a UV no sentido HORÁRIO: rotation 90 = imagem girada 90° horário na face
            for _ in range((rot % 360) // 90):
                im = im.transpose(Image.ROTATE_270)
            chave[k] = len(pedacos)
            pedacos.append(im)
            achatado.append((zu, zv) if (rot % 180) == 0 else (zv, zu))
        return chave[k]

    def uv_caixa(e):
        """UV de caixa (box UV) a partir de uv_offset, como o Blockbench faz."""
        s = [math.floor(e["to"][i] - e["from"][i] + 1e-6) for i in range(3)]
        o = e.get("uv_offset") or [0, 0]
        r = box_uv(s[0], s[1], s[2], o[0], o[1], espelho=e.get("mirror_uv", False))
        return {EST2BB[k]: v for k, v in r.items()}

    caixa_proj = bool(meta.get("box_uv"))
    faces_el = {}
    for uid, e in els.items():
        if e.get("type", "cube") != "cube":
            av.append(f"'{e.get('name')}' é {e.get('type')} (malha): o estúdio só desenha cubos, ficou de fora")
            continue
        if e.get("export") is False:
            continue
        caixa = e.get("box_uv", caixa_proj)
        cu = uv_caixa(e) if caixa and e.get("uv_offset") is not None else None
        fs = {}
        for fn, f in (e.get("faces") or {}).items():
            tx = f.get("texture")
            if tx is None or tx is False:
                continue  # face desligada
            ti = porid.get(tx, tx) if isinstance(tx, str) else tx
            if not isinstance(ti, int) or ti >= len(texs) or texs[ti] is None:
                ti = 0 if texs and texs[0] else None
            if ti is None:
                continue
            uv = cu[fn] if cu else f.get("uv")
            if not uv:
                continue
            fs[BB2EST[fn]] = pedaco(ti, uv, int(f.get("rotation", 0) or 0))
        faces_el[uid] = fs

    # 2) empacota os pedaços (prateleiras, do mais alto para o mais baixo) num atlas potência de 2
    ordem = sorted(range(len(pedacos)), key=lambda i: (-pedacos[i].height, -pedacos[i].width))
    larg = 16
    while larg < max([p.width for p in pedacos] + [16]):
        larg *= 2
    area = sum(p.width * p.height for p in pedacos)
    while larg * larg < area * 1.15:
        larg *= 2
    while True:
        pos, x, y, hl = {}, 0, 0, 0
        for i in ordem:
            p = pedacos[i]
            if x + p.width > larg:
                x, y, hl = 0, y + hl, 0
            pos[i] = (x, y)
            x, hl = x + p.width, max(hl, p.height)
        alt = y + hl
        alt2 = 16
        while alt2 < alt:
            alt2 *= 2
        if alt2 <= larg * 2:
            break
        larg *= 2
    atlas = Image.new("RGBA", (larg, max(alt2, 16)), (0, 0, 0, 0))
    for i, p in enumerate(pedacos):
        atlas.paste(p, pos[i])

    # 3) grupos e cubos
    G = {}

    def nome_livre(n):
        n = n or "grupo"
        b, k = n, 2
        while n in G:
            n, k = f"{b}_{k}", k + 1
        return n

    def cubo_est(e):
        c = {"origin": list(map(float, e.get("origin", e["from"]))), "from": list(map(float, e["from"])),
             "size": [float(e["to"][i] - e["from"][i]) for i in range(3)]}
        if e.get("inflate"):
            c["offset"] = float(e["inflate"])
        if e.get("rotation") and any(e["rotation"]):
            c["rotate"] = list(map(float, e["rotation"]))
        uvs = {}
        for fn, pi in faces_el.get(e["uuid"], {}).items():
            x, y = pos[pi]
            zu, zv = achatado[pi]
            uvs[fn] = [x, y, x + (0 if zu else pedacos[pi].width), y + (0 if zv else pedacos[pi].height)]
        c["uvs"] = uvs
        return c

    def anda(no, pai):
        if isinstance(no, str):
            e = els.get(no)
            if e and e["uuid"] in faces_el:
                alvo = pai or "anchor"
                if alvo not in G:
                    G[alvo] = {"origin": [0.0, 0.0, 0.0]}
                G[alvo].setdefault("cubes", []).append(cubo_est(e))
            return
        g = dict(gdef.get(no.get("uuid"), {}), **{k: v for k, v in no.items() if k != "children"})
        if g.get("export") is False:
            return
        n = nome_livre(g.get("name"))
        G[n] = {"origin": list(map(float, g.get("origin", [0, 0, 0])))}
        if g.get("rotation") and any(g["rotation"]):
            G[n]["rotate"] = list(map(float, g["rotation"]))
        if pai:
            G[n]["parent"] = pai
        for ch in no.get("children", []):
            anda(ch, n)

    for no in bb.get("outliner", []):
        anda(no if isinstance(no, str) else no, None)
    b = io.BytesIO()
    atlas.save(b, "PNG", optimize=True)
    return {"groups": G, "texture": [atlas.width, atlas.height]}, b.getvalue()


def _num(v):
    try:
        return float(str(v).strip() or 0)
    except Exception:
        return 0.0  # expressão Molang (ex.: math.sin(query.anim_time)) não entra: vira 0


def anims_de_bbmodel(bb, nomes_grupo=None):
    """animações do Blockbench → lista do banco: [{nome, dur, loop, ossos:{grupo:{rotation|position|scale:[[t,x,y,z,interp],...]}}}].
    Valores como no Blockbench (graus e pixels, eixos do Blockbench); o estúdio e o Modelador trocam o sinal de x e z ao tocar,
    igual fazem com o 'rotate' dos grupos. nomes_grupo: uuid → nome usado no banco (se o conversor renomeou)."""
    out = []
    for a in bb.get("animations", []) or []:
        ossos = {}
        for uid, an in (a.get("animators") or {}).items():
            if an.get("type", "bone") != "bone":
                continue
            nome = (nomes_grupo or {}).get(uid) or an.get("name")
            if not nome:
                continue
            canais = {}
            for k in an.get("keyframes", []) or []:
                ch = k.get("channel")
                if ch not in ("rotation", "position", "scale"):
                    continue
                dp = (k.get("data_points") or [{}])[0]
                canais.setdefault(ch, []).append([round(_num(k.get("time")), 4), _num(dp.get("x")), _num(dp.get("y")), _num(dp.get("z")), k.get("interpolation") or "linear"])
            for ch in canais:
                canais[ch].sort(key=lambda x: x[0])
            if canais:
                ossos[nome] = canais
        if ossos:
            out.append({"nome": a.get("name") or "animacao", "dur": round(_num(a.get("length")) or 1.0, 4), "loop": a.get("loop") or "once", "ossos": ossos})
    return out


def anims_para_bbmodel(anims, uuid_grupo):
    """banco → animações do .bbmodel (para abrir no Blockbench e continuar animando)."""
    out = []
    for a in anims or []:
        animators = {}
        for osso, canais in (a.get("ossos") or {}).items():
            uid = uuid_grupo.get(osso)
            if not uid:
                continue
            kfs = []
            for ch, lst in canais.items():
                for t, x, y, z, it in lst:
                    kfs.append({"channel": ch, "data_points": [{"x": x, "y": y, "z": z}], "uuid": str(_uuid.uuid4()), "time": t, "color": -1, "interpolation": it})
            animators[uid] = {"name": osso, "type": "bone", "keyframes": kfs}
        out.append({"uuid": str(_uuid.uuid4()), "name": a.get("nome", "animacao"), "loop": a.get("loop", "loop"), "override": False,
                    "length": a.get("dur", 1), "snapping": 24, "selected": False, "anim_time_update": "", "blend_weight": "",
                    "start_delay": "", "loop_delay": "", "animators": animators})
    return out


def para_bbmodel(d, nome=None):
    """arquivo do banco → .bbmodel (Blockbench 4.10+, formato 'Generic Model', UV por face) para a equipe abrir e retocar.
    Para mandar ao jogo pelo BBS depois de retocar: no Blockbench, plugin 'BBS Model Ex/importer' → Export BBS model."""
    M = json.loads(d["modelo"]) if isinstance(d["modelo"], str) else d["modelo"]
    tw, th = M.get("texture", [64, 64])
    els, nos = [], {}
    for gn, g in M["groups"].items():
        nos[gn] = {"name": gn, "origin": g.get("origin", [0, 0, 0]), "rotation": g.get("rotate", [0, 0, 0]), "color": 0,
                   "uuid": str(_uuid.uuid4()), "export": True, "mirror_uv": False, "isOpen": True, "locked": False,
                   "visibility": True, "autouv": 0, "children": []}
        for i, c in enumerate(g.get("cubes", [])):
            s, f = c["size"], c["from"]
            e = {"name": f"{gn}_{i + 1}", "box_uv": False, "rescale": False, "locked": False, "render_order": "default",
                 "allow_mirror_modeling": True, "from": f, "to": [f[k] + s[k] for k in range(3)], "autouv": 0, "color": 0,
                 "origin": c.get("origin", [0, 0, 0]), "faces": {}, "type": "cube", "uuid": str(_uuid.uuid4())}
            if c.get("offset"):
                e["inflate"] = c["offset"]
            if c.get("rotate"):
                e["rotation"] = c["rotate"]
            for fn in FACES:
                uv = c.get("uvs", {}).get(fn)
                e["faces"][EST2BB[fn]] = {"uv": uv[:4], "texture": 0} if uv else {"uv": [0, 0, 0, 0], "texture": None}
                if uv and len(uv) > 4 and uv[4]:
                    e["faces"][EST2BB[fn]]["rotation"] = uv[4]
            els.append(e)
            nos[gn]["children"].append(e["uuid"])
    raiz = []
    for gn, g in M["groups"].items():
        p = g.get("parent")
        (nos[p]["children"] if p in nos else raiz).append(nos[gn])
    tex = d["tex"][0] if d.get("tex") else None
    texturas = []
    if tex:
        from PIL import Image
        im = Image.open(io.BytesIO(base64.b64decode(tex["p"])))
        texturas.append({"path": "", "name": tex["n"] + ".png", "folder": "", "namespace": "", "id": "0", "width": im.width,
                         "height": im.height, "uv_width": tw, "uv_height": th, "particle": False, "use_as_default": True,
                         "render_mode": "default", "render_sides": "auto", "visible": True, "mode": "bitmap", "saved": False,
                         "uuid": str(_uuid.uuid4()), "source": "data:image/png;base64," + tex["p"]})
    return {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": nome or d.get("nome", "modelo"),
            "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "", "variable_placeholder_buttons": [],
            "timeline_setups": [], "unhandled_root_fields": {}, "resolution": {"width": tw, "height": th},
            "elements": els, "outliner": raiz, "textures": texturas,
            "animations": anims_para_bbmodel(d.get("animacoes"), {gn: n["uuid"] for gn, n in nos.items()})}


# ---------------------------------------------------------------- jogo: BBS e pacote de recursos (Java 1.20.1)
def para_bbs(d, pasta, procedural=None):
    """pasta do modelo para o BBS mod: <pasta>/model.bbs.json + model.png (+ config.json).
    No jogo ela vai em .minecraft/config/bbs/assets/models/<id>/ (o nome da pasta vira o id do modelo no BBS)."""
    M = json.loads(d["modelo"]) if isinstance(d["modelo"], str) else d["modelo"]
    os.makedirs(pasta, exist_ok=True)
    G = copy.deepcopy(M["groups"])
    with open(os.path.join(pasta, "model.bbs.json"), "w", encoding="utf-8") as f:
        json.dump({"version": "0.7.2", "model": {"groups": G, "texture": M.get("texture", [64, 64])}, "animations": {}}, f, ensure_ascii=False, indent=1)
    if d.get("tex"):
        open(os.path.join(pasta, "model.png"), "wb").write(base64.b64decode(d["tex"][0]["p"]))
    if procedural is None:
        procedural = d.get("tipo") == "personagem" and all(o in G for o in OSSOS)
    cfg = {}
    if procedural:
        cfg["procedural"] = True
        if "right_arm_item" in G:
            cfg["items_main"] = ["right_arm_item"]
        if "left_arm_item" in G:
            cfg["items_off"] = ["left_arm_item"]
    if cfg:
        json.dump(cfg, open(os.path.join(pasta, "config.json"), "w", encoding="utf-8"), indent=1)
    return pasta


ANG_JAVA = (-45, -22.5, 0, 22.5, 45)


def para_pacote(d, pasta, id_, item="paper", cmd=7001, ns="estudio"):
    """pacote de recursos Java 1.20.1 (pack_format 15) com o modelo como ITEM (CustomModelData num item comum).
    Só serve para objetos simples: sem rotação de grupo, cubo girado em UM eixo só e ângulo de 22,5 em 22,5 até 45."""
    from PIL import Image
    M = json.loads(d["modelo"]) if isinstance(d["modelo"], str) else d["modelo"]
    tw, th = M.get("texture", [64, 64])
    av, elementos = [], []
    for gn, g in M["groups"].items():
        if g.get("rotate") and any(g["rotate"]):
            av.append(f"grupo {gn} girado: o modelo de item do Java não gira grupos")
        for c in g.get("cubes", []):
            f, s = c["from"], c["size"]
            e = {"from": [f[0] + 8, f[1], f[2] + 8], "to": [f[0] + s[0] + 8, f[1] + s[1], f[2] + s[2] + 8], "faces": {}}
            r = c.get("rotate") or [0, 0, 0]
            eix = [i for i in range(3) if r[i]]
            if len(eix) > 1 or (eix and r[eix[0]] not in ANG_JAVA):
                av.append(f"cubo de {gn} girado {r}: o Java só aceita um eixo e -45/-22,5/22,5/45")
            elif eix:
                o = c.get("origin", f)
                e["rotation"] = {"angle": r[eix[0]], "axis": "xyz"[eix[0]], "origin": [o[0] + 8, o[1], o[2] + 8]}
            if c.get("offset"):
                av.append(f"cubo de {gn} inflado: o Java não infla (ficou do tamanho normal)")
            for fn, uv in c.get("uvs", {}).items():
                e["faces"][EST2BB[fn]] = {"uv": [round(uv[0] * 16 / tw, 4), round(uv[1] * 16 / th, 4), round(uv[2] * 16 / tw, 4), round(uv[3] * 16 / th, 4)], "texture": "#0"}
            elementos.append(e)
    for e in elementos:
        if min(e["from"] + e["to"]) < -16 or max(e["from"] + e["to"]) > 32:
            av.append("modelo passa do limite do Java (-16 a 32 px a partir do canto do bloco): diminua")
            break
    if av:
        return None, av
    os.makedirs(pasta, exist_ok=True)
    json.dump({"pack": {"pack_format": 15, "description": "Estúdio Problems: modelos"}}, open(os.path.join(pasta, "pack.mcmeta"), "w"), indent=1)
    md = os.path.join(pasta, "assets", ns, "models", "item")
    tx = os.path.join(pasta, "assets", ns, "textures", "item")
    os.makedirs(md, exist_ok=True)
    os.makedirs(tx, exist_ok=True)
    im = Image.open(io.BytesIO(base64.b64decode(d["tex"][0]["p"]))).convert("RGBA")
    lado = 16
    while lado < max(im.width, im.height):
        lado *= 2
    if (im.width, im.height) != (lado, lado):  # Java quer textura quadrada: completa com transparente e corrige a UV
        q = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
        q.paste(im, (0, 0))
        for e in elementos:
            for f in e["faces"].values():
                f["uv"] = [round(f["uv"][0] * im.width / lado, 4), round(f["uv"][1] * im.height / lado, 4),
                           round(f["uv"][2] * im.width / lado, 4), round(f["uv"][3] * im.height / lado, 4)]
        im = q
    im.save(os.path.join(tx, id_ + ".png"))
    json.dump({"textures": {"0": f"{ns}:item/{id_}", "particle": f"{ns}:item/{id_}"}, "elements": elementos,
               "display": {"thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.55, 0.55, 0.55]},
                           "firstperson_righthand": {"rotation": [0, -20, 0], "translation": [1, 3, 0], "scale": [0.6, 0.6, 0.6]},
                           "gui": {"rotation": [30, 225, 0], "scale": [0.625, 0.625, 0.625]},
                           "ground": {"translation": [0, 3, 0], "scale": [0.25, 0.25, 0.25]}}},
              open(os.path.join(md, id_ + ".json"), "w"), indent=1)
    vd = os.path.join(pasta, "assets", "minecraft", "models", "item")
    os.makedirs(vd, exist_ok=True)
    vp = os.path.join(vd, item + ".json")
    base = json.load(open(vp)) if os.path.exists(vp) else {"parent": "minecraft:item/generated", "textures": {"layer0": f"minecraft:item/{item}"}, "overrides": []}
    base["overrides"] = [o for o in base.get("overrides", []) if o["predicate"].get("custom_model_data") != cmd] + [{"predicate": {"custom_model_data": cmd}, "model": f"{ns}:item/{id_}"}]
    base["overrides"].sort(key=lambda o: o["predicate"]["custom_model_data"])
    json.dump(base, open(vp, "w"), indent=1)
    return f"/give @p minecraft:{item}{{CustomModelData:{cmd}}}", []


# ---------------------------------------------------------------- foto no próprio estúdio
JS_FOTO = r"""(async(S)=>{const im=await loadImg('data:image/png;base64,'+S.png),W=S.w,H=S.h,R=new THREE.WebGLRenderer({antialias:false,alpha:false,preserveDrawingBuffer:true});
 R.setPixelRatio(1);R.setSize(W,H,false);const lm=curBright;ENTLM.forEach(u=>u.value=1);ENTLMC.forEach(u=>u.value.set(1,1,1));const out=[];
 try{for(const v of S.vistas){const sc=new THREE.Scene(),b=buildBBSBody(S.modelo,im);sc.add(b.body);
  const OS={head:b.head,right_arm:b.armR,left_arm:b.armL,right_leg:b.legR,left_leg:b.legL};
  if(v.pose)for(const k in v.pose){const n=OS[k];if(n)n.rotation.set(...v.pose[k].map(d=>d*Math.PI/180),'ZYX');}
  const bx=new THREE.Box3().setFromObject(b.body),ct=bx.getCenter(new THREE.Vector3()),sz=bx.getSize(new THREE.Vector3());
  const gs=Math.max(2,Math.ceil(Math.max(sz.x,sz.z)+1.5));const grid=new THREE.GridHelper(gs,gs*1,0x3a3f4a,0x555b68);grid.position.y=0;sc.add(grid);
  if(v.ref){const g=new THREE.Group(),m=new THREE.LineBasicMaterial({color:0xffd400});const cx=(a,b2,c,x,y,z)=>{const e=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(a/16,b2/16,c/16)),m);e.position.set(x/16,y/16,z/16);g.add(e);};
   cx(8,8,8,0,28,0);cx(8,12,4,0,18,0);cx(4,12,4,-6,18,0);cx(4,12,4,6,18,0);cx(4,12,4,-2,6,0);cx(4,12,4,2,6,0);g.position.x=bx.max.x+0.45;sc.add(g);bx.expandByObject(g);bx.getCenter(ct);bx.getSize(sz);}
  const yaw=v.yaw*Math.PI/180,pit=v.pitch*Math.PI/180,r=Math.max(sz.x,sz.y,sz.z)*0.5*Math.sqrt(3);const fov=26,d=r/Math.sin(fov*Math.PI/360)*1.02;
  const cam=new THREE.PerspectiveCamera(fov,W/H,0.01,500);cam.position.set(ct.x+d*Math.cos(pit)*Math.sin(yaw),ct.y+d*Math.sin(pit),ct.z+d*Math.cos(pit)*Math.cos(yaw));cam.lookAt(ct);
  R.setClearColor(v.fundo||0x8fa6c4,1);R.render(sc,cam);out.push(R.domElement.toDataURL('image/png'));disposeTree(b.body);}}
 finally{ENTLM.forEach(u=>u.value=lm<0?1:lm);R.dispose();}return out;})(__S__)"""

# frente do personagem = -z do modelo = +z no estúdio; yaw 0 = câmera de frente
VISTAS = [("frente", 0, 8, None), ("3/4 lado direito dele", -40, 22, None), ("lado esquerdo dele", 90, 5, None), ("3/4 costas", 140, 25, None),
          ("costas", 180, 8, None), ("de cima", 20, 62, None), ("de baixo", -25, -45, None), ("escala", -30, 12, "ref")]
POSE = {"head": [-15, 30, 0], "right_arm": [-110, 0, 0], "left_arm": [35, 0, 0], "right_leg": [30, 0, 0], "left_leg": [-30, 0, 0]}


def foto(d, saida, nome="modelo", textura=None):
    """renderiza o modelo com o PRÓPRIO código do estúdio (buildBBSBody) em 8 ângulos (+ pose de teste para personagem)
    e monta <saida>/<nome>-folha.png com a textura ampliada. Usa o servidor e o Chromium do quadros.py."""
    sys.path.insert(0, os.path.join(RAIZ, "script", "cenas"))
    import quadros
    from PIL import Image, ImageDraw
    M = json.loads(d["modelo"]) if isinstance(d["modelo"], str) else d["modelo"]
    tex = next((t["p"] for t in d["tex"] if t["n"] == textura), d["tex"][0]["p"])
    vistas = [{"nome": n, "yaw": y, "pitch": p, "ref": bool(r)} for n, y, p, r in VISTAS]
    if d.get("tipo") == "personagem":
        vistas += [{"nome": "pose de teste", "yaw": -35, "pitch": 12, "pose": POSE},
                   {"nome": "pose (lado)", "yaw": 90, "pitch": 8, "pose": POSE}]
    S = {"png": tex, "modelo": M, "w": 360, "h": 420, "vistas": vistas}
    t3, tz = quadros.libs()
    porta = quadros.servidor()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        pg = b.new_page(viewport={"width": 900, "height": 700})
        erros = []
        pg.on("pageerror", lambda e: erros.append(str(e)[:300]))
        pg.route("**/three.min.js", lambda r: r.fulfill(path=t3, content_type="text/javascript"))
        pg.route("**/jszip.min.js", lambda r: r.fulfill(path=tz, content_type="text/javascript"))
        pg.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
        pg.route("https://cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.goto(f"http://127.0.0.1:{porta}/?teste=1")
        pg.wait_for_function("window.EP_TESTE&&EP_TESTE.aval&&EP_TESTE.aval(\"typeof buildBBSBody==='function'&&typeof loadImg==='function'\")", timeout=120000)
        urls = pg.evaluate("c=>EP_TESTE.aval(c)", JS_FOTO.replace("__S__", json.dumps(S)))
        b.close()
    ims = [Image.open(io.BytesIO(base64.b64decode(u.split(",")[1]))).convert("RGB") for u in urls]
    os.makedirs(saida, exist_ok=True)
    timg = Image.open(io.BytesIO(base64.b64decode(tex))).convert("RGBA")
    k = max(1, min(8, 420 // max(timg.width, timg.height)))
    tq = Image.new("RGBA", (timg.width * k, timg.height * k), (0, 0, 0, 0))
    xad = Image.new("RGBA", tq.size)
    dx = ImageDraw.Draw(xad)
    for y in range(0, tq.height, 8):
        for x in range(0, tq.width, 8):
            dx.rectangle([x, y, x + 7, y + 7], fill=(70, 70, 76, 255) if (x // 8 + y // 8) % 2 else (90, 90, 98, 255))
    tq = Image.alpha_composite(xad, timg.resize(tq.size, Image.NEAREST)).convert("RGB")
    cels = list(zip([v["nome"] for v in vistas], ims)) + [("textura " + "x".join(map(str, timg.size)), tq)]
    cols, cw, ch = 4, 360, 440
    rows = (len(cels) + cols - 1) // cols
    folha = Image.new("RGB", (cols * cw, rows * ch + 30), (24, 26, 30))
    dr = ImageDraw.Draw(folha)
    dr.text((8, 8), f"{d.get('nome', nome)} - {d.get('tipo')}/{d.get('uso')} - renderizado pelo estudio (buildBBSBody)", fill=(240, 240, 240))
    for i, (n, im) in enumerate(cels):
        x, y = (i % cols) * cw, 30 + (i // cols) * ch
        folha.paste(im if im.width <= cw else im.resize((cw, int(im.height * cw / im.width)), Image.NEAREST), (x, y + 20))
        dr.text((x + 6, y + 4), n, fill=(255, 212, 0))
    fn = os.path.join(saida, f"{nome}-folha.png")
    folha.save(fn)
    for (n, im) in zip([v["nome"] for v in vistas], ims):
        im.save(os.path.join(saida, f"{nome}-{re.sub(r'[^a-z0-9]+', '-', n)}.png"))
    return fn, erros


# ---------------------------------------------------------------- ida e volta
def mesmo_modelo(a, b, tol=1e-4):
    """compara dois modelos do estúdio olhando a GEOMETRIA (grupos, pivôs, cubos) e os PIXELS que cada face mostra."""
    from PIL import Image
    difs = []
    Ma, Mb = [json.loads(x["modelo"]) if isinstance(x["modelo"], str) else x["modelo"] for x in (a, b)]
    ia, ib = [Image.open(io.BytesIO(base64.b64decode(x["tex"][0]["p"]))).convert("RGBA") for x in (a, b)]
    if set(Ma["groups"]) != set(Mb["groups"]):
        difs.append(f"grupos diferentes: {sorted(set(Ma['groups']) ^ set(Mb['groups']))}")
        return difs
    for gn, ga in Ma["groups"].items():
        gb = Mb["groups"][gn]
        for k in ("origin", "rotate"):
            va, vb = ga.get(k, [0, 0, 0]), gb.get(k, [0, 0, 0])
            if any(abs(x - y) > tol for x, y in zip(va, vb)):
                difs.append(f"{gn}.{k}: {va} ≠ {vb}")
        if ga.get("parent") != gb.get("parent"):
            difs.append(f"{gn}.parent: {ga.get('parent')} ≠ {gb.get('parent')}")
        ca, cb = ga.get("cubes", []), gb.get("cubes", [])
        if len(ca) != len(cb):
            difs.append(f"{gn}: {len(ca)} ≠ {len(cb)} cubos")
            continue
        for i, (x, y) in enumerate(zip(ca, cb)):
            for k in ("from", "size", "origin", "rotate"):
                va, vb = x.get(k, [0, 0, 0]), y.get(k, [0, 0, 0])
                if any(abs(p - q) > tol for p, q in zip(va, vb)):
                    difs.append(f"{gn}[{i}].{k}: {va} ≠ {vb}")
            if set(x.get("uvs", {})) != set(y.get("uvs", {})):
                difs.append(f"{gn}[{i}]: faces {sorted(x.get('uvs', {}))} ≠ {sorted(y.get('uvs', {}))}")
                continue
            for fn in x.get("uvs", {}):
                pa, pb = [_pix_face(im, M, c["uvs"][fn]) for im, M, c in ((ia, Ma, x), (ib, Mb, y))]
                if pa != pb:
                    difs.append(f"{gn}[{i}].{fn}: pixels diferentes")
    return difs


def _pix_face(im, M, uv):
    tw, th = M.get("texture", [im.width, im.height])
    kx, ky = im.width / tw, im.height / th
    x0, x1 = uv[0] * kx, uv[2] * kx
    y0, y1 = uv[1] * ky, uv[3] * ky
    # amostra a face numa grade fixa (o que aparece na tela), independente do tamanho da imagem
    n = 11  # pontos fora das bordas de pixel (0,37 em vez de 0,5), para não cair na divisa entre dois pixels
    out = []
    for j in range(n):
        for i in range(n):
            x = int(math.floor(x0 + (x1 - x0) * (i + 0.37) / n))
            y = int(math.floor(y0 + (y1 - y0) * (j + 0.37) / n))
            out.append(im.getpixel((min(max(x, 0), im.width - 1), min(max(y, 0), im.height - 1))))
    return out


# ---------------------------------------------------------------- linha de comando
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["conferir", "foto", "registrar", "exportar", "ida-e-volta"])
    ap.add_argument("alvo", help="id do banco (site/dados/modelos/<id>.json) ou caminho de um arquivo .json do estúdio")
    ap.add_argument("--saida")
    ap.add_argument("--bbmodel", action="store_true")
    ap.add_argument("--bbs", action="store_true")
    ap.add_argument("--pacote", action="store_true")
    ap.add_argument("--item", default="paper")
    ap.add_argument("--cmd", type=int, default=7001)
    ap.add_argument("--textura", help="foto: qual textura do modelo (nome); sem isso, a primeira")
    a = ap.parse_args()
    id_ = os.path.splitext(os.path.basename(a.alvo))[0]
    if a.acao == "registrar":
        return registrar(a.alvo)
    d, _ = ler(a.alvo)
    if a.acao == "conferir":
        av, num = conferir(d)
        print(json.dumps({"modelo": id_, "numeros": num, "avisos": av}, ensure_ascii=False, indent=1))
        sys.exit(1 if av else 0)
    if a.acao == "foto":
        fn, err = foto(d, a.saida or os.path.join("/tmp", "modelos-foto"), id_ + ("-" + a.textura if a.textura else ""), a.textura)
        print(json.dumps({"folha": fn, "erros_js": err[:5]}, ensure_ascii=False))
        return
    if a.acao == "ida-e-volta":
        bb = para_bbmodel(d)
        av = []
        M2, png = de_bbmodel(json.loads(json.dumps(bb)), av)
        d2 = dict(d, modelo=json.dumps(M2), tex=[{"n": d["tex"][0]["n"], "p": base64.b64encode(png).decode()}])
        difs = mesmo_modelo(d, d2)
        print(json.dumps({"modelo": id_, "igual": not difs, "diferencas": difs[:20], "avisos": av}, ensure_ascii=False, indent=1))
        sys.exit(1 if difs else 0)
    if a.acao == "exportar":
        if not a.saida:
            sys.exit("--saida pasta")
        os.makedirs(a.saida, exist_ok=True)
        tudo = not (a.bbmodel or a.bbs or a.pacote)
        res = {}
        if a.bbmodel or tudo:
            p = os.path.join(a.saida, id_ + ".bbmodel")
            json.dump(para_bbmodel(d, id_), open(p, "w", encoding="utf-8"), ensure_ascii=False)
            res["bbmodel"] = p
        if a.bbs or tudo:
            res["bbs"] = para_bbs(d, os.path.join(a.saida, "bbs", id_))
        if a.pacote or tudo:
            cmd, av = para_pacote(d, os.path.join(a.saida, "pacote-estudio"), id_, a.item, a.cmd)
            res["pacote"] = {"comando": cmd} if cmd else {"nao_deu": av}
        print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
