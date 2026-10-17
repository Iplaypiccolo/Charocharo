import cv2, numpy as np, json
P='src/parts/길통이_'
ref=cv2.imread('src/reference/길통이_기본정면.png',cv2.IMREAD_UNCHANGED)
def ink(img,a): return ((img[...,0]<130)&(img[...,1]<100)&(img[...,2]<70)&(a>128)).astype(np.uint8)
RI=ink(ref,ref[...,3]); RId=cv2.dilate(RI,np.ones((3,3),np.uint8))
res={}
for n in ['망토','화면왼다리','화면오른다리','화면왼팔','화면오른팔','몸통','얼굴바탕','눈_기본','눈썹','입_기본미소']:
    im=cv2.imread(P+n+'.png',cv2.IMREAD_UNCHANGED); I=ink(im,im[...,3])
    ys,xs=np.where(I); cx,cy=xs.mean(),ys.mean()
    best=None
    for s in [0.96,0.98,1.0,1.02,1.04]:
        M0=np.array([[s,0,cx-s*cx],[0,s,cy-s*cy]],float)
        Is=cv2.warpAffine(I,M0,(1254,1254),flags=cv2.INTER_NEAREST)
        for dy in range(-24,25,2):
            for dx in range(-24,25,2):
                Mt=np.float32([[1,0,dx],[0,1,dy]]); J=cv2.warpAffine(Is,Mt,(1254,1254),flags=cv2.INTER_NEAREST)
                sc=(J&RId).sum()/max(1,J.sum())
                if best is None or sc>best[0]: best=(sc,s,dx,dy)
    base=(I&RId).sum()/I.sum()
    res[n]=dict(raw=round(float(base),3),best=round(float(best[0]),3),scale=best[1],dx=best[2],dy=best[3])
    print(n,res[n])
json.dump(res,open('work/reg.json','w'),ensure_ascii=False,indent=1)
