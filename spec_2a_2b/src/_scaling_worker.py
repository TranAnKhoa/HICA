
import sys, time, json
sys.path.insert(0, r"K:\\Data Science\\Q1 Research\\spec_2a_2b\\src")
import instance_gen as IG
import dp_labeling as DL
n, B, tw, cls = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
seed = int(sys.argv[5]); tau = float(sys.argv[6])
t0 = time.time()
drivers, orders, tt, meta = IG.generate_instance(n=n, B=B, tw_width=tw, n_drivers=4,
                                                 seed=seed, tau=tau, spatial_mode="dispersed")
t_gen = time.time() - t0
drv = [d for d in drivers if d["cls"] == cls][0]
t1 = time.time()
r = DL.run_pool(tt, drv, orders, B)
t_dp = time.time() - t1
print(json.dumps(dict(t_gen=t_gen, t_dp=t_dp, n_generated=r["n_generated"],
                      n_surviving=r["n_surviving"], peak_frontier=r["peak_frontier"],
                      n_bundles=r["n_bundles"], k_values=sorted(r["k_values"]))))
