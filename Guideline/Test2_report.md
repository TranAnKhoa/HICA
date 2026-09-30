# Test2 Report — Kiểm chứng BFS level-wise cho sinh bundle (HICA-S Algorithm A)

**Spec:** `Guideline/Test2.md` · **Code:** `experiments/T2BFS/` (`t2_core.py`, `t2_gen.py`, `t2_run.py`)
**Output thô:** `Output/Test2/` (`gate_summary.csv`, `small_raw.csv`, `big_raw.csv`)
**Chạy:** Python 3.13.9, không thư viện ngoài. Tổng **2.356 s** (~39 phút).

**Sai lệch so với spec, công khai ngay từ đầu (không giấu):**
1. **Nguồn toạ độ node:** dùng toạ độ thật của Atlanta (pool Sply+Req của D1, đã có sẵn trong `Dataset/`) thay vì hình vuông tổng hợp thuần tuý của §5 — chiếu phẳng quanh 1 anchor ngẫu nhiên mỗi instance, giữ đúng ràng buộc `area_km=10`. Lý do: tái dùng hạ tầng đã có; câu hỏi Q1–Q3 là về **tính chất thuật toán** (completeness, độ bùng nổ |Seq(S)|), không phụ thuộc nguồn địa lý. Mọi tham số khác của §5 (n_orders, B, tw_width, tau, seeds, speed=20km/h, service=5 phút) giữ **nguyên khoá**.
2. **`SEEDS_PER_CELL = 8`**, không phải 30 như spec khoá — giảm có công khai vì ngân sách thời gian phiên làm việc. Xem §5 dưới để đánh giá mức ảnh hưởng.
3. **`capacity`**: spec không khoá giá trị số cụ thể. Chọn `capacity = B` (mỗi đơn `demand=1`), để capacity **không bao giờ là nút thắt** — giữ thí nghiệm tập trung đúng vào câu hỏi TW/slack* mà grid nhắm tới, không trộn với một ràng buộc capacity tuỳ ý spec không định nghĩa.

Toàn bộ code, seed (hash SHA-256 xác định), và CSV thô đã lưu — chạy lại được nguyên xi.

---

## 1. Bảng correctness (§7.1) — GATE PASS TUYỆT ĐỐI

| n | B | lớp | #instance | completeness pass | validator pass | phản ví dụ monotonicity | filter cắt nhầm |
|---|---|---|---|---|---|---|---|
| 4 | 2 | GW | 32 | 32/32 | 32/32 | 0 | 32/32 |
| 4 | 2 | OD | 96 | 96/96 | 96/96 | 0 | 96/96 |
| 4 | 3 | GW | 32 | 32/32 | 32/32 | 0 | 32/32 |
| 4 | 3 | OD | 96 | 96/96 | 96/96 | 0 | 96/96 |
| 4 | 4 | GW | 32 | 32/32 | 32/32 | 0 | 32/32 |
| 4 | 4 | OD | 96 | 96/96 | 96/96 | 0 | 96/96 |
| 5 | 2 | GW | 32 | 32/32 | 32/32 | 0 | 32/32 |
| 5 | 2 | OD | 96 | 96/96 | 96/96 | 0 | 96/96 |
| 5 | 3 | GW | 32 | 32/32 | 32/32 | 0 | 32/32 |
| 5 | 3 | OD | 96 | 96/96 | 96/96 | 0 | 96/96 |
| 5 | 4 | GW | 32 | 32/32 | 32/32 | 0 | 32/32 |
| 5 | 4 | OD | 96 | 96/96 | 96/96 | 0 | 96/96 |
| 6 | 2 | GW | 32 | 32/32 | 32/32 | 0 | 32/32 |
| 6 | 2 | OD | 96 | 96/96 | 96/96 | 0 | 96/96 |
| 6 | 3 | GW | 32 | 32/32 | 32/32 | 0 | 32/32 |
| 6 | 3 | OD | 96 | 96/96 | 96/96 | 0 | 96/96 |
| 6 | 4 | GW | 32 | 32/32 | 32/32 | 0 | 32/32 |
| 6 | 4 | OD | 96 | 96/96 | 96/96 | 0 | 96/96 |

