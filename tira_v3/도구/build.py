# 무팔 티라(v3) 검수본: work/fixed 보정본(1254 좌표) → 자르기·절반 해상도 → charo-pet 형식 JSON
# 기준: 원본 ZIP의 rig_start.json 변환값 + 콘티_타이밍.csv(총 6.7초)
import cv2, numpy as np, json, base64, os, copy, math
W = '/home/claude/tira3/work/'; F = W + 'fixed/'; OUT = '/home/claude/tira3/out/'; os.makedirs(OUT + 'crops', exist_ok=True)
N = 1254
RS = json.load(open('/home/claude/tira3/src/rig_start.json')); J = {t['id']: t for t in RS['transforms']}
G = {k: J[k]['mouthGrip_after_transform'] for k in ('02', '04', '05', '06')}
G6 = G['06']
OFF = {k: (round(G[k][0] - G6[0], 2), round(G[k][1] - G6[1], 2)) for k in G}     # 머리 시점별 입 물림점 − 정면물기 물림점
FIRE_ROOT = (round(J['02']['fireRoot_source'][0] * J['02']['scale'] + J['02']['translate_x'], 2),
             round(J['02']['fireRoot_source'][1] * J['02']['scale'] + J['02']['translate_y'], 2))
def load(n): return cv2.imread(F + n + '.png', cv2.IMREAD_UNCHANGED)
assets, crops = {}, {}
def asset(key, im, pad=3):
    a = im[..., 3] > 8; ys, xs = np.where(a)
    x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad); x1, y1 = min(N, xs.max() + pad + 1), min(N, ys.max() + pad + 1)
    c = im[y0:y1, x0:x1]; cv2.imwrite(OUT + 'crops/' + key + '.png', c)
    sm = cv2.resize(c, (max(1, round(c.shape[1] / 2)), max(1, round(c.shape[0] / 2))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode('.png', sm, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assets['t3_' + key] = 'data:image/png;base64,' + base64.b64encode(buf.tobytes()).decode()
    crops[key] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0), canvas=[N, N])
    return dict(asset='t3_' + key, x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
def img(name, key, fname): d = asset(key, load(fname)); d['name'] = name; return d

PIV = {'rig': (640, 1121), 'sway': (627, 1112), 'head': (603, 650), 'bite': tuple(G6), 'tail': (790, 960),
       'footL': (478, 1032), 'footR': (747, 1032), 'body': (627, 1040), 'fire': FIRE_ROOT}
S = 0.30; RIG_AT = (200, 385)
def R(x, y, rot=0, s=1, op=1): return dict(x=x, y=y, rot=rot, sx=s, sy=s, op=op, img=0)
def part(id, name, parent, piv, images):
    rest = R(*RIG_AT, 0, S) if parent is None else R(*piv)
    return dict(id=id, name=name, parent=parent, pivot=dict(x=piv[0], y=piv[1]), rest=rest, images=images, follow=dict(on=False, max=0))
HEADS = [('정면 기본', '02'), ('뜨거워 ><', '03'), ('오른쪽 중간', '04'), ('뒤보기', '05'), ('정면 물기(태연)', '06')]
parts = [   # 그림 그리는 순서 = 뒤 → 앞
    part('rig', '무대 위치·전체 크기(그림 없음)', None, PIV['rig'], []),
    part('sway', '달리기·착지용 몸 전체(그림 없음)', 'rig', PIV['sway'], []),
    part('head', '머리 시점 그룹(목 접합점, 그림 없음)', 'sway', PIV['head'], []),
    part('bite', '입 물림점(팻말 회전축, 그림 없음)', 'head', PIV['bite'], []),
    part('sign11B', '팻말 옆면(등 뒤, 몸통 뒤에 가려짐)', 'bite', PIV['bite'], [img('11 옆면', 'sign11', 'sign11')]),
    part('tail', '꼬리', 'sway', PIV['tail'], [img('09 꼬리', 'tail', 'tail')]),
    part('footL', '화면 왼발', 'sway', PIV['footL'], [img('07 화면왼발', 'footL', 'footL')]),
    part('footR', '화면 오른발', 'sway', PIV['footR'], [img('08 화면오른발', 'footR', 'footR')]),
    part('body', '고정 아랫몸통·아래 뼈깃', 'sway', PIV['body'], [img('01 고정아랫몸통', 'body', 'body')]),
    part('headImg', '머리 자세(5장 중 하나만)', 'head', PIV['head'], [img(n, 'head' + k, 'head' + k) for n, k in HEADS]),
    part('collar', '목 접합 띠(몸통 윤곽선 이어줌)', 'sway', PIV['body'], [img('접합 띠', 'collar', 'collar')]),
    part('sign11F', '팻말 옆면(앞으로 나옴)', 'bite', PIV['bite'], [img('11 옆면', 'sign11f', 'sign11')]),
    part('sign14', '팻말 정면 ‘환영’ 거꾸로(14번 그대로)', 'bite', PIV['bite'], [img('14 거꾸로환영', 'sign14', 'sign14')]),
    part('mask', '입 앞가림(이빨·아랫입술)', 'head', PIV['head'], [img('04 입 앞가림', 'mask04', 'mask04'), img('06 입 앞가림', 'mask06', 'mask06')]),
    part('fire', '불꽃(입 왼쪽 끝 뿌리 고정)', 'head', PIV['fire'], [img('12 불꽃 작게', 'fire12', 'fire12'), img('13 불꽃 뿍', 'fire13', 'fire13')]),
]
HI = {k: i for i, (_, k) in enumerate(HEADS)}
FACES = [dict(id='f02', name='① 정면 기본', img=dict(headImg=0), mods={}),
         dict(id='f03', name='② 뜨거워 ><', img=dict(headImg=1), mods={}),
         dict(id='f06', name='③ 정면 물기(태연)', img=dict(headImg=4, mask=1), mods={}),
         dict(id='v04', name='시점: 오른쪽 중간', img=dict(headImg=2, mask=0), mods={}),
         dict(id='v05', name='시점: 뒤보기', img=dict(headImg=3), mods={})]
LAYERS = ('sign11B', 'sign11F', 'sign14', 'mask', 'fire')
HS = 277   # 무대에서 캐릭터 높이(px)

class Clip:
    def __init__(s, id, name, dur, loop=False, follow='center', **kw):
        s.c = dict(id=id, name=name, dur=dur, loop=loop, follow=follow, tracks={}); s.c.update(kw); s.dur = dur
    def k(s, part, prop, keys):
        out = {}
        for x in keys: t = round(x[0], 3); out[t] = dict(t=t, v=round(float(x[1]), 4), e=x[2] if len(x) > 2 else 'inout')
        s.c['tracks'].setdefault(part, {})[prop] = [out[t] for t in sorted(out)]; return s
    def im(s, part, keys):   # [(t, v, f)]
        s.c['tracks'].setdefault(part, {})['img'] = [dict(t=round(t, 3), v=v, f=f) for t, v, f in sorted(keys)]; return s
    def ops(s, part, keys):  # 계단식 보임/숨김
        s.k(part, 'op', [(t, v, 'step') for t, v in keys]); return s
def lag(keys, dt, sc=1.0): return [(round(k[0] + dt, 3), k[1] * sc) + tuple(k[2:]) for k in keys]

# ───────── 전체 인트로(6.7초, 콘티 시각 그대로) ─────────
END = 6.7
c = Clip('t_intro', 'B 전체 인트로(6.7초)', END)
# 0.00~1.20 정면 우다다닥: 멀리서 커지며 다가옴(rig) + 제자리 달리기(sway·발·꼬리)
c.k('rig', 'sx', [(0, 0.55), (1.15, 1, 'out'), (5.35, 1), (6.05, 0.6), (END, 0.6)])
c.k('rig', 'sy', [(0, 0.55), (1.15, 1, 'out'), (5.35, 1), (6.05, 0.6), (END, 0.6)])
c.k('rig', 'y', [(0, -60), (1.15, 0, 'out'), (5.35, 0), (6.05, 0.04 * HS), (END, 0.04 * HS)])
STEP = 0.12; steps = [round(0.04 + i * STEP, 3) for i in range(9)]          # 0.04 … 1.00
TILT = 7.5
rot = [(0, 0)]
for i, t in enumerate(steps):
    if 0.58 <= t <= 0.80: continue                                          # 불 반동 구간은 아래에서 따로
    rot.append((t, TILT if i % 2 == 0 else -TILT))
rot += [(0.62, 9.5, 'out'), (0.76, 8)]                                       # 자기 불이 뜨거워 화면 오른쪽(불 반대)으로 젖혀짐
rot += [(1.12, 0, 'out'), (1.20, 0)]
rot.sort(key=lambda r: r[0]); c.k('sway', 'rot', rot)
yk = [(0, 0)]
for t in steps: yk += [(t, 0, 'out'), (round(t + STEP / 2, 3), -22, 'in')]
yk += [(1.12, 0), (1.20, 0, 'out'), (3.66, 0), (3.78, -14, 'out'), (3.92, 0, 'in'), (END, 0)]   # 3.7초 무렵 작은 들썩임 1번
c.k('sway', 'y', yk)
c.k('sway', 'sy', [(0, 1), (1.16, 1, 'in'), (1.22, 0.955, 'out'), (1.34, 1.0), (3.62, 1), (3.70, 0.975), (3.80, 1.012), (3.95, 1), (END, 1)])
c.k('sway', 'sx', [(0, 1), (1.16, 1, 'in'), (1.22, 1.03, 'out'), (1.34, 1.0), (END, 1)])
fl, fr = [(0, 0)], [(0, 0)]
for i, t in enumerate(steps):
    g = fl if i % 2 == 0 else fr; g += [(t, -30, 'out'), (round(t + STEP * 0.8, 3), 0, 'in')]
c.k('footL', 'y', fl + [(1.14, 0), (END, 0)]).k('footR', 'y', fr + [(1.14, 0), (END, 0)])
tl = lag([r for r in rot if r[0] <= 1.12], 0.08, -1.3)
c.k('tail', 'rot', tl + [(1.28, 3, 'out'), (1.38, 0), (2.55, 0), (3.30, 4), (4.15, 0), (END, 0)])
# 불: 작은 불 → 뿍 → 작은 불 → 숨김 한 묶음, 뿍 순간 >< 머리
FIRE = [(0.52, 'small'), (0.60, 'big'), (0.70, 'small'), (0.78, None)]
op = [(0, 0)]; fim = [(0, 0, 0)]
for t, f in FIRE:
    op.append((t, 0 if f is None else 1))
    if f: fim.append((t, 0 if f == 'small' else 1, 0))
c.ops('fire', op + [(END, 0)]); c.im('fire', fim); c.c['fireFrames'] = [[t, f] for t, f in FIRE]
# 머리 자세(한 번에 한 장): 기본 → 뜨거워 → 기본 → 오른쪽중간 → 뒤보기 → 오른쪽중간 → 정면물기
HEADK = [(0, '02'), (0.60, '03'), (0.86, '02'), (1.56, '04'), (1.68, '05'), (2.17, '04'), (2.35, '06')]
c.im('headImg', [(t, HI[k], 0) for t, k in HEADK])   # 시점 교체는 즉시(교차 페이드로 눈·이빨이 두 겹 되는 것 방지)
# 1.45~1.80 머리만: 눈이 먼저 오른쪽을 보는 대신 머리가 오른쪽으로 살짝 먼저 움직임(선행) → 시점 교체
c.k('head', 'x', [(0, 0), (1.45, 0), (1.52, 5, 'out'), (1.62, 3), (1.80, 0), (2.12, 0), (2.20, -4, 'out'), (2.36, -2), (2.42, 0), (END, 0)])
c.k('head', 'rot', [(0, 0), (1.45, 0), (1.52, 1.5, 'out'), (1.62, 0.8), (1.80, 0), (1.90, -1.5, 'out'), (1.98, 0), (END, 0)])
c.k('head', 'y', [(0, 0), (1.82, 0), (1.90, 6, 'out'), (1.97, 0), (END, 0)])   # 등 뒤 꼭지를 무는 작은 끄덕
# 팻말: 물림점은 머리 시점마다 입 위치로 이동(계단), 회전은 물림점 축
c.k('bite', 'x', [(0, OFF['05'][0], 'step'), (2.17, OFF['04'][0], 'step'), (2.35, 0, 'step'), (END, 0)])
c.k('bite', 'y', [(0, OFF['05'][1], 'step'), (2.17, OFF['04'][1], 'step'), (2.35, 0, 'step'), (END, 0)])
c.k('bite', 'rot', [(0, -8), (1.90, -8, 'out'), (2.04, -52), (2.12, -48), (2.17, -36, 'out'), (2.33, -12), (2.35, -12, 'out'),
                    (2.49, 5), (2.55, 0), (2.80, 0), (3.05, 4), (3.35, -3), (3.65, 1.5), (3.90, -0.5), (4.10, 0), (END, 0)])
c.k('sign14', 'sx', [(0, 1), (2.35, 0.18, 'out'), (2.49, 1.0), (END, 1)])       # 옆면 → 정면으로 펼쳐짐
c.ops('sign11B', [(0, 0), (1.90, 1), (2.17, 0), (END, 0)])
c.ops('sign11F', [(0, 0), (2.17, 1), (2.35, 0), (END, 0)])
c.ops('sign14', [(0, 0), (2.35, 1), (END, 1)])
c.ops('mask', [(0, 0), (2.17, 1), (END, 1)]); c.im('mask', [(0, 0, 0), (2.17, 0, 0), (2.35, 1, 0)])
c.c['beat'] = dict(start=2.55, end=2.80, note='거꾸로 판을 태연하게 제시하는 읽기 박자(장면 정지 없음)')
INTRO = c.c

# ───────── 재생기 표본 추출(엔진과 같은 보간) → 구간 잘라 부분 미리보기 만들기 ─────────
def ease(e, u):
    return {'linear': u, 'in': u * u, 'out': 1 - (1 - u) ** 2, 'inout': (2 * u * u if u < .5 else 1 - (-2 * u + 2) ** 2 / 2),
            'step': 0}.get(e, u)
def sample(keys, t):
    if t <= keys[0]['t']: return keys[0]['v']
    for a, b in zip(keys, keys[1:]):
        if t < b['t']:
            u = (t - a['t']) / (b['t'] - a['t']) if b['t'] > a['t'] else 1
            return a['v'] + (b['v'] - a['v']) * ease(a['e'], u)
    return keys[-1]['v']
def slice_clip(src, id, name, a, b, stretch=1.0, extra=None):
    d = round((b - a) * stretch, 3); out = Clip(id, name, d)
    for pid, tr in src['tracks'].items():
        for prop, keys in tr.items():
            if prop == 'img':
                last = [k for k in keys if k['t'] <= a + 1e-6]
                ks = [(0, (last[-1] if last else keys[0])['v'], 0)] + [(round((k['t'] - a) * stretch, 3), k['v'], k['f'] * stretch) for k in keys if a + 1e-6 < k['t'] < b]
                out.im(pid, ks); continue
            v0 = sample(keys, a); e0 = 'linear'
            for x, y in zip(keys, keys[1:]):
                if x['t'] <= a < y['t']: e0 = 'step' if x['e'] == 'step' else 'linear'
            ks = [(0, v0, e0)] + [(round((k['t'] - a) * stretch, 3), k['v'], k['e']) for k in keys if a < k['t'] < b] + [(d, sample(keys, b))]
            out.k(pid, prop, ks)
    if extra: extra(out)
    return out.c

clips = []
# A 대기: 정면 기본, 팻말·불·앞가림 숨김(기본 투명도는 1이므로 동작에서 0으로)
c = Clip('t_idle', 'A 대기', 3.0, loop=True, follow='on')
c.k('sway', 'sy', [(0, 1), (1.5, 1.015), (3, 1)]).k('sway', 'sx', [(0, 1), (1.5, 0.994), (3, 1)])
c.k('tail', 'rot', [(0, 0), (0.35, 0), (1.85, -4), (3, 0)])
for L_ in LAYERS: c.ops(L_, [(0, 0), (3, 0)])
c.im('headImg', [(0, 0, 0)])
clips.append(c.c)
clips.append(INTRO)
clips.append(slice_clip(INTRO, 't_run', 'C 달리기·불뿜기(0~1.2초)', 0, 1.45))
clips.append(slice_clip(INTRO, 't_fetch', 'D 머리만 뒤돌아 입으로 꺼내기(1.2~2.55초)', 1.20, 2.60))
clips.append(slice_clip(INTRO, 't_welcome', 'E 거꾸로 환영·정렬(2.55~6.7초)', 2.55, END))
clips.append(slice_clip(INTRO, 't_turn_slow', 'F 느린 머리 회전 ×4(아랫몸통 고정 확인)', 1.40, 2.60, 4.0))
ZK = 1.7
def zoom(o):   # 입 주변 확대: 전체 크기 ×1.7, 입이 무대 가운데 오도록 이동
    o.k('rig', 'sx', [(0, ZK), (o.dur, ZK)]).k('rig', 'sy', [(0, ZK), (o.dur, ZK)])
    o.k('rig', 'x', [(0, -20), (o.dur, -20)]).k('rig', 'y', [(0, 71), (o.dur, 71)])
clips.append(slice_clip(INTRO, 't_fetch_zoom', 'G 확대·느린 꺼내기 ×3(입 접점·앞뒤 겹침)', 1.78, 2.85, 3.0, zoom))
# H 모션 줄이기: 머리 돌리기·불·흔들림 없이 정면 물기 자세로 안정, 정렬 축소만
c = Clip('t_intro_r', 'H 모션 줄이기 버전', END)
c.k('rig', 'sx', [(0, 1), (5.35, 1), (6.05, 0.6), (END, 0.6)]).k('rig', 'sy', [(0, 1), (5.35, 1), (6.05, 0.6), (END, 0.6)])
c.k('rig', 'y', [(0, 0), (5.35, 0), (6.05, 0.04 * HS), (END, 0.04 * HS)])
c.im('headImg', [(0, 4, 0)]); c.im('mask', [(0, 1, 0)])
c.ops('sign11B', [(0, 0), (END, 0)]).ops('sign11F', [(0, 0), (END, 0)]).ops('fire', [(0, 0), (END, 0)])
c.ops('sign14', [(0, 1), (END, 1)]).ops('mask', [(0, 1), (END, 1)])
c.k('bite', 'x', [(0, 0), (END, 0)]).k('bite', 'y', [(0, 0), (END, 0)]).k('bite', 'rot', [(0, 0), (END, 0)])
clips.append(c.c)
for cl in clips:   # 모든 동작에서 보임/숨김 층을 명시(빠지면 기본값 1로 보임)
    for L_ in LAYERS: assert 'op' in cl['tracks'].get(L_, {}), (cl['id'], L_)
    for tr in cl['tracks'].values():
        if 'img' in tr: tr['img'].sort(key=lambda d: d['t'])
preview = [dict(label=c_['name'].split(' ', 1)[0] + ' ' + c_['name'].split(' ', 1)[1], clip=c_['id']) for c_ in clips]
proj = dict(version=1, name='티라 v3 무팔 (검수본)', stage=dict(w=400, h=400), parts=parts, clips=clips, rules=[], baseClip='t_idle',
            faces=FACES, preview=preview, reducedClip={'t_intro': 't_intro_r'},
            display=dict(size=170, corner='right', margin=16, hideOnMobile=False, closable=False), assets=assets)
s = json.dumps(proj, ensure_ascii=False, separators=(',', ':'))
open(OUT + 'tira_v3.json', 'w').write(s)
json.dump(dict(canvas=[N, N], source='rig_start.json 변환 적용 후 work/fix.py·mask.py 보정', stage_scale=S, rig_at_stage=list(RIG_AT), pivots=PIV,
               mouthGrip=G, bite_offsets_from_06=OFF, fireRoot=FIRE_ROOT, crops=crops, draw_order=[p['id'] for p in parts],
               parents={p['id']: p['parent'] for p in parts}, head_sequence=HEADK, fire=FIRE,
               timeline=[[0, 1.2, '정면 우다다닥(불 1묶음)'], [1.2, 1.45, '멈칫'], [1.45, 1.8, '머리만 02→04→05'], [1.8, 2.05, '등 뒤 물기(11 옆면 조금)'],
                         [2.05, 2.55, '05→04→06, 11→14'], [2.55, 2.8, '읽기 박자(정지 없이 유지)'], [2.8, 4.15, '판만 물림점 축 흔들림→안정, 들썩임 1번'],
                         [4.15, 5.35, '물기 유지'], [5.35, 6.7, '정렬 축소(뒤집힌 판 유지)']]),
          open(OUT + 'rig.json', 'w'), ensure_ascii=False, indent=1)
print('json KB', len(s) // 1024, [c_['id'] for c_ in clips])
