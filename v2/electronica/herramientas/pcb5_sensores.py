from pcb2 import *
from ruteo2 import route_nc
import math, sys
W,H=96,59
R=90.0; d=7.7/R; cx=48; y0=13; RE=R+13
b=Board('/mnt/user-data/uploads/KiCAD/Esquemas V2/sensores/sensores.kicad_pcb','sensores.kicad_sch','sensores.kicad_sch.esperado.json','PCB sensores',ox=round((297-W)/2,1),oy=round((210-H)/2,1))
b.W,b.H=W,H
ccy=y0+R; yc=ccy-math.sqrt(RE**2-cx**2)   # y donde el arco toca los costados
X=lambda v: round(b.ox+v,3); Y=lambda v: round(b.oy+v,3)
def ln(x0,y0_,x1,y1): b.extra.append(f'(gr_line (start {X(x0)} {Y(y0_)}) (end {X(x1)} {Y(y1)}) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "{U()}"))')
b.extra.append(f'(gr_arc (start {X(0)} {Y(yc)}) (mid {X(cx)} {Y(ccy-RE)}) (end {X(W)} {Y(yc)}) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "{U()}"))')
ln(W,yc,W,H); ln(W,H,0,H); ln(0,H,0,yc)
b.inside=lambda x,y: min(RE-math.hypot(x-cx,y-ccy),x,W-x,H-y)
RV='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical'
def put(ref,lid,val,tx,ty,rot,center,**k):
    c,s=math.cos(math.radians(rot)),math.sin(math.radians(rot))
    lx,ly=center
    if k.get('side')=='B': ly=-ly
    ox=tx-(lx*c+ly*s); oy=ty-(-lx*s+ly*c)
    b.place(ref,lid,val,ox,oy,rot,**k)
R220,R10K=R+7.5,R-12
for k in range(12):
    th=(k-5.5)*d; deg=math.degrees(th)
    def at(r): return cx+r*math.sin(th), ccy-r*math.cos(th)
    x,y=at(R); put(f'OP{k+1}','OptoDevice:Vishay_TCRT5000','TCRT5000',x,y,90-deg,(2.75,1.27),side='B',solder='top')
    if k in(0,11):
        th2=th*0.9; x,y=cx+R220*math.sin(th2), ccy-R220*math.cos(th2); put(f'R{k+1}',RV,'220',x,y,90-math.degrees(th2),(1.27,0))
    else:
        x,y=at(R220); put(f'R{k+1}',RV,'220',x,y,90-deg,(1.27,0))
    x,y=at(R10K); put(f'R{13+k}',RV,'10k',x,y,90-deg,(1.27,0))
MUXY=float(sys.argv[2]) if len(sys.argv)>2 else 45
put('U1','HC4067:ANALOG_MUX_BREAKOUT_HC4067','CD74HC4067',48,MUXY,180,(0,0),solder='bottom')
b.place('Q1','Package_TO_SOT_THT:TO-92_Inline_Wide','2N2222',6,53)
b.place('R25',RV,'470',14,55.5); b.place('R26',RV,'10k',20,55.5)
b.place('C1','Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm','100nF',19,46)
b.place('J1','Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical','A principal',72,55,90,solder='bottom')
bad=[]
for a,A in b.boxes:
    for (px,py) in ((A[0],A[1]),(A[2],A[1]),(A[0],A[3]),(A[2],A[3])):
        if b.inside(px-b.ox,py-b.oy)<0.5: bad.append(a); break
for i,(a,A) in enumerate(b.boxes):
    for c2,B2 in b.boxes[i+1:]:
        if A[0]<B2[2] and B2[0]<A[2] and A[1]<B2[3] and B2[1]<A[3]: bad.append(a+'~'+c2)
print('choques',bad)
if len(sys.argv)>1 and sys.argv[1]=='r':
    f,conf,nv,ns=route_nc(b,power={'GND','+5V'},via_cost=float(sys.argv[4]) if len(sys.argv)>4 else 25,iters=int(sys.argv[3]) if len(sys.argv)>3 else 170,pm=0.15,npm=0.3)
    print('CONFLICTOS',conf); print('FALLAS',f,'vias',nv,'segmentos',ns)
    o=sys.argv[5] if len(sys.argv)>5 else 'sensores3'; b.save(o+'.kicad_pcb'); json.dump(dict(fallas=f,vias=nv,seg=ns),open(o+'_ruteo.json','w'))
