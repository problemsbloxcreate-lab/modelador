#!/usr/bin/env python3
"""Modelo-fonte: o livro "A Cor Escondida" do Problems (objeto de mão), feito do zero pela skill modelar-3d.

  python3 modelador/modelos-fonte/livro_cor_escondida.py [--substituir]

PLANO (passo 1 da skill)
  Referência: a capa do livro (já no banco, mochila-livro, arte do próprio canal).
  Silhueta: um bloco retangular em pé; o que diz "livro" de longe é a capa SOBRANDO 1 px em volta das folhas.
  Cubos: 3 (capa da frente 12×16×1, miolo de folhas 11×14×1, capa de trás 12×16×1). Nada menor que 1 px.
  Escala: um livro de verdade teria ~4×6 px na mão do boneco (ilegível). Objeto pequeno pode quebrar a escala
  para ser lido: 12×16 px (3/4 de bloco), igual ao livro que o Problems mostra para a câmera.
  Partes que mexem: nenhuma (um grupo só, "livro", pivô no centro da lombada de baixo).
  Textura: 64×64, caixa UV, 1 px de textura = 1 px de modelo. (Testei a capa de verdade em dobro de resolução:
  na conferência ficou borrada e fora do estilo; quem quiser a capa fiel usa o modelo "mochila-livro".)
"""
import argparse, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ferramentas"))
import modelos3d as M3  # noqa: E402

ID = "livro-cor-escondida"

# ---------- geometria (frente = -z; lombada no lado direito do livro = +x)
m = M3.Modelo(64, 64)
m.grupo("livro", [0, 0, 0])
capa = m.cubo("livro", [-6, 0, -2], [12, 16, 1], uv=(0, 0))      # caixa 26×17 em (0,0)
miolo = m.cubo("livro", [-5, 1, -1], [11, 14, 1], uv=(0, 17))    # caixa 24×15 em (0,17)
fundo = m.cubo("livro", [-6, 0, 0], [12, 16, 1], uv=(26, 0))     # caixa 26×17 em (26,0)

# ---------- paleta restrita (rampas com hue shifting a partir do meio-tom)
AZUL = M3.rampa("#1d2b4f", 5, 0.07)         # capa: azul-noite
PAPEL = M3.rampa("#e9dfc4", 5, 0.06, 0.02)  # folhas
ROSA, CIANO = M3.rampa("#d9488c", 3, 0.12), M3.rampa("#4fb6d8", 3, 0.12)
VERDE, AZG = M3.rampa("#1f8d5f", 3), M3.rampa("#1c6aa2", 3)
PELE, CABELO = M3.rampa("#5a7fb0", 3, 0.14), M3.rampa("#b4405c", 3, 0.12)
BRANCO, AMARELO, PRETO = (240, 240, 236, 255), (232, 199, 90, 255), (18, 16, 26, 255)

# capa 12×16 desenhada à mão (linha de cima para baixo). Cada letra = uma cor da paleta acima.
# 1ª tentativa (planeta + prédios + 3 personagens em 12×16) virou borrão na conferência: detalhe demais para o tamanho.
# Regra da skill: se não cabe em 16 px, tire o detalhe. Ficou: logo, UM rosto grande (o Problems sorrindo), título.
CAPA = [
    "nnnnnnnnnnnn",
    "nCcCcCcCcCcn",  # logo PROBLEMS (faixa ciano com brilho)
    "nccccccccccn",
    "nnnnbgnnnnnn",  # o planetinha
    "nnnddddddnnn",  # cabelo escuro espetado
    "nnddddddddnn",
    "nndFffffFdnn",  # testa (realce no canto de cima, luz da esquerda)
    "nnfkmffmkfnn",  # olhos
    "nnffffffffnn",
    "nnfmmmmmmfnn",  # o sorriso grande
    "nnnfkkkkfnnn",
    "nnnnffffnhhn",  # pescoço e o cabelo vermelho da menina
    "nnnnnnnnhHhn",
    "pptpptpptppt",  # título A COR ESCONDIDA (rosa e ciano)
    "tptptptptptp",
    "nnnnnwwnnnnn",  # selo da editora
]
COR = {"k": PRETO, "n": AZUL[2], "c": CIANO[1], "C": CIANO[2], "b": AZG[2], "g": VERDE[2], "d": (34, 40, 78, 255),
       "w": AMARELO, "f": PELE[1], "F": PELE[2], "m": BRANCO, "h": CABELO[1], "H": CABELO[2], "p": ROSA[1], "t": CIANO[2]}


def pinta(T):
    # capa da frente: a arte. Bordas da capa (lados/topo/baixo) no azul, 1 degrau mais escuro nos lados (luz de cima/frente)
    T.face(capa, "front", lambda i, j, w, h: COR[CAPA[j][i]])
    for c in (capa, fundo):
        for f in ("top", "bottom", "left", "right"):
            T.face(c, f, lambda i, j, w, h, f=f: AZUL[2 + M3.sombra_por_face(f)])
    # contracapa: azul com linhas de texto e o código de barras
    def costas(i, j, w, h):
        if j in (3, 5, 7, 9) and 2 <= i <= 9 - (j % 3):
            return AZUL[3]
        if 12 <= j <= 13 and 7 <= i <= 10:
            return BRANCO if (i + j) % 2 else (200, 200, 196, 255)
        return AZUL[1]
    T.face(fundo, "back", costas)
    T.face(capa, "back", lambda i, j, w, h: AZUL[0])
    T.face(fundo, "front", lambda i, j, w, h: AZUL[0])
    # lombada (lado direito, +x): azul com o logo ciano no alto e o título rosa embaixo
    T.face(miolo, "right", lambda i, j, w, h: CIANO[1] if j < 3 else ROSA[1] if 9 <= j <= 11 else AZUL[1])
    T.face(capa, "right", lambda i, j, w, h: AZUL[1])
    T.face(fundo, "right", lambda i, j, w, h: AZUL[1])
    # folhas: papel com riscas finas (as páginas), mais escuro embaixo (sombra) e mais claro em cima
    T.face(miolo, "left", lambda i, j, w, h: PAPEL[1] if j % 2 else PAPEL[2])
    T.face(miolo, "top", lambda i, j, w, h: PAPEL[3] if i % 2 else PAPEL[2])
    T.face(miolo, "bottom", lambda i, j, w, h: PAPEL[0] if i % 2 else PAPEL[1])
    T.face(miolo, "front", lambda i, j, w, h: PAPEL[2])
    T.face(miolo, "back", lambda i, j, w, h: PAPEL[2])


def textura_pixel():
    T = M3.Textura(64, 64)
    pinta(T)
    return T


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--substituir", action="store_true")
    a = ap.parse_args()
    T = textura_pixel()
    d = M3.montar_arquivo(m.json(), "Livro A Cor Escondida (cubos)", "estudio", "objeto", "mao",
                          [("pixel", T.png())], {"escala": 0.75})
    print(M3.salvar(ID, d, a.substituir))
    M3.registrar(ID)
