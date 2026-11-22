import uuid, copy, json, sys
from sx import *
U=lambda: str(uuid.uuid4())
OFF=parse(open('/mnt/user-data/uploads/KiCAD/Esquemas V2/_simbolos_oficiales/simbolos_oficiales.kicad_sch').read())
OFFL={s[1].strip('"'):s for s in find(OFF,'lib_symbols')[0][1:]}
USR=parse(open('/mnt/user-data/uploads/KiCAD/Librerias/Símbolos/Simbolos.kicad_sym').read())
USRL={s[1].strip('"'):s for s in USR[1:] if isinstance(s,list) and s[0]=='symbol'}
K7={}
def k7(lib):
    if lib not in K7:
        L=parse(open(f'/usr/share/kicad/symbols/{lib}.kicad_sym').read())
        K7[lib]={s[1].strip('"'):s for s in L[1:] if isinstance(s,list) and s[0]=='symbol'}
    return K7[lib]
def libsym(lid):
    lib,name=lid.split(':')
    if lib=='Simbolos':
        s=copy.deepcopy(USRL[name]); s[1]=f'"{lid}"'; return s
    s=copy.deepcopy(OFFL[lid])
    ex=find(s,'extends')
    if ex:  # aplanar con la grafica/pines del simbolo padre oficial
        par=ex[0][1].strip('"'); p=copy.deepcopy(k7(lib).get(par) or k7('Device')[par])
        props=find(s,'property')
        body=[e for e in p[2:] if not (isinstance(e,list) and e[0] in('property','extends'))]
        for e in body:
            if isinstance(e,list) and e[0]=='symbol': e[1]=e[1].replace(par,name,1)
        hdr=[e for e in p[2:] if isinstance(e,list) and e[0] in ('pin_names','pin_numbers','exclude_from_sim','in_bom','on_board')]
        body=[e for e in body if e not in hdr]
        s=['symbol',f'"{lid}"']+hdr+props+body
    return s
class Sch:
    def __init__(s,proj,title):
        s.proj=proj; s.title=title; s.root=U(); s.items=[]; s.libs={}; s.conn=[]; s.nflag=0; s.npwr=0
    def add(s,lid,ref,val,x,y,nets,fp='',board=True,nc=()):
        if lid not in s.libs: s.libs[lid]=libsym(lid)
        ls=s.libs[lid]; ps=pins(ls)
        props=[]
        for pr in find(ls,'property'):
            k=pr[1].strip('"'); at=find(pr,'at')[0]
            v={'Reference':ref,'Value':val,'Footprint':fp}.get(k,pr[2].strip('"'))
            hide=any(isinstance(e,list) and e[0]=='hide' for e in pr) or 'hide' in dump(find(pr,'effects')[0] if find(pr,'effects') else []) or k not in('Reference','Value')
            props.append(f'(property "{k}" "{v}" (at {x+float(at[1]):.2f} {y-float(at[2]):.2f} 0) (effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""}))')
        pinl=' '.join(f'(pin "{p["num"]}" (uuid "{U()}"))' for p in ps)
        ob='yes' if board else 'no'
        s.items.append(f'(symbol (lib_id "{lid}") (at {x:.2f} {y:.2f} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board {ob}) (dnp no) (uuid "{U()}") {" ".join(props)} {pinl} (instances (project "{s.proj}" (path "/{s.root}" (reference "{ref}") (unit 1)))))')
        used=set()
        for p in ps:
            key=p['num'] if p['num'] in nets else p['name']
            ex,ey=x+p['x'],y-p['y']
            if p['a'] in (0,180): dx,dy=(-1 if p['x']<0 else 1),0
            else: dx,dy=0,(1 if p['y']<0 else -1)
            if key in nets and nets[key] is None:
                s.conn.append((ref,p['num'],p['name'],'(apilado con otro pin, misma red)')); continue
            if key in nets:
                n=nets[key]
                wx,wy=ex+dx*2.54,ey+dy*2.54
                s.items.append(f'(wire (pts (xy {ex:.2f} {ey:.2f}) (xy {wx:.2f} {wy:.2f})) (stroke (width 0) (type default)) (uuid "{U()}"))')
                ang={(-1,0):180,(1,0):0,(0,-1):90,(0,1):270}[(dx,dy)]
                just={180:'right',0:'left',90:'left',270:'right'}[ang]
                s.items.append(f'(label "{n}" (at {wx:.2f} {wy:.2f} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid "{U()}"))')
                s.conn.append((ref,p['num'] or '(vacío)',p['name'],n))
            else:
                s.items.append(f'(no_connect (at {ex:.2f} {ey:.2f}) (uuid "{U()}"))')
                s.conn.append((ref,p['num'],p['name'],'NC'))
    def flag(s,net,x,y):
        s.nflag+=1; s.add('power:PWR_FLAG',f'#FLG{s.nflag:02d}','PWR_FLAG',x,y,{'1':net})
    def text(s,t,x,y,size=1.5):
        t=t.replace('"',"'")
        s.items.append(f'(text "{t}" (exclude_from_sim no) (at {x} {y} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid "{U()}"))')
    def save(s,path,date='2026-11-12'):
        libs='\n'.join(dump(v,1) for v in s.libs.values())
        out=f'''(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0") (uuid "{s.root}") (paper "A3")
(title_block (title "{s.title}") (date "{date}") (rev "V2-A") (company "Seguidor de Linea V2") (comment 1 "Rama seguidor-caseroV2. Pendiente de revision de Alan."))
(lib_symbols
{libs}
)
'''+'\n'.join(s.items)+f'\n(sheet_instances (path "/" (page "1")))\n)\n'
        open(path,'w').write(out)
        json.dump(s.conn,open(path+'.conexiones.json','w'),ensure_ascii=False,indent=0)
