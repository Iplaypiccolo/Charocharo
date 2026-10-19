#!/usr/bin/env node
/*
 * 로그인 화면 키보드 반응 클립 넣기 (add_keys.js)
 * 사용법: node intro/tools/add_keys.js <여섯캐릭터_키보드액션 폴더>
 *
 * - 각 폴더의 '키보드_클립만.json'(kb_type·kb_echo·kb_private_in·kb_private_hold·kb_private_out)을 현재 캐릭터 파일에 합칩니다.
 *   원본 그림·파츠·피벗·기본 자세는 건드리지 않습니다(자료의 원본과 현재 파일이 같음을 먼저 확인).
 * - 1/120초마다 적힌 키를 '직선으로 이어지는 중간 키'만 빼서 줄입니다(허용 오차: 회전 0.15도, 위치 0.15, 배율·투명도 0.003 — 로그인 화면 크기(키 70~150px)에서 1px 의 수십 분의 1).
 *   변하지 않고 기본값(위치 0·배율 1·투명 1)과 같은 속성은 뺍니다 → 대기 자세·마우스용 기본 설정이 그대로 살아 있음.
 * - 마우스용 m_ 파츠는 키보드 동작 중 보이지 않게 op 0 키를 넣습니다(재생기에서도 따로 끔).
 * - 길통이: 비밀번호 때 원통팔을 볼 앞에 → 원본 팔 그림을 그대로 쓰는 k_armLTop·k_armRTop 파츠(머리 다음에 그림)에
 *   clip(몸통 좌표의 얼굴 영역)을 걸어 '얼굴 앞 부분만' 다시 그림. 새 그림 없음. 다른 동작에서는 op 0.
 * - 다시 돌려도 같은 결과(예전에 넣은 kb_ 클립·k_ 파츠를 먼저 지움).
 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.resolve(__dirname, '..', '..');
const SRC = process.argv[2];
if (!SRC) { console.error('사용법: node intro/tools/add_keys.js <여섯캐릭터_키보드액션 폴더>'); process.exit(1); }
const win = { document: { currentScript: null }, performance: { now: () => 0 } };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'charo-pet.js'), 'utf8'), { window: win, document: win.document, performance: win.performance });
const CP = win.CharoPet;

const MAP = {
  giltong: ['01_길통이', 'giltong/giltong.json'],
  charocharo: ['02_차로차로', 'charo-pet.json'],
  tira: ['03_티라', 'tira_v3/tira_v3.json'],
  chumdani: ['04_첨다니', 'chumdani/chumdani.json'],
  doroduck: ['05_도로덕', 'doroduck/doroduck.json'],
  tarotaro: ['06_타로타로', 'tarotaro/tarotaro.json'],
};
// 키보드 동작 중 마우스용 기본 설정(p.mouse.base)을 되돌릴 파츠: 타로타로는 마우스용 눈 대신 원래 눈 그림을 씀
const UNBASE = { tarotaro: { eyes: { op: 1 } } };
const TOL = { x: 0.15, y: 0.15, rot: 0.15, sx: 0.003, sy: 0.003, op: 0.003 };
const DEF = { x: 0, y: 0, rot: 0, sx: 1, sy: 1, op: 1 };

function thin(keys, tol) {   // 직선 보간으로 tol 안에 들어오는 중간 키 제거(Ramer–Douglas–Peucker)
  if (keys.length <= 2) return keys;
  const keep = new Array(keys.length).fill(false); keep[0] = keep[keys.length - 1] = true;
  (function rec(a, b) {
    let worst = -1, wi = -1;
    for (let i = a + 1; i < b; i++) {
      const u = (keys[i].t - keys[a].t) / (keys[b].t - keys[a].t), v = keys[a].v + (keys[b].v - keys[a].v) * u, d = Math.abs(keys[i].v - v);
      if (d > worst) { worst = d; wi = i; }
    }
    if (worst > tol) { keep[wi] = true; rec(a, wi); rec(wi, b); }
  })(0, keys.length - 1);
  return keys.filter((k, i) => keep[i]).map(k => ({ t: +k.t.toFixed(4), v: +k.v.toFixed(4), e: 'linear' }));
}

function strip(p) {
  p.parts = p.parts.filter(x => !x.id.startsWith('k_'));
  p.clips = p.clips.filter(c => !c.id.startsWith('kb_'));
  for (const c of p.clips) for (const k of Object.keys(c.tracks)) if (k.startsWith('k_')) delete c.tracks[k];
  p.preview = (p.preview || []).filter(x => !x.clip.startsWith('kb_'));
}

const report = {};
for (const [id, [dir, file]] of Object.entries(MAP)) {
  const f = path.join(ROOT, file), p = JSON.parse(fs.readFileSync(f, 'utf8'));
  const orig = JSON.parse(fs.readFileSync(path.join(SRC, dir, '원본_캐릭터.json'), 'utf8'));
  const kb = JSON.parse(fs.readFileSync(path.join(SRC, dir, '키보드_클립만.json'), 'utf8'));
  strip(p);
  // 1) 원본 대조: 파츠 이름·부모·피벗·기본 자세·그림 자리가 같아야 함
  for (const o of orig.parts) {
    const c = CP.findPart(p, o.id);
    if (!c) throw new Error(id + ': 현재 파일에 없는 파츠 ' + o.id);
    for (const k of ['parent', 'pivot', 'rest']) if (JSON.stringify(o[k]) !== JSON.stringify(c[k])) throw new Error(id + ': ' + o.id + ' 의 ' + k + ' 가 다름');
    o.images.forEach((v, i) => { const w = c.images[i]; if (!w || ['asset', 'x', 'y', 'w', 'h'].some(k => v[k] !== w[k])) throw new Error(id + ': ' + o.id + ' 그림 ' + i + ' 다름'); });
    for (const v of o.images) if (orig.assets[v.asset] !== p.assets[v.asset]) throw new Error(id + ': 그림 파일 ' + v.asset + ' 다름');
  }
  // 2) 길통이 볼 앞 팔 파츠
  const extra = [];
  if (id === 'giltong') {
    const hi = p.parts.findIndex(x => x.id === 'head');
    const top = ['armL', 'armR'].map(a => {
      const s = CP.findPart(p, a);
      return { id: 'k_' + a + 'Top', name: '키보드: ' + (a === 'armL' ? '왼' : '오른') + '팔 얼굴 앞 부분(원본 팔 그림, 얼굴 영역만)', parent: s.parent,
        pivot: { ...s.pivot }, rest: { ...s.rest }, images: s.images.map(v => ({ ...v })), follow: { on: false, max: 0 },
        clip: { part: 'body', rect: [180, 100, 900, 690] } };
    });
    p.parts.splice(hi + 1, 0, ...top);
    extra.push('k_armLTop', 'k_armRTop');
    for (const c of p.clips) for (const k of extra) c.tracks[k] = { op: [{ t: 0, v: 0, e: 'step' }, { t: +c.dur.toFixed(3), v: 0, e: 'step' }] };
  }
  // 3) 클립 줄이기·합치기
  const mParts = p.parts.filter(x => x.id.startsWith('m_')).map(x => x.id);
  let keysIn = 0, keysOut = 0;
  for (const c0 of kb.clips) {
    if (CP.findClip(p, c0.id)) throw new Error(id + ': 클립 이름 겹침 ' + c0.id);
    const c = { id: c0.id, name: c0.name, dur: c0.dur, loop: !!c0.loop, tracks: {} };
    for (const [pid, tr] of Object.entries(c0.tracks)) {
      const part = CP.findPart(p, pid); if (!part) throw new Error(id + ': 없는 파츠 ' + pid);
      const out = {};
      for (const k of Object.keys(TOL)) {
        const keys = tr[k]; if (!keys || !keys.length) continue;
        keysIn += keys.length;
        const flat = keys.every(q => Math.abs(q.v - keys[0].v) < 1e-6);
        if (flat && Math.abs(keys[0].v - DEF[k]) < 1e-6) continue;
        out[k] = flat ? [{ t: 0, v: +keys[0].v.toFixed(4), e: 'linear' }] : thin(keys, TOL[k]);
        keysOut += out[k].length;
      }
      if (tr.img && tr.img.length && !(tr.img.length === 1 && tr.img[0].v === (part.rest.img || 0))) out.img = tr.img.map(q => ({ t: +q.t.toFixed(4), v: q.v, f: 0 }));
      if (Object.keys(out).length) c.tracks[pid] = out;
    }
    for (const m of mParts) c.tracks[m] = { op: [{ t: 0, v: 0, e: 'step' }, { t: c.dur, v: 0, e: 'step' }] };
    if (id === 'giltong') {   // 볼 앞 팔: 원본 팔과 같은 움직임, 비밀번호 동작에서 팔이 올라가기 시작하면 보임
      const fg = c.id === 'kb_private_in' ? 0.01 : c.id === 'kb_private_hold' ? 0 : c.id === 'kb_private_out' ? 'out' : null;
      for (const a of ['armL', 'armR']) {
        const t = { ...(c.tracks[a] || {}) };
        if (fg === null) t.op = [{ t: 0, v: 0, e: 'step' }, { t: c.dur, v: 0, e: 'step' }];
        else if (fg === 'out') t.op = [{ t: 0, v: 1, e: 'step' }, { t: +(c.dur - 0.01).toFixed(3), v: 0, e: 'step' }, { t: c.dur, v: 0, e: 'step' }];
        else if (fg === 0) t.op = [{ t: 0, v: 1, e: 'step' }, { t: c.dur, v: 1, e: 'step' }];
        else t.op = [{ t: 0, v: 0, e: 'step' }, { t: fg, v: 1, e: 'step' }, { t: c.dur, v: 1, e: 'step' }];
        delete t.img;
        c.tracks['k_' + a + 'Top'] = t;
      }
    }
    p.clips.push(c);
    p.preview = p.preview || []; p.preview.push({ label: '키보드: ' + c.name, clip: c.id });
  }
  p.keys = { unbase: UNBASE[id] || {} };
  fs.writeFileSync(f, JSON.stringify(p), 'utf8');
  report[id] = { keysIn, keysOut, kb: Math.round(JSON.stringify(p.clips.filter(c => c.id.startsWith('kb_'))).length / 1024) };
}
console.log(JSON.stringify(report, null, 1));
