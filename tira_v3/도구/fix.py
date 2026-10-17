# 무팔 티라 검수본 보정: 원본 PNG는 그대로 두고 work/fixed/에 1254 좌표로 배치·보정한 결과를 저장
import sys; sys.path.insert(0,'/home/claude/tira3/work'); from rig import *
OUT='/home/claude/tira3/work/fixed/'; os.makedirs(OUT,exist_ok=True)
LOG={}
def keycols(p):
    a=p[...,3]>=250; c=p[...,:3].astype(float); lum=c.mean(2)
    brown=a&(abs(c[...,2]-200)<40)&(abs(c[...,1]-158)<35)&(c[...,0]<140)
    dark=a&(lum<95); white=a&(lum>225)
    return [np.median(c[m],0) for m in (dark,brown,white)]
BODY=placed('01'); KB=keycols(BODY)
def recolor(p,K):
    c=p[...,:3].astype(float); out=c.copy()
    for ch in range(3):
        xs=[K[0][ch],K[1][ch],K[2][ch]]; ys=[KB[0][ch],KB[1][ch],KB[2][ch]]
        o=np.argsort(xs); xs=np.array(xs)[o]; ys=np.array(ys)[o]
        out[...,ch]=np.interp(c[...,ch],np.r_[0,xs,255],np.r_[0 if ys[0]>xs[0] else 0,ys,255])
    q=p.copy(); q[...,:3]=np.clip(out,0,255).astype(np.uint8); return q
def complete_spike(p):
    # 머리 아래 오른쪽에서 잘린 뼈깃: 위의 온전한 뼈깃(흰 판+자기 윤곽)만 오려 같은 간격 아래로 옮겨 잘린 끝을 닫음
    white=(p[...,3]>200)&(p[...,:3].min(2)>200)
    n,lab,st,_=cv2.connectedComponentsWithStats(white.astype(np.uint8))
    ids=[i for i in range(1,n) if st[i][4]>2000 and st[i][0]>820]
    ids.sort(key=lambda i:st[i][1]); fi,ci=ids[-2],ids[-1]; full,cut=st[fi],st[ci]
    assert cut[1]+cut[3]>=650
    dy=int(cut[1]-full[1]); R=646
    xs_c=np.where(lab[R]==ci)[0]; xs_f=np.where(lab[R-dy]==fi)[0]
    dx=int(round(((xs_c.min()+xs_c.max())-(xs_f.min()+xs_f.max()))/2))
    fw=(lab==fi).astype(np.uint8)
    ring=cv2.dilate(fw,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(37,37)))>0
    lum=p[...,:3].mean(2); dark=(lum<130)&(p[...,3]>0)
    yy=np.arange(N)[:,None]; xx=np.arange(N)[None,:]
    keep=(fw>0)|(ring&dark&(xx>=full[0]-2))
    src=p.copy(); src[~keep,3]=0
    sh=cv2.warpAffine(src,np.float32([[1,0,dx],[0,1,dy]]),(N,N),flags=cv2.INTER_NEAREST,borderValue=(0,0,0,0))
    ramp=np.clip((yy-648)/8,0,1)
    sa=sh[...,3:4].astype(float)/255*ramp[...,None]
    q=p.astype(float); q[...,:3]=sh[...,:3]*sa+q[...,:3]*(1-sa); q[...,3:4]=np.maximum(q[...,3:4],sa*255)
    return q.astype(np.uint8),dict(full=list(map(int,full[:4])),cut=list(map(int,cut[:4])),shift=[dx,dy])
def feather_bottom(p):
    # 머리 아래 끝 가로선 방지: 652~657행의 갈색 안쪽만 투명도를 서서히 낮춤(색을 맞췄으므로 몸통과 이어짐)
    q=p.copy(); c=q[...,:3].astype(int)
    brown=(abs(c[...,2]-200)<45)&(abs(c[...,1]-158)<40)&(c[...,0]<145)
    for y in range(646,N):
        k=max(0.0,1-(y-646)/10)
        row=brown[y]; q[y,row,3]=(q[y,row,3]*k).astype(np.uint8)
    return q
for h in ['02','03','04','05','06']:
    p=placed(h); K=keycols(p); q=recolor(p,K); info=dict(colors_before=[list(map(round,k)) for k in K])
    if h in ('02','03','06'): q,si=complete_spike(q); info['spike']=si
    q=feather_bottom(q); cv2.imwrite(OUT+'head'+h+'.png',q); LOG['head'+h]=info
