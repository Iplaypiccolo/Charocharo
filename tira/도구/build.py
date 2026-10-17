# 티라 검수본 조립: work/fixed 보정본 → 자르기·절반 해상도 → charo-pet 형식 JSON
# 좌표는 모두 원래 캔버스 1254×1254. 잘라낸 그림마다 원래 위치(x,y,w,h)를 기록.
import cv2, numpy as np, json, base64, os
from PIL import Image, ImageDraw, ImageFont
F = '/home/claude/tira/work/fixed/'; OUT = '/home/claude/tira/out/'; os.makedirs(OUT + 'crops', exist_ok=True)
N = 1254; SPLIT_X = 627
SIGN_TEXT = '환영'
def load(n): return cv2.imread(F + n + '.png', cv2.IMREAD_UNCHANGED)
def half(im, side):
    im = im.copy()
    if side == 'L': im[:, SPLIT_X:] = 0
    else: im[:, :SPLIT_X] = 0
    return im
# 팻말 글자: 빈 판의 흰 영역(154~1099, 366~671) 가운데에 코드로 그림 → 팻말과 같은 좌표계라 함께 움직임
def sign_text(txt):
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc' if os.path.exists('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc') else '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 250)
    bx0, by0, bx1, by1 = 154, 366, 1099, 671
    w = d.textlength(txt, font=fnt); asc, desc = fnt.getmetrics()
    x = (bx0 + bx1) / 2 - w / 2; y = (by0 + by1) / 2 - (asc + desc) / 2 - 10
    d.text((x, y), txt, font=fnt, fill=(74, 40, 20, 255))
    a = np.array(img); return cv2.cvtColor(a, cv2.COLOR_RGBA2BGRA)
