import cv2,numpy as np,sys
P=sys.argv[1]; OUT=sys.argv[2]; BODY=sys.argv[3] if len(sys.argv)>3 else '차체바탕'
ORDER=['화면왼귀','화면오른귀','안테나','화면왼바퀴','화면오른바퀴',BODY]+(sys.argv[4].split(',') if len(sys.argv)>4 else [])+['눈썹_기본','눈_기본']
def ld(n):
    for d in (P,'wifi/'):
        im=cv2.imread(d+'첨다니_'+n+'.png',cv2.IMREAD_UNCHANGED)
        if im is None: im=cv2.imread(d+n+'.png',cv2.IMREAD_UNCHANGED)
        if im is not None: return im
c=np.zeros((1254,1254,4),float)
for n in ORDER:
    im=ld(n).astype(float); a=im[...,3:4]/255; c[...,:3]=im[...,:3]*a+c[...,:3]*(1-a); c[...,3:4]=255*a+c[...,3:4]*(1-a)
f=(c[...,:3]*(c[...,3:4]/255)+255*(1-c[...,3:4]/255)).astype(np.uint8)
r=cv2.imread('src/참고/첨다니_조립기준형.png',cv2.IMREAD_UNCHANGED).astype(float); rf=(r[...,:3]*(r[...,3:4]/255)+255*(1-r[...,3:4]/255)).astype(np.uint8)
ink=lambda im: im.max(2)<100
d=np.full((1254,1254,3),255,np.uint8); d[ink(rf)]=(0,180,0); d[ink(f)]=(0,0,230); d[ink(rf)&ink(f)]=(40,40,40)
cv2.imwrite(OUT+'_full.png',f); cv2.imwrite(OUT+'_overlay.png',cv2.resize(np.hstack([f,rf,d])[150:1100],None,fx=0.42,fy=0.42,interpolation=cv2.INTER_AREA))
