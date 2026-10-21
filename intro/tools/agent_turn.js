#!/usr/bin/env node
/*
 * 비밀번호 요원 모드 v5 (agent_turn.js) — 2026-10-21 사용자 요청 5건 반영(구도 전환·선글라스·도로덕)
 * 사용법: node intro/tools/agent_turn.js            (저장소 맨 위에서. 여러 번 돌려도 같은 결과)
 *
 * 하는 일(여섯 친구 파일의 ag_in·ag_hold·ag_out 동작을 다시 만듦. 그림·파츠는 그대로, 원래 동작은 src_ag_* 로 보관해 거기서 다시 만듦)
 *  1) 구도 전환: 예전에는 0.42초에 정면 그림 → 35도 그림이 한 프레임에 바뀌고(휙), 그 전 0.42초는 눈 감기였음.
 *     지금은 눈 감기 없이 평소 얼굴 그대로 서 있다가 T0~T1(0.17~0.67초)에 정면 → 35도로 '돌아섬':
 *       · 그림 교차(덮어 그리기 'o': 이전 그림은 그대로 두고 새 그림이 위로 서서히 → 몸통이 반투명해지지 않음)
 *       · 자세(위치·회전·크기)를 부드럽게 이어 붙임 + 몸 전체 가로가 살짝 좁아졌다 펴짐(돌아서는 느낌, 최대 9%)
 *  2) 눈: 정면 눈·눈썹·입은 돌아서는 동안 서서히 사라지고, 같은 시간에 35도 몸통에 그려진 눈이 올라옴 → 눈이 갑자기 없어지는 순간이 없음.
 *     35도 그림의 눈은 선글라스가 완전히 씌워질 때까지 그대로 보임.
 *  3) 선글라스: 위에서 크게 떨어지던 것을 눈 바로 앞에서 흐려지며 내려앉게(떨어지는 거리 30%), 크기를 친구마다 눈 간격에 맞춰 줄임(GLASS 표), 기울기 보정.
 *  4) 도로덕: 35도 그림에서 앞으로 나온 쪽 날개를 몸통 위에 그림(p.agent.order).
 *  5) 나올 때(ag_out)도 같은 방식으로 35도 → 정면으로 서서히(예전에는 0.42초 끝에 그림이 휙 바뀜).
 * 재생기 쪽: charo-pet.js 그림 키의 o:1(덮어 그리기), charo-mouse.js 는 그대로.
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.resolve(__dirname, '..', '..');
const win = { document: { currentScript: null }, performance: { now: () => 0 } };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'charo-pet.js'), 'utf8'), { window: win, document: win.document, performance: win.performance });
const CP = win.CharoPet;
const FILES = { giltong: 'giltong/giltong.json', doroduck: 'doroduck/doroduck.json', charocharo: 'charo-pet.json', chumdani: 'chumdani/chumdani.json', tarotaro: 'tarotaro/tarotaro.json', tira: 'tira_v3/tira_v3.json' };
const T0 = 0.12, T1 = 0.62, X0 = 0.28, X1 = 0.52, OUT0 = 0.0, SQUASH = 0.09;   // T: 자세 이어 붙임, X: 그림·눈 교차(짧을수록 두 그림이 겹쳐 보이는 시간이 짧음)
// 선글라스 그림(여섯 모두 같은 1254×1254)의 두 렌즈 가운데 = (855, 668). 크기(g)·기울기 보정(dr 도)·이동(dx,dy: 그림 좌표)
const LENS = [855, 668];
const GLASS = {
  doroduck: { g: 0.9, dr: 0, dx: 0, dy: 0 },
  charocharo: { g: 0.93, dr: 0, dx: 0, dy: -35 },   // dy: 선글라스 그림 좌표(음수 = 위). 입과 겹치지 않게 살짝 올림
  tira: { g: 0.84, dr: 0, dx: 0, dy: 0 },
  chumdani: { g: 0.9, dr: 6, dx: 0, dy: 0 },
  tarotaro: { g: 0.92, dr: 0, dx: 0, dy: -35 },
  giltong: { g: 0.93, dr: 0, dx: 0, dy: 0 },
};
// 35도 자세에서 떨어져 보이는 부품을 다시 붙임(부모 좌표 이동량, 35도 자세에만 적용). 길통이: 머리를 몸통 쪽으로 내리고 망토를 팔 뒤로 붙임
const STITCH = { giltong: { head: { y: 30 }, cape: { x: 42, y: -12 } } };
const ORDER = { doroduck: ['wingL', 'footR', 'footL', 'body', 'wingR', 'beak', 'k_agentGlasses'] };   // 앞으로 나온 날개는 몸통 위
const FACE = /^(eye|brow|mouth|m_|headImg$|mask$|fire$|excl$|eyes$)/;
const TOL = { x: 0.15, y: 0.15, rot: 0.1, sx: 0.003, sy: 0.003, op: 0.003 }, DEF = { x: 0, y: 0, rot: 0, sx: 1, sy: 1, op: 1 }, PR = ['x', 'y', 'rot', 'sx', 'sy', 'op'];
const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v, smooth = u => { u = clamp01(u); return u * u * (3 - 2 * u); };
const clone = o => JSON.parse(JSON.stringify(o));
function thin(keys, tol) {
  if (keys.length <= 2) return keys;
  const keep = new Array(keys.length).fill(false); keep[0] = keep[keys.length - 1] = true;
  (function rec(a, b) { let w = -1, wi = -1; for (let i = a + 1; i < b; i++) { const u = (keys[i].t - keys[a].t) / (keys[b].t - keys[a].t), d = Math.abs(keys[i].v - (keys[a].v + (keys[b].v - keys[a].v) * u)); if (d > w) { w = d; wi = i; } } if (w > tol) { keep[wi] = true; rec(a, wi); rec(wi, b); } })(0, keys.length - 1);
  return keys.filter((k, i) => keep[i]);
}
const report = {};
for (const [cid, file] of Object.entries(FILES)) {
  const F = path.join(ROOT, file), p = JSON.parse(fs.readFileSync(F, 'utf8')), A = p.agent;
  if (!A) throw new Error(cid + ': 요원 동작이 없음');
  // 원래 동작 보관(src_ag_*) — 이미 있으면 그것에서 다시 만듦
  const src = {};
  for (const id of [A.in, A.hold, A.out]) {
    let s = p.clips.find(c => c.id === 'src_' + id);
    if (!s) { s = clone(p.clips.find(c => c.id === id)); s.id = 'src_' + id; s.name = '(원본) ' + s.name; p.clips.push(s); }
    src[id] = s;
  }
  const part = id => CP.findPart(p, id), root = p.parts.filter(x => !x.parent)[0].id;
  const baseOff = CP.offsetsFrom(p, CP.clipPose(p, CP.findClip(p, p.baseClip), 0));
  const idleOff = clone(baseOff);
  for (const bp in (p.mouse && p.mouse.base) || {}) { const o = idleOff[bp], b = p.mouse.base[bp]; if (!o) continue; if (b.op != null) o.op = b.op; if (b.img != null) o.img = { img: b.img, prev: b.img, mix: 1 }; }
  const idle = CP.finalPose(p, idleOff, null);
  function poseOf(clip, t) {
    const off = clone(baseOff), pose = CP.clipPose(p, clip, t);
    for (const id in pose) { const q = pose[id], o = off[id]; if (!o) continue; for (const k of PR) if (q[k] != null) o[k] = q[k]; if (q.img) o.img = q.img; }
    const f = CP.finalPose(p, off, null); for (const id in f) f[id] = { x: f[id].x, y: f[id].y, rot: f[id].rot, sx: f[id].sx, sy: f[id].sy, op: f[id].op, img: f[id].img }; return f;
  }
  // 선글라스: 크기 조정 g(렌즈 가운데 고정) + 기울기 + 이동, 떨어지는 거리 줄이기·서서히 나타남
  const GL = GLASS[cid], gp = part('k_agentGlasses'), pv = gp.pivot;
  const finalHold = poseOf(src[A.hold], 0).k_agentGlasses, finalIn = poseOf(src[A.in], A.in === 'ag_in' ? 1.6 : 1.6).k_agentGlasses;
  // 위에서 떨어지는 길이 줄이기(렌즈 가운데 기준): 원래 y 궤적에서 최종값과의 차이 30%만 남김
  function glassFix(f, t, inClip) {
    const o = f.k_agentGlasses; if (!o) return;
    let dyO = 0, dxO = 0;
    if (inClip && t < 1.7) { dyO = (finalIn.y - o.y) * 0.7; dxO = (finalIn.x - o.x) * 0.7; }
    o.y += dyO; o.x += dxO;
    // 렌즈 가운데 고정 크기·기울기 변경
    const vx = LENS[0] - pv.x, vy = LENS[1] - pv.y, r0 = o.rot * Math.PI / 180, c0 = Math.cos(r0), s0 = Math.sin(r0);
    const cx = o.x + (c0 * vx - s0 * vy) * o.sx, cy = o.y + (s0 * vx + c0 * vy) * o.sy;
    o.sx *= GL.g; o.sy *= GL.g; o.rot += GL.dr; const r1 = o.rot * Math.PI / 180, c1 = Math.cos(r1), s1 = Math.sin(r1);
    o.x = cx - (c1 * vx - s1 * vy) * o.sx + GL.dx * o.sx; o.y = cy - (s1 * vx + c1 * vy) * o.sy + GL.dy * o.sy;
    if (inClip) o.op = clamp01((t - 0.8) / 0.22) * (o.op > 0 ? 1 : 0);
  }
  function stitch(f) { const T = STITCH[cid]; if (!T) return; for (const id in T) { const o = f[id]; if (!o) continue; if (T[id].x) o.x += T[id].x; if (T[id].y) o.y += T[id].y; if (T[id].rot) o.rot += T[id].rot; } }
  // 한 장 한 장 모아 동작으로(트랙 얇게 정리). fr[i] = {t, f:{파츠:{x,y,rot,sx,sy,op,img,o?}}, xf:{파츠:전환 길이(초)}}
  function build(id, name, dur, loop, fn) {
    const n = Math.round(dur * 120), fr = [];
    for (let i = 0; i <= n; i++) { const t = +(dur * i / n).toFixed(4); fr.push({ t, f: fn(Math.min(t, dur - 1e-4)) }); }
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
        const im = []; let last = null;
        for (const { t, f } of fr) { const q = f[x.id], v = q.img; if (v !== last) { const k = { t, v, f: (last != null && q.xf) ? +q.xf.toFixed(3) : 0 }; if (last != null && q.xf) k.o = 1; im.push(k); last = v; } }
        if (!(im.length === 1 && im[0].v === (r.img || 0))) tr.img = im;
      }
      if (Object.keys(tr).length) tracks[x.id] = tr;
    }
    return { id, name, dur, loop, tracks };
  }
  function lerpPose(a, b, e, o) {
    for (const k of ['x', 'y', 'sx', 'sy', 'op']) o[k] = a[k] + (b[k] - a[k]) * e;
    let ar = a.rot; while (ar - b.rot > 180) ar -= 360; while (b.rot - ar > 180) ar += 360; o.rot = ar + (b.rot - ar) * e;
  }
  // 투명도 이어 붙임: 몸 같은 그림(얼굴 아님)이 서로 바뀔 때 반투명하게 비치지 않도록 — 나타나는 쪽이 먼저 차고(앞 절반), 사라지는 쪽은 그다음(뒤 절반)
  function opMix(a, b, ef, face) {
    if (face || (a.op > 0.01) === (b.op > 0.01)) return a.op + (b.op - a.op) * ef;
    return b.op > a.op ? b.op * smooth(ef * 2) : a.op * (1 - smooth(ef * 2 - 1));
  }
  function faceOf(f) { for (const id in f) if (FACE.test(id) && idle[id]) { f[id].op = idle[id].op; f[id].img = idle[id].img; } return f; }
  // ── ag_in ──
  const sIn = src[A.in], dIn = sIn.dur;
  const inFn = t => {
    const S = poseOf(sIn, Math.max(t, 0.425)); glassFix(S, t, true); stitch(S);
    if (t >= T1) return S;
    const Fm = faceOf(poseOf(sIn, Math.min(t, 0.41))); { const g = Fm.k_agentGlasses; if (g && S.k_agentGlasses) Object.assign(g, S.k_agentGlasses); }   // 선글라스는 전환 동안 제자리(투명도로만 나타남, 0.8초부터)
    const u = clamp01((t - T0) / (T1 - T0)), e = smooth(u), ef = smooth((t - X0) / (X1 - X0)), out = {};
    for (const x of p.parts) {
      const id = x.id, a = Fm[id], b = S[id], o = {};
      lerpPose(a, b, e, o); o.op = opMix(a, b, ef, FACE.test(id) || /^k_agentGlasses$/.test(id));
      const hideAtSide = b.op < 0.01 && a.op > 0.01 && FACE.test(id);
      if (hideAtSide || a.img === b.img) o.img = hideAtSide ? a.img : b.img;
      else if (t < X0) o.img = a.img;
      else { o.img = b.img; o.xf = X1 - X0; }
      if (t < T0) { o.x = a.x; o.y = a.y; o.rot = a.rot; o.sx = a.sx; o.sy = a.sy; }
      if (id === root) o.sx *= 1 - SQUASH * Math.sin(Math.PI * u);
      out[id] = o;
    }
    return out;
  };
  // 이미지 전환 키는 T0 에서 한 번(전환 길이 T1-T0)만 — 프레임마다 xf 가 붙어도 값이 바뀔 때만 키가 생김
  const newIn = build(A.in, sIn.name.replace(/^\(원본\) /, ''), dIn, !!sIn.loop, inFn);
  // ── ag_hold: 선글라스만 보정 ──
  const sHold = src[A.hold];
  const newHold = build(A.hold, sHold.name.replace(/^\(원본\) /, ''), sHold.dur, !!sHold.loop, t => { const f = poseOf(sHold, t); glassFix(f, t, false); stitch(f); return f; });
  // ── ag_out: 35도 → 정면으로 서서히 ──
  const sOut = src[A.out], dOut = sOut.dur;
  const outFn = t => {
    const S = poseOf(sOut, t); glassFix(S, t, false); stitch(S);
    const u = clamp01((t - OUT0) / (dOut - OUT0)), e = smooth(u), o2 = {};
    const gl = S.k_agentGlasses; if (gl) gl.op = 1 - clamp01(t / 0.2);   // 선글라스는 먼저 거둠
    for (const x of p.parts) {
      const id = x.id, a = S[id], b = idle[id], o = {};
      lerpPose(a, b, e, o);
      const toFace = FACE.test(id) && b.op > 0.01 && a.op < 0.01;
      o.op = opMix(a, b, smooth((u - 0.1) / 0.8), FACE.test(id));
      if (toFace) o.op = b.op * smooth((u - 0.4) / 0.6);
      if (id === 'k_agentGlasses') o.op = gl ? gl.op : 0;
      if (a.img === b.img || toFace) o.img = toFace ? b.img : a.img;
      else if (b.op < 0.01) o.img = a.img;
      else { o.img = b.img; o.xf = dOut - OUT0; }
      if (u >= 1) { Object.assign(o, { x: b.x, y: b.y, rot: b.rot, sx: b.sx, sy: b.sy, op: b.op, img: b.img }); }
      if (id === root) o.sx *= 1 - SQUASH * Math.sin(Math.PI * u);
      o2[id] = o;
    }
    return o2;
  };
  const newOut = build(A.out, sOut.name.replace(/^\(원본\) /, ''), dOut, !!sOut.loop, outFn);
  p.clips = p.clips.filter(c => ![A.in, A.hold, A.out].includes(c.id)).concat([newIn, newHold, newOut]);
  if (ORDER[cid]) A.order = ORDER[cid];
  A.turn = { t0: T0, t1: T1, version: 5 };
  fs.writeFileSync(F, JSON.stringify(p), 'utf8');
  report[cid] = { fileKB: Math.round(fs.statSync(F).size / 1024), imgKeys: Object.entries(newIn.tracks).filter(([, t]) => t.img).map(([k, t]) => k + ':' + t.img.length) };
}
console.log(JSON.stringify(report));
