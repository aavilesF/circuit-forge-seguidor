from pcb2 import *
W,H=96,84
b=Board('/mnt/user-data/uploads/KiCAD/Esquemas V2/principal/principal.kicad_pcb','principal.kicad_sch','principal.kicad_sch.esperado.json','PCB principal',ox=round((297-W)/2,1),oy=round((210-H)/2,1))
b.edge(W,H)
R7='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'; CD='Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
CP='Capacitor_THT:CP_Radial_D8.0mm_P3.50mm'; H2='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'; DD='Diode_THT:D_DO-201AD_P15.24mm_Horizontal'
def P(*a,**k):
    k.setdefault('solder','both'); b.place(*a,**k)
BOT=dict(solder='bottom')
P('U1','MP1584:MP1584module','MP1584 5V',14,12,**BOT)
P('U2','MP1584:MP1584module','MP1584 6V',14,33,**BOT)
P('C1',CP,'470uF',5,47,**BOT); P('C2',CP,'470uF',15,47,**BOT)
P('D2',DD,'1N5822',4,56)
P('F1','Fuse:Fuse_BelFuse_0ZRE0150FF_L23.4mm_W5.3mm','PTC 1.5A',9,64)
P('J1',H2,'BAT',4,72,**BOT); P('J2',H2,'KCD1',10,72,**BOT)
P('R1',R7,'100k',25,44); P('R2',R7,'33k',25,48); P('C3',CD,'100nF',25,52)
P('J6','Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical','A sensores',27.5,10,**BOT)
P('A1','ESP32:ESP32-DevKit-USB-C','ESP32',36,8,**BOT)
P('U3','DRV8833:DRV8833','DRV8833',76,18,rot=90,**BOT)
P('J3',H2,'MOT_I',87,25,**BOT); P('J4',H2,'MOT_D',92,25,**BOT)
P('C4',CD,'100nF',67,30); P('C5',CD,'100nF',79,30)
P('Q1','Package_TO_SOT_THT:TO-220-3_Vertical','IRLZ44N',70,40)
P('R4',R7,'100',66,46); P('R5',R7,'10k',66,50)
P('D1',DD,'1N5822',66,57); P('J5',H2,'FAN',85,47,**BOT)
P('SW2','Button_Switch_THT:SW_PUSH-12mm','START',38,64,**BOT)
P('SW3','Button_Switch_THT:SW_PUSH_6mm','CAL',56,64,**BOT)
P('SW4','Button_Switch_THT:SW_PUSH_6mm','RESET',56,74,**BOT)
print('choques',b.check())
POW={'GND','/VBAT_RAW','/VBAT_F','/VBAT_SW','/+6V_MOT','/+5V','/ESP_5V','/MOTL_A','/MOTL_B','/MOTR_A','/MOTR_B','/FAN_SW'}
from ruteo2 import route_nc
f,conf,nv,ns=route_nc(b,power=POW,iters=260,pm=0.22,via_cost=35)
print('CONFLICTOS',conf)
print('FALLAS',f,'vias',nv,'segmentos',ns)
b.save('principal.kicad_pcb'); json.dump(dict(fallas=f,vias=nv,seg=ns),open('principal_ruteo.json','w'))
