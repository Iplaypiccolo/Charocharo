// 무팔 티라 데이터 검사(엔진 수식 그대로 사용): 아랫몸통 고정, 물림점 일치, 층 배타, 불 꺼짐, 머리 한 장
global.window = global; global.document = { currentScript: null };
require('/home/claude/charo-pet.js'); const CP = window.CharoPet;
const P = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const RIG = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
const G = RIG.mouthGrip, HK = ['02', '03', '04', '05', '06'], G6 = G['06'];
const R = {}; const bad = (k, v) => { (R[k] = R[k] || []).length < 6 && R[k].push(v); };
function at(clip, t) { const off = CP.offsetsFrom(P, CP.clipPose(P, clip, t)); const fp = CP.finalPose(P, off, null); return { fp, W: CP.worldMatrices(P, fp) }; }
const intro = CP.findClip(P, 't_intro');
let ref = null, faces = new Set(), maxGap = 0, beatMove = 0, beatRef = null;
for (let t = 0; t <= intro.dur + 1e-9; t += 1 / 120) {
  const { fp, W } = at(intro, t);
  const hk = HK[fp.headImg.img]; if (['02', '03', '06'].includes(hk)) faces.add(hk);
  if (fp.headImg.mix < 1 && fp.headImg.prev !== fp.headImg.img) bad('head_two_layers', t.toFixed(3));
  // 아랫몸통 고정: 1.40~(들썩임 전 3.62) 동안 몸·발·꼬리·sway 행렬 불변
  if (t >= 1.15 && t <= 2.30) {
    const m = ['body', 'footL', 'footR', 'tail'].map(k => W[k].map(v => +v.toFixed(4)).join(',')).join('|');
    if (ref === null) ref = m; else if (m !== ref) bad('lower_body_moved', t.toFixed(3));
  }
  const vis = ['sign11B', 'sign11F', 'sign14'].filter(k => fp[k].op > 0.01);
  if (vis.length > 1) bad('two_signs', t.toFixed(3) + vis);
  if (vis.length && fp.fire.op > 0.01) bad('fire_while_biting', t.toFixed(3));
  if (fp.fire.op > 0.01 && !['02', '03'].includes(hk)) bad('fire_on_turned_head', t.toFixed(3));
  if (vis.length) {   // 팻말 물림점(정면물기 기준 G6를 bite 행렬로) == 현재 머리의 입 물림점(head 행렬로)
    const a = CP.apply(W.bite, G6[0], G6[1]), b = CP.apply(W.headImg, G[hk][0], G[hk][1]);
    const gap = Math.hypot(a[0] - b[0], a[1] - b[1]); const edge = Math.abs(t - Math.round(t * 100) / 100) <= 1e-5 && gap > 0.5; if (!edge) maxGap = Math.max(maxGap, gap); else R.boundary_frames = (R.boundary_frames || 0) + 1; if (gap > 0.5 && Math.abs(t - Math.round(t * 100) / 100) > 1e-5) bad('mouth_gap', [t.toFixed(3), hk, vis[0], gap.toFixed(1)]);
    if (hk === '02' || hk === '03') bad('sign_with_front_head', t.toFixed(3));
    if (vis[0] === 'sign14' && hk !== '06') bad('sign14_wrong_head', t.toFixed(3));
    if (fp.mask.op < 0.5 && vis[0] !== 'sign11B') bad('no_front_mask', t.toFixed(3));
  }
  if (fp.sign14.op > 0.5) { if (Math.abs(fp.sign14.rot) > 1e-6) bad('sign14_extra_rot', t); if (t >= 2.30 && Math.abs(fp.bite.rot) > 6) bad('sign_rot_big', [t.toFixed(2), fp.bite.rot.toFixed(1)]); }
  if (t >= 2.30 && t <= 2.55) { const s = JSON.stringify([fp.bite.rot.toFixed(3), fp.head.x, fp.head.rot, fp.sway.y.toFixed(2)]); if (beatRef === null) beatRef = s; else if (s !== beatRef) beatMove++; }
  if (t >= 2.30 && fp.sign14.op < 0.5) bad('sign_lost_after_present', t.toFixed(3));
}
R.faces = [...faces]; R.max_mouth_gap_world_px = +maxGap.toFixed(3); R.beat_frames_moving = beatMove;
const end = at(intro, intro.dur).fp; R.final = { head: HK[end.headImg.img], sign14: end.sign14.op, fire: end.fire.op, rot: end.bite.rot };
const red = CP.findClip(P, 't_intro_r'); const heads = new Set(); let redFire = 0, redSign = 1;
for (let t = 0; t <= red.dur; t += 0.05) { const { fp } = at(red, t); heads.add(HK[fp.headImg.img]); redFire = Math.max(redFire, fp.fire.op); redSign = Math.min(redSign, fp.sign14.op); }
R.reduced = { heads: [...heads], fire: redFire, sign14_min: redSign };
const idle = CP.findClip(P, 't_idle'); const fi = at(idle, 1.0).fp; R.idle_layers = ['sign11B', 'sign11F', 'sign14', 'mask', 'fire'].map(k => fi[k].op);
console.log(JSON.stringify(R, null, 1));
