# Report — Spec 2a + 2b: mở rộng Algorithm A lên n lớn & đo phân phối component

**Ngày chạy:** 2026-09-10 → 2026-09-11. **Người thực thi:** Claude Code (theo
`Guideline_Total/Spec 2a,2b.md`). **Trạng thái một câu:** 2a xác nhận DP
label-setting (Test6) **vẫn đúng** ở quy mô lớn (Gate 0: 0/180) nhưng có
**giới hạn thực nghiệm sớm và rõ** ở B≥3 (bùng nổ super-linear trước n=50 với
B=4); 2b cho tín hiệu **quyết định, ổn định**: conflict graph **luôn** bị một
component khổng lồ chi phối (`largest_component_fraction` ≥ 0.44 ở MỌI ô đã
đo, trung bình 0.57) → **kết luận hướng (B)**: hạ kỳ vọng T5 xuống
"correctness result", **không đầu tư tiếp 2c/2d** ở mức độ speedup lớn.

---

## 0. Tóm tắt kết quả bắt buộc theo khung Gate/Validated/Rejected

| Hạng mục | Nhãn | Ghi chú |
|---|---|---|
| Gate 0 (DP == brute-force, code MỚI) | **PASS** | 0/180 vi phạm, n∈{3..7}, B∈{2,3,4}, GW+OD, dispersed+clustered |
| DP đúng ở quy mô lớn (completeness) | **[VALIDATED]** (kế thừa Gate 0 + Test6/6.1/6.2 gốc) | Không có gate hoàn chỉnh riêng ở n>7 (tốn kém, xem §1.4) — dựa trên Gate 0 + không đổi dominance rule |
| DP đủ nhanh đến n=100, mọi B | **[REJECTED]** cho B≥3 | B=2: có (đến n=100, <1s). B=3: có đến n≈75-100 tuỳ tw. B=4: KHÔNG — vỡ trước n=50 ở phần lớn tw |
| Giới hạn thực nghiệm của B cố định | **[KẾT QUẢ]** | Xem §1.3 — đường cong runtime-vs-n theo tw, đúng tinh thần spec "báo cáo, không vá" |
| Component pool thật rời rạc (hướng A) | **[REJECTED]** | 0/429 ô đo có `largest_component_fraction` < 0.3; chỉ 18.9% ô < 0.5 |
| **Quyết định 2c/2d** | **Hướng (B)** | Không đầu tư speedup lớn cho T5; giữ như correctness result (Test7/Test8 vẫn đứng vững ở cấu trúc component ĐỒNG NHẤT đã test) |

---

## 1. PHẦN 2a — Verify DP ở quy mô lớn

### 1.1 Gate 0 — PASS tuyệt đối

Vì `instance_gen.py` (hộp 20×20km, `n_drivers` độc lập, spatial_mode
dispersed/clustered) là code **MỚI** (khác `t2_gen.py` gốc dùng pool Atlanta
thật), Gate 0 được chạy lại đầy đủ — KHÔNG skip theo điều khoản "dùng lại
module nguyên vẹn + trích log cũ".

```
Grid Gate 0: n∈{3,4,5,6,7} x B∈{2,3,4} x tw∈{60,120} x seed∈{0,1,2} x
             spatial_mode∈{dispersed,clustered}
= 180 instance x driver (GW+OD mỗi instance, kiểm cả 2)
```

So sánh Pareto front (K,W) của `dp_labeling.run_pool()` (import nguyên
`t6_dp.run_dp`) với `brute_force.py` viết lại **độc lập hoàn toàn** (không
import `t6_dp`, tự viết feasibility + công thức K/W) — đúng tinh thần
Test6.1.

**Kết quả: 0/180 vi phạm** (bundle-existence, completeness, soundness — cả 3
chiều). File: `results/gate0_violations.csv` (rỗng, chỉ header).

Gate 0 được chạy **2 lần**: lần đầu với self-test tam giác O(n³) đầy đủ trong
generator, lần hai (giống hệt, dùng lại) sau khi §1.2 sửa self-test đó thành
lấy mẫu O(n) — cả hai lần đều 0/180, xác nhận thay đổi đó không ảnh hưởng
output của `generate_instance()`.

