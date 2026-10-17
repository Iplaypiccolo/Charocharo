import cv2, numpy as np, sys
P=sys.argv[1] if len(sys.argv)>1 else 'src/parts/도로덕_'; OUT=sys.argv[2] if len(sys.argv)>2 else 'work/raw'
ORDER=['화면왼날개','화면오른날개','화면왼발','화면오른발','몸통바탕','눈_기본','부리_붉은타원']
c=np.zeros((1254,1254,4),float)
for n in ORDER:
    im=cv2.imread(P+n+'.png',cv2.IMREAD_UNCHANGED).astype(float); a=im[...,3:4]/255
    c[...,:3]=im[...,:3]*a+c[...,:3]*(1-a); c[...,3:4]=255*a+c[...,3:4]*(1-a)
f=(c[...,:3]*(c[...,3:4]/255)+255*(1-c[...,3:4]/255)).astype(np.uint8)
ref=cv2.imread('src/reference/도로덕_기본정면.png',cv2.IMREAD_UNCHANGED).astype(float)
rf=(ref[...,:3]*(ref[...,3:4]/255)+255*(1-ref[...,3:4]/255)).astype(np.uint8)
def ink(img): return (img.max(2)<90)
d=np.full((1254,1254,3),255,np.uint8); d[ink(rf)]=(0,180,0); d[ink(f)]=(0,0,230); d[ink(rf)&ink(f)]=(40,40,40)
cv2.imwrite(OUT+'_overlay.png',cv2.resize(np.hstack([f,rf,d])[150:1120],None,fx=0.5,fy=0.5,interpolation=cv2.INTER_AREA)); cv2.imwrite(OUT+'_full.png',f)
