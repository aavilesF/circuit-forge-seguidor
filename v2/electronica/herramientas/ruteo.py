# Esquematico con cables reales: colocacion manual + ruteador ortogonal A* en rejilla de 1.27 mm
import uuid, copy, heapq, json, math
from sx import *
import gen
U=lambda: str(uuid.uuid4())
G=1.27
def C(v): return int(round(v/G))
def libsym(lid):
    if lid.startswith('power:') and lid not in gen.OFFL:
        s=copy.deepcopy(gen.k7('power')[lid.split(':')[1]]); s[1]=f'"{lid}"'; return s
    return gen.libsym(lid)
def bbox(ls):
    xs=[];ys=[]
    def walk(n):
        for e in n:
            if not isinstance(e,list) or not e: continue
            if e[0]=='pin': continue
            if e[0] in('rectangle',):
                for k in('start','end'):
                    a=find(e,k)[0]; xs.append(float(a[1])); ys.append(float(a[2]))
            elif e[0] in('polyline','bezier'):
                for p in find(find(e,'pts')[0],'xy'): xs.append(float(p[1])); ys.append(float(p[2]))
            elif e[0]=='circle':
                c=find(e,'center')[0]; r=float(find(e,'radius')[0][1]); xs.extend([float(c[1])-r,float(c[1])+r]); ys.extend([float(c[2])-r,float(c[2])+r])
            elif e[0]=='arc':
                for k in('start','mid','end'):
                    a=find(e,k)[0]; xs.append(float(a[1])); ys.append(float(a[2]))
            elif e[0]=='symbol': walk(e)
    walk(ls)
    return (min(xs),min(ys),max(xs),max(ys)) if xs else None
