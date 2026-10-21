#!/usr/bin/env node
/*
 * 비밀번호 요원 모드 v4 (add_agent_v4.js) — 2026-10-21 '여섯친구_요원모드_35도_수평카메라' 자료: 여섯 친구를 같은 카메라(35도 3/4, 고개 5도)로 교체
 * 사용법: node intro/tools/add_agent_v4.js <여섯친구_요원모드_35도_수평카메라 폴더>
 *
 * - 친구마다 설정/추가파츠.json 의 variants(새 그림)를 해당 파츠 그림 목록 맨 뒤에 덧붙임(기존 0번·예전 요원 그림은 그대로 둠).
 *   newPart(차로차로 k_cameraWheelL·R)는 새 파츠로 만들고 다른 모든 동작에서는 op 0(이름이 k_ 라 재생기도 요원 동작 때만 보임).
 *   새 그림은 바이트 그대로(해시 확인), drawRect 그대로. 다시 쓰는 원본(reuses)은 해시 확인.
 * - 동작: 클립 길이·순서는 지금 것(ag_in·ag_hold·ag_out) 그대로. 자료 지시대로
 *     '정적 새 자세 + (지금 동작 값 − 지금 정적 값)'(배율은 비율)로 다시 만듦.
 *   지금 정적 값 = 지금 ag_in 의 조용한 순간(선글라스 안착 뒤·바람 전, REF) 자세. 정적 새 자세 = 기본 자세 + finalPoseOverrides(최종값).
 *   0.42초 전(정면에서 눈 감기)은 지금 그대로. 그 뒤는 새 그림 번호·hideDuringAgent 숨김·새 파츠 보이기, 선글라스 투명도(착·거두기)는 지금 것.
 * - 바닥: 프레임마다 supportParts 그림의 불투명 아랫부분(양 끝 15% 들임)의 가장 낮은 점을 기본 자세의 바닥 높이에 맞춤(친구마다 정한 부품의 y 를 보정).
 * - p.agent = 지금 설정 + targetAgent(그리는 순서·버전, 티라는 반짝 위치).
 * - 다시 돌려도 같은 결과(cam4_ 그림·k_camera 파츠를 지우고 다시 넣음; 동작은 차이만 쓰므로 같아짐).
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto'), cp = require('child_process'), os = require('os');
const ROOT = path.resolve(__dirname, '..', '..');
const PKG = process.argv[2];
if (!PKG || !fs.existsSync(path.join(PKG, '캐릭터목록.json'))) { console.error('사용법: node intro/tools/add_agent_v4.js <여섯친구_요원모드_35도_수평카메라 폴더>'); process.exit(1); }
const win = { document: { currentScript: null }, performance: { now: () => 0 } };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'charo-pet.js'), 'utf8'), { window: win, document: win.document, performance: win.performance });
const CP = win.CharoPet;
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
// 친구별: 지금 정적 순간(REF), 바닥을 맞출 때 움직이는 부품(GP), 기본 자세의 바닥 부품(BASE)
const PER = {
  giltong: { REF: 2.0, GP: 'body', BASE: ['legL', 'legR'] },
  charocharo: { REF: 2.0, GP: 'body', BASE: ['body'] },
  tira: { REF: 2.0, GP: 'sway', BASE: ['footL', 'footR'] },
  chumdani: { REF: 2.2, GP: 'body', BASE: ['wheelL', 'wheelR'] },
  tarotaro: { REF: 2.0, GP: 'body', BASE: ['wheelL', 'wheelR'] },
  doroduck: { REF: 2.0, GP: 'body', BASE: ['footL', 'footR'] },
};
const ab = {};   // 그림 불투명 범위 캐시
function alphaBox(p, asset) {
  if (ab[asset]) return ab[asset];
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ab')), f = path.join(tmp, 'a.png');
  fs.writeFileSync(f, Buffer.from(p.assets[asset].split(',')[1], 'base64'));
  const out = JSON.parse(cp.execFileSync('python3', ['-c', 'import sys,json\nfrom PIL import Image\nim=Image.open(sys.argv[1]);A=im.getchannel("A").point(lambda v:255 if v>16 else 0);print(json.dumps([im.size,A.getbbox()]))', f]).toString());
  fs.rmSync(tmp, { recursive: true, force: true });
  return (ab[asset] = out);
}
const TOL = { x: 0.15, y: 0.15, rot: 0.1, sx: 0.003, sy: 0.003, op: 0.003 }, DEF = { x: 0, y: 0, rot: 0, sx: 1, sy: 1, op: 1 };
function thin(keys, tol) {
  if (keys.length <= 2) return keys;
  const keep = new Array(keys.length).fill(false); keep[0] = keep[keys.length - 1] = true;
  (function rec(a, b) { let w = -1, wi = -1; for (let i = a + 1; i < b; i++) { const u = (keys[i].t - keys[a].t) / (keys[b].t - keys[a].t), d = Math.abs(keys[i].v - (keys[a].v + (keys[b].v - keys[a].v) * u)); if (d > w) { w = d; wi = i; } } if (w > tol) { keep[wi] = true; rec(a, wi); rec(wi, b); } })(0, keys.length - 1);
  return keys.filter((k, i) => keep[i]);
}
const list = JSON.parse(fs.readFileSync(path.join(PKG, '캐릭터목록.json'), 'utf8'));
const report = {};
for (const ch of list) {
  const DIR = path.join(PKG, ch.folder), CFG = JSON.parse(fs.readFileSync(path.join(DIR, '설정', '추가파츠.json'), 'utf8')), K = PER[CFG.characterId];
  if (!K) throw new Error('모르는 친구 ' + CFG.characterId);
  const F = path.join(ROOT, CFG.projectFile), p = JSON.parse(fs.readFileSync(F, 'utf8'));
  // 0) 예전 v4 지우기
  p.parts = p.parts.filter(x => !/^k_camera/.test(x.id));
  for (const x of p.parts) x.images = x.images.filter(v => !/^cam4_/.test(v.asset));
  for (const k of Object.keys(p.assets)) if (/^cam4_/.test(k)) delete p.assets[k];
  for (const c of p.clips) for (const k of Object.keys(c.tracks)) if (/^k_camera/.test(k)) delete c.tracks[k];
  const OLD = JSON.parse(JSON.stringify(p)), part = id => CP.findPart(p, id);   // 지금 동작을 읽을 사본
  if (!p.agent || !CP.findClip(p, p.agent.in)) throw new Error(CFG.characterId + ': 지금 요원 동작이 없음');
  // 1) 확인: 다시 쓰는 원본, 파츠 부모·피벗
  for (const r of CFG.reuses) { const v = part(r.partId).images[r.imageIndex]; if (!v || v.asset !== r.assetId || sha(Buffer.from(p.assets[r.assetId].split(',')[1], 'base64')) !== r.sha256) throw new Error(CFG.characterId + ': 원본 그림 다름 ' + r.assetId); }
  // 2) 새 그림·새 파츠
  const IDX = {}, NEWP = [];
  for (const v of CFG.variants) {
    const a = CFG.assets[v.key], buf = fs.readFileSync(path.join(DIR, a.file));
    if (sha(buf) !== a.sha256) throw new Error('새 그림 해시 다름 ' + a.file);
    p.assets[a.assetId] = 'data:image/png;base64,' + buf.toString('base64');
    let pt = part(v.partId);
    if (v.newPart) {
      if (pt) throw new Error('이미 있는 파츠 ' + v.partId);
      pt = { id: v.partId, name: '요원: ' + v.partId, parent: v.parent, pivot: { ...v.pivot }, rest: { x: v.pivot.x, y: v.pivot.y, rot: 0, sx: 1, sy: 1, op: 1, img: 0 }, images: [], follow: { on: false, max: 0 } };
      const bi = p.parts.findIndex(x => x.id === v.parent); p.parts.splice(bi, 0, pt); NEWP.push(v.partId);
    } else {
      if ((pt.parent || null) !== (v.parent || null) || Math.abs(pt.pivot.x - v.pivot.x) > 1e-6 || Math.abs(pt.pivot.y - v.pivot.y) > 1e-6) throw new Error(CFG.characterId + ': ' + v.partId + ' 부모/피벗이 자료와 다름');
    }
    const r = v.drawRect; pt.images.push({ asset: a.assetId, name: '요원 35도: ' + v.key, x: r.x, y: r.y, w: r.w, h: r.h });
    IDX[v.partId] = pt.images.length - 1;
  }
  for (const c of p.clips) if (!c.id.startsWith('ag_')) for (const id of NEWP) c.tracks[id] = { op: [{ t: 0, v: 0, e: 'step' }, { t: +c.dur.toFixed(3), v: 0, e: 'step' }] };
  // 3) 자세 계산 도구
  const baseOffOld = CP.offsetsFrom(OLD, CP.clipPose(OLD, CP.findClip(OLD, OLD.baseClip), 0));
  function oldPose(clipId, t) {   // 지금 동작의 최종 자세(재생기와 같이: 대기 자세 위에 키 있는 속성만 덮어씀)
    const off = JSON.parse(JSON.stringify(baseOffOld)), pose = CP.clipPose(OLD, CP.findClip(OLD, clipId), t);
    for (const id in pose) { const q = pose[id], o = off[id]; if (!o) continue; for (const k of CP.PROPS) if (q[k] != null) o[k] = q[k]; if (q.img) o.img = q.img; }
    return CP.finalPose(OLD, off, null);
  }
  const baseOff = CP.offsetsFrom(p, CP.clipPose(p, CP.findClip(p, p.baseClip), 0));
  function floorOf(f, ids) {
    const W = CP.worldMatrices(p, f); let y = -Infinity;
    for (const id of ids) {
      const pt = part(id), v = pt.images[f[id].img] || pt.images[0], [sz, bb] = alphaBox(p, v.asset), kx = v.w / sz[0], ky = v.h / sz[1];
      const x0 = v.x + bb[0] * kx, x1 = v.x + bb[2] * kx, yb = v.y + bb[3] * ky, inset = (x1 - x0) * 0.15;
      for (const x of [x0 + inset, x1 - inset]) y = Math.max(y, CP.apply(W[id], x, yb)[1]);
    }
    return y;
  }
  const target = floorOf(CP.finalPose(p, baseOff, null), K.BASE);
  const hide = new Set(CFG.hideDuringAgent), O = CFG.finalPoseOverrides;
  const S = CP.finalPose(p, baseOff, null);   // 정적 새 자세
  for (const [id, v] of Object.entries(O)) if (S[id]) Object.assign(S[id], v);
  const REF = oldPose(OLD.agent.in, K.REF), side = OLD.agent.side || 0.42;
  function compose(clipId, t, isSide) {
    const fo = oldPose(clipId, t);
    if (!isSide) { const f = CP.finalPose(p, baseOff, null); for (const id in fo) if (f[id]) Object.assign(f[id], fo[id]); for (const id of NEWP) f[id].op = 0; return f; }
    const f = CP.finalPose(p, baseOff, null);
    for (const x of p.parts) {
      const id = x.id, s = S[id], o = fo[id], r = REF[id], n = f[id];
      if (!o) { Object.assign(n, s); n.img = IDX[id] || 0; n.op = 1; continue; }   // 새 파츠(차로차로 요원 바퀴): 기본 자세에선 숨김이라 여기서 켬
      for (const k of ['x', 'y', 'rot']) n[k] = s[k] + (o[k] - r[k]);
      for (const k of ['sx', 'sy']) n[k] = s[k] * (r[k] ? o[k] / r[k] : 1);
      n.img = id in IDX ? IDX[id] : o.img;
      n.op = hide.has(id) ? 0 : id === 'k_agentGlasses' ? o.op : (id in IDX) ? 1 : o.op;
      if (/^m_|^k_arm/.test(id)) n.op = 0;
    }
    for (let i = 0; i < 2; i++) { const par = part(K.GP).parent, ky = par ? CP.worldMatrices(p, f)[par][3] : 1; f[K.GP].y += (target - floorOf(f, CFG.supportParts)) / ky; }   // 수평 바닥
    return f;
  }
  function clip(id, name, dur, loop, fn) {
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
        const im = []; let last = null; for (const { t, f } of fr) { const v = f[x.id].img; if (v !== last) { im.push({ t, v, f: 0 }); last = v; } }
        if (!(im.length === 1 && im[0].v === (r.img || 0))) tr.img = im;
      }
      if (Object.keys(tr).length) tracks[x.id] = tr;
    }
    return { id, name, dur, loop, tracks };
  }
  const A = OLD.agent, made = [];
  for (const [cid, isIn] of [[A.in, true], [A.hold, false], [A.out, false]]) {
    const old = CP.findClip(OLD, cid);
    made.push(clip(cid, old.name.replace(/^요원:/, '요원(35도):'), old.dur, !!old.loop, t => compose(cid, t, !isIn || t >= side)));
  }
  p.clips = p.clips.filter(c => !c.id.startsWith('ag_')).concat(made);
  const keep = CFG.keepClipTiming; for (const c of made) if (keep[c.id] != null && Math.abs(keep[c.id] - c.dur) > 0.011) throw new Error(CFG.characterId + ': 클립 길이 ' + c.id + ' ' + c.dur + ' ≠ ' + keep[c.id]);
  p.agent = Object.assign({}, A, CFG.targetAgent); delete p.agent.bury; delete p.agent.puffs;
  fs.writeFileSync(F, JSON.stringify(p), 'utf8');
  report[CFG.characterId] = { images: IDX, newParts: NEWP, clips: made.map(c => [c.id, c.dur]), fileKB: Math.round(fs.statSync(F).size / 1024) };
}
console.log(JSON.stringify(report, null, 0));
