#!/usr/bin/env python3
"""Converte um modelo do Blockbench (.bbmodel) para o banco do Estúdio Problems (site/dados/modelos/<id>.json).

  python3 modelador/ferramentas/bbmodel-para-estudio.py arquivo.bbmodel --id meu-modelo --nome "Meu modelo" \
      --pack livres --tipo objeto --uso mao [--escala-mao 1] [--registrar] [--foto pasta] [--substituir]

O que ele faz (detalhes em modelador/ferramentas/modelos3d.py, função de_bbmodel):
  - grupos do Blockbench viram grupos do estúdio (mesmo nome, pivô = origin, rotação, pai); cubos soltos vão para "anchor";
  - todas as texturas viram UMA só (o estúdio e o BBS usam uma textura por modelo), recortando só o que as faces usam;
  - caixa UV (box UV) e UV por face funcionam; a rotação de UV de uma face já sai "pintada" girada;
  - malhas (mesh) ficam de fora com aviso (o estúdio só desenha cubos).
Para um personagem ser animado pelo estúdio, os grupos precisam se chamar head, right_arm, left_arm, right_leg, left_leg
(o direito do personagem em +x, a frente em -z / norte). Use --renomear velho=novo para acertar nomes.
Nunca sobrescreve um modelo que já existe no banco (a não ser com --substituir).
"""
import argparse, base64, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelos3d as M3  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bbmodel")
    ap.add_argument("--id", required=True, help="nome do arquivo no banco: minúsculas, números e hífen")
    ap.add_argument("--nome", required=True, help="nome que aparece no estúdio")
    ap.add_argument("--pack", default="livres")
    ap.add_argument("--tipo", choices=["personagem", "objeto"], default="objeto")
    ap.add_argument("--uso", choices=["corpo", "mao"], default="mao")
    ap.add_argument("--escala-mao", type=float, help="tamanho na mão (1 = como está; sem isso o estúdio encaixa sozinho)")
    ap.add_argument("--textura", default="textura", help="nome da textura no banco")
    ap.add_argument("--renomear", action="append", default=[], help="velho=novo (nome de grupo)")
    ap.add_argument("--tirar", action="append", default=[], help="grupo que não é desenho (ex.: hitbox) e sai do modelo")
    ap.add_argument("--registrar", action="store_true", help="já põe no _lista.json e no índice")
    ap.add_argument("--foto", help="pasta para a folha de conferência renderizada no estúdio")
    ap.add_argument("--substituir", action="store_true")
    a = ap.parse_args()
    with open(a.bbmodel, encoding="utf-8") as f:
        bb = json.load(f)
    av = []
    mod, png = M3.de_bbmodel(bb, av)
    for g in a.tirar:  # ex.: hitbox, mount, tag_name (pontos de outros mods que não são desenho)
        mod["groups"].pop(g, None)
        for x in mod["groups"].values():
            if x.get("parent") == g:
                x.pop("parent")
    for par in a.renomear:
        velho, novo = par.split("=", 1)
        if velho in mod["groups"]:
            mod["groups"][novo] = mod["groups"].pop(velho)
            for g in mod["groups"].values():
                if g.get("parent") == velho:
                    g["parent"] = novo
        else:
            av.append(f"--renomear: não achei o grupo {velho}")
    d = M3.montar_arquivo(mod, a.nome, a.pack, a.tipo, a.uso, [(a.textura, png)],
                          {"escala": a.escala_mao} if a.escala_mao else None)
    av2, num = M3.conferir(d)
    p = M3.salvar(a.id, d, a.substituir)
    out = {"arquivo": p, "numeros": num, "avisos_conversao": av, "avisos_regras": av2}
    if a.registrar:
        M3.registrar(a.id)
    if a.foto:
        fn, err = M3.foto(d, a.foto, a.id)
        out["folha"], out["erros_js"] = fn, err[:5]
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
