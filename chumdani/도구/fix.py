# 검수본: 원본은 그대로, work/fixed 에 보정본. 와이파이는 원래 무늬 크기·중심에 맞추고, 강함을 점/안쪽/바깥 3구역으로 나눔
import cv2, numpy as np, json, os
N=1254; O='work/fixed/'; os.makedirs(O,exist_ok=True)
def S(s,cx,cy,dx=0,dy=0): return np.array([[s,0,cx-s*cx+dx],[0,s,cy-s*cy+dy]],float)
def warp(im,M): return cv2.warpAffine(im,M,(N,N),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
def ld(p): return cv2.imread(p,cv2.IMREAD_UNCHANGED)
log={}
def put(name,im,note): cv2.imwrite(O+name+'.png',im); log[name]=note
put('차체바탕', ld('wifi/첨다니_차체바탕_와이파이분리.png'), ['교체용 차체(와이파이 분리) 그대로 사용. 기존 차체와 윤곽 겹침 95%, 위치 보정 필요 없음'])
put('차체바탕_구', ld('src/첨다니_차체바탕.png'), ['비교용(조립에는 사용 안 함)'])
put('안테나', warp(ld('src/첨다니_안테나.png'),S(0.62,626,334,0,-60)), ['노란 공 크기를 기준형에 맞춰 62%(공 중심 기준), 위로 60px'])
put('화면왼귀', ld('src/첨다니_화면왼귀.png'), [])
put('화면오른귀', warp(ld('src/첨다니_화면오른귀.png'),S(0.80,992.5,430,12,-24)), ['왼귀보다 커서 80%, 오른쪽 12px·위 24px'])
put('화면왼바퀴', warp(ld('src/첨다니_화면왼바퀴.png'),S(1.02,412.5,994.5,-4,0)), ['102%, 왼쪽 4px'])
put('화면오른바퀴', ld('src/첨다니_화면오른바퀴.png'), [])
put('눈_기본', ld('src/첨다니_눈_기본.png'), [])
# 눈썹: 한 장에 두 개 → 각각 50%로 줄여 기준형 자리로
br=ld('src/첨다니_눈썹_기본.png'); L=br.copy(); L[:,627:]=0; R=br.copy(); R[:,:627]=0
L=warp(L,S(0.5,468,531,9,-14)); R=warp(R,S(0.5,796,531,-23,-14))
a=L[...,3:4]/255.; br2=(R.astype(float)); br2[...,:3]=L[...,:3]*a+br2[...,:3]*(1-a); br2[...,3:4]=np.maximum(L[...,3:4],R[...,3:4])
put('눈썹_기본', br2.astype(np.uint8), ['두 눈썹을 각각 50%로 줄여 기준형 위치(477,517)/(773,517)로'])
# 질끈 눈: 가로 중심을 기본 눈에 맞춤
ey=ld('src/첨다니_눈_질끈웃음.png'); L=ey.copy(); L[:,627:]=0; R=ey.copy(); R[:,:627]=0
L=warp(L,S(1,0,0,-6,-3)); R=warp(R,S(1,0,0,12,-3))
a=L[...,3:4]/255.; e2=R.astype(float); e2[...,:3]=L[...,:3]*a+e2[...,:3]*(1-a); e2[...,3:4]=np.maximum(L[...,3:4],R[...,3:4])
put('눈_질끈웃음', e2.astype(np.uint8), ['왼쪽 -6px·오른쪽 +12px·위 3px (기본 눈과 가로·세로 중심 맞춤)'])
# 와이파이: 원래 무늬(555~700, 821~927)에 맞춤 → 75%, 중심 (626.5,887)→(627.5,874)
WM=S(0.75,626.5,887,1,-13)
weak=warp(ld('wifi/첨다니_와이파이_신호약함.png'),WM); strong=warp(ld('wifi/첨다니_와이파이_신호강함.png'),WM)
put('와이파이_약함', weak, ['원래 무늬 크기에 맞춰 75%, 위로 13px·오른쪽 1px (강함과 같은 보정)'])
n,lab,st,cen=cv2.connectedComponentsWithStats((strong[...,3]>20).astype(np.uint8))
comps=sorted([i for i in range(1,n) if st[i][4]>30],key=lambda i:-cen[i][1])   # 아래부터: 점, 안쪽, 바깥
names=['와이파이_강함_점','와이파이_강함_안쪽','와이파이_강함_바깥']
assert len(comps)==3, len(comps)
for nm,i in zip(names,comps):
    m=cv2.dilate((lab==i).astype(np.uint8),np.ones((5,5),np.uint8))>0; im=strong.copy(); im[~m]=0; put(nm,im,['강함 레이어를 이 구역만 남겨 나눔(같은 보정)'])
json.dump(log,open(O+'_fix_log.json','w'),ensure_ascii=False,indent=1); print(json.dumps(log,ensure_ascii=False,indent=0)[:1500])
