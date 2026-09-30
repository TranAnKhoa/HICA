# Report: RQ1 — Complementarity GW×OD

> Thực thi đầy đủ theo `Rq1.md` Mục 10 (Bước 1-8). Toàn bộ tham số (θ, q_o, r0,
> alignment targets, seed policy) đã khóa TRƯỚC khi chạy instance đầu tiên
> (`rq1_locked_params.json`, hash SHA-256 `16a84c77...`). Báo cáo TOÀN BỘ 60
> cell, không cherry-pick (Sec8).

**Kết luận một câu:** Complementarity gain (JOINT so với tốt nhất trong
GW-only/OD-only) gần như **bằng 0** ở alignment ≤ 0.50, bắt đầu xuất hiện rõ
ở alignment=0.70 (median ~0.9-2.2%), và chỉ đáng kể ở alignment=0.90
(median ~4.2-7.8%, trung bình cell ~5.9%). **Đây là kết quả hợp lệ theo đúng
dự trù ở Sec9 dòng 197-200**: complementarity chỉ xuất hiện rõ ở mức alignment
cao — phát hiện "hai lớp GW/OD chỉ bổ trợ đáng kể khi hành trình OD trùng
vùng demand ở mức cao" là kết luận chính, không phải một kết quả thất bại
cần giấu.

---

## 0. Tình trạng thực thi Mục 10

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 1 | θ_i, q_o generation + unit-check (§1.1-1.3) | Hoàn tất |
| 2 | Calibration pass q_o (§1.4) | Hoàn tất — base_fee=8.0, rate_per_km=3.0 |
| 3 | Alignment metric + calibration curve (§3) | Hoàn tất — r0=1.3615km, 5 target đã khóa (2 deviation tại 0.10/0.30) |
| 4 | 2 sequential treatment (§5) | Hoàn tất — `rq1_treatments.py` |
| 5 | Dry-run gate n≤6 (§7) | **PASS 0/360 violation** |
| 6 | Khóa `rq1_locked_params.json`, hash | Hoàn tất — SHA-256 `16a84c77...` |
| 7 | Full 60-cell grid, naive Algorithm C | Hoàn tất — 1,500 instance × 5 treatment = 7,500 solve, **tất cả OPTIMAL** |
| 8 | Phân tích §6, toàn bộ đường cong | Báo cáo này |

## 1. Dry-run gate (§7) — bắt buộc trước khi tin số liệu

So JOINT + 4 treatment còn lại (bao gồm 2 sequential — code path MỚI) với
**oracle exhaustive độc lập** (không CPLEX): route pool từ `brute_force.py`
(đã audit độc lập, dùng lại từ Gate 0/616/160 và Testb_hull_final.md), WDP
giải bằng duyệt toàn bộ tổ hợp thuần Python (n≤6 đủ nhỏ).

```
Grid: n∈{3,4,5,6} × (B_gw,B_od)∈{(2,2),(3,2),(2,3)} × tw∈{60,120} × seed∈{0,1,2}
= 72 instance × 5 treatment = 360 check
Kết quả: 0/360 violation — PASS
```

**Lần chạy đầu tiên FAIL 7/360** (chỉ ở treatment GW-FIRST) — nhưng lỗi nằm
ở **chính oracle** (`rq1_dryrun_gate.py`), không phải pipeline: khi tra cứu
lại chi phí đã chọn ở Pass 1 theo bundle, code lấy nhầm điểm Pareto ĐẦU TIÊN
thay vì điểm THẬT SỰ được chọn trong lời giải tối ưu (1 bundle có thể có
nhiều điểm (K,W) khác chi phí thật). Sửa bằng cách lưu trực tiếp (bundle,
cost) đã chọn trong quá trình tìm kiếm thay vì tra cứu lại. Pipeline CPLEX
(`rq1_treatments.py`) đúng từ đầu — đây là minh chứng gate hoạt động đúng
chức năng (bắt lỗi ở khâu so sánh, không phải khâu bị so sánh).

## 2. Tối ưu hiệu năng (trước khi chạy full grid)

