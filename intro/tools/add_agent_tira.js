#!/usr/bin/env node
/*
 * 티라 비밀번호 요원 모드 넣기 (add_agent_tira.js) — 2026-10-21, 세 번째 친구
 * 사용법: node intro/tools/add_agent_tira.js <티라_요원모드_사선_경량자료 폴더>
 *
 * - 자료의 설정/추가파츠.json + 새이미지 4장(사선 몸체·굽힌 몸체·선글라스·눈더미)만 읽음. 새 그림은 바이트 그대로 drawRect 로 배치.
 *   다시 쓰는 원본(발 두 개·꼬리)은 현재 파일의 그림을 해시로 확인. 꼬리는 가로 배율 음수(좌우 반전)로 등 뒤에 — 픽셀은 그대로.
 * - 새 파츠(모두 k_ 로 시작 → 다른 동작에서는 op 0):
 *     k_agentBody(sway 아래, 감은 눈·다섯 이빨·뼈깃이 이어진 사선 몸체; 땅 위만 보이게 sway 좌표 y<1046 으로 자름)
 *     k_agentGlasses(k_agentBody 아래, 등록 행렬 그대로) · k_agentBuried(sway 아래, 얼굴 없는 굽힌 몸체) · k_agentSnow(rig 아래 = 바닥에 고정)
 * - 시간표(개별 콘티): 0 눈 감기(원래 정면 headImg 1) → 0.42 사선 몸체 → 0.72~0.88 앞으로 숙임·먼 발 당김 → 0.88 '푹!' 굽힌 몸체·눈더미
 *   → 1.08~1.55 꼬리 까딱 두 번·몸 꼼지락 → 1.55~1.95 머리를 쑥(사선 몸체가 구멍 쪽 (+210,+600) 에서 제자리로, 땅 아래는 잘림), 굽힌 몸체 1.68~1.78 사라짐
 *   → 1.72~2.0 선글라스가 7도 비뚤게 걸렸다 정돈 → 1.95~2.07 눈더미 사라짐·작은 반동 → 2.05~2.21 반짝 한 번(재생기가 그림)
 *   → 2.4~3.65 바람(몸 1.5도, 꼬리 0.15초 늦게 6도) → 4.6초마다 잔바람(1/4). ag_out 0.42초: 선글라스 거두기.
 * - p.agent 에 ready 2.30, 그리는 순서, 반짝·눈가루(재생기가 코드로 그림) 정보를 적음.
 * - 다시 돌려도 같은 결과.
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..', '..');
const SRC = process.argv[2];
if (!SRC || !fs.existsSync(path.join(SRC, '설정', '추가파츠.json'))) { console.error('사용법: node intro/tools/add_agent_tira.js <티라_요원모드 자료 폴더>'); process.exit(1); }
const win = { document: { currentScript: null }, performance: { now: () => 0 } };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'charo-pet.js'), 'utf8'), { window: win, document: win.document, performance: win.performance });
const CP = win.CharoPet;
const CFG = JSON.parse(fs.readFileSync(path.join(SRC, '설정', '추가파츠.json'), 'utf8'));
if (CFG.character !== '티라') throw new Error('티라 자료가 아님');
const F = path.join(ROOT, CFG.projectFile), p = JSON.parse(fs.readFileSync(F, 'utf8')), part = id => CP.findPart(p, id);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v)), ease = v => { v = clamp(v); return v * v * (3 - 2 * v); };
const bump = (t, a, b) => (t > a && t < b) ? Math.sin((t - a) / (b - a) * Math.PI) : 0;
const NEW = ['k_agentBody', 'k_agentGlasses', 'k_agentBuried', 'k_agentSnow'];

// 0) 예전 것 지우기
p.parts = p.parts.filter(x => !NEW.includes(x.id));
for (const k of Object.keys(p.assets)) if (/_agent_v2_/.test(k)) delete p.assets[k];
p.clips = p.clips.filter(c => !c.id.startsWith('ag_'));
for (const c of p.clips) for (const k of NEW) delete c.tracks[k];
p.preview = (p.preview || []).filter(x => !x.clip.startsWith('ag_'));
delete p.agent;
// 1) 원본 확인
for (const r of CFG.reuses) {
  const v = part(r.partId).images[r.imageIndex];
  if (!v || v.asset !== r.assetId) throw new Error(r.partId + ' 그림 ' + r.imageIndex + ' 가 ' + r.assetId + ' 가 아님');
  if (sha(Buffer.from(p.assets[r.assetId].split(',')[1], 'base64')) !== r.sha256) throw new Error('원본 그림이 자료와 다름 ' + r.assetId);
}
// 2) 새 그림
for (const a of Object.values(CFG.assets)) {
  const b = fs.readFileSync(path.join(SRC, a.file)); if (sha(b) !== a.sha256) throw new Error('새 그림 해시 다름 ' + a.file);
  p.assets[a.assetId] = 'data:image/png;base64,' + b.toString('base64');
}
const A = k => CFG.assets[k].assetId, P = CFG.parts, rect = (k, r) => ({ asset: A(k), name: '요원: ' + k, x: r.x, y: r.y, w: r.w, h: r.h });
const mk = (id, name, parent, pivot, images, extra) => Object.assign({ id, name, parent, pivot: { ...pivot }, rest: { x: pivot.x, y: pivot.y, rot: 0, sx: 1, sy: 1, op: 1, img: 0 }, images, follow: { on: false, max: 0 } }, extra || {});
const body = mk('k_agentBody', '요원: 사선 몸체(감은 눈·이빨 포함)', 'sway', P.k_agentBody.pivot, [rect('standing', P.k_agentBody.variants[0].drawRect)],
  { clip: { part: 'sway', rect: [-3000, -3000, 7000, 3000 + CFG.popReference.clipGroundY] } });
const buried = mk('k_agentBuried', '요원: 머리 박은 굽힌 몸체', 'sway', P.k_agentBuried.pivot, [rect('buried', P.k_agentBuried.drawRect)]);
const snow = mk('k_agentSnow', '요원: 작은 눈더미(바닥에 고정)', 'rig', { x: 0, y: 0 }, [rect('snow', P.k_agentSnow.drawRect)]);
const M = P.k_agentGlasses.pngToParentMatrix, E = P.k_agentGlasses.finalPose, piv = [627, 627];
const glasses = mk('k_agentGlasses', '요원: 선글라스(몸체에 붙음)', 'k_agentBody', { x: piv[0], y: piv[1] }, [{ asset: A('glasses'), name: '요원: 선글라스', x: 0, y: 0, w: 1254, h: 1254 }]);
glasses.rest = { x: M[0] * piv[0] + M[2] * piv[1] + M[4], y: M[1] * piv[0] + M[3] * piv[1] + M[5], rot: E.rot, sx: E.sx, sy: E.sy, op: 1, img: 0 };
if (CP.localM(glasses.rest, glasses.pivot).some((v, i) => Math.abs(v - M[i]) > 1e-3)) throw new Error('선글라스 행렬 환산 오류');
p.parts.splice(p.parts.findIndex(x => x.id === 'collar') + 1, 0, buried, body, glasses, snow);
for (const c of p.clips) for (const k of NEW) c.tracks[k] = { op: [{ t: 0, v: 0, e: 'step' }, { t: +c.dur.toFixed(3), v: 0, e: 'step' }] };

// 3) 자세(최종값) → 동작 키
const baseOff = CP.offsetsFrom(p, CP.clipPose(p, CP.findClip(p, p.baseClip), 0));
const hide = new Set(CFG.hideDuringAgent), SP = CFG.standingPose, BP = CFG.buriedPose, POP = CFG.popReference.standingImageOffsetAtStart;
const IN = CFG.engineIntegration.durations.in, HOLD = CFG.engineIntegration.durations.hold, OUT = CFG.engineIntegration.durations.out;
function base() { const f = CP.finalPose(p, baseOff, null); for (const x of p.parts) if (/^(m_|k_)/.test(x.id)) f[x.id].op = 0; return f; }
function front(t) {   // 0~0.42: 원래 정면, 감은 눈(><), 불·팻말·마우스 얼굴 끔
  const f = base(); f.headImg.img = 1; for (const k of ['sign11B', 'sign11F', 'sign14', 'mask', 'fire']) f[k].op = 0; return f;
}
const lerp = (a, b, u) => a + (b - a) * u, mixPose = (f, A0, B0, u) => { for (const id of Object.keys(A0)) for (const k of ['x', 'y', 'rot', 'sx', 'sy']) f[id][k] = lerp(A0[id][k], B0[id][k], u); };
function agent(t, out) {
  if (t < 0.42 && out == null) return front(t);
  const f = base();
  for (const id of hide) if (f[id]) f[id].op = 0;
  const b = f.k_agentBody, g = f.k_agentGlasses, bu = f.k_agentBuried, sn = f.k_agentSnow;
  b.op = 1; Object.keys(SP).forEach(id => Object.assign(f[id], SP[id]));
  let gust = 0, lag = 0;
  if (out == null && t < 2.07) {
    // 숙임(0.72~0.88): 몸체 앞으로, 먼 발 뒤로 한 번
    const lean = ease((t - 0.72) / 0.16);
    b.rot += 9 * lean; f.footR.x = lerp(SP.footR.x, BP.footR.x, lean * 0.6);
    if (t >= 0.88) {   // 푹! 굽힌 몸체
      const sink = ease((t - 0.88) / 0.2);
      b.op = 0; bu.op = 1; sn.op = 1;
      mixPose(f, SP, BP, Math.min(1, 0.6 + sink));
      bu.y += (1 - sink) * -18;
      if (t >= 1.08 && t < 1.55) { const q = (t - 1.08) / 0.47; f.tail.rot = BP.tail.rot + 7 * Math.sin(q * Math.PI * 4); bu.rot += 1.2 * Math.sin(q * Math.PI * 6); }   // 꼬리 까딱 두 번·꼼지락
    }
    if (t >= 1.55) {   // 쑥! 사선 몸체가 구멍 쪽에서 올라오며 펴짐(땅 아래는 잘림)
      const u = ease((t - 1.55) / 0.4);
      b.op = 1; b.rot = 0; b.x += POP.x * (1 - u); b.y += POP.y * (1 - u);
      bu.op = t < 1.68 ? 1 : 1 - ease((t - 1.68) / 0.1);
      mixPose(f, BP, SP, ease((t - 1.55) / 0.25));
      b.y -= bump(t, 1.9, 2.05) * 14;   // 작은 위쪽 반동
    }
    sn.op = t < 0.86 ? 0 : t < 1.95 ? 1 : 1 - ease((t - 1.95) / 0.12);
  } else { b.y -= out == null ? bump(t, 1.9, 2.05) * 14 : 0; }
  // 선글라스: 1.72~2.0 위에서 7도 비뚤게 걸렸다 정돈
  if (out == null) {
    g.op = t < 1.72 ? 0 : 1; g.y -= (1 - ease((t - 1.72) / 0.18)) * 160; g.rot += 7 * (1 - ease((t - 1.86) / 0.14));
    gust = bump(t, 2.4, 3.5); lag = bump(t, 2.55, 3.65);
    if (t >= 3.65) { const q = (t - 3.65) * Math.PI * 2 / HOLD; gust = 0.25 * Math.sin(q); lag = 0.25 * Math.sin(q - 0.32); }
  } else {
    const k = 1 - ease(out); const q = 0; gust = 0.25 * Math.sin(q) * k;
    g.y -= ease(out / 0.8) * 160; g.op = 1 - ease((out - 0.25) / 0.5);
  }
  b.rot += 1.5 * gust; f.tail.rot += 6 * lag;
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
  clip('ag_in', '요원: 비밀번호 — 눈 감기·사선·눈에 머리 박기·쑥·선글라스·바람', IN, false, t => agent(t)),
  clip('ag_hold', '요원: 경계(잔바람, 반복)', HOLD, true, t => agent(3.65 + t)),
  clip('ag_out', '요원: 선글라스 거두고 복귀', OUT, false, t => agent(3.65, t / OUT)),
];
for (const c of made) { p.clips.push(c); p.preview.push({ label: c.name, clip: c.id }); }
p.agent = { in: 'ag_in', hold: 'ag_hold', out: 'ag_out', ready: CFG.engineIntegration.agentReady, side: 0.42, version: 2,
  order: CFG.drawOrder.filter(id => part(id)),
  glint: { part: 'k_agentGlasses', at: CFG.effect.glintLocalPoint, t: CFG.timeline.glint, r: 45 },   // 반짝 한 번(진입 때만)
  puffs: [{ part: 'k_agentSnow', at: CFG.parts.k_agentSnow.holeAnchor, t: [0.86, 1.04] }, { part: 'k_agentSnow', at: CFG.parts.k_agentSnow.holeAnchor, t: [1.52, 1.74] }],   // 눈가루
  bury: [0.86, 1.95] };
fs.writeFileSync(F, JSON.stringify(p), 'utf8');
console.log(JSON.stringify({ clips: made.map(c => [c.id, c.dur, Math.round(JSON.stringify(c).length / 1024) + 'KB']), order: p.agent.order, fileKB: Math.round(fs.statSync(F).size / 1024) }));
