import math, heapq, numpy as np
from pcb2 import Board, U
def route_nc(s,power=(),pm=0.35,npm=0.4,G=0.5,wsig=0.8,wpow=1.0,clr=0.5,via_cost=25,iters=40,limit=200000,log=print):
    W,H=int(s.W/G)+1,int(s.H/G)+1
    def cell(x,y): return int(round((x-s.ox)/G)),int(round((y-s.oy)/G))
    def disc(r):
        k=int(math.ceil(r/G)); return [(i,j) for i in range(-k,k+1) for j in range(-k,k+1) if (i*i+j*j)*G*G<=r*r+1e-9]
    nets=sorted(set(p['net'] for p in s.pads if p['net']))
    nid={n:i+1 for i,n in enumerate(nets)}
    hard=[np.zeros((W,H),np.int32) for _ in(0,1)]
    ek=int(math.ceil((1.0+wpow/2)/G))
    for L in(0,1):
        hard[L][:ek,:]=-1; hard[L][-ek:,:]=-1; hard[L][:,:ek]=-1; hard[L][:,-ek:]=-1
    for p in s.pads:
        cx,cy=cell(p['x'],p['y']); n=nid.get(p['net'],-1) if not p['np'] else -1
        for i,j in disc((p['r']+0.25+npm+wsig/2) if p['np'] else (p['r']+clr+pm+wsig/2)):
            a,b=cx+i,cy+j
            if 0<=a<W and 0<=b<H:
                for L in(0,1):
                    v=hard[L][a,b]; hard[L][a,b]=n if (v in(0,n) and n>0) else -1
    for p in s.pads:   # el cobre propio del pad siempre es de su red
        if p['np'] or not p['net']: continue
        cx,cy=cell(p['x'],p['y']); n=nid[p['net']]
        for i,j in disc(max(p['r']-0.35,0.01)):
            a,b=cx+i,cy+j
            if 0<=a<W and 0<=b<H:
                for L in(0,1): hard[L][a,b]=n
    novia=np.zeros((W,H),bool)
    for p in s.pads:
        cx,cy=cell(p['x'],p['y'])
        for i,j in disc(p['r']+0.9+0.3):
            a,b=cx+i,cy+j
            if 0<=a<W and 0<=b<H: novia[a,b]=True
    padsby={}
    for p in s.pads:
        if p['net'] and not p['np']: padsby.setdefault(p['net'],[]).append(p)
    rn=[n for n in padsby if len(padsby[n])>1]
    def lay(p): return {'both':(0,1),'top':(0,),'bottom':(1,)}[p['solder']]
    occ=[np.zeros((W,H),np.int16) for _ in(0,1)]
    hist=[np.zeros((W,H),np.float32) for _ in(0,1)]
    D={n:disc((wpow if n in power else wsig)/2+clr+wsig/2) for n in rn}
    DV=disc(0.9+clr+wpow/2)
    routes={}   # n -> (paths list, vias list, marked cells list)
    def addmark(cells,sgn):
        for L,a,b in cells: occ[L][a,b]+=sgn
    def marks_for(n,paths,vias):
        S=set()
        for path in paths:
            for L,i,j in path:
                for a,b in D[n]:
                    x,y=i+a,j+b
                    if 0<=x<W and 0<=y<H: S.add((L,x,y))
        for i,j in vias:
            for a,b in DV:
                x,y=i+a,j+b
                if 0<=x<W and 0<=y<H: S.add((0,x,y)); S.add((1,x,y))
        return list(S)
    def astar(k,starts,goals,pres):
        pq=[]; best={}; prev={}
        gl=list(goals)[:80]
        def h(i,j): return min(max(abs(i-a),abs(j-b)) for _,a,b in gl)
        for st in starts: best[st]=0; heapq.heappush(pq,(h(st[1],st[2]),0.0,st))
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
            for di,dj,c in((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)):
                a,b=i+di,j+dj
                if not(0<=a<W and 0<=b<H): continue
                hv=hard[L][a,b]
                if hv not in(0,k): continue
                o=occ[L][a,b]
                ng=g+c*(1+(pres*o+hist[L][a,b] if o else hist[L][a,b]*0.2))+(0.3 if L==0 else 0)
                nst=(L,a,b)
                if ng<best.get(nst,1e18): best[nst]=ng; prev[nst]=st; heapq.heappush(pq,(ng+h(a,b),ng,nst))
            ol=1-L
            if hard[ol][i,j] in(0,k) and not novia[i,j]:
                pen=sum(1 for a,b in DV[::3] if 0<=i+a<W and 0<=j+b<H and (hard[0][i+a,j+b] not in(0,k) or hard[1][i+a,j+b] not in(0,k)))
                if pen==0:
                    ng=g+via_cost+pres*(occ[0][i,j]+occ[1][i,j])
                    nst=(ol,i,j)
                    if ng<best.get(nst,1e18): best[nst]=ng; prev[nst]=st; heapq.heappush(pq,(ng+h(i,j),ng,nst))
        return None
    def route_net(n,pres):
        k=nid[n]; ps=sorted(padsby[n],key=lambda p:(p['x'],p['y']))
        tree=set((L,)+cell(ps[0]['x'],ps[0]['y']) for L in lay(ps[0]))
        paths=[]; vias=[]; fail=[]
        rest=ps[1:]
        while rest:
            tl=list(tree)
            rest.sort(key=lambda p:min(abs(cell(p['x'],p['y'])[0]-t[1])+abs(cell(p['x'],p['y'])[1]-t[2]) for t in tl[::max(1,len(tl)//200)]))
            p=rest.pop(0)
            st={(L,)+cell(p['x'],p['y']) for L in lay(p)}
            path=astar(k,st,tree,pres)
            if not path: fail.append(p); continue
            paths.append(path); tree|=set(path)
            for a,b in zip(path,path[1:]):
                if a[0]!=b[0]: vias.append((b[1],b[2]))
        return paths,vias,fail
    pres=0.5; best=None
    for it in range(iters):
        fails=[]
        order=sorted(rn,key=lambda n:-len(routes.get(n,([],[],[],[]))[3]) if it else 0)
        for n in order:
            if n in routes: addmark(routes[n][2],-1)
            paths,vias,fail=route_net(n,pres)
            m=marks_for(n,paths,vias); addmark(m,+1)
            routes[n]=(paths,vias,m,fail)
            fails+= [(n,p['ref'],p['num']) for p in fail]
        # conflictos: centros de pista de una red dentro de la zona de otra
        conf=0; confnets=set()
        for n,(paths,vias,m,fail) in routes.items():
            own=set(m)
            for path in paths:
                for L,i,j in path:
                    if occ[L][i,j]>1: conf+=1; confnets.add(n); hist[L][i,j]+=1.0
        nv=sum(len(r[1]) for r in routes.values())
        log(f'it {it}: fallas {len(fails)} conflictos {conf} vias {nv} {sorted(confnets)[:6]}')
        score=(len(fails),conf,nv)
        if best is None or score<best[0]: best=(score,{n:(r[0],r[1],r[3]) for n,r in routes.items()},fails)
        if not fails and conf==0: break
        pres=min(pres*1.3,50)
    score,R,fails=best
    out=[]; nvias=0
    for n,(paths,vias,fail) in R.items():
        w=wpow if n in power else wsig
        for path in paths:
            run=[path[0]]
            def flush(run):
                if len(run)<2: return
                pts=[run[0]]
                for a,b,c in zip(run,run[1:],run[2:]):
                    if (b[1]-a[1],b[2]-a[2])!=(c[1]-b[1],c[2]-b[2]): pts.append(b)
                pts.append(run[-1])
                for a,b in zip(pts,pts[1:]):
                    out.append(f'(segment (start {s.ox+a[1]*G:.3f} {s.oy+a[2]*G:.3f}) (end {s.ox+b[1]*G:.3f} {s.oy+b[2]*G:.3f}) (width {w}) (layer "{"F.Cu" if a[0]==0 else "B.Cu"}") (net {s.nets[n]}) (uuid "{U()}"))')
            for q in path[1:]:
                if q[0]!=run[-1][0]: flush(run); run=[q]
                else: run.append(q)
            flush(run)
        for i,j in dict.fromkeys(vias):
            nvias+=1
            out.append(f'(via (at {s.ox+i*G:.3f} {s.oy+j*G:.3f}) (size 1.8) (drill 0.8) (layers "F.Cu" "B.Cu") (net {s.nets[n]}) (uuid "{U()}"))')
    s.extra+=out
    return fails,score[1],nvias,len([o for o in out if o.startswith('(segment')])
