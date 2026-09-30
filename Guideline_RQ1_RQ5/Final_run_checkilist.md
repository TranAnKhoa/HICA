# HICA-S — Runbook chạy chốt (một lần duy nhất)

**Mục đích:** gom toàn bộ việc `[PENDING]` còn lại trong `HICA-S_Master_Writeup.md` §18
thành một lần chạy. Bốn việc đầu là **bắt buộc, rẻ, không giải lại bài toán nào** — chỉ
đọc lại dữ liệu/pool đã có và tính lại thống kê hoặc thêm một điều kiện lọc. Ba việc cuối
là **tùy chọn**, chỉ làm nếu còn thời gian, và không được trộn kết quả của chúng vào các
bảng chính đã khóa.

**Nguyên tắc bắt buộc (không đổi so với các lần trước):**
- Không sinh instance mới ngoài các trường hợp ghi rõ ở việc tùy chọn.
- Không đổi bất kỳ tham số đã khóa (`rq1_locked_params.json`, `rq_all_locked_params.json`).
- Không giải lại WDP/removal-solve nào đã có kết quả — chỉ đọc lại pool/CSV đã lưu.
- Báo cáo toàn bộ, không chọn lọc cell đẹp. Nếu một việc cho kết quả không như kỳ vọng,
  ghi nhận thẳng, không lặp lại với tham số khác để "tìm tín hiệu".
- Sau khi xong, chỉ cập nhật các bảng trong `HICA-S_Master_Writeup.md` đã đánh dấu
  `[PENDING]` — không viết lại các bảng đã chốt.

**Thứ tự chạy:** A → B → C → D bắt buộc, theo đúng thứ tự này vì D dùng lại output của A.
E/F/G tùy chọn, độc lập với nhau, có thể bỏ qua toàn bộ.

---

## A. Tách "K★ rỗng" thành hai loại (ứng với §18.1)

### Vì sao
Con số hiện tại (77.3% driver ở alignment 0.50, v.v.) gộp hai chuyện khác nhau: tài xế
không có route khả thi nào ($R_i = \emptyset$, sự thật hình học, không liên quan Theorem 4)
và tài xế có route nhưng bị FD vượt trội hoàn toàn ($R_i \ne \emptyset$ nhưng $\mathcal
K^\star_i = \emptyset$, đây mới là hệ quả của Theorem 4). Chỉ loại thứ hai được phép trích
dẫn như bằng chứng "$\mathcal K^\star$ chứng nhận trước khi đấu giá".

### Việc cần làm

Sửa `spec_2a_2b/src/kstar_empty_rate.py` và `kstar_empty_rate_shard.py`: với mỗi driver
trong mỗi instance, tính thêm hai cờ trước khi gộp thống kê.

```python
# Chèn ngay sau khi có R_i (pool trước K*) và trước khi gọi local_frontier
feasible_empty = (len(R_i) == 0)
k_star = local_frontier(R_i, (18, 25), inst.q)   # giữ nguyên lời gọi cũ
kstar_empty = (len(k_star) == 0)
fd_dominated = kstar_empty and not feasible_empty   # <-- CỜ MỚI, đây mới là Theorem 4
```

Đổi output mỗi dòng driver thành:

```python
rows.append({
    "instance_id": inst.id,
    "alignment": getattr(inst, "alignment", None),
    "fd_multiplier": getattr(inst, "fd_multiplier", 1.0),
    "driver_id": i,
    "feasible_empty": feasible_empty,
    "kstar_empty": kstar_empty,
    "fd_dominated": fd_dominated,
})
```

Không đổi tập instance dùng (vẫn đúng 1,500 instance RQ1 main grid cho phần theo alignment,
đúng 180 instance RQ5 V0/V5/V6 cho phần theo giá FD — như đã chạy).

### Bảng kết quả cần điền

**Theo alignment, per-driver (mean trên toàn bộ driver, n=1,500 instance × driver count):**

| alignment | % feasible_empty | % fd_dominated (trên mọi driver) | % fd_dominated \| $R_i \ne \emptyset$ |
|---:|---:|---:|---:|
| 0.10 | | | |
| 0.30 | | | |
| 0.50 | | | |
| 0.70 | | | |
| 0.90 | | | |

**Theo alignment, per-instance:**

