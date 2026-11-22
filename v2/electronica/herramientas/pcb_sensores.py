from pcb import *
b=Board('/mnt/user-data/uploads/KiCAD/Esquemas V2/sensores/sensores.kicad_pcb','sensores.kicad_sch','sensores.kicad_sch.esperado.json','PCB sensores')
b.edge(96,56)
RV='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical'
TC={'1':'COLL','2':'E','3':'A','4':'CATH'}   # huella oficial Vishay -> pines del simbolo de Alan
for i in range(12):
    x=5.5+i*7.6
    b.place(f'OP{i+1}','OptoDevice:Vishay_TCRT5000','TCRT5000',x,50,90,pinmap=TC)
    b.place(f'R{i+1}',RV,'220',x+1.5,36.5,90)
    b.place(f'R{13+i}',RV,'10k',x+4.5,29.5,90)
b.place('Q1','Package_TO_SOT_THT:TO-92_Inline_Wide','2N2222',58,17)
b.place('R25',RV,'470',68,17); b.place('R26',RV,'10k',75,17)
b.place('C1','Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm','100nF',82,17)
b.place('J1','Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical','A principal',60,5,90)
b.rect(3,3,47,24); b.note('U1 CD74HC4067 (modulo 40x20 mm UNIT): SIN HUELLA APROBADA - espacio reservado',4,13)
b.note('Colocacion PRELIMINAR (13 nov). Sin pistas. Sensores: cara hacia el piso por definir.',1,54.5)
print(b.check()); b.save('sensores.kicad_pcb')
