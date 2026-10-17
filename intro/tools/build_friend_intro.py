# 로그인 인트로(2026-10-17 개정)용으로 친구들 파일에 '인트로 전용' 동작만 추가합니다. 기존 동작·파츠는 그대로.
#  - *_run_i : 기존 달리기에서 '멀리서 커지며 다가오기'(뿌리 파츠의 배율 0.55→1, 높이 차)를 뺀 제자리 달리기.
#              원근(점에서 커지기)은 인트로 재생기 바깥 층 하나로만 처리 → 두 번 커지는 일 없음.
#  - c_jump_i: 첨다니 고무공 점프(옆으로 납작 → 위로 쭉 → 공중 → 착지 찌그러짐). 이동 궤적은 바깥 층.
# 실행: python3 intro/tools/build_friend_intro.py   (저장소 맨 위에서. 다시 실행해도 결과 같음)
import json, os, copy
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
def load(f): return json.load(open(os.path.join(ROOT, f), encoding='utf-8'))
def save(f, p): json.dump(p, open(os.path.join(ROOT, f), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
def interp(pts, t):
    if t <= pts[0][0]: return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if t <= b: return va + (vb - va) * (t - a) / (b - a)
    return pts[-1][1]
def in_place(clip, root, new_id, name):
    c = copy.deepcopy(clip); c['id'] = new_id; c['name'] = name; c['intro'] = True
    tr = c['tracks'][root]
    tr.pop('sx', None); tr.pop('sy', None)                         # 다가오기 배율 제거
    ys = tr['y']; ground = [(k['t'], k['v']) for k in ys if k.get('e') == 'out'] or [(0, ys[0]['v'])]
    ground = [(0, ys[0]['v'])] + ground + [(ys[-1]['t'], ys[-1]['v'])]
    for k in ys: k['v'] = round(k['v'] - interp(ground, k['t']), 4)   # 발 닿는 높이를 0으로 → 통통 튀는 높이만 남김
    return c
def put(p, clip):
    p['clips'] = [x for x in p['clips'] if x['id'] != clip['id']] + [clip]
REPORT = {}
for f, run, root, nid in [('giltong/giltong.json', 'g_run', 'body', 'g_run_i'), ('doroduck/doroduck.json', 'd_run', 'body', 'd_run_i'), ('chumdani/chumdani.json', 'c_run', 'rig', 'c_run_i')]:
    p = load(f); srcs = [c for c in p['clips'] if c['id'] == run]
    if not srcs: REPORT[nid] = '원본 달리기 없음(에디터 정리 뒤) → 기존 ' + nid + ' 유지'; continue   # 정리 뒤에는 이미 만든 동작을 그대로 둠
    src = srcs[0]
    c = in_place(src, root, nid, '인트로 제자리 달리기 (원근은 인트로 재생기)'); put(p, c)
    ys = [k['v'] for k in c['tracks'][root]['y']]; REPORT[nid] = dict(y_range=[min(ys), max(ys)])
    if f.startswith('chumdani'):
        # 고무공 점프: 뿌리(rig) 기준점이 몸 가운데라 납작해질 때 바퀴가 뜨지 않게 y로 보정(발은 기준점 아래 68px, 무대 단위)
        FEET = 68.0
        S = [(0, 1.0, 1.0), (0.10, 1.26, 0.76), (0.16, 1.26, 0.76), (0.24, 0.84, 1.22), (0.40, 1.0, 1.0), (0.54, 1.0, 1.0), (0.60, 1.18, 0.82), (0.70, 0.95, 1.05), (0.80, 1.0, 1.0)]
        j = dict(id='c_jump_i', name='인트로 고무공 점프', dur=0.8, loop=False, follow='center', intro=True, tracks={})
        j['tracks']['rig'] = {
            'sx': [dict(t=t, v=sx, e='out' if i % 2 else 'inout') for i, (t, sx, sy) in enumerate(S)],
            'sy': [dict(t=t, v=sy, e='out' if i % 2 else 'inout') for i, (t, sx, sy) in enumerate(S)],
            'y': [dict(t=t, v=round(FEET * (1 - sy), 2) if (t < 0.24 or t >= 0.54) else 0.0, e='inout') for (t, sx, sy) in S]}
        # 들뜬 신호: 점프 동안 와이파이 전체 켜짐, 귀·안테나는 늦게 따라옴
        for w in ('wifi1', 'wifi2', 'wifi3'): j['tracks'][w] = {'op': [dict(t=0, v=1, e='step'), dict(t=0.8, v=1, e='step')]}
        j['tracks']['earL'] = {'rot': [dict(t=0, v=0, e='inout'), dict(t=0.22, v=-14, e='inout'), dict(t=0.45, v=8, e='inout'), dict(t=0.66, v=-6, e='inout'), dict(t=0.8, v=0, e='inout')]}
        j['tracks']['earR'] = {'rot': [dict(t=0, v=0, e='inout'), dict(t=0.22, v=14, e='inout'), dict(t=0.45, v=-8, e='inout'), dict(t=0.66, v=6, e='inout'), dict(t=0.8, v=0, e='inout')]}
        j['tracks']['ant'] = {'rot': [dict(t=0, v=0, e='inout'), dict(t=0.26, v=-10, e='inout'), dict(t=0.5, v=7, e='inout'), dict(t=0.7, v=-3, e='inout'), dict(t=0.8, v=0, e='inout')]}
        put(p, j); REPORT['c_jump_i'] = 'added'
    save(f, p)
# 도로덕: 환영 뒤 균형 회복 + 팻말 내리기까지만(0~0.85초). 원래 마무리의 '작아져 정렬'은 인트로 재생기가 하므로 몸통 이동·축소는 0.7초 이후 빼고 고정
p = load('doroduck/doroduck.json'); _s = [c for c in p['clips'] if c['id'] == 'd_finish']
src = _s[0] if _s else None
if src is None: print(json.dumps(REPORT, ensure_ascii=False)); raise SystemExit   # 정리 뒤: d_finish_i·팻말 배율은 이미 반영됨
c = copy.deepcopy(src); c['id'] = 'd_finish_i'; c['name'] = '인트로 균형 회복·팻말 내림'; c['intro'] = True; c['dur'] = 0.85
for part, tr in c['tracks'].items():
    for prop, ks in list(tr.items()):
        if prop == 'img': continue
        if part == 'body' and prop in ('y', 'sx', 'sy'):
            keep = [k for k in ks if k['t'] <= 0.7]; keep.append(dict(t=0.85, v=keep[-1]['v'], e='inout')); tr[prop] = keep
        else:
            v85 = interp([(k['t'], k['v']) for k in ks], 0.85)
            keep = [k for k in ks if k['t'] < 0.85] + [dict(t=0.85, v=round(v85, 4), e='inout')]; tr[prop] = keep
put(p, c)
# 2026-10-17 사용자 요청: 도로덕 '합니다!' 팻말 25% 크게(손잡이 끝 기준점 그대로). 원래 배율을 baseScale로 남겨 다시 실행해도 1.25배 한 번만
sg = [pt for pt in p['parts'] if pt['id'] == 'sign'][0]
sg.setdefault('baseScale', sg['rest']['sx']); sg['rest']['sx'] = sg['rest']['sy'] = round(sg['baseScale'] * 1.25, 4)
REPORT['doroduck_sign_scale'] = [sg['baseScale'], sg['rest']['sx']]
save('doroduck/doroduck.json', p); REPORT['d_finish_i'] = 'added'
print(json.dumps(REPORT, ensure_ascii=False))