Đo thời gian mẫu 1 cell tại n=20 (nặng nhất): ~46s/replication → ước tính
toàn grid ~8.6 giờ. Nguyên nhân: Algorithm A (route pool) bị chạy lại **4
lần/replication** (JOINT, GW-ONLY, OD-ONLY, 2 pool của sequential) dù pool
của mỗi driver hoàn toàn độc lập với driver khác (đã xác nhận thực nghiệm:
pool của 1 driver giống hệt dù chạy riêng hay chạy cùng driver khác).

**Tối ưu:** build route pool 1 lần/replication cho toàn bộ driver, slice
theo driver id cho từng treatment thay vì build lại (`build_joint_pool()` +
các hàm `run_*_from_pool()` trong `rq1_treatments.py`). Giảm ~3.5x (n=20:
46s → 13s/replication). Dry-run gate **chạy lại trên đúng code path tối ưu
này** (không phải bản chưa tối ưu) — vẫn PASS 0/360 — trước khi đưa vào main
grid.

## 3. Main grid — 60 cell, kết quả thực thi

```
5 alignment × 3 n × 4 supply ratio = 60 cell × 25 replication = 1,500 instance
× 5 treatment = 7,500 solve CPLEX
Thời gian thực tế: 54.6 phút (nhanh hơn ước tính 2.6 giờ nhờ tối ưu §2 +
n nhỏ/supply ratio thấp chạy nhanh hơn worst-case đã đo)
```

**Gate §7 kiểm tra sau khi chạy xong:**
- OPTIMAL/gap=0: **7,500/7,500 — 100%**, không có solve nào bị loại khỏi
  bảng kinh tế.
- JOINT weakly dominates mọi treatment khác trên MỌI replication (đúng theo
  lý thuyết — JOINT có không gian hành động lớn nhất): **0/6,000 vi phạm**
  (6,000 = 1,500 replication × 4 so sánh JOINT-vs-{GW-only,OD-only,OD-FIRST,
  GW-FIRST}).
