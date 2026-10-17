# v2 검수본: 초기보정값 적용 + 팔 색 맞춤 + 불꽃 뿌리 맞춤. 원본(src)은 그대로
import cv2,numpy as np,json,os,sys
sys.argv=['x']; exec(open('work/assemble.py').read().split("if __name__")[0])
O='work/fixed/'; log={}
BODY=np.array([85,158,211.])
def brownmask(im): return (im[...,2]>150)&(im[...,1]>110)&(im[...,1]<200)&(im[...,0]<140)&(im[...,3]>0)
for n in J:
    im=part(n); note=['초기보정값 적용: 배율 %.3f, 이동 (%.1f, %.1f)'%(J[n]['scale'],J[n]['translate_x'],J[n]['translate_y'])] if J[n]['scale']!=1 or J[n]['translate_x'] else ['그대로']
    if n in ('화면왼팔_올림','화면오른팔_올림'):
        m=brownmask(im); med=np.median(im[m&(im[...,3]>200)][:,:3].astype(float),0)
        px=im[...,:3].astype(float); px[m]=np.clip(px[m]*(BODY/med),0,255); im[...,:3]=px.astype(np.uint8)
        note.append('팔 갈색 %s → 몸통 갈색 %s (BGR, 접합부 색 차이 제거)'%(list(med.astype(int)),list(BODY.astype(int))))
    if n=='불꽃_뿍':
        im=cv2.warpAffine(im,np.array([[1,0,0],[0,1,4.5]],float),(N,N),borderValue=(0,0,0,0)); note.append('뿌리를 작은 불꽃과 같은 높이로 아래 4.5px (두 프레임 뿌리 x449, y553)')
    cv2.imwrite(O+n+'.png',im); log[n]=note
json.dump(log,open(O+'_fix_log.json','w'),ensure_ascii=False,indent=1); print(json.dumps(log,ensure_ascii=False)[:900])
