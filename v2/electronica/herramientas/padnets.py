import sys
from sx import *
def padnets(path):
    o=parse(open(path).read()); m={}
    for fp in find(o,'footprint'):
        ref=None
        for pr in find(fp,'property'):
            if pr[1].strip('"')=='Reference': ref=pr[2].strip('"')
        for p in find(fp,'pad'):
            n=find(p,'net'); num=p[1].strip('"')
            if num: m[(ref,num)]=n[0][2].strip('"') if n else None
    return m
if __name__=='__main__':
    a,b=padnets(sys.argv[1]),padnets(sys.argv[2])
    d=[(k,a.get(k),b.get(k)) for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)]
    print(len(a),len(b),'diferencias',len(d)); [print(x) for x in d[:20]]
