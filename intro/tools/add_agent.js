#!/usr/bin/env node
/*
 * 비밀번호 요원 모드 넣기 (add_agent.js) — 2026-10-21, 첫 번째: 길통이
 * 사용법: node intro/tools/add_agent.js <길통이_비밀번호요원_제작자료 폴더>
 *
 * - 자료의 새 그림 4장(사선 머리·사선 몸통·선글라스·다문 입)을 그대로(바이트 동일) 넣고, 조립좌표.json 의 drawRect 로 원본 1254 좌표에 놓음.
 *   늘이거나 자르지 않음. 팔·다리·망토는 현재 파일의 원본 그림을 그대로 씀(자료의 원본 해시와 같은지 먼저 확인).
 * - 머리·몸통·입에는 그림 하나씩 덧붙이고(번호는 맨 뒤), 선글라스는 head 아래 새 파츠 k_agentGlasses(입 다음에 그림).
 *   k_ 로 시작 → 다른 모든 동작에서는 op 0, 재생기도 요원 동작 때만 보이게 함.
 * - 동작 3개(자료의 길통이_동작참고.js 시간표를 그대로 옮김, 1/120초 → 직선 구간만 줄임):
 *     ag_in   3.65초: 눈 감기(0) → 0.2~0.62 끄덕임·0.42 사선 머리·몸통 교체 → 0.8~1.18 선글라스 착 → 1.18~1.42 정돈 → 2.25 바람 한 번(망토 0.15초 늦게)
 *     ag_hold 4.6초 반복: 약한 잔바람(첫 바람의 1/3 이하)
 *     ag_out  0.42초: 선글라스 위로 거두기(눈은 감은 채) → 끝나면 재생기가 원래 얼굴·정면으로
 *   발 접지는 프레임마다 다리 윤곽(groundHulls)으로 맞춤.
 * - 캐릭터 파일에 p.agent = { in, hold, out, ready } 를 적음(로그인 화면 charo-mouse.js 가 읽음).
 * - 다시 돌려도 같은 결과(예전에 넣은 g_agent_ 그림·k_agentGlasses·ag_ 동작을 먼저 지움).
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..', '..');
const SRC = process.argv[2];
if (!SRC || !fs.existsSync(path.join(SRC, '조립', '조립좌표.json'))) { console.error('사용법: node intro/tools/add_agent.js <길통이_비밀번호요원_제작자료 폴더>'); process.exit(1); }
const win = { document: { currentScript: null }, performance: { now: () => 0 } };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'charo-pet.js'), 'utf8'), { window: win, document: win.document, performance: win.performance });
const CP = win.CharoPet;
const META = JSON.parse(fs.readFileSync(path.join(SRC, '조립', '조립좌표.json'), 'utf8'));
const F = path.join(ROOT, 'giltong', 'giltong.json');
const p = JSON.parse(fs.readFileSync(F, 'utf8'));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const part = id => CP.findPart(p, id);

// 0) 예전 것 지우기
p.parts = p.parts.filter(x => x.id !== 'k_agentGlasses');
for (const x of p.parts) x.images = x.images.filter(v => !v.asset.startsWith('g_agent_'));
for (const k of Object.keys(p.assets)) if (k.startsWith('g_agent_')) delete p.assets[k];
p.clips = p.clips.filter(c => !c.id.startsWith('ag_'));
for (const c of p.clips) delete c.tracks.k_agentGlasses;
p.preview = (p.preview || []).filter(x => !x.clip.startsWith('ag_'));

// 1) 원본 그림 확인(자료의 해시 = 현재 파일)
for (const o of META.originalAssets) {
  const uri = p.assets[o.asset]; if (!uri) throw new Error('현재 파일에 없는 원본 그림 ' + o.asset);
  if (sha(Buffer.from(uri.split(',')[1], 'base64')) !== o.sha256) throw new Error('원본 그림이 자료와 다름: ' + o.asset);
}
// 2) 새 그림 4장
const IDX = {};
for (const [key, im] of Object.entries(META.images)) {
  const buf = fs.readFileSync(path.join(SRC, im.file));
  if (sha(buf) !== im.sha256) throw new Error('새 그림 해시 다름: ' + im.file);
  p.assets[im.asset] = 'data:image/png;base64,' + buf.toString('base64');
  const r = im.drawRect, v = { asset: im.asset, name: '요원: ' + key, x: +r.x.toFixed(3), y: +r.y.toFixed(3), w: +r.w.toFixed(3), h: +r.h.toFixed(3) };
  if (key === 'glasses') continue;
  const pt = part(key); pt.images.push(v); IDX[key] = pt.images.length - 1;
}
const g = META.images.glasses, gr = g.drawRect;
const mi = p.parts.findIndex(x => x.id === 'mouth');
p.parts.splice(mi + 1, 0, { id: 'k_agentGlasses', name: '요원: 선글라스(머리에 붙음)', parent: 'head', pivot: { x: 662, y: 533 },
  rest: { x: 662, y: 533, rot: 0, sx: 1, sy: 1, op: 1, img: 0 }, images: [{ asset: g.asset, name: '요원: 선글라스', x: +gr.x.toFixed(3), y: +gr.y.toFixed(3), w: +gr.w.toFixed(3), h: +gr.h.toFixed(3) }], follow: { on: false, max: 0 } });
for (const c of p.clips) c.tracks.k_agentGlasses = { op: [{ t: 0, v: 0, e: 'step' }, { t: +c.dur.toFixed(3), v: 0, e: 'step' }] };

// 3) 자세(자료의 길통이_동작참고.js 를 이 파일 구조로 옮김). 반환은 '최종 자세'(rest 포함)
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v)), ease = v => { v = clamp(v); return v * v * (3 - 2 * v); };
const body0 = part('body').rest, sourceMax = Math.max(...Object.values(META.groundHulls).flat().map(q => q[1]));
const targetFloor = body0.y + (sourceMax - 1005) * body0.sy;
function base() { const f = {}; for (const x of p.parts) f[x.id] = { ...x.rest, img: x.rest.img || 0 }; f.armL.rot = -48; f.armR.rot = 48; return f; }
function agent(t, out) {   // out: 0~1 (ag_out 진행)
  const f = base(), side = t >= 0.42 || out != null, fall = ease((t - 0.8) / 0.38);
  f.head.img = side ? IDX.head : 0; f.body.img = side ? IDX.body : 0;
  f.mouth.img = IDX.mouth; if (!side) f.mouth.x += -54;
  f.eyeL.img = f.eyeR.img = 1; f.eyeL.sy = f.eyeR.sy = 0.22; f.eyeL.sx = f.eyeR.sx = 0.65;
  f.eyeL.op = f.eyeR.op = (t >= 1.18 && out == null) ? 0 : 1;
  f.browL.op = f.browR.op = 0;
  if (side) { f.eyeL.x += 45; f.eyeR.x -= 2; f.eyeL.y += 5; f.eyeR.y -= 12; }
  f.head.y += t < 0.62 ? Math.sin(clamp((t - 0.2) / 0.42) * Math.PI) * 8 : 0;
  f.k_agentGlasses.op = t < 0.8 ? 0 : 1; f.k_agentGlasses.y -= (1 - fall) * 160;
  if (t > 1.18 && t < 1.42) f.k_agentGlasses.y += Math.sin((t - 1.18) / 0.24 * Math.PI) * 5;
  let gust = 0, lag = 0;
  if (t >= 2.25 && t < 3.35) gust = Math.sin((t - 2.25) / 1.1 * Math.PI);
  if (t >= 2.40 && t < 3.65) lag = Math.sin((t - 2.40) / 1.25 * Math.PI);
  if (t >= 3.65) { const q = (t - 3.65) * Math.PI * 2 / 4.6; gust = 0.23 * Math.sin(q); lag = 0.32 * Math.sin(q - 0.32); }
  if (out != null) { const k = 1 - ease(out); gust *= k; lag *= k; const u = ease(out / 0.8); f.k_agentGlasses.y -= u * 160; f.k_agentGlasses.op = 1 - ease((out - 0.25) / 0.5); }
  f.body.rot = 1.7 * gust; f.head.rot = -0.75 * gust; f.cape.rot = -11 * lag; f.armL.rot -= 0.8 * lag; f.armR.rot -= 0.8 * lag;
  let W = CP.worldMatrices(p, f), floor = -Infinity;   // 발 접지
  for (const id of ['legL', 'legR']) for (const q of META.groundHulls[id]) floor = Math.max(floor, CP.apply(W[id], q[0], q[1])[1]);
  f.body.y += targetFloor - floor;
  return f;
}
// 최종 자세 → 동작 키(기본 자세에 대한 변화량: 위치·회전은 차이, 배율·투명도는 비율)
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
      if (flat && Math.abs(keys[0].v - DEF[k]) < 1e-6 && !(x.id === 'k_agentGlasses' && k === 'op')) continue;
      tr[k] = flat ? [keys[0]] : thin(keys, TOL[k]);
    }
    if (x.images.length > 1 || x.id === 'k_agentGlasses') {
      const im = []; let last = null; for (const { t, f } of fr) { const v = f[x.id].img; if (v !== last) { im.push({ t, v, f: 0 }); last = v; } }
      if (!(im.length === 1 && im[0].v === (r.img || 0))) tr.img = im;
    }
    if (/^m_|^k_arm/.test(x.id)) { tracks[x.id] = { op: [{ t: 0, v: 0, e: 'step' }, { t: dur, v: 0, e: 'step' }] }; continue; }
    if (Object.keys(tr).length) tracks[x.id] = tr;
  }
  return { id, name, dur, loop, tracks };
}
const IN = 3.65, HOLD = 4.6, OUT = 0.42;
const made = [
  clip('ag_in', '요원: 비밀번호 — 눈 감기·사선·선글라스 착·바람', IN, false, t => agent(t)),
  clip('ag_hold', '요원: 경계(잔바람, 반복)', HOLD, true, t => agent(IN + t)),
  clip('ag_out', '요원: 선글라스 거두고 복귀', OUT, false, t => agent(IN, t / OUT)),
];
for (const c of made) { p.clips.push(c); p.preview.push({ label: c.name, clip: c.id }); }
p.agent = { in: 'ag_in', hold: 'ag_hold', out: 'ag_out', ready: 1.42 };
fs.writeFileSync(F, JSON.stringify(p), 'utf8');
console.log(JSON.stringify({ images: IDX, clips: made.map(c => [c.id, c.dur, Math.round(JSON.stringify(c).length / 1024) + 'KB']), kb: Math.round(fs.statSync(F).size / 1024) }));
