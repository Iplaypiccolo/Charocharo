# 타로타로 캐릭터 파일 만들기(charo-pet 형식). 원본 PNG는 그대로 두고, 조립_시작값.json의 source_rect만 잘라
# guide_draw_rect 자리에 놓음. 엔진 좌표 = 가이드(400×420) × K.
import json, os, base64, io
from PIL import Image
SRC = '/home/claude/taro/src/'; OUT = '/home/claude/taro/out/'; os.makedirs(OUT + 'crops', exist_ok=True)
G = json.load(open(SRC + '조립_시작값.json')); A = {a['id']: a for a in G['assets']}
K = 3.0           # 엔진 좌표 배율(가이드 1칸 = 3)
STORE = 0.5       # 저장 해상도(엔진 좌표의 절반 크기 그림, 화면 키 ~230px·2배 화면까지 충분)
def W(v): return round(v * K, 2)
assets, crops = {}, {}
def img(key, name):
    a = A[key]; sx, sy, sw, sh = a['source_rect_xywh']; dx, dy, dw, dh = a['guide_draw_rect_xywh']
    im = Image.open(SRC + a['file']).convert('RGBA').crop((sx, sy, sx + sw, sy + sh))
    tw, th = max(1, round(dw * K * STORE)), max(1, round(dh * K * STORE))
    im = im.resize((tw, th), Image.LANCZOS); im.save(OUT + 'crops/' + key + '.png')
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    assets['tt_' + key] = 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
    crops[key] = dict(source_rect=a['source_rect_xywh'], guide_rect=a['guide_draw_rect_xywh'], world=[W(dx), W(dy), W(dw), W(dh)], stored_px=[tw, th])
    return dict(asset='tt_' + key, name=name, x=W(dx), y=W(dy), w=W(dw), h=W(dh))
AP = G['attach_pivots_stage']
FEET = (200, 385); LWB = (136, 385)    # 전체 기준점(바퀴 끝), 왼쪽 바퀴 바닥(한쪽 착지 회전축)
PIV = {'rig': FEET, 'land': LWB, 'body': FEET, 'earL': AP['earL'], 'earR': AP['earR'], 'antenna': AP['antenna'],
       'wheelL': AP['wheelL'], 'wheelR': AP['wheelR'], 'bodyImg': FEET, 'eyes': (200, 227), 'mouth': (200, 265), 'excl': (294.5, 135)}
PIVW = {k: (W(v[0]), W(v[1])) for k, v in PIV.items()}
S = 0.30; RIG_AT = (200, 385)        # 400 무대: 키 312칸×3×0.3 ≈ 281px
def R(x, y, s=1): return dict(x=x, y=y, rot=0, sx=s, sy=s, op=1, img=0)
def part(id, name, parent, images):
    p = PIVW[id]; rest = R(*RIG_AT, S) if parent is None else R(*p)
    return dict(id=id, name=name, parent=parent, pivot=dict(x=p[0], y=p[1]), rest=rest, images=images, follow=dict(on=False, max=0))
parts = [   # 그리는 순서 = 뒤 → 앞 (안테나·귀·바퀴는 몸통 뒤, 눈·입·느낌표는 앞)
    part('rig', '무대 위치·전체 크기(그림 없음)', None, []),
    part('land', '한쪽 착지 회전(왼쪽 바퀴 바닥 축, 그림 없음)', 'rig', []),
    part('body', '몸 전체(눌림·기울기, 그림 없음)', 'land', []),
    part('antenna', '번개 안테나', 'body', [img('antenna', '05 번개 안테나')]),
    part('earL', '화면 왼쪽 귀', 'body', [img('earL', '03 귀 화면왼쪽')]),
    part('earR', '화면 오른쪽 귀', 'body', [img('earR', '04 귀 화면오른쪽')]),
    part('wheelL', '화면 왼쪽 바퀴', 'body', [img('wheelL', '06 바퀴 화면왼쪽')]),
    part('wheelR', '화면 오른쪽 바퀴', 'body', [img('wheelR', '07 바퀴 화면오른쪽')]),
    part('bodyImg', '몸통(정면/왼쪽15도 중 하나)', 'body', [img('body_front', '01 몸통 정면'), img('body_left15', '02 몸통 왼쪽15도')]),
    part('eyes', '눈(한 쌍)', 'body', [img('eyes_smile', '08 눈 빵긋'), img('eyes_shock15', '10 눈 15도 놀람'), img('eyes_proud', '12 눈 엣헴')]),
    part('mouth', '입', 'body', [img('mouth_smile', '09 입 빵긋'), img('mouth_shock15', '11 입 15도 놀람'), img('mouth_proud', '13 입 엣헴')]),
    part('excl', '느낌표', 'body', [img('exclamation', '14 느낌표')]),
]
FACE = {'A': dict(bodyImg=0, eyes=0, mouth=0), 'B': dict(bodyImg=1, eyes=1, mouth=1), 'C': dict(bodyImg=0, eyes=2, mouth=2)}
FACES = [dict(id='fA', name='A 기본·환영 (빵긋)', img=FACE['A'], mods={}), dict(id='fB', name='B 놀람 (왼쪽 15도)', img=FACE['B'], mods={}),
         dict(id='fC', name='C 엣헴', img=FACE['C'], mods={})]
