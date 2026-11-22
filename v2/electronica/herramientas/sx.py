import re
def parse(t):
    tok=re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',t); i=0
    def rd():
        nonlocal i
        x=tok[i]; i+=1
        if x=='(':
            l=[]
            while tok[i]!=')': l.append(rd())
            i+=1; return l
        return x
    return rd()
def dump(x,ind=0):
    if isinstance(x,str): return x
    if all(isinstance(e,str) for e in x): return '('+' '.join(x)+')'
    s='('+x[0]
    for e in x[1:]: s+='\n'+'\t'*(ind+1)+dump(e,ind+1)
    return s+')'
def find(x,key): return [e for e in x if isinstance(e,list) and e and e[0]==key]
def pins(sym):
    out=[]
    def walk(n):
        for e in n:
            if isinstance(e,list) and e:
                if e[0]=='pin':
                    at=find(e,'at')[0]; ln=float(find(e,'length')[0][1])
                    nm=find(e,'name')[0][1].strip('"'); nu=find(e,'number')[0][1].strip('"')
                    out.append(dict(name=nm,num=nu,x=float(at[1]),y=float(at[2]),a=int(float(at[3])) if len(at)>3 else 0,type=e[1],len=ln))
                elif e[0]=='symbol': walk(e)
    walk(sym); return out
