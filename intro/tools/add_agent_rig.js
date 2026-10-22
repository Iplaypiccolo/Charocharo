#!/usr/bin/env node
/*
 * 비밀번호 요원 모드 — '검수 확정 리그' 넣기 (add_agent_rig.js) · 2026-10-22, 친구 하나씩(길통이·차로차로)
 * 사용법: node intro/tools/add_agent_rig.js <친구_요원모드_최종파츠 폴더>     (여러 번 돌려도 같은 결과)
 *
 * 자료 형식: 설정/<이름>_조립설정.json 의 engineRecipe(파츠·그림 파일·sha256)와 timeline(시간표), 파츠/*.png(1254×1254 투명).
 * 하는 일
 *  - 자료의 새 리그(engineRecipe.parts, 예: gt_verified_*)를 그대로 등록. 그림은 sha256 확인 후 그대로(여백 자르기·다시 맞추기 없음).
 *    pivot·rest 는 자료 값 그대로. 크기·위치는 자료의 projectRoot(정면 좌표계 등록값) 하나뿐 — 예전 회전 보정·가로 압축·파츠별 offset 을 덧붙이지 않음.
 *  - 기존 파츠·그림·평소 동작은 지우지 않음. 평소 동작(인트로·마우스·타자·터치 등 ag_ 아닌 모든 동작)에는 새 파츠의 '숨김(op 0)' 트랙만 추가.
 *  - ag_in(진입) · ag_hold(대기, 반복) · ag_out(35도+선글라스에서 복귀) · ag_out35(35도, 선글라스 전) · ag_out24 · ag_out12 를 새로 만듦.
 *    각도(img 0=12°,1=24°,2=35°)는 모든 새 파츠가 같은 프레임에 바뀜(f=0, 보간 없음). 연속 값(팔·안경·몸 기울기·망토)은 자료 시간표를 smoothstep 으로.
 *    새 리그가 보이는 동안 이 친구의 기존 파츠는 모두 숨김(op 0). 정면 단계(0~첫 각도)는 기존 파츠를 평소 모습 그대로.
 *  - p.agent.rig: 재생기(charo-mouse.js)가 나가고 다시 들어올 때 지금 각도에서 이어 가도록 쓰는 표(각도 단계·복귀 동작·재진입 위치).
 *  - 예전 v5 원본 동작(src_ag_*)은 이 친구에서 지움. agent_turn.js 는 p.agent.rig 가 있는 친구를 건너뜀.
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..', '..');
const SRC = process.argv[2];
const cfgFile = SRC && fs.existsSync(path.join(SRC, '설정')) && fs.readdirSync(path.join(SRC, '설정')).find(f => /_조립설정\.json$/.test(f));
if (!cfgFile) { console.error('사용법: node intro/tools/add_agent_rig.js <친구_요원모드_최종파츠 폴더>'); process.exit(1); }
const win = { document: { currentScript: null }, performance: { now: () => 0 } };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'charo-pet.js'), 'utf8'), { window: win, document: win.document, performance: win.performance });
const CP = win.CharoPet;
const cfgRaw = fs.readFileSync(path.join(SRC, '설정', cfgFile)), CFG = JSON.parse(cfgRaw), R = CFG.engineRecipe, TL = CFG.timeline;
const F = path.join(ROOT, CFG.originalFront.projectFile), p = JSON.parse(fs.readFileSync(F, 'utf8'));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const PROPS = ['x', 'y', 'rot', 'sx', 'sy', 'op'];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
function sampleKeys(keys, t, k) {   // 자료 참고 코드(클로드용/*_요원리그.js)의 sampleKeys 와 같음: 키 사이 smoothstep
  if (!keys) return null;
  if (t <= keys[0].t) return keys[0][k];
  for (let i = 1; i < keys.length; i++) if (t <= keys[i].t) { let u = (t - keys[i - 1].t) / (keys[i].t - keys[i - 1].t); u = u * u * (3 - 2 * u); return keys[i - 1][k] + (keys[i][k] - keys[i - 1][k]) * u; }
  return keys[keys.length - 1][k];
}

// 0) 이전에 넣은 같은 리그 지우기(다시 돌려도 같게)
const PFX = R.partPrefix, RID = R.rootId;
p.parts = p.parts.filter(q => !q.id.startsWith(PFX));
for (const a of Object.keys(p.assets)) if (a.startsWith(PFX)) delete p.assets[a];
for (const c of p.clips) for (const id of Object.keys(c.tracks || {})) if (id.startsWith(PFX)) delete c.tracks[id];
if (p.mouse && p.mouse.base) for (const id of Object.keys(p.mouse.base)) if (id.startsWith(PFX)) delete p.mouse.base[id];
const originalIds = p.parts.map(q => q.id);

// 1) 그림 등록(sha256 확인) + 파츠 등록(자료 값 그대로)
for (const [asset, d] of Object.entries(R.assetFiles)) {
  const b = fs.readFileSync(path.join(SRC, d.file));
  if (sha(b) !== d.sha256) throw new Error('그림이 자료와 다름: ' + d.file);
  p.assets[asset] = 'data:image/png;base64,' + b.toString('base64');
}
for (const q of R.parts) p.parts.push(JSON.parse(JSON.stringify(q)));
const newIds = R.parts.map(q => q.id), part = id => CP.findPart(p, id);
const keyOf = {}; for (const id of newIds) keyOf[id] = id === RID ? 'root' : id.slice(PFX.length);   // gt_verified_arm_near → arm_near
const ANG = CFG.angles;   // [12,24,35] → img 0,1,2
for (const id of newIds) { const pt = part(id); if (pt.images.length && pt.images.length !== ANG.length) throw new Error(id + ' 그림 수가 각도 수와 다름'); }

// 2) 평소 모습(정면 단계에서 기존 파츠를 이 모습 그대로): 기본 동작 0초 + 로그인 대기(mouse.base), 키보드용(k_)·마우스 얼굴(m_)은 숨김
const baseOff = CP.offsetsFrom(p, CP.clipPose(p, CP.findClip(p, p.baseClip), 0));
for (const [id, b] of Object.entries((p.mouse && p.mouse.base) || {})) if (baseOff[id] && b.op != null) baseOff[id].op = b.op;
const idle = CP.finalPose(p, baseOff, null);
for (const id of originalIds) if (/^(k_|m_)/.test(id)) idle[id].op = 0;

// 3) 시각별 상태 → 자세
const STEPS = TL.turn.map(k => [k.t, k.angle]);   // [[0,0],[.15,12],[.3,24],[.45,35]]
const angleAt = (steps, t) => { let a = steps[0][1]; for (const [t0, v] of steps) if (t >= t0 - 1e-9) a = v; return a; };
const OUTS = {   // 복귀: 자료 참고 코드 sample(phase 'out') 와 같은 각도 단계
  '35g': { clip: 'ag_out', steps: [[0, 35], [0.14, 24], [0.28, 12], [0.42, 0]], glasses: 1 },
  '35': { clip: 'ag_out35', steps: [[0, 35], [0.14, 24], [0.28, 12], [0.42, 0]], glasses: 0 },
  '24': { clip: 'ag_out24', steps: [[0, 24], [0.14, 12], [0.28, 0]], glasses: 0 },
  '12': { clip: 'ag_out12', steps: [[0, 12], [0.28, 0]], glasses: 0 },
};
const GLASS_AT = TL.glassesOpacity.find((k, i, a) => i > 0 && k.v > 0 && a[i - 1].v === 0) ? TL.glassesOpacity.filter(k => k.v === 0).slice(-1)[0].t : 0.6;
// 시간표 키 → 움직일 파츠(자료 조립설정 timeline). 모르는 키가 있으면 멈춤(빠뜨리지 않게)
const MOTION = { rootLean: 'root', capeLag: 'cape', nearArm: 'arm_near', glassesNudge: 'glasses',   // 길통이
  hullLean: 'hull', nearWing: 'wing_near', farWing: 'wing_far' };                                     // 차로차로
// 대기(6초 반복, 3~4.8초에 약한 바람 한 번) — 자료 참고 코드(클로드용/*_요원리그.js) sample(phase 'hold') 의 값. 파츠 키: 회전 배율(도)
const HOLD = { gt_verified_: { root: 0.55, cape: -0.66 }, charo_verified_: { hull: 0.25, wing_near: 0.9, wing_far: -0.5 } };
const SKIP_TL = new Set(['duration', 'turn', 'glassesOpacity', 'outDuration', 'wheelMotion']);
for (const [k, v] of Object.entries(TL)) if (!SKIP_TL.has(k) && Array.isArray(v) && !MOTION[k]) throw new Error('시간표 키를 모름(도구에 추가 필요): ' + k);
if (!HOLD[PFX]) throw new Error('대기 바람 값을 모름(도구 HOLD 에 추가 필요): ' + PFX);
for (const k of Object.values(MOTION)) if (Object.keys(TL).some(t => MOTION[t] === k) && !Object.values(keyOf).includes(k)) throw new Error('시간표가 움직이는 파츠가 리그에 없음: ' + k);
function state(kind, t) {   // { angle, glasses, mv: { 파츠키: { rot, dy, scale } } }
  if (kind === 'in') {
    const mv = {};
    for (const [tk, pk] of Object.entries(MOTION)) if (TL[tk]) mv[pk] = { rot: sampleKeys(TL[tk], t, 'rot') || 0, dy: sampleKeys(TL[tk], t, 'dy') || 0, scale: TL[tk][0].scale != null ? sampleKeys(TL[tk], t, 'scale') : 1 };
    return { angle: angleAt(STEPS, t), glasses: sampleKeys(TL.glassesOpacity, t, 'v'), mv };
  }
  if (kind === 'hold') { const w = t % 6, v = w > 3 && w < 4.8 ? Math.sin((w - 3) / 1.8 * Math.PI * 2) : 0, mv = {}; for (const [pk, a] of Object.entries(HOLD[PFX])) mv[pk] = { rot: v * a, dy: 0, scale: 1 }; return { angle: 35, glasses: 1, mv }; }
  const o = OUTS[kind]; return { angle: angleAt(o.steps, t), glasses: o.glasses * (1 - clamp(t / 0.1, 0, 1)), mv: {} };   // 움직임은 재생기가 나가는 순간 자세에서 0.12초에 0으로 이어 붙임
}
function pose(kind, t) {
  const st = state(kind, t), on = st.angle !== 0, f = {};
  for (const q of p.parts) f[q.id] = Object.assign({}, q.rest, { img: q.rest.img || 0 });
  for (const id of originalIds) f[id].op = on ? 0 : idle[id].op;
  const ai = ANG.indexOf(st.angle);
  for (const id of newIds) {
    const q = f[id], k = keyOf[id]; q.op = on ? 1 : 0;
    if (part(id).images.length) q.img = on ? ai : 0;
    if (!on) continue;
    const m = st.mv[k]; if (m) { q.rot += m.rot; q.y += m.dy; q.sx *= m.scale; q.sy *= m.scale; }   // 같은 비율(sx=sy)만
    if (k === 'glasses') q.op = st.glasses;
  }
  return f;
}

// 4) 동작 만들기: 1/120초 + 단계 경계, 연속 값은 직선 키(허용 오차 안에서 줄임), 그림·숨김은 step
const TOL = { x: 0.05, y: 0.05, rot: 0.02, sx: 0.0005, sy: 0.0005, op: 0.003 };
function thin(keys, tol) {
  if (keys.length <= 2) return keys;
  const keep = new Array(keys.length).fill(false); keep[0] = keep[keys.length - 1] = true;
  (function rec(a, b) { let w = -1, wi = -1; for (let i = a + 1; i < b; i++) { const u = (keys[i].t - keys[a].t) / (keys[b].t - keys[a].t), d = Math.abs(keys[i].v - (keys[a].v + (keys[b].v - keys[a].v) * u)); if (d > w) { w = d; wi = i; } } if (w > tol) { keep[wi] = true; rec(a, wi); rec(wi, b); } })(0, keys.length - 1);
  return keys.filter((k, i) => keep[i]);
}
const val = (q, f, k) => (k === 'sx' || k === 'sy' || k === 'op') ? (q.rest[k] ? f[k] / q.rest[k] : 0) : f[k] - q.rest[k];
function makeClip(id, name, dur, kind, loop, cuts) {
  const ts = new Set([0, dur]); for (let i = 0; i <= Math.round(dur * 120); i++) ts.add(+(dur * i / Math.round(dur * 120)).toFixed(5));
  for (const c of cuts) if (c > 0 && c < dur) { ts.add(c); ts.add(+(c - 1e-4).toFixed(5)); }
  const tt = [...ts].sort((a, b) => a - b), fr = tt.map(t => ({ t, f: pose(kind, t) })), tracks = {};
  for (const q of p.parts) {
    const tr = {}, isNew = newIds.includes(q.id);
    for (const k of PROPS) {
      if (!isNew && k !== 'op') continue;   // 기존 파츠는 숨김/보임만(자세는 평소 그대로 둠)
      const raw = fr.map(({ t, f }) => ({ t: +t.toFixed(4), v: +val(q, f[q.id], k).toFixed(5) }));
      const flat = raw.every(r => Math.abs(r.v - raw[0].v) < 1e-6);
      if (flat) { if (k === 'op' || Math.abs(raw[0].v - (k === 'sx' || k === 'sy' ? 1 : 0)) > 1e-6) tr[k] = [{ t: 0, v: raw[0].v, e: 'step' }]; continue; }
      const stepLike = k === 'op' && !(isNew && keyOf[q.id] === 'glasses');
      if (stepLike) { const s = []; for (const r of raw) if (!s.length || Math.abs(s[s.length - 1].v - r.v) > 1e-6) s.push({ t: r.t, v: r.v, e: 'step' }); tr[k] = s; }
      else {   // 단계 경계에서 끊어 따로 줄임(경계 앞뒤가 섞이지 않게)
        const segs = []; let cur = [];
        raw.forEach((r, i) => { if (i && cuts.some(c => raw[i - 1].t < c && r.t >= c)) { segs.push(cur); cur = []; } cur.push(r); });
        segs.push(cur); tr[k] = [].concat(...segs.map(s => thin(s, TOL[k]))).map(r => ({ t: r.t, v: r.v, e: 'linear' }));
      }
    }
    if (isNew && q.images.length) { const im = []; for (const { t, f } of fr) if (!im.length || im[im.length - 1].v !== f[q.id].img) im.push({ t: +t.toFixed(4), v: f[q.id].img, f: 0 }); tr.img = im; }
    if (Object.keys(tr).length) tracks[q.id] = tr;
  }
  return { id, name, dur, loop, tracks };
}
const DUR = TL.duration, CUTS = STEPS.map(s => s[0]);
p.clips = p.clips.filter(c => !/^(src_)?ag_/.test(c.id));
p.preview = (p.preview || []).filter(x => !/^(src_)?ag_/.test(x.clip));
for (const c of p.clips) { c.tracks = c.tracks || {}; for (const id of newIds) c.tracks[id] = { op: [{ t: 0, v: 0, e: 'step' }] }; }   // 평소 동작: 새 리그 숨김만
const made = [
  makeClip('ag_in', '요원: 정면→12°→24°→35°·안경 고쳐 쓰기·차렷', DUR, 'in', false, CUTS.concat([GLASS_AT])),
  makeClip('ag_hold', '요원: 대기(조용히 섰다가 약한 바람 한 번, 6초 반복)', 6, 'hold', true, []),
];
for (const [key, o] of Object.entries(OUTS)) made.push(makeClip(o.clip, '요원 복귀(' + key + '): ' + o.steps.map(s => s[1] + '°').join('→'), o.steps[o.steps.length - 1][0], key, false, o.steps.map(s => s[0])));
for (const c of made) { p.clips.push(c); p.preview.push({ label: c.name, clip: c.id }); }
if (!p.mouse) p.mouse = {}; if (!p.mouse.base) p.mouse.base = {}; for (const id of newIds) p.mouse.base[id] = { op: 0 };
p.agent = {
  in: 'ag_in', hold: 'ag_hold', out: 'ag_out', ready: DUR, side: STEPS[1][0], version: 7,
  rig: { parts: newIds, steps: STEPS, glassesAt: GLASS_AT, outs: Object.fromEntries(Object.entries(OUTS).map(([k, o]) => [k, { clip: o.clip, steps: o.steps }])),
    resume: { '35g': 1.65, '35': STEPS[3][0], '24': STEPS[2][0], '12': STEPS[1][0], '0': 0 } },
  source: { package: path.basename(path.resolve(SRC)), configSHA256: sha(cfgRaw) },
};
fs.writeFileSync(F, JSON.stringify(p), 'utf8');
console.log(JSON.stringify({ file: CFG.originalFront.projectFile, newParts: newIds.length, images: Object.keys(R.assetFiles).length, clips: made.map(c => [c.id, c.dur, Object.keys(c.tracks).length]), glassesAt: GLASS_AT, fileKB: Math.round(fs.statSync(F).size / 1024) }));
