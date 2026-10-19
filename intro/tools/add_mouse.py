# 로그인 화면 마우스 반응: 캐릭터 파일에 추가 그림(파츠)과 반응 동작(m_ 로 시작)을 넣습니다.
# - 재료: mouse/<번호_이름>/ (GPT 제작 자료 그대로: 추가파츠 PNG·추가파츠_조립정보.json·세부콘티)
# - 추가 파츠는 평소에 보이지 않게, 기존 동작(인트로·대기 등) 전부에 '투명(op 0)' 키를 넣음 → 인트로·에디터의 기존 동작은 그대로
# - 반응 동작은 '키가 있는 속성만' 대기 자세 위에 덮어씀(로그인 화면 login/mouse.js 가 재생). 시선 따라보기는 실시간 계산이라 여기 없음
# - 여러 번 실행해도 결과 같음(이전에 넣은 m_ 파츠·그림·동작을 지우고 다시 넣음)
# 실행: python3 intro/tools/add_mouse.py   (저장소 맨 위에서)
import base64, io, json, os, sys
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
M = os.path.join(ROOT, 'mouse')


def crop_asset(png, src_rect, w, h, k=1.5):
    """source_rect 만 잘라 그릴 크기(원본 좌표 w×h)의 k배 해상도로 저장 → data URI"""
    sx, sy, sw, sh = src_rect
    im = Image.open(png).convert('RGBA').crop((sx, sy, sx + sw, sy + sh))
    im = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


class Clip:
    def __init__(s, id, name, dur):
        s.c = dict(id=id, name=name, dur=dur, loop=False, follow='center', tracks={}, mouse=True)
    def k(s, part, prop, keys):
        out = {}
        for x in keys:
            t = round(x[0], 3); out[t] = dict(t=t, v=round(float(x[1]), 4), e=x[2] if len(x) > 2 else 'inout')
        s.c['tracks'].setdefault(part, {})[prop] = [out[t] for t in sorted(out)]; return s
    def img(s, part, keys):
        s.c['tracks'].setdefault(part, {})['img'] = [dict(t=round(t, 3), v=v, f=0) for t, v in keys]; return s


def strip_old(p):
    """예전에 이 스크립트가 넣은 것 지우기(m_ 파츠·m_ 그림·m_ 동작, 기존 동작의 m_ 파츠 키)"""
    p['parts'] = [pt for pt in p['parts'] if not pt['id'].startswith('m_')]
    for pt in p['parts']:
        pt['images'] = [v for v in pt['images'] if not v['asset'].startswith('m_')]
    p['clips'] = [c for c in p['clips'] if not c['id'].startswith('m_')]
    for c in p['clips']:
        for pid in [k for k in c['tracks'] if k.startswith('m_')]: del c['tracks'][pid]
    p['assets'] = {k: v for k, v in p['assets'].items() if not k.startswith('m_')}
    p['preview'] = [x for x in p.get('preview', []) if not x['clip'].startswith('m_')]


def hide_new_parts_in_old_clips(p, new_ids):
    for c in p['clips']:
        if c['id'].startswith('m_'): continue
        for pid in new_ids:
            c['tracks'].setdefault(pid, {})['op'] = [dict(t=0, v=0, e='step'), dict(t=round(c['dur'], 3), v=0, e='step')]


def part_index(p, pid):
    return [i for i, pt in enumerate(p['parts']) if pt['id'] == pid][0]


def new_part(id, name, parent, pivot, images):
    return dict(id=id, name=name, parent=parent, pivot=dict(x=pivot[0], y=pivot[1]),
                rest=dict(x=pivot[0], y=pivot[1], rot=0, sx=1, sy=1, op=1, img=0), images=images, follow=dict(on=False, max=0))


