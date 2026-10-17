# 로그인 인트로용 차로차로 동작(i_charo, 6.7초)과 표정 프리셋 f22를 charo-pet.json에 넣습니다.
# 기존 파츠(parent·pivot·rest·이미지 x/y/w/h)와 기존 동작·표정은 건드리지 않고, 같은 id만 새로 덮어씁니다(다시 실행해도 결과 같음).
# 실행: python3 intro/tools/build_charo_intro.py   (저장소 맨 위에서)
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
F = os.path.join(ROOT, 'charo-pet.json')
p = json.load(open(F, encoding='utf-8'))
parts = {pt['id']: pt for pt in p['parts']}

# ── 실제 데이터에서 이름으로 이미지 번호를 다시 확인(번호가 바뀌었으면 멈춤) ──
def idx(part, name):
    names = [v.get('name', '') for v in parts[part]['images']]
    assert name in names, (part, name, names)
    return names.index(name)
FACE_A = dict(eyeL=idx('eyeL', '기본'), eyeR=idx('eyeR', '기본'), browL=idx('browL', '기본 눈썹'), browR=idx('browR', '기본 눈썹'), mouth=idx('mouth', '기본 미소'))
FACE_B = dict(eyeL=idx('eyeL', '질끈 > <'), eyeR=idx('eyeR', '질끈 > <'), browL=idx('browL', '질끈 > < 눈썹'), browR=idx('browR', '질끈 > < 눈썹'),
              mouth=idx('mouth', '폭소 (이·혀) · 01 대폭소'))
assert FACE_A == dict(eyeL=0, eyeR=0, browL=0, browR=0, mouth=0) and FACE_B == dict(eyeL=3, eyeR=3, browL=3, browR=3, mouth=1), (FACE_A, FACE_B)
f00 = [f for f in p['faces'] if f['id'] == 'f00'][0]; assert f00['img'] == FACE_A

# 화면에서 보이는 몸통 높이 H(무대 px) = 몸통 그림 높이 × 몸통 배율
H = parts['body']['images'][0]['h'] * parts['body']['rest']['sy']          # ≈ 233.7
# 날개 대칭: 왼쪽 +θ = 위로, 오른쪽 −θ = 위로. 날개 끝 반지름(뿌리→끝 × 배율)이 조금 달라 오른쪽 각도를 줄여 끝 이동 거리를 맞춤
def tip_r(pid, far_x):
    pt = parts[pid]; return abs(far_x - pt['pivot']['x']) * pt['rest']['sx']
wl = parts['wingL']['images'][0]; wr = parts['wingR']['images'][0]
RL = tip_r('wingL', wl['x']); RR = tip_r('wingR', wr['x'] + wr['w'])
KR = round(RL / RR, 3)                                                       # 오른쪽 날개 각도 배율

class Clip:
    def __init__(s, id, name, dur, **kw):
        s.c = dict(id=id, name=name, dur=dur, loop=False, follow='center', tracks={}, intro=True)   # 눈은 정면(에디터·미리보기에서 커서를 따라가지 않게); s.c.update(kw)
    def k(s, part, prop, keys):
        out = {}
        for x in keys: t = round(x[0], 3); out[t] = dict(t=t, v=round(float(x[1]), 3), e=x[2] if len(x) > 2 else 'inout')
        s.c['tracks'].setdefault(part, {})[prop] = [out[t] for t in sorted(out)]; return s
    def face(s, keys):   # [(t, FACE)] — 눈 둘·눈썹 둘·입을 같은 순간에
        for part in ('eyeL', 'eyeR', 'browL', 'browR', 'mouth'):
            s.c['tracks'].setdefault(part, {})['img'] = [dict(t=round(t, 3), v=F_[part], f=0) for t, F_ in keys]
        return s
def wings(c, L, lag=0.0, kr=KR, rlag=None):
    """L = 왼쪽 날개 키 [(t, 각도, ease)]. 오른쪽은 부호를 바꾸고 끝 거리 보정, lag초 늦게."""
    c.k('wingL', 'rot', L)
    R = [(round(t + lag, 3), -v * kr) + tuple(r) for (t, v, *r) in L]
    c.k('wingR', 'rot', R)

END = 6.7
c = Clip('i_charo', '로그인 인트로 (6.7초)', END)
c.face([(0, FACE_A), (2.30, FACE_B), (4.55, FACE_A)])        # A → B(땅에서 떨어지는 순간) → A(착지 정리 뒤)

