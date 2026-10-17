import cv2, numpy as np, json
P='src/parts/도로덕_'
ref=cv2.imread('src/reference/도로덕_기본정면.png',cv2.IMREAD_UNCHANGED)
body=cv2.imread(P+'몸통바탕.png',cv2.IMREAD_UNCHANGED)
bodyM=cv2.erode((body[...,3]>128).astype(np.uint8),np.ones((5,5),np.uint8))   # 몸통이 덮는 곳(살짝 안쪽)
refA=((ref[...,3]>128)&(bodyM==0)).astype(np.uint8)       # 몸통 밖으로 보이는 참고 그림 영역(날개·발)
res={}
for n in ['화면왼날개','화면오른날개','화면왼발','화면오른발','눈_기본','부리_붉은타원']:
    im=cv2.imread(P+n+'.png',cv2.IMREAD_UNCHANGED); A=(im[...,3]>128).astype(np.uint8)
    face = n.startswith('눈') or n.startswith('부리')
    R = (ref[...,3]>128).astype(np.uint8) if not face else None
    if face:  # 얼굴 파츠는 참고 그림의 해당 색 영역과 비교
        if n.startswith('눈'): R=((ref[...,:3].max(2)<90)&(ref[...,3]>128)).astype(np.uint8); R[:400]=0; R[520:]=0
        else: R=((ref[...,2]>200)&(ref[...,1]<110)&(ref[...,3]>128)).astype(np.uint8)
    else: R=refA
    ys,xs=np.where(A); cx,cy=(xs.min()+xs.max())/2,(ys.min()+ys.max())/2
    x0,x1,y0,y1=max(0,xs.min()-80),min(1254,xs.max()+80),max(0,ys.min()-80),min(1254,ys.max()+80)
    best=None
    for s in np.arange(0.86,1.121,0.02):
        M0=np.array([[s,0,cx-s*cx],[0,s,cy-s*cy]],float); As=cv2.warpAffine(A,M0,(1254,1254),flags=cv2.INTER_NEAREST)
        for dy in range(-30,31,2):
            for dx in range(-30,31,2):
                J=np.roll(np.roll(As,dy,0),dx,1)
                if not face: J=J&(1-bodyM)
                Jc=J[y0:y1,x0:x1]; Rc=R[y0:y1,x0:x1]
                iou=(Jc&Rc).sum()/max(1,(Jc|Rc).sum())
                if best is None or iou>best[0]: best=(iou,round(float(s),2),dx,dy)
    J0=A if face else A&(1-bodyM); raw=(J0[y0:y1,x0:x1]&R[y0:y1,x0:x1]).sum()/max(1,(J0[y0:y1,x0:x1]|R[y0:y1,x0:x1]).sum())
    res[n]=dict(raw_iou=round(float(raw),3),best_iou=round(float(best[0]),3),scale=best[1],dx=best[2],dy=best[3],center=[float(cx),float(cy)])
    print(n,res[n])
json.dump(res,open('work/reg.json','w'),ensure_ascii=False,indent=1)
