from ruteo import *

RV='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical'
Esq.FP={**{f'R{i}':RV for i in range(1,27)},**{f'OP{i}':'OptoDevice:Vishay_TCRT5000' for i in range(1,13)},
 'Q1':'Package_TO_SOT_THT:TO-92_Inline_Wide','C1':'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm','J1':'Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical','U1':'HC4067:ANALOG_MUX_BREAKOUT_HC4067'}
s=Esq('sensores','Seguidor V2 - PCB de sensores',W=405,H=282)
def P(v): return round(v/2.54)*2.54
T=s.text
T('1. DOCE SENSORES TCRT5000 (LED: +5V -> 220 -> A, CATH -> EMIT_K ; salida: COLL -> SENn con pull-up 10k a +3V3 ; E -> GND)',P(15),P(15),1.6)
for i in range(12):
    n=i+1; col=i%3; row=i//3
    x=P(45+col*85); y=P(40+row*45)
    s.add('Device:R',f'R{n}','220',x-P(22),y-P(5),{'1':'+5V','2':f'LEDA{n}'})
    s.add('Simbolos:TCRT5000',f'OP{n}','TCRT5000',x,y,{'3':f'LEDA{n}','4':'EMIT_K','1':f'SEN{n}','2':'GND'})
    s.add('Device:R',f'R{12+n}','10k',x+P(20),y-P(8),{'1':'+3V3','2':f'SEN{n}'})
T('2. MULTIPLEXOR CD74HC4067 (modulo HW-178)',P(300),P(15),1.8)
mux={'VCC':'+3V3','GND':'GND','EN':'GND','S0':'S0','S1':'S1','S2':'S2','S3':'S3','SIG':'SIG'}
for i in range(12): mux[f'C{i}']=f'SEN{i+1}'
s.add('Simbolos:HC4067_BREAKOUT_BOARD','U1','Modulo CD74HC4067',P(345),P(115),mux)
s.add('Device:C','C1','100nF',P(390),P(60),{'1':'+3V3','2':'GND'})
T('3. CONTROL DE LOS LED (2N2222, ~200 mA)',P(15),P(222),1.8)
s.add('Device:R','R25','470',P(45),P(250),{'1':'EMIT_EN','2':'BASE_Q1'})
s.add('Device:R','R26','10k',P(65),P(262),{'1':'BASE_Q1','2':'GND'})
s.add('Transistor_BJT:PN2222A','Q1','2N2222 E-B-C',P(85),P(250),{'1':'GND','2':'BASE_Q1','3':'EMIT_K'})
T('4. CABLE A PCB PRINCIPAL (9 hilos, mismo orden que J6)',P(150),P(222),1.8)
s.add('Connector_Generic:Conn_01x09','J1','A principal',P(250),P(250),{'1':'+3V3','2':'GND','3':'S0','4':'S1','5':'S2','6':'S3','7':'SIG','8':'EMIT_EN','9':'+5V'})
s.add('power:PWR_FLAG','#FLG01','PWR_FLAG',P(390),P(250),{'1':'GND'})
s.add('power:PWR_FLAG','#FLG02','PWR_FLAG',P(375),P(250),{'1':'+3V3'})
s.add('power:PWR_FLAG','#FLG03','PWR_FLAG',P(360),P(250),{'1':'+5V'})
f=s.build({'GND':'power:GND','+3V3':'power:+3V3','+5V':'power:+5V'},label_nets=['S0','S1','S2','S3','SIG','EMIT_EN'])
print('fallos',{k:len(v) for k,v in f.items()})
s.save('sensores.kicad_sch'); print('verif',verificar('sensores.kicad_sch'))
