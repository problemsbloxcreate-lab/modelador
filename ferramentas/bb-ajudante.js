/* bb-ajudante.js — comandos simples para o robô (e para o Claude no chat) modelarem, pintarem e animarem DENTRO do Blockbench
 * (a nossa cópia em blockbench/app), sem tela. Carregado por ferramentas/bbsemtela.py. Licença MIT.
 *
 * Tudo em PIXELS do Minecraft (1 bloco = 16). y para cima, chão em y = 0. A FRENTE do modelo olha para o NORTE (-z).
 * O lado DIREITO do personagem fica em +x (ele olha para -z). Pivô de cada osso na JUNTA: cabeça no pescoço (base da cabeça),
 * braço no ombro (topo do braço), perna no quadril (topo da perna). O conferidor (modelos3d.py conferir) avisa se errar.
 *
 *   BBA.novo({nome, textura:[64,64]})                         projeto novo (Generic Model), sem nada
 *   BBA.osso(nome, pivo:[x,y,z], {pai, rot:[x,y,z]})          grupo/osso (gira em volta do pivô)
 *   BBA.cubo(nome, de:[x,y,z], ate:[x,y,z], {osso, inflar, rot, pivo, espelhar})   cubo
 *   BBA.caixa(nome, centro:[x,y,z], tam:[w,h,d], {...})      cubo pelo centro e tamanho
 *   BBA.espelhar(nomeCubo, {eixo:'x'})                         cópia espelhada (ex.: braço esquerdo)
 *   BBA.molde({resolucao:16})                                  cria a textura-molde e arruma o UV de todos os cubos (sem esticar)
 *   BBA.face(cubo, lado) → {x,y,w,h}                           retângulo da face na textura (lado: norte, sul, leste, oeste, cima, baixo)
 *   BBA.pinta(cubo, lado|'todas', (ctx,r,lado)=>{...})         desenha na face com o canvas 2D (r = retângulo da face)
 *   BBA.cor(cubo, '#rrggbb', {sombra:true})                   pinta o cubo inteiro com a luz do jogo (topo claro, base escura)
 *   BBA.ruido(cubo, cores:[...], {lados, semente, chance})    "grão" de pixel com uma paleta curta (pedra, terra, tecido)
 *   BBA.animacao(nome, {dur, loop:'loop'|'once'|'hold'})      animação nova
 *   BBA.chave(anim, osso, canal, tempo, [x,y,z], {interp})    quadro-chave (canal: rotation | position | scale; interp: linear | catmullrom | bezier | step)
 *   BBA.info()                                                 resumo: cubos, ossos, textura, animações
 *   BBA.salvar() → texto do .bbmodel
 */
