#!/usr/bin/env python3
"""Modelo-fonte: "Golenzinho de Musgo" (personagem animável), feito do zero pela skill modelar-3d.

  python3 modelador/modelos-fonte/golem_musgo.py [--substituir]

PLANO (passo 1 da skill)
  Ideia: um golenzinho de pedra coberta de musgo, forte e bobo. Original (não é mob do jogo).
  Silhueta: ombros largos e braços compridos e grossos (lê "forte"), pernas curtas (lê "pesado/fofo"),
  cabeça pequena para o corpo e um nariz de 2 px saindo da cara (quebra o quadrado e dá personalidade de lado).
  Proporção (pixels; o jogador tem 32 de altura): 24 px de altura = 3/4 do jogador.
    pernas 4×7×4 (y 0–7) · tronco 10×10×6 (y 7–17) · cabeça 8×7×7 (y 17–24) · braços 4×13×4 (pendurados até y 4)
  Cubos: 7 (cabeça, nariz, tronco, 2 braços, 2 pernas). Sem cubos menores que 1 px, todos com tamanho inteiro.
  Partes que mexem (ossos com os nomes que o estúdio anima):
    head (pivô no pescoço, y=17) · right_arm/left_arm (pivô no ombro, y=16) · right_leg/left_leg (pivô no quadril, y=7)
    O lado DIREITO do personagem fica em +x (ele olha para -z).
  Textura: 64×64, caixa UV (box UV), 1 px de textura = 1 px de modelo.
    Pedra em rampa de 5 cores com hue shifting (sombra puxada para azul-roxo, luz para amarelo);
    musgo em rampa de 4 verdes por cima (topo e ombros, escorrendo nos lados); olhos acesos cor de âmbar.
    Topo e frente mais claros que costas e baixo (regra das entidades); luz do alto à esquerda.
"""
import argparse, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ferramentas"))
import modelos3d as M3  # noqa: E402

ID = "golenzinho-musgo"

m = M3.Modelo(64, 64)
m.grupo("body", [0, 7, 0])
m.grupo("head", [0, 17, 0], parent="body")
m.grupo("right_arm", [6.5, 16, 0], parent="body")
m.grupo("left_arm", [-6.5, 16, 0], parent="body")
m.grupo("right_leg", [2.5, 7, 0])
m.grupo("left_leg", [-2.5, 7, 0])

C = {}
C["cabeca"] = m.cubo("head", [-4, 17, -3.5], [8, 7, 7], uv=(0, 0))          # caixa 30×14
C["nariz"] = m.cubo("head", [-1, 18, -5.5], [2, 3, 2], uv=(30, 0))          # caixa 8×5
C["tronco"] = m.cubo("body", [-5, 7, -3], [10, 10, 6], uv=(0, 14))          # caixa 32×16
C["braco_d"] = m.cubo("right_arm", [5, 4, -2], [4, 13, 4], uv=(32, 14))     # caixa 16×17
C["braco_e"] = m.cubo("left_arm", [-9, 4, -2], [4, 13, 4], uv=(48, 14))     # caixa 16×17
C["perna_d"] = m.cubo("right_leg", [0.5, 0, -2], [4, 7, 4], uv=(0, 30))     # caixa 16×11
C["perna_e"] = m.cubo("left_leg", [-4.5, 0, -2], [4, 7, 4], uv=(16, 30))    # caixa 16×11

PEDRA = M3.rampa("#7d7f86", 5, 0.11, 0.035, 0.03)   # 0 sombra funda … 4 realce
MUSGO = M3.rampa("#4f8a3a", 5, 0.10, 0.04, 0.0)
AMBAR = M3.rampa("#f2b134", 3, 0.16)
ESCURO = (38, 36, 50, 255)