# ───────────────────────── 길통이: 어? 뭐지? ─────────────────────────
def giltong():
    f = os.path.join(ROOT, 'giltong', 'giltong.json'); p = json.load(open(f, encoding='utf-8')); strip_old(p)
    d = os.path.join(M, '01_길통이'); G = json.load(open(os.path.join(d, '추가파츠_조립정보.json'), encoding='utf-8'))
    A = {a['id']: a for a in G['additional_assets']}
    def add_img(aid, name, src=None, dst=None, key=None):
        a = A[aid]; x, y, w, h = dst or a['guide_draw_rect_in_existing_1254_coordinates']
        key = key or ('m_g_' + aid); p['assets'][key] = crop_asset(os.path.join(d, a['file']), src or a['source_rect_xywh'], w, h)
        return dict(asset=key, name=name, x=x, y=y, w=w, h=h)
    mouth = p['parts'][part_index(p, 'mouth')]
    mouth['images'] += [add_img('mouth_curious', '마우스: 호기심 ㅇ 입'), add_img('mouth_thinking', '마우스: 생각하는 입')]
    MC, MT = len(mouth['images']) - 2, len(mouth['images']) - 1
    # 턱 괸 팔(2026-10-19 손 파츠 수정본): 소스 어깨 [850,950] → 부모 [520,822], 배율 0.32
    #  ① 팔 전체는 원래 왼팔 자리(몸통·머리 뒤)에 그림  ② 윗부분(몸통 좌표 [300,600,230,190] 안)만 머리 다음에 한 번 더 → 얼굴 앞 손, 어깨 끝은 셔츠 뒤
    arm = A['arm_chin']; sx, sy, sw, sh = arm['source_rect_xywh']; dx, dy, dw, dh = arm['guide_draw_rect_in_existing_1254_coordinates']; k = dw / sw
    cx0, cy0, cw, ch = 300, 600, 230, 190
    tx0, ty0, tx1, ty1 = max(dx, cx0), max(dy, cy0), min(dx + dw, cx0 + cw), min(dy + dh, cy0 + ch)
    top_src = [sx + (tx0 - dx) / k, sy + (ty0 - dy) / k, (tx1 - tx0) / k, (ty1 - ty0) / k]
    armB = new_part('m_armChin', '마우스: 턱 괸 왼팔(몸통 뒤)', 'body', (520, 822), [add_img('arm_chin', '턱 가까이 올린 왼팔')])
    armT = new_part('m_armChinTop', '마우스: 턱 괸 왼팔 윗부분(얼굴 앞)', 'body', (520, 822),
                    [add_img('arm_chin', '턱 괸 팔 윗부분', src=top_src, dst=[tx0, ty0, tx1 - tx0, ty1 - ty0], key='m_g_arm_chin_top')])
    qi = add_img('question', '물음표'); qi['x'] += 28; qi['y'] -= 14            # 모자 챙과 붙지 않게 조금 오른쪽 위로
    q = new_part('m_question', '마우스: 물음표', 'head', (qi['x'] + qi['w'] / 2, qi['y'] + qi['h']), [qi])
    ai = part_index(p, 'armL'); p['parts'][ai + 1:ai + 1] = [armB]
    hi = part_index(p, 'head'); p['parts'][hi + 1:hi + 1] = [armT]          # 머리 다음, 눈·눈썹·입 앞
    p['parts'].append(q)
    NEW = ['m_armChin', 'm_armChinTop', 'm_question']
    hide_new_parts_in_old_clips(p, NEW)
    # '어? 뭐지?' 2.6초 — 세부콘티 흐름에 움직임을 더 풍부하게(2026-10-19 사용자 요청: 눈·얼굴 더 많이)
    D = 2.6; c = Clip('m_mouse', '마우스: 어? 뭐지? (2.6초)', D)
    c.img('mouth', [(0, 0), (0.14, MC), (0.86, MT), (1.98, 0)])
    # 눈: 움찔(가늘게) → 휘둥그레 → 생각할 때 위·옆을 굴림 → 끄덕일 때 한 번 깜빡 → 기본
    for e in ('eyeL', 'eyeR'):
        c.k(e, 'sx', [(0, 1), (0.1, 0.96), (0.24, 1.16, 'out'), (0.36, 1.1), (0.8, 1.1, 'out'), (0.92, 1.0), (D, 1)])
        c.k(e, 'sy', [(0, 1), (0.1, 0.86), (0.24, 1.06, 'out'), (0.36, 1.0), (0.8, 1.0), (0.92, 1.0), (1.99, 1.0, 'in'), (2.04, 0.12, 'out'), (2.11, 1.0), (D, 1)])
        c.k(e, 'x', [(0, 0), (0.9, 0, 'inout'), (1.08, 12), (1.24, 12, 'inout'), (1.34, -8), (1.5, -8, 'inout'), (1.6, 6), (1.9, 0), (D, 0)])
        c.k(e, 'y', [(0, 0), (0.9, 0, 'inout'), (1.08, -14), (1.24, -14, 'inout'), (1.34, -6), (1.6, -8), (1.9, 0), (D, 0)])
    c.k('browL', 'y', [(0, 0), (0.1, 4), (0.24, -16, 'out'), (0.36, -12), (0.82, -12, 'out'), (0.94, -20), (1.3, -18), (1.86, -18, 'out'), (2.0, 0), (D, 0)])
    c.k('browR', 'y', [(0, 0), (0.1, 4), (0.24, -16, 'out'), (0.36, -12), (0.82, -12, 'out'), (0.94, 0), (D, 0)])
    c.k('browL', 'rot', [(0, 0), (0.82, 0), (0.94, -10), (1.86, -10), (2.0, 0), (D, 0)])
    # 머리: 살짝 움츠렸다(예비 동작) '어?' 하며 톡 솟음 → 오른쪽 크게 갸웃(살짝 넘었다 돌아옴) → 생각하며 천천히 흔들 → 바로 → 끄덕
    c.k('head', 'y', [(0, 0), (0.1, 6, 'out'), (0.24, -12, 'out'), (0.4, -3), (0.6, 0), (1.86, 0, 'out'), (2.0, 14, 'inout'), (2.16, -4), (2.32, 2), (2.45, 0), (D, 0)])
    c.k('head', 'sy', [(0, 1), (0.1, 0.975), (0.24, 1.03, 'out'), (0.4, 1.0), (1.86, 1.0, 'out'), (2.0, 0.97), (2.16, 1.01), (2.3, 1.0), (D, 1)])
    c.k('head', 'rot', [(0, 0), (0.1, -1.5), (0.26, 2), (0.65, 1.5), (1.02, 10, 'out'), (1.16, 8), (1.34, 9.2), (1.52, 7.6), (1.64, 8.4), (1.86, 0), (2.0, -1), (2.18, 0.8), (2.35, 0), (D, 0)])
    c.k('head', 'x', [(0, 0), (0.65, 0), (1.02, 10), (1.64, 10), (1.86, 0), (D, 0)])
    c.k('body', 'rot', [(0, 0), (0.12, -0.6), (0.3, 0.6), (0.65, 0.4), (1.05, 2.2), (1.64, 2.2), (1.95, -0.8), (2.2, 0.3), (2.4, 0), (D, 0)])
    c.k('body', 'sy', [(0, 1), (0.1, 0.985), (0.24, 1.02, 'out'), (0.42, 1.0), (1.96, 1.0), (2.02, 0.99), (2.16, 1.0), (D, 1)])
    c.k('cape', 'rot', [(0, 0), (0.22, 0), (0.4, 1.2), (0.75, 0.2), (1.15, 3), (1.7, 2.6), (2.05, -1.4), (2.3, 0.4), (2.5, 0), (D, 0)])     # 망토는 0.1초쯤 늦게
    # 팔: 원래 왼팔이 들리다 머리 옆에서 턱 괸 팔로 바뀜 → 손이 턱에 톡(살짝 넘었다 제자리) → 내릴 때 반대로
    c.k('armL', 'rot', [(0, -48), (0.26, -48, 'in'), (0.4, -18), (1.8, -18, 'out'), (2.06, -48), (D, -48)])
    c.k('armL', 'op', [(0, 1, 'step'), (0.4, 0, 'step'), (1.8, 1, 'step'), (D, 1)])
    for pid in ('m_armChin', 'm_armChinTop'):
        c.k(pid, 'op', [(0, 0, 'step'), (0.4, 1, 'step'), (1.8, 0, 'step'), (D, 0)])
        c.k(pid, 'rot', [(0, -30), (0.4, -30, 'out'), (0.58, 4), (0.7, -1), (0.8, 0), (1.3, 0), (1.42, 2), (1.54, 0), (1.62, 0, 'in'), (1.8, -30), (D, -30)])
    c.k('armR', 'rot', [(0, 48), (0.24, 48), (0.34, 42), (0.5, 48), (D, 48)])
    # 물음표: 톡 튀어나와 좌우로 까딱 → 사라짐
    c.k('m_question', 'op', [(0, 0, 'step'), (0.78, 1, 'step'), (1.62, 1, 'linear'), (1.76, 0), (D, 0)])
    c.k('m_question', 'sx', [(0, 0.6), (0.78, 0.6, 'out'), (0.92, 1.15), (1.02, 0.94), (1.1, 1.0), (D, 1)]).k('m_question', 'sy', [(0, 0.6), (0.78, 0.6, 'out'), (0.92, 1.15), (1.02, 0.94), (1.1, 1.0), (D, 1)])
    c.k('m_question', 'rot', [(0, 0), (0.78, -14), (0.95, 10), (1.12, -6), (1.3, 4), (1.48, 0), (D, 0)])
    c.k('m_question', 'y', [(0, 10), (0.78, 10, 'out'), (0.95, -6), (1.1, 0), (D, 0)])
    p['clips'].append(c.c)
    p.setdefault('preview', []).append(dict(label=c.c['name'], clip=c.c['id']))
    # 평소: 눈은 커서 쪽으로 크게(원본 26px), 눈썹 따라, 머리는 최대 5도 + 옆으로 살짝, 몸도 조금 기울임, 가끔 깜빡임
    p['mouse'] = dict(clip='m_mouse', dwell=0.7, gap=3.0, gaze=dict(eyeL=[26, 18], eyeR=[26, 18], browL=[8, 7], browR=[8, 7]),
                      head='head', headMax=5, headShift=[10, 6], body='body', bodyMax=1.5, blink=dict(parts=['eyeL', 'eyeR'], every=[2.4, 5.5]))
    json.dump(p, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return dict(parts=len(p['parts']), kb=os.path.getsize(f) // 1024, top_src=[round(v, 1) for v in top_src])


# ───────────────────────── 공통 도우미 ─────────────────────────
import math
def load_char(rel, folder):
    f = os.path.join(ROOT, rel); p = json.load(open(f, encoding='utf-8')); strip_old(p)
    d = os.path.join(M, folder); G = json.load(open(os.path.join(d, '추가파츠_조립정보.json'), encoding='utf-8'))
    A = {a['id']: a for a in G['additional_assets']}
    def img(aid, name, key, rect=None):
        a = A[aid]; x, y, w, h = rect or a.get('guide_draw_rect_in_existing_1254_coordinates') or a['guide_draw_rect_in_existing_engine_coordinates']
        if key not in p['assets']: p['assets'][key] = crop_asset(os.path.join(d, a['file']), a['source_rect_xywh'], w, h)
        return dict(asset=key, name=name, x=x, y=y, w=w, h=h)
    return f, p, A, img


def save_char(f, p, c_list, mouse):
    for c in c_list:
        p['clips'].append(c.c); p.setdefault('preview', []).append(dict(label=c.c['name'], clip=c.c['id']))
    p['mouse'] = mouse
    json.dump(p, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return dict(parts=len(p['parts']), clips=[c.c['id'] for c in c_list], kb=os.path.getsize(f) // 1024)


def DIRS():   # (접미사, d: 커서 쪽 −1=왼쪽 / +1=오른쪽, 이름)
    return [('L', -1, '왼쪽'), ('R', 1, '오른쪽')]


# ───────────────────────── 차로차로: 여기 봐! 파닥·찡긋 ─────────────────────────
def charocharo():
    f, p, A, img = load_char('charo-pet.json', '02_차로차로')
    m = p['parts'][part_index(p, 'mouth')]; m['images'] += [img('mouth_curious', '마우스: 호기심 입', 'm_c_mouth_curious'), img('mouth_smile', '마우스: 찡긋 웃음 입', 'm_c_mouth_smile')]
    MC, MS = len(m['images']) - 2, len(m['images']) - 1
    eL = p['parts'][part_index(p, 'eyeL')]; eR = p['parts'][part_index(p, 'eyeR')]
    eL['images'].append(img('eye_wink', '마우스: 윙크 눈', 'm_c_eye_wink')); WL = len(eL['images']) - 1
    eR['images'].append(img('eye_wink', '마우스: 윙크 눈', 'm_c_eye_wink', A['eye_wink']['right_eye_draw_rect'])); WR = len(eR['images']) - 1
    GY = {0: 0, 1: -1.25, 2: -2.5, 3: -3.74, 4: -5.0}                 # 몸을 기울일 때 바퀴가 바닥에 붙도록(무대 단위, 조립정보 값)
    def gy(a): a = abs(a); lo = int(a); hi = min(4, lo + 1); return GY[lo] + (GY[hi] - GY[lo]) * (a - lo)
    clips = []
    for suf, d, nm in DIRS():
        D = 2.7; c = Clip('m_mouse_' + suf, '마우스: 여기 봐! 파닥·찡긋 · 커서 ' + nm + ' (2.7초)', D)
        near, far = ('wingL', 'wingR') if d < 0 else ('wingR', 'wingL')
        ns = 1 if near == 'wingL' else -1; fs = -ns                     # 날개 올리는 방향: 왼날개 +, 오른날개 −
        ne, fe = ('eyeL', 'eyeR') if d < 0 else ('eyeR', 'eyeL')
        c.img('mouth', [(0, 0), (0.14, MC), (1.22, MS), (1.98, 0)])
        c.img(ne, [(0, 0), (1.22, WL if ne == 'eyeL' else WR), (1.98, 0)])
        for e in ('eyeL', 'eyeR'):
            wink = e == ne
            c.k(e, 'sx', [(0, 1), (0.08, 0.96), (0.2, 1.14, 'out'), (0.32, 1.08), (1.16, 1.08, 'out'), (1.22, 1.0), (D, 1)])
            c.k(e, 'sy', [(0, 1), (0.08, 0.86), (0.2, 1.12, 'out'), (0.32, 1.08), (1.16, 1.08, 'out'), (1.22, 1.0), (1.99, 1.0, 'in'), (2.05, 0.12, 'out'), (2.12, 1.0), (D, 1)])
            c.k(e, 'x', [(0, 0), (0.2, d * 6), (0.6, d * 10), (1.16, d * 12), (1.22, 0 if wink else d * 6), (1.9, 0), (D, 0)])
            c.k(e, 'y', [(0, 0), (0.2, -4), (0.6, -6), (1.16, -6), (1.22, 0 if wink else -3), (1.9, 0), (D, 0)])
        for b in ('browL', 'browR'):
            c.k(b, 'y', [(0, 0), (0.08, 4), (0.2, -14, 'out'), (0.32, -9), (1.16, -9, 'out'), (1.22, -4 if b[-1] == ne[-1] else 0), (1.6, -4 if b[-1] == ne[-1] else 0), (1.9, 0), (D, 0)])
        # 몸: 웅크렸다(예비) 커서 쪽으로 기울며 톡 늘어남 → 파닥일 때 통통 → 찡긋 때 한 번 더 까딱 → 바로
        rk = [(0, 0), (0.1, -d * 0.8), (0.28, d * 2.2), (0.52, d * 3.5), (0.6, d * 3.2), (1.15, d * 3), (1.22, d * 4.2), (1.36, d * 2), (1.65, d * 2), (1.9, -d * 0.6), (2.15, d * 0.3), (2.35, 0), (D, 0)]
        c.k('body', 'rot', rk).k('body', 'y', [(t, gy(v)) for t, v in rk])
        c.k('body', 'sy', [(0, 1), (0.1, 0.965), (0.2, 1.035, 'out'), (0.34, 1.0), (0.66, 1.02), (0.74, 0.99), (0.86, 1.015), (0.96, 0.995), (1.08, 1.0), (1.22, 1.02), (1.32, 1.0), (D, 1)])
        c.k('body', 'sx', [(0, 1), (0.1, 1.025), (0.2, 0.975, 'out'), (0.34, 1.0), (0.66, 0.985), (0.74, 1.01), (0.86, 0.99), (0.96, 1.005), (1.08, 1.0), (D, 1)])
        # 날개: 가까운 날개 먼저 들고 멈칫 → 두 번 파닥(크게·작게, 먼 날개 0.08초 늦게) → 찡긋 때 가까운 날개만 살짝 → 0.1초 늦게 반동 후 정착
        c.k(near, 'rot', [(0, 0), (0.28, 0, 'out'), (0.5, ns * 16), (0.6, ns * 15), (0.68, ns * 20), (0.78, ns * 4), (0.88, ns * 14), (0.98, ns * 2), (1.08, ns * 10), (1.15, ns * 6), (1.3, ns * 9), (1.65, ns * 8), (1.82, -ns * 3), (1.98, ns * 1.5), (2.12, 0), (D, 0)])
        c.k(far, 'rot', [(0, 0), (0.3, 0, 'out'), (0.52, fs * 4), (0.68, fs * 4), (0.76, fs * 10), (0.86, fs * 2), (0.96, fs * 7), (1.06, fs * 1), (1.16, fs * 3), (1.4, 0), (1.9, 0), (2.0, -fs * 1.5), (2.14, 0), (D, 0)])
        clips.append(c)
    hide_new_parts_in_old_clips(p, [])
    return save_char(f, p, clips, dict(clip='m_mouse', dir=True, dwell=0.65, gap=4.0, gaze=dict(eyeL=[22, 16], eyeR=[22, 16], browL=[7, 6], browR=[7, 6]),
                                       body='body', bodyMax=2, lag=[dict(part='wingL', rot=3, tau=0.45), dict(part='wingR', rot=3, tau=0.45)], blink=dict(parts=['eyeL', 'eyeR'], every=[2.2, 5.0])))


# ───────────────────────── 첨다니: 신호가 통했나? 쫑긋·빙긋 ─────────────────────────
def chumdani():
    f, p, A, img = load_char('chumdani/chumdani.json', '04_첨다니')
    eL = p['parts'][part_index(p, 'eyeL')]; eR = p['parts'][part_index(p, 'eyeR')]
    eL['images'].append(img('eye_smile', '마우스: 빙긋 눈', 'm_ch_eye_smile')); SL = len(eL['images']) - 1
    eR['images'].append(img('eye_smile', '마우스: 빙긋 눈', 'm_ch_eye_smile', A['eye_smile']['right_eye_draw_rect'])); SR = len(eR['images']) - 1
    sp = img('sparkle', '발견 반짝', 'm_ch_sparkle')
    p['parts'].append(new_part('m_sparkle', '마우스: 발견 반짝', 'ant', (sp['x'] + sp['w'] / 2, sp['y'] + sp['h'] / 2), [sp]))
    hide_new_parts_in_old_clips(p, ['m_sparkle'])
    GY = {0: 0, 1: -3.9, 2: -7.8, 3: -11.7}                            # 기울일 때 바퀴 접지(원본 좌표, 조립정보 값)
    def gy(a): a = abs(a); lo = min(2, int(a)); return GY[lo] + (GY[lo + 1] - GY[lo]) * (a - lo)
    clips = []
    for suf, d, nm in DIRS():
        D = 2.8; c = Clip('m_mouse_' + suf, '마우스: 신호가 통했나? 쫑긋·빙긋 · 커서 ' + nm + ' (2.8초)', D)
        near, far = ('earL', 'earR') if d < 0 else ('earR', 'earL')
        ns = 1 if near == 'earL' else -1; fs = -ns                       # 귀 올리는 방향: 왼귀 +, 오른귀 −
        nb, fb = ('browL', 'browR') if d < 0 else ('browR', 'browL')
        c.img('eyeL', [(0, 0), (0.96, SL), (2.05, 0)]).img('eyeR', [(0, 0), (0.96, SR), (2.05, 0)])
        for e in ('eyeL', 'eyeR'):
            c.k(e, 'sx', [(0, 1), (0.06, 0.95), (0.18, 1.16, 'out'), (0.3, 1.1), (0.9, 1.1, 'out'), (0.96, 1.0), (D, 1)])
            c.k(e, 'sy', [(0, 1), (0.06, 0.85), (0.18, 1.16, 'out'), (0.3, 1.1), (0.9, 1.1, 'out'), (0.96, 1.0), (2.06, 1.0, 'in'), (2.11, 0.12, 'out'), (2.18, 1.0), (D, 1)])
            c.k(e, 'x', [(0, 0), (0.18, d * 8), (0.9, d * 10), (0.96, 0), (D, 0)]).k(e, 'y', [(0, 0), (0.18, -6), (0.5, -8), (0.9, -6), (0.96, 0), (D, 0)])
        c.k(nb, 'y', [(0, 0), (0.06, 3), (0.18, -12, 'out'), (0.3, -9), (0.9, -9, 'out'), (0.96, -5), (1.9, -5), (2.05, 0), (D, 0)])
        c.k(fb, 'y', [(0, 0), (0.06, 3), (0.18, -5, 'out'), (0.3, -3), (0.9, -3, 'out'), (0.96, -5), (1.9, -5), (2.05, 0), (D, 0)])
        rk = [(0, 0), (0.08, -d * 0.6), (0.3, d * 1.4), (0.85, d * 2.2), (1.0, d * 1.4), (1.2, d * 1.6), (1.7, d * 1.2), (1.95, -d * 0.5), (2.2, d * 0.2), (2.4, 0), (D, 0)]
        c.k('body', 'rot', rk).k('body', 'y', [(t, gy(v)) for t, v in rk])
        c.k('body', 'sy', [(0, 1), (0.08, 0.975), (0.2, 1.025, 'out'), (0.34, 1.0), (1.22, 1.0), (1.32, 0.988), (1.44, 1.006), (1.56, 1.0), (D, 1)])
        c.k('body', 'sx', [(0, 1), (0.08, 1.02), (0.2, 0.985, 'out'), (0.34, 1.0), (1.22, 1.0), (1.32, 1.01), (1.44, 0.996), (1.56, 1.0), (D, 1)])
        c.k('ant', 'rot', [(0, 0), (0.1, -d * 3), (0.3, d * 4), (0.85, d * 4), (1.0, d * 6), (1.12, d * 3), (1.82, d * 3), (1.98, -d * 3), (2.14, d * 1.2), (2.3, 0), (D, 0)])
        c.k(near, 'rot', [(0, 0), (0.2, ns * 2), (0.42, ns * 14), (0.52, ns * 11), (0.85, ns * 12), (1.0, ns * 9), (1.2, ns * 8), (1.88, ns * 8), (2.06, -ns * 3), (2.22, ns * 1.2), (2.38, 0), (D, 0)])
        c.k(far, 'rot', [(0, 0), (0.3, fs * 3), (0.85, fs * 3), (1.0, -fs * 9), (1.2, -fs * 8), (1.88, -fs * 8), (2.06, fs * 3), (2.22, -fs * 1.2), (2.38, 0), (D, 0)])
        # 와이파이: 강함 세 조각이 사라졌다가 점 → 안쪽 → 바깥 차례로 톡톡 켜짐 → 한 번 부드럽게 일렁(실제 통신 상태와 무관)
        for i, on in ((1, 0.30), (2, 0.48), (3, 0.66)):
            w = 'wifi%d' % i
            c.k(w, 'op', [(0, 1), (0.15, 0, 'step'), (on, 1), (1.2, 1), (1.45, 0.7), (1.7, 1), (D, 1)])
            c.k(w, 'sx', [(0, 1), (on, 0.7, 'out'), (on + 0.08, 1.18), (on + 0.16, 1.0), (D, 1)]).k(w, 'sy', [(0, 1), (on, 0.7, 'out'), (on + 0.08, 1.18), (on + 0.16, 1.0), (D, 1)])
        c.k('m_sparkle', 'op', [(0, 0, 'step'), (0.9, 1, 'step'), (1.45, 1, 'linear'), (1.65, 0), (D, 0)])
        c.k('m_sparkle', 'sx', [(0, 0.6), (0.9, 0.6, 'out'), (1.02, 1.12), (1.12, 1.0), (D, 1)]).k('m_sparkle', 'sy', [(0, 0.6), (0.9, 0.6, 'out'), (1.02, 1.12), (1.12, 1.0), (D, 1)])
        c.k('m_sparkle', 'rot', [(0, -20), (0.9, -20, 'out'), (1.2, 10), (1.65, 18), (D, 18)])
        clips.append(c)
    return save_char(f, p, clips, dict(clip='m_mouse', dir=True, dwell=0.9, gap=5.0, gaze=dict(eyeL=[15, 11], eyeR=[15, 11], browL=[5, 4], browR=[5, 4]),
                                       body='body', bodyMax=1.2, lag=[dict(part='ant', rot=3, tau=0.4), dict(part='earL', rot=2.5, tau=0.5), dict(part='earR', rot=2.5, tau=0.5)],
                                       blink=dict(parts=['eyeL', 'eyeR'], every=[2.4, 5.2])))


# ───────────────────────── 티라: 먹는 건가? …딸꾹, 뿍! ─────────────────────────
def tira():
    f, p, A, img = load_char('tira_v3/tira_v3.json', '03_티라')
    fb = A['face_base']; bb = Image.open(os.path.join(M, '03_티라', fb['file'])).getchannel('A').getbbox()   # 1254 전체 캔버스 → 실제 그림 범위만(좌표는 1:1)
    fb['source_rect_xywh'] = [bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]]; fb['guide_draw_rect_in_existing_1254_coordinates'] = list(fb['source_rect_xywh'])
    face = new_part('m_face', '마우스: 얼굴 안쪽 바탕', 'head', (603, 650), [img('face_base', '얼굴 바탕', 'm_t_face')])
    eL = new_part('m_eyeL', '마우스: 왼눈(점눈)', 'head', (517, 446), [img('eye_dot', '점눈', 'm_t_eye')])
    eR = new_part('m_eyeR', '마우스: 오른눈(점눈)', 'head', (679, 446), [img('eye_dot', '점눈', 'm_t_eye', A['eye_dot']['right_eye_draw_rect'])])
    mo = new_part('m_mouth', '마우스: 입', 'head', (600, 571), [img('mouth_base', '다섯 이빨 기본 입', 'm_t_mouth_base'), img('mouth_curious', '호기심 ㅇ 입', 'm_t_mouth_curious')])
    hi = part_index(p, 'headImg'); p['parts'][hi + 1:hi + 1] = [face, eL, eR, mo]      # headImg 다음, collar 앞
    NEW = ['m_face', 'm_eyeL', 'm_eyeR', 'm_mouth']; hide_new_parts_in_old_clips(p, NEW)
    clips = []
    for suf, d, nm in DIRS():
        D = 2.7; c = Clip('m_mouse_' + suf, '마우스: 먹는 건가? …딸꾹, 뿍! · 커서 ' + nm + ' (2.7초)', D)
        farFoot = 'footR' if d < 0 else 'footL'
        c.img('headImg', [(0, 0), (0.95, 1), (1.55, 0)])
        c.img('m_mouth', [(0, 0), (0.14, 1), (0.95, 1), (1.55, 0)])
        for pid in NEW: c.k(pid, 'op', [(0, 1, 'step'), (0.95, 0, 'step'), (1.55, 1, 'step'), (D, 1)])
        for e in ('m_eyeL', 'm_eyeR'):
            c.k(e, 'sx', [(0, 1), (0.06, 0.9), (0.18, 1.2, 'out'), (0.3, 1.1), (D, 1.1)]).k(e, 'sy', [(0, 1), (0.06, 0.8), (0.18, 1.2, 'out'), (0.3, 1.1), (0.95, 1.1), (1.55, 1.0), (2.05, 1.0, 'in'), (2.1, 0.12, 'out'), (2.17, 1.0), (D, 1)])
            c.k(e, 'sx', [(0, 1), (0.06, 0.9), (0.18, 1.2, 'out'), (0.3, 1.1), (0.95, 1.1), (1.55, 1.0), (D, 1)])
            c.k(e, 'x', [(0, 0), (0.18, d * 10), (0.75, d * 12), (0.95, d * 12), (1.55, 0), (D, 0)]).k(e, 'y', [(0, 0), (0.18, 6), (0.75, 8), (0.95, 8), (1.55, 0), (D, 0)])   # 커서를 먹이처럼 내려다봄
        # 몸·머리: 커서 쪽으로 기울며(머리 먼저) 먼 발 꼼지락 → 들숨 → 딸꾹! 머리가 뒤로 젖혀짐 → 멈칫 → 멀뚱히 바로
        c.k('head', 'rot', [(0, 0), (0.06, -d * 1), (0.3, d * 3), (0.75, d * 6), (0.85, d * 5.4), (0.95, d * 5), (1.0, -d * 4), (1.12, -d * 2.5), (1.55, -d * 1.5), (1.85, d * 0.8), (2.1, 0), (D, 0)])
        c.k('head', 'y', [(0, 0), (0.75, 0, 'out'), (0.9, -6), (0.95, -6), (0.99, -14, 'out'), (1.1, -4), (1.3, 0), (D, 0)])
        c.k('sway', 'rot', [(0, 0), (0.3, d * 0.6), (0.75, d * 2), (0.95, d * 1.8), (1.05, -d * 0.8), (1.55, d * 0.4), (1.8, -d * 0.4), (2.05, 0), (D, 0)])
        c.k('sway', 'sy', [(0, 1), (0.75, 1.0, 'inout'), (0.92, 1.018), (0.97, 0.985), (1.08, 1.006), (1.2, 1.0), (D, 1)]).k('sway', 'sx', [(0, 1), (0.75, 1.0, 'inout'), (0.92, 0.985), (0.97, 1.012), (1.08, 0.997), (1.2, 1.0), (D, 1)])
        c.k('tail', 'rot', [(0, 0), (0.4, 0), (0.85, -d * 6), (1.0, -d * 6), (1.08, d * 9), (1.25, -d * 3), (1.6, 0), (1.9, d * 2.5), (2.15, -d * 1), (2.4, 0), (D, 0)])
        fs = 1 if farFoot == 'footR' else -1
        c.k(farFoot, 'y', [(0, 0), (0.32, 0), (0.42, -8), (0.52, 0), (0.6, -6), (0.7, 0), (D, 0)]).k(farFoot, 'rot', [(0, 0), (0.32, 0), (0.42, fs * 4), (0.52, 0), (0.6, fs * 3), (0.7, 0), (D, 0)])
        # 불: 작게 → 작게 줄인 큰 불 → 작게 → 끔 (늘 화면 왼쪽, 원래 방향 그대로)
        c.img('fire', [(0, 0), (0.95, 0), (0.99, 1), (1.10, 0)])
        c.k('fire', 'op', [(0, 0, 'step'), (0.95, 1, 'step'), (1.17, 0, 'step'), (D, 0)])
        c.k('fire', 'sx', [(0, 1, 'step'), (0.99, 0.6, 'step'), (1.10, 1, 'step'), (D, 1)]).k('fire', 'sy', [(0, 1, 'step'), (0.99, 0.65, 'step'), (1.10, 1, 'step'), (D, 1)])
        clips.append(c)
    base = {k: dict(op=1) for k in NEW}; base.update({k: dict(op=0) for k in ('sign11B', 'sign11F', 'sign14', 'mask', 'fire')}); base['headImg'] = dict(img=0); base['m_mouth'] = dict(op=1, img=0)
    return save_char(f, p, clips, dict(clip='m_mouse', dir=True, dwell=0.85, gap=6.0, gaze=dict(m_eyeL=[14, 10], m_eyeR=[14, 10]), head='head', headMax=3, headShift=[4, 3],
                                       lag=[dict(part='tail', rot=-3, tau=0.6), dict(part='sway', rot=0.8, tau=0.5)], blink=dict(parts=['m_eyeL', 'm_eyeR'], every=[2.6, 5.6]), base=base))


# ───────────────────────── 도로덕: 빼꼼…들켰덕! ─────────────────────────
def doroduck():
    f, p, A, img = load_char('doroduck/doroduck.json', '05_도로덕')
    a = A['eye_focus']
    eL = p['parts'][part_index(p, 'eyeL')]; eR = p['parts'][part_index(p, 'eyeR')]
    eL['images'].append(img('eye_focus', '마우스: 집중 눈', 'm_d_eye_focus')); FL = len(eL['images']) - 1
    eR['images'].append(img('eye_focus', '마우스: 집중 눈', 'm_d_eye_focus', a['right_eye_draw_rect'])); FR = len(eR['images']) - 1
    clips = []
    for suf, d, nm in DIRS():
        D = 2.9; c = Clip('m_mouse_' + suf, '마우스: 빼꼼…들켰덕! · 커서 ' + nm + ' (2.9초)', D)
        ne, fe = ('eyeL', 'eyeR') if d < 0 else ('eyeR', 'eyeL')
        farFoot, ffs = ('footR', 1) if d < 0 else ('footL', -1)
        c.img(fe, [(0, 0), (0.16, FL if fe == 'eyeL' else FR), (1.1, 1), (2.3, 0)])
        c.img(ne, [(0, 0), (1.1, 1), (2.3, 0)])
        c.k(ne, 'sx', [(0, 1), (0.16, 1.18, 'out'), (0.3, 1.12), (1.04, 1.12, 'out'), (1.1, 1.0), (D, 1)])
        c.k(fe, 'sy', [(0, 1), (0.1, 0.8), (0.16, 1.0), (D, 1)])
        for e in ('eyeL', 'eyeR'):
            c.k(e, 'x', [(0, 0), (0.16, d * 8), (0.8, d * 9), (0.86, d * 4), (1.04, d * 4), (1.1, 0), (D, 0)]).k(e, 'y', [(0, 0), (0.16, -2), (0.8, -2), (1.1, 0), (D, 0)])
            c.k(e, 'sy', [(0, 1), (0.1, 0.8 if e == ne else 0.8), (0.16, 1.0), (2.3, 1.0), (2.36, 1.0, 'in'), (2.41, 0.15, 'out'), (2.48, 1.0), (D, 1)])
        # 몸: 반대로 살짝 망설임 → 커서 쪽으로 빼꼼(늘어나며) → 들킨 듯 멈칫(살짝 움찔) → 눈웃음·날개 으쓱 → 천천히 내림 → 바로
        rk = [(0, 0), (0.16, -d * 1), (0.4, d * 3), (0.8, d * 4.4), (0.86, d * 3.6), (0.92, d * 4), (1.1, d * 4), (1.35, d * 1.5), (2.3, d * 1.2), (2.5, -d * 0.6), (2.7, 0), (D, 0)]
        c.k('body', 'rot', rk).k('body', 'y', [(t, -abs(v) * 0.75) for t, v in rk])
        c.k('body', 'sx', [(0, 1), (0.4, 0.99), (0.8, 0.982), (0.86, 1.01), (0.95, 0.995), (1.1, 1.0), (1.35, 1.02), (1.5, 1.0), (D, 1)])
        c.k('body', 'sy', [(0, 1), (0.4, 1.015), (0.8, 1.028), (0.86, 0.985), (0.95, 1.005), (1.1, 1.0), (1.35, 0.985), (1.5, 1.0), (D, 1)])
        c.k(farFoot, 'x', [(0, 0), (0.3, 0), (0.42, ffs * 6), (0.54, 0), (0.64, ffs * 5), (0.76, 0), (1.75, 0), (1.85, ffs * 4), (1.95, 0), (D, 0)])
        c.k(farFoot, 'y', [(0, 0), (0.3, 0), (0.42, -6), (0.54, 0), (0.64, -5), (0.76, 0), (1.75, 0), (1.85, -4), (1.95, 0), (D, 0)])
        c.k(farFoot, 'rot', [(0, 0), (0.3, 0), (0.42, ffs * 8), (0.54, 0), (0.64, ffs * 6), (0.76, 0), (1.75, 0), (1.85, ffs * 5), (1.95, 0), (D, 0)])
        c.k('wingL', 'rot', [(0, 0), (1.1, 0, 'out'), (1.32, 30), (1.42, 26), (1.65, 28, 'inout'), (2.3, 3), (2.45, -4), (2.6, 1), (2.75, 0), (D, 0)])
        c.k('wingR', 'rot', [(0, 0), (1.1, 0, 'out'), (1.32, -30), (1.42, -26), (1.65, -28, 'inout'), (2.3, -3), (2.45, 4), (2.6, -1), (2.75, 0), (D, 0)])
        clips.append(c)
    base = {k: dict(op=0) for k in ('sign', 'signText', 'signF', 'signTextF', 'wingRf')}
    return save_char(f, p, clips, dict(clip='m_mouse', dir=True, dwell=0.8, gap=5.0, gaze=dict(eyeL=[12, 6, 1], eyeR=[12, 6, 1]), body='body', bodyMax=1.5,
                                       lag=[dict(part='wingL', rot=3, tau=0.5), dict(part='wingR', rot=3, tau=0.5)], blink=dict(parts=['eyeL', 'eyeR'], every=[2.4, 5.4]), base=base))


# ───────────────────────── 타로타로: 한쪽 바퀴로 까딱, 엣헴! ─────────────────────────
def tarotaro():
    f, p, A, img = load_char('tarotaro/tarotaro.json', '06_타로타로')
    a = A['eye_dot']
    eL = new_part('m_eyeL', '마우스: 왼눈(점눈)', 'body', (539, 681), [img('eye_dot', '점눈', 'm_tt_eye')])
    eR = new_part('m_eyeR', '마우스: 오른눈(점눈)', 'body', (661, 681), [img('eye_dot', '점눈', 'm_tt_eye', a['right_eye_draw_rect'])])
    mo = new_part('m_mouth', '마우스: 정면 호기심 입', 'body', (600, 795), [img('mouth_curious', '정면 호기심 ㅇ 입', 'm_tt_mouth')])
    ei = part_index(p, 'eyes'); p['parts'][ei + 1:ei + 1] = [eL, eR]
    mi = part_index(p, 'mouth'); p['parts'][mi + 1:mi + 1] = [mo]
    NEW = ['m_eyeL', 'm_eyeR', 'm_mouth']; hide_new_parts_in_old_clips(p, NEW)
    P = (600.0, 1155.0)
    def T(theta, Ax):   # 선택한 바퀴 바닥을 축으로 돌 때 몸통 이동량(원본 좌표): A + R(θ)(P−A) − P
        r = math.radians(theta); vx, vy = P[0] - Ax, 0.0
        return Ax + vx * math.cos(r) - vy * math.sin(r) - P[0], 1155 + vx * math.sin(r) + vy * math.cos(r) - P[1]
    clips = []
    for suf, d, nm in DIRS():
        D = 2.8; c = Clip('m_mouse_' + suf, '마우스: 한쪽 바퀴로 까딱, 엣헴! · 커서 ' + nm + ' (2.8초)', D)
        Ax = 408.0 if d < 0 else 792.0
        th = [(0, 0), (0.08, -d * 0.6), (0.25, d * 2), (0.5, d * 5), (0.62, d * 6.8), (0.74, d * 5.6), (0.85, d * 6), (0.95, d * 5.6), (1.05, d * 6.2), (1.15, d * 6),
              (1.6, d * 3), (1.9, d * 1), (2.15, 0), (D, 0)]
        dense = []
        for (t0, a0), (t1, a1) in zip(th, th[1:]):
            for i in range(4):
                u = i / 4; dense.append((t0 + (t1 - t0) * u, a0 + (a1 - a0) * (u * u * (3 - 2 * u))))
        dense.append(th[-1])
        c.k('body', 'rot', [(t, v, 'linear') for t, v in dense])
        c.k('body', 'x', [(t, T(v, Ax)[0], 'linear') for t, v in dense]).k('body', 'y', [(t, T(v, Ax)[1], 'linear') for t, v in dense])
        c.k('land', 'rot', [(0, 0), (D, 0)])
        c.k('body', 'sy', [(0, 1), (2.15, 1.0, 'in'), (2.2, 0.99), (2.3, 1.0), (D, 1)]).k('body', 'sx', [(0, 1), (2.15, 1.0, 'in'), (2.2, 1.01), (2.3, 1.0), (D, 1)])
        # 얼굴: 점눈(마우스 A) → B 집중(작은 ㅇ 입, 눈 조금 커짐) → C 엣헴(기존 엣헴 눈·입) → A
        c.k('eyes', 'op', [(0, 0, 'step'), (1.15, 1, 'step'), (2.15, 0, 'step'), (D, 0)])
        c.img('eyes', [(0, 2)]).img('mouth', [(0, 0), (1.15, 2), (2.15, 0)])
        c.k('mouth', 'op', [(0, 1, 'step'), (0.12, 0, 'step'), (1.15, 1, 'step'), (D, 1)])
        c.k('m_mouth', 'op', [(0, 0, 'step'), (0.12, 1, 'step'), (1.15, 0, 'step'), (D, 0)])
        for e in ('m_eyeL', 'm_eyeR'):
            c.k(e, 'op', [(0, 1, 'step'), (1.15, 0, 'step'), (2.15, 1, 'step'), (D, 1)])
            c.k(e, 'sx', [(0, 1), (0.06, 0.92), (0.18, 1.14, 'out'), (0.3, 1.06), (D, 1.06)])
            c.k(e, 'sy', [(0, 1), (0.06, 0.8), (0.18, 1.14, 'out'), (0.3, 1.06), (2.15, 1.06), (2.24, 1.0, 'in'), (2.29, 0.12, 'out'), (2.36, 1.0), (D, 1)])
            c.k(e, 'x', [(0, 0), (0.18, d * 8), (1.15, d * 8), (2.15, 0), (D, 0)]).k(e, 'y', [(0, 0), (0.18, -4), (1.15, -4), (2.15, 0), (D, 0)])
        # 귀·안테나: 0.1초 늦게 반동, 엣헴 때 귀 쫑긋
        c.k('earL', 'rot', [(0, 0), (0.35, d * 6), (0.7, -d * 4), (1.0, d * 3), (1.25, 4), (1.6, -2), (1.8, 4), (2.3, -2), (2.5, 0), (D, 0)])
        c.k('earR', 'rot', [(0, 0), (0.35, d * 6), (0.7, -d * 4), (1.0, d * 3), (1.25, -4), (1.6, 2), (1.8, -4), (2.3, 2), (2.5, 0), (D, 0)])
        c.k('antenna', 'rot', [(0, 0), (0.35, -d * 4), (0.75, d * 3), (1.05, -d * 2), (1.3, 2), (1.6, -1.5), (1.9, 1), (2.3, -1), (2.5, 0), (D, 0)])
        clips.append(c)
    base = dict(eyes=dict(op=0), m_eyeL=dict(op=1), m_eyeR=dict(op=1), m_mouth=dict(op=0), excl=dict(op=0), bodyImg=dict(img=0))
    return save_char(f, p, clips, dict(clip='m_mouse', dir=True, dwell=0.85, gap=6.0, gaze=dict(m_eyeL=[12, 9], m_eyeR=[12, 9]), body='body', bodyMax=1.2,
                                       lag=[dict(part='earL', rot=3, tau=0.45), dict(part='earR', rot=3, tau=0.45), dict(part='antenna', rot=-2.5, tau=0.55)],
                                       blink=dict(parts=['m_eyeL', 'm_eyeR'], every=[2.4, 5.2]), base=base))


if __name__ == '__main__':
    todo = sys.argv[1:] or ['giltong', 'charocharo', 'chumdani', 'tira', 'doroduck', 'tarotaro']
    print({k: globals()[k]() for k in todo})