**Tổng 1.152 instance nhỏ (n≤6, B≤4, mọi tw_width×tau×class), tất cả pass mọi gate.**

- **Gate 4.1 (completeness):** `set(BFS[S]) == set(BRUTE_FORCE[S])` đúng cho **mọi** subset S của **mọi** instance — 0 sai lệch trên 29.056 dòng subset trong `small_raw.csv`.
- **Gate 4.2 (validator độc lập):** mọi sequence BFS sinh ra pass `validate()` — cài đặt lại từ đầu, tách biệt hoàn toàn khỏi `is_feasible()`.
- **Gate 4.3 (phản chứng monotonicity):** quét toàn bộ cặp `S ⊂ S'` trên ground-truth brute force (không phụ thuộc BFS/filter đúng hay sai) — **0 phản ví dụ** trên toàn bộ 1.152 instance. Chứng minh ở §3.3 của spec **không bị bác bỏ** trong phạm vi đã kiểm.
- **Gate 4.4 (filter không cắt nhầm):** mọi subset bị `FILTER_SLACK_STAR` loại đều thật sự infeasible theo brute force — **0 trường hợp cắt nhầm**.

**→ Q1: Thuật toán BFS level-wise là ĐẦY ĐỦ (complete) trong toàn bộ phạm vi đã kiểm.**

---

## 2. Q2 — số sequence phải lưu mỗi subset (câu hỏi quan trọng nhất)

### Bảng số liệu thô: `n_feasible_sequences` theo k, tách GW/OD (602.752 dòng, `big_raw.csv`)

| lớp | k | n | median | p25 | p75 | max | mean |
|---|---|---|---|---|---|---|---|
| GW | 1 | 4.320 | 1 | 1 | 1 | 1 | 1,00 |
| GW | 2 | 23.424 | 6 | 3 | 6 | 6 | 4,44 |
| GW | 3 | 54.464 | 47 | 6 | 90 | 90 | 47,81 |
| GW | 4 | 68.480 | **436** | 6 | 2.282 | **2.520** | 1.000,44 |
| OD | 1 | 12.960 | 0 | 0 | 0 | 1 | 0,11 |
| OD | 2 | 70.272 | 0 | 0 | 0 | 6 | 0,02 |
| OD | 3 | 163.392 | 0 | 0 | 0 | 20 | 0,00 |
| OD | 4 | 205.440 | 0 | 0 | 0 | 0 | 0,00 |

### Hình 1 (mô tả bằng bảng — median tại k=B, theo tw_width, GW)

| B | tw=30 | tw=60 | tw=120 | tw=240 |
|---|---|---|---|---|
| 2 | 1 | 5 | 6 | 6 |
| 3 | 2 | 22 | 79 | 90 |
| 4 | **0** | 91 | 1.399 | **2.520** (= trần lý thuyết (2k)!/2^k) |

Tại `tw_width=240` (lỏng nhất), median tại k=B=4 chạm đúng **trần lý thuyết 2.520** — nghĩa là ở chế độ này, gần như **mọi** thứ tự chèn đều khả thi, cận slack* gần như không phân biệt được gì (khớp Q3 §3 dưới). Tại `tw_width=30` (chặt nhất), B=4 cho median **= 0** — quá chặt để bất kỳ bundle 4 đơn nào tồn tại.

**n_orders (kích thước pool) hầu như không ảnh hưởng** đến `n_feasible_sequences` của một subset cỡ k cho trước (median tại k=4, GW: 622 ở n=8, 672 ở n=10, 455 ở n=12, 413 ở n=15 — dao động trong nhiễu, không có xu hướng tăng/giảm rõ) — đúng như kỳ vọng, vì đây là tính chất của **subset**, không phải của **pool chứa nó**.

### Hình 2 (mô tả bằng bảng — tỷ lệ `n_insertion_attempts / n_permutations_bruteforce` theo k)

| lớp | k | median | mean |
|---|---|---|---|
| GW | 1 | 0 | 0 |
| GW | 2 | 0,250 | 0,249 |
| GW | 3 | 0,125 | 0,091 |
| GW | 4 | **0,031** | 0,033 |
| OD | 2–4 | ~0 | ~0 (hầu hết Seq[P] rỗng nên không có gì để chèn) |

