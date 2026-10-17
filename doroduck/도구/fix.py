# 검수본: 원본(src/parts)은 그대로, work/fixed 에 최소 보정본
import cv2, numpy as np, json, os, shutil
N=1254; O='work/fixed/'
def M_scale(s,cx,cy,dx,dy): return np.array([[s,0,cx-s*cx+dx],[0,s,cy-s*cy+dy]],float)
FIX={   # 기본정면과 몸통 밖 윤곽을 맞춰 정한 값 (기준점 = 파츠 상자 가운데)
 '화면오른날개':('왼날개보다 약 13% 큼 → 85%로 줄이고 왼쪽 12px·위 6px', M_scale(0.85,942,776.5,-12,-6)),
 '화면오른발':('약간 작음 → 108%, 위 6px', M_scale(1.08,734.5,1024,2,-6)),
 '화면왼발':('약간 작음 → 104%, 오른쪽 2px', M_scale(1.04,512,1024.5,2,0)),
}
log={}
def shift_half(im, side, dx):   # 두 눈이 한 그림 → 한쪽만 옮김
    h=im.copy(); o=im.copy()
    if side=='L': h[:, 627:]=0; o[:, :627]=0
    else: h[:, :627]=0; o[:, 627:]=0
    h=cv2.warpAffine(h,np.array([[1,0,dx],[0,1,0]],float),(N,N),borderValue=(0,0,0,0))
    a=h[...,3:4]/255.; out=o.astype(float); out[...,:3]=h[...,:3]*a+out[...,:3]*(1-a); out[...,3:4]=np.maximum(h[...,3:4],o[...,3:4]); return out.astype(np.uint8)
for f in sorted(os.listdir('src/parts')):
    n=f[len('도로덕_'):-4]; im=cv2.imread('src/parts/'+f,cv2.IMREAD_UNCHANGED); note=[]
    if n in FIX:
        d,M=FIX[n]; im=cv2.warpAffine(im,M,(N,N),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0)); note.append(d)
    if n=='눈_환영웃음':
        im=shift_half(im,'L',7); note.append('왼쪽 웃는 눈만 오른쪽으로 7px (기본 눈과 중심·간격 맞춤)')
    cv2.imwrite(O+n+'.png',im); log[n]=note
json.dump(log,open(O+'_fix_log.json','w'),ensure_ascii=False,indent=1); print(log)
