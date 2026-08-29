"""Small dependency-free SVG normalizer for line-art plotter designs.
It converts supported shapes and path commands to absolute polylines, fits to margin,
and deliberately preserves open paths rather than inventing a closing segment.
"""
import math, re, xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
from config import SETTINGS
Point=Tuple[float,float]
TOKEN=re.compile(r'[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')

def _sample_cubic(p0,p1,p2,p3,n=12): return [tuple((1-t)**3*p0[j]+3*(1-t)**2*t*p1[j]+3*(1-t)*t*t*p2[j]+t**3*p3[j] for j in (0,1)) for t in [k/n for k in range(1,n+1)]]
def _sample_quad(p0,p1,p2,n=10): return [tuple((1-t)**2*p0[j]+2*(1-t)*t*p1[j]+t*t*p2[j] for j in (0,1)) for t in [k/n for k in range(1,n+1)]]
def _arc(p,q,rx,ry,rotation,large,sweep):
    """SVG endpoint-arc conversion, sampled for a pen plotter."""
    rx,ry=abs(rx),abs(ry)
    if not rx or not ry or p==q:return [q]
    phi=math.radians(rotation%360);cp,sp=math.cos(phi),math.sin(phi);dx=(p[0]-q[0])/2;dy=(p[1]-q[1])/2
    xp=cp*dx+sp*dy;yp=-sp*dx+cp*dy;lam=xp*xp/(rx*rx)+yp*yp/(ry*ry)
    if lam>1: s=math.sqrt(lam);rx*=s;ry*=s
    sign=-1 if bool(large)==bool(sweep) else 1;num=rx*rx*ry*ry-rx*rx*yp*yp-ry*ry*xp*xp;den=rx*rx*yp*yp+ry*ry*xp*xp
    coef=sign*math.sqrt(max(0,num/max(den,1e-12)));cxp=coef*rx*yp/ry;cyp=coef*-ry*xp/rx
    cx=cp*cxp-sp*cyp+(p[0]+q[0])/2;cy=sp*cxp+cp*cyp+(p[1]+q[1])/2
    a0=math.atan2((yp-cyp)/ry,(xp-cxp)/rx);a1=math.atan2((-yp-cyp)/ry,(-xp-cxp)/rx);da=(a1-a0)%(2*math.pi)
    if not sweep: da-=2*math.pi
    n=max(4,math.ceil(abs(da)*max(rx,ry)/1.0))
    return [(cx+cp*rx*math.cos(a0+da*k/n)-sp*ry*math.sin(a0+da*k/n),cy+sp*rx*math.cos(a0+da*k/n)+cp*ry*math.sin(a0+da*k/n)) for k in range(1,n+1)]