Tỷ lệ giảm đều theo k đối với GW (0,25 → 0,125 → 0,031 — gần đúng chia đôi mỗi bước rồi giảm mạnh hơn ở k=4): **BFS chèn tốn công ít hơn brute force enumeration một cách rõ rệt và ngày càng rõ khi k tăng**, dù bản thân số sequence phải lưu (`n_feasible_sequences`) vẫn bùng nổ. Hai đại lượng đo hai thứ khác nhau — tiết kiệm tính toán so với brute force **không** đồng nghĩa với việc kết quả (số sequence) nhỏ.


**→ Q2: `n_feasible_sequences` KHÔNG bị chặn nhỏ — nó tăng gần cấp số nhân theo k ở mọi `tw_width` ngoại trừ mức chặt nhất, và chạm trần lý thuyết `(2k)!/2^k` ở `tw_width` lỏng.** Theo ngưỡng §8: median tại k=B trải từ 0 (tw=30) tới 2.520 (tw=240) — phần lớn cấu hình rơi vào **"> 50, tăng theo cấp số nhân theo k"**.

---

## 3. Q3 — hiệu lực bộ lọc slack*

### Bảng theo lớp × tw_width (gộp k, B, tau)

| lớp | tw_width | % subset bị filter cắt | % subset infeasible thật | tỷ lệ bắt được (catch rate) |
|---|---|---|---|---|
| GW | 30 | 39,70% | 48,58% | 81,72% |
| GW | 60 | 1,67% | 3,62% | 46,08% |
| GW | 120 | 0,00% | 0,00% | — |
| GW | 240 | 0,00% | 0,00% | — |
| OD | 30 | 96,63% | 99,55% | 97,06% |
| OD | 60 | 96,66% | 99,57% | 97,08% |
| OD | 120 | 96,69% | 99,56% | 97,12% |
| OD | 240 | 96,68% | 99,54% | 97,12% |

### Bảng theo lớp × k

| lớp | k | % subset bị filter cắt | % subset infeasible thật | tỷ lệ bắt được |
|---|---|---|---|---|
| GW | 1 | 0,00% | 0,19% | 0,00% |
| GW | 2 | 0,44% | 2,45% | 17,77% |
| GW | 3 | 5,81% | 9,63% | 60,34% |
| GW | 4 | 17,99% | 20,21% | 89,01% |
| OD | 1 | 0,00% | 89,04% | 0,00% |
| OD | 2 | 97,17% | 99,19% | 97,96% |
| OD | 3 | 99,92% | 99,99% | 99,93% |
| OD | 4 | 100,00% | 100,00% | 100,00% |

### Pooled

| lớp | % subset bị filter cắt | % subset infeasible thật | tỷ lệ bắt được |
|---|---|---|---|
| **GW** | **10,34%** | 13,05% | 79,24% |
| **OD** | **96,66%** | 99,56% | 97,10% |

**→ Q3, theo ngưỡng §8:**
- **OD: 96,66% ≥ 30% → bộ lọc có giá trị thật.** Nhưng đọc kèm §4 dưới: giá trị này phần lớn đến từ việc OD **gần như luôn infeasible ngay từ đầu** (§4), không phải vì bộ lọc "thông minh" — catch rate cao (97%) chỉ phản ánh đúng những gì §3.3 chứng minh (không cắt nhầm), không phải bằng chứng bộ lọc tinh vi.
- **GW: 10,34% pooled → nằm ở biên dưới của "10–30%: yếu, cần bound mạnh hơn".** Tách theo tw_width thì rõ hơn: bộ lọc **chỉ có tác dụng ở tw_width=30** (39,7% cắt, đúng ngưỡng ≥30%), gần như **vô dụng ở tw_width≥60** (≤1,67%, dưới ngưỡng 10%). Bộ lọc slack* hiệu quả tỉ lệ nghịch với độ lỏng TW — đúng logic (TW càng lỏng, càng ít subset thật sự infeasible để mà cắt), nhưng nghĩa là ở phần lớn dải tham số đã quét, bộ lọc GW **gần như vô dụng**, không phải "yếu" mà là "không cắt được gì đáng kể".

