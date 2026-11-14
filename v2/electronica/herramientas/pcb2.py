import math, copy, re, json, heapq
import numpy as np
from sx import *
import pcb
from pcb import Board as B0, loadfp, bbox, U
FLIPL={'F.':'B.','B.':'F.'}
def flipel(e):
    if isinstance(e,str):
        m=re.match(r'^"([FB])\.(.*)"$',e)
        return f'"{"B" if m.group(1)=="F" else "F"}.{m.group(2)}"' if m else e
    if not e: return e
    if e[0] in('at','start','end','center','mid','xy') and len(e)>=3:
        e=list(e); e[2]=str(-float(e[2]))
        if e[0]=='at' and len(e)>=4: e[3]=str(-float(e[3]))
        return e
    out=[flipel(x) for x in e]
    if out[0]=='effects':
        j=find(out,'justify')
        if j: j[0].append('mirror')
        else: out.append(['justify','mirror'])
    return out
class Board(B0):
    def __init__(s,*a,ox=0,oy=0,**k):
        super().__init__(*a,**k); s.ox,s.oy=ox,oy; s.pads=[]; s.segs=[]; s.vias=[]
    def place(s,ref,lid,val,x,y,rot=0,pinmap=None,side='F',solder='both'):
        x+=s.ox; y+=s.oy
        fp=loadfp(lid)
        n0=len(s.fps)
        super().place(ref,lid,val,x,y,rot,pinmap)
        # recalcular caja con el desplazamiento (ya incluido) y registrar pads
        txt=s.fps[-1]; o=parse(txt)
        if side=='B':
            o=[o[0],o[1]]+[flipel(e) if not(isinstance(e,list) and e and e[0] in('at','uuid','path','sheetname','sheetfile')) else e for e in o[2:]]
            s.fps[-1]=dump(o,1)
        c,sn=math.cos(math.radians(rot)),math.sin(math.radians(rot))
        for p in find(o,'pad'):
            at=find(p,'at')[0]; lx,ly=float(at[1]),float(at[2])
            gx,gy=x+lx*c+ly*sn, y-lx*sn+ly*c
            sz=find(p,'size')[0]; d=find(p,'drill')
            nn=find(p,'net')
            net=nn[0][2].strip('"') if nn else None
            r=(math.hypot(float(sz[1]),float(sz[2]))/2) if p[3] in('rect','roundrect') else max(float(sz[1]),float(sz[2]))/2
            s.pads.append(dict(ref=ref,num=p[1].strip('"'),x=gx,y=gy,r=r,net=net,solder=solder,np=p[2]=='np_thru_hole',drill=float(d[0][1]) if d and len(d[0])>1 and d[0][1]!='oval' else 1.0))
    def edge(s,w,h):
        s.extra.append(f'(gr_rect (start {s.ox} {s.oy}) (end {s.ox+w} {s.oy+h}) (stroke (width 0.1) (type default)) (fill no) (layer "Edge.Cuts") (uuid "{U()}"))')
        s.W,s.H=w,h
    def check(s):
        bad=[]
        for i,(a,A) in enumerate(s.boxes):
            A=(A[0]-s.ox,A[1]-s.oy,A[2]-s.ox,A[3]-s.oy)
            if A[0]<0.5 or A[1]<0.5 or A[2]>s.W-0.5 or A[3]>s.H-0.5: bad.append(f'{a} fuera {tuple(round(v,1) for v in A)}')
            for b,Bx in s.boxes[i+1:]:
                Bx=(Bx[0]-s.ox,Bx[1]-s.oy,Bx[2]-s.ox,Bx[3]-s.oy)
                if A[0]<Bx[2] and Bx[0]<A[2] and A[1]<Bx[3] and Bx[1]<A[3]: bad.append(f'{a}~{b}')
        return bad
    # ---------------- ruteador de 2 capas en rejilla ----------------
    def route(s,power=(),G=0.5,wsig=0.8,wpow=1.0,clr=0.5,via_cost=40,iters=6,limit=250000,log=print):
        W,H=int(s.W/G)+1,int(s.H/G)+1
        def cell(x,y): return int(round((x-s.ox)/G)),int(round((y-s.oy)/G))
        wmax=wpow
        nets=sorted(set(p['net'] for p in s.pads if p['net']))
        nid={n:i+1 for i,n in enumerate(nets)}
        def disc(r):
            k=int(math.ceil(r/G)); return [(i,j) for i in range(-k,k+1) for j in range(-k,k+1) if (i*i+j*j)*G*G<=r*r]
        D_tr=disc(wmax/2+clr+wmax/2); D_via=disc(0.9+clr+wmax/2); D_viachk=disc(0.9+clr+wmax/2)
        edgek=int(math.ceil((1.0+wmax/2)/G))
        def base():
            blk=[np.zeros((W,H),np.int32) for _ in range(2)]
            for L in(0,1):
                blk[L][:edgek,:]=-1; blk[L][-edgek:,:]=-1; blk[L][:,:edgek]=-1; blk[L][:,-edgek:]=-1
            for p in s.pads:
                cx,cy=cell(p['x'],p['y']); n=nid.get(p['net'],-1) if not p['np'] else -1
                for (i,j) in disc(p['r']+clr+wmax/2):
                    a,b=cx+i,cy+j
                    if 0<=a<W and 0<=b<H:
                        for L in(0,1):
                            v=blk[L][a,b]
                            blk[L][a,b]=n if v in(0,n) and n>0 else -1
            return blk
        def mark(blk,L,c,n,D):
            for (i,j) in D:
                a,b=c[0]+i,c[1]+j
                if 0<=a<W and 0<=b<H:
                    v=blk[L][a,b]
                    blk[L][a,b]=n if v in(0,n) else -1
        padsby={}
        for p in s.pads:
            if p['net'] and not p['np']: padsby.setdefault(p['net'],[]).append(p)
        def layers_of(p): return {'both':(0,1),'top':(0,),'bottom':(1,)}[p['solder']]
        def order0():
            def span(n):
                ps=padsby[n]; return (max(q['x'] for q in ps)-min(q['x'] for q in ps))+(max(q['y'] for q in ps)-min(q['y'] for q in ps))
            return sorted([n for n in padsby if len(padsby[n])>1],key=span)
        def astar(blk,n,starts,goals):
            # starts/goals: sets of (L,i,j)
            pq=[]; best={}; prev={}
            gl=list(goals); gx=[g[1] for g in gl]; gy=[g[2] for g in gl]
            def h(i,j): return min(abs(i-a)+abs(j-b) for a,b in zip(gx[:60],gy[:60]))*0.9
            for st in starts:
                best[st]=0; heapq.heappush(pq,(h(st[1],st[2]),0,st))
            cnt=0
            while pq:
                f,g,st=heapq.heappop(pq); cnt+=1
                if cnt>limit: return None
                if st in goals and st not in starts:
                    path=[st]
                    while path[-1] in prev: path.append(prev[path[-1]])
                    return path[::-1]
                if g>best.get(st,1e18): continue
                L,i,j=st
                for di,dj,cst in((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.42),(1,-1,1.42),(-1,1,1.42),(-1,-1,1.42)):
                    a,b=i+di,j+dj
                    if not(0<=a<W and 0<=b<H): continue
                    v=blk[L][a,b]
                    nst=(L,a,b)
                    if v not in(0,n) and nst not in goals: continue
                    ng=g+cst+(0.4 if L==0 else 0)
                    if ng<best.get(nst,1e18): best[nst]=ng; prev[nst]=st; heapq.heappush(pq,(ng+h(a,b),ng,nst))
                # via
                o=1-L; nst=(o,i,j)
                if all(0<=i+a<W and 0<=j+b<H and blk[0][i+a,j+b] in(0,n) and blk[1][i+a,j+b] in(0,n) for a,b in D_viachk):
                    ng=g+via_cost
                    if ng<best.get(nst,1e18): best[nst]=ng; prev[nst]=st; heapq.heappush(pq,(ng+h(i,j),ng,nst))
            return None
        bestres=None; order=order0()
        for it in range(iters):
            blk=base(); segs=[]; vias=[]; fails=[]
            for n in order:
                k=nid[n]; ps=padsby[n]; w=wpow if n in power else wsig
                tree=set(); first=ps[0]
                for L in layers_of(first): tree.add((L,)+cell(first['x'],first['y']))
                rest=ps[1:]
                while rest:
                    rest.sort(key=lambda p:min(abs(cell(p['x'],p['y'])[0]-t[1])+abs(cell(p['x'],p['y'])[1]-t[2]) for t in list(tree)[:400]))
                    p=rest.pop(0)
                    st={(L,)+cell(p['x'],p['y']) for L in layers_of(p)}
                    path=astar(blk,k,st,tree)
                    if not path: fails.append((n,p['ref'],p['num'])); continue
                    for idx,(L,i,j) in enumerate(path):
                        tree.add((L,i,j)); mark(blk,L,(i,j),k,D_tr)
                        if idx and path[idx-1][0]!=L:
                            vias.append((n,i,j)); mark(blk,0,(i,j),k,D_via); mark(blk,1,(i,j),k,D_via)
                    # segmentos
                    run=[path[0]]
                    for q in path[1:]:
                        if q[0]!=run[-1][0]:
                            segs.append((n,w,run)); run=[q]; continue
                        run.append(q)
                    segs.append((n,w,run))
            log(f'iter {it}: fallas {len(fails)} vias {len(vias)}')
            if bestres is None or (len(fails),len(vias))<(len(bestres[2]),len(bestres[1])): bestres=(segs,vias,fails)
            if not fails: break
            fn=list(dict.fromkeys(f[0] for f in fails)); order=fn+[n for n in order if n not in fn]
        segs,vias,fails=bestres
        out=[]
        for n,w,run in segs:
            if len(run)<2: continue
            pts=[run[0]]
            for a,b,c in zip(run,run[1:],run[2:]):
                if (b[1]-a[1],b[2]-a[2])!=(c[1]-b[1],c[2]-b[2]): pts.append(b)
            pts.append(run[-1])
            for a,b in zip(pts,pts[1:]):
                Lname='F.Cu' if a[0]==0 else 'B.Cu'
                out.append(f'(segment (start {s.ox+a[1]*G:.3f} {s.oy+a[2]*G:.3f}) (end {s.ox+b[1]*G:.3f} {s.oy+b[2]*G:.3f}) (width {w}) (layer "{Lname}") (net {s.nets["/"+n if False else n] if n in s.nets else 0}) (uuid "{U()}"))')
        for n,i,j in vias:
            out.append(f'(via (at {s.ox+i*G:.3f} {s.oy+j*G:.3f}) (size 1.8) (drill 0.8) (layers "F.Cu" "B.Cu") (net {s.nets[n]}) (uuid "{U()}"))')
        s.extra+=out
        # unir el centro real del pad con su celda (pad fuera de rejilla)
        return fails,len(vias),len([o for o in out if o.startswith('(segment')])
