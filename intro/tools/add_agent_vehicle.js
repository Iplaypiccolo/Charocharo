#!/usr/bin/env node
/*
 * 첨다니·타로타로 비밀번호 요원 모드 넣기 (add_agent_vehicle.js) — 2026-10-21, 네·다섯 번째 친구(바퀴 달린 친구)
 * 사용법: node intro/tools/add_agent_vehicle.js <첨다니_요원모드… 또는 타로타로_요원모드… 폴더>
 *
 * - 자료의 설정/추가파츠.json + 새이미지 2장(사선 차체·선글라스)만 읽음. 새 그림은 바이트 그대로 drawRect·등록 행렬로 배치(자르거나 늘이지 않음).
 *   다시 쓰는 원본(귀·안테나·바퀴, 첨다니는 와이파이도)은 현재 파일 그림을 해시로 확인.
 * - 차체 그림은 기존 그림 목록 맨 뒤에 덧붙임(0·1번 등 원래 그림 그대로). 선글라스 k_agentGlasses 는 차체 파츠(첨다니 body, 타로타로 bodyImg)의 자식.
 * - 요원 상태 자세(귀·안테나·바퀴·와이파이 최종값 → rest 차이로 환산), 숨길 파츠, 그리는 순서는 설정 그대로.
 * - 시간표(개별 콘티): 0 정면에서 눈 감기 → 0.42 사선 차체로 교체 → 0.8~1.18 선글라스 착(처음 4~5도 기울었다 정돈)
 *   → (첨다니) 1.2~1.8 와이파이 한 번 차례로 켰다 끔(약한 테두리 wifi0 은 계속)
 *   → 바람(몸 그룹이 버팀, 안테나 0.14초·귀 0.18초 늦게) → (타로타로) 3.55~3.95 작은 엣헴 반동 → 4.6초마다 잔바람(1/5).
 *   바퀴는 프레임마다 wheelHulls 를 변환해 기본 자세 때 바닥 높이에 맞춤. 반짝 없음(티라만).
 * - 다시 돌려도 같은 결과.
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..', '..');
const SRC = process.argv[2];
if (!SRC || !fs.existsSync(path.join(SRC, '설정', '추가파츠.json'))) { console.error('사용법: node intro/tools/add_agent_vehicle.js <요원모드 자료 폴더>'); process.exit(1); }
const win = { document: { currentScript: null }, performance: { now: () => 0 } };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'charo-pet.js'), 'utf8'), { window: win, document: win.document, performance: win.performance });
const CP = win.CharoPet;
const CFG = JSON.parse(fs.readFileSync(path.join(SRC, '설정', '추가파츠.json'), 'utf8'));
const TL = CFG.timeline;
const VEH = {
  '첨다니': { wind: TL.windBody, amp: 1.3, lags: [['ant', 8, TL.antennaDelay], ['earL', 5.5, TL.earDelay], ['earR', 3.5, TL.earDelay]], tilt: 5,
    front: { eyeL: { img: 2 }, eyeR: { img: 2 }, browL: { op: 0 }, browR: { op: 0 } }, wifi: true },
  '타로타로': { wind: TL.windBody, amp: 1.5, lags: [['antenna', 7, TL.antennaDelay], ['earL', 5, TL.earDelay], ['earR', 3, TL.earDelay]], tilt: 4,
    front: { eyes: { img: 0, op: 1 }, excl: { op: 0 }, mouth: { img: 0 } }, proud: TL.proudRecovery },
}[CFG.character];
if (!VEH) throw new Error('첨다니·타로타로 자료가 아님: ' + CFG.character);
const F = path.join(ROOT, CFG.projectFile), p = JSON.parse(fs.readFileSync(F, 'utf8')), part = id => CP.findPart(p, id);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v)), ease = v => { v = clamp(v); return v * v * (3 - 2 * v); };
const bump = (t, a, b) => (t > a && t < b) ? Math.sin((t - a) / (b - a) * Math.PI) : 0;

// 0) 예전 것 지우기
p.parts = p.parts.filter(x => x.id !== 'k_agentGlasses');
for (const x of p.parts) x.images = x.images.filter(v => !/_agent_v\d_/.test(v.asset));
for (const k of Object.keys(p.assets)) if (/_agent_v\d_/.test(k)) delete p.assets[k];
p.clips = p.clips.filter(c => !c.id.startsWith('ag_'));
for (const c of p.clips) delete c.tracks.k_agentGlasses;
p.preview = (p.preview || []).filter(x => !x.clip.startsWith('ag_'));
delete p.agent;
// 1) 원본 확인
for (const r of CFG.reuses) {
  const v = part(r.partId).images[r.imageIndex];
  if (!v || v.asset !== r.assetId) throw new Error(r.partId + ' 그림 ' + r.imageIndex + ' 이 ' + r.assetId + ' 가 아님');
  if (sha(Buffer.from(p.assets[r.assetId].split(',')[1], 'base64')) !== r.sha256) throw new Error('원본 그림이 자료와 다름 ' + r.assetId);
}
// 2) 새 그림
for (const a of Object.values(CFG.assets)) {
  const b = fs.readFileSync(path.join(SRC, a.file)); if (sha(b) !== a.sha256) throw new Error('새 그림 해시 다름 ' + a.file);
  p.assets[a.assetId] = 'data:image/png;base64,' + b.toString('base64');
}
const BV = CFG.bodyVariant, bodyPart = part(BV.partId), r0 = BV.drawRect;
bodyPart.images.push({ asset: CFG.assets[BV.key].assetId, name: '요원: 사선 차체', x: r0.x, y: r0.y, w: r0.w, h: r0.h });
const BODY_IMG = bodyPart.images.length - 1;
const G = CFG.glasses, M = G.pngToParentMatrix, E = G.finalPose, piv = [627, 627];
const glasses = { id: 'k_agentGlasses', name: '요원: 선글라스(' + G.parent + '에 붙음)', parent: G.parent, pivot: { x: piv[0], y: piv[1] },
  rest: { x: M[0] * piv[0] + M[2] * piv[1] + M[4], y: M[1] * piv[0] + M[3] * piv[1] + M[5], rot: E.rot, sx: E.sx, sy: E.sy, op: 1, img: 0 },
  images: [{ asset: CFG.assets[G.key].assetId, name: '요원: 선글라스', x: 0, y: 0, w: 1254, h: 1254 }], follow: { on: false, max: 0 } };
if (CP.localM(glasses.rest, glasses.pivot).some((v, i) => Math.abs(v - M[i]) > 1e-3)) throw new Error('선글라스 행렬 환산 오류');
const last = Math.max(...CFG.drawOrder.map(id => p.parts.findIndex(x => x.id === id)).filter(i => i >= 0));
p.parts.splice(last + 1, 0, glasses);
for (const c of p.clips) c.tracks.k_agentGlasses = { op: [{ t: 0, v: 0, e: 'step' }, { t: +c.dur.toFixed(3), v: 0, e: 'step' }] };

// 3) 자세
const baseOff = CP.offsetsFrom(p, CP.clipPose(p, CP.findClip(p, p.baseClip), 0));
const hide = new Set(CFG.hideDuringAgent), O = CFG.finalPoseOverrides, H = CFG.wheelHulls;
function floorOf(f) { const W = CP.worldMatrices(p, f); let y = -Infinity; for (const id of Object.keys(H)) for (const q of H[id]) y = Math.max(y, CP.apply(W[id], q[0], q[1])[1]); return y; }
const target = floorOf(CP.finalPose(p, baseOff, null));
function base() { const f = CP.finalPose(p, baseOff, null); for (const x of p.parts) if (/^(m_|k_)/.test(x.id)) f[x.id].op = 0; return f; }
function front() { const f = base(); for (const [id, v] of Object.entries(VEH.front)) Object.assign(f[id], v); return f; }
const IN = CFG.engineIntegration.durations.in, HOLD = CFG.engineIntegration.durations.hold, OUT = CFG.engineIntegration.durations.out;
const W0 = VEH.wind[0], W1 = VEH.wind[1], CALM = VEH.proud ? VEH.proud[1] : W1 + Math.max(...VEH.lags.map(l => l[2])) + 0.1;
function wave(t, d) {   // 바람 한 번(지연 d) 뒤 잔바람(1/5, 4.6초 주기)
  if (t < CALM) return bump(t, W0 + d, W1 + d);
  return 0.2 * Math.sin((t - CALM) * Math.PI * 2 / HOLD - d * 2);
}
function agent(t, out) {
  if (t < 0.42 && out == null) return front();
  const f = base();
  for (const id of hide) if (f[id]) f[id].op = 0;
  f[BV.partId].img = BODY_IMG;
  for (const [id, v] of Object.entries(O)) Object.assign(f[id], v);
  const g = f.k_agentGlasses;
  if (out == null) {
    g.op = t < 0.8 ? 0 : 1; g.y -= (1 - ease((t - 0.8) / 0.38)) * 160; g.rot += VEH.tilt * (1 - ease((t - 1.0) / 0.25)); g.y += bump(t, 1.18, 1.38) * 4;
  } else { g.y -= ease(out / 0.8) * 160; g.op = 1 - ease((out - 0.25) / 0.5); }
  if (VEH.wifi) {   // 약한 테두리는 계속, 진입 때 한 번만 차례로 켰다 끔
    f.wifi0.op = 1;
    const fade = out == null ? 1 - ease((t - 1.62) / 0.18) : 0;
    f.wifi1.op = out == null && t >= TL.wifiDot[0] ? fade : 0; f.wifi2.op = out == null && t >= TL.wifiInner[0] ? fade : 0; f.wifi3.op = out == null && t >= TL.wifiOuter[0] ? fade : 0;
  }
  const k = out == null ? 1 : 1 - ease(out), tt = out == null ? t : IN;
  f.body.rot += VEH.amp * wave(tt, 0) * k;
  for (const [id, amp, d] of VEH.lags) f[id].rot += amp * wave(tt, d) * k;
  if (VEH.proud && out == null) { f.body.rot -= 0.8 * bump(t, VEH.proud[0], VEH.proud[1]); f.body.y -= 4 * bump(t, VEH.proud[0], VEH.proud[1]); }   // 엣헴
  f.body.y += target - floorOf(f);   // 바퀴 접지
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
      const im = []; let lastV = null; for (const { t, f } of fr) { const v = f[x.id].img; if (v !== lastV) { im.push({ t, v, f: 0 }); lastV = v; } }
      if (!(im.length === 1 && im[0].v === (r.img || 0))) tr.img = im;
    }
    if (Object.keys(tr).length) tracks[x.id] = tr;
  }
  return { id, name, dur, loop, tracks };
}
const made = [
  clip('ag_in', '요원: 비밀번호 — 눈 감기·사선·선글라스' + (VEH.wifi ? '·신호 점검' : '') + '·바람' + (VEH.proud ? '·엣헴' : ''), IN, false, t => agent(t)),
  clip('ag_hold', '요원: 경계(잔바람, 반복)', HOLD, true, t => agent(IN + t)),
  clip('ag_out', '요원: 선글라스 거두고 복귀', OUT, false, t => agent(IN, t / OUT)),
];
for (const c of made) { p.clips.push(c); p.preview.push({ label: c.name, clip: c.id }); }
p.agent = { in: 'ag_in', hold: 'ag_hold', out: 'ag_out', ready: CFG.engineIntegration.agentReady, side: 0.42, version: 2, order: CFG.drawOrder.filter(id => part(id)) };
fs.writeFileSync(F, JSON.stringify(p), 'utf8');
console.log(JSON.stringify({ who: CFG.character, bodyImg: BODY_IMG, clips: made.map(c => [c.id, c.dur, Math.round(JSON.stringify(c).length / 1024) + 'KB']), order: p.agent.order, fileKB: Math.round(fs.statSync(F).size / 1024) }));
