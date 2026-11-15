from ruteo import *

R7='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'; CD='Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
CP='Capacitor_THT:CP_Radial_D8.0mm_P3.50mm'; H2='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'; DD='RobotCasero:D_DO-201AD_P20.32mm_Taladro1.3'
Esq.FP=dict(U1='MP1584:MP1584module',U2='MP1584:MP1584module',C1=CP,C2=CP,D1=DD,D2=DD,R1=R7,R2=R7,R4=R7,R5=R7,C3=CD,C4=CD,C5=CD,
 F1='Fuse:Fuse_BelFuse_0ZRE0150FF_L23.4mm_W5.3mm',J1=H2,J2=H2,J3=H2,J4=H2,J5=H2,J6='Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical',
 U3='DRV8833:DRV8833',Q1='Package_TO_SOT_THT:TO-220-3_Vertical',A1='ESP32:ESP32-DevKit-USB-C',SW2='Button_Switch_THT:SW_PUSH-12mm',SW3='Button_Switch_THT:SW_PUSH_6mm',SW4='Button_Switch_THT:SW_PUSH_6mm')
s=Esq('principal','Seguidor V2 - PCB principal',W=405,H=282)
def P(v): return round(v/2.54)*2.54
T=s.text
T('1. ALIMENTACION Y PROTECCION',P(15),P(15),2)
s.add('Device:Battery','BT1','LiPo 2S 7.4V (EXTERNA)',P(25),P(45),{'1':'VBAT_RAW','2':'GND'},board=False)
s.add('Connector_Generic:Conn_01x02','J1','Bateria JST-RC',P(50),P(43),{'1':'VBAT_RAW','2':'GND'})
s.add('Device:Polyfuse','F1','PTC 1.5A >=16V (por comprar)',P(70),P(30),{'1':'VBAT_RAW','2':'VBAT_F'})
s.add('Connector_Generic:Conn_01x02','J2','Interruptor KCD1',P(100),P(43),{'1':'VBAT_F','2':'VBAT_SW'})
s.add('Switch:SW_SPST','SW1','KCD1 rojo (EXTERNO)',P(100),P(25),{'1':'VBAT_F','2':'VBAT_SW'},board=False)
s.add('Device:C_Polarized','C1','470uF 16V',P(130),P(45),{'1':'VBAT_SW','2':'GND'})
T('2. MEDICION DE BATERIA',P(145),P(15),2)
s.add('Device:R','R1','100k',P(155),P(35),{'1':'VBAT_SW','2':'VBAT_SENSE'})
s.add('Device:R','R2','33k',P(155),P(55),{'1':'VBAT_SENSE','2':'GND'})
s.add('Device:C','C3','100nF',P(170),P(55),{'1':'VBAT_SENSE','2':'GND'})
T('3. REGULADORES MP1584',P(15),P(75),2)
s.add('Simbolos:MP1584module','U1','MP1584 -> 5.0 V',P(45),P(95),{'IN+':'VBAT_SW','IN-':'GND','OUT+':'+5V','OUT-':'GND'})
s.add('Diode:1N5822','D2','1N5822',P(90),P(92),{'2':'+5V','1':'ESP_5V'})
s.add('Simbolos:MP1584module','U2','MP1584 -> 6.0 V (motores)',P(45),P(135),{'IN+':'VBAT_SW','IN-':'GND','OUT+':'+6V_MOT','OUT-':'GND'})
s.add('Device:C_Polarized','C2','470uF 16V',P(90),P(140),{'1':'+6V_MOT','2':'GND'})
T('4. ESP32 DevKit 30 pines',P(160),P(80),2)
esp={'15':'ESP_5V','16':'+3V3','14':'GND','17':None,'1':'EN','2':'VBAT_SENSE','4':'SIG','7':'S3','8':'S0','9':'S1','10':'S2',
 '11':'CAL','13':'EMIT_EN','20':'START','21':'DRV_SLEEP','22':'FAN_PWM','25':'AIN1','26':'AIN2','29':'BIN1','30':'BIN2'}
