"""Spec 2a - do duong cong scaling cua DP label-setting (t6_dp, dung nguyen).

Muc dich: xac dinh DP con "du nhanh" den n nao truoc khi bung no sieu tuyen
tinh (Spec 2a - dieu kien dung/bao cao). IN-PROCESS (subprocess.run khong on
dinh tren may nay - fork fail). Chay MOT driver / lan (GW va OD rieng).

Cat-off: khi t_dp cua 1 diem > BREAK_S thi coi (cls,B,tw) do da "vo" o quy
mo n hien tai va KHONG thu n lon hon (blowup sieu tuyen tinh -> chac chan
lau hon). Ghi lai diem vo do voi status="broke".

Ket qua -> results/scaling_probe.csv
"""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "scaling_probe.csv")

N_GRID = (10, 20, 30, 40, 50, 60, 75, 100)
B_GRID = (2, 3, 4)
TW_GRID = (30, 60, 120, 240)
CLS_GRID = ("GW", "OD")
SEED = 7
TAU = 20.0
BREAK_S = 90.0     # 1 driver > 90s -> coi nhu vo o quy mo do, bo n lon hon


def main():
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cls", "n", "B", "tw_width", "status", "t_gen_s", "t_dp_s",
                    "n_generated", "n_surviving", "survival_ratio", "peak_frontier",
                    "n_bundles", "k_values"])
        t_all = time.time()
        for cls in CLS_GRID:
            for B in B_GRID:
                for tw in TW_GRID:
                    for n in N_GRID:
                        seed = IG.stable_seed(n, B, tw, cls, SEED, "probe")
                        t0 = time.time()
                        drivers, orders, tt, meta = IG.generate_instance(
                            n=n, B=B, tw_width=tw, n_drivers=4, seed=seed,
                            tau=TAU, spatial_mode="dispersed")
                        t_gen = time.time() - t0
                        drv = [d for d in drivers if d["cls"] == cls][0]
                        t1 = time.time()
                        r = DL.run_pool(tt, drv, orders, B)
                        t_dp = time.time() - t1
                        gen, surv = r["n_generated"], r["n_surviving"]
                        sr = surv / gen if gen else 0.0
                        status = "broke" if t_dp > BREAK_S else "completed"
                        w.writerow([cls, n, B, tw, status, round(t_gen, 3), round(t_dp, 3),
                                    gen, surv, round(sr, 6), r["peak_frontier"],
                                    r["n_bundles"], "|".join(str(x) for x in sorted(r["k_values"]))])
                        f.flush()
                        print("  cls=%s B=%d tw=%3d n=%3d  %-9s  t_dp=%8.2fs  peak=%7d  gen=%8d  surv_ratio=%.3f"
                              % (cls, B, tw, n, status, t_dp, r["peak_frontier"], gen, sr), flush=True)
                        if status == "broke":
                            print("    -> vo o n=%d (t_dp=%.1fs > %ds); bo n>%d cho (cls=%s,B=%d,tw=%d)"
                                  % (n, t_dp, BREAK_S, n, cls, B, tw), flush=True)
                            break
        print("\nDONE (%.1fs) -> %s" % (time.time() - t_all, OUT), flush=True)


if __name__ == "__main__":
    main()