| alignment | % instance mọi driver feasible_empty | % instance mọi driver kstar_empty | % instance mọi driver có $R_i\ne\emptyset$ đều fd_dominated |
|---:|---:|---:|---:|
| 0.10 | | | |
| 0.30 | | | |
| 0.50 | | | |
| 0.70 | | | |
| 0.90 | | | |

**Theo giá FD (alignment 0.50, RQ5 V0/V5/V6), per-driver và per-instance:** dùng đúng cấu
trúc hai bảng trên, thay cột alignment bằng FD multiplier.

### `[CHECK]`
- Cột `% feasible_empty` phải **không đổi** theo FD multiplier (đây là feasibility hình học,
  không phụ thuộc giá FD) — nếu đổi, có bug trong cách gán cờ.
- Cột `% fd_dominated` phải **giảm đơn điệu** khi FD đắt hơn (đúng Remark 14). Nếu không,
  dừng lại và kiểm `local_frontier`/việc gán `inst.q` trước khi báo cáo.
- Chỉ dùng cột `fd_dominated` (không dùng `kstar_empty` thô) khi viết câu "X% driver được
  biết trước là không đáng dùng" vào paper.

### File output
`spec_2a_2b/results/rq_all/kstar_empty_split_by_alignment.csv` (per-driver, ~1,500×driver
dòng), `kstar_empty_split_by_alignment_instance.csv` (per-instance, 1,500 dòng),
`kstar_empty_split_by_fd_price.csv` (180×driver dòng).

---

## B. Tính lại thống kê RQ1 theo quy ước đã khóa (ứng với §18.4)

### Vì sao
Bảng RQ1 hiện tại dùng "mean của median cell" (0.01% / 0.08% / 0.00% / 0.93% / 5.86%),
khác quy ước đã chốt cho paper: **median [IQR] · mean (95% bootstrap CI), tính trên
instance**, giống hệt cách RQ2/RQ3 đã làm.

### Việc cần làm

Đọc `rq1_main_grid_results.csv` (không giải lại gì). Với mỗi instance, complementarity
gain đã có sẵn (hoặc tính lại từ `true_cost` các treatment GW-only/OD-only/JOINT đã lưu):

```python
import pandas as pd, numpy as np

df = pd.read_csv("spec_2a_2b/results/rq1_main_grid_results.csv")
wide = df.pivot_table(index=["instance_id", "alignment", "n"],
                       columns="treatment", values="true_cost").reset_index()
wide["comp_gain"] = (
    np.minimum(wide["GW_only"], wide["OD_only"]) - wide["JOINT"]
) / np.minimum(wide["GW_only"], wide["OD_only"])

def bootstrap_ci(x, n_boot=2000, seed=0):
    rng = np.random.default_rng(seed)
    means = [rng.choice(x, size=len(x), replace=True).mean() for _ in range(n_boot)]
    return np.percentile(means, [2.5, 97.5])

rows = []
for align, g in wide.groupby("alignment"):
    x = g["comp_gain"].values
    lo, hi = bootstrap_ci(x)
    rows.append({
        "alignment": align,
        "median": np.median(x) * 100,
        "iqr_lo": np.percentile(x, 25) * 100,
        "iqr_hi": np.percentile(x, 75) * 100,
        "mean": x.mean() * 100,
        "ci_lo": lo * 100,
        "ci_hi": hi * 100,
        "n": len(x),
    })
pd.DataFrame(rows).to_csv("spec_2a_2b/results/rq_all/rq1_comp_gain_recomputed.csv", index=False)
```

Lặp lại cùng cấu trúc, tách thêm theo `n` (bảng phụ, giống cách RQ2 đã làm ở §11.1 của
Master Writeup) nếu muốn có bảng theo cả alignment × n.

### Bảng kết quả cần điền (thay bảng cũ trong Master Writeup §10)

| alignment | median [IQR] · mean (95% CI), % | n instance |
|---:|---|---:|
| 0.10 | | 300 |
| 0.30 | | 300 |
| 0.50 | | 300 |
| 0.70 | | 300 |
| 0.90 | | 300 |

### `[CHECK]`
- $n$ = 300 mỗi alignment (3 giá trị $n$ × 4 supply × 25 rep). Nếu khác, kiểm lại pivot.
- Median ở alignment 0.10/0.30/0.50 rất có thể bằng 0.00% (vì phần lớn instance JOINT =
  min(GW-only, OD-only) khi FD chiếm ưu thế) — đây là kết quả hợp lệ, không phải lỗi.
