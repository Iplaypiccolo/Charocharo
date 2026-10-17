import cv2, numpy as np, json
P='src/parts/티라_'; N=1254
ref=cv2.imread('src/reference/티라_기본정면.png',cv2.IMREAD_UNCHANGED)
BODY_M=np.array([[0.88,0,640-0.88*640],[0,0.88,1100-0.88*1100-65]],float)
body=cv2.warpAffine(cv2.imread(P+'몸통바탕.png',cv2.IMREAD_UNCHANGED),BODY_M,(N,N),borderValue=(0,0,0,0))
cv2.imwrite('work/body_interim.png',body)
bodyM=cv2.erode((body[...,3]>128).astype(np.uint8),np.ones((5,5),np.uint8))
refA=(ref[...,3]>128).astype(np.uint8)
dark=((ref[...,:3].max(2)<90)&(ref[...,3]>128)).astype(np.uint8)
res={}
for n in ['꼬리','화면왼팔','화면오른팔','화면왼발','화면오른발','눈_기본','입_기본이빨']:
    im=cv2.imread(P+n+'.png',cv2.IMREAD_UNCHANGED); A=(im[...,3]>128).astype(np.uint8)
    face=n.startswith('눈') or n.startswith('입')
    if n.startswith('눈'): R=dark.copy(); R[:380]=0; R[500:]=0
    elif n.startswith('입'): R=cv2.morphologyEx(dark,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8)); R[:480]=0; R[620:]=0; A=cv2.morphologyEx(A,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
    else: R=refA&(1-bodyM)
    ys,xs=np.where(A); cx,cy=(xs.min()+xs.max())/2,(ys.min()+ys.max())/2
    x0,x1,y0,y1=max(0,xs.min()-120),min(N,xs.max()+120),max(0,ys.min()-160),min(N,ys.max()+120)
    best=None
    for s in np.arange(0.76,1.13,0.03):
        M0=np.array([[s,0,cx-s*cx],[0,s,cy-s*cy]],float); As=cv2.warpAffine(A,M0,(N,N),flags=cv2.INTER_NEAREST)
        for dy in range(-120,61,4):
            for dx in range(-60,61,4):
                J=np.roll(np.roll(As,dy,0),dx,1)
                if not face: J=J&(1-bodyM)
                Jc=J[y0:y1,x0:x1]; Rc=R[y0:y1,x0:x1]; iou=(Jc&Rc).sum()/max(1,(Jc|Rc).sum())
                if best is None or iou>best[0]: best=(iou,round(float(s),2),dx,dy)
    res[n]=dict(best_iou=round(float(best[0]),3),scale=best[1],dx=best[2],dy=best[3],center=[float(cx),float(cy)]); print(n,res[n])
json.dump(res,open('work/reg.json','w'),ensure_ascii=False,indent=1)
