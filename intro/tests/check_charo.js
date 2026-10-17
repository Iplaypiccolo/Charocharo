// 차로차로 인트로 동작 데이터 검사(재생기 수식 그대로). 실행: node intro/tests/check_charo.js charo-pet.json
global.window = global; global.document = { currentScript: null };
require(require('path').resolve(__dirname, '../../charo-pet.js')); const CP = window.CharoPet;
const P = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const C = CP.findClip(P, 'i_charo'), R = {}, bad = (k, v) => { (R[k] = R[k] || []).length < 5 && R[k].push(v); };
const FACE = ['eyeL', 'eyeR', 'browL', 'browR', 'mouth'];
const fk = id => { const f = P.faces.find(x => x.id === id); return FACE.map(k => f.img[k]).join(','); }, KA = fk('f00'), KB = fk('f22');   // 표정 A·B 그림 번호(데이터에서)
const at = t => CP.finalPose(P, CP.offsetsFrom(P, CP.clipPose(P, C, t)), null);
const rest = {}; P.parts.forEach(p => rest[p.id] = p.rest);
let prev = null, faceSeq = [], firstAir = null, maxSlowWing = 0, maxFastWing = 0, scaleOut = [], tiraMax = { y: 0, wing: 0 }, flipMax = { y: 0, rot: 0, wing: 0 };
const dt = 1 / 240;
for (let t = 0; t <= C.dur + 1e-9; t += dt) {
  const f = at(t), imgs = FACE.map(k => f[k].img), key = imgs.join(',');
  if (!(key === KA || key === KB)) bad('face_mixed', [t.toFixed(3), key]);
  if (FACE.some(k => f[k].mix < 1 && f[k].prev !== f[k].img)) bad('face_fade', t.toFixed(3));
  if (!faceSeq.length || faceSeq[faceSeq.length - 1][1] !== key) faceSeq.push([+t.toFixed(3), key]);
  const y = f.body.y - rest.body.y;
  if (t > 2.05 && firstAir === null && y < -0.05) firstAir = +t.toFixed(3);
  if (prev) {
    const wv = Math.max(Math.abs(f.wingL.rot - prev.wingL.rot), Math.abs(f.wingR.rot - prev.wingR.rot)) / dt;
    if (t > 2.37 && t < 3.85) maxSlowWing = Math.max(maxSlowWing, wv);
    if (t > 2.14 && t < 2.28) maxFastWing = Math.max(maxFastWing, wv);
  }
  const sy = f.body.sy / rest.body.sy, sx = f.body.sx / rest.body.sx;
  const key_moment = (t > 2.05 && t < 2.30) || (t > 4.08 && t < 4.17);
  if (!key_moment && (Math.abs(sy - 1) > 0.05 + 1e-6 || Math.abs(sx - 1) > 0.05 + 1e-6)) scaleOut.push([+t.toFixed(3), +sy.toFixed(3), +sx.toFixed(3)]);
  if (Math.abs(sy - 1) > 0.10 + 1e-6 || Math.abs(sx - 1) > 0.10 + 1e-6) bad('scale_over_10', [t.toFixed(3), sy, sx]);
  if (t >= 1.15 && t < 1.98) { tiraMax.y = Math.max(tiraMax.y, Math.abs(y)); tiraMax.wing = Math.max(tiraMax.wing, Math.abs(f.wingL.rot - rest.wingL.rot), Math.abs(f.wingR.rot - rest.wingR.rot)); }
  if (t >= 4.31 && t <= 5.10) { flipMax.y = Math.max(flipMax.y, Math.abs(y)); flipMax.rot = Math.max(flipMax.rot, Math.abs(f.body.rot)); flipMax.wing = Math.max(flipMax.wing, Math.abs(f.wingL.rot - rest.wingL.rot), Math.abs(f.wingR.rot - rest.wingR.rot)); }
  prev = f;
}
const H = P.parts.find(p => p.id === 'body').images[0].h * rest.body.sy;
let apex = 0, apexT = 0; for (let t = 2.1; t < 4.0; t += 0.005) { const y = -(at(t).body.y - rest.body.y); if (y > apex) { apex = y; apexT = t; } }
const end = at(C.dur), breath0 = CP.finalPose(P, CP.offsetsFrom(P, CP.clipPose(P, CP.findClip(P, 'c_breath'), 0)), null);
let endDiff = 0; for (const id in end) for (const k of ['x', 'y', 'rot', 'sx', 'sy', 'op']) endDiff = Math.max(endDiff, Math.abs(end[id][k] - breath0[id][k]));
Object.assign(R, { faceSeq, firstAir, faceB_at: 2.12, maxFastWing_dps: Math.round(maxFastWing), maxSlowWing_dps: Math.round(maxSlowWing),
  jump_apex_px: +apex.toFixed(1), jump_apex_ratio_H: +(apex / H).toFixed(3), apex_t: +apexT.toFixed(2), scale_outside_095_105: scaleOut.length ? scaleOut.slice(0, 4) : 'none',
  tira_window_max: { y: +tiraMax.y.toFixed(1), wing_deg: +tiraMax.wing.toFixed(1) }, flip_window_max: { y: +flipMax.y.toFixed(1), rot: +flipMax.rot.toFixed(1), wing_deg: +flipMax.wing.toFixed(1) },
  end_vs_breath0_maxdiff: +endDiff.toFixed(6) });
console.log(JSON.stringify(R, null, 1));
