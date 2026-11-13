from gen import *
s=Sch('principal','Seguidor V2 - PCB principal (ESP32, DRV8833, 2x MP1584, ventilador)')
G=2.54
def P(n): return round(n/G)*G
# --- Alimentacion (arriba izquierda)
s.text('ALIMENTACION: LiPo 2S (externa) -> J1 -> F1 PTC -> J2/KCD1 (externo) -> VBAT_SW',P(20),P(20),2)
s.add('Device:Battery','BT1','LiPo 2S 7.4V (EXTERNA, cable JST-RC)',P(30),P(45),{'1':'VBAT_RAW','2':'GND'},board=False)
s.add('Connector_Generic:Conn_01x02','J1','Bateria (conector en PCB)',P(55),P(42),{'1':'VBAT_RAW','2':'GND'})
s.add('Device:Polyfuse','F1','PTC reseteable (valor pendiente P-V2-03)',P(75),P(45),{'1':'VBAT_RAW','2':'VBAT_F'})
s.add('Switch:SW_SPST','SW1','KCD1 rojo (EXTERNO, en chasis)',P(100),P(40),{'1':'VBAT_F','2':'VBAT_SW'},board=False)
s.add('Connector_Generic:Conn_01x02','J2','Interruptor KCD1 (conector en PCB)',P(100),P(55),{'1':'VBAT_F','2':'VBAT_SW'})
s.add('Device:C_Polarized','C1','470uF 16V',P(125),P(45),{'1':'VBAT_SW','2':'GND'})
s.add('Device:R','R1','100k',P(140),P(45),{'1':'VBAT_SW','2':'VBAT_SENSE'})
s.add('Device:R','R2','33k',P(150),P(45),{'1':'VBAT_SENSE','2':'GND'})
s.add('Device:C','C3','100nF',P(160),P(45),{'1':'VBAT_SENSE','2':'GND'})
s.text('Divisor: 8.4 V -> 2.08 V en GPIO36 (VP)',P(135),P(58))
# --- Reguladores
s.text('REGULADORES MP1584 (modulos)',P(20),P(75),2)
s.add('Simbolos:MP1584module','U1','MP1584 ajustado a 5.0 V',P(45),P(95),{'IN+':'VBAT_SW','IN-':'GND','OUT+':'+5V','OUT-':'GND'})
s.add('Diode:1N5822','D2','1N5822 (aisla USB / 5V)',P(85),P(100),{'2':'+5V','1':'ESP_5V'})
s.add('Simbolos:MP1584module','U2','MP1584 ajustado a 6.0 V (motores)',P(45),P(125),{'IN+':'VBAT_SW','IN-':'GND','OUT+':'+6V_MOT','OUT-':'GND'})
s.add('Device:C_Polarized','C2','470uF 16V',P(85),P(125),{'1':'+6V_MOT','2':'GND'})
# --- ESP32
s.text('ESP32 DevKit 30 pines',P(185),P(75),2)
esp={'15':'ESP_5V','16':'+3V3','14':'GND','17':None,'1':'EN','2':'VBAT_SENSE','4':'SIG','7':'S3','8':'S0','9':'S1','10':'S2',
 '11':'CAL','13':'EMIT_EN','20':'START','21':'DRV_SLEEP','22':'FAN_PWM','25':'AIN1','26':'AIN2','29':'BIN1','30':'BIN2'}
s.add('Simbolos:ESP32-DevKit-USB-C','A1','ESP32 DevKit 30p USB-C',P(210),P(115),esp)
s.add('Switch:SW_Push','SW2','START (12x12 mm)',P(170),P(160),{'1':'START','2':'GND'})
s.add('Switch:SW_Push','SW3','CAL (6x6 mm)',P(200),P(160),{'1':'CAL','2':'GND'})
s.add('Switch:SW_Push','SW4','RESET (6x6 mm)',P(230),P(160),{'1':'EN','2':'GND'})
s.text('Botones a GND; START y CAL usan pull-up interno del ESP32',P(165),P(172))
# --- Motores
s.text('MOTORES: DRV8833 (modulo)',P(280),P(20),2)
s.add('Simbolos:DRV8833','U3','Modulo DRV8833',P(300),P(45),{'10':'+6V_MOT','9':'GND','7':'AIN1','8':'AIN2','11':'BIN1','12':'BIN2','1':'DRV_SLEEP',
 '2':'MOTL_A','3':'MOTL_B','4':'MOTR_A','5':'MOTR_B'})
s.text('ULT (nFAULT) sin conectar (P13). Puente J1 del modulo abierto.',P(280),P(62))
s.add('Connector_Generic:Conn_01x02','J3','Motor izquierdo (conector)',P(345),P(35),{'1':'MOTL_A','2':'MOTL_B'})
s.add('Device:C','C4','100nF',P(360),P(37),{'1':'MOTL_A','2':'MOTL_B'})
s.add('Motor:Motor_DC','M1','N20 izquierdo (EXTERNO)',P(380),P(37),{'1':'MOTL_A','2':'MOTL_B'},board=False)
s.add('Connector_Generic:Conn_01x02','J4','Motor derecho (conector)',P(345),P(65),{'1':'MOTR_A','2':'MOTR_B'})
s.add('Device:C','C5','100nF',P(360),P(67),{'1':'MOTR_A','2':'MOTR_B'})
s.add('Motor:Motor_DC','M2','N20 derecho (EXTERNO)',P(380),P(67),{'1':'MOTR_A','2':'MOTR_B'},board=False)
# --- Ventilador
s.text('VENTILADOR 4010 12 V: interruptor de lado bajo',P(280),P(95),2)
s.add('Device:R','R4','100',P(290),P(120),{'1':'FAN_PWM','2':'FAN_G'})
s.add('Device:R','R5','10k',P(300),P(130),{'1':'FAN_G','2':'GND'})
s.add('Transistor_FET:IRLZ44N','Q1','IRLZ44N',P(320),P(125),{'1':'FAN_G','2':'FAN_SW','3':'GND'})
s.add('Diode:1N5822','D1','1N5822 (rueda libre)',P(340),P(110),{'1':'VBAT_SW','2':'FAN_SW'})
s.add('Connector_Generic:Conn_01x02','J5','Ventilador (conector)',P(360),P(120),{'1':'VBAT_SW','2':'FAN_SW'})
s.add('Motor:Fan','M3','Ventilador 4010 12V (EXTERNO)',P(385),P(122),{'1':'VBAT_SW','2':'FAN_SW'},board=False)
# --- Cable a sensores
s.text('CABLE A PCB DE SENSORES (8 hilos)',P(280),P(155),2)
s.add('Connector_Generic:Conn_01x08','J6','A placa de sensores',P(320),P(175),{'1':'+3V3','2':'GND','3':'S0','4':'S1','5':'S2','6':'S3','7':'SIG','8':'EMIT_EN'})
# --- PWR_FLAG
x=P(30)
for n in ['VBAT_SW','+5V','+6V_MOT','ESP_5V','+3V3','GND']:
    s.flag(n,x,P(200)); x+=P(20)
s.text('PWR_FLAG: solo indican al ERC que la red tiene fuente. No son piezas.',P(20),P(212))
s.text('Simbolos marcados EXTERNO: on_board=no (no tienen huella; se conectan por cable al conector Jx).',P(20),P(218))
s.save('/home/claude/gen/principal.kicad_sch')
