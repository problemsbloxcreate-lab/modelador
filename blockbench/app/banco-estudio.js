/* Banco do Estúdio — plugin do Blockbench embutido no Modelador (Estúdio Problems).
 * Licença: MIT (plugins do Blockbench podem ter licença própria; o Blockbench em si é GPL-3.0).
 *
 * O que faz:
 *  - menu "Banco do Estúdio" na barra do Blockbench: "Abrir do banco…" e "Salvar no banco";
 *  - abre direto um modelo quando a página vem com ?banco=<id> (botão "Editar no Blockbench" do Modelador);
 *  - "Salvar no banco" manda o .bbmodel para o servidor da equipe (Worker de sons, senha da equipe) e a Action
 *    salvar-modelo.yml do estúdio converte para o banco, tira as fotos e publica. Não usa o limite do Claude.
 * Os modelos ficam em ../../dados/modelos-export/<id>.bbmodel (gerados a partir do banco) e o índice em ../../dados/modelosmeta/indice.json.
 */
(function () {
	'use strict';
	const DADOS = new URL('../../dados/', location.href).href;
	const senha = () => { try { return localStorage.getItem('estudio.senhaSons') || ''; } catch (e) { return ''; } };
	let URLW = '', INDICE = null;
	const msg = (t, ms) => { try { Blockbench.showQuickMessage(t, ms || 2500); } catch (e) { console.log(t); } };
	const caixa = (titulo, texto) => { try { Blockbench.showMessageBox({ title: titulo, message: texto }); } catch (e) { alert(texto); } };
	const slug = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60);

	async function urlEquipe() {
		if (URLW) return URLW;
		try { const r = await fetch(DADOS + 'sons-url.json', { cache: 'no-store' }); if (r.ok) URLW = String((await r.json()).url || '').replace(/\/$/, ''); } catch (e) { }
		return URLW;
	}
	async function indice() {
		if (INDICE) return INDICE;
		try { const r = await fetch(DADOS + 'modelosmeta/indice.json', { cache: 'no-store' }); INDICE = r.ok ? ((await r.json()).itens || []) : []; } catch (e) { INDICE = []; }
		return INDICE;
	}

	async function abrirDoBanco(id) {
		const r = await fetch(DADOS + 'modelos-export/' + encodeURIComponent(id) + '.bbmodel', { cache: 'no-store' });
		if (!r.ok) { caixa('Banco do Estúdio', 'Não achei o arquivo do Blockbench do modelo "' + id + '". Modelos novos do robô já vêm com ele.'); return; }
		const txt = await r.text();
		loadModelFile({ path: id + '.bbmodel', name: id + '.bbmodel', content: txt });
		const it = (await indice()).find(x => x.id === id) || {};
		setTimeout(() => {
			if (!window.Project) return;
			Project.banco = { id, nome: it.nome || id, pack: it.pack || 'estudio', tipo: it.tipo || 'objeto', uso: it.uso || 'corpo', variacoes: (it.tex || []).length };
			if (Project.banco.variacoes > 1) msg('Este modelo tem ' + Project.banco.variacoes + ' texturas no banco; aqui você edita a principal.', 5000);
			else msg('Aberto do banco: ' + Project.banco.nome);
		}, 400);
	}

	async function dialogoAbrir() {
		const itens = (await indice()).slice().sort((a, b) => String(a.nome).localeCompare(String(b.nome), 'pt'));
		if (!itens.length) { caixa('Banco do Estúdio', 'Não consegui ler o banco de modelos.'); return; }
		const op = {};
		itens.forEach(x => { op[x.id] = x.nome + '  ·  ' + (x.pack || 'outros'); });
		new Dialog({
			id: 'banco_estudio_abrir', title: 'Abrir do banco do Estúdio', width: 460,
			form: { modelo: { label: 'Modelo', type: 'select', options: op, value: itens[0].id } },
			onConfirm(r) { abrirDoBanco(r.modelo); },
		}).show();
	}

	async function salvarNoBanco() {
		if (!window.Project) { caixa('Banco do Estúdio', 'Abra ou crie um modelo primeiro.'); return; }
		const w = await urlEquipe();
		if (!w) { caixa('Banco do Estúdio', 'O servidor da equipe não está ligado neste site.'); return; }
		const b = Project.banco || {};
		const temOssos = !!(window.Group && Group.all && Group.all.some(g => ['head', 'right_arm', 'left_arm', 'right_leg', 'left_leg'].includes(g.name)));
		new Dialog({
			id: 'banco_estudio_salvar', title: 'Salvar no banco do Estúdio', width: 500,
			form: {
				info: { type: 'info', text: b.id ? 'Vai SUBSTITUIR o modelo "' + b.nome + '" no banco (fica uma cópia da versão antiga no histórico do GitHub).' : 'Modelo novo no banco.' },
				nome: { label: 'Nome', type: 'text', value: b.nome || Project.name || '' },
				pack: { label: 'Pack', type: 'text', value: b.pack || 'estudio' },
				tipo: { label: 'O que é', type: 'select', value: b.tipo === 'personagem' || (!b.id && temOssos) ? 'personagem' : (b.uso === 'mao' ? 'mao' : 'objeto'), options: { personagem: 'Personagem (anima cabeça, braços e pernas)', objeto: 'Objeto / cenário', mao: 'Item de mão' } },
				por: { label: 'Quem está salvando', type: 'text', value: (() => { try { return localStorage.getItem('modelador.por') || ''; } catch (e) { return ''; } })() },
				senha: senha() ? { type: 'info', text: '🔒 Senha da equipe: já está neste navegador.' } : { label: 'Senha da equipe', type: 'password', value: '' },
			},
			async onConfirm(r) {
				if (r.senha) { try { localStorage.setItem('estudio.senhaSons', r.senha); } catch (e) { } }
				if (!senha()) { caixa('Banco do Estúdio', 'Falta a senha da equipe.'); return; }
				const nome = String(r.nome || '').trim(); if (!nome) { caixa('Banco do Estúdio', 'Dê um nome ao modelo.'); return; }
				try { localStorage.setItem('modelador.por', r.por || ''); } catch (e) { }
				let id = b.id || slug(nome);
				if (!b.id && (await indice()).some(x => x.id === id)) id = id + '-' + Date.now().toString(36).slice(-4);
				let bb;
				try { bb = Codecs.project.compile({ raw: true }); } catch (e) { caixa('Banco do Estúdio', 'Não consegui ler o modelo: ' + e.message); return; }
				const corpo = JSON.stringify({ nome, pack: slug(r.pack) || 'estudio', tipo: r.tipo === 'personagem' ? 'personagem' : 'objeto', uso: r.tipo === 'mao' ? 'mao' : 'corpo', por: String(r.por || '').slice(0, 40), substituir: !!b.id, bbmodel: bb });
				if (corpo.length > 20 * 1048576) { caixa('Banco do Estúdio', 'O modelo ficou grande demais para mandar (mais de 20 MB).'); return; }
				msg('Mandando para o banco…', 4000);
				try {
					const resp = await fetch(w + '/modelo/salvar?id=' + encodeURIComponent(id), { method: 'PUT', headers: { 'x-senha': senha(), 'content-type': 'application/json' }, body: corpo });
					if (resp.status === 401) { try { localStorage.removeItem('estudio.senhaSons'); } catch (e) { } caixa('Banco do Estúdio', 'Senha da equipe errada. Tente de novo.'); return; }
					const j = await resp.json().catch(() => ({}));
					if (!resp.ok) { caixa('Banco do Estúdio', 'O servidor da equipe recusou: ' + (j.erro || resp.status)); return; }
					Project.banco = Object.assign({}, b, { id, nome, pack: slug(r.pack) || 'estudio' });
					Project.saved = true;
					caixa('Banco do Estúdio', j.disparado
						? 'Enviado! Em uns 3 minutos o modelo "' + nome + '" aparece no banco (o robô converte, tira as fotos e publica).'
						: 'Salvei no servidor da equipe, mas não consegui chamar a conversão agora (' + (j.robo || 'sem resposta') + '). Avise no chat.');
				} catch (e) { caixa('Banco do Estúdio', 'Não consegui falar com o servidor da equipe: ' + e.message); }
			},
		}).show();
	}

	function instala() {
		const abrir = new Action('banco_estudio_abrir', { name: 'Abrir do banco…', icon: 'folder_open', click: dialogoAbrir });
		const salvar = new Action('banco_estudio_salvar', { name: 'Salvar no banco', icon: 'cloud_upload', click: salvarNoBanco, condition: () => !!window.Project });
		const voltar = new Action('banco_estudio_voltar', { name: 'Voltar ao Modelador', icon: 'arrow_back', click: () => { location.href = '../'; } });
		const menu = new BarMenu('banco_estudio', [abrir, salvar, '_', voltar], { name: '🧊 Banco do Estúdio' });
		MenuBar.addMenu(menu, 'file');
		const id = Blockbench.queries && Blockbench.queries.banco;
		if (id && /^[a-z0-9-]{1,80}$/.test(id)) abrirDoBanco(id);
	}
	(function espera(n) {
		if (window.Blockbench && Blockbench.setup_successful && window.MenuBar && window.BarMenu && window.Action && window.Dialog) { try { instala(); } catch (e) { console.error('Banco do Estúdio', e); } return; }
		if (n < 400) setTimeout(() => espera(n + 1), 150);
	})(0);
})();
