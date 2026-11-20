# Esquema de EMERGENCIA UNIFICADO (placa perforada): principal + barra de 8 sensores en UN solo esquema (19 nov 2026).
# Une emergencia_principal.py y emergencia_sensores.py. El cable de 9 hilos (J6 / J1) desaparece: las redes
# S0-S3, SIG, EMIT_EN, +3V3, +5V y GND pasan directo. Los sensores siguen siendo una barra aparte en lo fisico
# (EM-06), pero en el esquema ya no hay conectores intermedios.
# Renumeracion de la parte de sensores (para no chocar con la principal):
#   R1,R2 (100k/33k divisor)  | R3-R10 = 220 ohm LED (antes R1-R8) | R11-R18 = 10k pull-up (antes R9-R16)
#   R19 = 470 (antes R17)     | R20 = 10k base (antes R18)        | C6 = 100 nF del mux (antes C1) | U4 = mux (antes U1)
from ruteo import *
R7='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'; RV='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical'
CD='Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'; CP='Capacitor_THT:CP_Radial_D8.0mm_P3.50mm'
H2='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'; DD='RobotCasero:D_DO-201AD_P20.32mm_Taladro1.3'
Esq.FP=dict(U1='MP1584:MP1584module',U2='MP1584:MP1584module',U3='DRV8833:DRV8833',U4='HC4067:ANALOG_MUX_BREAKOUT_HC4067',
 A1='ESP32:ESP32-DevKit-USB-C',C1=CP,C2=CP,D2=DD,R1=R7,R2=R7,C3=CD,C4=CD,C5=CD,C6=CD,J1=H2,J2=H2,J3=H2,J4=H2,
 SW2='Button_Switch_THT:SW_PUSH-12mm',SW3='Button_Switch_THT:SW_PUSH_6mm',Q1='Package_TO_SOT_THT:TO-92_Inline_Wide',
 **{f'R{i}':RV for i in range(3,21)},**{f'OP{i}':'OptoDevice:Vishay_TCRT5000' for i in range(1,9)})
s=Esq('robot_emergencia_unificado','Seguidor V2 EMERGENCIA - esquema unico',W=580,H=406,paper='A2')
def P(v): return round(v/2.54)*2.54
T=s.text
# ---------------- PARTE PRINCIPAL (igual que principal_emergencia, sin J6) ----------------
T('1. ALIMENTACION (fusible EN LINEA externo, sin PTC)',P(15),P(15),2)
s.add('Device:Battery','BT1','LiPo 2S 7.4V (EXTERNA)',P(25),P(45),{'1':'VBAT_RAW','2':'GND'},board=False)
s.add('Device:Fuse','F2','Fusible en linea 3A (EXTERNO, en el cable)',P(40),P(28),{'1':'VBAT_RAW','2':'VBAT_F'},board=False)
s.add('Connector_Generic:Conn_01x02','J1','Bateria JST-RC',P(60),P(43),{'1':'VBAT_RAW','2':'GND'})
s.add('Connector_Generic:Conn_01x02','J2','Interruptor KCD1',P(100),P(43),{'1':'VBAT_F','2':'VBAT_SW'})
s.add('Switch:SW_SPST','SW1','KCD1 rojo (EXTERNO)',P(100),P(25),{'1':'VBAT_F','2':'VBAT_SW'},board=False)
s.add('Device:C_Polarized','C1','470uF 16V',P(130),P(45),{'1':'VBAT_SW','2':'GND'})
T('2. MEDICION DE BATERIA (8.4 V -> 2.08 V)',P(145),P(15),2)
s.add('Device:R','R1','100k',P(155),P(35),{'1':'VBAT_SW','2':'VBAT_SENSE'})
s.add('Device:R','R2','33k',P(155),P(55),{'1':'VBAT_SENSE','2':'GND'})
s.add('Device:C','C3','100nF',P(170),P(55),{'1':'VBAT_SENSE','2':'GND'})
T('3. REGULADORES MP1584 (ajustar ANTES de soldar: U1=5.0V, U2=6.0V)',P(15),P(75),2)
s.add('Simbolos:MP1584module','U1','MP1584 -> 5.0 V',P(45),P(95),{'IN+':'VBAT_SW','IN-':'GND','OUT+':'+5V','OUT-':'GND'})
s.add('Diode:1N5822','D2','1N5822 (protege el USB)',P(90),P(92),{'2':'+5V','1':'ESP_5V'})
s.add('Simbolos:MP1584module','U2','MP1584 -> 6.0 V (motores)',P(45),P(135),{'IN+':'VBAT_SW','IN-':'GND','OUT+':'+6V_MOT','OUT-':'GND'})
s.add('Device:C_Polarized','C2','470uF 16V',P(90),P(140),{'1':'+6V_MOT','2':'GND'})
T('4. ESP32 DevKit 30 pines (mismos GPIO que el diseno aprobado)',P(160),P(80),2)
esp={'15':'ESP_5V','16':'+3V3','14':'GND','17':None,'2':'VBAT_SENSE','4':'SIG','7':'S3','8':'S0','9':'S1','10':'S2',
 '11':'CAL','13':'EMIT_EN','20':'START','21':'DRV_SLEEP','25':'AIN1','26':'AIN2','29':'BIN1','30':'BIN2'}