def pedra(semente, nivel, i, j):
    """pedra em BLOCOS de 2×2 (não ruído pixel a pixel): cada bloquinho sobe ou desce um degrau da rampa."""
    r = M3.ruido(i // 2 + (j // 2) * 7, j // 2, semente)
    k = nivel + (1 if r > 0.78 else -1 if r < 0.2 else 0)
    if M3.ruido(i, j, semente + 9) > 0.93 and k > 0:  # rachadura: 1 px mais escuro, poucos
        k -= 1
    return PEDRA[max(0, min(4, k))]


def com_musgo(semente, nivel, alto, i, j, w, h):
    """musgo na faixa de cima da face (alto px), escorrendo irregular; o resto é pedra."""
    escorre = alto + int(M3.ruido(i, 3, semente) * 3) - (1 if i % 3 == 0 else 0)
    if j < escorre:
        k = nivel + (1 if j == 0 and nivel < 3 else 0) - (1 if j == escorre - 1 else 0)
        return MUSGO[max(0, min(4, k))]
    return pedra(semente, nivel, i, j)


def pinta():
    T = M3.Textura(64, 64)
    lado = M3.sombra_por_face
    for nome, c in C.items():
        sem = hash(nome) % 97
        for f in M3.FACES:
            base = 2 + lado(f)
            if f == "top":
                T.face(c, f, lambda i, j, w, h, b=base, s=sem: MUSGO[b + (1 if (i + j) % 5 == 0 else 0) - (1 if M3.ruido(i, j, s) > 0.8 else 0)])
            elif nome in ("cabeca", "braco_d", "braco_e", "tronco") and f != "bottom":
                alto = 2 if nome != "tronco" else 1
                T.face(c, f, lambda i, j, w, h, b=base, s=sem, a=alto: com_musgo(s, b, a, i, j, w, h))
            else:
                T.face(c, f, lambda i, j, w, h, b=base, s=sem: pedra(s, b, i, j))
    # a cara (frente da cabeça, 8×7): sobrancelha pesada, olhos de âmbar acesos, boca de fresta
    def cara(i, j, w, h):
        if j == 2 and 1 <= i <= 6:
            return PEDRA[0]                       # sobrancelha (sombra embaixo do musgo)
        if j == 3 and i in (1, 2, 5, 6):
            return AMBAR[2] if i in (1, 5) else AMBAR[1]   # olhos 2×1, brilho no pixel de cima-esquerda
        if j == 4 and i in (1, 2, 5, 6):
            return AMBAR[0]
        if j == 6 and 2 <= i <= 5:
            return ESCURO                         # boca
        return None
    T.face(C["cabeca"], "front", cara)
    # nariz: pedra um degrau mais clara na frente (pega luz), base escura
    T.face(C["nariz"], "front", lambda i, j, w, h: PEDRA[3] if j < 2 else PEDRA[2])
    # tronco: uma pedra-coração em relevo pintado no peito (4×3), com borda escura embaixo e à direita
    def peito(i, j, w, h):
        if 3 <= i <= 6 and 4 <= j <= 6:
            if j == 6 or i == 6:
                return PEDRA[1]
            return MUSGO[3] if (i, j) == (4, 4) else MUSGO[2]
        return None
    T.face(C["tronco"], "front", peito)
    # mãos e pés: as 2 linhas de baixo mais escuras (peso no chão, contato)
    for n in ("braco_d", "braco_e", "perna_d", "perna_e"):
        for f in ("front", "back", "left", "right"):
            T.face(C[n], f, lambda i, j, w, h, f=f: PEDRA[max(0, 1 + M3.sombra_por_face(f))] if j >= h - 2 and (j == h - 1 or i % 2) else None)
    return T


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--substituir", action="store_true")
    a = ap.parse_args()
    T = pinta()
    d = M3.montar_arquivo(m.json(), "Golenzinho de Musgo", "estudio", "personagem", "corpo", [("pedra", T.png())])
    print(M3.salvar(ID, d, a.substituir))
    M3.registrar(ID)
