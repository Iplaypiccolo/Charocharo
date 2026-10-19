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


if __name__ == '__main__':
    todo = sys.argv[1:] or ['giltong']
    print({k: globals()[k]() for k in todo})