- So sánh **hướng** với bảng cũ (0.01/0.08/0.00/0.93/5.86 tăng dần trừ điểm lõm ở 0.50):
  median/mean mới có thể khác giá trị tuyệt đối nhưng phải giữ hình dạng tương tự. Nếu
  hình dạng đổi hẳn (ví dụ không còn lõm ở 0.50), dừng lại và đối chiếu với FD rate ở
  Việc A output cũ trước khi báo cáo.

---

## C. Kiểm miền bid Θ dùng cho biến thể V8 (ứng với §18.5)

### Vì sao
RQ5 V8 đặt $\theta \sim U[15, 30]$, rộng hơn $\Theta = [18, 25]$ dùng cho message space
và cho $\mathcal K^\star$ ở mọi RQ khác. Nếu V8 vẫn giới hạn report trong $[18,25]$, tài xế
có $\theta \in [15,18) \cup (25,30]$ không thể khai thật — DSIC theo nghĩa thông thường
không còn áp dụng nguyên vẹn, và kết quả V8 cần được mô tả khác đi.

### Việc cần làm

Không chạy gì — chỉ đọc code, một lần:

```bash
grep -n "V8\|theta_range\|Theta\|theta_min\|theta_max\|18.*25\|15.*30" \
    spec_2a_2b/src/rq_runner.py spec_2a_2b/src/rq_common.py \
    spec_2a_2b/results/rq_all/rq_all_locked_params.json
```

Trả lời chính xác một trong hai trường hợp:

- **(i) V8 đã mở rộng $\Theta$ thành $[15,30]$ cho mọi bước** (sinh $\theta$, giới hạn
  report, và $\mathcal K^\star$ nếu V8 có dùng): không cần sửa gì, chỉ ghi rõ trong paper
  rằng V8 dùng $\Theta = [15,30]$ khác với baseline.
- **(ii) V8 chỉ đổi phân phối sinh $\theta$ nhưng report vẫn bị giới hạn $[18,25]$**: đây là
  một cơ chế khác — tài xế có $\theta$ ngoài khoảng đó bị ép khai sai lệch bắt buộc. Cần
  thêm một câu Limitation rõ ràng, và **không** gọi kết quả V8 là "robustness của mechanism
  gốc" — nó đo độ nhạy của mechanism khi type vượt khỏi message space đã công bố, một câu
  hỏi khác (thú vị nhưng khác).

### Ghi vào Master Writeup
Điền kết quả (i) hoặc (ii) vào ô `[PENDING-CHECK]` ở §2.3 và câu tương ứng ở §14 (RQ5), và
sửa cách diễn giải V8 trong bảng RQ5 nếu rơi vào trường hợp (ii).

---

## D. Đối chiếu thời gian dựng $\mathcal K^\star$ giữa hai lần đo (ứng với §18.6)

### Vì sao
[S2] báo 17–75 ms/instance để dựng $\mathcal K^\star$ (5 instance RQ1). RQ4 báo trung bình
$90.6\,\text{s}/600 \approx 151\,\text{ms}$/instance. Cần xác nhận chênh lệch đến từ kích
thước pool (RQ4 có $n$ tới 20, alignment 0.90, pool lớn hơn), không phải khác cài đặt.

### Việc cần làm

Chạy lại **chỉ bước dựng $\mathcal K^\star$** (không giải WDP, không đo lại speed-up) trên
đúng 5 instance của [S2] và trên 5 instance ngẫu nhiên rút từ RQ4 (đã biết $n$, alignment)
để so trực tiếp:

```python
import time
from kstar_rule import local_frontier

def time_kstar_build(instances):
    rows = []
    for inst in instances:
        pool = build_route_pool_all_drivers(inst)
        t0 = time.perf_counter()
        for i, R_i in pool.items():
            local_frontier(R_i, (18, 25), inst.q)
        t1 = time.perf_counter()
        rows.append({
            "instance_id": inst.id, "n": inst.n, "alignment": inst.alignment,
            "n_drivers": len(pool),
            "pool_size_total": sum(len(r) for r in pool.values()),
            "kstar_build_time_s": t1 - t0,
        })
    return rows

# (i) 5 instance của Final_t4_Speedup_RESULTS.md — đúng seed đã dùng
t4_instances = load_instances([(12,42),(10,1),(15,7),(12,123),(10,999)])
# (ii) 5 instance rút ngẫu nhiên từ RQ3/RQ4 set (n=20, alignment=0.90 và n=10, alignment=0.50)
rq4_sample = load_rq34_instances()[:5]  # hoặc chọn tường minh 5 id cụ thể, ghi lại id đã chọn

results = time_kstar_build(t4_instances) + time_kstar_build(rq4_sample)
import pandas as pd
pd.DataFrame(results).to_csv(
    "spec_2a_2b/results/rq_all/kstar_build_time_reconciliation.csv", index=False)
```

