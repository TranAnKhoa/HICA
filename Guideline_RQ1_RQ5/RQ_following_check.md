# RQ1–RQ5 — Ba việc kiểm tra bổ sung (chạy bằng Claude Code)

**Bối cảnh:** Report_RQ_All.md (2026-09-27) cho FD rate 73–95% ở alignment ≤ 0.70, và
RQ4 cho thấy K★ cắt 100% pool ở alignment 0.50. Ba việc dưới đây kiểm tra: (a) calibration
giá FD có đúng như dự định không; (b) T5 (component decomposition) có tín hiệu tốt hơn khi
chạy trên pool đã cắt K★ thay vì pool đầy đủ; (c) đo trực tiếp tần suất K★ rỗng — bằng
chứng "không cần mở phiên đấu giá" mà report hiện chưa khai thác.

**Nguyên tắc bắt buộc, áp dụng cho cả ba việc (kế thừa từ `RQ_Master.md` §8):**
- Đây là các phép đo bổ sung trên hạ tầng đã có, **không phải calibrate lại rồi chạy lại
  RQ1–RQ5**. Không đổi `q_o`, không đổi `κ`, không đổi bất kỳ tham số đã khóa trong
  `rq_all_locked_params.json` hay `rq1_locked_params.json`.
- Nếu (a) phát hiện calibration lệch, **ghi nhận sự lệch đó**, không tự sửa `q_o` rồi
  chạy lại RQ1–RQ5 trong cùng lần này — đó là một quyết định riêng, cần bàn trước.
- Dùng lại instance/pool đã có (từ RQ1 main grid, RQ3+RQ4 instance set) bất cứ khi nào
  có thể, thay vì sinh instance mới — để kết quả so sánh được trực tiếp với báo cáo cũ.
- Báo cáo toàn bộ, không chọn lọc cell đẹp.

---

## Việc (a) — Kiểm lại calibration giá FD

### Mục tiêu
Xác nhận: tham số `q_o` (công thức `8.0 + 3.0·max(0, dist_km − 1.0)`) có từng được
calibrate theo một mục tiêu FD rate cụ thể không, và mục tiêu đó (nếu có) được đo ở
cấu hình nào. Nếu pilot calibration chỉ chạy ở một lát cắt hẹp (ví dụ n=12, một
alignment), kiểm xem mục tiêu đó có generalize sang toàn bộ grid chính hay không.

### Bước 1 — Tìm lại calibration pilot (nếu tồn tại)

```bash
# Tìm mọi file/script/log có nhắc tới calibration của q_o hoặc FD rate target
grep -rln "FD.rate\|fd_rate\|calibrat" spec_2a_2b/ New_t4/ Guideline_Total/ 2>/dev/null
grep -rn "q_o\s*=" spec_2a_2b/src/*.py
```

- Nếu tìm thấy script/log pilot: đọc lại nó, ghi rõ: (i) mục tiêu FD rate là bao nhiêu
  (ví dụ 10–50%), (ii) pilot chạy ở n, alignment, supply nào, (iii) có bao nhiêu rep.
- Nếu **không** tìm thấy — nghĩa là con số "khóa theo FD rate 10–50% trên pilot n=12"
  không có trong codebase hiện tại (có thể chỉ là ghi chú từ một phiên làm việc trước,
  chưa lưu thành file). Trong trường hợp này, bỏ qua bước xác nhận nguồn gốc, chuyển
  thẳng sang Bước 2 để đo FD rate thực tế trên toàn bộ grid — đây là thông tin cần có
  dù pilot cũ có tìm lại được hay không.

### Bước 2 — Đo FD rate thực tế theo alignment, n, supply, và giá FD

Dùng lại **chính** 1,500 instance của RQ1 main grid (không sinh mới). Với mỗi instance,
chỉ cần đọc lại route pool đã build hoặc rebuild theo đúng `gen_seed`/`theta_seed` đã
ghi trong `rq1_main_grid_results.csv`.

