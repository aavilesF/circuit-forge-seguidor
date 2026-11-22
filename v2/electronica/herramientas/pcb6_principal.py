from pcb2 import *
import sys
W,H=96,74
b=Board('/mnt/user-data/uploads/KiCAD/Esquemas V2/principal/principal.kicad_pcb','principal.kicad_sch','principal.kicad_sch.esperado.json','PCB principal',ox=round((297-W)/2,1),oy=round((210-H)/2,1))
b.edge(W,H)
R7='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'; CD='Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
CP='Capacitor_THT:CP_Radial_D8.0mm_P3.50mm'; H2='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'; DD='RobotCasero:D_DO-201AD_P20.32mm_Taladro1.3'
def P(*a,**k):
    k.setdefault('solder','both'); b.place(*a,**k)
BOT=dict(solder='bottom')
P('U1','MP1584:MP1584module','MP1584 5V',12.7,10,**BOT)
P('U2','MP1584:MP1584module','MP1584 6V',12.7,29.5,**BOT)
P('C1',CP,'470uF',4,44,**BOT); P('C2',CP,'470uF',15,44,**BOT)
P('D2',DD,'1N5822',3,53)
P('F1','Fuse:Fuse_BelFuse_0ZRE0150FF_L23.4mm_W5.3mm','PTC 1.5A',7.6,61)
P('J1',H2,'BAT',3,68,**BOT); P('J2',H2,'KCD1',9,68,**BOT)
P('R1',R7,'100k',25.5,4); P('R2',R7,'33k',25.5,9); P('C3',CD,'100nF',25.5,14)
P('J6','Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical','A sensores',27.5,36,**BOT)
P('A1','ESP32:ESP32-DevKit-USB-C','ESP32',33,27.2,**BOT)
P('SW4','Button_Switch_THT:SW_PUSH_6mm','RESET',39.5,6,**BOT)
P('SW3','Button_Switch_THT:SW_PUSH_6mm','CAL',51,6,**BOT)
P('U3','DRV8833:DRV8833','DRV8833',76,18,rot=90,**BOT)
P('J3',H2,'MOT_I',87,25,**BOT); P('J4',H2,'MOT_D',92,25,**BOT)
P('C4',CD,'100nF',67,30); P('C5',CD,'100nF',79,30)
P('Q1','Package_TO_SOT_THT:TO-220-3_Vertical','IRLZ44N',70,39.5)
P('R4',R7,'100',65,45); P('R5',R7,'10k',65,49)
P('D1',DD,'1N5822',64,54.5); P('J5',H2,'FAN',88,46,**BOT)
P('SW2','Button_Switch_THT:SW_PUSH-12mm','START',63.5,63,**BOT)
print('choques',b.check())
if len(sys.argv)>1:
    POW={'GND','/VBAT_RAW','/VBAT_F','/VBAT_SW','/+6V_MOT','/+5V','/ESP_5V','/MOTL_A','/MOTL_B','/MOTR_A','/MOTR_B','/FAN_SW'}
    from ruteo2 import route_nc
    f,conf,nv,ns=route_nc(b,power=POW,iters=260,pm=0.22,via_cost=float(sys.argv[2]) if len(sys.argv)>2 else 35)
    print('CONFLICTOS',conf); print('FALLAS',f,'vias',nv,'segmentos',ns)
    out=sys.argv[3] if len(sys.argv)>3 else 'principal3'; b.save(out+'.kicad_pcb'); json.dump(dict(fallas=f,vias=nv,seg=ns),open(out+'_ruteo.json','w'))
