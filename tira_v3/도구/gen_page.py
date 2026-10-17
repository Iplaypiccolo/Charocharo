# 검수 미리보기 페이지 만들기 (재생기 + 캐릭터 파일 + 검수표 + 점검 이미지를 한 파일에)
import json, base64, io, os
from PIL import Image
G = '/home/claude/tira3/'
def jpg(path, w=None, q=84):
    im = Image.open(path).convert('RGB')
    if w and im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=q, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
REPORT = json.load(open(G + 'work/report.json')) if os.path.exists(G + 'work/report.json') else dict(parts=[], checks=[], timeline=[], requests=[], summary=[])
player = open('/home/claude/charo-pet.js').read()
data = open(G + 'out/tira_v3.json').read(); rig = open(G + 'out/rig.json').read()
assert '</script' not in player and '</' not in data
imgs = dict(cmp=jpg(G + 'out/compare_views.png', 1600), turn=jpg(G + 'out/head_turn_strip.png', 2700), zoom=jpg(G + 'out/fetch_zoom_strip.png', 3140), size=jpg(G + 'out/actual_size.png', 900), fire=jpg(G + 'out/fire_root_zoom.png', 880), pb=jpg(G + 'out/putback_strip.png', 2240))
src = open(G + 'work/page.src.html').read()
out = (src.replace('/*@@PLAYER@@*/', player).replace('/*@@JSON@@*/null', data).replace('/*@@RIG@@*/null', rig)
          .replace('/*@@IMG@@*/null', json.dumps(imgs)).replace('/*@@REPORT@@*/null', json.dumps(REPORT, ensure_ascii=False)))
open(G + 'out/tira3-review.html', 'w').write(out)
print('page KB', len(out) // 1024)
