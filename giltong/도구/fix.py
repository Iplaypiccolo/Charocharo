# 검수본 만들기: 원본(src/parts)은 그대로 두고 work/fixed 에 최소 보정본을 만든다.
import cv2, numpy as np, json, shutil, os
P='src/parts/길통이_'; O='work/fixed/'
N=1254
FIX = {   # 이름: (설명, 2x3 변환)  — 기본정면(reference)과 윤곽을 비교해 정한 값
 '화면왼다리': ('왼쪽으로 6px', [[1,0,-6],[0,1,0]]),
 '화면오른다리': ('왼쪽 6px·아래 7px', [[1,0,-6],[0,1,7]]),
 '망토': ('위쪽 가운데(626,780) 기준 가로 96%·세로 105%', None),
}
def cape_M():
    sx,sy,cx,cy=0.96,1.05,626,780
    return [[sx,0,cx-sx*cx],[0,sy,cy-sy*cy]]
log={}
for f in sorted(os.listdir('src/parts')):
    n=f[len('길통이_'):-4]; im=cv2.imread('src/parts/'+f,cv2.IMREAD_UNCHANGED)
    note=[]
    if n in FIX:
        desc,M=FIX[n]; M=M or cape_M()
        im=cv2.warpAffine(im,np.array(M,float),(N,N),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0)); note.append(desc)
    if n=='몸통':   # 옷의 파랑이 팔·기본정면보다 밝음 → 팔과 같은 파랑으로
        px=im[...,:3].astype(float); blue=(px[...,0]>150)&(px[...,2]<90)&(im[...,3]>0)
        k=np.array([202/240,117.5/132,1.0]); px[blue]=np.clip(px[blue]*k,0,255); im[...,:3]=px.astype(np.uint8); note.append('옷 파랑 (240,132,0)→(202,117,0) BGR')
    cv2.imwrite(O+n+'.png',im); log[n]=note
json.dump(log,open(O+'_fix_log.json','w'),ensure_ascii=False,indent=1); print(log)
