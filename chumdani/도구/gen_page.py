# 검수 미리보기 페이지 만들기 (재생기 + 캐릭터 파일 + 검수표 + 점검 이미지를 한 파일에)
import json, base64, io
from PIL import Image
G = '/home/claude/chumdani/'
def jpg(path, w=None, q=84):
    im = Image.open(path).convert('RGB')
    if w and im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=q, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
REPORT = json.load(open(G + 'work/report.json'))
player = open('/home/claude/charo-pet.js').read()
data = open(G + 'out/chumdani.json').read(); rig = open(G + 'out/rig.json').read()
assert '</script' not in player and '</' not in data
imgs = dict(asm=jpg(G + 'out/assembly_preview.png', 1600), rot=jpg(G + 'out/wifi_states.png', 1240), size=jpg(G + 'out/actual_size.png', 1400))
src = open(G + 'work/page.src.html').read()
out = (src.replace('/*@@PLAYER@@*/', player).replace('/*@@JSON@@*/null', data).replace('/*@@RIG@@*/null', rig)
          .replace('/*@@IMG@@*/null', json.dumps(imgs)).replace('/*@@REPORT@@*/null', json.dumps(REPORT, ensure_ascii=False)))
open(G + 'out/chumdani-review.html', 'w').write(out)
print('page KB', len(out) // 1024)
