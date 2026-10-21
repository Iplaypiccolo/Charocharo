#!/usr/bin/env node
/*
 * 비밀번호 요원 모드 넣기 (add_agent.js) — v2(2026-10-21): 40~45도 사선, 길통이·차로차로
 * 사용법: node intro/tools/add_agent.js <요원모드_v2_사선수정_경량자료 폴더>
 *
 * - 자료의 설정/추가파츠.json(작은 차이 정보)과 새이미지/ 4장만 읽음. 다시 쓰는 원본 그림(팔·다리·망토·날개)은 현재 파일의 것을 해시로 확인.
 * - 새 그림은 바이트 그대로 넣음: 머리·몸통은 기존 그림 목록 맨 뒤에 덧붙임(0번 기본 그림 그대로), drawRect 그대로 배치(늘이지 않음).
 * - 선글라스(공통 PNG 한 장): 캐릭터마다 다른 등록 행렬(pngToParentMatrix)을 그대로 씀. 이 재생기 방식에 맞게
 *   그림 영역 (0,0,1254,1254), 회전 중심 = 그림 가운데(627,627), 기본 자리 = 행렬로 옮긴 가운데, 회전·배율 = equivalentPose → 같은 행렬.
 *   파츠 k_agentGlasses(길통이 head 아래, 차로차로 body 아래). 다른 동작에서는 op 0.
 * - 요원 상태 자세: finalPoseOverrides 는 '최종값'(rest 에 더하는 값 아님) → 동작 키로 바꿀 때 rest 와의 차이로 환산.
 *   hideDuringAgent 파츠는 숨김. 앞뒤 순서 agentDrawOrder 는 p.agent.order 에 적어 두고 재생기가 요원 그림일 때만 씀.
 * - 시간표(전체 콘티): 0초 눈 감기(원래 정면 + 기존 감은 눈) → 0.42초 사선 그림·자세로 교체(눈·입 그림 포함된 새 그림, 기존 얼굴 숨김)
 *   → 0.8~1.18초 선글라스 착·작은 반동 → 바람 한 번(길통이 2.25초, 차로차로 2.33초; 소품은 늦게) → 4.6초마다 잔바람(1/3).
 *   나올 때 ag_out 0.42초: 선글라스를 위로 거둠(끝나면 재생기가 원래 얼굴·정면·순서로).
 * - 바닥: 프레임마다 발(길통이 다리)·바퀴(차로차로 몸통) 그림의 불투명 아랫부분이 기본 자세 때와 같은 높이가 되게 맞춤.
 * - 다시 돌려도 같은 결과(예전 v1·v2 요원 그림·k_agentGlasses·ag_ 동작을 먼저 지움).
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto'), cp = require('child_process');
const ROOT = path.resolve(__dirname, '..', '..');
const SRC = process.argv[2];
if (!SRC || !fs.existsSync(path.join(SRC, '설정', '추가파츠.json'))) { console.error('사용법: node intro/tools/add_agent.js <요원모드_v2 자료 폴더(설정/추가파츠.json 이 있는 곳)>'); process.exit(1); }
const win = { document: { currentScript: null }, performance: { now: () => 0 } };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'charo-pet.js'), 'utf8'), { window: win, document: win.document, performance: win.performance });
const CP = win.CharoPet;
const CFG = JSON.parse(fs.readFileSync(path.join(SRC, '설정', '추가파츠.json'), 'utf8'));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v)), ease = v => { v = clamp(v); return v * v * (3 - 2 * v); };
const bump = (t, a, b) => (t > a && t < b) ? Math.sin((t - a) / (b - a) * Math.PI) : 0;
// 그림의 불투명 범위(알파 > 16) — PIL 로 한 번에
function alphaBoxes(bufs) {
  const tmp = path.join(require('os').tmpdir(), 'agent_alpha_' + process.pid);
  fs.mkdirSync(tmp, { recursive: true });
  const files = Object.entries(bufs).map(([k, b]) => { const f = path.join(tmp, k + '.png'); fs.writeFileSync(f, b); return [k, f]; });
  const py = 'import sys,json\nfrom PIL import Image\no={}\nfor a in sys.argv[1:]:\n k,f=a.split("=",1); im=Image.open(f); A=im.getchannel("A").point(lambda v:255 if v>16 else 0); o[k]=[im.size,A.getbbox()]\nprint(json.dumps(o))';
  const out = JSON.parse(cp.execFileSync('python3', ['-c', py, ...files.map(([k, f]) => k + '=' + f)]).toString());
  fs.rmSync(tmp, { recursive: true, force: true });
  return out;
}
const TOL = { x: 0.15, y: 0.15, rot: 0.1, sx: 0.003, sy: 0.003, op: 0.003 }, DEF = { x: 0, y: 0, rot: 0, sx: 1, sy: 1, op: 1 };
function thin(keys, tol) {
  if (keys.length <= 2) return keys;
  const keep = new Array(keys.length).fill(false); keep[0] = keep[keys.length - 1] = true;
  (function rec(a, b) { let w = -1, wi = -1; for (let i = a + 1; i < b; i++) { const u = (keys[i].t - keys[a].t) / (keys[b].t - keys[a].t), d = Math.abs(keys[i].v - (keys[a].v + (keys[b].v - keys[a].v) * u)); if (d > w) { w = d; wi = i; } } if (w > tol) { keep[wi] = true; rec(a, wi); rec(wi, b); } })(0, keys.length - 1);
  return keys.filter((k, i) => keep[i]);
}

const JOBS = {
  giltong: { file: 'giltong/giltong.json', cfg: CFG.giltong, ground: ['legL', 'legR'], windAt: 2.25,
    closed: { eyeL: { img: 1 }, eyeR: { img: 1 }, browL: { op: 0 }, browR: { op: 0 } } },
  charocharo: { file: 'charo-pet.json', cfg: CFG.charocharo, ground: ['body'], windAt: 2.33,
    closed: { eyeL: { img: 2 }, eyeR: { img: 2 }, browL: { img: 2 }, browR: { img: 2 } } },
};
const report = {};
for (const [cid, J] of Object.entries(JOBS)) {
  const F = path.join(ROOT, J.file), p = JSON.parse(fs.readFileSync(F, 'utf8')), C = J.cfg, part = id => CP.findPart(p, id);
  // 0) 예전 것 지우기(v1 g_agent_*, v2 *_agent_v2_*)
  const old = k => /^g_agent_|_agent_v2_/.test(k);
  p.parts = p.parts.filter(x => x.id !== 'k_agentGlasses');
  for (const x of p.parts) x.images = x.images.filter(v => !old(v.asset));
  for (const k of Object.keys(p.assets)) if (old(k)) delete p.assets[k];
  p.clips = p.clips.filter(c => !c.id.startsWith('ag_'));
  for (const c of p.clips) delete c.tracks.k_agentGlasses;
  p.preview = (p.preview || []).filter(x => !x.clip.startsWith('ag_'));
  delete p.agent;
  // 1) 다시 쓰는 원본 그림 확인
  for (const r of C.reuses) {
    const pt = part(r.partId), v = pt && pt.images[r.imageIndex];
    if (!v || v.asset !== r.assetId) throw new Error(cid + ': ' + r.partId + ' 그림 ' + r.imageIndex + ' 이 ' + r.assetId + ' 가 아님');
    if (sha(Buffer.from(p.assets[r.assetId].split(',')[1], 'base64')) !== r.sha256) throw new Error(cid + ': 원본 그림이 자료와 다름 ' + r.assetId);
  }
  // 2) 새 그림
  const buf = k => { const a = CFG.assets[k], b = fs.readFileSync(path.join(SRC, a.file)); if (sha(b) !== a.sha256) throw new Error('새 그림 해시 다름: ' + a.file); return b; };
  const IDX = {};
  for (const [pid, v] of Object.entries(C.variants)) {
    p.assets[v.targetAssetId] = 'data:image/png;base64,' + buf(v.assetKey).toString('base64');
    const r = v.drawRect; part(pid).images.push({ asset: v.targetAssetId, name: '요원 v2: ' + pid, x: +r.x.toFixed(3), y: +r.y.toFixed(3), w: +r.w.toFixed(3), h: +r.h.toFixed(3) });
    IDX[pid] = part(pid).images.length - 1;
  }
  const G = C.glasses, M = G.pngToParentMatrix, E = G.equivalentPose;
  p.assets[G.targetAssetId] = 'data:image/png;base64,' + buf(G.assetKey).toString('base64');
  const piv = [627, 627], at = [M[0] * piv[0] + M[2] * piv[1] + M[4], M[1] * piv[0] + M[3] * piv[1] + M[5]];
  const glasses = { id: 'k_agentGlasses', name: '요원: 선글라스(' + G.parent + '에 붙음)', parent: G.parent, pivot: { x: piv[0], y: piv[1] },
    rest: { x: at[0], y: at[1], rot: E.rot, sx: E.sx, sy: E.sy, op: 1, img: 0 },
    images: [{ asset: G.targetAssetId, name: '요원: 선글라스', x: 0, y: 0, w: 1254, h: 1254 }], follow: { on: false, max: 0 } };
  const after = cid === 'giltong' ? 'mouth' : 'mouth';
  p.parts.splice(p.parts.findIndex(x => x.id === after) + 1, 0, glasses);
  { // 등록 행렬과 같은지 확인
    const L = CP.localM(glasses.rest, glasses.pivot); if (L.some((v, i) => Math.abs(v - M[i]) > 1e-3)) throw new Error(cid + ': 선글라스 행렬 환산 오류 ' + L);
  }
  for (const c of p.clips) c.tracks.k_agentGlasses = { op: [{ t: 0, v: 0, e: 'step' }, { t: +c.dur.toFixed(3), v: 0, e: 'step' }] };

  // 3) 바닥 기준: 발/바퀴 그림의 불투명 아랫부분 양 끝(가운데 쪽으로 15% 들임)
  const gAssets = {}; for (const id of J.ground) for (const v of part(id).images) gAssets[v.asset] = Buffer.from(p.assets[v.asset].split(',')[1], 'base64');
  const AB = alphaBoxes(gAssets);
  function floorOf(f) {
    const W = CP.worldMatrices(p, f); let y = -Infinity;
    for (const id of J.ground) {
      const v = part(id).images[f[id].img] || part(id).images[0], [sz, bb] = AB[v.asset], kx = v.w / sz[0], ky = v.h / sz[1];
      const x0 = v.x + bb[0] * kx, x1 = v.x + bb[2] * kx, yb = v.y + bb[3] * ky, inset = (x1 - x0) * 0.15;
      for (const x of [x0 + inset, x1 - inset]) y = Math.max(y, CP.apply(W[id], x, yb)[1]);
    }
    return y;
  }
  const baseClip = CP.findClip(p, p.baseClip), baseOff = CP.offsetsFrom(p, CP.clipPose(p, baseClip, 0));
  const target = floorOf(CP.finalPose(p, baseOff, null)), root = p.parts.find(x => !x.parent).id;

  // 4) 자세: 최종 자세(rest 포함)를 만들고 동작 키로 바꿈
  const hide = new Set(C.hideDuringAgent), O = C.finalPoseOverrides;
  function front(t) {   // 0~0.42: 원래 정면 + 기존 감은 눈(바로)
    const f = CP.finalPose(p, baseOff, null);
    for (const [id, v] of Object.entries(J.closed)) Object.assign(f[id], v);
    for (const x of p.parts) if (/^(m_|k_)/.test(x.id)) f[x.id].op = 0;
    if (cid === 'giltong') f.head.y += Math.sin(clamp((t - 0.2) / 0.42) * Math.PI) * 8;   // 짧은 끄덕임
    return f;
  }
  function agent(t, out) {   // 사선 요원. out: ag_out 진행(0~1)
    if (t < 0.42 && out == null) return front(t);
    const f = CP.finalPose(p, baseOff, null);
    for (const x of p.parts) { if (/^(m_|k_arm)/.test(x.id) || hide.has(x.id)) f[x.id].op = 0; }
    for (const [pid, i] of Object.entries(IDX)) f[pid].img = i;
    for (const [id, v] of Object.entries(O)) Object.assign(f[id], v);
    const g = f.k_agentGlasses, fall = ease((t - 0.8) / 0.38);
    g.op = t < 0.8 ? 0 : 1; g.y -= (1 - fall) * 160; g.y += bump(t, 1.18, 1.42) * 5;
    if (cid === 'giltong') f.head.y += t < 0.62 ? Math.sin(clamp((t - 0.2) / 0.42) * Math.PI) * 8 : 0;
    const w0 = J.windAt; let gust = 0, lag = 0, lag2 = 0;
    gust = bump(t, w0, w0 + 1.1); lag = bump(t, w0 + 0.15, w0 + 1.4); lag2 = bump(t, w0 + 0.22, w0 + 1.47);
    if (t >= w0 + 1.4) { const q = (t - (w0 + 1.4)) * Math.PI * 2 / 4.6; gust = 0.23 * Math.sin(q); lag = 0.32 * Math.sin(q - 0.32); lag2 = 0.3 * Math.sin(q - 0.45); }
    if (out != null) { const k = 1 - ease(out); gust *= k; lag *= k; lag2 *= k; g.y -= ease(out / 0.8) * 160; g.op = 1 - ease((out - 0.25) / 0.5); }
    if (cid === 'giltong') { f.body.rot += 1.6 * gust; f.head.rot += -0.75 * gust; f.cape.rot += -10 * lag; f.armL.rot -= 0.8 * lag; f.armR.rot -= 0.8 * lag; }
    else { f.body.rot += 1.8 * gust; f.wingL.rot += 6 * lag; f.wingR.rot += 4.5 * lag2; }
    return f;
  }
  function grounded(f) { f[root].y += target - floorOf(f); return f; }
  function clip(id, name, dur, loop, fn) {
    const n = Math.round(dur * 120), fr = [];
    for (let i = 0; i <= n; i++) fr.push({ t: +(dur * i / n).toFixed(4), f: grounded(fn(dur * i / n)) });
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
  const IN = J.windAt + 1.4, HOLD = 4.6, OUT = 0.42;
  const made = [
    clip('ag_in', '요원: 비밀번호 — 눈 감기·사선·선글라스 착·바람', +IN.toFixed(2), false, t => agent(t)),
    clip('ag_hold', '요원: 경계(잔바람, 반복)', HOLD, true, t => agent(IN + t)),
    clip('ag_out', '요원: 선글라스 거두고 복귀', OUT, false, t => agent(IN, t / OUT)),
  ];
  for (const c of made) { p.clips.push(c); p.preview.push({ label: c.name, clip: c.id }); }
  p.agent = { in: 'ag_in', hold: 'ag_hold', out: 'ag_out', ready: 1.42, side: 0.42, order: C.agentDrawOrder, version: 2 };
  fs.writeFileSync(F, JSON.stringify(p), 'utf8');
  report[cid] = { images: IDX, glasses: glasses.rest, clips: made.map(c => [c.id, c.dur, Math.round(JSON.stringify(c).length / 1024) + 'KB']), fileKB: Math.round(fs.statSync(F).size / 1024) };
}
console.log(JSON.stringify(report));
