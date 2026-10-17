import cv2, numpy as np
P='src/parts/길통이_'
ORDER=['망토','화면왼다리','화면오른다리','화면왼팔','화면오른팔','몸통','얼굴바탕','눈_기본','눈썹','입_기본미소']
def over(order, offs=None):
    c=np.zeros((1254,1254,4),float)
    for n in order:
        im=cv2.imread(P+n+'.png',cv2.IMREAD_UNCHANGED).astype(float)
        if offs and n in offs:
            M=np.array(offs[n],float); im=cv2.warpAffine(im,M,(1254,1254),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
        a=im[...,3:4]/255; c[...,:3]=im[...,:3]*a+c[...,:3]*(1-a); c[...,3:4]=255*a+c[...,3:4]*(1-a)
    return c
def flat(c,bg=255):
    a=c[...,3:4]/255; return (c[...,:3]*a+bg*(1-a)).astype(np.uint8)
if __name__=='__main__':
    c=over(ORDER); f=flat(c)
    ref=cv2.imread('src/reference/길통이_기본정면.png',cv2.IMREAD_UNCHANGED)
    rf=flat(ref.astype(float))
    # 차이 시각화: 우리 윤곽(남색)=빨강, 참고 윤곽=초록
    def ink(img): return (img[...,0]<120)&(img[...,1]<90)&(img[...,2]<60)
    d=np.full((1254,1254,3),255,np.uint8); d[ink(rf)]=(0,180,0); d[ink(f)]=(0,0,230); d[ink(rf)&ink(f)]=(40,40,40)
    out=np.hstack([f,rf,d]); cv2.imwrite('work/raw_overlay.png',cv2.resize(out,None,fx=0.5,fy=0.5,interpolation=cv2.INTER_AREA))
    cv2.imwrite('work/raw_full.png',f)