- Không có cell nào có `min(C_GW-only, C_OD-only) = 0` (proxy cho "1 lớp
  thắng trắng tuyệt đối") — **0/60 cell** rơi vào trường hợp này.
- Không có trường hợp nào JOINT thua sequential treatment (Sec9 dòng
  201-202 — tín hiệu ngược cần điều tra riêng): **0/1,500 replication**.

## 4. Đường cong Complementarity Gain theo Alignment — TOÀN BỘ, không cherry-pick

Gain = `[min(C_GW-only, C_OD-only) − C_joint] / min(C_GW-only, C_OD-only)`,
trung bình của **median mỗi cell** (12 cell/alignment level = 3 n × 4 supply
ratio), mỗi cell đã tính median + IQR + 95% bootstrap CI (clustered theo
replication — 5 treatment trên cùng 1 instance dùng chung 1 draw, không coi
là 5 mẫu độc lập khi bootstrap).

| alignment target | mean của 12 median cell | range median cell | Ghi chú |
|---:|---:|---:|---|
| 0.10 | 0.01% | 0.00% - 0.13% | `[DEVIATION]` — target thật đạt được chỉ 0.35 (xem `rq1_locked_params.json`) |
| 0.30 | 0.08% | 0.00% - 0.35% | `[DEVIATION]` nhẹ — target thật đạt được cũng 0.35 (cùng combo corridor_share/buffer với 0.10) |
| 0.50 | 0.00% | 0.00% - 0.00% | Đạt đúng target, không deviation |
| 0.70 | 0.93% | 0.00% - 2.16% | Đạt đúng target |
| 0.90 | 5.86% | 4.24% - 7.80% | Đạt đúng target |

**Toàn bộ 60 cell (chi tiết đầy đủ trong `results/rq1_analysis_by_cell.csv`)
đều được báo cáo — không có cell nào bị loại hay giấu.**

Xu hướng đơn điệu tăng rõ ràng theo alignment, nhất quán qua mọi n và mọi
supply ratio (xem chi tiết cell-by-cell trong CSV) — không phải hiệu ứng của
1-2 cell riêng lẻ.

## 5. So sánh JOINT với sequential treatment (Sec6 dòng 163-165)

Ngoài so với GW-only/OD-only, so trực tiếp JOINT với OD-FIRST→GW và
GW-FIRST→OD (không phải min của 2 cái, mà so RIÊNG từng cái — câu hỏi khác:
"thứ tự có quan trọng không" tách biệt khỏi "cùng bid có tốt hơn 1 lớp
không"):

- **JOINT vs OD-FIRST→GW**: gain rất nhỏ xuyên suốt mọi alignment (median
  0.00% ở hầu hết cell, cao nhất ~0.5% tại alignment=0.90) — OD-FIRST→GW gần
  như đã đạt hiệu quả ngang JOINT.
- **JOINT vs GW-FIRST→OD**: gain LỚN HƠN nhiều so với OD-FIRST→GW ở alignment
  cao (0.70-0.90: median 1.3-5.3%, có cell tới 8.4% IQR) — GW-FIRST→OD (ưu
  tiên GW trước) mất nhiều giá trị hơn hẳn so với ưu tiên OD trước.

**Phát hiện phụ đáng chú ý**: thứ tự xử lý (OD trước hay GW trước) tạo ra
chênh lệch RÕ RỆT — ưu tiên OD trước (OD-FIRST→GW) luôn gần JOINT hơn ưu
tiên GW trước (GW-FIRST→OD). Điều này hợp logic: OD có ít route hơn (do τ
detour budget hẹp), giữ OD lại cho pass sau sẽ lãng phí nhiều cơ hội hơn là
giữ GW lại (GW linh hoạt hơn, "chờ" ít tốn kém hơn). Đây là một finding phụ
đáng đưa vào phần thảo luận, không nằm trong §6 metric chính nhưng liên quan
trực tiếp câu hỏi "giá trị của cùng bid" ở Sec9 dòng 201-202 — ở đây JOINT
KHÔNG thua sequential (nên không kích hoạt điều tra riêng), nhưng độ chênh
giữa 2 sequential treatment tự nó là một tín hiệu về cấu trúc bất đối xứng
GW/OD.

### 5.1 Kiểm chứng cơ chế — OD pool nhỏ hơn GW trên chính instance RQ1

Trước khi đưa finding phụ trên vào phần chính thức, đã kiểm nhanh (theo yêu
cầu người dùng, 2026-09-16): liệu "OD pool nhỏ hơn hẳn" — cơ chế dùng để
giải thích finding phụ — có thật sự đúng trên **chính các instance RQ1 đã
dùng** (alignment=0.70, 0.90), hay chỉ đúng ở hot cell T5 tách biệt trước đó.

**Cách kiểm:** tái tạo chính xác các instance đã chạy trong RQ1 main grid tại
2 alignment level này (dùng đúng `instance_seed_formula` đã khóa trong
`rq1_locked_params.json` + đúng `corridor_share`/`corridor_buffer_km` đã
khóa), chạy Algorithm A (`dp_labeling.build_route_pool`, không đổi logic),
đếm số bundle/driver, tách theo `cls` (GW/OD). Không có logic mới — chỉ thêm
1 bước đếm vào output đã có sẵn của Algorithm A. Grid kiểm: `n∈{10,15,20} ×
supply_ratio∈{(2,2),(3,2),(2,3),(3,3)} × 25 replication × 2 alignment level`
= 2,400 instance, tổng 750 driver GW + 750 driver OD/mỗi alignment level.

**Kết quả — alignment=0.70:**

| n | supply (GW,OD) | GW mean bundles/driver | OD mean bundles/driver | ratio OD/GW |
|---:|---:|---:|---:|---:|
| 10 | (2,2) | 175.00 | 2.68 | 0.0153 |
| 10 | (3,2) | 175.00 | 3.40 | 0.0194 |
| 10 | (2,3) | 175.00 | 2.31 | 0.0132 |
| 10 | (3,3) | 175.00 | 2.57 | 0.0147 |
| 15 | (2,2) | 575.00 | 4.82 | 0.0084 |
| 15 | (3,2) | 575.00 | 4.62 | 0.0080 |
| 15 | (2,3) | 575.00 | 4.48 | 0.0078 |
| 15 | (3,3) | 575.00 | 4.00 | 0.0070 |
| 20 | (2,2) | 1350.00 | 7.12 | 0.0053 |
| 20 | (3,2) | 1350.00 | 9.62 | 0.0071 |
| 20 | (2,3) | 1350.00 | 8.20 | 0.0061 |
| 20 | (3,3) | 1350.00 | 6.44 | 0.0048 |

Tổng hợp (750 driver GW, 750 driver OD): GW mean=700.00 (median=575.00,
min=175, max=1350). OD mean=4.95 (median=4.00, min=0, max=40). **Ratio
OD/GW = 0.0071** — OD pool trung bình chỉ bằng 0.71% GW pool.

**Kết quả — alignment=0.90:**

| n | supply (GW,OD) | GW mean bundles/driver | OD mean bundles/driver | ratio OD/GW |
|---:|---:|---:|---:|---:|
| 10 | (2,2) | 175.00 | 8.84 | 0.0505 |
| 10 | (3,2) | 175.00 | 6.58 | 0.0376 |
| 10 | (2,3) | 175.00 | 7.32 | 0.0418 |
| 10 | (3,3) | 175.00 | 6.53 | 0.0373 |
| 15 | (2,2) | 575.00 | 10.54 | 0.0183 |
| 15 | (3,2) | 575.00 | 11.62 | 0.0202 |
| 15 | (2,3) | 575.00 | 11.25 | 0.0196 |
| 15 | (3,3) | 575.00 | 8.61 | 0.0150 |
| 20 | (2,2) | 1350.00 | 19.28 | 0.0143 |
| 20 | (3,2) | 1350.00 | 20.20 | 0.0150 |
| 20 | (2,3) | 1350.00 | 14.92 | 0.0111 |
| 20 | (3,3) | 1350.00 | 17.49 | 0.0130 |

Tổng hợp (750 driver GW, 750 driver OD): GW mean=700.00 (median=575.00,
min=175, max=1350). OD mean=11.75 (median=9.00, min=0, max=75). **Ratio
OD/GW = 0.0168** — OD pool trung bình bằng 1.68% GW pool.

**Nhận xét:**
- GW pool giống hệt nhau giữa 2 alignment level (175/575/1350 tại
  n=10/15/20) — đúng kỳ vọng: alignment chỉ tác động vị trí pickup order,
  không tác động ràng buộc τ/B của GW (open route, không home-terminating).
- OD pool tăng theo alignment (0.70→0.90: mean 4.95→11.75, ~2.4x) — hợp lý:
  alignment cao hơn nghĩa là nhiều order pickup nằm gần corridor OD hơn, lọt
  vào τ detour budget của OD nhiều hơn. Nhưng dù tăng, OD pool vẫn nhỏ hơn
  GW pool 1-2 bậc độ lớn ở cả 2 mức.
- Không có cell nào lệch hướng — ratio OD/GW < 1 tuyệt đối ở toàn bộ 24 dòng
  (12 cell × 2 alignment level), không ngoại lệ.

**Kết luận:** cơ chế giải thích finding phụ ở trên (OD-FIRST→GW luôn gần
JOINT hơn GW-FIRST→OD vì OD có ít route hơn, giữ nó lại cho pass sau lãng
phí nhiều cơ hội hơn giữ GW lại) được xác nhận **trực tiếp, định lượng, trên
chính data RQ1** — không còn là suy diễn logic từ hot cell T5 tách biệt
(`Report_Checklist_Diagnosis.md` Part C1). An toàn để đưa finding phụ này
vào phần chính thức của luận văn.

Script/log kiểm tra: `spec_2a_2b/src/rq1_pool_size_check.py`,
`spec_2a_2b/results/rq1_pool_size_check.log` (dùng lại seed formula + tham
số đã khóa của `rq1_main_grid.py`, không cần CPLEX — chỉ chạy Algorithm A).

## 6. `[DECISION]` Theo Sec9

Kết quả rơi vào nhánh thứ hai của Sec9 (dòng 197-200): **"Complementarity
nhỏ/chỉ xuất hiện ở alignment phi thực tế"** — cụ thể hơn: complementarity
chỉ đáng kể (~5-8%) ở alignment=0.90 (mức cao nhất trong lưới, và bản thân
việc đạt alignment=0.90 cần corridor_share=1.0 — mọi order pickup đều được
"kéo" gần corridor OD, một chế độ sinh instance khá cực đoan). Ở 4/5
alignment level còn lại (0.10-0.70), gain trung bình dưới 1%.

Theo đúng quy tắc đã khóa trước (Sec9): đây là **một finding hợp lệ** —
"hai lớp GW/OD chỉ bổ trợ đáng kể khi hành trình cá nhân của OD trùng vùng
demand ở mức rất cao" — không phải kết quả thất bại. Theo Sec9, phát hiện
này gợi ý **chuyển trọng tâm bài sang phần lý thuyết/cấu trúc** (Lemma T4 —
forward label-setting DP, Proposition T5 — supported completeness/component
decomposition), với RQ1 đóng vai trò một kết quả thực nghiệm bổ trợ có giới
hạn rõ ràng, không phải trụ cột chính — target hướng về thuần C&OR thay vì
kết hợp OR+Economics rộng hơn.

## 7. Không vi phạm quy tắc chống bịa kết quả (Sec8)

1. Hash `rq1_locked_params.json` (SHA-256 `16a84c77...`) ghi TRƯỚC instance
   đầu tiên của main grid — xác nhận tại đầu file JSON.
2. Toàn bộ 60 cell được báo cáo (bảng §4, CSV đầy đủ `rq1_analysis_by_cell.csv`)
   — không chỉ trình bày cell "đẹp" (alignment=0.90).
3. Không có sửa tham số giữa chừng — grid chạy 1 lần liên tục 54.6 phút,
   không dừng/patch.
4. Không tinh chỉnh alignment target/supply ratio/θ/q_o sau khi xem kết quả
   sơ bộ.
5. Kết luận "complementarity chỉ đáng kể ở alignment cao" được viết đầy đủ
   vào báo cáo này — không giấu.

---

## File & tái tạo

```
spec_2a_2b/src/rq1_cost_gen.py           theta_i, q_o generation (Sec1)
spec_2a_2b/src/rq1_alignment.py          alignment metric + calibration curve (Sec3)
spec_2a_2b/src/rq1_treatments.py         5 treatment (Sec5) + toi uu build_joint_pool
spec_2a_2b/src/rq1_wdp.py                cau noi pool -> CPLEX WDP (Sec2/Sec8 de cuong)
spec_2a_2b/src/rq1_dryrun_gate.py        Gate Sec7 - 0/360 PASS (oracle exhaustive doc lap)
spec_2a_2b/src/rq1_main_grid.py          Main grid runner (Sec10 Buoc7) - 60 cell
spec_2a_2b/src/rq1_analysis.py           Phan tich Sec6/Buoc8 - complementarity gain + bootstrap CI
spec_2a_2b/src/rq1_pool_size_check.py    Kiem tra §5.1 - GW vs OD pool size tren chinh instance RQ1
spec_2a_2b/results/rq1_locked_params.json    Toan bo tham so khoa + hash SHA-256
spec_2a_2b/results/rq1_main_grid_results.csv 7,500 dong (1,500 replication x 5 treatment)
spec_2a_2b/results/rq1_analysis_by_cell.csv  60 dong (1 dong/cell, median/IQR/CI)
spec_2a_2b/results/rq1_pool_size_check.log   Output day du kiem tra §5.1 (24 dong chi tiet + tong hop)
```

Chạy lại (Python 3.7.7, cần CPLEX active cho main_grid/dry_run_gate):
```
python rq1_dryrun_gate.py     # ~vai phut, gate bat buoc truoc grid
python rq1_main_grid.py       # ~55 phut, ghi CSV
python rq1_analysis.py        # ~vai giay, doc CSV, in + ghi rq1_analysis_by_cell.csv
python rq1_pool_size_check.py # ~vai phut, kiem tra §5.1 (khong can CPLEX)
```