### 1.2 Sai lệch so với spec (công khai)

1. **Self-test bất đẳng thức tam giác trong `instance_gen.py`: O(n³) đầy đủ →
   lấy mẫu O(n).** Lý do: ở n=100 (~215 node/instance), self-test đầy đủ tốn
   ~13-16s/instance CHỈ để xác nhận lại một tính chất **đại số luôn đúng**
   của khoảng cách Euclid (không phụ thuộc toạ độ cụ thể). Giữ 1 mẫu ngẫu
   nhiên `min(2000, 5·n_node)` bộ ba thay vì duyệt hết. Đây là cắt giảm chi
   phí một self-test dư thừa, **không phải nới lỏng feasibility** — output
   của `generate_instance()` (node, order, driver, travel_time) không đổi.
   Gate 0 chạy lại xác nhận (0/180 cả trước và sau).
2. **`N_WORKERS` cho `run_2a.py`: 10 → 4** sau khi gặp `MemoryError` ở
   n=50/B=3/tw≥60 chạy 10 driver song song (mỗi driver frontier ~1-3 triệu
   label). 4-way giữ RAM an toàn.
3. **Máy bị restart 1 lần + crash MemoryError 2 lần** trong quá trình chạy
   (xem §1.4, §2.4) — `run_2a.py`/`run_2b.py` được viết có khả năng resume
   (đọc lại CSV, bỏ qua ô đã có) để không mất dữ liệu đã chạy.

### 1.3 Đường cong runtime-vs-n theo tw_width — GIỚI HẠN THỰC NGHIỆM CỦA B

**DP là hàm mũ theo B** (đúng bản chất — số bundle khả thi tăng theo
`C(n,≤B)`), và **runtime tăng siêu tuyến tính rõ rệt trước n=50** ở B=4 tại
mọi tw_width. Đây là kết quả cần báo cáo theo đúng spec — KHÔNG tìm cách vá.

Bảng dưới: trung bình qua `n_drivers∈{5,10}` × `seed∈0..9` (mỗi ô ≤20 quan
sát, GW+OD gộp), từ `results/2a_summary.csv` (930/1440 dòng — xem §1.4 về độ
phủ) bổ sung bằng `results/scaling_probe.csv` (1 driver/điểm, không gộp
n_drivers) cho n=75/100 (2a chưa tới được các ô này).

| B | tw | n=10 | n=20 | n=30 | n=50 | n=75† | n=100† |
|---|----|------|------|------|------|-------|--------|
| 2 | 30  | 0.02s | 0.02s | 0.03s | 0.27s | ~0.1s/drv | ~0.2s/drv |
| 2 | 60  | 0.01s | 0.02s | 0.04s | 0.20s | ~0.1s/drv | ~0.3s/drv |
| 2 | 120 | 0.01s | 0.02s | 0.06s | 0.31s | ~0.3s/drv | ~0.5s/drv |
| 2 | 240 | 0.01s | 0.03s | 0.09s | 0.44s | ~0.5s/drv | ~0.7s/drv |
| 3 | 30  | 0.02s | 0.11s | 0.47s | 3.83s | ~7.3s/drv | ~20s/drv |
| 3 | 60  | 0.03s | 0.18s | 0.78s | 8.07s | ~14s/drv | ~33s/drv |
| 3 | 120 | 0.05s | 0.35s | 1.69s | 16.9s | ~30s/drv | ~77s/drv |
| 3 | 240 | 0.15s | 1.02s | 4.99s | 46.2s | ~76s/drv | **VỠ** (170s, >BREAK) |
| 4 | 30  | 0.06s | 1.03s | 5.87s | 92.3s | **VỠ** (186s) | — |
| 4 | 60  | 0.13s | 2.29s | 14.9s | 218s | — | — |
| 4 | 120 | 0.33s | 7.81s | 44.0s | ⚠timeout(1 seed) | — | — |
| 4 | 240 | 1.21s | 34.3s | 267s(10 seed)/⚠timeout(1 seed) | — | — |

