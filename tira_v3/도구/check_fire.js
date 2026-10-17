// 불꽃 뿌리 검사: 불이 보이는 모든 프레임에서 그려진 뿌리(작은 불·큰 불 모두 같은 점)가 머리의 입 지점과 같은 자리인지
global.window = global; global.document = { currentScript: null };
require('/home/claude/charo-pet.js'); const CP = window.CharoPet;
const P = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const fire = P.parts.find(p => p.id === 'fire'), RP = [fire.pivot.x, fire.pivot.y];
const C = CP.findClip(P, 't_intro'); let max = 0, n = 0, heads = new Set(), imgs = new Set(), last = -1;
for (let t = 0; t <= C.dur; t += 1 / 240) {
  const fp = CP.finalPose(P, CP.offsetsFrom(P, CP.clipPose(P, C, t)), null); if (fp.fire.op < 0.01) continue;
  const W = CP.worldMatrices(P, fp), a = CP.apply(W.fire, RP[0], RP[1]), b = CP.apply(W.headImg, RP[0], RP[1]);
  max = Math.max(max, Math.hypot(a[0] - b[0], a[1] - b[1])); n++; heads.add(fp.headImg.img); imgs.add(fp.fire.img); last = t;
}
console.log(JSON.stringify({ visible_frames_240fps: n, root_vs_mouth_max_px: +max.toFixed(6), heads_while_fire: [...heads], fire_images: [...imgs], last_fire_t: +last.toFixed(3), fire_pivot: RP,
  fire_images_assets: fire.images.map(v => v.name + ' ' + v.asset + ' ' + [v.x, v.y, v.w, v.h].join(',')) }));