# B 상태의 귀·안테나 위치 보정(가이드 값 × K)
BADJ = G['state_B_ear_adjustment']
EARLX, EARRX, ANTX = W(BADJ['earL']['offset_xy'][0]), W(BADJ['earR']['offset_xy'][0]), W(BADJ['antenna']['offset_xy'][0])
H_STAGE = 312 * K * S   # 400 무대에서 키(px)

class Clip:
    def __init__(s, id, name, dur, loop=False, **kw):
        s.c = dict(id=id, name=name, dur=dur, loop=loop, follow='center', tracks={}); s.c.update(kw); s.dur = dur
    def k(s, part, prop, keys):
        out = {}
        for x in keys: t = round(x[0], 3); out[t] = dict(t=t, v=round(float(x[1]), 4), e=x[2] if len(x) > 2 else 'inout')
        s.c['tracks'].setdefault(part, {})[prop] = [out[t] for t in sorted(out)]; return s
    def face(s, keys):   # [(t, 'A'|'B'|'C')] 몸통·눈·입을 같은 순간에
        for pid in ('bodyImg', 'eyes', 'mouth'):
            s.c['tracks'].setdefault(pid, {})['img'] = [dict(t=round(t, 3), v=FACE[f][pid], f=0) for t, f in keys]
        return s
    def ops(s, part, keys): return s.k(part, 'op', [(t, v, 'step') for t, v in keys])

