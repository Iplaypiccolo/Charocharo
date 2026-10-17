# 검수본: 원본(src/parts)은 그대로, work/fixed 에 보정본
import cv2, numpy as np, json, os
N=1254; O='work/fixed/'
def S(s,cx,cy,dx=0,dy=0,sy=None): sy=s if sy is None else sy; return np.array([[s,0,cx-s*cx+dx],[0,sy,cy-sy*cy+dy]],float)
FIX={
 '몸통바탕':('임시: 아래 가운데(640,1100) 기준 88%로 줄이고 위로 65px (모양·등 돌기 차이는 그림 수정 필요)', S(0.88,640,1100,0,-65)),
 '입_기본이빨':('위로 43px·왼쪽 15px, 96%', S(0.96,627,629,-15,-43)),
 '입_환영웃음':('기본 입과 같은 보정(위로 43px·왼쪽 15px, 96%)', S(0.96,627,629,-15,-43)),
 '눈_기본':('위로 9px', S(1,0,0,0,-9)),
 '화면왼팔':('임시 몸통이 넓어진 만큼 바깥(왼쪽)으로 25px', S(1,0,0,-25,0)),
 '화면오른팔':('임시 몸통이 넓어진 만큼 바깥(오른쪽)으로 25px·아래 20px', S(1,0,0,25,20)),
 '화면왼발':('아래로 22px', S(1,0,0,0,22)),
 '화면오른발':('아래로 22px, 94%', S(0.94,745,1032,0,22)),
}
def shift_half(im, side, dx, dy):
    h=im.copy(); o=im.copy()
    if side=='L': h[:,627:]=0; o[:,:627]=0
    else: h[:,:627]=0; o[:,627:]=0
    h=cv2.warpAffine(h,np.array([[1,0,dx],[0,1,dy]],float),(N,N),borderValue=(0,0,0,0))
    a=h[...,3:4]/255.; out=o.astype(float); out[...,:3]=h[...,:3]*a+out[...,:3]*(1-a); out[...,3:4]=np.maximum(h[...,3:4],o[...,3:4]); return out.astype(np.uint8)
log={}
for f in sorted(os.listdir('src/parts')):
    n=f[len('티라_'):-4]; im=cv2.imread('src/parts/'+f,cv2.IMREAD_UNCHANGED); note=[]
    if n in FIX:
        d,M=FIX[n]; im=cv2.warpAffine(im,M,(N,N),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0)); note.append(d)
    if n=='눈_환영웃음':
        im=shift_half(im,'L',11,3); im=shift_half(im,'R',2,3); note.append('기본 눈과 가로 중심 맞춤(왼쪽 +11px, 오른쪽 +2px), 둘 다 아래 3px')
    cv2.imwrite(O+n+'.png',im); log[n]=note
json.dump(log,open(O+'_fix_log.json','w'),ensure_ascii=False,indent=1)
