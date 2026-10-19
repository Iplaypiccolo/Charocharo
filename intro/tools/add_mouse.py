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
    def add_img(aid, name):
        a = A[aid]; x, y, w, h = a['guide_draw_rect_in_existing_1254_coordinates']
        key = 'm_g_' + aid; p['assets'][key] = crop_asset(os.path.join(d, a['file']), a['source_rect_xywh'], w, h)
        return dict(asset=key, name=name, x=x, y=y, w=w, h=h)
    mouth = p['parts'][part_index(p, 'mouth')]
    mouth['images'] += [add_img('mouth_curious', '마우스: 호기심 ㅇ 입'), add_img('mouth_thinking', '마우스: 생각하는 입')]
    MC, MT = len(mouth['images']) - 2, len(mouth['images']) - 1
    arm = new_part('m_armChin', '마우스: 턱 괸 왼팔', 'body', (520, 822), [add_img('arm_chin', '턱 가까이 올린 왼팔')])
    qi = add_img('question', '물음표'); qi['x'] += 28; qi['y'] -= 14            # 모자 챙과 붙지 않게 조금 오른쪽 위로
    q = new_part('m_question', '마우스: 물음표', 'head', (qi['x'] + qi['w'] / 2, qi['y'] + qi['h']), [qi])
    hi = part_index(p, 'head'); p['parts'][hi + 1:hi + 1] = [arm]          # 머리 다음, 눈·눈썹·입 앞
    p['parts'].append(q)
    hide_new_parts_in_old_clips(p, ['m_armChin', 'm_question'])
    # 세부콘티 2.3초. 회전은 기존 기본(대기) 위 '절대값'(팔 -48/+48은 대기 동작 값과 같게)
    c = Clip('m_mouse', '마우스: 어? 뭐지? (2.3초)', 2.3)
    c.img('mouth', [(0, 0), (0.14, MC), (0.85, MT), (1.95, 0)])
    c.k('eyeL', 'sx', [(0, 1), (0.08, 1, 'out'), (0.2, 1.08), (0.8, 1.08, 'out'), (0.9, 1), (2.3, 1)]).k('eyeL', 'sy', [(0, 1), (0.08, 1, 'out'), (0.2, 0.96), (0.8, 0.96, 'out'), (0.9, 1), (2.3, 1)])
    c.k('eyeR', 'sx', [(0, 1), (0.08, 1, 'out'), (0.2, 1.08), (0.8, 1.08, 'out'), (0.9, 1), (2.3, 1)]).k('eyeR', 'sy', [(0, 1), (0.08, 1, 'out'), (0.2, 0.96), (0.8, 0.96, 'out'), (0.9, 1), (2.3, 1)])
    c.k('browL', 'y', [(0, 0), (0.08, 0, 'out'), (0.2, -8), (0.8, -8, 'out'), (0.92, -12), (1.85, -12, 'out'), (1.97, 0), (2.3, 0)])
    c.k('browR', 'y', [(0, 0), (0.08, 0, 'out'), (0.2, -8), (0.8, -8, 'out'), (0.92, 0), (2.3, 0)])
    # 머리: 먼저 1도 → 0.65~1.05 오른쪽 6도 → 1.60~1.80 바로 → 작은 끄덕임 한 번(아래로 살짝·세로 눌림) → 정착
    c.k('head', 'rot', [(0, 0), (0.22, 1), (0.65, 1), (1.05, 6), (1.6, 6), (1.82, 0), (2.3, 0)])
    c.k('head', 'y', [(0, 0), (1.82, 0, 'out'), (1.94, 7, 'inout'), (2.1, 0), (2.3, 0)])
    c.k('head', 'sy', [(0, 1), (1.82, 1, 'out'), (1.94, 0.985, 'inout'), (2.1, 1), (2.3, 1)])
    c.k('body', 'rot', [(0, 0), (0.65, 0), (1.05, 1), (1.6, 1), (1.9, 0), (2.3, 0)])
    c.k('cape', 'rot', [(0, 0), (0.75, 0), (1.15, 1.6), (1.7, 1.6), (2.0, -0.5), (2.2, 0), (2.3, 0)])     # 망토 0.1초 늦게
    # 팔: 기존 왼팔이 올라가다(머리 옆에서) 사라지고 턱 괸 팔이 그 자리에서 올라옴 → 내릴 때 반대로
    c.k('armL', 'rot', [(0, -48), (0.25, -48, 'in'), (0.4, -14), (1.78, -14, 'out'), (2.05, -48), (2.3, -48)])
    c.k('armL', 'op', [(0, 1, 'step'), (0.4, 0, 'step'), (1.78, 1, 'step'), (2.3, 1)])
    c.k('m_armChin', 'op', [(0, 0, 'step'), (0.4, 1, 'step'), (1.78, 0, 'step'), (2.3, 0)])
    c.k('m_armChin', 'rot', [(0, -26), (0.4, -26, 'out'), (0.62, 0), (1.6, 0, 'in'), (1.78, -26), (2.3, -26)])
    c.k('armR', 'rot', [(0, 48), (2.3, 48)])
    c.k('m_question', 'op', [(0, 0, 'step'), (0.75, 1, 'step'), (1.6, 1, 'linear'), (1.75, 0), (2.3, 0)])
    c.k('m_question', 'sx', [(0, 0.7), (0.75, 0.7, 'out'), (0.9, 1.08), (1.0, 1.0), (2.3, 1)]).k('m_question', 'sy', [(0, 0.7), (0.75, 0.7, 'out'), (0.9, 1.08), (1.0, 1.0), (2.3, 1)])
    p['clips'].append(c.c)
    p.setdefault('preview', []).append(dict(label=c.c['name'], clip=c.c['id']))
    p['mouse'] = dict(clip='m_mouse', dwell=0.7, gap=3.0, gaze=dict(eyeL=12, eyeR=12, browL=3.6, browR=3.6), head='head', headMax=2)
    json.dump(p, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return dict(parts=len(p['parts']), kb=os.path.getsize(f) // 1024)


if __name__ == '__main__':
    todo = sys.argv[1:] or ['giltong']
    print({k: globals()[k]() for k in todo})