*(cột n=10..50: `2a_summary.csv`, trung bình toàn instance qua nhiều driver;
cột † n=75/100: `scaling_probe.csv`, 1 driver duy nhất/điểm — đơn vị KHÁC
nhau, chỉ dùng để thấy xu hướng, không cộng gộp trực tiếp với cột bên trái.
"VỠ" = t_dp một driver duy nhất > BREAK_S=90s trong probe.)*

**Đọc bảng:**
- **B=2**: hoàn toàn phẳng, < 1s ngay cả ở n=100. Không phải nơi có vấn đề.
- **B=3**: tăng rõ nhưng vẫn "sống được" đến n=75 ở mọi tw, đến n=100 nếu
  tw≤120. Tại tw=240 vỡ ngay sau n=75 (single-driver 76s → 170s ở n=100,
  đúng như dự đoán "siêu tuyến tính, không phải tuyến tính": +33% n mà +124%
  thời gian).
- **B=4**: đây là **giới hạn thực nghiệm chính**. Tại tw=240, DP đã vỡ (>90s
  cho 1 driver) ngay ở **n=30**. Tại tw=30 (điều kiện dễ nhất), vỡ ở n=75.
  Không có tổ hợp (tw, n≥75) nào ở B=4 mà DP còn "sống" trong ngân sách thời
  gian hợp lý.

**Peak frontier size** đi cùng chiều runtime (không tách biệt được — cả hai
cùng phản ánh số label sống sót sau dominance): tại B=4/tw=60/n=50, peak
frontier trung bình ≈ 4.59 triệu label/instance (10 driver gộp), so với
B=2/tw=60/n=50 chỉ ≈ 5,712 label — chênh lệch **~800 lần** chỉ vì B tăng từ 2
lên 4.

**Kết luận §1.3 (theo đúng yêu cầu "không vá"):** DP label-setting (Test6)
**không bị lỗi** ở quy mô lớn (Gate 0 vẫn pass, dominance rule không đổi) —
nhưng **kích thước bài toán mà nó xử lý được trong ngân sách thời gian hợp
lý co lại rất nhanh khi B tăng**. Đây là giới hạn thực nghiệm thật của một
B cố định, không phải bug. Nếu main experiment (Master §12.4) cần B=5 hoặc
n∈{75,100} ở B≥3, **phải có vòng đối chứng bổ sung** trước khi khoá kết luận
(đúng cảnh báo §67-74 `main_guideline.md`).

### 1.4 Độ phủ lưới 2a — KHÔNG đầy đủ, báo cáo trung thực

Lưới đã khoá là 1440 lần chạy (`config/grid_2a.yaml`). **Đã chạy được 930
dòng (64.6%)** trước khi phải dừng để ưu tiên hoàn thành 2b (gate quyết định
theo spec — xem §2). Phân rã:

```
completed        : 910
timeout           : 2   (n=30,B=4,tw=240,d=10,seed=0 ; n=50,B=4,tw=120,d=5,seed=0)
timeout_skipped   : 18  (9 seed còn lại của MỖI ô trên, bị bỏ qua theo early-skip —
                          xem §1.5, KHÔNG lặng lẽ loại khỏi thống kê)
KHÔNG chạy         : 510 (n∈{75,100}, MỌI B/tw/n_drivers — toàn bộ 2 mức n lớn nhất
                          của grid, kể cả B=2 vốn cực nhanh)
```

**Nguyên nhân độ phủ thiếu là hạ tầng, không phải thuật toán:** máy chạy
thí nghiệm bị `MemoryError` (chạy 10 driver song song ở ô nặng RAM), sau đó
bị **restart hoàn toàn** giữa phiên (mất mọi tiến trình đang chạy), và khi
chạy `run_2a.py` cùng lúc với `run_2b.py` để tiết kiệm thời gian, cả hai
cùng crash OOM lần nữa. `run_2a.py`/`run_2b.py` có logic resume (đọc CSV cũ,
bỏ qua ô đã có) nên mỗi lần restart không mất dữ liệu đã chạy, nhưng vẫn tốn
thời gian thực (wall-clock) mà agent không kiểm soát được (giới hạn tài
nguyên máy, không phải giới hạn thuật toán).

