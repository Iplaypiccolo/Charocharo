#!/usr/bin/env node
/*
 * 티라 비밀번호 요원 모드 (add_agent_tira.js) — v3(2026-10-21 수정본): 머리 박기·뽑기 없이 선 채로 선글라스, 발·꼬리 작은 반동
 * 사용법: node intro/tools/add_agent_tira.js <티라_요원모드_사선_경량자료(v3) 폴더>
 *
 * - 새 그림 없음(newProductionPNGCount 0). 이미 들어 있는 k_agentBody(사선 몸체)·k_agentGlasses·원본 발·꼬리를 해시로 확인해 그대로 씀.
 * - v2 의 머리 박기용 것을 지움: k_agentBuried·k_agentSnow 파츠와 모든 동작의 그 트랙, 다른 데서 안 쓰는 그 그림(t_agent_v2_buried·snow),
 *   k_agentBody 의 땅 clip, p.agent 의 bury·puffs(→ 재생기가 눈가루를 만들지 않음). p.agent 는 설정의 targetAgent 로 통째로 바꿈.
 * - 시간표(개별 콘티): 0 원래 정면 감은 눈(><) → 0.42 사선 몸체(몸체 자체 자세는 고정) → 0.8~1.18 선글라스 80 위에서 착(3도 기울었다 정돈)
 *   → 1.18~1.52 먼 발 한 번 작게 고쳐 딛기(x +12, y -8) → 1.3~1.88 꼬리 두 번 까딱(7도에서 줄어듦) → 잠깐 정지 → 2.05~2.21 반짝(재생기)
 *   → 2.4~3.65 바람(상위 sway 1.25도, 꼬리 0.16초 늦게 6도) → 4.6초마다 아주 약한 잔바람. ag_out 0.42초.
 *   발 접지: 두 발 윤곽(footHulls)의 가장 아랫점이 기본 자세 때와 같게 sway.y 보정(rig 배율로 나눔).
 * - 다시 돌려도 같은 결과(ag_ 동작만 다시 만듦).
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..', '..');
const SRC = process.argv[2];
if (!SRC || !fs.existsSync(path.join(SRC, '설정', '추가파츠.json'))) { console.error('사용법: node intro/tools/add_agent_tira.js <티라 요원모드 v3 자료 폴더>'); process.exit(1); }
const win = { document: { currentScript: null }, performance: { now: () => 0 } };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'charo-pet.js'), 'utf8'), { window: win, document: win.document, performance: win.performance });
const CP = win.CharoPet;
const CFG = JSON.parse(fs.readFileSync(path.join(SRC, '설정', '추가파츠.json'), 'utf8'));
if (CFG.character !== '티라' || CFG.version !== 3) throw new Error('티라 v3 자료가 아님');
const F = path.join(ROOT, CFG.projectFile), p = JSON.parse(fs.readFileSync(F, 'utf8')), part = id => CP.findPart(p, id);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v)), ease = v => { v = clamp(v); return v * v * (3 - 2 * v); };
const bump = (t, a, b) => (t > a && t < b) ? Math.sin((t - a) / (b - a) * Math.PI) : 0;
const TL = CFG.timeline;

// 0) 재사용 그림 확인
for (const r of CFG.reuses) {
  const pt = part(r.partId), v = pt && pt.images[r.imageIndex];
  if (!v || v.asset !== r.assetId) throw new Error(r.partId + ' 그림 ' + r.imageIndex + ' 이 ' + r.assetId + ' 가 아님(먼저 v2 를 넣어야 함)');
  if (sha(Buffer.from(p.assets[r.assetId].split(',')[1], 'base64')) !== r.sha256) throw new Error('그림이 자료와 다름 ' + r.assetId);
}
// 1) 머리 박기용 것 지우기
p.parts = p.parts.filter(x => !CFG.removeParts.includes(x.id));
for (const c of p.clips) for (const id of CFG.removeParts) delete c.tracks[id];
const used = new Set(); for (const x of p.parts) for (const v of x.images) used.add(v.asset);
for (const a of CFG.removeAssetsIfUnreferenced) if (!used.has(a)) delete p.assets[a];
for (const k of CFG.removeBodyProperties) delete part('k_agentBody')[k];
for (const [id, d] of Object.entries(CFG.parts)) {   // 파츠 부모·피벗·rest 가 설정과 같은지
  const x = part(id); for (const k of ['parent']) if (x[k] !== d[k]) throw new Error(id + ' ' + k + ' 다름');
  for (const k of ['x', 'y', 'rot', 'sx', 'sy']) if (Math.abs(x.rest[k] - d.rest[k]) > 1e-6 || (k in d.pivot && Math.abs(x.pivot[k] - d.pivot[k]) > 1e-6)) throw new Error(id + ' rest/pivot 다름');
}
p.clips = p.clips.filter(c => !c.id.startsWith('ag_'));
p.preview = (p.preview || []).filter(x => !x.clip.startsWith('ag_'));

// 2) 자세
const baseOff = CP.offsetsFrom(p, CP.clipPose(p, CP.findClip(p, p.baseClip), 0));
const hide = new Set(CFG.hideDuringAgent), SP = CFG.standingPose, H = CFG.footHulls;
function floorOf(f) { const W = CP.worldMatrices(p, f); let y = -Infinity; for (const id of Object.keys(H)) for (const q of H[id]) y = Math.max(y, CP.apply(W[id], q[0], q[1])[1]); return y; }
function base() { const f = CP.finalPose(p, baseOff, null); for (const x of p.parts) if (/^(m_|k_)/.test(x.id)) f[x.id].op = 0; return f; }
const target = floorOf(CP.finalPose(p, baseOff, null));
function ground(f) { for (let i = 0; i < 2; i++) { const ky = CP.worldMatrices(p, f).rig[3]; f.sway.y += (target - floorOf(f)) / ky; } }
const IN = CFG.engineIntegration.durations.in, HOLD = CFG.engineIntegration.durations.hold, OUT = CFG.engineIntegration.durations.out;
const W0 = TL.wind[0], W1 = TL.wind[1], D = TL.tailWindDelay, CALM = W1 + 0.2;
function wave(t, d) { return t < CALM ? bump(t, W0 + d, W1 + d) : 0.15 * Math.sin((t - CALM) * Math.PI * 2 / HOLD - d * 3); }
function front() { const f = base(); f.headImg.img = 1; for (const k of ['sign11B', 'sign11F', 'sign14', 'mask', 'fire']) f[k].op = 0; return f; }
function agent(t, out) {
  if (t < 0.42 && out == null) return front();
  const f = base();
  for (const id of hide) if (f[id]) f[id].op = 0;
  f.k_agentBody.op = 1; Object.keys(SP).forEach(id => Object.assign(f[id], SP[id]));
  const g = f.k_agentGlasses;
  if (out == null) {
    g.op = t < TL.glassesLand[0] ? 0 : 1; g.y -= (1 - ease((t - 0.8) / 0.38)) * 80; g.rot += 3 * (1 - ease((t - 1.0) / 0.18));
    const fr = bump(t, TL.tinyFootReset[0], TL.tinyFootReset[1]); f.footR.x += 12 * fr; f.footR.y -= 8 * fr;   // 먼 발 한 번
    if (t >= TL.twoTailFlicks[0] && t < TL.twoTailFlicks[1]) { const q = (t - TL.twoTailFlicks[0]) / (TL.twoTailFlicks[1] - TL.twoTailFlicks[0]); f.tail.rot += 7 * Math.sin(q * Math.PI * 4) * (1 - q); }   // 꼬리 두 번
  } else { g.y -= ease(out / 0.8) * 80; g.op = 1 - ease((out - 0.25) / 0.5); }
  const k = out == null ? 1 : 1 - ease(out), tt = out == null ? t : IN;
  f.sway.rot += 1.25 * wave(tt, 0) * k; f.tail.rot += 6 * wave(tt, D) * k;   // 바람은 상위 sway 에서만, 꼬리 늦게
  ground(f);
  return f;
}
const TOL = { x: 0.15, y: 0.15, rot: 0.1, sx: 0.003, sy: 0.003, op: 0.003 }, DEF = { x: 0, y: 0, rot: 0, sx: 1, sy: 1, op: 1 };
function thin(keys, tol) {
  if (keys.length <= 2) return keys;
  const keep = new Array(keys.length).fill(false); keep[0] = keep[keys.length - 1] = true;
  (function rec(a, b) { let w = -1, wi = -1; for (let i = a + 1; i < b; i++) { const u = (keys[i].t - keys[a].t) / (keys[b].t - keys[a].t), d = Math.abs(keys[i].v - (keys[a].v + (keys[b].v - keys[a].v) * u)); if (d > w) { w = d; wi = i; } } if (w > tol) { keep[wi] = true; rec(a, wi); rec(wi, b); } })(0, keys.length - 1);
  return keys.filter((k, i) => keep[i]);
}
function clip(id, name, dur, loop, fn) {
  const n = Math.round(dur * 120), fr = [];
  for (let i = 0; i <= n; i++) fr.push({ t: +(dur * i / n).toFixed(4), f: fn(dur * i / n) });
  const tracks = {};
  for (const x of p.parts) {
    const r = x.rest, tr = {};
    for (const k of Object.keys(TOL)) {
      const keys = fr.map(({ t, f }) => { const a = f[x.id][k]; return { t, v: +(k === 'sx' || k === 'sy' || k === 'op' ? (r[k] ? a / r[k] : 0) : a - r[k]).toFixed(4), e: 'linear' }; });
      const flat = keys.every(q => Math.abs(q.v - keys[0].v) < 1e-6);
      if (flat && Math.abs(keys[0].v - DEF[k]) < 1e-6 && !(/^(m_|k_)/.test(x.id) && k === 'op')) continue;
      tr[k] = flat ? [keys[0]] : thin(keys, TOL[k]);
    }
    if (x.images.length > 1) {
      const im = []; let last = null; for (const { t, f } of fr) { const v = f[x.id].img; if (v !== last) { im.push({ t, v, f: 0 }); last = v; } }
      if (!(im.length === 1 && im[0].v === (r.img || 0))) tr.img = im;
    }
    if (Object.keys(tr).length) tracks[x.id] = tr;
  }
  return { id, name, dur, loop, tracks };
}
const made = [
  clip('ag_in', '요원: 비밀번호 — 눈 감기·사선·선글라스·발 고쳐 딛기·꼬리 까딱·바람', IN, false, t => agent(t)),
  clip('ag_hold', '요원: 경계(잔바람, 반복)', HOLD, true, t => agent(IN + t)),
  clip('ag_out', '요원: 선글라스 거두고 복귀', OUT, false, t => agent(IN, t / OUT)),
];
for (const c of made) { p.clips.push(c); p.preview.push({ label: c.name, clip: c.id }); }
p.agent = JSON.parse(JSON.stringify(CFG.targetAgent));   // bury·puffs 없는 새 설정으로 통째로
fs.writeFileSync(F, JSON.stringify(p), 'utf8');
console.log(JSON.stringify({ clips: made.map(c => [c.id, c.dur, Math.round(JSON.stringify(c).length / 1024) + 'KB']), agent: p.agent, parts: p.parts.map(x => x.id).filter(x => /^k_/.test(x)), fileKB: Math.round(fs.statSync(F).size / 1024) }));