### Bảng kết quả cần điền

| Nguồn | n | alignment | pool size (tổng) | thời gian dựng K★ (s) |
|---|---:|---:|---:|---:|
| [S2] instance 1 (n12 s42) | 12 | — | | |
| [S2] instance 2 (n10 s1) | 10 | — | | |
| [S2] instance 3 (n15 s7) | 15 | — | | |
| [S2] instance 4 (n12 s123) | 12 | — | | |
| [S2] instance 5 (n10 s999) | 10 | — | | |
| RQ4 sample 1 | | | | |
| RQ4 sample 2 | | | | |
| RQ4 sample 3 | | | | |
| RQ4 sample 4 | | | | |
| RQ4 sample 5 | | | | |

### `[CHECK]`
- Nếu thời gian dựng tương quan rõ với `pool_size_total` (tuyến tính hoặc gần tuyến tính,
  đúng Remark 15: $O(|R_i| 2^B f \log(2^B f))$) → xác nhận chênh lệch là do kích thước pool,
  không phải khác cài đặt. Ghi một câu vào §13 của Master Writeup.
- Nếu **không** tương quan (ví dụ instance nhỏ mà dựng lâu bất thường) → có khả năng khác
  biệt môi trường (CPU, phiên bản Python) hoặc lỗi cài đặt — cần điều tra thêm trước khi
  ghi bất kỳ câu giải thích nào vào paper.

---

## E–G. Việc tùy chọn — chỉ làm nếu còn thời gian, không bắt buộc cho lần chạy này

Ba việc dưới đây **không cần làm** để hoàn thiện bản thảo hiện tại. Chỉ liệt kê ở đây để
không phải mở lại toàn bộ ngữ cảnh nếu sau này quyết định làm.

### E. Lát cắt alignment mịn hơn (§18.2)
Thêm alignment $\{0.40, 0.45, 0.55, 0.60\}$, $n=15$, 4 supply × 15 rep, chỉ treatment JOINT
B3, để vẽ rõ hình dạng lồi của FD rate/K★-empty. Không đổi kết luận RQ nào. Bỏ qua nếu
không cần hình minh họa đẹp hơn trong paper.

### F. RQ5 lặp lại ở alignment 0.90 (§18.3)
Lặp V1–V8 với baseline alignment 0.90 thay vì 0.50, để có robustness ở chế độ crowd cạnh
tranh. Đây là phân tích bổ sung, **không thay thế** RQ5 gốc — nếu làm, ghi rõ là
`[DEVIATION]`/phụ lục, giữ nguyên bảng RQ5 chính.

### G. Vector hóa $\mathcal K^\star$ (§18.7)
Chỉ cần nếu muốn claim speed-up thật cho một phiên đấu giá đơn lẻ (hiện 1.06×). Đây là
việc kỹ thuật thuần túy (viết lại `local_frontier` dùng numpy/vector hóa phép tính margin
thay vì vòng lặp Python), không phải chạy thí nghiệm — bỏ qua nếu không có thời gian, vì
kết quả 1.06× vẫn có thể báo cáo trung thực trong paper mà không cần cải thiện.

---

## Checklist tổng kết trước khi coi phần code là xong hẳn

- [ ] A: bảng per-driver và per-instance đã điền, `fd_dominated` giảm đơn điệu theo giá FD
- [ ] B: bảng RQ1 mới (median/IQR/mean/CI trên instance) đã thay bảng cũ trong Master Writeup
- [ ] C: đã xác định V8 dùng $\Theta$ nào, đã ghi vào Master Writeup
- [ ] D: đã xác nhận (hoặc bác bỏ) giả thuyết "chênh lệch do kích thước pool"
- [ ] Đã cập nhật mọi ô `[PENDING]`/`[PENDING-CHECK]` liên quan trong
      `HICA-S_Master_Writeup.md` bằng số thật, xóa nhãn `[PENDING]` ở dòng tương ứng
- [ ] Không có bảng nào trong Master Writeup còn bị đổi ngoài bốn việc A–D ở trên