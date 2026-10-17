import cv2, numpy as np, json
P='src/첨다니_'; N=1254
ref=cv2.imread('src/참고/첨다니_조립기준형.png',cv2.IMREAD_UNCHANGED)
body=cv2.imread(P+'차체바탕.png',cv2.IMREAD_UNCHANGED); bodyM=cv2.erode((body[...,3]>128).astype(np.uint8),np.ones((5,5),np.uint8))
refA=(ref[...,3]>128).astype(np.uint8); dark=((ref[...,:3].max(2)<100)&(ref[...,3]>128)).astype(np.uint8)
res={}
for n,sr in [('안테나',(0.5,0.9)),('화면오른귀',(0.84,1.06)),('화면왼귀',(0.9,1.1)),('눈썹_기본',(0.6,1.0)),('눈_기본',(0.9,1.1)),('화면왼바퀴',(0.9,1.12)),('화면오른바퀴',(0.9,1.12))]:
    im=cv2.imread(P+n+'.png',cv2.IMREAD_UNCHANGED); A=(im[...,3]>128).astype(np.uint8)
    face=n.startswith('눈')
    if face:
        R=dark.copy(); 
        if n.startswith('눈썹'): R[:470]=0; R[575:]=0
        else: R[:570]=0; R[680:]=0
        R=R&bodyM  # 차체 안쪽 어두운 것(기둥 포함)…기둥 제외
        R[:, 615:640]=0
    else: R=refA&(1-bodyM)
    ys,xs=np.where(A); cx,cy=(xs.min()+xs.max())/2,(ys.min()+ys.max())/2
    x0,x1,y0,y1=max(0,xs.min()-120),min(N,xs.max()+120),max(0,ys.min()-160),min(N,ys.max()+120)
    best=None
    for s in np.arange(sr[0],sr[1]+1e-6,0.02):
        M0=np.array([[s,0,cx-s*cx],[0,s,cy-s*cy]],float); As=cv2.warpAffine(A,M0,(N,N),flags=cv2.INTER_NEAREST)
        for dy in range(-80,41,4):
            for dx in range(-40,41,4):
                J=np.roll(np.roll(As,dy,0),dx,1)
                if not face: J=J&(1-bodyM)
                Jc=J[y0:y1,x0:x1]; Rc=R[y0:y1,x0:x1]; iou=(Jc&Rc).sum()/max(1,(Jc|Rc).sum())
                if best is None or iou>best[0]: best=(iou,round(float(s),2),dx,dy)
    res[n]=dict(best_iou=round(float(best[0]),3),scale=best[1],dx=best[2],dy=best[3],center=[float(cx),float(cy)]); print(n,res[n])
json.dump(res,open('work/reg.json','w'),ensure_ascii=False,indent=1)