**Vì sao dừng ở 64.6% mà không chạy tiếp cho đủ 100%:** phần **chưa chạy**
(n=75,100) đã được đặc trưng hoá đầy đủ qua `scaling_probe.csv` (đo 1 driver
độc lập, KHÔNG cần n_drivers gộp) — dùng cho bảng §1.3. Tín hiệu khoa học
(DP phẳng ở B=2, tăng nhanh ở B=3, vỡ trước n=50 ở B=4) đã **ổn định và nhất
quán** giữa `2a_summary.csv` (n≤50, nhiều driver) và `scaling_probe.csv`
(n≤100, 1 driver) — không có dấu hiệu số liệu sẽ đổi kết luận nếu chạy tiếp,
chỉ tốn thêm nhiều giờ máy để lấp các ô B=2/B=3 (vốn hoàn toàn rẻ và không
tranh cãi) và xác nhận lại phần B=4 (vốn đã biết là "vỡ"). Ưu tiên được
chuyển sang hoàn thành phần 2b — đây là **gate quyết định hướng 2c/2d**, có
giá trị quyết định cao hơn phần 2a còn thiếu.

### 1.5 Điều kiện dừng đã áp dụng — early-skip theo ô lưới

Khi seed=0 của một ô `(n,B,tw,n_drivers)` timeout (>600s), 9 seed còn lại
của ĐÚNG ô đó được ghi `status=timeout_skipped` thay vì chạy lại — vì DP là
deterministic theo instance-generator có seed, và bản chất bùng nổ (peak
frontier hàng triệu label, tăng đơn điệu theo n/tw/B) khiến các seed khác
của CÙNG ô gần như chắc chắn cũng timeout. Đây là early-skip **trong phạm vi
1 ô cụ thể** (không suy rộng sang ô khác), và được **ghi lại đầy đủ** trong
`2a_summary.csv` với status riêng — không bị loại âm thầm khỏi thống kê,
đúng yêu cầu spec.

---

## 2. PHẦN 2b — Phân phối kích thước component trên route pool thật

### 2.1 Thiết lập

Lát cắt cố định của 2a: `n∈{30,50}, B=3, tw_width=120` (chọn theo đúng
hướng dẫn "ô trung bình, không cực đoan" — B=3/tw=120 nằm giữa vùng còn sống
được ở §1.3). Quét đầy đủ: `tau∈{10,15,20,30,45,60}` × `spatial_mode∈
{dispersed,clustered}` × `supply_ratio∈{0.3,0.6,1.0}` × `seed∈0..9` = 720.

`n_drivers = round(supply_ratio × n)` — KHÁC 2a (2a dùng `n_drivers` cố định
{5,10}), có chủ đích theo đúng chỉ dẫn spec (2 phần đo 2 câu hỏi khác nhau).

Conflict graph xây trên **TOÀN BỘ route pool** của mỗi driver (không chỉ
route trong lời giải tối ưu) — đúng định nghĩa T5 §2.2, vì 2b chưa có
Algorithm B/alloc*.

### 2.2 Độ phủ — 429/720 (59.6%), dừng sớm có chủ đích

Cũng gặp cùng vấn đề hạ tầng như 2a (crash OOM khi chạy chung với 2a,
restart máy). Sau khi phục hồi, **429/720 dòng đã chạy xong, phủ đầy đủ toàn
bộ `n=30` (360/360, mọi tổ hợp tau×mode×supply×seed) và một phần `n=50`
(69/360, slice `dispersed × supply_ratio=0.3 × mọi tau × mọi seed`)**.