(function () {
	'use strict';
	const LADO = { norte: 'north', sul: 'south', leste: 'east', oeste: 'west', cima: 'up', baixo: 'down',
		frente: 'north', costas: 'south', direita: 'west', esquerda: 'east', north: 'north', south: 'south', east: 'east', west: 'west', up: 'up', down: 'down' };
	const LADOS = ['north', 'south', 'east', 'west', 'up', 'down'];
	const acha = (Cls, nome) => (typeof nome === 'object' && nome) ? nome : Cls.all.find(x => x.name === nome);
	let tex = null;

	function rng(seed) { let s = (seed >>> 0) || 1; return () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return ((s >>> 0) % 100000) / 100000; }; }
	function hex2rgb(h) { const n = parseInt(String(h).replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
	function rgb2hex(r, g, b) { return '#' + [r, g, b].map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join(''); }
	/* luz de entidade do jogo + "hue shift": sombra puxa para azul/roxo, luz para amarelo (guia de estilo do Blockbench) */
	function tom(hex, k) {
		const [r, g, b] = hex2rgb(hex);
		if (k >= 1) return rgb2hex(r + (255 - r) * (k - 1) * 0.9 + 6 * (k - 1), g + (255 - g) * (k - 1) * 0.85, b + (255 - b) * (k - 1) * 0.6);
		return rgb2hex(r * k - 4 * (1 - k), g * k, b * k + 10 * (1 - k));
	}
	const LUZ = { up: 1.18, north: 1.0, east: 0.9, west: 0.9, south: 0.82, down: 0.68 };

	const BBA = {
		novo(o) {
			o = o || {};
			newProject(Formats.free);
			Project.name = o.nome || 'modelo';
			const [w, h] = o.textura || [64, 64];
			Project.texture_width = w; Project.texture_height = h;
			Project.box_uv = false;
			tex = null;
			return BBA;
		},
		osso(nome, pivo, o) {
			o = o || {};
			const g = new Group({ name: nome, origin: pivo || [0, 0, 0], rotation: o.rot || [0, 0, 0] });
			const pai = o.pai ? acha(Group, o.pai) : null;
			if (o.pai && !pai) throw new Error('osso pai não existe: ' + o.pai);
			if (pai) g.addTo(pai); g.init();
			return g;
		},
		cubo(nome, de, ate, o) {
			o = o || {};
			const c = new Cube({ name: nome, from: de, to: ate, inflate: o.inflar || 0, rotation: o.rot || [0, 0, 0],
				origin: o.pivo || [(de[0] + ate[0]) / 2, (de[1] + ate[1]) / 2, (de[2] + ate[2]) / 2], box_uv: false });
			const g = o.osso ? acha(Group, o.osso) : null;
			if (o.osso && !g) throw new Error('osso não existe: ' + o.osso);
			if (g) c.addTo(g); c.init();
			if (tex) c.applyTexture(tex, true);
			return c;
		},
		caixa(nome, centro, tam, o) {
			const de = centro.map((v, i) => v - tam[i] / 2), ate = centro.map((v, i) => v + tam[i] / 2);
			return BBA.cubo(nome, de, ate, o);
		},
		espelhar(nome, o) {
			o = o || {}; const c = acha(Cube, nome); if (!c) throw new Error('cubo não existe: ' + nome);
			const novo = o.nome || nome.replace(/direit[oa]|_r\b|right/gi, m => ({ direito: 'esquerdo', direita: 'esquerda', _r: '_l', right: 'left' }[m.toLowerCase()] || m + '_esp'));
			const de = [-c.to[0], c.from[1], c.from[2]], ate = [-c.from[0], c.to[1], c.to[2]];
			const pai = c.parent && c.parent !== 'root' ? c.parent : null;
			let osso = pai;
			if (o.osso) osso = acha(Group, o.osso);
			return BBA.cubo(novo, de, ate, { osso, inflar: c.inflate, rot: [c.rotation[0], -c.rotation[1], -c.rotation[2]], pivo: [-c.origin[0], c.origin[1], c.origin[2]] });
		},
		/* textura-molde do próprio Blockbench: arruma o UV de TODAS as faces sem esticar (1 px de textura = 1 px de modelo) */
		async molde(o) {
			o = o || {};
			Outliner.selected.empty(); Cube.all.forEach(c => Outliner.selected.push(c));
			let t = null;
			await TextureGenerator.generateTemplate({ type: 'template', resolution: o.resolucao || 16, rearrange_uv: true, double_use: false, padding: !!o.margem,
				box_uv: false, color: null, particle: false, name: o.nome || 'textura', power: true },
				(url) => { t = new Texture({ name: o.nome || 'textura', mode: 'bitmap', keep_size: true }).fromDataURL(url).add(false); return t; });
			for (let n = 0; n < 200 && !(t && t.width && t.img && t.img.complete); n++) await new Promise(r => setTimeout(r, 30));
			if (!t || !t.width) throw new Error('o molde de textura não terminou');
			tex = t; Cube.all.forEach(c => c.applyTexture(tex, true)); Canvas.updateAll();
			return { largura: t.width, altura: t.height };
		},
		usarTextura(nome) { tex = acha(Texture, nome) || Texture.all[0] || null; return tex; },
		face(cubo, lado) {
			const c = acha(Cube, cubo); if (!c) throw new Error('cubo não existe: ' + cubo);
			const f = c.faces[LADO[lado] || lado]; if (!f) throw new Error('lado não existe: ' + lado);
			const t = tex || Texture.all[0]; if (!t) throw new Error('sem textura: use await BBA.molde()'); const kx = t.width / Project.texture_width, ky = t.height / Project.texture_height;
			const x0 = Math.min(f.uv[0], f.uv[2]) * kx, x1 = Math.max(f.uv[0], f.uv[2]) * kx, y0 = Math.min(f.uv[1], f.uv[3]) * ky, y1 = Math.max(f.uv[1], f.uv[3]) * ky;
			return { x: Math.round(x0), y: Math.round(y0), w: Math.round(x1 - x0), h: Math.round(y1 - y0), espelhoX: f.uv[0] > f.uv[2], espelhoY: f.uv[1] > f.uv[3], rot: f.rotation || 0 };
		},
		pinta(cubo, lado, fn) {
			const t = tex || Texture.all[0]; if (!t) throw new Error('crie a textura com BBA.molde() antes de pintar');
			const lados = lado === 'todas' ? LADOS : [].concat(lado);
			t.edit((canvas) => {
				const ctx = canvas.getContext('2d');
				for (const l of lados) {
					const r = BBA.face(cubo, l); if (!r.w || !r.h) continue;
					ctx.save(); ctx.beginPath(); ctx.rect(r.x, r.y, r.w, r.h); ctx.clip(); ctx.imageSmoothingEnabled = false;
					fn(ctx, r, Object.keys(LADO).find(k => LADO[k] === (LADO[l] || l) && /^[a-z]+$/.test(k) && k.length > 4) || l);
					ctx.restore();
				}
			}, { no_undo: true });
			return BBA;
		},
		cor(cubo, hex, o) {
			o = o || {};
			return BBA.pinta(cubo, o.lados || 'todas', (ctx, r, l) => { ctx.fillStyle = o.sombra === false ? hex : tom(hex, LUZ[LADO[l] || l] || 1); ctx.fillRect(r.x, r.y, r.w, r.h); });
		},
		ruido(cubo, cores, o) {
			o = o || {}; const rnd = rng(o.semente || 7), chance = o.chance == null ? 0.35 : o.chance;
			return BBA.pinta(cubo, o.lados || 'todas', (ctx, r, l) => {
				for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) {
					if (rnd() > chance) continue;
					const c = cores[Math.floor(rnd() * cores.length)];
					ctx.fillStyle = o.sombra === false ? c : tom(c, LUZ[LADO[l] || l] || 1); ctx.fillRect(x, y, 1, 1);
				}
			});
		},
		tom,
		animacao(nome, o) {
			o = o || {};
			const a = new Animation({ name: nome, length: o.dur || 1, loop: o.loop || 'loop', snapping: 24 }).add(true);
			return a;
		},
		chave(anim, osso, canal, tempo, xyz, o) {
			o = o || {};
			const a = acha(Animation, anim); if (!a) throw new Error('animação não existe: ' + anim);
			const g = acha(Group, osso); if (!g) throw new Error('osso não existe: ' + osso);
			const ba = a.getBoneAnimator(g);
			ba.addKeyframe({ channel: canal, time: tempo, interpolation: o.interp || 'catmullrom', data_points: [{ x: xyz[0], y: xyz[1], z: xyz[2] }] });
			return BBA;
		},
		info() {
			return {
				cubos: Cube.all.length, ossos: Group.all.map(g => g.name), textura: Texture.all.map(t => t.name + ' ' + t.width + '×' + t.height),
				animacoes: Animation.all.map(a => ({ nome: a.name, dur: a.length, loop: a.loop, ossos: Object.keys(a.animators).length })),
				tamanho: (() => { const b = new THREE.Box3(); Cube.all.forEach(c => { b.expandByPoint(new THREE.Vector3(...c.from)); b.expandByPoint(new THREE.Vector3(...c.to)); }); const s = b.getSize(new THREE.Vector3()); return [s.x, s.y, s.z].map(v => Math.round(v * 10) / 10); })(),
			};
		},
		salvar() { return Codecs.project.compile({ raw: false }); },
	};
	window.BBA = BBA;
})();