def parse_path(d:str)->List[List[Point]]:
    t=TOKEN.findall(d); i=0; cmd=None; p=(0.,0.); start=None; paths=[]; cur=[]; last_ctrl=None
    def num():
        nonlocal i
        x=float(t[i]); i+=1; return x
    while i<len(t):
        if t[i].isalpha(): cmd=t[i]; i+=1
        if not cmd: raise ValueError('path lacks command')
        rel=cmd.islower(); c=cmd.upper()
        if c=='Z':
            if cur and start and cur[-1]!=start: cur.append(start)
            if cur: paths.append(cur)
            cur=[]; p=start or p; cmd=None; continue
        if c=='M':
            x,y=num(),num(); p=(x+p[0],y+p[1]) if rel else (x,y)
            if cur: paths.append(cur)
            cur=[p]; start=p; cmd='l' if rel else 'L'; continue
        if c=='L': x,y=num(),num(); q=(x+p[0],y+p[1]) if rel else (x,y); cur.append(q);p=q
        elif c=='H': x=num(); p=(x+p[0] if rel else x,p[1]);cur.append(p)
        elif c=='V': y=num(); p=(p[0],y+p[1] if rel else y);cur.append(p)
        elif c=='C':
            a=(num(),num());b=(num(),num());q=(num(),num()); a=tuple(a[j]+p[j] for j in (0,1)) if rel else a;b=tuple(b[j]+p[j] for j in (0,1)) if rel else b;q=tuple(q[j]+p[j] for j in (0,1)) if rel else q;cur+=_sample_cubic(p,a,b,q);p=q;last_ctrl=b
        elif c=='S':
            a=(2*p[0]-last_ctrl[0],2*p[1]-last_ctrl[1]) if last_ctrl else p;b=(num(),num());q=(num(),num());b=tuple(b[j]+p[j] for j in (0,1)) if rel else b;q=tuple(q[j]+p[j] for j in (0,1)) if rel else q;cur+=_sample_cubic(p,a,b,q);p=q;last_ctrl=b
        elif c=='Q':
            a=(num(),num());q=(num(),num());a=tuple(a[j]+p[j] for j in (0,1)) if rel else a;q=tuple(q[j]+p[j] for j in (0,1)) if rel else q;cur+=_sample_quad(p,a,q);p=q;last_ctrl=a
        elif c=='T':
            a=(2*p[0]-last_ctrl[0],2*p[1]-last_ctrl[1]) if last_ctrl else p;q=(num(),num());q=tuple(q[j]+p[j] for j in (0,1)) if rel else q;cur+=_sample_quad(p,a,q);p=q;last_ctrl=a
        elif c=='A':
            rx,ry,rot,large,sweep=num(),num(),num(),num(),num();q=(num(),num());q=tuple(q[j]+p[j] for j in (0,1)) if rel else q
            cur += _arc(p,q,rx,ry,rot,large,sweep);p=q
        else: raise ValueError('unsupported SVG command')
    if cur: paths.append(cur)
    return [x for x in paths if len(x)>1]
def _circle(el):
    cx=float(el.get('cx',0));cy=float(el.get('cy',0));r=float(el.get('r',0)); return [ [(cx+r*math.cos(2*math.pi*k/48),cy+r*math.sin(2*math.pi*k/48)) for k in range(49)] ]
def read_svg(path:str)->List[List[Point]]:
    root=ET.parse(path).getroot(); out=[]
    for e in root.iter():
        tag=e.tag.rsplit('}',1)[-1]
        if tag=='path': out+=parse_path(e.get('d',''))
        elif tag=='circle': out+=_circle(e)
        elif tag in ('polygon','polyline'):
            nums=[float(x) for x in re.findall(r'[-+]?\d*\.?\d+',e.get('points',''))]; p=list(zip(nums[::2],nums[1::2]));
            if tag=='polygon' and p and p[0]!=p[-1]:p.append(p[0])
            if len(p)>1:out.append(p)
    return out
def fit_paths(paths):
    pts=[p for x in paths for p in x];
    if not pts: raise ValueError('SVG has no drawable geometry')
    lo_x,hi_x=min(x for x,y in pts),max(x for x,y in pts);lo_y,hi_y=min(y for x,y in pts),max(y for x,y in pts)
    scale=min((70-2*SETTINGS.margin_mm)/max(hi_x-lo_x,1e-9),(70-2*SETTINGS.margin_mm)/max(hi_y-lo_y,1e-9));ox=SETTINGS.margin_mm+(60-(hi_x-lo_x)*scale)/2;oy=SETTINGS.margin_mm+(60-(hi_y-lo_y)*scale)/2
    return [[((x-lo_x)*scale+ox,(y-lo_y)*scale+oy) for x,y in path] for path in paths]
def normalize_svg(input_path, output_path=None):
    paths=fit_paths(read_svg(input_path))
    if output_path:
        d=''.join('<path d="M '+' L '.join(f'{x:.3f} {y:.3f}' for x,y in p)+'" fill="none" stroke="black"/>' for p in paths)
        open(output_path,'w',encoding='utf8').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 70 70">'+d+'</svg>')
    return paths
