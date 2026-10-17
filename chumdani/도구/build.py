# 첨다니 검수본 조립: work/fixed 보정본 → 자르기·절반 해상도 → charo-pet 형식 JSON
# 좌표는 모두 원래 캔버스 1254×1254. 잘라낸 그림마다 원래 위치(x,y,w,h)를 기록.
import cv2, numpy as np, json, base64, os
from PIL import Image, ImageDraw, ImageFont
F = '/home/claude/chumdani/work/fixed/'; OUT = '/home/claude/chumdani/out/'; os.makedirs(OUT + 'crops', exist_ok=True)
N = 1254; SPLIT_X = 627
SIGN_TEXT = '합니다!'
def load(n): return cv2.imread(F + n + '.png', cv2.IMREAD_UNCHANGED)
def half(im, side):
    im = im.copy()
    if side == 'L': im[:, SPLIT_X:] = 0
    else: im[:, :SPLIT_X] = 0
    return im
assets, crops = {}, {}
def asset(key, im, pad=3):
    a = im[..., 3] > 8; ys, xs = np.where(a)
    x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad); x1, y1 = min(N, xs.max() + pad + 1), min(N, ys.max() + pad + 1)
    c = im[y0:y1, x0:x1]; cv2.imwrite(OUT + 'crops/' + key + '.png', c)
    sm = cv2.resize(c, (max(1, round(c.shape[1] / 2)), max(1, round(c.shape[0] / 2))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode('.png', sm, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assets['c_' + key] = 'data:image/png;base64,' + base64.b64encode(buf.tobytes()).decode()
    crops[key] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0), canvas=[N, N])
    return dict(asset='c_' + key, x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
def img(name, key, im): d = asset(key, im); d['name'] = name; return d
def centre(im):
    ys, xs = np.where(im[..., 3] > 128); return [round(float((xs.min() + xs.max()) / 2), 1), round(float((ys.min() + ys.max()) / 2), 1)]


NAMES = ['화면왼귀','화면오른귀','안테나','화면왼바퀴','화면오른바퀴','차체바탕','와이파이_약함','와이파이_강함_점','와이파이_강함_안쪽','와이파이_강함_바깥','눈썹_기본','눈_기본','눈_질끈웃음']
src = {n: load(n) for n in NAMES}
eB = {s: half(src['눈_기본'], s) for s in 'LR'}; eW = {s: half(src['눈_질끈웃음'], s) for s in 'LR'}; bB = {s: half(src['눈썹_기본'], s) for s in 'LR'}
PIV = {
    'rig': (627, 700), 'flip': (627, 700),      # 무대 위치·전체 크기 / 공중제비 회전(차체 가운데)
    'body': (627, 990),                         # 차체 아래 가운데(통통 튀기·찌그러짐)
    'earL': (360, 470), 'earR': (900, 465), 'ant': (626, 415),
    'wheelL': (409, 965), 'wheelR': (842, 980),
    'eyeL': tuple(centre(eB['L'])), 'eyeR': tuple(centre(eB['R'])),
    'browL': tuple(centre(bB['L'])), 'browR': tuple(centre(bB['R'])),
    'wifi': (627.5, 874),
}
S = 0.20; RIG_AT = (200, 215)
def R(x, y, rot=0, s=1, op=1): return dict(x=x, y=y, rot=rot, sx=s, sy=s, op=op, img=0)
def part(id, name, parent, piv, images, follow=None, rest=None):
    if rest is None: rest = R(*RIG_AT, 0, S) if parent is None else R(*piv)
    return dict(id=id, name=name, parent=parent, pivot=dict(x=piv[0], y=piv[1]), rest=rest, images=images, follow=follow or dict(on=False, max=0))
parts = [
    part('rig', '무대 위치·전체 크기(그림 없음)', None, PIV['rig'], []),
    part('flip', '공중제비 회전(그림 없음)', 'rig', PIV['flip'], []),
    part('earL', '화면 왼귀', 'body', PIV['earL'], [img('화면 왼귀', 'earL', src['화면왼귀'])]),
    part('earR', '화면 오른귀', 'body', PIV['earR'], [img('화면 오른귀', 'earR', src['화면오른귀'])]),
    part('ant', '안테나', 'body', PIV['ant'], [img('안테나', 'ant', src['안테나'])]),
    part('wheelL', '화면 왼바퀴', 'body', PIV['wheelL'], [img('화면 왼바퀴', 'wheelL', src['화면왼바퀴'])]),
    part('wheelR', '화면 오른바퀴', 'body', PIV['wheelR'], [img('화면 오른바퀴', 'wheelR', src['화면오른바퀴'])]),
    part('body', '차체바탕(와이파이 분리, 전조등 고정)', 'flip', PIV['body'], [img('차체바탕', 'body', src['차체바탕'])]),
    part('wifi0', '와이파이 약함(테두리)', 'body', PIV['wifi'], [img('신호 약함', 'wifi_weak', src['와이파이_약함'])]),
    part('wifi1', '와이파이 강함: 아래 점', 'body', PIV['wifi'], [img('강함 점', 'wifi_dot', src['와이파이_강함_점'])]),
    part('wifi2', '와이파이 강함: 안쪽 곡선', 'body', PIV['wifi'], [img('강함 안쪽', 'wifi_in', src['와이파이_강함_안쪽'])]),
    part('wifi3', '와이파이 강함: 바깥 곡선', 'body', PIV['wifi'], [img('강함 바깥', 'wifi_out', src['와이파이_강함_바깥'])]),
    part('browL', '화면 왼눈썹', 'body', PIV['browL'], [img('눈썹', 'browL', bB['L'])], dict(on=True, max=10)),
    part('browR', '화면 오른눈썹', 'body', PIV['browR'], [img('눈썹', 'browR', bB['R'])], dict(on=True, max=10)),
    part('eyeL', '화면 왼눈', 'body', PIV['eyeL'], [img('기본 눈', 'eyeL_basic', eB['L']), img('질끈 웃음 눈', 'eyeL_squint', eW['L'])], dict(on=True, max=14)),
    part('eyeR', '화면 오른눈', 'body', PIV['eyeR'], [img('기본 눈', 'eyeR_basic', eB['R']), img('질끈 웃음 눈', 'eyeR_squint', eW['R'])], dict(on=True, max=14)),
]
FACES = {'f00': dict(id='f00', name='기본', img=dict(eyeL=0, eyeR=0), mods={}), 'f01': dict(id='f01', name='질끈 웃음', img=dict(eyeL=1, eyeR=1), mods={})}
H = 166
class Clip:
    def __init__(s, id, name, dur, loop=False, follow='center', **kw):
        s.c = dict(id=id, name=name, dur=dur, loop=loop, follow=follow, tracks={}); s.c.update(kw); s.dur = dur
    def k(s, part, prop, keys):
        out = {}
        for x in keys: t = round(x[0], 3); out[t] = dict(t=t, v=round(float(x[1]), 4), e=x[2] if len(x) > 2 else 'inout')
        s.c['tracks'].setdefault(part, {})[prop] = [out[t] for t in sorted(out)]; return s
    def face(s, t, fid, f=0.04, brow_y=0):
        for p_, v in FACES[fid]['img'].items(): s.c['tracks'].setdefault(p_, {}).setdefault('img', []).append(dict(t=round(t, 3), v=v, f=f))
        return s
    def wifi(s, steps):
        """신호 단계 [(시각, 0~3)] → 강함 3구역의 투명도(뚝 바꿈). 약함 테두리는 늘 표시"""
        for lv in (1, 2, 3):
            keys = []
            for t, st in steps: keys.append((t, 1 if st >= lv else 0, 'step'))
            if keys[0][0] > 0: keys.insert(0, (0, keys[0][1], 'step'))
            keys.append((s.dur, keys[-1][1], 'step'))
            s.k('wifi%d' % lv, 'op', keys)
        s.c.setdefault('wifiSteps', [[round(t, 3), st] for t, st in steps])
        return s
    def build(s):
        for tr in s.c['tracks'].values():
            if 'img' in tr: tr['img'].sort(key=lambda d: d['t'])
        return s.c
def alt(t0, t1, step, a, b, e='inout'):
    out, i, t = [], 0, t0
    while t <= t1 + 1e-9: out.append((round(t, 3), a if i % 2 == 0 else b, e)); i += 1; t = round(t + step, 3)
    return out
def seq(t0, step, levels): return [(round(t0 + i * step, 3), lv) for i, lv in enumerate(levels)]
clips = []
# A 대기: 강함 정지(깜빡이지 않음), 작은 숨, 귀·안테나 아주 조금 늦게
c = Clip('c_idle', 'A 대기', 3.0, loop=True, follow='on')
c.k('body', 'sy', [(0, 1), (1.5, 1.02), (3, 1)]).k('body', 'sx', [(0, 1), (1.5, 0.993), (3, 1)])
c.k('earL', 'rot', [(0, 0), (1.7, -3), (3, 0)]).k('earR', 'rot', [(0, 0), (1.7, 3), (3, 0)]).k('ant', 'rot', [(0, 0), (1.8, 2), (3, 0)])
c.wifi([(0, 3)])
clips.append(c.build())
c = Clip('c_blink', '깜빡임', 0.22, follow='on')
for s_ in 'LR': c.k('eye' + s_, 'sy', [(0, 1, 'in'), (0.07, 0.1, 'out'), (0.18, 1)])
clips.append(c.build())
# B 정면 달려오기 2.4초: 바퀴 짧게 번갈아, 차체 작게 통통(지그재그 없음). 신호는 마지막에 한 번만 아래→위 점등
c = Clip('c_run', 'B 정면 달려오기', 2.4)
c.face(0, 'f00', 0)
c.k('rig', 'sx', [(0, 0.55), (2.05, 1.0, 'out'), (2.4, 1)]).k('rig', 'sy', [(0, 0.55), (2.05, 1.0, 'out'), (2.4, 1)])
STEP = 0.13; steps = [round(0.05 + i * STEP, 3) for i in range(16) if 0.05 + i * STEP < 2.06]
yk = [(0, -0.2 * H)]
for t in steps:
    base = -0.2 * H * (1 - min(1, t / 2.05)) ** 1.6
    yk += [(t, base, 'out'), (round(t + STEP / 2, 3), base - 0.02 * H, 'in')]
c.k('rig', 'y', yk + [(2.15, 0, 'out'), (2.4, 0)])
wl, wr = [(0, 0)], [(0, 0)]
for i, t in enumerate(steps):
    g = wl if i % 2 == 0 else wr; g += [(t, -14, 'out'), (round(t + STEP * 0.8, 3), 0, 'in')]
c.k('wheelL', 'y', wl + [(2.4, 0)]).k('wheelR', 'y', wr + [(2.4, 0)])
c.k('earL', 'rot', [(0, 0)] + [(round(t + 0.06, 3), -9 if i % 2 == 0 else 2) for i, t in enumerate(steps)] + [(2.25, 0), (2.4, 0)])
c.k('earR', 'rot', [(0, 0)] + [(round(t + 0.06, 3), 9 if i % 2 == 0 else -2) for i, t in enumerate(steps)] + [(2.25, 0), (2.4, 0)])
c.k('ant', 'rot', [(0, 0)] + [(round(t + 0.08, 3), 4 if i % 2 == 0 else -4) for i, t in enumerate(steps)] + [(2.25, 0), (2.4, 0)])
c.wifi([(0, 0)] + seq(1.78, 0.18, [1, 2, 3]))
clips.append(c.build())
# C 환영 슬로모션 3.2초(오른쪽 위에서 기울어진 자세 유지): 질끈 웃음과 동시에 점등 시작. 슬로모션이라 단계도 2배로 느리게(0.18→0.36초), 최대 두 번
SLOW = 2.0
c = Clip('c_welcome', 'C 환영 슬로모션', 3.2)
c.face(0, 'f00', 0).face(0.14, 'f01', 0.03)
c.k('body', 'rot', [(0, 0), (0.12, -3, 'out'), (0.32, 12, 'out'), (3.2, 15, 'linear')])
c.k('rig', 'x', [(0, 0), (0.32, 6, 'out'), (3.2, 9, 'linear')]).k('rig', 'y', [(0, 0), (0.12, 3, 'out'), (0.32, -8, 'out'), (3.2, -11, 'linear')])
c.k('body', 'sy', [(0, 1), (0.12, 0.92, 'out'), (0.32, 1.05, 'out'), (0.8, 1.03), (3.2, 1.02, 'linear')]).k('body', 'sx', [(0, 1), (0.12, 1.06, 'out'), (0.32, 0.97, 'out'), (0.8, 0.985), (3.2, 0.99, 'linear')])
c.k('wheelL', 'y', [(0, 0), (0.3, -10, 'out'), (3.2, -14, 'linear')])     # 한쪽 바퀴가 살짝 들림
c.k('earL', 'rot', [(0, 0), (0.25, 6, 'out'), (0.7, -14), (1.6, -8), (2.4, -13), (3.2, -10)]).k('earR', 'rot', [(0, 0), (0.25, -6, 'out'), (0.7, 16), (1.6, 10), (2.4, 15), (3.2, 12)])
c.k('ant', 'rot', [(0, 0), (0.3, -10, 'out'), (0.8, 8), (1.6, 3), (3.2, 6)])
st = 0.18 * SLOW; t0 = 0.14
w = [(0, 3), (t0, 0)] + seq(t0 + st, st, [1, 2, 3])
t1 = t0 + 4 * st + 0.3 * SLOW
w += [(t1, 0)] + seq(t1 + st * 0.4, st, [1, 2, 3])
c.wifi(w)
clips.append(c.build())
# D 당황·머뭇거림 2.6초: 기본 눈 유지, 차체가 작게 갸웃. 0→1→0, 멈춤, 1→2→0, 다시 강함으로
c = Clip('c_flust', 'D 당황', 2.6)
c.face(0, 'f00', 0)
c.k('body', 'rot', [(0, 0), (0.3, -7, 'out'), (1.0, -7), (1.3, 5, 'inout'), (1.9, 5), (2.3, 0), (2.6, 0)])
c.k('rig', 'y', [(0, 0), (0.2, 3, 'out'), (0.4, 0), (2.6, 0)])
c.k('ant', 'rot', [(0, 0), (0.38, 9, 'out'), (0.6, -4), (0.8, 0), (1.4, -8, 'out'), (1.65, 3), (1.85, 0), (2.6, 0)])
c.k('earL', 'rot', [(0, 0), (0.35, -8, 'out'), (0.7, 0), (1.35, 6, 'out'), (1.75, 0), (2.6, 0)]).k('earR', 'rot', [(0, 0), (0.35, -6, 'out'), (0.7, 0), (1.35, 8, 'out'), (1.75, 0), (2.6, 0)])
c.k('browL', 'y', [(0, 0), (0.3, -8, 'out'), (2.2, -8), (2.5, 0), (2.6, 0)]).k('browR', 'y', [(0, 0), (0.3, -8, 'out'), (2.2, -8), (2.5, 0), (2.6, 0)])
c.wifi([(0, 3), (0.25, 0), (0.45, 1), (0.65, 0), (1.15, 1), (1.33, 2), (1.55, 0), (2.25, 1), (2.35, 2), (2.45, 3)])
clips.append(c.build())
# E 공중제비·착지·정렬 4.4초: 웅크림(0→3 충전) → 오른쪽→왼쪽 포물선, 반시계 한 바퀴(전체 회전 그룹) → 착지(3→1, 0.25초 뒤 3) → 귀·안테나 반동 가라앉음 → 작아져 아래로(최종 정렬) → (시험용) 원래대로
c = Clip('c_flip', 'E 공중제비·착지·정렬', 4.4)
c.face(0, 'f00', 0).face(0.42, 'f01', 0.03).face(1.75, 'f00', 0.04)
X0, X1 = 48, -48
c.k('rig', 'x', [(0, 0), (0.15, X0, 'out'), (0.42, X0), (1.25, X1, 'linear'), (2.3, X1), (2.9, 0, 'inout'), (4.4, 0)])
c.k('rig', 'y', [(0, 0), (0.42, 0), (0.83, -0.3 * H, 'out'), (1.25, 0, 'in'), (2.3, 0), (2.9, 0.2 * H, 'inout'), (3.6, 0.2 * H), (4.2, 0, 'inout'), (4.4, 0)])
c.k('rig', 'sx', [(0, 1), (2.3, 1), (2.9, 0.62, 'inout'), (3.6, 0.62), (4.2, 1, 'inout'), (4.4, 1)]).k('rig', 'sy', [(0, 1), (2.3, 1), (2.9, 0.62, 'inout'), (3.6, 0.62), (4.2, 1, 'inout'), (4.4, 1)])
c.k('flip', 'rot', [(0, 0), (0.42, 0), (1.25, -360, 'inout'), (4.4, -360)])
c.k('body', 'sy', [(0, 1), (0.15, 1), (0.38, 0.86, 'out'), (0.46, 1.1, 'out'), (0.7, 1.0), (1.2, 1.0, 'in'), (1.3, 0.85, 'out'), (1.45, 1.05), (1.6, 0.98), (1.75, 1), (4.4, 1)])
c.k('body', 'sx', [(0, 1), (0.15, 1), (0.38, 1.1, 'out'), (0.46, 0.92, 'out'), (0.7, 1.0), (1.2, 1.0, 'in'), (1.3, 1.12, 'out'), (1.45, 0.97), (1.6, 1.01), (1.75, 1), (4.4, 1)])
c.k('earL', 'rot', [(0, 0), (0.38, 8), (0.5, -18, 'out'), (1.2, -10), (1.38, 16, 'out'), (1.58, -6), (1.78, 2), (1.95, 0), (4.4, 0)])
c.k('earR', 'rot', [(0, 0), (0.38, -8), (0.5, 18, 'out'), (1.2, 10), (1.38, -16, 'out'), (1.58, 6), (1.78, -2), (1.95, 0), (4.4, 0)])
c.k('ant', 'rot', [(0, 0), (0.5, -12, 'out'), (1.2, -6), (1.4, 14, 'out'), (1.6, -5), (1.8, 2), (1.95, 0), (4.4, 0)])
c.wifi([(0, 3), (0.02, 0)] + seq(0.12, 0.09, [1, 2, 3]) + [(1.27, 1), (1.52, 3)])
clips.append(c.build())
rules = [dict(id='r_blink', event='random', clip='c_blink', min=2.5, max=6)]
preview = [dict(label='A 대기', clip='c_idle'), dict(label='B 정면 달려오기', clip='c_run'), dict(label='C 환영 슬로모션', clip='c_welcome'), dict(label='D 당황', clip='c_flust'), dict(label='E 공중제비·착지·정렬', clip='c_flip')]
proj = dict(version=1, name='첨다니 (검수본)', stage=dict(w=400, h=400), parts=parts, clips=clips, rules=rules, baseClip='c_idle',
            faces=list(FACES.values()), preview=preview, display=dict(size=170, corner='right', margin=16, hideOnMobile=False, closable=False), assets=assets)
s = json.dumps(proj, ensure_ascii=False, separators=(',', ':'))
open(OUT + 'chumdani.json', 'w').write(s)
json.dump(dict(canvas=[N, N], split_x=SPLIT_X, stage_scale=S, rig_at_stage=RIG_AT, pivots=PIV, crops=crops, draw_order=[p['id'] for p in parts], parents={p['id']: p['parent'] for p in parts},
               wifi=dict(levels={'0': '약함 테두리만', '1': '아래 점', '2': '점+안쪽 곡선', '3': '전부'}, steps={c_['id']: c_.get('wifiSteps') for c_ in clips})), open(OUT + 'rig.json', 'w'), ensure_ascii=False, indent=1)
print('json KB', len(s) // 1024)