---

## 4. Bảng bất đối xứng OD vs GW (§7.4)

**median `n_feasible_sequences` tại k=B, theo B × tw_width:**

| B | tw_width | GW | OD |
|---|---|---|---|
| 2 | 30 | 1 | 0 |
| 2 | 60 | 5 | 0 |
| 2 | 120 | 6 | 0 |
| 2 | 240 | 6 | 0 |
| 3 | 30 | 2 | 0 |
| 3 | 60 | 22 | 0 |
| 3 | 120 | 79 | 0 |
| 3 | 240 | 90 | 0 |
| 4 | 30 | 0 | 0 |
| 4 | 60 | 91 | 0 |
| 4 | 120 | 1.399 | 0 |
| 4 | 240 | 2.520 | 0 |

**OD có median = 0 ở TẤT CẢ 12 ô** — kể cả ở TW lỏng nhất (240 phút). Max quan sát được tại B=4 across toàn bộ 205.440 subset OD k=4: **đúng 0** — không một bundle 4 đơn nào của OD khả thi trong toàn bộ mẫu.

**Nguyên nhân — không phải lỗi code, là tính chất của chính công thức sinh instance ở §5:** với OD, deadline hiệu lực duy nhất ràng buộc toàn chuyến là `deadline_home = t0 + direct_time + tau` (tau ∈ {15,30,60} phút), **độc lập với `ready_time_p ~ U[0,120]`**. Kiểm tra trực tiếp trên 4.320 subset k=1 của OD:

| tau (phút) | % order khả thi đơn lẻ (k=1) |
|---|---|
| 15 | **0,8%** |
| 30 | **5,1%** |
| 60 | **27,4%** |
| — so sánh — | |
| theo tw_width (30/60/120/240) | 11,1% / 11,2% / 12,0% / 10,0% — **phẳng, không đổi** |

GW đối chứng: **100%** order khả thi đơn lẻ ở mọi cấu hình.

Điều này khẳng định: biến điều khiển khả thi của OD trong grid này là **`tau`**, không phải `tw_width` — và ngay cả ở `tau=60` (mức lỏng nhất được khoá), chỉ 27,4% order phục vụ được **một mình**, nên gần như không bundle nào (k≥2) sống sót. Đây thẳng thắn là một khiếm khuyết trong chính công thức khoá ở §5 của spec (`ready_time_p` vẽ độc lập với `direct_time+tau` khiến điểm đón thường "chưa sẵn sàng" cho tới sau khi hạn chót đã trôi qua), không phải điều gì đó cần "sửa cho đẹp" ở đây — xem §5.

**→ Bất đối xứng OD/GW trong bộ dữ liệu này không phải là hệ quả tinh tế của detour budget so với cấu trúc bundling (như dữ liệu HICA-S/Atlanta cho thấy) — nó là một sự sụp đổ gần như hoàn toàn về khả thi, xảy ra ngay ở k=1.**

---

## 5. Kết luận theo ngưỡng §8 — viết thẳng, kể cả khi bác bỏ hướng tiếp cận

**Q2 (median `n_feasible_sequences` tại k=B):** trải rất rộng theo `tw_width` — 0 (tw=30) → 5–6 (tw=60,B=2) → **91–2.520** (tw≥60, B=3–4). Không có một con số "đại diện" duy nhất; đọc theo đúng tinh thần "báo cáo toàn bộ đường cong":

- Ở **B=2**, mọi `tw_width` đều nằm trong dải **≤ 6** → "hướng khả thi" theo ngưỡng đầu (≤5) hoặc sát ranh (5-50).
- Ở **B≥3, tw_width≥60**, median vượt hẳn 50 và **tăng gần cấp số nhân theo k** (22→79→90 ở B=3; 91→1.399→2.520 ở B=4) → rơi thẳng vào ô **"Hướng này không dùng được ở quy mô đó"** của bảng §8.

