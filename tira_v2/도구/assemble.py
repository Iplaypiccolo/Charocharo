import cv2,numpy as np,json,sys
N=1254
J={p['file'].replace('티라_v2_','').replace('.png',''):p for p in json.load(open('src/조립_초기보정값.json'))['parts']}
OVR=json.load(open('work/override.json')) if len(sys.argv)>1 and sys.argv[1]=='ovr' else {}
def part(n):
    im=cv2.imread('src/티라_v2_'+n+'.png',cv2.IMREAD_UNCHANGED); p=dict(J[n]); p.update(OVR.get(n,{}))
    M=np.array([[p['scale'],0,p['translate_x']],[0,p['scale'],p['translate_y']]],float)
    return cv2.warpAffine(im,M,(N,N),flags=cv2.INTER_AREA,borderValue=(0,0,0,0))
def comp(names):
    c=np.zeros((N,N,4),float)
    for n in names:
        im=part(n).astype(float); a=im[...,3:4]/255; c[...,:3]=im[...,:3]*a+c[...,:3]*(1-a); c[...,3:4]=255*a+c[...,3:4]*(1-a)
    return (c[...,:3]*(c[...,3:4]/255)+255*(1-c[...,3:4]/255)).astype(np.uint8)
if __name__=='__main__':
    A=comp(['꼬리','화면왼발','화면오른발','몸통바탕','화면왼팔_올림','화면오른팔_올림','눈_기본','입_기본이빨'])
    B=comp(['꼬리','화면왼발','화면오른발','몸통바탕','팻말_빈판','화면왼팔_올림','화면오른팔_올림','눈_질끈','입_환영웃음','불꽃_뿍'])
    cv2.imwrite('work/init_A.png',A); cv2.imwrite('work/init_B.png',B)
    cv2.imwrite('work/init.png',cv2.resize(np.hstack([A,B])[200:1100],None,fx=0.45,fy=0.45,interpolation=cv2.INTER_AREA))