END = 6.3; SLOW0, SLOW1 = 2.30, 3.90
def intro_local(c):
    """인트로 공통 시간축(6.3초) 기준 타로타로 자신의 움직임. 무대 위 이동(점프 궤적·정렬)은 인트로 재생기 바깥 층이 맡음."""
    c.face([(0, 'A'), (0.37, 'B'), (0.90, 'A'), (4.45, 'C'), (4.85, 'A')])   # 놀람은 느낌표가 사라지는 0.90에 끝
    # B 동안 귀·안테나 위치 보정(몸통 방향과 같은 순간), 느낌표는 0.37 팝 → 0.90 사라짐
    c.k('earL', 'x', [(0, 0, 'step'), (0.37, EARLX, 'step'), (0.90, 0, 'step'), (END, 0)]).k('earL', 'sx', [(0, 1, 'step'), (0.37, 0.9, 'step'), (0.90, 1, 'step'), (END, 1)])
    c.k('earR', 'x', [(0, 0, 'step'), (0.37, EARRX, 'step'), (0.90, 0, 'step'), (END, 0)])
    c.k('antenna', 'x', [(0, 0, 'step'), (0.37, ANTX, 'step'), (0.90, 0, 'step'), (END, 0)])
    c.ops('excl', [(0, 0), (0.37, 1), (0.90, 0), (END, 0)])
    c.k('excl', 'sx', [(0, 0.6), (0.37, 0.6, 'out'), (0.45, 1.1), (0.52, 1.0), (END, 1)]).k('excl', 'sy', [(0, 0.6), (0.37, 0.6, 'out'), (0.45, 1.1), (0.52, 1.0), (END, 1)])
    c.k('excl', 'y', [(0, 0), (0.37, 12, 'out'), (0.47, -6), (0.55, 0), (END, 0)])
    # 몸: 대기 숨쉬기 → 움찔(오른쪽=불 반대로 물러나며 5° 젖힘, 깡충) → 멈칫·준비 → 웅크림 → 이륙(정면·A) → 환영 왼쪽 10° → 착지 → 엣헴
    # 몸: 대기 → 움찔(0.37~0.90, 불 반대쪽으로 물러나며 젖힘·깡충) → 0.90 빵긋으로 돌아옴 → 고무공 도움닫기(양옆으로 크게 납작) → 1.74 튕겨 오르며 세로로 쭉 → 환영 왼쪽 10° → 착지 → 엣헴
    c.k('body', 'x', [(0, 0), (0.37, 0, 'out'), (0.48, 22), (0.80, 18), (1.10, 6), (1.30, 0), (END, 0)])
    c.k('body', 'y', [(0, 0), (0.37, 0, 'out'), (0.43, -18, 'in'), (0.52, 0), (END, 0)])
    c.k('body', 'rot', [(0, 0), (0.37, 0, 'out'), (0.45, 6.5), (0.80, 4), (1.10, 0), (1.74, 0, 'out'), (2.10, -4),
                        (SLOW0, -8, 'inout'), (2.95, -11), (3.45, -9.5), (SLOW1, -10.5, 'in'), (4.12, 0), (END, 0)])
    # 도움닫기(한 번): 1.30부터 쭉 눌려 1.72에 키 50%·가로 1.55배로 아주 납작 → 1.81 세로로 쭉(0.80·1.28) → 2.00 원래대로
    c.k('body', 'sy', [(0, 1), (0.37, 1, 'out'), (0.41, 0.95), (0.47, 1.04), (0.56, 1.0), (1.30, 1.0, 'inout'), (1.72, 0.50, 'out'),
                       (1.81, 1.28, 'inout'), (1.91, 0.93), (2.00, 1.0),
                       (SLOW0, 1.01), (3.10, 1.02), (SLOW1, 1.01), (4.28, 1.0, 'in'), (4.31, 0.95, 'out'), (4.40, 1.02), (4.45, 1.0, 'out'),
                       (4.56, 1.04), (4.78, 1.03), (4.88, 1.0), (END, 1)])
    c.k('body', 'sx', [(0, 1), (0.37, 1, 'out'), (0.41, 1.04), (0.47, 0.97), (0.56, 1.0), (1.30, 1.0, 'inout'), (1.72, 1.55, 'out'),
                       (1.81, 0.80, 'inout'), (1.91, 1.06), (2.00, 1.0),
                       (4.28, 1.0, 'in'), (4.31, 1.04, 'out'), (4.40, 0.99), (4.45, 1.0, 'out'), (4.56, 0.98), (4.78, 0.985), (4.88, 1.0), (END, 1)])
    # 착지: 내려오며 기울기를 '왼쪽 바퀴 축'으로 넘김 → 4.16 왼쪽 바퀴 접지(이 점은 땅에 고정) → 4.28 오른쪽 바퀴 접지 → 살짝 넘었다 섬
    c.k('land', 'rot', [(0, 0), (SLOW1, 0, 'inout'), (4.12, -7), (4.16, -7, 'inout'), (4.28, 0, 'out'), (4.34, 1.2), (4.45, 0), (END, 0)])
    c.k('wheelL', 'y', [(0, 0), (4.15, 0, 'out'), (4.19, -10, 'in'), (4.26, 0), (END, 0)])     # 바퀴 서스펜션: 닿는 순간 살짝 눌림
    c.k('wheelR', 'y', [(0, 0), (4.27, 0, 'out'), (4.31, -10, 'in'), (4.38, 0), (END, 0)])
    # 귀·안테나: 몸보다 0.06초 늦게(움찔), 환영 때 느린 반동, 엣헴 때 쫑긋
    c.k('earL', 'rot', [(0, 0), (0.43, 0, 'out'), (0.52, 16), (0.64, -6), (0.78, 4), (0.92, 0), (1.30, 0), (1.72, 30, 'out'), (1.83, -18), (1.96, 10), (2.10, -4),
                        (SLOW0, 4), (2.85, 10), (3.40, 2), (SLOW1, 8), (4.20, -8), (4.36, 10), (4.48, 0), (4.56, -8), (4.70, 0), (END, 0)])
    c.k('earR', 'rot', [(0, 0), (0.43, 0, 'out'), (0.52, -14), (0.64, 6), (0.78, -3), (0.92, 0), (1.30, 0), (1.72, -30, 'out'), (1.83, 18), (1.96, -10), (2.10, 4),
                        (SLOW0, -2), (2.95, -9), (3.50, -1), (SLOW1, -7), (4.32, 8), (4.44, -8), (4.56, 0), (4.62, 7), (4.76, 0), (END, 0)])
    c.k('antenna', 'rot', [(0, 0), (0.43, 0, 'out'), (0.52, 10), (0.66, -5), (0.82, 2), (0.95, 0), (1.30, 0), (1.72, 8, 'out'), (1.84, -12), (1.98, 4), (2.10, -3),
                           (SLOW0, 2), (3.00, 6), (3.55, 0), (SLOW1, 4), (4.20, -6), (4.36, 5), (4.48, 0), (4.58, -5), (4.72, 2), (4.85, 0), (END, 0)])
    return c

