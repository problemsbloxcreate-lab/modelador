// Receita de exemplo para ferramentas/bbsemtela.py: "Cogumelinho", personagem pequeno (nível Médio) com 2 animações.
// Rode:  python3 modelador/ferramentas/bbsemtela.py modelador/modelos-fonte/exemplo-receita.js --saida /tmp/cogumelo --animacoes
// Etapas: 1 silhueta (ossos + cubos) · 2 molde de textura · 3 pintura · 4 animações.

BBA.novo({ nome: 'cogumelinho', textura: [64, 64] });

// ---- 1. silhueta: ossos com os nomes que o estúdio anima (pivô nas juntas) ----
BBA.osso('body', [0, 0, 0]);
BBA.osso('head', [0, 8, 0], { pai: 'body' });            // pivô no pescoço
BBA.osso('right_arm', [4, 11, 0], { pai: 'body' });       // direito do personagem = +x (ele olha para -z)
BBA.osso('left_arm', [-4, 11, 0], { pai: 'body' });
BBA.osso('right_leg', [1.5, 4, 0], { pai: 'body' });
BBA.osso('left_leg', [-1.5, 4, 0], { pai: 'body' });

BBA.caixa('chapeu', [0, 16, 0], [14, 6, 14], { osso: 'head' });          // chapéu largo = silhueta reconhecível de longe
BBA.caixa('chapeu_topo', [0, 20, 0], [8, 2, 8], { osso: 'head' });
BBA.caixa('rosto', [0, 10.5, 0], [6, 5, 6], { osso: 'head' });
BBA.caixa('tronco', [0, 6, 0], [6, 4, 4], { osso: 'body' });
BBA.caixa('braco_direito', [4, 8.5, 0], [2, 5, 2], { osso: 'right_arm' });
BBA.espelhar('braco_direito', { nome: 'braco_esquerdo', osso: 'left_arm' });
BBA.caixa('perna_direita', [1.5, 2, 0], [2, 4, 2], { osso: 'right_leg' });
BBA.espelhar('perna_direita', { nome: 'perna_esquerda', osso: 'left_leg' });

// ---- 2. molde: o Blockbench arruma o UV de todas as faces, sem esticar ----
await BBA.molde({ resolucao: 16 });

// ---- 3. pintura: cor base com a luz do jogo + grão + detalhes desenhados na face ----
BBA.cor('chapeu', '#d8322f'); BBA.cor('chapeu_topo', '#d8322f');
BBA.pinta('chapeu', ['cima', 'norte', 'sul', 'leste', 'oeste'], (ctx, r, lado) => {   // bolinhas brancas do cogumelo
  const pts = [[0.2, 0.25], [0.65, 0.4], [0.35, 0.7], [0.8, 0.8]];
  for (const [u, v] of pts) { ctx.fillStyle = BBA.tom('#f2ede4', lado === 'cima' ? 1.1 : 0.95); ctx.fillRect(Math.floor(r.x + u * r.w), Math.floor(r.y + v * r.h), 2, 2); }
});
BBA.cor('chapeu', '#f0e6d2', { lados: ['baixo'] });                 // lamelas embaixo do chapéu
BBA.cor('rosto', '#f2dcb8'); BBA.cor('tronco', '#e9d3ad');
BBA.ruido('tronco', ['#d9c19a', '#f4e4c6'], { semente: 3, chance: 0.2 });
BBA.pinta('rosto', 'norte', (ctx, r) => {                            // olhos e boca na frente (norte)
  ctx.fillStyle = '#2b1d14'; ctx.fillRect(r.x + 1, r.y + 1, 1, 2); ctx.fillRect(r.x + r.w - 2, r.y + 1, 1, 2);
  ctx.fillStyle = '#b5523b'; ctx.fillRect(r.x + 2, r.y + r.h - 2, r.w - 4, 1);
});
for (const c of ['braco_direito', 'braco_esquerdo']) BBA.cor(c, '#e9d3ad');
for (const c of ['perna_direita', 'perna_esquerda']) BBA.cor(c, '#7a5537');

// ---- 4. animações: parado (respira, chapéu balança) e andar (ciclo de 0,8 s) ----
BBA.animacao('parado', { dur: 2, loop: 'loop' });
BBA.chave('parado', 'head', 'rotation', 0, [0, 0, 0]);
BBA.chave('parado', 'head', 'rotation', 1, [0, 0, 4]);
BBA.chave('parado', 'head', 'rotation', 2, [0, 0, 0]);
BBA.chave('parado', 'body', 'position', 0, [0, 0, 0]);
BBA.chave('parado', 'body', 'position', 1, [0, -0.4, 0]);
BBA.chave('parado', 'body', 'position', 2, [0, 0, 0]);

BBA.animacao('andar', { dur: 0.8, loop: 'loop' });
for (const [t, s] of [[0, 1], [0.4, -1], [0.8, 1]]) {
  BBA.chave('andar', 'right_leg', 'rotation', t, [35 * s, 0, 0]);
  BBA.chave('andar', 'left_leg', 'rotation', t, [-35 * s, 0, 0]);
  BBA.chave('andar', 'right_arm', 'rotation', t, [-30 * s, 0, 0]);
  BBA.chave('andar', 'left_arm', 'rotation', t, [30 * s, 0, 0]);
}
for (const t of [0, 0.4, 0.8]) BBA.chave('andar', 'body', 'position', t, [0, 0, 0]);
for (const t of [0.2, 0.6]) BBA.chave('andar', 'body', 'position', t, [0, 0.8, 0]);   // quique a cada passo
BBA.chave('andar', 'head', 'rotation', 0, [0, 0, 3]);
BBA.chave('andar', 'head', 'rotation', 0.4, [0, 0, -3]);
BBA.chave('andar', 'head', 'rotation', 0.8, [0, 0, 3]);
