import uuid, json, math, copy, sys
from sx import *
U=lambda: str(uuid.uuid4())
H='/mnt/user-data/uploads/KiCAD/_tmp_huellas/'
def loadfp(lid):
    lib,name=lid.split(':')
    f={'ESP32':'ESP32__','DRV8833':'DRV8833__','MP1584':'MP1584__'}.get(lib,lib+'__')+name+'.kicad_mod'
    return parse(open(H+f).read())
def bbox(fp):
    xs=[];ys=[]
    for e in fp:
        if isinstance(e,list) and e and e[0] in('fp_line','fp_rect','fp_poly','fp_circle') and any(isinstance(l,list) and l[0]=='layer' and 'CrtYd' in l[1] for l in e):
            if e[0]=='fp_circle':
                c=find(e,'center')[0]; en=find(e,'end')[0]; r=math.hypot(float(en[1])-float(c[1]),float(en[2])-float(c[2]))
                xs+=[float(c[1])-r,float(c[1])+r]; ys+=[float(c[2])-r,float(c[2])+r]; continue
            for k in ('start','end'):
                for a in find(e,k): xs.append(float(a[1])); ys.append(float(a[2]))
            for p in find(e,'pts'):
                for q in find(p,'xy'): xs.append(float(q[1])); ys.append(float(q[2]))
    if not xs:  # sin courtyard: usar serigrafia/pads
        for e in fp:
            if isinstance(e,list) and e and e[0] in('fp_rect','fp_line'):
                for k in ('start','end'):
                    for a in find(e,k): xs.append(float(a[1])); ys.append(float(a[2]))
    return min(xs),min(ys),max(xs),max(ys)
class Board:
    def __init__(s,template,sch,esperado,title):
        s.tpl=open(template).read(); s.nets={}; s.fps=[]; s.title=title; s.boxes=[]; s.extra=[]
        o=parse(open(sch).read()); s.symu={}
        for sy in find(o,'symbol'):
            ref=[p for p in find(sy,'property') if p[1]=='"Reference"'][0][2].strip('"')
            s.symu[ref]=find(sy,'uuid')[0][1].strip('"')
        s.sch=sch.split('/')[-1]
        s.pinnet={}
        s.vals={}
        for sy in find(o,'symbol'):
            ref=[p for p in find(sy,'property') if p[1]=='"Reference"'][0][2].strip('"')
            s.vals[ref]=[p for p in find(sy,'property') if p[1]=='"Value"'][0][2].strip('"')
        POW={'GND','+3V3','+5V'} if 'sensores' in sch else {'GND','+3V3'}
        for ref,num,net in json.load(open(esperado))['esperado']: s.pinnet[(ref,num)]=net if net in POW else '/'+net
        if ('A1','14') in s.pinnet: s.pinnet[('A1','17')]=s.pinnet[('A1','14')]
    def net(s,n):
        if n not in s.nets: s.nets[n]=len(s.nets)+1
        return s.nets[n]
    def place(s,ref,lid,val,x,y,rot=0,pinmap=None):
        fp=loadfp(lid); b=bbox(fp)
        c,sn=math.cos(math.radians(rot)),math.sin(math.radians(rot))
        pts=[(x+px*c+py*sn, y-px*sn+py*c) for px in(b[0],b[2]) for py in(b[1],b[3])]
        bx=(min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts))
        s.boxes.append((ref,bx))
        out=['footprint',f'"{lid}"']
        for e in fp[2:]:
            if isinstance(e,list) and e and e[0] in('version','generator','generator_version'): continue
            e=copy.deepcopy(e)
            if isinstance(e,list) and e and e[0]=='layer':
                out.append(e); out.append(['uuid',f'"{U()}"']); out.append(['at',f'{x:.3f}',f'{y:.3f}',str(rot)]); continue
            if isinstance(e,list) and e and e[0]=='property':
                if e[1]=='"Reference"': e[2]=f'"{ref}"'
                if e[1]=='"Value"': e[2]=f'"{s.vals.get(ref,val)}"'
                at=find(e,'at')
                if at and rot:
                    while len(at[0])<4: at[0].append('0')
                    at[0][3]=str((float(at[0][3])+rot)%360)
            if isinstance(e,list) and e and e[0]=='pad':
                num=e[1].strip('"'); key=(pinmap or {}).get(num,num)
                n=s.pinnet.get((ref,key))
                at=find(e,'at')[0]
                if rot:
                    while len(at)<4: at.append('0')
                    at[3]=str((float(at[3])+rot)%360)
                if n: e.append(['net',str(s.net(n)),f'"{n}"'])
            out.append(e)
        if ref in s.symu:
            out.append(['path',f'"/{s.symu[ref]}"']); out.append(['sheetname','"/"']); out.append(['sheetfile',f'"{s.sch}"'])
        s.fps.append(dump(out,1))
    def edge(s,w,h,x0=0,y0=0):
        s.extra.append(f'(gr_rect (start {x0} {y0}) (end {x0+w} {y0+h}) (stroke (width 0.1) (type default)) (fill no) (layer "Edge.Cuts") (uuid "{U()}"))')
        s.W,s.H=w,h
    def note(s,t,x,y,layer='Cmts.User'):
        s.extra.append(f'(gr_text "{t}" (at {x} {y} 0) (layer "{layer}") (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15)) (justify left)))')
    def rect(s,x0,y0,x1,y1,layer='Cmts.User'):
        s.extra.append(f'(gr_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width 0.15) (type dash)) (fill no) (layer "{layer}") (uuid "{U()}"))')
    def check(s):
        bad=[]
        for i,(a,A) in enumerate(s.boxes):
            if A[0]<0.5 or A[1]<0.5 or A[2]>s.W-0.5 or A[3]>s.H-0.5: bad.append(f'{a} fuera {tuple(round(v,1) for v in A)}')
            for b,B in s.boxes[i+1:]:
                if A[0]<B[2] and B[0]<A[2] and A[1]<B[3] and B[1]<A[3]: bad.append(f'{a}~{b}')
        return bad
    def save(s,path):
        t=s.tpl.rstrip().rstrip(')').rstrip()
        t=t.replace('(title "','(title "',1)
        nets='\t(net 0 "")\n'+''.join(f'\t(net {i} "{n}")\n' for n,i in s.nets.items())
        i=t.index('\t(embedded_fonts')
        t=t[:i]+nets+'\n'.join('\t'+f for f in s.fps)+'\n'+'\n'.join('\t'+x for x in s.extra)+'\n'+t[i:]+'\n)\n'
        open(path,'w').write(t)