clips = []
c = Clip('tt_idle', '대기', 3.0, loop=True)
c.face([(0, 'A')]).ops('excl', [(0, 0), (3.0, 0)])
c.k('body', 'sy', [(0, 1), (1.5, 1.015), (3, 1)]).k('body', 'sx', [(0, 1), (1.5, 0.994), (3, 1)])
c.k('earL', 'rot', [(0, 0), (1.6, 4), (3, 0)]).k('earR', 'rot', [(0, 0), (1.4, -4), (3, 0)]).k('antenna', 'rot', [(0, 0), (1.5, 2), (3, 0)])
clips.append(c.c)
INTRO = intro_local(Clip('tt_intro', '인트로 (6.3초 전체, 무대 이동 제외)', END, intro=True)).c
clips.append(INTRO)
# 미리보기용: 같은 움직임 + 점프·하강 궤적(인트로에서는 이 궤적을 바깥 층이 맡음). 400 무대에서 인트로 크기(0.6배)로 보여 줌
P_ = Clip('tt_preview', '미리보기 (점프 궤적 포함)', END, preview_only=True)
intro_local(P_)
SC = 0.6; JX, JY = -100, -144           # 출발 → 티라 위 자리(인트로 좌표 차이를 이 무대 크기로)
P_.k('rig', 'sx', [(0, SC), (END, SC)]).k('rig', 'sy', [(0, SC), (END, SC)])
xs = [(0, 55), (1.74, 55, 'linear')]; ys = [(0, 0), (1.74, 0, 'linear')]
for i in range(1, 9):                     # 1.74~2.30 포물선(위로 솟았다 자리로)
    u = i / 8; xs.append((1.74 + 0.56 * u, 55 + JX * u, 'linear')); ys.append((1.74 + 0.56 * u, JY * u - 4 * 40 * u * (1 - u), 'linear'))
xs += [(SLOW0, 55 + JX), (SLOW1, 55 + JX - 3, 'inout')]; ys += [(SLOW0, JY), (3.10, JY - 3), (SLOW1, JY - 1, 'inout')]
for i in range(1, 9):                     # 3.90~4.16 오른쪽으로 휘며 하강(티라 머리·팻말을 지나지 않게)
    u = i / 8; xs.append((SLOW1 + 0.26 * u, 55 + JX - 3 + (3 - JX) * u + 4 * 30 * u * (1 - u), 'linear')); ys.append((SLOW1 + 0.26 * u, (JY - 1) * (1 - u * u), 'linear'))
xs += [(END, 55)]; ys += [(END, 0)]
P_.k('rig', 'x', xs).k('rig', 'y', ys)
PREVIEW = P_.c
clips.append(PREVIEW)
# 구간 미리보기(궤적 포함 버전을 잘라 냄)
def ease(e, u): return {'linear': u, 'in': u * u, 'out': 1 - (1 - u) ** 2, 'inout': (2 * u * u if u < .5 else 1 - (-2 * u + 2) ** 2 / 2), 'step': 0}.get(e, u)
def sample(keys, t):
    if t <= keys[0]['t']: return keys[0]['v']
    for a, b in zip(keys, keys[1:]):
        if t < b['t']:
            u = (t - a['t']) / (b['t'] - a['t']) if b['t'] > a['t'] else 1
            return a['v'] + (b['v'] - a['v']) * ease(a['e'], u)
    return keys[-1]['v']
