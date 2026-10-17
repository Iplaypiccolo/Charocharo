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
       'footL': (478, 1032), 'footR': (747, 1032), 'body': (627, 1040), 'fire': (round(FIRE_ROOT[0] + 8, 2), FIRE_ROOT[1])}   # 불꽃 뿌리 = fireRoot + 입 안쪽 8px(fix.py INSET) → 커지고 흔들려도 뿌리 고정
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
    part('fire', '불꽃(입 왼쪽 끝 뿌리 고정)', 'head', PIV['fire'], [img('12 불꽃 작게', 'fire12', 'fire12'), img('13 불꽃 크게(교체본)', 'fire13b', 'fire13b')]),
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

# ───────── 전체 인트로(6.3초, 2026-10-17 개정 콘티) ─────────
# 티라는 처음부터 제자리에 서 있음(달리지 않음). 친구들이 멀리서 달려오는 동안 불을 뿜고 → 뜨거워하고 → '아 맞다' →
# 머리만 돌려 등 뒤 팻말을 입으로 꺼냄 → 슬로모션 시작(2.30초)에 거꾸로 '환영'이 펼쳐져 있음.
# 다가오기·정렬 축소는 인트로 재생기 바깥 층이 맡으므로 이 동작에는 없음(rig 키 없음).
END = 6.3; SLOW0, SLOW1 = 2.30, 3.90
c = Clip('t_intro', 'B 전체 인트로(6.3초, 제자리)', END)
# 0.30~0.82 불: 작은 불 → 큰 불(0.32초 동안 뿌리 기준으로 커졌다 출렁) → 작은 불 → 숨김
FIRE = [(0.30, 'small'), (0.40, 'big'), (0.72, 'small'), (0.82, None)]
op = [(0, 0)]; fim = [(0, 0, 0)]
for t, f in FIRE:
    op.append((t, 0 if f is None else 1))
    if f: fim.append((t, 0 if f == 'small' else 1, 0))
c.ops('fire', op + [(END, 0)]); c.im('fire', fim); c.c['fireFrames'] = [[t, f] for t, f in FIRE]
c.k('fire', 'sx', [(0, 1), (0.40, 0.78, 'out'), (0.45, 1.0), (0.52, 1.05), (0.60, 0.98), (0.66, 1.04), (0.72, 1.0, 'step'), (END, 1)])
c.k('fire', 'sy', [(0, 1), (0.40, 0.85, 'out'), (0.45, 1.0), (0.52, 0.95), (0.60, 1.02), (0.66, 0.97), (0.72, 1.0, 'step'), (END, 1)])
c.k('fire', 'rot', [(0, 0), (0.40, 0), (0.46, -3), (0.53, 2), (0.60, -2), (0.66, 1), (0.72, 0, 'step'), (END, 0)])
# 뜨거워 반응: 큰 불 순간 >< 머리, 몸 전체가 불 반대쪽(화면 오른쪽)으로 젖혀지며 깜짝 폴짝 → 천천히 돌아옴
c.k('sway', 'rot', [(0, 0), (0.40, 0, 'out'), (0.46, 7.5), (0.70, 6), (0.95, 0, 'inout'), (END, 0)])
c.k('sway', 'y', [(0, 0), (0.42, 0, 'out'), (0.48, -12, 'in'), (0.58, 0), (3.41, 0, 'out'), (3.53, -14, 'in'), (3.67, 0), (END, 0)])   # 깜짝 폴짝 / 환영 중 들썩임 1번
c.k('sway', 'sy', [(0, 1), (0.40, 1, 'in'), (0.44, 0.96, 'out'), (0.48, 1.03), (0.58, 0.96, 'out'), (0.68, 1.0), (3.37, 1), (3.45, 0.975), (3.55, 1.012), (3.70, 1), (END, 1)])
c.k('sway', 'sx', [(0, 1), (0.40, 1, 'in'), (0.44, 1.03, 'out'), (0.48, 0.98), (0.58, 1.03, 'out'), (0.68, 1.0), (END, 1)])
c.k('tail', 'rot', [(0, 0), (0.50, 0, 'out'), (0.60, -9), (0.80, 5), (1.00, -2), (1.12, 0), (SLOW0, 0), (3.05, 4), (SLOW1, 0), (END, 0)])
c.k('footL', 'y', [(0, 0), (END, 0)]).k('footR', 'y', [(0, 0), (END, 0)])
# 머리 자세(한 번에 한 장): 기본 → 뜨거워 → 기본('아 맞다' 빈 박자 0.98~1.20) → 오른쪽중간 → 뒤보기 → 오른쪽중간 → 정면물기
HEADK = [(0, '02'), (0.40, '03'), (0.98, '02'), (1.31, '04'), (1.43, '05'), (1.92, '04'), (2.10, '06')]
c.im('headImg', [(t, HI[k], 0) for t, k in HEADK])
# 1.20~ 머리만: 오른쪽으로 살짝 먼저 움직임(선행) → 시점 교체. 1.15~2.30 동안 아랫몸통·발·꼬리 고정
c.k('head', 'x', [(0, 0), (1.20, 0), (1.27, 5, 'out'), (1.37, 3), (1.55, 0), (1.87, 0), (1.95, -4, 'out'), (2.11, -2), (2.17, 0), (END, 0)])
c.k('head', 'rot', [(0, 0), (1.20, 0), (1.27, 1.5, 'out'), (1.37, 0.8), (1.55, 0), (1.65, -1.5, 'out'), (1.73, 0), (END, 0)])
c.k('head', 'y', [(0, 0), (1.57, 0), (1.65, 6, 'out'), (1.72, 0), (END, 0)])   # 등 뒤 꼭지를 무는 작은 끄덕
c.k('bite', 'x', [(0, OFF['05'][0], 'step'), (1.92, OFF['04'][0], 'step'), (2.10, 0, 'step'), (END, 0)])
c.k('bite', 'y', [(0, OFF['05'][1], 'step'), (1.92, OFF['04'][1], 'step'), (2.10, 0, 'step'), (END, 0)])
c.k('bite', 'rot', [(0, -8), (1.65, -8, 'out'), (1.79, -52), (1.87, -48), (1.92, -36, 'out'), (2.08, -12), (2.10, -12, 'out'),
                    (2.24, 5), (SLOW0, 0), (2.55, 0), (2.80, 4), (3.10, -3), (3.40, 1.5), (3.65, -0.5), (3.85, 0), (END, 0)])