# 몸통 윗부분(618~655) 윤곽선 끝이 머리 윤곽선보다 바깥으로 튀어나와 계단이 보임 → 위로 갈수록 안쪽으로 다듬음
B2=BODY.copy()
for y in range(612,656):
    k=(y-612)/(655-612); L=345+(331-345)*k; R=862+(877-862)*k
    xs=np.arange(N); a=np.clip(np.minimum(xs-L+1,R-xs+1),0,1)
    a[xs>890]=1
    B2[y,:,3]=(B2[y,:,3]*a).astype(np.uint8)
cv2.imwrite(OUT+'body.png',B2)
for i,n in [('07','footL'),('08','footR'),('09','tail')]: cv2.imwrite(OUT+n+'.png',placed(i))
# 목 접합 띠: 몸통 윤곽선을 620→652 사이 점점 진하게 머리 위에 덮어, 머리 윤곽선(얇음)→몸통 윤곽선(두꺼움)으로 이어 줌
c=BODY.copy(); yy=np.arange(N)[:,None]; xx=np.arange(N)[None,:]
lum=c[...,:3].mean(2); dark=(lum<120)&(c[...,3]>0)
w=np.clip((yy-620)/(652-620),0,1)*((yy<=660))
zone=((xx<385)|((xx>828)&(xx<884)))
c[...,3]=(c[...,3]*w*dark*zone).astype(np.uint8)
cv2.imwrite(OUT+'collar.png',c)
# 불꽃: 각 불꽃의 '입에 붙는 뿌리'를 머리 02/03의 fireRoot에 맞춰 1254 좌표에 배치(p_out = fireRoot + s·(p − root))
FR=np.array(J['02']['fireRoot_source'])*J['02']['scale']+[J['02']['translate_x'],J['02']['translate_y']]
FIRES={'fire12':dict(src=FILES['12'],s=J['12']['scale'],root=J['12']['source_flame_root']),
       # 13번 교체(2026-10-17): 굵은 만화 불꽃. 이전 13번 값(0.68306, 423,563.5)은 쓰지 않음
       'fire13b':dict(src='/home/claude/tira3/src/파츠_교체/티라_무팔_13_불꽃_크게.png',s=0.307,root=[1175,638])}
INSET=8   # 뿌리를 입 안쪽으로 8px(1254 좌표, 실제 화면 약 1.5px) 겹침. fireRoot 값 자체는 그대로
for n,f in FIRES.items():
    im=cv2.imread(f['src'],cv2.IMREAD_UNCHANGED); s_=f['s']; t=FR+[INSET,0]-s_*np.array(f['root'],float)
    a=im.astype(np.float32); al=a[...,3:4]/255; pm=np.concatenate([a[...,:3]*al,a[...,3:4]],2)
    w=cv2.warpAffine(pm,np.array([[s_,0,t[0]],[0,s_,t[1]]]),(N,N),flags=cv2.INTER_AREA,borderValue=(0,0,0,0))
    A=w[...,3:4]; rgb=np.where(A>0.5,w[...,:3]/np.maximum(A,1e-3)*255,0)
    out=np.clip(np.concatenate([rgb,A],2),0,255).astype(np.uint8); cv2.imwrite(OUT+n+'.png',out)
    ys,xs=np.where(out[...,3]>127); LOG[n]=dict(inset_px=INSET,scale=s_,source_root=f['root'],fireRoot=[round(float(v),2) for v in FR],visible_bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())])
# 팻말: 물림점(꼭지 상단)이 정면물기 머리(06)의 입 물림점에 오도록 배치. 2026-10-17: 사용자 요청으로 원래 배율의 1.25배
SIGN_SCALE=1.25
G6=J['06']['mouthGrip_after_transform']
for i,n in (('14','sign14'),('11','sign11')):
    cv2.imwrite(OUT+n+'.png',placed(i,sign_M(i,G6,J[i].get('scale',1)*SIGN_SCALE)))
    LOG[n]=dict(scale=round(J[i].get('scale',1)*SIGN_SCALE,6),base_scale=J[i].get('scale',1),x=SIGN_SCALE,bite_anchor=J[i]['source_bite_anchor'],mouthGrip06=G6)
LOG['body_colors']=[list(map(round,k)) for k in KB]
json.dump(LOG,open(OUT+'fixlog.json','w'),indent=1)
print(json.dumps(LOG))