def slice_clip(src, id, name, a, b, stretch=1.0):
    d = round((b - a) * stretch, 3); out = Clip(id, name, d)
    for pid, tr in src['tracks'].items():
        for prop, keys in tr.items():
            if prop == 'img':
                last = [k for k in keys if k['t'] <= a + 1e-6]
                out.c['tracks'].setdefault(pid, {})['img'] = [dict(t=0, v=(last[-1] if last else keys[0])['v'], f=0)] + [dict(t=round((k['t'] - a) * stretch, 3), v=k['v'], f=0) for k in keys if a + 1e-6 < k['t'] < b]
                continue
            e0 = 'linear'
            for x, y in zip(keys, keys[1:]):
                if x['t'] <= a < y['t']: e0 = 'step' if x['e'] == 'step' else 'linear'
            out.k(pid, prop, [(0, sample(keys, a), e0)] + [(round((k['t'] - a) * stretch, 3), k['v'], k['e']) for k in keys if a < k['t'] < b] + [(d, sample(keys, b))])
    return out.c
clips.append(slice_clip(PREVIEW, 'tt_p1', '① 불 보고 움찔·느낌표 (0.3~1.0초)', 0.25, 1.05))
clips.append(slice_clip(PREVIEW, 'tt_p2', '② 고무공 도움닫기 → 점프 → 티라 위 환영 (1.1~3.9초)', 1.10, SLOW1))
clips.append(slice_clip(PREVIEW, 'tt_p3', '③ 하강·한쪽씩 착지 → 엣헴 (3.9~5.2초)', SLOW1 - 0.05, 5.15))
clips.append(slice_clip(PREVIEW, 'tt_land_slow', '④ 착지만 느리게 ×4 (4.0~4.5초)', 4.0, 4.5, 4.0))
r = Clip('tt_intro_r', '인트로 · 모션 줄이기', END, intro=True)
r.face([(0, 'A')]).ops('excl', [(0, 0), (END, 0)]).k('body', 'rot', [(0, 0), (END, 0)])
clips.append(r.c)
for cl in clips: assert 'op' in cl['tracks'].get('excl', {}) or cl['id'].startswith('tt_p') or cl['id'] == 'tt_land_slow', cl['id']
preview = [dict(label=c_['name'], clip=c_['id']) for c_ in clips if not c_.get('loop')]
proj = dict(version=1, name='타로타로', stage=dict(w=400, h=400), parts=parts, clips=clips, rules=[], baseClip='tt_idle', faces=FACES, preview=preview,
            reducedClip={'tt_intro': 'tt_intro_r'}, display=dict(size=170, corner='right', margin=16, hideOnMobile=False, closable=False), assets=assets)
s = json.dumps(proj, ensure_ascii=False, separators=(',', ':')); open(OUT + 'tarotaro.json', 'w').write(s)
json.dump(dict(guide_stage=G['stage'], K=K, store=STORE, stage_scale=S, rig_at_stage=RIG_AT, height_stage_px=round(H_STAGE, 1), pivots_guide=PIV, pivots_world=PIVW,
               crops=crops, faces=FACE, state_B_adjust_world=dict(earL=[EARLX, 0.9], earR=EARRX, antenna=ANTX), draw_order=[p['id'] for p in parts],
               timeline=[[0, 0.30, 'A 대기'], [0.37, 0.85, 'B 움찔·느낌표(0.37~0.90)'], [0.85, 1.62, 'B 멈칫·준비'], [1.62, 1.74, '웅크림'], [1.74, 2.30, 'A 이륙(바깥 층 궤적)'],
                         [2.30, 3.90, 'A 환영 슬로모션 왼쪽 8~11°'], [3.90, 4.16, '하강(오른쪽으로 휨)'], [4.16, 4.28, '왼쪽 바퀴 → 오른쪽 바퀴 접지'], [4.28, 4.45, '수습'],
                         [4.45, 4.85, 'C 엣헴'], [4.85, 6.30, 'A']]), open(OUT + 'rig.json', 'w'), ensure_ascii=False, indent=1)
print('json KB', len(s) // 1024, [c_['id'] for c_ in clips])
