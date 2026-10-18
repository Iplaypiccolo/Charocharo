# 인트로 화면 재생 검수(헤드리스 크롬). 실행: python3 intro/tests/t_intro.py  (저장소 맨 위에서)
import subprocess, time, json, os
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
srv = subprocess.Popen(['python3', '-m', 'http.server', '8813', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.6)
URL = 'http://localhost:8813/intro/index.html'
# 캐릭터마다 그림 네 모서리를 화면 논리 좌표(1000×600)로 바꿔 상자를 구함
BOX = """(id)=>{const CP=CharoPet,I=__intro,c=I.cast.find(x=>x.id===id),L=I.info().last[id]; if(!L) return null;
 const W=CP.worldMatrices(c.P,L.fp), cvw=document.getElementById('cv').width, cvh=document.getElementById('cv').height, sc=Math.min(cvw/1000,cvh/600);
 let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9; c.P.parts.forEach(pt=>{const f=L.fp[pt.id]; if(!f||f.op<=0.01) return; const v=pt.images[f.img]||pt.images[0]; if(!v) return;
  const m=CP.mul(L.view,W[pt.id]); [[v.x,v.y],[v.x+v.w,v.y],[v.x,v.y+v.h],[v.x+v.w,v.y+v.h]].forEach(q=>{const a=CP.apply(m,q[0],q[1]); x0=Math.min(x0,a[0]/sc);x1=Math.max(x1,a[0]/sc);y0=Math.min(y0,a[1]/sc);y1=Math.max(y1,a[1]/sc);});});
 return [x0,y0,x1,y1].map(v=>+v.toFixed(1));}"""
def ov(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
R = {}
try:
  with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1100, 'height': 900}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_function('window.__intro && __intro.info().state=="idle"', timeout=20000)
    DUR = pg.evaluate('CharoIntroCast.duration'); SL = pg.evaluate('CharoIntroCast.slow')
    ids = ['chumdani', 'giltong', 'tira', 'tarotaro', 'charocharo', 'doroduck']
    # 1) 시점별 실제 픽셀 검사: 캐릭터마다 따로 1000×600에 그려 보이는 픽셀로 잘림·겹침 판단(투명 여백 제외)
    PIX = """(T)=>{const CP=CharoPet,I=__intro; I.seek(T); const sc0=Math.min(document.getElementById('cv').width/1000,document.getElementById('cv').height/600);
     const out={}; const masks={};
     I.cast.forEach(c=>{const L=I.info().last[c.id]; const cv=document.createElement('canvas'); cv.width=1000; cv.height=600; const x=cv.getContext('2d');
       const v=L.view.map((a,i)=>a/sc0); CP.render(x,c.P,L.fp,CP.worldMatrices(c.P,L.fp),v);
       const d=x.getImageData(0,0,1000,600).data; let x0=1e9,y0=1e9,x1=-1,y1=-1; const m=new Uint8Array(1000*600);
       for(let j=0;j<600;j++)for(let i=0;i<1000;i++){if(d[(j*1000+i)*4+3]>40){m[j*1000+i]=1;if(i<x0)x0=i;if(i>x1)x1=i;if(j<y0)y0=j;if(j>y1)y1=j;}}
       // 그림이 캔버스 밖으로 나갔는지: 같은 그림을 여백 300px 큰 캔버스에 그려 비교
       const cb=document.createElement('canvas'); cb.width=1600; cb.height=1200; const xb=cb.getContext('2d'); const vb=v.slice(); vb[4]+=300; vb[5]+=300;
       CP.render(xb,c.P,L.fp,CP.worldMatrices(c.P,L.fp),vb); const db=xb.getImageData(0,0,1600,1200).data; let inside=0,all=0;
       for(let k=3;k<db.length;k+=16){if(db[k]>40){all++; const px=(k>>2)%1600-300, py=Math.floor((k>>2)/1600)-300; if(px>=0&&px<1000&&py>=0&&py<600) inside++;}}
       masks[c.id]=m; out[c.id]={box:[x0,y0,x1,y1], outside:all-inside};});
     const cm=masks.charocharo; const res={T:T,clip:{},face:{},text:0};
     I.cast.forEach(c=>{ if(out[c.id].outside>0) res.clip[c.id]=out[c.id].outside; if(c.id==='charocharo') return; if(c.id==='chumdani') return;   // 첨다니는 일부러 차로차로 뒤(따로 비율 계산)
       const b=out[c.id].box, fy=b[1]+(b[3]-b[1])*0.45, m=masks[c.id]; let n=0;
       for(let j=b[1];j<=fy;j++)for(let i=b[0];i<=b[2];i++){const k=j*1000+i; if(m[k]&&cm[k]) n++;} const ord=I.info().last.__order; if(n && ord.indexOf('charocharo')>ord.indexOf(c.id)) res.face[c.id]=n; });   // 차로차로가 그 친구보다 앞에 그려질 때만 '가림'
     const W=__fx.boxes().title.map(Math.round); res.title={};
     if(__fx.active(T)) I.cast.forEach(c=>{const b=out[c.id].box, fy=b[1]+(b[3]-b[1])*0.45, m=masks[c.id]; let n=0;
       for(let j=Math.max(b[1],W[1]);j<=Math.min(fy,W[3]);j++)for(let i=Math.max(b[0],W[0]);i<=Math.min(b[2],W[2]);i++) if(m[j*1000+i]) n++; if(n) res.title[c.id]=n;});
     // 첨다니(차로차로 뒤에 자리)의 얼굴 쪽(위 45%)이 차로차로에 가려진 비율
     {const b=out.chumdani.box, fy=b[1]+(b[3]-b[1])*0.45, m=masks.chumdani; let a=0,h=0; for(let j=Math.max(0,b[1]);j<=fy;j++)for(let i=Math.max(0,b[0]);i<=b[2];i++){const k=j*1000+i; if(m[k]){a++; if(cm[k]) h++;}} res.chumFaceHidden=a?h/a:0;}
     res.charoBox=out.charocharo.box; return res;}"""
    clip, text_hit, face_hit, prevc, maxjump, chum = [], [], [], None, 0, []
    t = 0.0
    while t <= DUR + 1e-4:
        pg.evaluate(f'__intro.seek({t})'); pg.wait_for_timeout(30)
        r = pg.evaluate(PIX, t)
        if r['clip']: clip.append((round(t, 2), r['clip']))
        for k, n in r['title'].items(): text_hit.append((round(t, 2), k, n))
        for k, n in r['face'].items(): face_hit.append((round(t, 2), k, n))
        if SL[0] <= t <= SL[1]: chum.append(r['chumFaceHidden'])
        c = r['charoBox']
        if prevc and t > 5.1: maxjump = max(maxjump, max(abs(a - b_) for a, b_ in zip(c, prevc)))
        prevc = c; t = round(t + 0.05, 2)
    R['clipped_pixels_outside_screen'] = clip[:8] or 'none'; R['title_over_character_faces_px'] = text_hit[:6] or 'none'
    R['charo_over_friend_face_px'] = (face_hit[:8] + [('총 프레임', len(face_hit))]) if face_hit else 'none'
    R['chumdani_face_hidden_by_charo_in_slow'] = dict(mean=round(sum(chum) / len(chum), 3), max=round(max(chum), 3))
    # 효과가 슬로모션 밖에 남지 않는지: 효과만 따로 그려 픽셀 수
    FXPIX = """(T)=>{const k=document.createElement('canvas');k.width=1000;k.height=600;const x=k.getContext('2d');__fx.drawBack(x,T);__fx.drawFront(x,T);
      const d=x.getImageData(0,0,1000,600).data;let n=0;for(let i=3;i<d.length;i+=4) if(d[i]>8) n++; return n;}"""
    R['fx_pixels_outside_slow'] = {str(t): pg.evaluate(FXPIX, t) for t in (0.5, SL[0] - 0.01, SL[1] + 0.01, 4.5, DUR)}
    R['fx_pixels_inside_slow'] = {str(t): pg.evaluate(FXPIX, t) for t in (SL[0] + 0.3, SL[0] + 1.0)}
    R['lineup_max_step_px_per_0.05s'] = round(maxjump, 1)
    # 2) 정상 종료 vs 건너뛰기: 끝난 뒤 위치·자세가 같은지
    def snap():
        return pg.evaluate("(()=>{const L=__intro.info().last,o={};for(const k in L){o[k]={v:L[k].view.map(x=>+x.toFixed(3)),f:Object.fromEntries(Object.entries(L[k].fp).map(([a,b])=>[a,[+b.x.toFixed(2),+b.y.toFixed(2),+b.rot.toFixed(2),+b.sx.toFixed(4),+b.sy.toFixed(4),+b.op.toFixed(2),b.img]]))}};return o})()")
    ES = "(()=>{const L=__intro.endState(),o={};for(const k in L){o[k]={v:L[k].view.map(x=>+x.toFixed(3)),f:Object.fromEntries(Object.entries(L[k].fp).map(([a,b])=>[a,[+b.x.toFixed(2),+b.y.toFixed(2),+b.rot.toFixed(2),+b.sx.toFixed(4),+b.sy.toFixed(4),+b.op.toFixed(2),b.img]]))}};return o})()"
    pg.evaluate('__intro.start()'); pg.wait_for_function('__intro.info().state=="wait"', timeout=12000)
    e1 = pg.evaluate(ES)
    pg.evaluate('__intro.start()'); pg.wait_for_timeout(1500); pg.evaluate('__intro.skip()'); pg.wait_for_timeout(30); e2 = pg.evaluate(ES)
    diff = []
    for k in e1:
        if e1[k]['v'] != e2[k]['v']: diff.append((k, 'view'))
        for part in e1[k]['f']:
            a, b_ = e1[k]['f'][part], e2[k]['f'][part]
            if any(abs(x - y) > 0.6 for x, y in zip(a[:6], b_[:6])) or a[6] != b_[6]: diff.append((k, part, a, b_))
    R['skip_equals_end'] = diff[:5] or 'same'
    # 3) 끝 → 대기 이어짐: 끝 직전·직후 차로차로 상자 차이
    pg.evaluate(f'__intro.seek({DUR-0.01})'); pg.wait_for_timeout(30); a = pg.evaluate(BOX, 'charocharo')
    pg.evaluate('__intro.skip()'); pg.wait_for_timeout(30); b2 = pg.evaluate(BOX, 'charocharo')
    R['end_to_wait_box_delta'] = round(max(abs(x - y) for x, y in zip(a, b2)), 2)
    # 4) 창 크기 변경: 논리 좌표 그대로인지
    pg.set_viewport_size({'width': 700, 'height': 900}); pg.wait_for_timeout(200); b3 = pg.evaluate(BOX, 'charocharo')
    R['resize_box_delta_logical'] = round(max(abs(x - y) for x, y in zip(b2, b3)), 2)
    # 5) 인트로 중 마우스·키보드·클릭이 동작을 바꾸지 않음
    pg.evaluate('__intro.seek(3.0)'); pg.wait_for_timeout(40); s1 = pg.evaluate(BOX, 'charocharo')
    pg.mouse.move(100, 100); pg.mouse.click(300, 300); pg.keyboard.type('abc'); pg.mouse.move(600, 400); pg.wait_for_timeout(300); s2 = pg.evaluate(BOX, 'charocharo')
    R['input_does_not_change_pose'] = s1 == s2
    R['pet_engine_mounted'] = pg.evaluate('!!(window.CharoPet && CharoPet.site)'); R['scripts'] = pg.evaluate("[...document.scripts].map(s=>s.src.split('/').pop())")
    # 6) 모션 줄이기
    pg.evaluate('__intro.setReduce(true); __intro.seek(3.0)'); pg.wait_for_timeout(40)
    f = pg.evaluate("(()=>{const f=__intro.info().last.charocharo.fp;return [f.body.y,f.body.rot,f.eyeL.img,f.mouth.img]})()")
    R['reduce_charo_at_3s'] = f
    pg.evaluate('__intro.skip()'); pg.wait_for_timeout(30); r_end = pg.evaluate(BOX, 'charocharo'); pg.evaluate('__intro.setReduce(false)')
    R['reduce_final_box_delta'] = round(max(abs(x - y) for x, y in zip(r_end, b3)), 2)
    # 7) 휴대폰 폭
    m = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2); m.goto(URL); m.wait_for_function('window.__intro && __intro.info().state=="idle"', timeout=20000)
    R['mobile_scroll'] = m.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]')
    m.evaluate('__intro.skip()'); m.wait_for_timeout(50); R['mobile_final_box_delta'] = round(max(abs(x - y) for x, y in zip(m.evaluate(BOX, 'charocharo'), b3)), 2)
    m.screenshot(path='/tmp/claude-0/ci/mobile_intro.png')
    # 8) 그림 하나가 깨지면 시작하지 않음
    x = b.new_page(); x.goto(URL); x.wait_for_function('window.__intro && __intro.info().state!="loading"', timeout=20000)
    x.evaluate("""(async()=>{const p=await (await fetch('../charo-pet.json')).json(); const k=Object.keys(p.assets)[0]; p.assets[k]='data:image/png;base64,AAAA';
      const cv=document.createElement('canvas'); cv.id='cv2'; cv.style.cssText='width:300px;height:180px'; document.body.appendChild(cv);
      window.__bad=CharoIntro.create({canvas:cv,duration:6.7,cast:[{id:'charocharo',data:p,anchor:[200,370],stageH:231,idle:'c_breath',segs:[{t0:0,t1:6.7,clip:'i_charo'}],place:[[0,500,500,150]]}]});
      try{await __bad.ready}catch(e){} })()""")
    x.wait_for_timeout(800); R['broken_image'] = x.evaluate('__bad.info().state + " / " + __bad.info().error')
    R['broken_canvas_blank'] = x.evaluate("(()=>{const c=document.getElementById('cv2');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;for(let i=3;i<d.length;i+=4) if(d[i]) return false;return true})()")
    R['errors'] = errs
    b.close()
finally:
    srv.terminate()
print(json.dumps(R, ensure_ascii=False, indent=1))
