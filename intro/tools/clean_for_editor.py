# 에디터 정리(2026-10-17): 로그인 인트로에 실제로 쓰는 동작 + 차로차로 '날고 싶어'만 남기고 나머지 동작·반응 규칙·표정 프리셋·안 쓰는 그림을 지웁니다.
# - 정리 전 파일은 보관/2026-10-17_정리전/ 에 그대로 복사해 둠(필요하면 되살리기)
# - 남은 그림의 번호가 바뀌면 동작 키·표정 프리셋·기본 자세의 그림 번호를 함께 고침(순서는 유지)
# ※ m_ 로 시작하는 마우스 반응 동작과 kb_ 키보드·mt_ 터치 반응 동작은 남김. 이 스크립트를 돌린 뒤에는 intro/tools/add_mouse.py 를 다시 실행(이름표를 되살림)
# 실행: python3 intro/tools/clean_for_editor.py   (저장소 맨 위에서. 여러 번 실행해도 결과 같음)
# 다른 스크립트로 캐릭터 파일을 다시 만들었다면(티라 build.py 등) 마지막에 이 스크립트를 다시 실행
import json, os, shutil
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ARC = os.path.join(ROOT, '보관', '2026-10-17_정리전')
KEEP = {
    'charo-pet.json': dict(clips=['c_breath', 'c02', 'i_charo', 'i_charo_r', 'm_mouse_L', 'm_mouse_R', 'kb_type', 'kb_echo', 'kb_private_in', 'kb_private_hold', 'kb_private_out', 'mt_press', 'mt_tap', 'mt_cancel'],
        names={'c_breath': '대기 숨쉬기', 'c02': '날고 싶어! 그런데 안 떠…', 'i_charo': '인트로 (6.3초 전체)', 'i_charo_r': '인트로 · 모션 줄이기'}),
    'chumdani/chumdani.json': dict(clips=['c_idle', 'c_run_i', 'c_jump_i', 'c_welcome', 'c_flip', 'm_mouse_L', 'm_mouse_R', 'kb_type', 'kb_echo', 'kb_private_in', 'kb_private_hold', 'kb_private_out', 'mt_press', 'mt_tap', 'mt_cancel'],
        names={'c_idle': '대기', 'c_run_i': '인트로 ① 제자리 달리기', 'c_jump_i': '인트로 ② 고무공 점프', 'c_welcome': '인트로 ③ 환영 슬로모션', 'c_flip': '인트로 ④ 공중제비(앞 1.75초 사용)'}),
    'giltong/giltong.json': dict(clips=['g_idle', 'g_run_i', 'g_welcome', 'g_finish', 'm_mouse', 'kb_type', 'kb_echo', 'kb_private_in', 'kb_private_hold', 'kb_private_out', 'mt_press', 'mt_tap', 'mt_cancel'],
        names={'m_mouse': '마우스: 어? 뭐지? (2.6초)', 'g_idle': '대기', 'g_run_i': '인트로 ① 제자리 달리기', 'g_welcome': '인트로 ② 환영 슬로모션', 'g_finish': '인트로 ③ 균형 회복(앞 0.6초 사용)'}),
    'doroduck/doroduck.json': dict(clips=['d_idle', 'd_run_i', 'd_welcome', 'd_finish_i', 'm_mouse_L', 'm_mouse_R', 'kb_type', 'kb_echo', 'kb_private_in', 'kb_private_hold', 'kb_private_out', 'mt_press', 'mt_tap', 'mt_cancel'],
        names={'d_idle': '대기', 'd_run_i': '인트로 ① 제자리 달리기', 'd_welcome': '인트로 ② 환영 슬로모션', 'd_finish_i': '인트로 ③ 균형 회복·팻말 내림'}),
    'tira_v3/tira_v3.json': dict(clips=['t_idle', 't_intro', 't_intro_r', 'm_mouse_L', 'm_mouse_R', 'kb_type', 'kb_echo', 'kb_private_in', 'kb_private_hold', 'kb_private_out', 'mt_press', 'mt_tap', 'mt_cancel'],
        names={'t_idle': '대기', 't_intro': '인트로 (6.3초 전체: 불 → 팻말 꺼내기 → 거꾸로 환영 → 다시 넣기)', 't_intro_r': '인트로 · 모션 줄이기'}),
}
os.makedirs(ARC, exist_ok=True)
REPORT = {}
for f, k in KEEP.items():
    path = os.path.join(ROOT, f); p = json.load(open(path, encoding='utf-8'))
    arc = os.path.join(ARC, f.replace('/', '__'))
    if not os.path.exists(arc): shutil.copy(path, arc)                      # 처음 정리할 때만 보관
    before = dict(clips=len(p['clips']), rules=len(p.get('rules', [])), faces=len(p.get('faces', [])), assets=len(p.get('assets', {})))
    keep = [c for c in p['clips'] if c['id'] in k['clips']]
    keep.sort(key=lambda c: k['clips'].index(c['id']))
    for c in keep:
        c['name'] = k['names'].get(c['id'], c['name']); c.pop('previewNext', None)
    p['clips'] = keep; ids = set(c['id'] for c in keep)
    # 반응 규칙: 남은 동작만 가리키는 것만
    rules = []
    for r in p.get('rules', []):
        if r.get('clips'): r['clips'] = [x for x in r['clips'] if x in ids]
        if r.get('clip') not in ids:
            if r.get('clips'): r['clip'] = r['clips'][0]
            else: continue
        if any(r.get(x) and r[x] not in ids for x in ('clipLeft', 'end', 'enter', 'exit')): continue
        rules.append(r)
    p['rules'] = rules
    if p.get('baseClip') not in ids: p['baseClip'] = keep[0]['id']
    # 남은 동작에서 실제 쓰는 그림 번호(+기본 자세) → 안 쓰는 그림 지우고 번호 다시 매김
    used = {pt['id']: {pt['rest'].get('img', 0)} for pt in p['parts']}
    for c in keep:
        for pid, tr in c['tracks'].items():
            for kk in tr.get('img', []): used.setdefault(pid, set()).add(kk['v'])
    remap = {}
    for pt in p['parts']:
        idx = (sorted(i for i in used[pt['id']] if i < len(pt['images'])) or [0]) if pt['images'] else []
        remap[pt['id']] = {o: n for n, o in enumerate(idx)}
        pt['images'] = [pt['images'][i] for i in idx]
        pt['rest']['img'] = remap[pt['id']].get(pt['rest'].get('img', 0), 0)
    for c in keep:
        for pid, tr in c['tracks'].items():
            for kk in tr.get('img', []): kk['v'] = remap[pid][kk['v']]
    # 표정 프리셋: 남은 그림만으로 만들 수 있고, 남은 동작에 실제 나오는 조합만
    combos = set()
    for c in keep:
        fparts = [pid for pid in c['tracks'] if 'img' in c['tracks'][pid]]
        times = sorted(set(kk['t'] for pid in fparts for kk in c['tracks'][pid]['img']))
        for t in times:
            st = {}
            for pid in fparts:
                v = None
                for kk in c['tracks'][pid]['img']:
                    if kk['t'] <= t + 1e-9: v = kk['v']
                if v is not None: st[pid] = v
            combos.add(json.dumps(st, sort_keys=True))
    faces = []
    for fc in p.get('faces', []):
        img = {}
        ok = True
        for pid, v in fc['img'].items():
            if pid not in remap or v not in remap[pid]: ok = False; break
            img[pid] = remap[pid][v]
        if not ok: continue
        if any(all(json.loads(cb).get(pid) == v for pid, v in img.items()) for cb in combos):
            fc['img'] = img; faces.append(fc)
    p['faces'] = faces
    # 미리보기 버튼 = 남은 동작(대기 제외)
    p['preview'] = [dict(label=c['name'], clip=c['id']) for c in keep if not c.get('loop')]
    if p.get('reducedClip'): p['reducedClip'] = {a: b for a, b in p['reducedClip'].items() if a in ids and b in ids}
    used_assets = set(v['asset'] for pt in p['parts'] for v in pt['images'])
    p['assets'] = {a: d for a, d in p.get('assets', {}).items() if a in used_assets}
    json.dump(p, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    REPORT[f] = dict(before=before, after=dict(clips=len(p['clips']), rules=len(p['rules']), faces=len(p['faces']), assets=len(p['assets'])),
                     kb=os.path.getsize(path) // 1024, faces=[x['id'] + ' ' + x['name'] for x in p['faces']])
print(json.dumps(REPORT, ensure_ascii=False, indent=1))
