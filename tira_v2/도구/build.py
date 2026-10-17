# 티라 v2 검수본 조립: work/fixed 보정본 → 자르기·절반 해상도 → charo-pet 형식 JSON
# 좌표는 모두 원래 캔버스 1254×1254. 잘라낸 그림마다 원래 위치(x,y,w,h)를 기록.
import cv2, numpy as np, json, base64, os
from PIL import Image, ImageDraw, ImageFont
F = '/home/claude/tira2/work/fixed/'; OUT = '/home/claude/tira2/out/'; os.makedirs(OUT + 'crops', exist_ok=True)
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
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc' if os.path.exists('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc') else '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 120)
    bx0, by0, bx1, by1 = 453, 642, 726, 777
    w = d.textlength(txt, font=fnt); asc, desc = fnt.getmetrics()
    x = (bx0 + bx1) / 2 - w / 2; y = (by0 + by1) / 2 - (asc + desc) / 2 - 6
    d.text((x, y), txt, font=fnt, fill=(74, 40, 20, 255))
    a = np.array(img); return cv2.cvtColor(a, cv2.COLOR_RGBA2BGRA)
assets, crops = {}, {}
def asset(key, im, pad=3):
    a = im[..., 3] > 8; ys, xs = np.where(a)
    x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad); x1, y1 = min(N, xs.max() + pad + 1), min(N, ys.max() + pad + 1)
    c = im[y0:y1, x0:x1]; cv2.imwrite(OUT + 'crops/' + key + '.png', c)
    sm = cv2.resize(c, (max(1, round(c.shape[1] / 2)), max(1, round(c.shape[0] / 2))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode('.png', sm, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assets['v_' + key] = 'data:image/png;base64,' + base64.b64encode(buf.tobytes()).decode()
    crops[key] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0), canvas=[N, N])
    return dict(asset='v_' + key, x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
def img(name, key, im): d = asset(key, im); d['name'] = name; return d
def centre(im):
    ys, xs = np.where(im[..., 3] > 128); return [round(float((xs.min() + xs.max()) / 2), 1), round(float((ys.min() + ys.max()) / 2), 1)]


NAMES=['꼬리','화면왼발','화면오른발','몸통바탕','팻말_빈판','화면왼팔_올림','화면오른팔_올림','눈_기본','눈_질끈','입_기본이빨','입_환영웃음','불꽃_작게','불꽃_뿍']
src = {n: load(n) for n in NAMES}
txt = sign_text(SIGN_TEXT)
PIV = {'body': (627, 1012), 'tail': (770, 930), 'footL': (505, 990), 'footR': (675, 985),
       'hold': (590, 740),                       # 팻말과 두 팔을 함께 움직이는 그룹(가슴 앞)
       'armL': (440, 745), 'armR': (740, 745),   # 어깨(몸통 안쪽 열린 끝)
       'eyes': (589.5, 449.5), 'mouth': (589.5, 549.5), 'fire': (449, 553), 'sign': (590, 710)}
S = 0.30; BODY_AT = (205, 335)
def R(x, y, rot=0, s=1, op=1): return dict(x=x, y=y, rot=rot, sx=s, sy=s, op=op, img=0)
def part(id, name, parent, piv, images, follow=None, rest=None):
    if rest is None: rest = R(*BODY_AT, 0, S) if parent is None else R(*piv)
    return dict(id=id, name=name, parent=parent, pivot=dict(x=piv[0], y=piv[1]), rest=rest, images=images, follow=follow or dict(on=False, max=0))
parts = [   # 뒤 → 앞: 꼬리·발 → 몸통 → 팻말 → 팔(손이 판 옆을 덮음) → 눈·입 → 불꽃
    part('tail', '꼬리', 'body', PIV['tail'], [img('꼬리', 'tail', src['꼬리'])]),
    part('footL', '화면 왼발', 'body', PIV['footL'], [img('화면 왼발', 'footL', src['화면왼발'])]),
    part('footR', '화면 오른발', 'body', PIV['footR'], [img('화면 오른발', 'footR', src['화면오른발'])]),
    part('body', '몸통바탕 v2(등판 포함)', None, PIV['body'], [img('몸통바탕', 'body', src['몸통바탕'])]),
    part('hold', '팻말+팔 그룹(그림 없음)', 'body', PIV['hold'], []),
    part('sign', '팻말', 'hold', PIV['sign'], [img('빈 팻말', 'sign', src['팻말_빈판'])]),
    part('signText', '팻말 글자', 'sign', PIV['sign'], [img(SIGN_TEXT, 'sign_text', txt)]),
    part('armL', '화면 왼팔(올림)', 'hold', PIV['armL'], [img('화면 왼팔', 'armL', src['화면왼팔_올림'])]),
    part('armR', '화면 오른팔(올림)', 'hold', PIV['armR'], [img('화면 오른팔', 'armR', src['화면오른팔_올림'])]),
    part('eyes', '눈', 'body', PIV['eyes'], [img('기본 눈', 'eye_basic', src['눈_기본']), img('질끈 눈', 'eye_squint', src['눈_질끈'])], dict(on=True, max=12)),
    part('mouth', '입', 'body', PIV['mouth'], [img('기본 이빨 입', 'mouth_basic', src['입_기본이빨']), img('환영 웃음 입', 'mouth_smile', src['입_환영웃음'])], dict(on=True, max=6)),
    part('fire', '불꽃(입 왼쪽 끝에 고정)', 'mouth', PIV['fire'], [img('불꽃 작게', 'fire_s', src['불꽃_작게']), img('불꽃 뿍', 'fire_b', src['불꽃_뿍'])]),
]
# 팻말·불꽃은 기본 자세(투명도 1)로 두고, 동작마다 투명도 트랙으로 숨기거나 보임(투명도는 곱해지므로 기본값을 0으로 두면 동작에서 켤 수 없음)
FACES = {'f00': dict(id='f00', name='① 기본 눈+기본 이빨 입', img=dict(eyes=0, mouth=0), mods={}),
         'f01': dict(id='f01', name='② 질끈 눈+기본 이빨 입', img=dict(eyes=1, mouth=0), mods={}),
         'f02': dict(id='f02', name='③ 질끈 눈+환영웃음 입', img=dict(eyes=1, mouth=1), mods={})}
H = 242
class Clip:
    def __init__(s, id, name, dur, loop=False, follow='center', **kw):
        s.c = dict(id=id, name=name, dur=dur, loop=loop, follow=follow, tracks={}); s.c.update(kw); s.dur = dur
    def k(s, part, prop, keys):
        out = {}
        for x in keys: t = round(x[0], 3); out[t] = dict(t=t, v=round(float(x[1]), 4), e=x[2] if len(x) > 2 else 'inout')
        s.c['tracks'].setdefault(part, {})[prop] = [out[t] for t in sorted(out)]; return s
    def face(s, t, fid, f=0.03):
        for p_, v in FACES[fid]['img'].items(): s.c['tracks'].setdefault(p_, {}).setdefault('img', []).append(dict(t=round(t, 3), v=v, f=f))
        return s
    def fire(s, frames):   # [(t, 'small'|'big'|None)]
        op, im = [(0, 0, 'step')], [dict(t=0, v=0, f=0)]
        for t, f in frames:
            op.append((t, 0 if f is None else 1, 'step'))
            if f: im.append(dict(t=round(t, 3), v=0 if f == 'small' else 1, f=0))
        op.append((s.dur, 0, 'step')); s.k('fire', 'op', op); s.c['tracks'].setdefault('fire', {})['img'] = im
        s.c['fireFrames'] = [[t, f] for t, f in frames]; return s
    def sign(s, keys): s.k('sign', 'op', keys); s.k('signText', 'op', keys); return s
    def build(s):
        for tr in s.c['tracks'].values():
            if 'img' in tr: tr['img'].sort(key=lambda d: d['t'])
        return s.c
def lag(keys, dt, sc=1.0): return [(round(k[0] + dt, 3), k[1] * sc) + tuple(k[2:]) for k in keys]
clips = []
c = Clip('v_idle', 'A 대기', 3.0, loop=True, follow='on')
c.k('body', 'sy', [(0, 1), (1.5, 1.02), (3, 1)]).k('body', 'sx', [(0, 1), (1.5, 0.992), (3, 1)])
c.k('tail', 'rot', [(0, 0), (0.35, 0), (1.85, -4), (3, 0)]).k('hold', 'y', [(0, 0), (1.5, -3), (3, 0)])
c.sign([(0, 0), (3, 0)]); c.fire([])
clips.append(c.build())
c = Clip('v_blink', '깜빡임', 0.22, follow='on')
c.k('eyes', 'sy', [(0, 1, 'in'), (0.07, 0.1, 'out'), (0.18, 1)])
c.sign([(0, 0), (0.22, 0)]); c.fire([])
clips.append(c.build())
# B 정면 달려오기: 짧은 발 번갈아, 몸 통통, 팔은 엇박자로 작게, 꼬리는 기울기보다 늦게
c = Clip('v_run', 'B 정면 달려오기', 2.4)
c.face(0, 'f00', 0); c.sign([(0, 0), (2.4, 0)]); c.fire([])
STEP = 0.12; steps = [round(0.05 + i * STEP, 3) for i in range(17) if 0.05 + i * STEP < 2.06]
c.k('body', 'sx', [(0, 0.55), (2.05, 1.0, 'out'), (2.4, 1)]).k('body', 'sy', [(0, 0.55), (2.05, 1.0, 'out'), (2.4, 1)])
yk = [(0, -0.2 * H)]
for t in steps:
    base = -0.2 * H * (1 - min(1, t / 2.05)) ** 1.6
    yk += [(t, base, 'out'), (round(t + STEP / 2, 3), base - 0.025 * H, 'in')]
c.k('body', 'y', yk + [(2.15, 0, 'out'), (2.4, 0)])
tilt = [(t, 3.5 if i % 2 == 0 else -3.5) for i, t in enumerate(steps)]
c.k('body', 'rot', [(0, 0)] + tilt + [(2.2, 0), (2.4, 0)]); c.k('tail', 'rot', [(0, 0)] + lag(tilt, 0.08, 2.5) + [(2.32, 0), (2.4, 0)])
fl, fr = [(0, 0)], [(0, 0)]
for i, t in enumerate(steps):
    g = fl if i % 2 == 0 else fr; g += [(t, -14, 'out'), (round(t + STEP * 0.8, 3), 0, 'in')]
c.k('footL', 'y', fl + [(2.4, 0)]).k('footR', 'y', fr + [(2.4, 0)])
c.k('armL', 'rot', [(0, 0)] + [(round(t + 0.03, 3), -8 if i % 2 == 0 else 6) for i, t in enumerate(steps)] + [(2.2, 0), (2.4, 0)])
c.k('armR', 'rot', [(0, 0)] + [(round(t + 0.03, 3), -6 if i % 2 == 0 else 8) for i, t in enumerate(steps)] + [(2.2, 0), (2.4, 0)])
clips.append(c.build())
# C 환영 슬로모션 3.2초 = 지침의 상대 시간(0~1.1초)을 2배로 느리게 + 아주 느린 버팀
SL = 2.0; T = lambda t: round(t * SL, 3)
c = Clip('v_welcome', 'C 환영 슬로모션(불뿜기)', 3.2)
c.face(0, 'f00', 0).face(T(0.25), 'f01').face(T(0.75), 'f02')
c.sign([(0, 0), (T(0.03), 0, 'linear'), (T(0.12), 1), (3.2, 1)])
c.k('hold', 'y', [(0, 70), (T(0.25), -6, 'out'), (T(0.32), 0), (T(0.75), 0), (T(0.82), -5), (T(0.9), 3), (T(1.0), -1.5), (T(1.1), 0), (3.2, 0)])   # 올림 → 판 작게 흔들림 후 안정
c.k('hold', 'rot', [(0, 0), (T(0.75), 0), (T(0.82), 3), (T(0.9), -2), (T(1.0), 1), (T(1.1), 0), (3.2, 0)])
c.k('body', 'rot', [(0, 0), (T(0.25), -6, 'out'), (T(0.4), -7.5), (T(0.5), -3, 'out'), (T(0.75), -4), (T(1.1), -5), (3.2, -6, 'linear')])   # 뒤로(바깥으로) 젖힘 → 불 반동으로 반대로 밀림
c.k('body', 'x', [(0, 0), (T(0.25), -6, 'out'), (T(0.4), -8), (T(0.5), -3, 'out'), (T(0.75), -4), (3.2, -6, 'linear')])
c.k('body', 'y', [(0, 0), (T(0.25), -4, 'out'), (T(0.4), -5), (3.2, -7, 'linear')])
c.k('body', 'sy', [(0, 1), (T(0.25), 1.02), (T(0.3), 0.97, 'out'), (T(0.4), 1.0), (3.2, 1.01)])   # 멈칫(크게 부풀리지 않음)
c.k('footR', 'y', [(0, 0), (T(0.25), -10, 'out'), (3.2, -13, 'linear')])
c.k('tail', 'rot', [(0, 0), (T(0.3), -6, 'out'), (T(0.55), 12, 'out'), (T(0.8), 4), (T(1.05), 9), (3.2, 7)])   # 불 반동 뒤 늦게 휙
c.fire([(T(0.40), 'small'), (T(0.50), 'big'), (T(0.64), 'small'), (T(0.75), None)])
clips.append(c.build())
# D 마무리: 발을 디뎌 균형 → 팻말 흔들림 가라앉고 내림 → 작아져 아래로(정렬) → (시험용) 원래대로
END = 3.0; c = Clip('v_finish', 'D 균형 회복·정렬', END)
c.face(0, 'f02', 0).face(0.62, 'f00'); c.fire([])
c.k('body', 'rot', [(0, -6), (0.22, 3, 'out'), (0.42, -1.5), (0.6, 0), (END, 0)]).k('body', 'x', [(0, -6), (0.3, 0, 'out'), (END, 0)])
c.k('body', 'y', [(0, -7), (0.2, 0, 'in'), (0.3, 3), (0.42, 0), (0.8, 0, 'inout'), (1.3, 0.17 * H, 'inout'), (2.2, 0.17 * H), (2.75, 0, 'inout'), (END, 0)])
c.k('body', 'sy', [(0, 1.01), (0.2, 0.93, 'out'), (0.34, 1.03), (0.46, 1.0), (0.8, 1.0, 'inout'), (1.3, 0.6, 'inout'), (2.2, 0.6), (2.75, 1.0, 'inout'), (END, 1)])
c.k('body', 'sx', [(0, 0.995), (0.2, 1.05, 'out'), (0.34, 0.985), (0.46, 1.0), (0.8, 1.0, 'inout'), (1.3, 0.6, 'inout'), (2.2, 0.6), (2.75, 1.0, 'inout'), (END, 1)])
c.k('footR', 'y', [(0, -13), (0.2, 0, 'in'), (0.28, -4), (0.38, 0), (END, 0)])
c.k('hold', 'rot', [(0, 0), (0.25, 3, 'out'), (0.42, -1.5), (0.55, 0), (END, 0)]).k('hold', 'y', [(0, 0), (0.55, 0), (0.8, 60, 'in'), (END, 0)])
c.sign([(0, 1), (0.6, 1), (0.8, 0), (END, 0)])
c.k('tail', 'rot', [(0, 7), (0.3, 7), (0.5, -9, 'out'), (0.75, 4), (0.95, -1.5), (1.15, 0), (END, 0)])
clips.append(c.build())
rules = [dict(id='r_blink', event='random', clip='v_blink', min=2.5, max=6)]
preview = [dict(label='A 대기', clip='v_idle'), dict(label='B 정면 달려오기', clip='v_run'), dict(label='C 환영 슬로모션(불뿜기)', clip='v_welcome'), dict(label='D 균형 회복·정렬', clip='v_finish')]
proj = dict(version=1, name='티라 v2 (검수본)', stage=dict(w=400, h=400), parts=parts, clips=clips, rules=rules, baseClip='v_idle',
            faces=list(FACES.values()), preview=preview, display=dict(size=170, corner='right', margin=16, hideOnMobile=False, closable=False), assets=assets)
s = json.dumps(proj, ensure_ascii=False, separators=(',', ':'))
open(OUT + 'tira_v2.json', 'w').write(s)
json.dump(dict(canvas=[N, N], stage_scale=S, body_at_stage=BODY_AT, pivots=PIV, crops=crops, draw_order=[p['id'] for p in parts], parents={p['id']: p['parent'] for p in parts},
               fire={c_['id']: c_.get('fireFrames') for c_ in clips}, slow_factor=SL), open(OUT + 'rig.json', 'w'), ensure_ascii=False, indent=1)
print('json KB', len(s) // 1024)