class Esq:
    def __init__(s,proj,title,W=330,H=230):
        s.proj=proj; s.title=title; s.root=U(); s.libs={}; s.comps=[]; s.items=[]; s.pins={}  # net->list of (cell, dir, ref, num)
        s.W,s.H=W,H; s.blocked=set(); s.node={}; s.oh={}; s.ov={}; s.segs={}; s.npwr=0; s.esperado=[]; s.nc=[]; s.labels=[]; s.stub={}
        for i in range(C(283),C(410)):
            for j in range(C(236),C(290)): s.blocked.add((i,j))
    FP={}
    def add(s,lid,ref,val,x,y,nets,fp='',board=True,power=('GND','+3V3')):
        fp=fp or s.FP.get(ref,'')
        if lid not in s.libs: s.libs[lid]=libsym(lid)
        ls=s.libs[lid]; ps=pins(ls)
        props=[]
        for pr in find(ls,'property'):
            k=pr[1].strip('"'); at=find(pr,'at')[0]
            v={'Reference':ref,'Value':val,'Footprint':fp}.get(k,pr[2].strip('"'))
            hide=k not in('Reference','Value') or ref.startswith('#')
            props.append(f'(property "{k}" "{v}" (at {x+float(at[1]):.2f} {y-float(at[2]):.2f} 0) (effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""}))')
        pinl=' '.join(f'(pin "{p["num"]}" (uuid "{U()}"))' for p in ps)
        s.items.append(f'(symbol (lib_id "{lid}") (at {x:.2f} {y:.2f} 0) (unit 1) (exclude_from_sim no) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"yes" if board else "no"}) (dnp no) (uuid "{U()}") {" ".join(props)} {pinl} (instances (project "{s.proj}" (path "/{s.root}" (reference "{ref}") (unit 1)))))')
        b=bbox(ls)
        if b and not ref.startswith('#'):
            x0,y0,x1,y1=x+b[0],y-b[3],x+b[2],y-b[1]
            for i in range(C(x0),C(x1)+1):
                for j in range(C(y0),C(y1)+1): s.blocked.add((i,j))
        for p in ps:
            ex,ey=x+p['x'],y-p['y']
            if p['a'] in (0,180): d=(-1 if p['x']<0 else 1,0)
            else: d=(0,1 if p['y']<0 else -1)
            if p['x']==0 and p['y']==0: d=(0,-1)
            cell=(C(ex),C(ey))
            # linea del pin bloqueada (hacia el cuerpo)
            L=C(p['len'])
            for k in range(1,L+1): s.blocked.add((cell[0]-d[0]*k,cell[1]-d[1]*k))
            key=p['num'] if p['num'] in nets else p['name']
            net=nets.get(key,'__NC__') if nets.get(key,1) is not None else None
            if net is None: continue
            s.node[cell]='#pin'
            if net=='__NC__':
                s.items.append(f'(no_connect (at {ex:.2f} {ey:.2f}) (uuid "{U()}"))'); s.nc.append((ref,p['num'])); continue
            s.esperado.append((ref,p['num'],net))
            # si el extremo del pin queda dentro del dibujo del simbolo, abrir un pasillo hasta salir
            L2=2
            if b and not ref.startswith('#'):
                k=0
                while C(x0)<=cell[0]+d[0]*k<=C(x1) and C(y0)<=cell[1]+d[1]*k<=C(y1): k+=1
                if k>0:
                    L2=k+1
                    for q in range(0,k+1): s.blocked.discard((cell[0]+d[0]*q,cell[1]+d[1]*q))
            s.stub[(ref,p['num'])]=L2
            s.pins.setdefault(net,[]).append((cell,d,ref,p['num']))
    def pwr(s,lid,cell,d):
        s.npwr+=1
        rot={(0,1):0,(1,0):90,(0,-1):180,(-1,0):270}[d]
        name=lid.split(':')[1]
        if lid not in s.libs: s.libs[lid]=libsym(lid)
        ref=f'#PWR{s.npwr:03d}'
        x,y=cell[0]*G,cell[1]*G
        s.items.append(f'(symbol (lib_id "{lid}") (at {x:.2f} {y:.2f} {rot}) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "{U()}") (property "Reference" "{ref}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Value" "{name}" (at {x:.2f} {y+ (3.8 if d==(0,1) else -3.8):.2f} 0) (effects (font (size 1.27 1.27)))) (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes))) (pin "1" (uuid "{U()}")) (instances (project "{s.proj}" (path "/{s.root}" (reference "{ref}") (unit 1)))))')
    def wire(s,net,a,b):
        s.segs.setdefault(net,[]).append((a,b))
    def ok(s,c):
        return 0<=c[0]<=C(s.W*1.27/1.27*1) and True
    def route(s,net,lab=None):
        P=s.pins[net]
        # stubs de 2 celdas hacia afuera para despegar de los cuerpos
        tree=set(); starts=[]
        for cell,d,ref,num in P:
            L2=s.stub[(ref,num)]
            e=(cell[0]+d[0]*L2,cell[1]+d[1]*L2)
            bad=any(((cell[0]+d[0]*k,cell[1]+d[1]*k) in s.blocked) or (s.node.get((cell[0]+d[0]*k,cell[1]+d[1]*k)) not in (None,net) and k>0) or (cell[0]+d[0]*k,cell[1]+d[1]*k) in s.oh or (cell[0]+d[0]*k,cell[1]+d[1]*k) in s.ov for k in range(1,L2+1))
            if bad: e=cell
            else:
                s.wire(net,cell,e); s.mark(net,[(cell[0]+d[0]*k,cell[1]+d[1]*k) for k in range(L2+1)])
            starts.append((e,d))
        if lab=='POWER':
            return
        fails=[]
        tree=set([starts[0][0]]); s.node[starts[0][0]]=net
        rest=list(range(1,len(starts)))
        while rest:
            # el mas cercano al arbol
            rest.sort(key=lambda i:min(abs(starts[i][0][0]-t[0])+abs(starts[i][0][1]-t[1]) for t in tree))
            i=rest.pop(0); st=starts[i][0]
            path=s.astar(net,st,tree)
            if path is None: fails.append(i); continue
            s.commit(net,path); tree|=set(path)
        return [P[i] for i in fails]
    def mark(s,net,cells):
        for c in cells: s.node[c]=net
    def astar(s,net,start,goals):
        W,H=C(s.W),C(s.H)
        if start in goals: return [start]
        gl=list(goals)
        def h(c): return min(abs(c[0]-g[0])+abs(c[1]-g[1]) for g in gl[:200])
        pq=[(h(start),0,start,None,None)]; best={(start,None):0}; prev={}
        n=0
        while pq:
            f,g,c,d,par=heapq.heappop(pq); n+=1
            if n>600000: return None
            if c in goals and c!=start:
                path=[c]; k=(c,d)
                while k in prev: k=prev[k]; path.append(k[0])
                return path[::-1]
            crossing=(c in s.oh and s.oh[c]!=net) or (c in s.ov and s.ov[c]!=net)
            for nd in ((1,0),(-1,0),(0,1),(0,-1)):
                if d and nd==(-d[0],-d[1]): continue
                if crossing and nd!=d: continue
                nc=(c[0]+nd[0],c[1]+nd[1])
                if not(2<=nc[0]<=W and 2<=nc[1]<=H): continue
                if nc in s.blocked: continue
                if nc not in goals:
                    nn=s.node.get(nc)
                    if nn is not None: continue
                horiz=nd[1]==0
                if horiz and nc in s.oh and s.oh[nc]!=net: continue
                if (not horiz) and nc in s.ov and s.ov[nc]!=net: continue
                if nc in goals and ((nc in s.oh and s.oh[nc]!=net) or (nc in s.ov and s.ov[nc]!=net)): continue
                cost=g+1+(6 if d and nd!=d else 0)+(4 if ((nc in s.oh) or (nc in s.ov)) else 0)
                k=(nc,nd)
                if cost<best.get(k,1e9):
                    best[k]=cost; prev[k]=(c,d); heapq.heappush(pq,(cost+h(nc),cost,nc,nd,c))
        return None
    def commit(s,net,path):
        # segmentos
        pts=[path[0]]
        for i in range(1,len(path)-1):
            a,b,c=path[i-1],path[i],path[i+1]
            if (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]): pts.append(b)
        pts.append(path[-1])
        for a,b in zip(pts,pts[1:]):
            s.wire(net,a,b)
            if a[1]==b[1]:
                for x in range(min(a[0],b[0]),max(a[0],b[0])+1): s.oh[(x,a[1])]=net
            else:
                for y in range(min(a[1],b[1]),max(a[1],b[1])+1): s.ov[(a[0],y)]=net
        for p in pts: s.node[p]=net
    def label(s,net,cell,d):
        ang={(-1,0):180,(1,0):0,(0,-1):90,(0,1):270}[d]
        just={180:'right',0:'left',90:'left',270:'right'}[ang]
        s.labels.append((net,cell))
        s.items.append(f'(label "{net}" (at {cell[0]*G:.2f} {cell[1]*G:.2f} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid "{U()}"))')
    def text(s,t,x,y,size=1.5):
        t=t.replace('"',"'")
        s.items.append(f'(text "{t}" (exclude_from_sim no) (at {x} {y} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid "{U()}"))')
    def finish(s):
        # dividir segmentos en puntos T y poner uniones
        for net,segs in s.segs.items():
            pts=set(p for sg in segs for p in sg)
            out=[]
            for a,b in segs:
                if a==b: continue
                inner=[p for p in pts if p not in(a,b) and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) and (a[0]==b[0]==p[0] or a[1]==b[1]==p[1])]
                ch=sorted([a]+inner+[b],key=lambda p:abs(p[0]-a[0])+abs(p[1]-a[1]))
                out+=list(zip(ch,ch[1:]))
            s.segs[net]=out
            deg={}
            for a,b in out:
                deg[a]=deg.get(a,0)+1; deg[b]=deg.get(b,0)+1
            for p,k in deg.items():
                if k>=3: s.items.append(f'(junction (at {p[0]*G:.2f} {p[1]*G:.2f}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
            for a,b in out:
                s.items.append(f'(wire (pts (xy {a[0]*G:.2f} {a[1]*G:.2f}) (xy {b[0]*G:.2f} {b[1]*G:.2f})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    def save(s,path):
        libs='\n'.join(dump(v,1) for v in s.libs.values())
        out=f'''(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0") (uuid "{s.root}") (paper "A3")
(title_block (title "{s.title}") (date "2026-11-12") (rev "V2-B") (company "Seguidor de Linea V2") (comment 1 "Rama seguidor-caseroV2. Cables reales. Pendiente de revision de Alan."))
(lib_symbols
{libs}
)
'''+'\n'.join(s.items)+'\n(sheet_instances (path "/" (page "1")))\n)\n'
        open(path,'w').write(out)
        json.dump(dict(esperado=s.esperado,nc=s.nc),open(path+'.esperado.json','w'),ensure_ascii=False)
    def build(s,power_nets,label_nets=()):
        """power_nets: {net: lib_id}. label_nets: nets que llevan ademas etiqueta en cada pin (interfaz entre placas)."""
        fallos={}
        order=sorted([n for n in s.pins if n not in power_nets],key=lambda n:(len(s.pins[n])>3, len(s.pins[n])))
        # primero simbolos de alimentacion (stub + simbolo)
        for n,lid in power_nets.items():
            for cell,d,ref,num in s.pins.get(n,[]):
                L2=s.stub[(ref,num)]
                e=(cell[0]+d[0]*L2,cell[1]+d[1]*L2)
                s.wire(n,cell,e); s.mark(n,[(cell[0]+d[0]*k,cell[1]+d[1]*k) for k in range(L2+1)])
                for k in range(1,L2+1): s.blocked.add((cell[0]+d[0]*k,cell[1]+d[1]*k))
                s.pwr(lid,e,d)
                for k in range(L2+1,L2+4):
                    s.blocked.add((cell[0]+d[0]*k,cell[1]+d[1]*k))
                    for q in(-1,1): s.blocked.add((cell[0]+d[0]*k+d[1]*q,cell[1]+d[1]*k+d[0]*q))
        for n in order:
            f=s.route(n)
            if f: fallos[n]=f
        for n,f in fallos.items():
            for cell,d,ref,num in f:
                e=(cell[0]+d[0]*s.stub[(ref,num)],cell[1]+d[1]*s.stub[(ref,num)])
                if (cell,e) not in s.segs.get(n,[]): s.wire(n,cell,e)
                s.label(n,e,d)
            # tambien etiqueta en un punto del arbol principal
            cell,d,ref,num=s.pins[n][0]; L2=s.stub[(ref,num)]; s.label(n,(cell[0]+d[0]*L2,cell[1]+d[1]*L2),d)
        # nombre explicito para cada red (asi la PCB recibe el mismo nombre): etiqueta en el extremo del primer pin
        con_etq=set(n for n,_ in s.labels)
        for n in s.pins:
            if n in power_nets or n in con_etq or n in label_nets: continue
            cell,d,ref,num=s.pins[n][0]; s.label(n,cell,d)
        for n in label_nets:
            if n in s.pins and n not in fallos and n not in power_nets:
                for cell,d,ref,num in s.pins[n]:
                    if ref.startswith('J'): s.label(n,cell,d)
        s.finish()
        return fallos
def verificar(path):
    """Rehace la conectividad desde el archivo (cables, pines, etiquetas, simbolos de poder) y la compara con lo esperado."""
    o=parse(open(path).read()); E=json.load(open(path+'.esperado.json'))
    libs={s[1].strip('"'):s for s in find(o,'lib_symbols')[0][1:]}
    par={}
    def f(x):
        while par.setdefault(x,x)!=x: par[x]=par[par[x]]; x=par[x]
        return x
    def un(a,b): par[f(a)]=f(b)
    R=lambda v: round(float(v)/G)
    wires=[((R(find(w,'pts')[0][1][1]),R(find(w,'pts')[0][1][2])),(R(find(w,'pts')[0][2][1]),R(find(w,'pts')[0][2][2]))) for w in find(o,'wire')]
    pinpts={}
    for sy in find(o,'symbol'):
        lid=find(sy,'lib_id')[0][1].strip('"'); at=find(sy,'at')[0]; x,y=float(at[1]),float(at[2])
        ref=[p for p in find(sy,'property') if p[1]=='"Reference"'][0][2].strip('"')
        val=[p for p in find(sy,'property') if p[1]=='"Value"'][0][2].strip('"')
        for p in pins(libs[lid]):
            pt=(R(x+p['x']),R(y-p['y']))
            pinpts[(ref,p['num'])]=pt
            if ref.startswith('#PWR'): un(pt,'NET:'+val)
    for a,b in wires:
        un(a,b)
    labpts=[(R(find(l,'at')[0][1]),R(find(l,'at')[0][2])) for l in find(o,'label')]
    allpts=set(pinpts.values())|set(p for w in wires for p in w)|set(labpts)
    for a,b in wires:
        for p in allpts:
            if (a[0]==b[0]==p[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1])) or (a[1]==b[1]==p[1] and min(a[0],b[0])<=p[0]<=max(a[0],b[0])): un(p,a)
    for l in find(o,'label'):
        at=find(l,'at')[0]; un((R(at[1]),R(at[2])),'NET:'+l[1].strip('"'))
    grp={}
    for ref,num,net in E['esperado']: grp.setdefault(net,set()).add(f(pinpts[(ref,num)]))
    err=[]
    for net,g in grp.items():
        if len(g)>1: err.append(f'red {net} partida en {len(g)} pedazos')
    inv={}
    for net,g in grp.items():
        for x in g: inv.setdefault(x,set()).add(net)
    for x,ns in inv.items():
        if len(ns)>1: err.append(f'corto entre {sorted(ns)}')
    for ref,num in E['nc']:
        p=f(pinpts[(ref,num)])
        if p in inv: err.append(f'pin NC {ref}.{num} toca {inv[p]}')
    return err