c.k('sign14', 'sx', [(0, 1), (2.10, 0.18, 'out'), (2.24, 1.0), (END, 1)])
c.ops('sign11B', [(0, 0), (1.65, 1), (1.92, 0), (END, 0)])
c.ops('sign11F', [(0, 0), (1.92, 1), (2.10, 0), (END, 0)])
c.ops('sign14', [(0, 0), (2.10, 1), (END, 1)])
c.ops('mask', [(0, 0), (1.92, 1), (END, 1)]); c.im('mask', [(0, 0, 0), (1.92, 0, 0), (2.10, 1, 0)])
c.c['beat'] = dict(start=SLOW0, end=2.55, note='슬로모션 시작과 함께 거꾸로 판을 태연하게 제시하는 읽기 박자(장면 정지 없음)')
c.c['slow'] = [SLOW0, SLOW1]
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
clips.append(slice_clip(INTRO, 't_run', 'C 제자리 불뿜기·뜨거워(0~1.2초)', 0, 1.25))
clips.append(slice_clip(INTRO, 't_fetch', 'D 머리만 뒤돌아 입으로 꺼내기(1.2~2.3초)', 0.95, 2.40))
clips.append(slice_clip(INTRO, 't_welcome', 'E 거꾸로 환영 슬로모션(2.3~3.9초)·대기', 2.30, END))
clips.append(slice_clip(INTRO, 't_turn_slow', 'F 느린 머리 회전 ×4(아랫몸통 고정 확인)', 1.15, 2.35, 4.0))
ZK = 1.7
def zoom(o):   # 입 주변 확대: 전체 크기 ×1.7, 입이 무대 가운데 오도록 이동
    o.k('rig', 'sx', [(0, ZK), (o.dur, ZK)]).k('rig', 'sy', [(0, ZK), (o.dur, ZK)])
    o.k('rig', 'x', [(0, -20), (o.dur, -20)]).k('rig', 'y', [(0, 71), (o.dur, 71)])
clips.append(slice_clip(INTRO, 't_fetch_zoom', 'G 확대·느린 꺼내기 ×3(입 접점·앞뒤 겹침)', 1.53, 2.60, 3.0, zoom))
# H 모션 줄이기: 머리 돌리기·불·흔들림 없이 처음부터 정면 물기 자세로 안정(정렬 축소는 인트로 재생기)
c = Clip('t_intro_r', 'H 모션 줄이기 버전', END)
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
               timeline=[[0, 0.30, '제자리 대기(친구들은 아직 안 보임)'], [0.30, 0.82, '불: 작게→큰 불(0.32초)→작게→끔, 뜨거워 >< ·젖힘·폴짝'],
                         [0.98, 1.20, '아 맞다 빈 박자(정면)'], [1.20, 1.55, '머리만 02→04→05'], [1.55, 1.92, '등 뒤 물기(11 옆면 조금)'],
                         [1.92, 2.24, '05→04→06, 11→14 펼침'], [2.30, 2.55, '슬로모션 시작·읽기 박자'], [2.55, 3.90, '판만 물림점 축 흔들림→안정, 들썩임 1번'],
                         [3.90, END, '물기 유지(정렬 축소는 인트로 재생기)']], slow=[SLOW0, SLOW1]),
          open(OUT + 'rig.json', 'w'), ensure_ascii=False, indent=1)
print('json KB', len(s) // 1024, [c_['id'] for c_ in clips])
