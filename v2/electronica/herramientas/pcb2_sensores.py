from pcb2 import *
from ruteo2 import route_nc
import math
W,H=96,88
b=Board('/mnt/user-data/uploads/KiCAD/Esquemas V2/sensores/sensores.kicad_pcb','sensores.kicad_sch','sensores.kicad_sch.esperado.json','PCB sensores',ox=round((297-W)/2,1),oy=round((210-H)/2,1))
b.edge(W,H)
RV='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical'
R=90.0; d=7.7/R; cx=48; y0=15
def put(ref,lid,val,tx,ty,rot,center,**k):
    c,s=math.cos(math.radians(rot)),math.sin(math.radians(rot))
    lx,ly=center
    if k.get('side')=='B': ly=-ly
    ox=tx-(lx*c+ly*s); oy=ty-(-lx*s+ly*c)
    b.place(ref,lid,val,ox,oy,rot,**k)
for k in range(12):
    th=(k-5.5)*d; deg=math.degrees(th)
    def at(r): return cx+r*math.sin(th), y0+R-r*math.cos(th)
    x,y=at(R); put(f'OP{k+1}','OptoDevice:Vishay_TCRT5000','TCRT5000',x,y,90-deg,(2.75,1.27),side='B',solder='top')
    if k in(0,11):
        th2=th*0.9; x,y=cx+(R+7.5)*math.sin(th2), y0+R-(R+7.5)*math.cos(th2); put(f'R{k+1}',RV,'220',x,y,90-math.degrees(th2),(1.27,0))
    else:
        x,y=at(R+7.5); put(f'R{k+1}',RV,'220',x,y,90-deg,(1.27,0))
    x,y=at(R-12); put(f'R{13+k}',RV,'10k',x,y,90-deg,(1.27,0))
put('U1','HC4067:ANALOG_MUX_BREAKOUT_HC4067','CD74HC4067',48,62,180,(0,0),solder='bottom')
b.place('Q1','Package_TO_SOT_THT:TO-92_Inline_Wide','2N2222',6,77)
b.place('R25',RV,'470',16,82); b.place('R26',RV,'10k',22,82)
b.place('C1','Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm','100nF',76,81)
b.place('J1','Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical','A principal',38,83,90,solder='bottom')
print('choques',b.check())
if __name__=='__main__':
    POW={'GND','+5V'}
    f,conf,nv,ns=route_nc(b,power=POW,iters=170,pm=0.15,npm=0.3)
    print('CONFLICTOS',conf); print('FALLAS',f,'vias',nv,'segmentos',ns)
    b.save('sensores.kicad_pcb')