s.add('Simbolos:ESP32-DevKit-USB-C','A1','ESP32 DevKit 30p USB-C',P(200),P(135),esp)
T('5. BOTONES',P(140),P(200),2)
s.add('Switch:SW_Push','SW2','START 12x12',P(150),P(215),{'1':'START','2':'GND'})
s.add('Switch:SW_Push','SW3','CAL 6x6',P(150),P(232),{'1':'CAL','2':'GND'})
s.add('Switch:SW_Push','SW4','RESET 6x6',P(150),P(249),{'1':'EN','2':'GND'})
T('6. DRV8833 Y MOTORES',P(270),P(15),2)
s.add('Simbolos:DRV8833','U3','Modulo DRV8833',P(290),P(55),{'10':'+6V_MOT','9':'GND','7':'AIN1','8':'AIN2','11':'BIN1','12':'BIN2','1':'DRV_SLEEP',
 '2':'MOTL_A','3':'MOTL_B','4':'MOTR_A','5':'MOTR_B'})
s.add('Device:C','C4','100nF',P(325),P(40),{'1':'MOTL_A','2':'MOTL_B'})
s.add('Connector_Generic:Conn_01x02','J3','Motor izq.',P(350),P(38),{'1':'MOTL_A','2':'MOTL_B'})
s.add('Motor:Motor_DC','M1','N20 izq. (EXTERNO)',P(380),P(40),{'1':'MOTL_A','2':'MOTL_B'},board=False)
s.add('Device:C','C5','100nF',P(325),P(75),{'1':'MOTR_A','2':'MOTR_B'})
s.add('Connector_Generic:Conn_01x02','J4','Motor der.',P(350),P(73),{'1':'MOTR_A','2':'MOTR_B'})
s.add('Motor:Motor_DC','M2','N20 der. (EXTERNO)',P(380),P(75),{'1':'MOTR_A','2':'MOTR_B'},board=False)
T('7. VENTILADOR',P(270),P(110),2)
s.add('Device:R','R4','100',P(285),P(150),{'1':'FAN_PWM','2':'FAN_G'})
s.add('Device:R','R5','10k',P(300),P(165),{'1':'FAN_G','2':'GND'})
s.add('Transistor_FET:IRLZ44N','Q1','IRLZ44N',P(320),P(160),{'1':'FAN_G','2':'FAN_SW','3':'GND'})
s.add('Diode:1N5822','D1','1N5822',P(340),P(135),{'1':'VBAT_SW','2':'FAN_SW'})
s.add('Connector_Generic:Conn_01x02','J5','Ventilador',P(360),P(150),{'1':'VBAT_SW','2':'FAN_SW'})
s.add('Motor:Fan','M3','4010 12V (EXTERNO)',P(385),P(152),{'1':'VBAT_SW','2':'FAN_SW'},board=False)
T('8. CABLE A PCB DE SENSORES (9 hilos)',P(255),P(195),2)
s.add('Connector_Generic:Conn_01x09','J6','A sensores',P(300),P(225),{'1':'+3V3','2':'GND','3':'S0','4':'S1','5':'S2','6':'S3','7':'SIG','8':'EMIT_EN','9':'+5V'})
for i,n in enumerate(['VBAT_SW','+5V','+6V_MOT','ESP_5V']):
    s.add('power:PWR_FLAG',f'#FLG0{i+1}','PWR_FLAG',P(30+i*18),P(190),{'1':n})
s.add('power:PWR_FLAG','#FLG05','PWR_FLAG',P(30),P(225),{'1':'GND'})
s.add('power:PWR_FLAG','#FLG06','PWR_FLAG',P(50),P(225),{'1':'+3V3'})
T('PWR_FLAG: solo avisa al ERC que la red tiene fuente; no es pieza. EXTERNO = sin huella, llega por cable a su conector J.',P(15),P(270),1.3)
f=s.build({'GND':'power:GND','+3V3':'power:+3V3'},label_nets=['S0','S1','S2','S3','SIG','EMIT_EN'])
print('fallos',{k:len(v) for k,v in f.items()})
s.save('principal.kicad_sch'); print('verif',verificar('principal.kicad_sch'))