# ── 몸통: 위치(y)는 바운스·점프만. 다가오기·정렬 이동/축소는 인트로 재생기(바깥 층)가 맡음 ──
hops = [0.04, 0.32, 0.60, 0.88]; hh = [0.075, 0.06, 0.04, 0.02]          # 4번, 가까워질수록 낮게(H 비율)
JUMP = 0.17                                                                # 점프 높이: H의 17%
y = [(0, 0)]; sy = [(0, 1)]; sx = [(0, 1)]; rot = [(0, 0)]
tilt = [4.5, -4.0, 3.5, -3.0]
for t, h, tl in zip(hops, hh, tilt):
    y += [(t, 0, 'out'), (t + 0.14, -h * H, 'in'), (t + 0.28, 0)]
    sy += [(t, 0.96, 'out'), (t + 0.06, 1.035), (t + 0.14, 1.0), (t + 0.26, 1.0, 'in')]
    sx += [(t, 1.035, 'out'), (t + 0.06, 0.975), (t + 0.14, 1.0), (t + 0.26, 1.0, 'in')]
    rot += [(t + 0.14, tl)]
rot += [(1.16, 0, 'out')]
# 1.20 멈춤: 짧게 눌렸다 원래 높이로 → 티라 구간(1.45~2.55)엔 작은 들썩임만
sy += [(1.16, 1.0, 'out'), (1.22, 0.93, 'out'), (1.34, 1.03), (1.44, 1.0), (1.62, 1.0), (1.69, 1.015), (1.78, 1.0), (1.90, 1.0), (1.96, 1.012), (2.04, 1.0)]
sx += [(1.16, 1.0, 'out'), (1.22, 1.06, 'out'), (1.34, 0.985), (1.44, 1.0)]
y += [(1.62, 0, 'out'), (1.69, -3, 'in'), (1.78, 0), (1.90, 0, 'out'), (1.96, -2, 'in'), (2.04, 0)]
# 2.16~2.30 웅크렸다 2.30 땅을 박차고 펴짐 → 슬로모션 시작(2.55) 때 아직 올라가는 중
sy += [(2.16, 1.0, 'in'), (2.28, 0.90, 'out'), (2.36, 1.07), (2.46, 1.035), (2.55, 1.03)]
sx += [(2.16, 1.0, 'in'), (2.28, 1.08, 'out'), (2.36, 0.95), (2.46, 0.975), (2.55, 0.98)]
y += [(2.30, 0, 'out'), (2.55, -0.13 * H)]
# 2.55~4.15 환영 슬로모션: 몸이 먼저 느려지며 정점(17%) → 아주 천천히 살짝 가라앉음(정지 아님)
y += [(3.30, -JUMP * H, 'inout'), (4.15, -0.155 * H, 'in')]
sy += [(3.30, 1.015), (4.15, 1.02, 'in')]
sx += [(3.30, 0.995), (4.15, 0.99, 'in')]
rot += [(2.28, 0), (2.55, 2.0, 'inout'), (3.20, 5.0), (3.70, 4.0), (4.15, 5.5, 'in')]    # 약 5° 기울어 균형 잡기
c.k('body', 'x', [(0, 0), (2.55, 0), (3.20, 2.5), (3.70, 1.5), (4.15, 2.5, 'in'), (4.36, 0.5, 'out'), (4.55, 0)])
# 4.15~4.55 작은 착지: 몸이 먼저 떨어져 눌리고(날개는 위에 남았다 늦게 내려옴) 작은 반동 한 번
y += [(4.36, 0, 'out'), (4.43, -3, 'in'), (4.50, 0), (END, 0)]
sy += [(4.34, 1.02, 'in'), (4.36, 0.92, 'out'), (4.46, 1.03), (4.55, 1.0), (END, 1.0)]
sx += [(4.34, 0.99, 'in'), (4.36, 1.07, 'out'), (4.46, 0.985), (4.55, 1.0), (END, 1.0)]
rot += [(4.36, 1.0, 'out'), (4.46, -1.5), (4.55, 0), (END, 0)]
c.k('body', 'y', y).k('body', 'sy', sy).k('body', 'sx', sx).k('body', 'rot', rot)

# ── 날개(왼쪽 기준, 오른쪽은 대칭·늦게) ──
L = [(0, 0)]
for t in hops:                                   # 몸보다 늦게: 떠오른 뒤 위로, 정점 지나 내려옴
    L += [(t + 0.05, 16, 'inout'), (t + 0.19, -4, 'inout')]
