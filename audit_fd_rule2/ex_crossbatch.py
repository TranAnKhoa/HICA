import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase1_ceiling import *
B=3
drivers, orders, tt, q = label_instance(10,4,999,B)
dr=[d for d in drivers if d["cls"]=="GW"][0]
res=run_dp_instr(tt,dr,orders,B)
groups=defaultdict(list)
for l in res["log"]:
    if l.batch[0] not in ("H","S"): groups[l.key()].append(l)
def seq(l):
    return " ".join("%s%s"%({"pickup":"p","delivery":"d","home":"h"}[a[0]], a[1]) for a,*_ in l.path() if a)
best=None
for k,g in groups.items():
    for b in g:
        if not b.expanded: continue
        for a in g:
            if a is not b and D._dominates_label(a,b) and a.batch!=b.batch:
                c=(len(seq(b)), k,a,b)
                if best is None or c[0]<best[0]: best=c
_,k,a,b=best
print("key v=%s IV=%s C=%s"%(k[0],sorted(k[1]),sorted(k[2])))
for nm,l in (("dominator a",a),("dominated b (EXPANDED)",b)):
    print(" %s: seq=[%s] batch=%s created#%d (t,K,W)=(%.2f,%.3f,%.2f) children=%d"%(nm,seq(l),l.batch,l.lid,l.t,l.K,l.W,l.nch))
