import subprocess, time, json
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8798','-d','/tmp/claude-0/rvt3'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(0.6)
R={}
POSE="(()=>{const l=__eng.last; const r={}; for(const k of ['rig','sway','head','bite','tail','footL','footR','sign14']) r[k]=[+l[k].x.toFixed(2),+l[k].y.toFixed(2),+l[k].rot.toFixed(2),+l[k].sx.toFixed(3),+l[k].sy.toFixed(3)]; for(const k of ['sign11B','sign11F','sign14','mask','fire']) r['op_'+k]=+l[k].op.toFixed(2); r.head_img=l.headImg.img?l.headImg.img.img:0; return r})()"
def dev(o):
    bad=[]
    for k,v in o.items():
        if k.startswith('op_'):
            if v>0.01: bad.append((k,v))
            continue
        if k=='head_img':
            if v!=0: bad.append((k,v))
            continue
        x,y,rot,sx,sy=v; lim=4.5 if k=='tail' else 0.6
        if abs(x)>0.5 or abs(y)>1.0 or abs(rot)>lim or abs(sx-1)>0.03 or abs(sy-1)>0.03: bad.append((k,)+tuple(v))
    return bad
try:
  with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':900}); errs=[]
    pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8798/'); pg.wait_for_function('window.__gt && window.__eng && __eng.last',timeout=15000); time.sleep(0.5)
    st=lambda: pg.evaluate('window.__gt')
    R['idle']=dev(pg.evaluate(POSE))
    pg.click('#b_intro'); seq=[]; t0=time.time()
    while time.time()-t0<7.0:
        s=st(); k=(s['head'],s['sign'],s['fire'])
        if not seq or seq[-1][1:]!=k: seq.append((round(time.time()-t0,2),)+k)
        time.sleep(0.01)
    R['intro_seq']=seq
    time.sleep(0.8); R['end_intro']=dev(pg.evaluate(POSE))
    for at in (0.6,1.9,2.3,3.0):
        pg.click('#b_intro'); time.sleep(at); pg.click('#b_stop'); time.sleep(0.4); R['skip_%s'%at]=dev(pg.evaluate(POSE))
    pg.click('#b_intro'); time.sleep(2.2); s1=st()['sign']; pg.click('#b_intro'); time.sleep(0.25); s=st(); R['restart']=(s1,s['sign'],s['head'],s['fire'])
    pg.click('#b_stop'); time.sleep(0.4)
    for i in range(6): pg.click('#b_intro'); time.sleep(0.04)
    time.sleep(0.3); R['spam']=st()['clip']; pg.click('#b_stop'); time.sleep(0.4)
    for cid,d in (('t_run',1.45),('t_fetch',1.4),('t_welcome',4.15),('t_turn_slow',4.8),('t_fetch_zoom',3.21)):
        pg.click('#b_'+cid); time.sleep(d+0.6); R['end_'+cid]=dev(pg.evaluate(POSE))
    pg.check('#t_reduce'); pg.click('#b_intro'); hs=set(); fs=set(); ss=set(); t0=time.time()
    while time.time()-t0<3.0: s=st(); hs.add(s['head']); fs.add(s['fire']); ss.add(s['sign']); time.sleep(0.02)
    R['reduce']=dict(clip=st()['clip'],heads=sorted(hs),fire=sorted(fs),sign=sorted(ss)); pg.click('#b_stop'); time.sleep(0.4); R['reduce_skip']=dev(pg.evaluate(POSE)); pg.uncheck('#t_reduce')
    m=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2); m.goto('http://localhost:8798/'); m.wait_for_function('window.__gt',timeout=15000); time.sleep(0.4)
    R['mobile_scroll']=m.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]'); m.click('#b_intro'); time.sleep(2.9); R['mobile_sign']=m.evaluate('__gt.sign')
    m.screenshot(path='/home/claude/tira3/work/mobile.png')
    b.close()
finally: srv.terminate()
print(json.dumps(R,ensure_ascii=False)); print('errs',errs)