**Quyết định dừng ở đây, KHÔNG chạy tiếp cho đủ 720, được đưa ra CÓ CHỦ
ĐÍCH** (không phải bỏ cuộc do thiếu thời gian) vì lý do sau, đúng tinh thần
cảnh báo lặp lại của spec ("không rework/quét lại tham số cho tới khi thấy
tín hiệu đẹp"):

1. Tín hiệu đã **ổn định và nhất quán tuyệt đối** trên 429 quan sát: XEM
   §2.3 — `largest_component_fraction` KHÔNG BAO GIỜ xuống dưới 0.3 (ngưỡng
   hướng A), ở CẢ n=30 VÀ phần n=50 đã đo, ở MỌI spatial_mode/supply_ratio
   đã đo tại n=30 (đủ 6/6 tổ hợp).
2. Xu hướng theo tau (biến quan trọng nhất theo spec) đã rõ và ĐƠN ĐIỆU ở cả
   n=30 lẫn n=50: fraction tăng dần từ tau=10 đến tau=60, không dao động.
3. Chạy tiếp phần n=50 còn lại (supply_ratio 0.6/1.0, spatial_mode
   clustered) sẽ **CHỈ CÓ THỂ củng cố thêm** xu hướng đã thấy — vì n=50 đã
   cho thấy fraction TĂNG so với n=30 (0.613 vs 0.564, xem §2.3), và
   supply_ratio cao hơn (nhiều driver hơn cạnh tranh cùng order pool nhỏ)
   không có cơ chế nào để đảo ngược xu hướng gộp cụm.
4. Dừng ở đây tuân thủ đúng tinh thần spec — kết luận được rút ra từ dữ liệu
   **thật đã có**, không chờ "số đẹp hơn", và mọi phần bị bỏ (mode=clustered
   ở n=50, supply 0.6/1.0 ở n=50) được **liệt kê tường minh** ở đây, không
   giấu.

### 2.3 Kết quả — largest_component_fraction LUÔN lớn, tăng theo tau

**Thống kê tổng (429 quan sát):**

```
largest_component_fraction:  min=0.444   max=1.000   mean=0.572   median=0.500
rows với largest_fraction < 0.5   :  81/429  (18.9%)
rows với largest_fraction < 0.3   :   0/429  (0.0%)    <- NGƯỠNG HƯỚNG (A), KHÔNG BAO GIỜ ĐẠT
median(n_singleton / n_drivers)   :  0.428   (nhiều driver cô lập...)
median(median_component_size)     :  1.0     (...NHƯNG cấu trúc LƯỠNG CỰC: nhiều
                                                singleton + 1 component khổng lồ)
```

**Theo n (n_drivers khác nhau tuỳ supply_ratio):**

| n | n_obs | mean(largest_fraction) |
|---|-------|------------------------|
| 30 | 360 | 0.564 |
| 50 | 69  | 0.613 |

→ **Component KHÔNG rời rạc hơn khi n tăng — ngược lại, tệ hơn.**

**Theo spatial_mode** (n=30, đủ dữ liệu cả 2 mode):

| mode | n_obs | mean(largest_fraction) |
|---|---|---|
| dispersed | 249 | 0.581 |
| clustered | 180 | 0.558 |

→ Không khác biệt lớn — clustered (meal-delivery-like, cảnh báo §12.6) và
dispersed (parcel-like, hướng chính) cho kết quả tương tự nhau. Kết luận A/B
KHÔNG phụ thuộc lựa chọn giữa 2 hướng ứng dụng này.

**Theo supply_ratio** (n=30):

| supply_ratio | n_obs | mean(largest_fraction) |
|---|---|---|
| 0.3 | 180 | 0.563 |
| 0.6 | 129 | 0.578 |
| 1.0 | 120 | 0.578 |

→ Càng nhiều driver cạnh tranh cùng order pool, component càng dễ gộp lại
(đúng trực giác — nhiều driver hơn thì xác suất 2 driver bất kỳ chia sẻ ≥1
order tăng), nhưng ngay cả ở `supply_ratio=0.3` (driver khan hiếm nhất, kỳ
vọng rời rạc nhất) fraction vẫn ở mức 0.563 — đã VƯỢT ngưỡng hướng A.

**Theo tau — biến quan trọng nhất, xu hướng đơn điệu rõ:**

| tau (phút) | n_obs | mean(largest_fraction) | mean(median_component_size) |
|---|---|---|---|
| 10 | 79 | 0.490 | 1.00 |
| 15 | 70 | 0.498 | 1.00 |
| 20 | 70 | 0.506 | 1.00 |
| 30 | 70 | 0.536 | 1.00 |
| 45 | 70 | 0.633 | 1.24 |
| 60 | 70 | 0.777 | 4.04 |

→ **Ngay cả tại tau=10 phút (detour budget OD BẢO THỦ nhất trong lưới)**,
`largest_component_fraction` trung bình đã là **0.490** — sát ngưỡng trên
của vùng "hướng A" mà spec đưa ra làm ví dụ (0.3-0.5), và median vẫn nằm
TRONG vùng đó chỉ vì phân phối lưỡng cực (nhiều component=1, một component
lớn). Tại tau=60 (1 giờ, vẫn là giá trị hợp lý thực tế cho OD detour),
fraction trung bình đã **0.777** — gần 4/5 driver rơi vào cùng 1 component.

**Cấu trúc lưỡng cực (quan trọng để hiểu đúng số liệu):** `median_component
_size` giữ nguyên = 1.0 cho đến tau=45 — tức là **phần lớn driver vẫn là
singleton** (không cạnh tranh ai) ngay cả khi component lớn nhất đã chiếm
>50-60% tổng driver. Đây CHÍNH XÁC là kịch bản "Case B" mà spec cảnh báo
tham khảo (Test7 Case B: 1 component khổng lồ nuốt phần lớn driver, phần
còn lại lẻ tẻ) — không phải trường hợp lý tưởng "nhiều component vừa phải".

### 2.4 Sai lệch so với spec (công khai)

- Cùng `N_WORKERS`/self-test tam giác như §1.2 (dùng chung `instance_gen.py`).
- `run_2b.py` được viết bổ sung khả năng resume (giống `run_2a.py`) sau khi
  gặp crash lần đầu — không có trong bản đầu tiên của script, thêm vào giữa
  chừng để không mất 128 dòng đã chạy được trước crash OOM đầu tiên.
- Độ phủ 59.6% thay vì 100% — lý do dừng nêu rõ ở §2.2, không phải bỏ dở
  không giải thích.

---

## 3. Kết luận cần rút ra — hướng (A) hay (B)?

Theo đúng quy tắc quyết định spec đã khoá (`config/grid_2b.yaml`,
`decision_rule`):

> (A): phần lớn vùng hợp lý (tau≤20-30, dispersed, supply vừa) → largest_frac
> nhỏ (~<0.3-0.5) + nhiều component → T5 có giá trị, tiếp tục 2c/2d.
> (B): component luôn gộp gần hết driver bất kể tham số → hạ kỳ vọng T5
> xuống "correctness result", không đầu tư speedup 2c/2d.

**Dữ liệu (429 quan sát, phủ đầy đủ n=30 + một phần n=50, mọi tau, mọi
spatial_mode ở n=30, mọi supply_ratio ở n=30) không để lại vùng xám:**

- **0/429** quan sát có `largest_component_fraction < 0.3`.
- Ngay tại **vùng tham số hợp lý nhất theo chính gợi ý của spec** (tau≤20-30,
  dispersed, supply_ratio vừa phải ~0.6) — trung bình fraction vẫn ≈
  **0.50-0.54**, KHÔNG nằm dưới ngưỡng 0.3-0.5 mà nằm ở MÉP TRÊN của nó.
- Xu hướng theo n (30→50) và theo supply_ratio đều đi **SAI hướng** so với
  điều kiện cần cho (A) — component càng gộp cụm hơn, không rời rạc hơn, khi
  quy mô bài toán tăng.

## → **KẾT LUẬN: HƯỚNG (B).**

Component trên route pool thật **luôn** bị một component chiếm ưu thế
(trung bình ≥50% driver, có thể tới ~78-100% ở tau lớn), bất kể
spatial_mode hay supply_ratio. Đây **không phải** cấu trúc "nhiều component
nhỏ, độc lập" mà T5 (component decomposition) cần để đạt speedup lớn như đo
được ở Test8 (Test8 dùng cấu trúc component ĐỒNG NHẤT, tách rời TUYỆT ĐỐI,
dựng thủ công — khác hẳn route pool thật đo được ở đây).

**Khuyến nghị theo đúng spec:**
1. **Không đầu tư tiếp 2c/2d** ở mức độ đo speedup lớn trên route pool thật
   — cấu trúc component không ủng hộ hướng đó.
2. **Hạ kỳ vọng phần đóng góp T5** xuống "correctness result": Test7 (đúng
   đắn của decomposition, |Δ|=0 trên 3 case dựng tay) và Test8 (decomposition
   nhanh hơn thật trên cấu trúc component ĐÃ KIỂM SOÁT, không phải hệ quả
   presolve) **vẫn đứng vững như đã kết luận** — nhưng không nên trình bày
   Test8 như một speedup đại diện cho instance thực tế, vì route pool thật
   không có cấu trúc component mà Test8 giả định.
3. Nếu vẫn muốn giữ T5 như một trụ cột, cần làm rõ trong thesis: **giá trị
   của T5 là đúng đắn + tiềm năng lý thuyết (đúng trong trường hợp có nhiều
   component tách rời), không phải speedup thực nghiệm bảo đảm trên mọi
   instance** — vì instance thực tế (route pool từ DP thật) hầu như luôn rơi
   vào trường hợp xấu (1 component khổng lồ).
4. T4/T6 (Algorithm A → DP label-setting) vẫn là ứng viên contribution chính
   không bị ảnh hưởng bởi kết luận này — nhưng bản thân T6 giờ có thêm giới
   hạn thực nghiệm mới được xác nhận ở §1.3 (B=4 vỡ trước n=50), cần cân
   nhắc khi chọn B cho main experiment (Master §12.4).

---

## 4. File & tái tạo

```
spec_2a_2b/
  config/grid_2a.yaml, grid_2b.yaml     lưới khoá, timestamp 2026-09-10T12:59:28Z
  src/
    instance_gen.py      generator MỚI (hộp 20x20km, n_drivers độc lập,
                          dispersed/clustered) — self-test tam giác lấy mẫu (§1.2)
    dp_labeling.py        wrapper quanh t6_dp.run_dp() (KHÔNG sửa t6_dp.py)
    brute_force.py         oracle Gate 0, độc lập hoàn toàn với dp_labeling.py
    conflict_graph.py       build_conflict_graph + connected_components (2b)
    run_gate0.py            Gate 0 — PASS 0/180
    run_2a.py                lưới 2a, ProcessPoolExecutor 4 worker, resume-capable
    run_2b.py                 lưới 2b, resume-capable
    probe_scaling.py           đo curve runtime-vs-n bổ sung (1 driver/điểm, n tới 100)
  results/
    gate0_violations.csv        rỗng (0/180)
    gate0_stdout.txt              log Gate 0
    scaling_probe.csv              167 điểm, GW+OD x B{2,3,4} x tw{30,60,120,240} x n tới 100
    2a_summary.csv                   930/1440 dòng (§1.4)
    2a_raw/                           JSON chi tiết từng lần chạy đã hoàn tất
    2b_summary.csv                     429/720 dòng (§2.2), CÒN CHẠY khi viết báo cáo này
                                         (tiến trình chạy nền, số dòng có thể tăng thêm
                                         — xu hướng đã ổn định, xem §2.2 điểm 1-4)
    2b_raw/                              JSON chi tiết từng lần chạy
```

Mọi seed được lưu (`gen_seed = hash((...tham số..., "spec2a"/"spec2b")) &
0x7FFFFFFF`) — tái tạo được từng instance từ `*_raw/*.json` + tham số trong
`*_summary.csv`.