assets, crops = {}, {}
def asset(key, im, pad=3):
    a = im[..., 3] > 8; ys, xs = np.where(a)
    x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad); x1, y1 = min(N, xs.max() + pad + 1), min(N, ys.max() + pad + 1)
    c = im[y0:y1, x0:x1]; cv2.imwrite(OUT + 'crops/' + key + '.png', c)
    sm = cv2.resize(c, (max(1, round(c.shape[1] / 2)), max(1, round(c.shape[0] / 2))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode('.png', sm, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assets['t_' + key] = 'data:image/png;base64,' + base64.b64encode(buf.tobytes()).decode()
    crops[key] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0), canvas=[N, N])
    return dict(asset='t_' + key, x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
def img(name, key, im): d = asset(key, im); d['name'] = name; return d
def centre(im):
    ys, xs = np.where(im[..., 3] > 128); return [round(float((xs.min() + xs.max()) / 2), 1), round(float((ys.min() + ys.max()) / 2), 1)]


src = {n: load(n) for n in ['꼬리', '화면왼발', '화면오른발', '몸통바탕', '화면왼팔', '화면오른팔', '눈_기본', '눈_환영웃음', '입_기본이빨', '입_환영웃음', '팻말_빈판']}
eB = {s: half(src['눈_기본'], s) for s in 'LR'}; eW = {s: half(src['눈_환영웃음'], s) for s in 'LR'}
txt = sign_text(SIGN_TEXT)
PIV = {
    'body': (627, 1050),                         # 몸통 아래 가운데
    'tail': (872, 948),                          # 꼬리 뿌리(몸통 속)
    'footL': (497, 1035), 'footR': (745, 1025),  # 발 위쪽(몸통 속)
    'armL': (372, 772), 'armR': (815, 775),      # 팔 뿌리(어깨 쪽, 몸통 위)
    'eyeL': tuple(centre(eB['L'])), 'eyeR': tuple(centre(eB['R'])),
    'mouth': (612, 586),
    'sign': (626.5, 980),                        # 팻말 막대 아래쪽(팔이 잡는 곳)
}
TIP_L = (262, 790)        # 화면 왼팔 끝(팻말을 잡는 곳)
SIGN_S = 0.42             # 팻말 크기(판 폭 약 400px)
S = 0.245; BODY_AT = (215, 340)
def R(x, y, rot=0, s=1, op=1): return dict(x=x, y=y, rot=rot, sx=s, sy=s, op=op, img=0)
def part(id, name, parent, piv, images, follow=None, rest=None):
    if rest is None: rest = R(*BODY_AT, 0, S) if parent is None else R(*piv)
    return dict(id=id, name=name, parent=parent, pivot=dict(x=piv[0], y=piv[1]), rest=rest, images=images, follow=follow or dict(on=False, max=0))
parts = [   # 뒤 → 앞: 팻말(뒤) · 꼬리 · 발 → 몸통 → 팻말(앞) → 팔 → 눈·입
    part('sign', '팻말(뒤)', 'armL', PIV['sign'], [img('빈 팻말', 'sign', src['팻말_빈판'])], rest=R(*TIP_L, 0, SIGN_S)),
    part('signText', '팻말 글자(뒤)', 'sign', PIV['sign'], [img(SIGN_TEXT, 'sign_text', txt)]),
    part('tail', '꼬리', 'body', PIV['tail'], [img('꼬리', 'tail', src['꼬리'])]),
    part('footL', '화면 왼발', 'body', PIV['footL'], [img('화면 왼발', 'footL', src['화면왼발'])]),
    part('footR', '화면 오른발', 'body', PIV['footR'], [img('화면 오른발', 'footR', src['화면오른발'])]),
    part('body', '몸통바탕(머리·등 돌기 포함)', None, PIV['body'], [img('몸통바탕', 'body', src['몸통바탕'])]),
    part('signF', '팻말(앞)', 'sign', PIV['sign'], [dict(img('빈 팻말', 'sign', src['팻말_빈판']))]),
    part('signTextF', '팻말 글자(앞)', 'signF', PIV['sign'], [dict(img(SIGN_TEXT, 'sign_text', txt))]),
    part('armL', '화면 왼팔', 'body', PIV['armL'], [img('화면 왼팔', 'armL', src['화면왼팔'])]),
    part('armR', '화면 오른팔', 'body', PIV['armR'], [img('화면 오른팔', 'armR', src['화면오른팔'])]),
    part('eyeL', '화면 왼눈', 'body', PIV['eyeL'], [img('기본 점눈', 'eyeL_basic', eB['L']), img('웃는 눈', 'eyeL_welcome', eW['L'])], dict(on=True, max=12)),
    part('eyeR', '화면 오른눈', 'body', PIV['eyeR'], [img('기본 점눈', 'eyeR_basic', eB['R']), img('웃는 눈', 'eyeR_welcome', eW['R'])], dict(on=True, max=12)),
    part('mouth', '입', 'body', PIV['mouth'], [img('기본 이빨 입', 'mouth_basic', src['입_기본이빨']), img('환영 웃음 입', 'mouth_welcome', src['입_환영웃음'])], dict(on=True, max=6)),
]
SIGNS = ('sign', 'signText'); FRONTS = ('signF', 'signTextF')
FACES = {'f00': dict(id='f00', name='기본', img=dict(eyeL=0, eyeR=0, mouth=0), mods={}),
         'f01': dict(id='f01', name='환영', img=dict(eyeL=1, eyeR=1, mouth=1), mods={})}
H = 216
class Clip:
    def __init__(s, id, name, dur, loop=False, follow='center', **kw):
        s.c = dict(id=id, name=name, dur=dur, loop=loop, follow=follow, tracks={}); s.c.update(kw)
    def k(s, part, prop, keys):
        out = {}
        for x in keys: t = round(x[0], 3); out[t] = dict(t=t, v=round(float(x[1]), 4), e=x[2] if len(x) > 2 else 'inout')
        s.c['tracks'].setdefault(part, {})[prop] = [out[t] for t in sorted(out)]; return s
    def face(s, t, fid, f=0.04):
        for p_, v in FACES[fid]['img'].items(): s.c['tracks'].setdefault(p_, {}).setdefault('img', []).append(dict(t=round(t, 3), v=v, f=f))
        return s
    def ops(s, back, front, end):   # 팻말 뒤/앞 층 투명도
        for p_ in SIGNS: s.k(p_, 'op', back + [(end, back[-1][1])])
        for p_ in FRONTS: s.k(p_, 'op', front + [(end, front[-1][1])])
        return s
    def build(s):
        for tr in s.c['tracks'].values():
            if 'img' in tr: tr['img'].sort(key=lambda d: d['t'])
        return s.c
def alt(t0, t1, step, a, b, e='inout'):
    out, i, t = [], 0, t0
    while t <= t1 + 1e-9: out.append((round(t, 3), a if i % 2 == 0 else b, e)); i += 1; t = round(t + step, 3)
    return out
def lag(keys, dt, scale=1.0): return [(round(k[0] + dt, 3), k[1] * scale) + tuple(k[2:]) for k in keys]
clips = []
# A 대기: 작게 들썩, 꼬리가 조금 늦게
c = Clip('t_idle', 'A 대기', 3.0, loop=True, follow='on')
c.k('body', 'sy', [(0, 1), (1.5, 1.025), (3, 1)]).k('body', 'sx', [(0, 1), (1.5, 0.99), (3, 1)])
c.k('tail', 'rot', [(0, 0), (0.35, 0), (1.85, -4), (3, 0)])
c.k('armL', 'rot', [(0, 0), (1.5, 3), (3, 0)]).k('armR', 'rot', [(0, 0), (1.5, -3), (3, 0)])
c.ops([(0, 0)], [(0, 0)], 3)
clips.append(c.build())
c = Clip('t_blink', '깜빡임', 0.22, follow='on')
for s_ in 'LR': c.k('eye' + s_, 'sy', [(0, 1, 'in'), (0.07, 0.1, 'out'), (0.18, 1)])
clips.append(c.build())
# B 정면 우다다: 짧은 발 빠르게, 통통, 팔 엇박자, 꼬리는 기울기보다 늦게
c = Clip('t_run', 'B 정면 우다다', 2.4)
c.face(0, 'f00', 0); c.ops([(0, 0)], [(0, 0)], 2.4)
STEP = 0.12; steps = [round(0.05 + i * STEP, 3) for i in range(17) if 0.05 + i * STEP < 2.06]
c.k('body', 'sx', [(0, 0.55), (2.05, 1.0, 'out'), (2.4, 1)]).k('body', 'sy', [(0, 0.55), (2.05, 1.0, 'out'), (2.4, 1)])
yk = [(0, -0.2 * H)]
for t in steps:
    base = -0.2 * H * (1 - min(1, t / 2.05)) ** 1.6
    yk += [(t, base, 'out'), (round(t + STEP / 2, 3), base - 0.03 * H, 'in')]
c.k('body', 'y', yk + [(2.15, 0, 'out'), (2.4, 0)])
tilt = [(t, 4 if i % 2 == 0 else -4) for i, t in enumerate(steps)]
c.k('body', 'rot', [(0, 0)] + tilt + [(2.2, 0), (2.4, 0)])
c.k('tail', 'rot', [(0, 0)] + lag(tilt, 0.08, 2.5) + [(2.32, 0), (2.4, 0)])
fl, fr = [(0, 0)], [(0, 0)]
for i, t in enumerate(steps):
    g = fl if i % 2 == 0 else fr; g += [(t, -16, 'out'), (round(t + STEP * 0.8, 3), 0, 'in')]
c.k('footL', 'y', fl + [(2.4, 0)]).k('footR', 'y', fr + [(2.4, 0)])
c.k('armL', 'rot', [(0, 0)] + [(round(t + 0.03, 3), 22 if i % 2 else -10) for i, t in enumerate(steps)] + [(2.2, 0), (2.4, 0)])
c.k('armR', 'rot', [(0, 0)] + [(round(t + 0.03, 3), -22 if i % 2 == 0 else 10) for i, t in enumerate(steps)] + [(2.2, 0), (2.4, 0)])
clips.append(c.build())
# C 환영 슬로모션: 왼쪽 바깥으로 기울고 오른발이 들림. 왼팔로 '환영' 팻말을 들어 올림(몸 뒤 → 다 올리면 앞으로)
AL = 78    # 왼팔 들기
c = Clip('t_welcome', 'C 환영 슬로모션', 3.2)
c.face(0, 'f00', 0).face(0.14, 'f01', 0.03)
c.k('body', 'rot', [(0, 0), (0.12, 3, 'out'), (0.32, -8, 'out'), (3.2, -11, 'linear')])
c.k('body', 'x', [(0, 0), (0.32, -6, 'out'), (3.2, -9, 'linear')])
c.k('body', 'y', [(0, 0), (0.12, 4, 'out'), (0.32, -6, 'out'), (3.2, -9, 'linear')])
c.k('body', 'sy', [(0, 1), (0.12, 0.92, 'out'), (0.32, 1.05, 'out'), (0.8, 1.03), (3.2, 1.02, 'linear')])
c.k('body', 'sx', [(0, 1), (0.12, 1.06, 'out'), (0.32, 0.97, 'out'), (0.8, 0.985), (3.2, 0.99, 'linear')])
c.k('footR', 'y', [(0, 0), (0.3, -14, 'out'), (3.2, -18, 'linear')]).k('footR', 'x', [(0, 0), (0.3, 40, 'out'), (3.2, 44, 'linear')]).k('footR', 'rot', [(0, 0), (0.3, -30, 'out'), (3.2, -34, 'linear')])
c.k('footL', 'rot', [(0, 0), (0.3, 5, 'out'), (3.2, 7, 'linear')])
c.k('armL', 'rot', [(0, 0), (0.4, AL, 'out'), (1.4, AL + 4), (2.4, AL - 2), (3.2, AL + 3)])
c.k('armR', 'rot', [(0, 0), (0.3, -24, 'out'), (1.5, -18), (3.2, -26)])
c.k('tail', 'rot', [(0, 0), (0.25, -6, 'out'), (0.65, 14, 'out'), (1.3, 8), (2.2, 12), (3.2, 9)])   # 늦게 휙
TILT = -24; SR = -AL + TILT
c.k('sign', 'rot', [(0, TILT), (0.4, SR, 'out'), (0.75, SR + 7), (1.3, SR - 4), (2.1, SR + 2), (3.2, SR - 2)])
c.ops([(0, 0), (0.1, 0, 'linear'), (0.24, 1), (0.32, 1, 'step'), (0.321, 0)], [(0, 0, 'step'), (0.32, 1)], 3.2)
clips.append(c.build())
# D 마무리: 들린 발을 디뎌 균형 → 팻말 흔들림 가라앉음 → 내리고 숨김 → 작게 → (시험용) 원래 크기
END = 3.0; c = Clip('t_finish', 'D 마무리', END)
c.face(0, 'f01', 0).face(0.62, 'f00', 0.04)
c.k('body', 'rot', [(0, -11), (0.22, 4, 'out'), (0.42, -2), (0.6, 0), (END, 0)])
c.k('body', 'x', [(0, -9), (0.3, 0, 'out'), (END, 0)])
c.k('body', 'y', [(0, -9), (0.2, 0, 'in'), (0.3, 4), (0.42, 0), (0.8, 0, 'inout'), (1.3, 0.17 * H, 'inout'), (2.2, 0.17 * H), (2.75, 0, 'inout'), (END, 0)])
c.k('body', 'sy', [(0, 1.02), (0.2, 0.9, 'out'), (0.34, 1.04), (0.46, 1.0), (0.8, 1.0, 'inout'), (1.3, 0.6, 'inout'), (1.7, 0.612), (2.2, 0.6), (2.75, 1.0, 'inout'), (END, 1)])
c.k('body', 'sx', [(0, 0.99), (0.2, 1.07, 'out'), (0.34, 0.98), (0.46, 1.0), (0.8, 1.0, 'inout'), (1.3, 0.6, 'inout'), (1.7, 0.596), (2.2, 0.6), (2.75, 1.0, 'inout'), (END, 1)])
c.k('footR', 'y', [(0, -18), (0.2, 0, 'in'), (0.28, -5), (0.38, 0), (END, 0)]).k('footR', 'x', [(0, 44), (0.2, 0, 'in'), (END, 0)]).k('footR', 'rot', [(0, -34), (0.2, 0, 'in'), (0.3, 5), (0.42, 0), (END, 0)])
c.k('footL', 'rot', [(0, 7), (0.2, 0), (0.3, -4), (0.42, 0), (END, 0)])
c.k('armL', 'rot', [(0, AL + 3), (0.25, AL - 6, 'out'), (0.7, 0, 'inout'), (0.85, -6), (1.0, 0), (END, 0)])
c.k('armR', 'rot', [(0, -26), (0.3, 8, 'out'), (0.5, -3), (0.7, 0), (END, 0)])
c.k('tail', 'rot', [(0, 9), (0.3, 9), (0.5, -10, 'out'), (0.75, 5), (0.95, -2), (1.15, 0), (END, 0)])
c.k('sign', 'rot', [(0, SR - 2), (0.25, SR + 12, 'out'), (0.45, SR - 5), (0.7, TILT, 'inout'), (END, TILT)])   # 흔들림이 가라앉음
c.ops([(0, 0, 'step'), (0.42, 1), (0.5, 1), (0.68, 0)], [(0, 1, 'step'), (0.42, 0)], END)
clips.append(c.build())
rules = [dict(id='r_blink', event='random', clip='t_blink', min=2.5, max=6)]
preview = [dict(label='A 대기', clip='t_idle'), dict(label='B 정면 우다다', clip='t_run'), dict(label='C 환영 슬로모션', clip='t_welcome'), dict(label='D 마무리', clip='t_finish')]
proj = dict(version=1, name='티라 (검수본)', stage=dict(w=400, h=400), parts=parts, clips=clips, rules=rules, baseClip='t_idle',
            faces=list(FACES.values()), preview=preview, display=dict(size=170, corner='right', margin=16, hideOnMobile=False, closable=False), assets=assets)
s = json.dumps(proj, ensure_ascii=False, separators=(',', ':'))
open(OUT + 'tira.json', 'w').write(s)
json.dump(dict(canvas=[N, N], split_x=SPLIT_X, stage_scale=S, body_at_stage=BODY_AT, pivots=PIV, sign=dict(parent='armL', grip_on_arm=TIP_L, scale=SIGN_S, text=SIGN_TEXT, text_box=[154, 366, 1099, 671]),
               crops=crops, draw_order=[p['id'] for p in parts], parents={p['id']: p['parent'] for p in parts}), open(OUT + 'rig.json', 'w'), ensure_ascii=False, indent=1)
print('json KB', len(s) // 1024)
