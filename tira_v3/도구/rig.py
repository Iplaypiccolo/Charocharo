import cv2,numpy as np,json
N=1254; J={t['id']:t for t in json.load(open('src/rig_start.json'))['transforms']}
import glob,os
FILES={os.path.basename(f)[6:8]:f for f in glob.glob('src/파츠/*.png')}
def raw(i): return cv2.imread(FILES[i],cv2.IMREAD_UNCHANGED)
def M(i, extra=None):
    t=J[i]; s=t.get('scale',1); tx=t.get('translate_x',0); ty=t.get('translate_y',0)
    return np.array([[s,0,tx],[0,s,ty]],float)
def placed(i,M_=None):
    # 투명 가장자리의 검은 번짐을 막기 위해 미리 곱한 알파(premultiplied)로 변환 후 되돌림
    im=raw(i).astype(np.float32); a=im[...,3:4]/255; pm=np.concatenate([im[...,:3]*a,im[...,3:4]],2)
    w=cv2.warpAffine(pm,M(i) if M_ is None else M_,(N,N),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
    al=w[...,3:4]; rgb=np.where(al>0.5,w[...,:3]/np.maximum(al,1e-3)*255,0)
    return np.clip(np.concatenate([rgb,al],2),0,255).astype(np.uint8)
def comp(layers,bg=255):
    c=np.zeros((N,N,4),float)
    for im in layers:
        im=im.astype(float); a=im[...,3:4]/255; c[...,:3]=im[...,:3]*a+c[...,:3]*(1-a); c[...,3:4]=255*a+c[...,3:4]*(1-a)
    return (c[...,:3]*(c[...,3:4]/255)+bg*(1-c[...,3:4]/255)).astype(np.uint8)
def sign_M(i, grip, s=None):
    t=J[i]; s=t.get('scale',1) if s is None else s; ax,ay=t['source_bite_anchor']
    return np.array([[s,0,grip[0]-s*ax],[0,s,grip[1]-s*ay]],float)