s.add('Simbolos:ESP32-DevKit-USB-C','A1','ESP32 DevKit 30p USB-C',P(200),P(135),esp)
T('5. BOTONES (RESET: usar el boton EN del DevKit)',P(140),P(200),2)
s.add('Switch:SW_Push','SW2','START 12x12',P(150),P(215),{'1':'START','2':'GND'})
s.add('Switch:SW_Push','SW3','CAL 6x6',P(150),P(232),{'1':'CAL','2':'GND'})
T('6. DRV8833 Y MOTORES',P(270),P(15),2)
s.add('Simbolos:DRV8833','U3','Modulo DRV8833',P(290),P(55),{'10':'+6V_MOT','9':'GND','7':'AIN1','8':'AIN2','11':'BIN1','12':'BIN2','1':'DRV_SLEEP',
 '2':'MOTL_A','3':'MOTL_B','4':'MOTR_A','5':'MOTR_B'})
s.add('Device:C','C4','100nF',P(325),P(40),{'1':'MOTL_A','2':'MOTL_B'})
s.add('Connector_Generic:Conn_01x02','J3','Motor izq.',P(350),P(38),{'1':'MOTL_A','2':'MOTL_B'})
s.add('Motor:Motor_DC','M1','N20 izq. (EXTERNO)',P(380),P(40),{'1':'MOTL_A','2':'MOTL_B'},board=False)
s.add('Device:C','C5','100nF',P(325),P(75),{'1':'MOTR_A','2':'MOTR_B'})
s.add('Connector_Generic:Conn_01x02','J4','Motor der.',P(350),P(73),{'1':'MOTR_A','2':'MOTR_B'})
s.add('Motor:Motor_DC','M2','N20 der. (EXTERNO)',P(380),P(75),{'1':'MOTR_A','2':'MOTR_B'},board=False)
# ---------------- PARTE DE SENSORES (franja inferior; antes en sensores_emergencia) ----------------
Y0=P(300)
T('7. OCHO TCRT5000 en fila recta, paso 12.7 mm, mirando al piso (LED: +5V -> 220 -> A, K -> EMIT_K ; salida: C -> SENn, pull-up 10k a +3V3 ; E -> GND)',P(15),Y0-P(20),2)
for i in range(8):
    n=i+1; x=P(45+i*50); y=Y0+P(18)
    s.add('Device:R',f'R{2+n}','220',x-P(16),y-P(5),{'1':'+5V','2':f'LEDA{n}'})
    s.add('Simbolos:TCRT5000',f'OP{n}',f'TCRT5000 #{n}',x,y,{'3':f'LEDA{n}','4':'EMIT_K','1':f'SEN{n}','2':'GND'})
    s.add('Device:R',f'R{10+n}','10k',x+P(14),y-P(8),{'1':'+3V3','2':f'SEN{n}'})
T('8. MULTIPLEXOR CD74HC4067 (C0-C7 = sensores 1-8; C8-C15 libres)',P(430),P(100),2)
mux={'VCC':'+3V3','GND':'GND','EN':'GND','S0':'S0','S1':'S1','S2':'S2','S3':'S3','SIG':'SIG'}
for i in range(8): mux[f'C{i}']=f'SEN{i+1}'
s.add('Simbolos:HC4067_BREAKOUT_BOARD','U4','Modulo CD74HC4067',P(510),P(200),mux)
s.add('Device:C','C6','100nF (junto al mux)',P(560),P(120),{'1':'+3V3','2':'GND'})
T('9. ENCENDIDO DE LOS LED (2N2222, 8 x 16 mA = 130 mA)',P(15),P(365),2)
s.add('Device:R','R19','470',P(45),P(385),{'1':'EMIT_EN','2':'BASE_Q1'})
s.add('Device:R','R20','10k',P(65),P(393),{'1':'BASE_Q1','2':'GND'})
s.add('Transistor_BJT:PN2222A','Q1','2N2222 E-B-C',P(85),P(385),{'1':'GND','2':'BASE_Q1','3':'EMIT_K'})
# ---------------- PWR_FLAG ----------------
for i,n in enumerate(['VBAT_SW','+5V','+6V_MOT','ESP_5V']):
    s.add('power:PWR_FLAG',f'#FLG0{i+1}','PWR_FLAG',P(30+i*18),P(190),{'1':n})
s.add('power:PWR_FLAG','#FLG05','PWR_FLAG',P(30),P(225),{'1':'GND'})
s.add('power:PWR_FLAG','#FLG06','PWR_FLAG',P(50),P(225),{'1':'+3V3'})
s.add('power:PWR_FLAG','#FLG07','PWR_FLAG',P(68),P(225),{'1':'VBAT_RAW'})
T('EXTERNO = va fuera de la placa, por cable. Potencia (bateria, KCD1, MP1584, DRV8833, motores) con cable 18-22 AWG; senales con cable fino.',P(15),P(250),1.5)
T('Las redes S0-S3, SIG y EMIT_EN se unen por ETIQUETA (mismo nombre = mismo cable) entre el ESP32 y la barra de sensores. +5V, +3V3 y GND por simbolo de alimentacion.',P(15),P(258),1.5)
T('En fisico la barra de sensores sigue siendo una placa aparte (EM-06): sus 9 hilos son +3V3, GND, S0-S3, SIG, EMIT_EN y +5V (la numeracion ya no es de un conector del esquema).',P(15),P(266),1.5)
T('PWR_FLAG solo avisa al ERC que la red tiene fuente. GPIO23 (antes ventilador) queda libre.',P(15),P(274),1.5)
f=s.build({'GND':'power:GND','+3V3':'power:+3V3','+5V':'power:+5V'},solo_etiqueta=['S0','S1','S2','S3','SIG','EMIT_EN'])
print('fallos',{k:len(v) for k,v in f.items()})
s.save('robot_emergencia_unificado.kicad_sch'); print('verif',verificar('robot_emergencia_unificado.kicad_sch'))
