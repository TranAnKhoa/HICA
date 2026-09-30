"""Kiem tra ground truth + tinh sound cua can tren dataset Atlanta."""
import glob, itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t4_atl as A

ROOT = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Dataset", "instances")


def brute(inst, i, S):
    """Liet ke TAT CA hoan vi 2k event, loc thu tu hop le, mo phong."""
    k = len(S)
    ev = []
    for j in range(k):
        ev.append((j, 0)); ev.append((j, 1))
    cap, until = inst.cap[i], inst.until[i]
    for perm in itertools.permutations(ev):
        seen = set(); ok = True
        for j, kind in perm:
            if kind == 0: seen.add(j)
            elif j not in seen: ok = False; break
        if not ok: continue
        t = 0.0; cur = -1; load = 0; good = True
        for j, kind in perm:
            o = S[j]
            nd = 2 * o + kind
            t = t + (inst.start_row[i][nd] if cur < 0 else inst.T[cur][nd])
            if kind == 0:
                if t < inst.release[o]: t = inst.release[o]
                load += 1
                if load > cap: good = False; break
            else:
                load -= 1
            if t > inst.deadline[o] or t > until: good = False; break
            cur = nd
        if good: return True
    return False


def main():
    files = []
    for sub, pat in [("main", "*n10_B3_tw0.15*"), ("main", "*n15_B3_tw0.30*"),
                     ("main", "*n10_B3_tw0.60*"), ("scale_a", "*n10_B3_tw0.30*")]:
        c = [f for f in sorted(glob.glob(os.path.join(ROOT, sub, pat + ".json")))
             if not f.endswith(".truth.json")]
        files.extend(c[:2])

    mism = tested = unsound = 0
    for f in files:
        inst = A.AtlInstance(f)
        for i in range(inst.m):
            cnt = 0
            for S in itertools.combinations(range(inst.n), 2):
                if cnt >= 60: break
                S = list(S); cnt += 1; tested += 1
                a = A.is_feasible(inst, i, S); b = brute(inst, i, S)
                if a != b:
                    mism += 1; print("  MISMATCH k2", inst.iid, i, S, a, b)
                if a and (A.mst_bound(inst, i, S) > A.budget(inst, S)
                          or A.one_tree_bound(inst, i, S) > A.budget(inst, S)):
                    unsound += 1
            cnt = 0
            for S in itertools.combinations(range(inst.n), 3):
                if cnt >= 40: break
                S = list(S); cnt += 1; tested += 1
                a = A.is_feasible(inst, i, S); b = brute(inst, i, S)
                if a != b:
                    mism += 1; print("  MISMATCH k3", inst.iid, i, S, a, b)
                if a and (A.mst_bound(inst, i, S) > A.budget(inst, S)
                          or A.one_tree_bound(inst, i, S) > A.budget(inst, S)):
                    unsound += 1
    print("files=%d  tested=%d  mismatch=%d  unsound=%d" % (len(files), tested, mism, unsound))
    print("KET QUA:", "PASS" if (mism == 0 and unsound == 0) else "FAIL")
    return 0 if (mism == 0 and unsound == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
