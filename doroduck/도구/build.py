# 도로덕 검수본 조립: work/fixed 보정본 → 자르기·절반 해상도 → charo-pet 형식 JSON
# 좌표는 모두 원래 캔버스 1254×1254. 잘라낸 그림마다 원래 위치(x,y,w,h)를 기록.
import cv2, numpy as np, json, base64, os
from PIL import Image, ImageDraw, ImageFont
F = '/home/claude/doroduck/work/fixed/'; OUT = '/home/claude/doroduck/out/'; os.makedirs(OUT + 'crops', exist_ok=True)
N = 1254; SPLIT_X = 627
SIGN_TEXT = '합니다!'
def load(n): return cv2.imread(F + n + '.png', cv2.IMREAD_UNCHANGED)
def half(im, side):
    im = im.copy()
    if side == 'L': im[:, SPLIT_X:] = 0
    else: im[:, :SPLIT_X] = 0
    return im
# 팻말 글자: 빈 판의 흰 영역(154~1099, 366~671) 가운데에 코드로 그림 → 팻말과 같은 좌표계라 함께 움직임
def sign_text(txt):
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc' if os.path.exists('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc') else '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 210)
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
    assets['d_' + key] = 'data:image/png;base64,' + base64.b64encode(buf.tobytes()).decode()
    crops[key] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0), canvas=[N, N])
    return dict(asset='d_' + key, x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
def img(name, key, im): d = asset(key, im); d['name'] = name; return d
def centre(im):
    ys, xs = np.where(im[..., 3] > 128); return [round(float((xs.min() + xs.max()) / 2), 1), round(float((ys.min() + ys.max()) / 2), 1)]

src = {n: load(n) for n in ['화면왼날개', '화면오른날개', '화면왼발', '화면오른발', '몸통바탕', '눈_기본', '눈_환영웃음', '부리_붉은타원', '팻말_빈판']}
eB = {s: half(src['눈_기본'], s) for s in 'LR'}; eW = {s: half(src['눈_환영웃음'], s) for s in 'LR'}
txt = sign_text(SIGN_TEXT)

PIV = {
    'body': (627, 995),                         # 몸통 아래 가운데
    'wingL': (372, 728), 'wingR': (880, 722),   # 날개 뿌리(몸통 윤곽 안쪽 약 25px)
    'footL': (548, 990), 'footR': (705, 990),   # 발 위쪽 붙는 곳(몸통 속)
    'eyeL': tuple(centre(eB['L'])), 'eyeR': tuple(centre(eB['R'])),
    'beak': (626, 559),
    'sign': (626.5, 980),                       # 팻말 막대 아래 끝 가까이(날개가 잡는 곳)
}
TIP_R = (990, 836)        # 오른날개 끝(팻말 막대를 잡는 곳) — 원래 캔버스 좌표
SIGN_S = 0.47             # 팻말 크기(판 폭 약 400px = 몸통 폭의 70%)
S = 0.26; BODY_AT = (190, 332)
def R(x, y, rot=0, s=1, op=1): return dict(x=x, y=y, rot=rot, sx=s, sy=s, op=op, img=0)
def part(id, name, parent, piv, images, follow=None, rest=None):
    if rest is None: rest = R(*BODY_AT, 0, S) if parent is None else R(*piv)
    return dict(id=id, name=name, parent=parent, pivot=dict(x=piv[0], y=piv[1]), rest=rest, images=images, follow=follow or dict(on=False, max=0))
parts = [   # 뒤 → 앞 (팻말은 몸통 뒤에서 올라오고, 막대는 날개 뒤에 있어 날개가 쥔 것처럼 보임)
    part('sign', '팻말', 'wingR', PIV['sign'], [img('빈 팻말', 'sign', src['팻말_빈판'])], rest=R(*TIP_R, 0, SIGN_S)),
    part('signText', '팻말 글자', 'sign', PIV['sign'], [img(SIGN_TEXT, 'sign_text', txt)]),
    part('wingL', '화면 왼날개', 'body', PIV['wingL'], [img('화면 왼날개', 'wingL', src['화면왼날개'])]),
    part('wingR', '화면 오른날개', 'body', PIV['wingR'], [img('화면 오른날개', 'wingR', src['화면오른날개'])]),
    part('footL', '화면 왼발', 'body', PIV['footL'], [img('화면 왼발', 'footL', src['화면왼발'])]),
    part('footR', '화면 오른발', 'body', PIV['footR'], [img('화면 오른발', 'footR', src['화면오른발'])]),
    part('body', '몸통바탕(머리털 포함)', None, PIV['body'], [img('몸통바탕', 'body', src['몸통바탕'])]),
    part('eyeL', '화면 왼눈', 'body', PIV['eyeL'], [img('기본 점눈', 'eyeL_basic', eB['L']), img('웃는 눈', 'eyeL_welcome', eW['L'])], dict(on=True, max=14)),
    part('eyeR', '화면 오른눈', 'body', PIV['eyeR'], [img('기본 점눈', 'eyeR_basic', eB['R']), img('웃는 눈', 'eyeR_welcome', eW['R'])], dict(on=True, max=14)),
    part('beak', '부리(붉은 타원, 바뀌지 않음)', 'body', PIV['beak'], [img('붉은 타원 부리', 'beak', src['부리_붉은타원'])], dict(on=True, max=6)),
]
FACES = {'f00': dict(id='f00', name='기본', img=dict(eyeL=0, eyeR=0), mods={}),
         'f01': dict(id='f01', name='환영(웃는 눈, 부리 그대로)', img=dict(eyeL=1, eyeR=1), mods={})}
H = 232
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
    def build(s):
        for tr in s.c['tracks'].values():
            if 'img' in tr: tr['img'].sort(key=lambda d: d['t'])
        return s.c
def alt(t0, t1, step, a, b, e='inout'):
    out, i, t = [], 0, t0
    while t <= t1 + 1e-9: out.append((round(t, 3), a if i % 2 == 0 else b, e)); i += 1; t = round(t + step, 3)
    return out
clips = []
# A. 대기: 작은 호흡, 기본 점눈, 부리 고정. 팻말은 숨김
c = Clip('d_idle', 'A 대기', 3.0, loop=True, follow='on')
c.k('body', 'sy', [(0, 1), (1.5, 1.022), (3, 1)]).k('body', 'sx', [(0, 1), (1.5, 0.992), (3, 1)])
c.k('wingL', 'rot', [(0, 0), (1.6, -3), (3, 0)]).k('wingR', 'rot', [(0, 0), (1.6, 3), (3, 0)])
c.k('sign', 'op', [(0, 0), (3, 0)]).k('signText', 'op', [(0, 0), (3, 0)])
clips.append(c.build())
c = Clip('d_blink', '깜빡임', 0.22, follow='on')
for s_ in 'LR': c.k('eye' + s_, 'sy', [(0, 1, 'in'), (0.07, 0.1, 'out'), (0.18, 1)])
clips.append(c.build())

# B. 정면 우다다: 짧은 발 번갈아, 몸 좌우 뒤뚱, 날개는 0.05초 늦게. 멀리서 다가오며 커짐
c = Clip('d_run', 'B 정면 우다다', 2.4)
c.face(0, 'f00', 0)
c.k('sign', 'op', [(0, 0), (2.4, 0)]).k('signText', 'op', [(0, 0), (2.4, 0)])
STEP = 0.13; steps = [round(0.05 + i * STEP, 3) for i in range(16)]
c.k('body', 'sx', [(0, 0.55), (2.05, 1.0, 'out'), (2.4, 1)]).k('body', 'sy', [(0, 0.55), (2.05, 1.0, 'out'), (2.4, 1)])
yk = [(0, -0.2 * H)]
for i, t in enumerate(steps):
    base = -0.2 * H * (1 - min(1, t / 2.05)) ** 1.6
    if t > 2.05: break
    yk += [(t, base, 'out'), (round(t + STEP / 2, 3), base - 0.025 * H, 'in')]
c.k('body', 'y', yk + [(2.15, 0, 'out'), (2.4, 0)])
c.k('body', 'rot', [(0, 0)] + [(t, 5 if i % 2 == 0 else -5) for i, t in enumerate(steps) if t < 2.1] + [(2.2, 0), (2.4, 0)])
fl, fr = [(0, 0)], [(0, 0)]
for i, t in enumerate(steps):
    if t > 2.05: break
    up = -12   # 발 들기(원래 캔버스 px) — 많이 들면 몸통 뒤로 숨으므로 조금만 들고 옆으로 기울임
    (fl if i % 2 == 0 else fr).append((t, up, 'out')); (fl if i % 2 == 0 else fr).append((round(t + STEP * 0.8, 3), 0, 'in'))
c.k('footL', 'y', fl + [(2.4, 0)]).k('footR', 'y', fr + [(2.4, 0)])
c.k('footL', 'x', [(k[0], -10 if k[1] else 0) + k[2:] for k in fl] + [(2.4, 0)]).k('footR', 'x', [(k[0], 10 if k[1] else 0) + k[2:] for k in fr] + [(2.4, 0)])
c.k('footL', 'rot', [(0, 0)] + [(t, -16 if i % 2 == 0 else 3) for i, t in enumerate(steps) if t < 2.1] + [(2.2, 0), (2.4, 0)])
c.k('footR', 'rot', [(0, 0)] + [(t, -3 if i % 2 == 0 else 16) for i, t in enumerate(steps) if t < 2.1] + [(2.2, 0), (2.4, 0)])
c.k('wingL', 'rot', [(0, 0)] + [(round(t + 0.05, 3), 14 if i % 2 == 0 else -6) for i, t in enumerate(steps) if t < 2.1] + [(2.25, 0), (2.4, 0)])
c.k('wingR', 'rot', [(0, 0)] + [(round(t + 0.05, 3), 6 if i % 2 == 0 else -14) for i, t in enumerate(steps) if t < 2.1] + [(2.25, 0), (2.4, 0)])
clips.append(c.build())

# C. 환영 슬로모션: 바깥쪽(오른쪽)으로 기울고 왼발이 들림. 오른날개로 '합니다!' 팻말을 올림(몸 뒤에서 솟아오름), 웃는 눈
WR = -100                 # 오른날개를 위로(오른쪽 위를 향하게)
c = Clip('d_welcome', 'C 환영 슬로모션', 3.2)
c.face(0, 'f00', 0).face(0.14, 'f01', 0.03)
c.k('body', 'rot', [(0, 0), (0.12, -3, 'out'), (0.32, 8, 'out'), (3.2, 11, 'linear')])
c.k('body', 'x', [(0, 0), (0.32, 0.03 * H / S * 0 + 6, 'out'), (3.2, 9, 'linear')])
c.k('body', 'y', [(0, 0), (0.12, 4, 'out'), (0.32, -6, 'out'), (3.2, -9, 'linear')])
c.k('body', 'sy', [(0, 1), (0.12, 0.92, 'out'), (0.32, 1.05, 'out'), (0.8, 1.03), (3.2, 1.02, 'linear')])
c.k('body', 'sx', [(0, 1), (0.12, 1.06, 'out'), (0.32, 0.97, 'out'), (0.8, 0.985), (3.2, 0.99, 'linear')])
c.k('footL', 'y', [(0, 0), (0.3, -14, 'out'), (3.2, -18, 'linear')]).k('footL', 'x', [(0, 0), (0.3, -60, 'out'), (3.2, -64, 'linear')]).k('footL', 'rot', [(0, 0), (0.3, 42, 'out'), (3.2, 46, 'linear')])   # 몸통 뒤로 숨지 않게 바깥으로 차올림
c.k('footR', 'rot', [(0, 0), (0.3, -6, 'out'), (3.2, -8, 'linear')])
c.k('wingR', 'rot', [(0, 0), (0.4, WR, 'out'), (1.4, WR - 4), (2.4, WR + 2), (3.2, WR - 3)])
c.k('wingL', 'rot', [(0, 0), (0.3, 18, 'out')] + alt(0.7, 3.0, 0.55, 10, 22) + [(3.2, 16)])   # 균형 잡는 느린 날갯짓
# 팻말: 날개를 따라 돌지만 막대가 거의 수직으로 서도록 반대로 돌림 + 뒤늦게 흔들림
TILT = 12; SR = -WR + TILT    # 날개 회전을 되돌려 막대를 세우고, 바깥쪽으로 조금 기울임
c.k('sign', 'rot', [(0, TILT), (0.4, SR, 'out'), (0.75, SR - 6), (1.3, SR + 4), (2.1, SR - 2), (3.2, SR + 2)])   # 0.4초 이후는 몸보다 늦게 흔들림
c.k('sign', 'op', [(0, 0), (0.1, 0, 'linear'), (0.24, 1), (3.2, 1)]).k('signText', 'op', [(0, 0), (0.1, 0, 'linear'), (0.24, 1), (3.2, 1)])
clips.append(c.build())

# D. 마무리: 들린 발을 한 번 디뎌 균형 회복 → 팻말 내리고 숨김 → 작은 기본형으로 축소·아래로 → 작게 대기 → (시험용) 원래 크기로
END = 3.0; c = Clip('d_finish', 'D 마무리', END)
c.face(0, 'f01', 0).face(0.62, 'f00', 0.04)
c.k('body', 'rot', [(0, 11), (0.22, -4, 'out'), (0.42, 2), (0.6, 0), (END, 0)])
c.k('body', 'x', [(0, 9), (0.3, 0, 'out'), (END, 0)])
c.k('body', 'y', [(0, -9), (0.2, 0, 'in'), (0.3, 4), (0.42, 0), (0.7, 0, 'inout'), (1.2, 0.17 * H, 'inout'), (2.2, 0.17 * H), (2.75, 0, 'inout'), (END, 0)])
c.k('body', 'sy', [(0, 1.02), (0.2, 0.9, 'out'), (0.34, 1.04), (0.46, 1.0), (0.7, 1.0, 'inout'), (1.2, 0.6, 'inout'), (1.6, 0.612), (2.0, 0.6), (2.2, 0.6), (2.75, 1.0, 'inout'), (END, 1)])
c.k('body', 'sx', [(0, 0.99), (0.2, 1.07, 'out'), (0.34, 0.98), (0.46, 1.0), (0.7, 1.0, 'inout'), (1.2, 0.6, 'inout'), (1.6, 0.596), (2.0, 0.6), (2.2, 0.6), (2.75, 1.0, 'inout'), (END, 1)])
c.k('footL', 'y', [(0, -18), (0.2, 0, 'in'), (0.28, -5), (0.38, 0), (END, 0)]).k('footL', 'x', [(0, -64), (0.2, 0, 'in'), (END, 0)]).k('footL', 'rot', [(0, 46), (0.2, 0, 'in'), (0.3, -5), (0.42, 0), (END, 0)])
c.k('footR', 'rot', [(0, -8), (0.2, 0), (0.3, 4), (0.42, 0), (END, 0)])
c.k('wingR', 'rot', [(0, WR - 3), (0.25, WR + 8, 'out'), (0.75, 0, 'inout'), (0.9, 8), (1.05, 0), (END, 0)])
c.k('wingL', 'rot', [(0, 16), (0.3, -8, 'out'), (0.5, 4), (0.7, 0), (END, 0)])
c.k('sign', 'rot', [(0, SR + 2), (0.25, -(WR + 8) + TILT - 8, 'out'), (0.75, TILT, 'inout'), (END, TILT)])
c.k('sign', 'op', [(0, 1), (0.5, 1), (0.7, 0), (END, 0)]).k('signText', 'op', [(0, 1), (0.5, 1), (0.7, 0), (END, 0)])
c.k('wingL', 'sy', [(0, 1), (END, 1)])
clips.append(c.build())

rules = [dict(id='r_blink', event='random', clip='d_blink', min=2.5, max=6)]
preview = [dict(label='A 대기', clip='d_idle'), dict(label='B 정면 우다다', clip='d_run'), dict(label='C 환영 슬로모션', clip='d_welcome'), dict(label='D 마무리', clip='d_finish')]
proj = dict(version=1, name='도로덕 (검수본)', stage=dict(w=400, h=400), parts=parts, clips=clips, rules=rules, baseClip='d_idle',
            faces=list(FACES.values()), preview=preview, display=dict(size=170, corner='right', margin=16, hideOnMobile=False, closable=False), assets=assets)
s = json.dumps(proj, ensure_ascii=False, separators=(',', ':'))
open(OUT + 'doroduck.json', 'w').write(s)
json.dump(dict(canvas=[N, N], split_x=SPLIT_X, stage_scale=S, body_at_stage=BODY_AT, pivots=PIV, sign=dict(parent='wingR', grip_on_wing=TIP_R, scale=SIGN_S, text=SIGN_TEXT, text_box=[154, 366, 1099, 671]),
               crops=crops, draw_order=[p['id'] for p in parts], parents={p['id']: p['parent'] for p in parts}), open(OUT + 'rig.json', 'w'), ensure_ascii=False, indent=1)
print('json KB', len(s) // 1024)