```python
# scripts/check_fd_calibration.py
import pandas as pd

df = pd.read_csv("spec_2a_2b/results/rq1_main_grid_results.csv")
# Giữ đúng treatment JOINT (B=3) — đây là baseline dùng cho toàn bộ RQ2-RQ5
joint = df[df["treatment"] == "JOINT"]

summary = (
    joint.groupby(["alignment", "n"])
    .agg(
        fd_rate_median=("fd_rate", "median"),
        fd_rate_mean=("fd_rate", "mean"),
        n_instance=("fd_rate", "count"),
    )
    .reset_index()
)
print(summary.to_string(index=False))
summary.to_csv("spec_2a_2b/results/rq_all/fd_rate_by_cell.csv", index=False)
```

Nếu cột `fd_rate` chưa có sẵn trong CSV, tính lại từ route pool + allocation đã lưu
(không phải giải lại WDP — chỉ đếm `z_o` trong nghiệm đã có).

### Bước 3 — Đối chiếu với mục tiêu pilot (nếu tìm thấy ở Bước 1)

Bảng cần điền:

| alignment | n | FD rate median (main grid) | Mục tiêu pilot (nếu có) | Trong khoảng mục tiêu? |
|---:|---:|---:|---:|---|
| 0.10 | 10/15/20 | | | |
| 0.30 | 10/15/20 | | | |
| 0.50 | 10/15/20 | | | |
| 0.70 | 10/15/20 | | | |
| 0.90 | 10/15/20 | | | |

### Bước 4 — Đo độ nhạy của FD rate theo giá FD (dùng dữ liệu RQ5 đã có)

RQ5 đã có V5 (FD×0.75) và V6 (FD×1.25) tại alignment 0.50, n=15. Chỉ cần trích xuất
FD rate của ba biến thể V0/V5/V6 từ `rq5_shard*.csv` đã có — không chạy lại:

```python
import pandas as pd
rq5 = pd.concat([pd.read_csv(f) for f in glob.glob("spec_2a_2b/results/rq_all/rq5_shard*.csv")])
for variant in ["V0", "V5", "V6"]:
    sub = rq5[rq5["variant"] == variant]
    print(variant, sub["fd_rate"].median(), sub["fd_rate"].mean())
```

### `[CHECK]` Tiêu chí đạt

