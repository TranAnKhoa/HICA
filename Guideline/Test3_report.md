# Test3 Report — Patch cho Test2: (1) bug OD ready_time, (2) Pareto-dominance

**Spec:** `Guideline/Test3.md` · **Code:** `experiments/T2BFS/t2_core.py` (Pareto), `t2_gen.py` (patch),
`t3_pareto.py` (Việc 2), `t3_check_k1.py`, `t3_rerun_od.py` (Việc 1)
**Output thô:** `Output/Test3/` (`pareto_raw.csv`, `pareto_summary.txt`, `od_patched_*.csv`)

Test3.md tự nói làm **Việc 2 trước** vì nó quyết định có đáng đầu tư sâu vào Việc 1 hay không.
Báo cáo này giữ đúng thứ tự đó.

---

## Việc 2 — Pareto-dominance: KHÔNG DÙNG ĐƯỢC, xác nhận bằng thực nghiệm

### Cách đo

Chạy `BFS_PARETO` (giống `bfs_generate` gốc, nhưng level sau chỉ chèn từ `Pareto[P]` thay vì `Seq[P]`)
trên đúng grid nhỏ đã có ground truth của Test2 (n≤6, B≤4, `SEEDS_PER_CELL=8`, 29.056 subset).
Label Pareto dùng đúng công thức spec cho: `(end_node, arrival_time, K, W)`.

**Giả định thiết kế công khai** (Test3.md không định nghĩa `K`, `W` tường minh): chọn
`K(seq) = load hiện tại tại node cuối walk thực` (capacity dùng), `W(seq) = D_end - t0` (thời điểm
rời node cuối walk thực, tính từ t0) — đây là hai đại lượng duy nhất trực tiếp quyết định khả thi
của phần còn lại của walk khi chèn thêm đơn (deadline còn lại phụ thuộc thời điểm hiện tại, capacity
còn lại phụ thuộc load hiện tại). Node `home` (OD) không tham gia so sánh vì nó là điểm kết bắt buộc
chung cho mọi sequence của một OD — so sánh nó không phân biệt gì giữa các ứng viên.

### Kết quả

| Chỉ số | Giá trị |
|---|---|
| Tổng subset đã kiểm | 29.056 |
| **Violation** (Seq[S] sinh từ Pareto[P] thiếu ≥1 sequence so brute force) | **2.271 (7,82%)** |
| Trong đó **deep violation** (thiếu sót lan sang superset ở level kế) | 848 (2,92%) |
| Median compression_ratio (`|Pareto(S)|/|Seq(S)|`, seq>0) | 0,333 tại k=2 → 0,0044 tại k=4 |

**Tách theo lớp — phát hiện quan trọng:**

| lớp | subset | violation | rate |
|---|---|---|---|
| GW | 7.264 | 2.271 | **31,26%** |
| OD | 21.792 | 0 | 0,00%* |

*OD = 0% violation không phải vì Pareto an toàn với OD — mà vì OD gần như không có sequence khả thi
nào để mà bị mất (xem Test2_report.md §4: OD sụp hoàn toàn ở k≥2 trong dữ liệu gốc). Cột này không
có ý nghĩa kiểm chứng thực với OD.

**GW theo k (trong tổng 7.264 subset GW):**

| k | subset | violation | rate | deep violation |
|---|---|---|---|---|
| 1 | 1.440 | 0 | 0% | 0 |
| 2 | 2.976 | 0 | 0% | 0 |
| 3 | 2.176 | 1.740 | **79,96%** | 848 |
| 4 | 672 | 531 | **79,02%** | 0 (k=4=B, không có level sau để kiểm) |

