# 정면물기(06) 입 앞가림: 이빨 + 윗입 부분 + 아랫입술 테두리만 머리 그림에서 오려 팻말 꼭지 위에 덮음
import sys; sys.path.insert(0,'/home/claude/tira3/work'); from rig import *
F='/home/claude/tira3/work/fixed/'
HEAD=sys.argv[2] if len(sys.argv)>2 else '06'
h=cv2.imread(F+'head'+HEAD+'.png',-1); lum=h[...,:3].mean(2); a=h[...,3]>128
reg=np.zeros(h.shape[:2],bool); R={'06':(540,640,440,780),'04':(520,660,560,860)}[HEAD]; reg[R[0]:R[1],R[2]:R[3]]=True
dark=a&(lum<120)&reg
n,lab,st,_=cv2.connectedComponentsWithStats(dark.astype(np.uint8)); i=1+np.argmax(st[1:,4])
band=(lab==i).astype(np.uint8); filled=band.copy()
cnts,_=cv2.findContours(band,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); cv2.drawContours(filled,cnts,-1,1,-1)
filled=filled>0; teeth=filled&(lum>200)
RIM=int(sys.argv[1]) if len(sys.argv)>1 else 8
m=np.zeros_like(filled)
for x in range(R[2],R[3]):
    col=np.where(filled[:,x])[0]
    if not len(col): continue
    t=np.where(teeth[:,x])[0]; tb=t.max()+2 if len(t) else col.min()+22
    bot=col.max()
    m[col.min():tb+1,x]=True; m[max(col.min(),bot-RIM):bot+1,x]=True
m=m&filled
m=cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8))>0
out=h.copy(); out[...,3]=(h[...,3]*m).astype(np.uint8)
cv2.imwrite(F+'mask'+HEAD+'.png',out)