- Bảng Bước 3 điền đầy đủ, không có ô trống.
- Nếu tìm thấy pilot: nêu rõ **một câu kết luận** — pilot có generalize không, và nếu
  không thì lệch bao xa (ví dụ "pilot nhắm 10–50% ở n=12/alignment X, nhưng main grid
  cho 73–95% ở phần lớn cell — lệch vì pilot không quét đủ alignment/n").
- Nếu không tìm thấy pilot: ghi nhận thẳng "không có bằng chứng calibration trong
  codebase; FD rate quan sát được là 73–95% ở alignment ≤0.70" — đây tự nó là một
  finding cần đưa vào thesis (giới hạn của thiết kế instance generator), không phải
  lỗi cần sửa ngay.

**Không tự động đổi `q_o` sau bước này.** Nếu kết luận là "cần calibrate lại", đó là
việc `[DEVIATION]` riêng, cần chạy lại toàn bộ RQ1–RQ5 theo đúng quy tắc §8 của
`RQ_Master.md` — không làm trong lần chạy này.

---

## Việc (b) — Component decomposition (T5) trên pool đã cắt K★

### Mục tiêu
`Report_2b_Component_Distribution.md` đã đóng với kết luận "component gộp ≥ 0.889
driver ở scale chính" — nghĩa là T5 gần như không giúp gì trên **pool đầy đủ**, vì hầu
hết driver rơi vào cùng một component (order trùng nhau quá nhiều). Câu hỏi mới: nếu
dựng conflict graph trên **pool đã bị K★ cắt** (75–100% route bị loại theo RQ4), liệu
số route/order còn lại có đủ thưa để tách thành nhiều component nhỏ hơn không?

Đây không phải chạy lại RQ4 — RQ4 đã tính K★ cho từng instance rồi. Việc này chỉ cần
build lại conflict graph trên **route pool đã lọc**, dùng đúng `t8_cplex.build_conflict_graph`
đã có, thay vì trên pool gốc.

### Bước 1 — Xác định input

Dùng đúng 600 instance của RQ3+RQ4 (đã có K★-pruned pool được lưu lại khi chạy RQ4, hoặc
tính lại từ `kstar_rule.local_frontier` với `Θ=[18,25]`, `FD=q_o` — công thức y hệt RQ4
§5 của `RQ_Master.md`).

### Bước 2 — Script

```python
# scripts/component_distribution_kstar.py
import json
from t8_cplex import build_conflict_graph
from kstar_rule import local_frontier
import networkx as nx  # hoặc dùng chính hàm đếm component nội bộ nếu đã có

records = []
for inst in load_rq34_instances():  # 600 instance, đúng seed đã dùng cho RQ3/RQ4
    pool_full = build_route_pool_all_drivers(inst)          # như RQ4 nhánh naive
    pool_kstar = {
        i: local_frontier(pool_full[i], theta_range=(18, 25), fd_prices=inst.q)
        for i in pool_full
    }

    g_full = build_conflict_graph(pool_full)
    g_kstar = build_conflict_graph(pool_kstar)

    comp_full = list(nx.connected_components(g_full))
    comp_kstar = list(nx.connected_components(g_kstar))

    n_drivers = len(pool_full)
    records.append({
        "instance_id": inst.id,
        "alignment": inst.alignment,
        "n_orders": inst.n,
        "n_drivers": n_drivers,
        "n_components_full": len(comp_full),
        "largest_component_full_frac": max(len(c) for c in comp_full) / n_drivers,
        "n_components_kstar": len(comp_kstar),
        "largest_component_kstar_frac": (
            max(len(c) for c in comp_kstar) / n_drivers if comp_kstar else 0
        ),
        "n_isolated_kstar": sum(1 for c in comp_kstar if len(c) == 1),
    })

import pandas as pd
df = pd.DataFrame(records)
df.to_csv("spec_2a_2b/results/rq_all/component_distribution_kstar.csv", index=False)
print(df.groupby("alignment")[
    ["largest_component_full_frac", "largest_component_kstar_frac", "n_isolated_kstar"]
].median())
```

### Bước 3 — So sánh với kết quả cũ

Bảng cần điền, theo alignment (0.50 và 0.90, đúng grid RQ3/RQ4):

| alignment | largest component / n_drivers — pool đầy đủ (median) | largest component / n_drivers — pool K★ (median) | % driver bị cô lập (component size 1) — pool K★ |
|---:|---:|---:|---:|
| 0.50 | 0.889 (đã có, trích dẫn) | | |
| 0.90 | | | |

### Bước 4 — Nếu component nhỏ hơn thật, đo speedup thật

Chỉ làm nếu Bước 3 cho thấy `largest_component_kstar_frac` giảm rõ rệt so với 0.889.
Với mỗi instance có ≥2 component ở pool K★, đo thời gian giải removal-solve theo
component (giải từng component riêng, cộng lại) so với giải removal-solve trên toàn
pool K★ (không tách component) — đây chính là phép đo `[CHECK]` cho Corollary 6/T5 áp
dụng lên K★, không phải giả định.

```python
# Với mỗi instance có >=2 component:
#   t_component_wise = sum(solve_removal(sub_instance(P)) for P in components)
#   t_monolithic = solve_removal(full_kstar_pool_instance)
#   speedup = t_monolithic / t_component_wise
```

### `[CHECK]` Tiêu chí đạt

- Chạy đủ cả hai alignment (0.50, 0.90) — alignment 0.50 dễ có tín hiệu tốt hơn vì K★
  cắt 100% pool (rất nhiều driver rỗng → tự động cô lập), alignment 0.90 mới là phép
  thử thật vì đó là nơi crowd cạnh tranh (K★ chỉ cắt ~75%).
- Nếu `largest_component_kstar_frac` ở alignment 0.90 vẫn ≥ 0.85 (gần bằng pool đầy đủ)
  → T5 trên K★ **không** cải thiện gì đáng kể ở chế độ cạnh tranh — đây là kết quả hợp
  lệ, ghi nhận thẳng, không cố tìm cách khác để "cứu" T5.
  Note: ở alignment 0.50, K★ rỗng gần hết nên component tự nhiên nhỏ — kết quả ở
  alignment này **không đại diện** cho "K★ giúp T5 nói chung", vì crowd gần như không
  tồn tại ở đó. Chỉ alignment 0.90 mới trả lời đúng câu hỏi.
- Nếu có cải thiện thật ở alignment 0.90: đo speedup cụ thể (Bước 4) trước khi viết vào
  thesis như một kết quả positive.

---

## Việc (c) — Tần suất K★ rỗng theo alignment và giá FD

### Mục tiêu
K★ rỗng cho một driver nghĩa là: **không có route nào của driver đó từng đáng dùng, bất
kể bid trong Θ là bao nhiêu** — biết được điều này *trước khi* mở phiên đấu giá. Đây là
một hệ quả thực tế trực tiếp của Theorem 4, và RQ4 đã ngầm cho thấy nó (K★ cắt 100% pool
ở alignment 0.50) nhưng chưa đo tường minh ở mức "driver nào, bao nhiêu %, theo điều kiện
nào". Việc này biến kết quả lý thuyết thành một con số vận hành cụ thể: *"X% phiên đấu
giá, tại Y% driver, nền tảng biết trước là không cần mở đấu giá."*

### Bước 1 — Định nghĩa đo lường

Với mỗi driver i trong một instance: K★_i rỗng ⟺ `local_frontier(R_i, Θ, q) == ∅`, tức
là **mọi** route của driver i đều bị FD hoàn thành-vượt-trội tại mọi bid trong Θ (theo
đúng Definition 2 của `T4_Combined.pdf`).

Hai mức đo:
- **Per-driver**: % driver có K★ rỗng, theo alignment.
- **Per-instance**: % instance mà **toàn bộ** driver đều có K★ rỗng (tức toàn bộ đơn
  hàng chắc chắn về FD, không cần giải WDP crowd) — đây là con số "biết trước không cần
  đấu giá" mạnh nhất.

### Bước 2 — Script

Dùng lại route pool đã build cho RQ1 main grid (1,500 instance) và cho RQ5 (biến thể
FD×0.75/×1.25) — không sinh instance mới.

```python
# scripts/kstar_empty_rate.py
import pandas as pd
from kstar_rule import local_frontier

def kstar_empty_stats(instances, theta_range=(18, 25)):
    rows = []
    for inst in instances:
        pool = build_route_pool_all_drivers(inst)  # pool trước K*
        n_drivers = len(pool)
        n_empty = 0
        for i, R_i in pool.items():
            k_star = local_frontier(R_i, theta_range, inst.q)
            if len(k_star) == 0:
                n_empty += 1
        rows.append({
            "instance_id": inst.id,
            "alignment": getattr(inst, "alignment", None),
            "fd_multiplier": getattr(inst, "fd_multiplier", 1.0),
            "n_drivers": n_drivers,
            "n_driver_kstar_empty": n_empty,
            "driver_empty_rate": n_empty / n_drivers,
            "instance_fully_fd": n_empty == n_drivers,
        })
    return pd.DataFrame(rows)

# (i) RQ1 main grid — theo alignment
df_align = kstar_empty_stats(load_rq1_main_grid_instances())
df_align.to_csv("spec_2a_2b/results/rq_all/kstar_empty_by_alignment.csv", index=False)
print(df_align.groupby("alignment")[["driver_empty_rate", "instance_fully_fd"]].mean())

# (ii) RQ5 V0/V5/V6 — theo giá FD, cùng alignment 0.50
df_fd = kstar_empty_stats(load_rq5_variant_instances(["V0", "V5", "V6"]))
df_fd.to_csv("spec_2a_2b/results/rq_all/kstar_empty_by_fd_price.csv", index=False)
print(df_fd.groupby("fd_multiplier")[["driver_empty_rate", "instance_fully_fd"]].mean())
```

### Bước 3 — Bảng cần điền

**Theo alignment (RQ1 main grid, 1,500 instance):**

| alignment | % driver có K★ rỗng (mean) | % instance toàn bộ driver K★ rỗng |
|---:|---:|---:|
| 0.10 | | |
| 0.30 | | |
| 0.50 | | |
| 0.70 | | |
| 0.90 | | |

**Theo giá FD (RQ5, alignment 0.50 cố định):**

| FD multiplier | % driver có K★ rỗng (mean) | % instance toàn bộ driver K★ rỗng |
|---:|---:|---:|
| ×0.75 (V5) | | |
| ×1.00 (V0) | | |
| ×1.25 (V6) | | |

### `[CHECK]` Tiêu chí đạt

- Xu hướng phải đơn điệu: % K★ rỗng giảm dần khi alignment tăng, và giảm dần khi FD
  multiplier tăng (FD đắt hơn → ít driver bị loại trước). Nếu không đơn điệu, có khả
  năng lỗi trong cách tính `local_frontier` hoặc trong việc gán `inst.q` — dừng lại,
  không báo cáo số cho tới khi tìm ra nguyên nhân.
- Đối chiếu chéo với K★ cut ratio đã có ở RQ4 (100% ở alignment 0.50, 75–77% ở
  alignment 0.90) — hai chỉ số phải nhất quán về hướng (cut ratio cao thì driver-empty
  rate cũng phải cao).
- Báo cáo đúng cả hai mức (per-driver và per-instance) — per-instance là con số ấn
  tượng hơn để trích dẫn ("X% phiên đấu giá không cần mở, biết trước bằng K★"), nhưng
  chỉ dùng nếu số thật sự cao; nếu per-instance thấp (vì chỉ cần 1 driver có K★ khác
  rỗng là đủ), dùng per-driver làm số chính.

---

## Tổng kết đưa vào thesis (viết sau khi cả ba việc xong)

1. **(a)** Một đoạn ngắn trong phần thiết kế thực nghiệm, nêu rõ FD rate quan sát được
   theo alignment, và calibration thật sự dựa trên cơ sở nào (pilot cũ nếu tìm thấy,
   hoặc thẳng thắn ghi là công thức `q_o` cố định không qua calibrate theo FD rate mục
   tiêu, nếu Bước 1 việc (a) không tìm thấy bằng chứng ngược lại).
2. **(b)** Nếu có tín hiệu tích cực ở alignment 0.90 → thêm một bảng vào Section T5 của
   `T4_Combined.tex`/paper, đổi khung "T5 hầu như không giúp gì" thành "T5 giúp khi kết
   hợp với K★". Nếu không có tín hiệu → giữ nguyên kết luận cũ, không thêm gì.
3. **(c)** Thêm một Remark trong Theorem 4 section: "trên dữ liệu RQ1 thật, K★ rỗng ở
   X% driver khi alignment ≤ 0.50 — một hệ quả vận hành trực tiếp: nền tảng biết trước,
   không cần đọc bid, rằng không cần mở phiên đấu giá cho phần lớn driver." Đây là câu
   trả lời trực tiếp cho lo ngại "FD luôn thắng thì đề tài có ý nghĩa gì" — K★ tự nó là
   công cụ phát hiện đúng lúc nào crowd đáng cân nhắc, không phải một lý thuyết suông.