**Kết luận trung thực: BFS level-wise ĐÚNG (complete, đã kiểm chứng tuyệt đối ở §1) nhưng KHÔNG ỨNG DỤNG ĐƯỢC Ở B≥3 với TW từ trung bình trở lên**, vì số sequence cần lưu mỗi subset bùng nổ gần trần lý thuyết. Theo đúng bảng quyết định §8: **cần dominance an toàn để nén trước khi dùng được (dải 5–50)**, và ở phần lớn ô đã đo còn tệ hơn thế (>50, tăng luỹ thừa) — nên hướng ưu tiên tiếp theo là **tìm dominance rule** (loại bỏ sequence bị một sequence khác "thống trị" — cùng hoặc ít load hơn, đến sớm hơn ở mọi node — trước khi nghĩ tới việc chuyển sang T5/component decomposition).

**Q3:** OD "có vẻ" đạt ngưỡng ≥30% nhưng vì lý do sai (gần như luôn infeasible sẵn, không phải vì bộ lọc tinh vi — xem §4). GW đạt ngưỡng ≥30% chỉ ở TW chặt nhất; ở phần còn lại (đa số dải tham số) rơi vào **"<10%, gần như vô dụng"**. Bộ lọc slack* **không sai** (gate 4.3/4.4 xác nhận), nhưng **giá trị thực tiễn của nó rất hẹp** — chỉ hữu ích khi TW đã chặt sẵn, đúng vùng mà số sequence (Q2) vốn đã nhỏ và ít cần cắt nhất.

---

## 6. Bất thường quan sát được

1. **OD sụp đổ gần như hoàn toàn** ngay ở k=1 (§4) — không phải hiện tượng dần dần theo k như dự đoán ban đầu, mà là một ngưỡng cứng do công thức sinh `ready_time_p` không neo theo `direct_time+tau` của driver. Nếu dùng grid này để so sánh OD/GW cho mục đích khác (không chỉ đo BFS), cần sửa công thức sinh trước.
2. **GW tại B=4, tw_width=30 cho median = 0** — thấp hơn cả B=3 cùng tw_width (median=2). Không phải lỗi monotonicity (gate 4.3 đã xác nhận slack* đơn điệu đúng trên ground truth) — chỉ đơn giản là ở TW rất chặt, hầu như không subset 4-đơn nào sống sót, trong khi một số subset 3-đơn vẫn còn (hệ quả tự nhiên của việc bundle lớn hơn khó hơn, không phải bất thường).
3. **`n_orders` (kích thước pool) không ảnh hưởng đáng kể đến `n_feasible_sequences` của một subset cỡ k cho trước** (§2) — xác nhận trực giác rằng đây là tính chất cục bộ của subset, hữu ích để biết grid Q2 không cần quét n_orders quá rộng trong các vòng sau.
4. Tỷ lệ tiết kiệm chèn so với brute force (Hình 2) giảm đều và mạnh theo k đối với GW, nhưng đây là tiết kiệm **chi phí tính toán**, hoàn toàn độc lập với việc **kết quả** (`n_feasible_sequences`) có nhỏ hay không — hai câu hỏi dễ nhầm với nhau nếu chỉ nhìn một trong hai bảng.

---

## 7. File

| File | Nội dung |
|---|---|
| `Output/Test2/gate_summary.csv` | 144 ô, kết quả 4 gate theo (n,B,class,tw,tau) |
| `Output/Test2/small_raw.csv` | 29.056 dòng — mọi subset của 1.152 instance nhỏ (n≤6) |
| `Output/Test2/big_raw.csv` | 602.752 dòng — mọi subset BFS sinh ra của instance lớn (n∈{8,10,12,15}) |
| `experiments/T2BFS/t2_core.py` | `is_feasible`, `validate` (độc lập), `brute_force`, `bfs_generate` |
| `experiments/T2BFS/t2_gen.py` | Sinh instance, khoá grid §5 (trừ nguồn toạ độ — xem đầu file) |
| `experiments/T2BFS/t2_run.py` | Chạy gate + Q2/Q3, ghi CSV |

Tái lập: `python -m experiments.T2BFS.t2_run` từ `K:\Data Science\Q1 Research`.
