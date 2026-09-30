import csv, glob, statistics
D = r"K:\Data Science\Q1 Research\spec_2a_2b\results\rq_all"
rows = []
for fn in sorted(glob.glob(D + r"\rq34_shard*.csv")):
    with open(fn, encoding="utf-8") as f:
        rows.extend(csv.DictReader(f))

s2 = [
    dict(name="[S2] n=12 seed=42", n=12, pool_full=879, t=0.03593),
    dict(name="[S2] n=10 seed=1", n=10, pool_full=714, t=0.04746),
    dict(name="[S2] n=15 seed=7", n=15, pool_full=1561, t=0.05249),
    dict(name="[S2] n=12 seed=123", n=12, pool_full=1416, t=0.04657),
    dict(name="[S2] n=10 seed=999", n=10, pool_full=510, t=0.01773),
]
print("| Nguon | n | pool_full | t_kstar_build (s) |")
print("|---|---:|---:|---:|")
for r in s2:
    print("| %s | %d | %d | %.5f |" % (r["name"], r["n"], r["pool_full"], r["t"]))

# 5 sample tu RQ4: chon tuong minh n=20 alignment=0.90 (pool lon) va n=10 alignment=0.50 (pool nho)
picks = []
for a, n, want in [(0.90, 20, 3), (0.50, 10, 2)]:
    cand = sorted([r for r in rows if abs(float(r["alignment"]) - a) < 1e-9 and int(r["n"]) == n],
                  key=lambda r: (r["n_gw"], r["n_od"], r["rep"]))
    picks.extend(cand[:want])

for r in picks:
    print("| RQ4 n=%s align=%s (gw%s,od%s,rep%s) | %s | %s | %.5f |"
          % (r["n"], r["alignment"], r["n_gw"], r["n_od"], r["rep"], r["n"], r["pool_full"], float(r["t_kstar"])))

pts = [(r["pool_full"], r["t"]) for r in s2] + [(int(r["pool_full"]), float(r["t_kstar"])) for r in picks]
xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
mx, my = statistics.mean(xs), statistics.mean(ys)
cov = sum((x-mx)*(y-my) for x,y in pts)
sx = sum((x-mx)**2 for x in xs)**0.5; sy = sum((y-my)**2 for y in ys)**0.5
r_corr = cov/(sx*sy) if sx>0 and sy>0 else float("nan")
print("\nCorrelation pool_size vs t_kstar_build (10 diem, 5 [S2] + 5 RQ4):", round(r_corr,3))

# full 600-instance check: t_kstar vs pool_full
xs2 = [float(r["pool_full"]) for r in rows]
ys2 = [float(r["t_kstar"]) for r in rows]
mx2, my2 = statistics.mean(xs2), statistics.mean(ys2)
cov2 = sum((x-mx2)*(y-my2) for x,y in zip(xs2,ys2))
sx2 = sum((x-mx2)**2 for x in xs2)**0.5; sy2 = sum((y-my2)**2 for y in ys2)**0.5
print("Correlation pool_size vs t_kstar_build (toan bo 600 instance RQ4):", round(cov2/(sx2*sy2),3))
print("mean pool_full RQ4 =", round(statistics.mean(xs2),1), " mean pool_full [S2] =", round(statistics.mean([r["pool_full"] for r in s2]),1))
print("mean t_kstar RQ4 =", round(statistics.mean(ys2)*1000,1), "ms   mean t [S2] =", round(statistics.mean([r["t"] for r in s2])*1000,1), "ms")
