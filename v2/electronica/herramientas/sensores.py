from gen import *
s=Sch('sensores','Seguidor V2 - PCB de sensores (12 TCRT5000 + CD74HC4067)')
G=2.54
def P(n): return round(n/G)*G
s.text('12 SENSORES TCRT5000: LED (A->CATH) y fototransistor (COLL->E)',P(15),P(15),2)
s.text('LED: +3V3 -> 330 ohm -> A ; CATH -> EMIT_K (colector de Q1). Salida: COLL -> SENn con pull-up 10k a +3V3; E -> GND',P(15),P(21))
for i in range(12):
    n=i+1; col=i%4; row=i//4
    x=P(35+col*70); y=P(45+row*45)
    s.add('Device:R',f'R{n}','330',x-P(22),y,{'1':'+3V3','2':f'LEDA{n}'})
    s.add('Simbolos:TCRT5000',f'OP{n}','TCRT5000',x,y,{'A':f'LEDA{n}','CATH':'EMIT_K','COLL':f'SEN{n}','E':'GND'})
    s.add('Device:R',f'R{12+n}','10k',x+P(22),y,{'1':'+3V3','2':f'SEN{n}'})
s.text('MULTIPLEXOR CD74HC4067 (modulo)',P(300),P(15),2)
mux={'VCC':'+3V3','GND':'GND','EN':'GND','S0':'S0','S1':'S1','S2':'S2','S3':'S3','SIG':'SIG'}
for i in range(12): mux[f'C{i}']=f'SEN{i+1}'
s.add('Simbolos:HC4067_BREAKOUT_BOARD','U1','Modulo CD74HC4067',P(345),P(110),mux)
s.text('C12-C15 sin usar (X). EN a GND = siempre habilitado.',P(300),P(200))
s.add('Device:C','C1','100nF',P(390),P(60),{'1':'+3V3','2':'GND'})
s.text('CONTROL DE EMISORES (2N2222, E-B-C)',P(15),P(195),2)
s.add('Device:R','R25','1k',P(30),P(220),{'1':'EMIT_EN','2':'BASE_Q1'})
s.add('Device:R','R26','10k',P(45),P(230),{'1':'BASE_Q1','2':'GND'})
s.add('Transistor_BJT:PN2222A','Q1','2N2222 (H331, E-B-C)',P(65),P(225),{'1':'GND','2':'BASE_Q1','3':'EMIT_K'})
s.text('EMIT_EN alto = LED encendidos. R26 los mantiene apagados si el cable se desconecta.',P(15),P(245))
s.text('CABLE A PCB PRINCIPAL (8 hilos, mismo orden que J6 de la principal)',P(130),P(195),2)
s.add('Connector_Generic:Conn_01x08','J1','A placa principal',P(170),P(220),{'1':'+3V3','2':'GND','3':'S0','4':'S1','5':'S2','6':'S3','7':'SIG','8':'EMIT_EN'})
x=P(230)
for n in ['+3V3','GND']:
    s.flag(n,x,P(230)); x+=P(20)
s.save('/home/claude/gen/sensores.kicad_sch')