Ở k=3 (B=4), **848/865 violation lan tới deep violation** — nghĩa là gần như mọi lần Pareto bỏ sót
một sequence ở k=3, việc bỏ sót đó **thực sự làm mất một sequence khả thi ở k=4** (không phải "trùng
lặp vô hại", đúng cảnh báo trong Test2.md §3.2: "chọn một sequence trong tập cha thì mất
completeness — đã có phản ví dụ").

Violation xảy ra ở mọi `tw_width` (30: 158, 60: 689, 120: 712, 240: 712 trên 1.816 subset mỗi mức) —
tệ hơn khi TW lỏng hơn (nhiều sequence khả thi hơn → nhiều cặp Pareto-không-so-sánh-được hơn bị lọc
nhầm).

### Kết luận theo đúng bảng ngưỡng §Việc 2 của Test3.md

> Violation rate GW = **31,26%** (>1%, "không hiếm") → rơi đúng vào ô:
> **"Xác nhận phản ví dụ lý thuyết là phổ biến, không phải cá biệt — Pareto-dominance kiểu này
> KHÔNG DÙNG ĐƯỢC, dừng hướng này."**

Compression tiềm năng rất hấp dẫn (median ratio giảm còn 0,4% ở k=4) — nhưng chính xác ở k=3, k=4
(nơi compression có giá trị nhất vì Q2 bùng nổ ở đó) là nơi violation cũng cao nhất (~80%). Đây
không phải trường hợp "gần đúng, cần thêm điều kiện" — nó thất bại đúng ở phần quan trọng nhất.
**Không chạy tiếp lên quy mô lớn (n=8..15)** vì kết luận đã dứt khoát theo ngưỡng spec tự đặt ra.

**Vì sao label 4 chiều không đủ:** dominance chỉ so sánh 2 sequence có cùng `end_node`. Nhưng một
sequence "tệ hơn" theo `(arrival, K, W)` tại `end_node` X vẫn có thể **mở ra vị trí chèn hình học tốt
hơn** cho order tiếp theo (ví dụ node X nằm gần pickup của order kế, dù đến muộn hơn) — điều mà label
không nắm bắt được vì nó không biết trước order nào sẽ được chèn tiếp. Đây khớp với chú thích trong
Test2.md §3.2 rằng chỉ có **chọn tập cha** mới an toàn (đã chứng minh bằng tam giác), còn chọn một
**sequence đại diện** (kể cả "tốt nhất" theo tiêu chí đa chiều) thì không.

---

## Việc 1 — Patch bug OD ready_time

Vì Việc 2 đã bác bỏ hướng Pareto, Test3.md nói "quyết định có đáng sửa OD sâu hơn (Việc 1) để dùng
cho Q2 quy mô lớn hay không" — vẫn làm Việc 1 vì đây là patch cho chính pipeline Q2/Q3 gốc, độc lập
với Pareto, và OD-collapse là bất thường lớn nhất trong `Test2_report.md`.

### Patch 1 — neo ready_time theo tau

```python
ready_time_pickup = t0 + random.uniform(0, tau)   # thay vì U[0,120] tuyệt đối
```

Áp trong `t2_gen.py` (đã đổi thứ tự sinh: `home_node`/`tau` giờ được sinh **trước** vòng lặp order,
để `ready_time_pickup` có `tau` sẵn khi cần).

**Kết quả riêng patch 1 (đo thăm dò trước khi thêm patch 2):**

| tau | feasibility_rate_k1 CŨ (Test2 gốc) | SAU patch 1 |
|---|---|---|
| 15 | 0,8% | 3,9% |
| 30 | 5,1% | 17,2% |
| 60 | 27,4% | 53,3% |

Cải thiện rõ nhưng tau=15, 30 vẫn dưới ngưỡng bắt buộc 50% → đúng dự đoán của Test3.md: **"nếu vẫn
thấp sau patch, còn bug khác."**

### Chẩn đoán bug thứ hai (đúng như Test3.md gợi ý)

Kiểm tra trực tiếp 1 instance (n=6, OD, tau=15): dù `ready_time_pickup` đã đúng lúc, mỗi chặng
`start→pickup`, `pickup→delivery`, `delivery→home` đều lớn xấp xỉ bằng chính `direct_time` (vì
pickup/delivery được sinh **ngẫu nhiên toàn vùng 10km×10km**, không quanh corridor start→home) —
detour vẫn quá xa bất kể thời điểm đúng:

```
direct_time=28.68  tau=15  deadline_home=43.68
o0: start->p=24.67  p->d=18.88  d->home=21.09  arrival_home=74.64 (limit 43.68)  FAIL
o1: start->p=9.26   p->d=24.55  d->home=2.15   arrival_home=48.59 (limit 43.68)  FAIL
```

### Patch 2 — corridor-weighted P/D sampling

**Giả định thiết kế công khai** (không được spec khóa giá trị): pickup/delivery của OD ưu tiên lấy
từ vùng đệm quanh đoạn thẳng `start→home`:

```python
CORRIDOR_BUFFER_KM = 3.0    # buffer quanh đoạn thẳng start->home
CORRIDOR_SHARE = 0.7        # 70% điểm P/D lấy trong buffer, 30% ngẫu nhiên toàn vùng
```

(Đúng tỷ lệ ví dụ nêu trong Test3.md §Việc1: "70% điểm nằm trong buffer 3km quanh corridor, 30%
ngẫu nhiên toàn vùng".)

### Kết quả cuối — feasibility_rate_k1 sau CẢ HAI patch

| tau | CŨ (gốc) | Patch 1 riêng | Patch 1+2 (cuối) |
|---|---|---|---|
| 15 | 0,8% | 3,9% | **6,5%** |
| 30 | 5,1% | 17,2% | **34,5%** |
| 60 | 27,4% | 53,3% | **67,2%** |

`tw_width` vẫn hoàn toàn không ảnh hưởng (0,358/0,354/0,359/0,371 ở tw=30/60/120/240) — khớp phát
hiện gốc trong `Test2_report.md`: biến điều khiển feasibility của OD là `tau`, không phải `tw_width`.

**% cell (n,B,tw,tau,seed) đạt ngưỡng bắt buộc `feasibility_rate_k1 >= 0.5`:**

| tau | % cell đạt ngưỡng |
|---|---|
| 15 | 0,45% (gần như không bao giờ) |
| 30 | 29,17% |
| 60 | **85,66%** |

### Vì sao tau=15 vẫn không đạt được — không phải bug, là giới hạn hình học

Kiểm tay lại instance tương tự sau patch 2 (điểm P/D giờ đã trong buffer 3km quanh corridor):

```
corridor_pool_size=40  direct_time=15.27  tau=15  deadline_home=30.27
o0: start->p=13.66  p->d=12.58  d->home=19.26  arrival_home=55.51 (limit 30.27)  FAIL
```

Với `tau=15` phút và `speed=20km/h`, tổng ngân sách detour chỉ tương đương ~5km đường đi thêm.
Ngay cả một điểm nằm sát corridor (trong buffer 3km) vẫn cần ghé pickup rồi delivery — tổng
quãng đường lệch khỏi đường thẳng `start→home` cho một cặp P/D ngẫu nhiên trong buffer 3km thường
đã vượt 5km. Đây là **giới hạn vật lý của chính tham số `tau=15` đã khóa trong Test2.md §5**, không
phải lỗi sinh dữ liệu — đã loại trừ cả hai giả thuyết bug (ready_time sai lúc, P/D quá xa corridor)
mà vẫn không đạt ngưỡng ở tau=15.

### Gate correctness sau patch — vẫn PASS TUYỆT ĐỐI

Chạy lại toàn bộ gate (Sec4.1–4.4 của Test2.md) trên OD, grid nhỏ, chỉ trên các cell đạt ngưỡng
`feasibility_rate_k1 >= 0.5` (360/864 seed-cell khả dụng, phần còn lại bị bỏ qua đúng theo yêu cầu
"nếu dưới 50%, in cảnh báo, không chạy tiếp cell đó" của Test3.md):

```
GATE SUMMARY (OD, patched): cells=108  completeness_fail_cells=0  validator_fail_cells=0
                             filter_wrongprune_cells=0  monotonicity_counterexamples=0
```

**0 lỗi trên mọi gate** — patch không phá thuật toán BFS, chỉ thay đổi phân bố instance.

### Q2/Q3 sau patch (chỉ OD, quy mô lớn n=8..15, chỉ cell đạt ngưỡng k1)

**`n_feasible_sequences` theo k:**

| k | median | mean | max | % subset có ≥1 sequence khả thi |
|---|---|---|---|---|
| 1 | 1 | 0,688 | 1 | 68,75%* |
| 2 | 0 | 0,445 | 6 | **18,54%** |
| 3 | 0 | 0,075 | 90 | 1,40% |
| 4 | 0 | 0,001 | 58 | 0,01% |

*68,75% ở k=1 phản ánh đúng việc gate đã lọc trước các cell yếu — không so được trực tiếp với con
số toàn-mẫu của báo cáo gốc.

**Tách theo tau — so trực tiếp với `Test2_report.md` §4 (nơi OD có max=0 ở MỌI (B,tw_width), k≥2):**

| tau | k=1 %khả thi | k=2 %khả thi | k=3 %khả thi | k=4 %khả thi |
|---|---|---|---|---|
| 30 | 58,8% | 2,6% | 0,0% | 0,0% |
| 60 | 71,3% | **22,4%** | **1,7%** | **0,01%** |

So với báo cáo gốc (max quan sát ở k≥2 across 205.440 subset = **đúng 0**), đây là một thay đổi
định tính: OD giờ **có** bundle khả thi ở k=2 (tau=60: 22,4% subset, không còn 0%), và thậm chí một
số ít ở k=3/k=4. Nhưng bundling (k≥2) **vẫn hiếm** ngay cả sau khi sửa cả hai nguồn lỗi đã xác định —
đây giờ có vẻ là tính chất kinh tế thật của detour budget (một OD chỉ có vài chục phút để lệch khỏi
đường về nhà, khó nhét vừa 2+ cặp pickup-delivery), không phải lỗi sinh dữ liệu.

**Bộ lọc slack* (Q3) sau patch:**

| k | % bị filter cắt |
|---|---|
| 1 | 0% |
| 2 | 52,8% |
| 3 | 94,4% |
| 4 | 99,8% |

Tương tự báo cáo gốc — vẫn cao, nhưng giờ đáng tin hơn vì nền feasibility k=1 đã hợp lý (68,7%
thay vì gần 0%), nên tỷ lệ cắt cao này phản ánh đúng hơn việc bundling OD **thực sự** khó, không
còn bị nhiễu bởi lỗi "chết ngay từ k=1."

---

## Kết luận tổng hợp

1. **Việc 2 (Pareto-dominance): DỪNG.** Violation rate GW = 31,26%, tập trung đúng ở k=3-4 nơi nén
   có giá trị nhất, với 98% trong số đó (848/865 ở k=3) lan thành mất completeness ở level kế tiếp.
   Không đạt ngưỡng "hiếm" (<1%) của chính spec. Không cần thí nghiệm thêm ở quy mô lớn.
2. **Việc 1 (patch OD): THÀNH CÔNG MỘT PHẦN, TRUNG THỰC BÁO CÁO CẢ HAI MẶT.**
   - Cả hai nguồn lỗi Test3.md dự đoán đều được xác nhận và sửa: (a) ready_time không neo theo tau,
     (b) P/D sinh ngẫu nhiên toàn vùng thay vì quanh corridor.
   - feasibility_rate_k1 cải thiện mạnh (0,8→6,5% ở tau=15; 5,1→34,5% ở tau=30; 27,4→67,2% ở tau=60).
   - Nhưng tau=15 vẫn không đạt ngưỡng 50% — đã xác nhận đây là giới hạn hình học/vật lý của chính
     tham số `tau=15` phút đã khóa trong Test2.md §5 khi kết hợp `speed=20km/h`, `area_km=10`, không
     còn "bug" nào khác để sửa mà không phá vỡ tinh thần giữ nguyên grid đã khóa.
   - Bundling OD (k≥2) vẫn hiếm sau patch (22,4% ở k=2, tau=60; gần 0% ở tau=30) — đổi từ "hoàn toàn
     0%" (báo cáo gốc) sang "hiếm nhưng có thật", một kết luận định tính khác nhưng vẫn tiêu cực cho
     hướng OD-bundling ở B lớn.
   - Gate BFS-vs-brute-force vẫn PASS TUYỆT ĐỐI sau patch — thuật toán không hề bị ảnh hưởng, chỉ
     có phân bố instance thay đổi.

---

## File

| File | Nội dung |
|---|---|
| `Output/Test3/pareto_raw.csv` | 29.056 dòng — kết quả Pareto (Việc 2) |
| `Output/Test3/pareto_summary.txt` | Tóm tắt violation/compression |
| `Output/Test3/od_patched_gate_summary.csv` | 108 cell gate OD sau patch |
| `Output/Test3/od_patched_small_raw.csv` | Subset-level, grid nhỏ, sau patch |
| `Output/Test3/od_patched_big_raw.csv` | 157.604 dòng Q2/Q3, grid lớn, sau patch |
| `Output/Test3/od_patched_k1_rates.csv`, `..._big.csv` | feasibility_rate_k1 từng cell |
| `experiments/T2BFS/t2_core.py` | + `label_of`, `dominates`, `filter_pareto_with_sched`, `bfs_generate_pareto` |
| `experiments/T2BFS/t2_gen.py` | Patch: neo ready_time theo tau, corridor-weighted P/D |
| `experiments/T2BFS/t3_pareto.py` | Runner Việc 2 |
| `experiments/T2BFS/t3_check_k1.py` | Check `feasibility_rate_k1 >= 0.5` |
| `experiments/T2BFS/t3_rerun_od.py` | Runner Việc 1 (gate+Q2+Q3, OD only, patched) |

**Lưu ý:** patch trong `t2_gen.py` áp dụng cho MỌI lần chạy `t2_gen.build_instance` với `driver_cls=
"OD"` kể từ giờ — bao gồm cả nếu ai đó chạy lại `t2_run.py` (Test2 gốc) sau này. Các CSV gốc của
Test2 (`Output/Test2/*.csv`, `Test2_report.md`) **không bị ghi đè** — chúng phản ánh hành vi TRƯỚC
patch và vẫn đúng như một snapshot lịch sử của bug đã tìm thấy.