L += [(1.16, -4, 'out'), (1.27, 22, 'inout'), (1.41, -6, 'inout'), (1.53, 0)]          # 몸은 멈췄는데 날개가 한 박자 더
L += [(1.64, 0, 'out'), (1.70, 5, 'inout'), (1.80, 0), (2.02, 0, 'out'), (2.10, 18), (2.16, 18, 'in')]  # 들썩 + 이륙 직전 살짝 들고 멈춤
L += [(2.24, -10, 'out')]                         # 웅크릴 때 아래로 한번
t = 2.30
while t < 2.45:                                   # 파닥파닥: 0.06초 간격(빠르게) 2.30~2.48
    L += [(t, 44, 'linear'), (round(t + 0.06, 3), 4, 'linear')]; t = round(t + 0.12, 3)
L += [(2.55, 40, 'inout'), (3.05, 6, 'inout'), (3.55, 38, 'inout'), (4.05, 10, 'inout')]   # 슬로모션 1.5회
L += [(4.15, 12, 'out'), (4.30, 30, 'inout'), (4.38, 28, 'inout'), (4.47, -6, 'inout'), (4.55, 0)]   # 떨어질 때 위에 남음 → 늦게 내려옴
L += [(4.75, 0, 'out'), (4.85, 6, 'inout'), (4.98, 0), (END, 0)]                         # 날개 끝 한 번 정리
c.k('wingL', 'rot', L)
def rlag(t):   # 오른쪽 날개 지연(초). 구간 경계에서 서서히 바꿔 키 순서가 뒤집히지 않게
    if t < 1.6: return 0.04
    if t < 2.29: return 0.03
    if t < 2.56: return 0.025
    if t < 2.70: return 0.025 + (t - 2.56) / 0.14 * 0.095
    if t < 4.05: return 0.12
    if t < 4.20: return 0.12 - (t - 4.05) / 0.15 * 0.09
    return 0.03
R = []
for (t, v, *r) in L:
    lag = rlag(t)                                                                                  # 한쪽이 조금 늦게 → 균형이 살짝 틀어짐
    amp = 0.9 if 2.56 <= t < 4.1 else 1.0                                                          # 슬로모션에선 오른쪽이 조금 덜 → 기울기 방향과 맞춤
    R.append((round(t + lag, 3) if 0 < t < END else t, -v * KR * amp) + tuple(r))
c.k('wingR', 'rot', R)
c.c['notes'] = dict(H=round(H, 1), jump_px=round(JUMP * H, 1), wing_tip_r=[round(RL, 1), round(RR, 1)], wingR_scale=KR,
                    faces={'A': 'f00', 'B': 'f22'}, face_switch=[0, 2.30, 4.55], slow=[2.55, 4.15], layers='전체 위치·크기 = 인트로 재생기 / 몸통 점프·기울기 = 이 동작')
INTRO = c.c

# 모션 줄이기: 표정 A, 몸 고정, 환영 때 날개만 아주 작게 한 번
r = Clip('i_charo_r', '로그인 인트로 (모션 줄이기)', END)
r.face([(0, FACE_A)])
r.k('body', 'y', [(0, 0), (END, 0)]).k('body', 'rot', [(0, 0), (END, 0)]).k('body', 'sy', [(0, 1), (END, 1)]).k('body', 'sx', [(0, 1), (END, 1)])
wings(r, [(0, 0), (2.55, 0), (2.9, 8), (3.3, 0), (END, 0)], lag=0.03)
REDUCED = r.c

p['clips'] = [x for x in p['clips'] if x['id'] not in ('i_charo', 'i_charo_r')] + [INTRO, REDUCED]
p['faces'] = [f for f in p['faces'] if f['id'] != 'f22'] + [dict(id='f22', name='22 신나서 질끈 (인트로)', img=FACE_B, mods={}, intro=True)]
p['preview'] = [v for v in p['preview'] if v['clip'] not in ('i_charo', 'i_charo_r')] + [dict(label='로그인 인트로', clip='i_charo', extra=True)]
p.setdefault('reducedClip', {})['i_charo'] = 'i_charo_r'
json.dump(p, open(F, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok H=%.1f jump=%.1fpx wing tips L=%.1f R=%.1f KR=%s' % (H, JUMP * H, RL, RR, KR))
