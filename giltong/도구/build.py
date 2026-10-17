# 길통이 검수본 조립: work/fixed 의 보정본 → 자르기·절반 해상도 → charo-pet 형식 JSON
# 원래 캔버스 1254×1254 좌표를 그대로 쓴다(잘라낸 그림마다 x,y,w,h = 원래 캔버스 안 위치).
import cv2, numpy as np, json, base64, os, sys
F = '/home/claude/giltong/work/fixed/'; OUT = '/home/claude/giltong/out/'; os.makedirs(OUT + 'crops', exist_ok=True)
N = 1254; SPLIT_X = 627          # 두 눈·두 눈썹 사이 빈 세로줄
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
    assets['g_' + key] = 'data:image/png;base64,' + base64.b64encode(buf.tobytes()).decode()
    crops[key] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0), canvas=[N, N])
    return dict(asset='g_' + key, x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
def img(name, key, im): d = asset(key, im); d['name'] = name; return d
def centre(im):
    ys, xs = np.where(im[..., 3] > 128); return [round(float((xs.min() + xs.max()) / 2), 1), round(float((ys.min() + ys.max()) / 2), 1)]

src = {n: load(n) for n in ['망토', '화면왼다리', '화면오른다리', '화면왼팔', '화면오른팔', '몸통', '얼굴바탕', '눈_기본', '눈_환영', '눈썹', '입_기본미소', '입_함박웃음']}
eB = {s: half(src['눈_기본'], s) for s in 'LR'}; eW = {s: half(src['눈_환영'], s) for s in 'LR'}; br = {s: half(src['눈썹'], s) for s in 'LR'}

# 회전 기준점(원래 캔버스 좌표)
PIV = {
    'body': (627, 1005),   # 옷 아랫단 가운데(엉덩이) — 들썩·늘이기의 중심
    'cape': (626, 790),    # 목 뒤
    'legL': (563, 990), 'legR': (690, 1000),   # 다리 위쪽 붙는 곳(옷 속)
    'armL': (520, 822), 'armR': (734, 822),    # 어깨(옷 속)
    'head': (627, 795),    # 목
    'eyeL': tuple(centre(eB['L'])), 'eyeR': tuple(centre(eB['R'])),
    'browL': tuple(centre(br['L'])), 'browR': tuple(centre(br['R'])),
    'mouth': (627, 676),
}
S = 0.24                     # 무대 400×400 에서의 크기 (캐릭터 높이 약 286칸)
BODY_AT = (200, 302)         # 무대에서 엉덩이 위치
def R(x, y, rot=0, s=1): return dict(x=x, y=y, rot=rot, sx=s, sy=s, op=1, img=0)
def part(id, name, parent, piv, images, follow=None):
    rest = R(*BODY_AT, 0, S) if parent is None else R(*piv)
    return dict(id=id, name=name, parent=parent, pivot=dict(x=piv[0], y=piv[1]), rest=rest, images=images, follow=follow or dict(on=False, max=0))
parts = [   # 뒤 → 앞
    part('cape', '망토', 'body', PIV['cape'], [img('망토', 'cape', src['망토'])]),
    part('legL', '화면 왼다리', 'body', PIV['legL'], [img('화면 왼다리', 'legL', src['화면왼다리'])]),
    part('legR', '화면 오른다리', 'body', PIV['legR'], [img('화면 오른다리', 'legR', src['화면오른다리'])]),
    part('armL', '화면 왼팔', 'body', PIV['armL'], [img('화면 왼팔', 'armL', src['화면왼팔'])]),
    part('armR', '화면 오른팔', 'body', PIV['armR'], [img('화면 오른팔', 'armR', src['화면오른팔'])]),
    part('body', '몸통', None, PIV['body'], [img('몸통', 'body', src['몸통'])]),
    part('head', '얼굴바탕(모자·귀 포함)', 'body', PIV['head'], [img('얼굴바탕', 'head', src['얼굴바탕'])]),
    part('eyeL', '화면 왼눈', 'head', PIV['eyeL'], [img('기본 눈', 'eyeL_basic', eB['L']), img('환영 눈 >', 'eyeL_welcome', eW['L'])], dict(on=True, max=18)),
    part('eyeR', '화면 오른눈', 'head', PIV['eyeR'], [img('기본 눈', 'eyeR_basic', eB['R']), img('환영 눈 <', 'eyeR_welcome', eW['R'])], dict(on=True, max=18)),
    part('browL', '화면 왼눈썹', 'head', PIV['browL'], [img('눈썹', 'browL', br['L'])], dict(on=True, max=12)),
    part('browR', '화면 오른눈썹', 'head', PIV['browR'], [img('눈썹', 'browR', br['R'])], dict(on=True, max=12)),
    part('mouth', '입', 'head', PIV['mouth'], [img('기본 미소', 'mouth_smile', src['입_기본미소']), img('함박웃음', 'mouth_big', src['입_함박웃음'])], dict(on=True, max=8)),
]
# 표정 두 세트: 눈·눈썹·입을 같은 순간에 바꿈
FACES = {'f00': dict(id='f00', name='기본', img=dict(eyeL=0, eyeR=0, browL=0, browR=0, mouth=0), mods={}),
         'f01': dict(id='f01', name='환영', img=dict(eyeL=1, eyeR=1, browL=0, browR=0, mouth=1), mods={'browL': {'y': -10}, 'browR': {'y': -10}})}

H = 286   # 무대에서 캐릭터 높이(칸)
class Clip:
    def __init__(s, id, name, dur, loop=False, follow='center', **kw):
        s.c = dict(id=id, name=name, dur=dur, loop=loop, follow=follow, tracks={}); s.c.update(kw); s.faces = []
    def k(s, part, prop, keys):
        out = {}
        for x in keys: t = round(x[0], 3); out[t] = dict(t=t, v=round(float(x[1]), 4), e=x[2] if len(x) > 2 else 'inout')
        s.c['tracks'].setdefault(part, {})[prop] = [out[t] for t in sorted(out)]; return s
    def face(s, t, fid, f=0.04):
        s.faces.append((t, fid))
        for p_, v in FACES[fid]['img'].items():
            s.c['tracks'].setdefault(p_, {}).setdefault('img', []).append(dict(t=round(t, 3), v=v, f=f))
        return s
    def build(s):
        # 표정 변형(환영 때 눈썹 올림)을 표정 바뀌는 순간에 0.07초로
        for p_ in ('browL', 'browR'):
            keys = [dict(t=0, v=0, e='step')]; cur = 0
            for t, fid in sorted(s.faces):
                v = FACES[fid]['mods'].get(p_, {}).get('y', 0)
                if v != cur: keys += [dict(t=round(t, 3), v=cur, e='out'), dict(t=round(t + 0.07, 3), v=v, e='inout')]; cur = v
            if len(keys) > 1: s.c['tracks'].setdefault(p_, {})['y'] = keys
        for p_, tr in s.c['tracks'].items():
            if 'img' in tr: tr['img'].sort(key=lambda d: d['t'])
        return s.c
def alt(t0, t1, step, a, b, e='inout'):
    out, i, t = [], 0, t0
    while t <= t1 + 1e-9: out.append((round(t, 3), a if i % 2 == 0 else b, e)); i += 1; t = round(t + step, 3)
    return out
def neg(keys): return [(k[0], -k[1]) + tuple(k[2:]) for k in keys]

clips = []
# ① 대기 (평소 반복): 작은 숨쉬기 + 기본 표정
c = Clip('g_idle', '① 대기', 3.0, loop=True, follow='on')
c.k('body', 'sy', [(0, 1), (1.5, 1.02), (3, 1)]).k('body', 'sx', [(0, 1), (1.5, 0.993), (3, 1)])
c.k('head', 'rot', [(0, 0), (1.6, 1.2), (3, 0)])
AD = 48   # 자연스럽게 선 자세: 팔을 수평에서 48° 내림(대기·동작 끝 자세)
c.k('armL', 'rot', [(0, -AD), (1.5, -AD + 2.5), (3, -AD)]).k('armR', 'rot', [(0, AD), (1.5, AD - 2.5), (3, AD)])
c.k('cape', 'rot', [(0, 0), (1.8, -1.2), (3, 0)])
clips.append(c.build())
# 깜빡임: 눈을 세로로 눌렀다 폄(기본 눈일 때만, 평소 동작 중에만 엔진이 재생)
c = Clip('g_blink', '깜빡임', 0.24, follow='on')
for s_ in 'LR': c.k('eye' + s_, 'sy', [(0, 1, 'in'), (0.08, 0.12, 'out'), (0.2, 1)])
clips.append(c.build())

# ② 정면 달리기 (2.4초): 멀리서(작게·위쪽) 다가오며 커짐. 팔·다리 엇박자, 걸음마다 들썩
c = Clip('g_run', '② 정면 달리기', 2.4)
c.face(0, 'f00', 0)
STEP = 0.15; steps = [round(0.05 + i * STEP, 3) for i in range(14)]          # 0.05~2.0
c.k('body', 'sx', [(0, 0.55), (2.0, 1.0, 'out'), (2.4, 1.0)]).k('body', 'sy', [(0, 0.55), (2.0, 1.0, 'out'), (2.4, 1.0)])
yk = [(0, -0.18 * H)]
for i, t in enumerate(steps):
    base = -0.18 * H * (1 - min(1, t / 2.0)) ** 1.6
    yk += [(t, base, 'out'), (round(t + STEP / 2, 3), base - 0.035 * H * (1 - t / 2.6), 'in')]
c.k('body', 'y', yk + [(2.12, 0, 'out'), (2.4, 0)])
c.k('body', 'rot', [(0, 0)] + [(t, 2.5 if i % 2 == 0 else -2.5) for i, t in enumerate(steps)] + [(2.15, 0), (2.4, 0)])
legs = [(t, 24 if i % 2 == 0 else -6) for i, t in enumerate(steps)]
c.k('legL', 'rot', [(0, 0)] + legs + [(2.15, 0), (2.4, 0)])
c.k('legR', 'rot', [(0, 0)] + [(t, -24 if i % 2 else 6) for i, t in enumerate(steps)] + [(2.15, 0), (2.4, 0)])
c.k('armL', 'rot', [(0, -AD)] + [(round(t + 0.03, 3), -64 if i % 2 == 0 else -20) for i, t in enumerate(steps)] + [(2.18, -AD), (2.4, -AD)])
c.k('armR', 'rot', [(0, AD)] + [(round(t + 0.03, 3), 20 if i % 2 == 0 else 64) for i, t in enumerate(steps)] + [(2.18, AD), (2.4, AD)])
c.k('head', 'rot', [(0, 0)] + [(round(t + 0.05, 3), -2 if i % 2 == 0 else 2) for i, t in enumerate(steps)] + [(2.2, 0), (2.4, 0)])
c.k('cape', 'rot', [(0, 0)] + [(round(t + 0.08, 3), 5 if i % 2 == 0 else -5) for i, t in enumerate(steps)] + [(2.25, 0), (2.4, 0)])
c.k('cape', 'sy', [(0, 1), (0.3, 1.04), (2.0, 1.04), (2.3, 1), (2.4, 1)])
clips.append(c.build())

# ③ 환영 슬로모션 (3.2초): 급정지(0~0.32, 보통 속도) → 넘어질 듯한 자세에서 아주 느리게 계속 움직임. 망토는 늦게 따라옴
WEL = dict(body_rot=9, body_x=0.03 * H, armL=24, armR=-16, legL=42, legR=-5, head=5, cape=-12)
c = Clip('g_welcome', '③ 환영 슬로모션', 3.2)
c.face(0, 'f00', 0).face(0.14, 'f01', 0.03)
c.k('body', 'rot', [(0, 0), (0.12, -3, 'out'), (0.32, WEL['body_rot'], 'out'), (3.2, WEL['body_rot'] + 3, 'linear')])
c.k('body', 'x', [(0, 0), (0.32, WEL['body_x'], 'out'), (3.2, WEL['body_x'] + 0.012 * H, 'linear')])
c.k('body', 'y', [(0, 0), (0.12, 4, 'out'), (0.32, -0.025 * H, 'out'), (3.2, -0.035 * H, 'linear')])
c.k('body', 'sy', [(0, 1), (0.12, 0.93, 'out'), (0.32, 1.05, 'out'), (0.8, 1.03), (3.2, 1.02, 'linear')])
c.k('body', 'sx', [(0, 1), (0.12, 1.05, 'out'), (0.32, 0.97, 'out'), (0.8, 0.985), (3.2, 0.99, 'linear')])
c.k('armL', 'rot', [(0, -AD), (0.36, WEL['armL'], 'out'), (1.3, WEL['armL'] + 4), (2.3, WEL['armL'] - 3), (3.2, WEL['armL'] + 3)])   # 아주 느리게 흔드는 인사
c.k('armR', 'rot', [(0, AD), (0.36, WEL['armR'], 'out'), (3.2, WEL['armR'] - 6, 'linear')])
c.k('legL', 'rot', [(0, 0), (0.3, WEL['legL'], 'out'), (3.2, WEL['legL'] + 5, 'linear')])
c.k('legR', 'rot', [(0, 0), (0.3, WEL['legR'], 'out'), (3.2, WEL['legR'] - 2, 'linear')])
c.k('head', 'rot', [(0, 0), (0.42, WEL['head'], 'out'), (3.2, WEL['head'] + 2, 'linear')])
c.k('cape', 'rot', [(0, 0), (0.2, 4, 'out'), (0.6, WEL['cape'], 'out'), (1.8, WEL['cape'] - 4), (3.2, WEL['cape'] - 6)])   # 뒤늦게 펄럭
c.k('cape', 'sy', [(0, 1), (0.6, 1.06, 'out'), (3.2, 1.08, 'linear')])
clips.append(c.build())

# ④ 마무리 (3.0초): 균형 회복 → 작은 기본형으로 축소·아래로 → 작게 대기 → (시험용) 원래 크기로 복귀
END = 3.0; c = Clip('g_finish', '④ 마무리', END)
wr = WEL['body_rot'] + 3
c.face(0, 'f01', 0).face(0.62, 'f00', 0.04)
c.k('body', 'rot', [(0, wr), (0.22, -4, 'out'), (0.42, 2), (0.6, 0), (END, 0)])
c.k('body', 'x', [(0, WEL['body_x'] + 0.012 * H), (0.3, 0, 'out'), (END, 0)])
c.k('body', 'y', [(0, -0.035 * H), (0.2, 0, 'in'), (0.3, 3), (0.42, 0), (0.7, 0, 'inout'), (1.2, 0.17 * H, 'inout'), (2.2, 0.17 * H), (2.75, 0, 'inout'), (END, 0)])
c.k('body', 'sy', [(0, 1.02), (0.2, 0.92, 'out'), (0.34, 1.03), (0.46, 1.0), (0.7, 1.0, 'inout'), (1.2, 0.6, 'inout'), (1.6, 0.612), (2.0, 0.6), (2.2, 0.6), (2.75, 1.0, 'inout'), (END, 1)])
c.k('body', 'sx', [(0, 0.99), (0.2, 1.06, 'out'), (0.34, 0.98), (0.46, 1.0), (0.7, 1.0, 'inout'), (1.2, 0.6, 'inout'), (1.6, 0.596), (2.0, 0.6), (2.2, 0.6), (2.75, 1.0, 'inout'), (END, 1)])
c.k('armL', 'rot', [(0, WEL['armL'] + 4), (0.3, -10, 'out'), (0.5, -2), (0.62, -2), (0.95, -AD - 4), (1.1, -AD), (END, -AD)])
c.k('armR', 'rot', [(0, WEL['armR'] - 6), (0.3, 10, 'out'), (0.5, 2), (0.62, 2), (0.97, AD + 4), (1.12, AD), (END, AD)])
c.k('legL', 'rot', [(0, WEL['legL'] + 5), (0.2, 0, 'in'), (0.3, -4), (0.45, 0), (END, 0)])
c.k('legR', 'rot', [(0, WEL['legR'] - 2), (0.2, 0, 'in'), (0.3, 3), (0.45, 0), (END, 0)])
c.k('head', 'rot', [(0, WEL['head'] + 2), (0.3, -3, 'out'), (0.55, 1), (0.75, 0), (END, 0)])
c.k('cape', 'rot', [(0, WEL['cape'] - 6), (0.35, 6, 'out'), (0.55, -3), (0.8, 1), (1.0, 0), (END, 0)])
c.k('cape', 'sy', [(0, 1.08), (0.4, 1.0), (END, 1)])
clips.append(c.build())

rules = [dict(id='r_blink', event='random', clip='g_blink', min=2.5, max=6)]
preview = [dict(label='① 대기', clip='g_idle'), dict(label='② 정면 달리기', clip='g_run'),
           dict(label='③ 환영 슬로모션', clip='g_welcome'), dict(label='④ 마무리', clip='g_finish')]
proj = dict(version=1, name='길통이 (검수본)', stage=dict(w=400, h=400), parts=parts, clips=clips, rules=rules, baseClip='g_idle',
            faces=list(FACES.values()), preview=preview, display=dict(size=170, corner='right', margin=16, hideOnMobile=False, closable=False), assets=assets)
s = json.dumps(proj, ensure_ascii=False, separators=(',', ':'))
open(OUT + 'giltong.json', 'w').write(s)
json.dump(dict(canvas=[N, N], split_x=SPLIT_X, stage_scale=S, body_at_stage=BODY_AT, pivots=PIV, crops=crops,
               draw_order=[p['id'] for p in parts], parents={p['id']: p['parent'] for p in parts}),
          open(OUT + 'rig.json', 'w'), ensure_ascii=False, indent=1)
print('json KB', len(s) // 1024, 'pivots', PIV)
