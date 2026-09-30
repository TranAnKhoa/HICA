# Báo cáo: Case 1 (feasibility phát hiện muộn) vs Case 2 (Pareto frontier bùng nổ)

> Trả lời câu hỏi nghiên cứu: khi Algorithm A (Test6 DP) chạy chậm ở vùng B_gw lớn/tw rộng,
> nguyên nhân là (1) DP mở rộng label tới muộn mới phát hiện infeasible (có thể sửa bằng
> resource-extension bound kiểu Ropke & Cordeau 2009), hay (2) label sống nhưng không thể
> dominate lẫn nhau nên frontier tự bùng nổ (giới hạn cấu trúc, không sửa được bằng pruning)?
>
> **Kết luận ngắn gọn: Case 2 — bùng nổ Pareto frontier — là nguyên nhân áp đảo ở đúng vùng
> cần cứu (B_gw lớn, tw rộng). Case 1 chỉ chiếm ưu thế ở vùng rẻ (B_gw nhỏ hoặc tw hẹp) —
> nơi vốn dĩ đã không phải vấn đề. Đầu tư resource-extension-bound sẽ KHÔNG giúp gì ở vùng
> nóng thật sự.**

---

## 1. Bối cảnh — vì sao cần tách 2 case này

Trước đó đã xác nhận: PCF (Pairwise Compatibility Filter) không mang lại lợi ích tốc độ đo
được, và runtime bùng nổ theo B_gw độc lập với driver class (GW vs OD bùng nổ như nhau ở
cùng B). Câu hỏi tiếp theo: **bản chất của sự bùng nổ này là gì** — do DP "chậm phát hiện"
các nhánh chết, hay do bản thân bài toán có nhiều route Pareto-tối-ưu không thể so sánh?

Đây là 2 bài toán khác hẳn nhau về hướng sửa:
- **Case 1** (label chết muộn): sửa được bằng cách thêm một cận (bound) kiểm tra sớm hơn,
  cắt nhánh trước khi mở rộng tới tận nơi phát hiện ra nó chết — đúng dòng kỹ thuật resource
  extension function của Ropke & Cordeau (2009), giữ nguyên tính đúng đắn (exact) nếu cận đó
  là điều kiện cần chứng minh được.
- **Case 2** (frontier Pareto bùng nổ): đây là giới hạn cấu trúc đã biết trong literature
  bicriteria shortest path (Ehrgott) — nếu 2 label thực sự không thể so sánh (A tốt hơn ở K
  nhưng tệ hơn ở W so với B), **không có dominance rule hợp lệ nào loại được cả hai** nếu vẫn
  giữ exactness. Cách duy nhất giảm case 2 mà không phá exactness là (a) giảm số label đi vào
  điểm phân kỳ ngay từ đầu — tức quay lại case 1, hoặc (b) tối ưu kỹ thuật thuần túy (bucket/
  index để so dominance nhanh hơn, không giảm |frontier|, chỉ giảm chi phí mỗi lần so sánh).

---

## 2. Phương pháp đo

### 2.1 Ba chỉ số theo từng round (`touched = 0..B`)

Viết bản `run_dp_instrumented` **copy trung thực 100%** logic `t6_dp.py::run_dp` (đối chiếu
`frontier_sizes` và `complete_by_C` khớp tuyệt đối với bản gốc trong smoke test), chỉ thêm
đếm:

- `killed_by_feasibility`: số lần `_try_pickup`/`_try_delivery` trả `None` (vi phạm
  time-window/capacity) — ứng viên Case 1.
- `killed_by_dominance`: số label bị `_filter_dominated_labels` loại (dominance hoạt động
  bình thường — **không phải** Case 2).
- `frontier_at_this_round` / `survived_to_next_round`: số label sống sót — ứng viên Case 2
  nếu tiếp tục tồn tại song song và tăng dần theo round.

### 2.2 Chỉ số bổ sung: "tuổi" của label khi chết (death-age histogram)

Theo góp ý của người dùng: `killed_by_feasibility` cao **không tự động** nghĩa là
look-ahead sẽ tiết kiệm được nhiều — cần biết **label đó đã sống bao nhiêu round trước khi
chết**. Nếu phần lớn label chết ngay ở round kế tiếp sau khi sinh ra (age=0), DP hiện tại đã
gần tối ưu, không có gì để look-ahead cắt sớm hơn.

Thêm `born_round[id(label)]` (round label được sinh ra), và với mỗi lần `_try_pickup`/
`_try_delivery` trả `None`, ghi `age = touched_hiện_tại - born_round[cha]` vào histogram.

### 2.3 Tiêu chí phán quyết (verdict)

```
case2_dominant  nếu  feas_kill_rate_lastround < 5%  VÀ  frontier tăng qua các round
case1_present   ngược lại
```

---

## 3. Kết quả — Vòng 1: lưới rộng (n=20, B_gw∈{3,4}, tw∈{30,60,120,240})

Script `research_case1_vs_case2.py`, chạy song song với `run_2b_v2.py`, dừng giữa chừng
khi đã đủ tín hiệu (23 cell, dữ liệu giữ nguyên làm bằng chứng — file
`results/research_case1_vs_case2_v1_partial.csv`).

| n | B_gw | tw | feas_kill_lastround | frontier_lastround | verdict |
|---:|---:|---:|---:|---:|:---|
| 20 | 3 | 30 | 32–56% | 42K–81K | **case1_present** (cả 3 seed) |
| 20 | 3 | 60 | 0.02–26% | 103K–230K | 2/3 case1, 1/3 case2 |
| 20 | 3 | 120 | 0.7–26% | 109K–264K | 2/3 case1, 1/3 case2 |
| 20 | 3 | 240 | 0–1% | 214K–243K | **case2_dominant** (cả 3 seed) |
| 20 | 4 | 30 | 66–72% | 303K–441K | **case1_present** (cả 3 seed) |
| 20 | 4 | 60 | 35–42% | 672K–888K | **case1_present** (cả 3 seed) |
| 20 | 4 | 120 | 2–26% | 1.29M–3.26M | 2/3 case1, 1/3 case2 |
| 20 | 4 | 240 | 0–0.2% | **2.95M–4.59M** | **case2_dominant** (cả 2 seed đã chạy) |

**Xu hướng rất rõ ràng và nhất quán: khi tw tăng (cửa sổ thời gian rộng ra), verdict dịch
chuyển từ `case1_present` (tw=30) sang `case2_dominant` (tw=240) một cách đơn điệu.** Ở
tw=30, `feas_kill_rate` cao (32–72%) — DP vẫn đang loại được nhiều nhánh vì vi phạm
time-window. Ở tw=240, `feas_kill_rate` gần như 0% — hầu như mọi nhánh đều hợp lệ về mặt
thời gian, vấn đề chuyển hoàn toàn sang việc frontier phình to vì không dominate được nhau.

---

## 4. Kết quả — Vòng 2: điểm dữ liệu chính xác tại vùng nóng nhất

Theo yêu cầu kiểm tra kỹ hơn: vùng nóng thực sự (đã xác nhận qua `run_2a_stepB.py`, runtime
86.81s trung bình) là **n=20, B_gw=4, tw=240**. Đo trực tiếp 1 seed tại đây với histogram
death-age đầy đủ:

```
verdict                  = case2_dominant
feas_kill_rate_round0    = 0.0%
feas_kill_rate_lastround = 0.0%
frontier_round0          = 5
frontier_lastround       = 4,587,608   (!!)
total_feasibility_deaths = 2,061,519
mean_death_age_rounds    = 0.0
death_age0_fraction      = 1.0   (100% tuyệt đối)
death_age_histogram      = '0:2061519'   (TOÀN BỘ nằm ở age=0, không có age=1,2,3,...)
```

**Đây là câu trả lời dứt khoát cho câu hỏi "look-ahead có lời không":** không chỉ trung bình
tuổi chết = 0, mà **100% trong hơn 2 triệu cái chết đều xảy ra ở round ngay-sau-khi-sinh**
— không có một label nào "sống lay lắt" vài round rồi mới chết. Không có "công lãng phí"
nào để resource-extension-bound tiết kiệm được, vì DP hiện tại đã phát hiện feasibility
**ngay tại thời điểm sớm nhất có thể** đối với mọi nhánh bị loại.

Đồng thời, `frontier_lastround = 4,587,608` xác nhận: vấn đề runtime tại cell này hoàn toàn
nằm ở **số lượng khổng lồ label sống sót** (không chết, không bị dominate) — đúng định
nghĩa Case 2.

---

## 5. Diễn giải — vì sao pattern lại đảo chiều theo tw

- **tw hẹp**: cửa sổ thời gian chặt buộc nhiều thứ tự pickup/delivery vi phạm deadline ngay
  lập tức → `killed_by_feasibility` cao → Case 1 chiếm ưu thế (nhưng ở vùng này DP vốn đã
  nhanh, tw=30/B_gw=4 chỉ mất ~8-15s, không phải vấn đề cần giải quyết).
- **tw rộng**: gần như mọi thứ tự đều "kịp giờ" về mặt time-window → dominance trở thành cơ
  chế cắt tỉa **duy nhất** còn hoạt động, nhưng dominance chỉ loại được label bị thống trị
  **hoàn toàn trên cả 3 trục (t, K, W)** — khi tw rộng, nhiều label có `t` khác nhau đáng kể
  vẫn "cùng hợp lệ" nên khó bị dominate lẫn nhau → frontier phình to theo cấp số nhân của
  B_gw, đúng độ phức tạp tổ hợp `(2k)!/2^k` đã nêu ở §7.3 thesis.

---

## 6. Kết luận và khuyến nghị

1. **Ở vùng nóng thật sự (B_gw lớn, tw rộng — nơi cần cứu) là Case 2 tuyệt đối (100%)**,
   không phải Case 1. Hướng resource-extension-bound (Ropke & Cordeau) — dù là kỹ thuật hợp
   lệ và còn mở về mặt lý thuyết — **sẽ không mang lại lợi ích đo được** ở đúng vùng đang gây
   ra thời gian chạy khổng lồ, vì không có gì để "phát hiện sớm hơn" khi mọi nhánh chết đều
   đã chết ở mức sớm nhất có thể.
2. Điều này **khớp hoàn toàn** với 2 phát hiện thực nghiệm trước đó: PCF (một dạng điều kiện
   cần khác) cũng thất bại hoàn toàn ở tw rộng (0% cắt), và cận MST/1-tree đơn giản cũng cho
   0% cắt xuyên suốt — cả 2 đều là các biến thể của "cố phát hiện infeasibility sớm hơn",
   và cả 2 đều vô dụng ở đúng nơi vấn đề Case 2 thống trị.
3. **Theo đúng phân tích lý thuyết đã có sẵn**: cách duy nhất giảm Case 2 mà không phá tính
   đúng đắn (exactness — bắt buộc theo điều kiện DSIC đã khoá) là:
   - Giảm số label vào tới điểm phân kỳ K/W ngay từ đầu (quay lại Case 1 — nhưng đã xác nhận
     không khả thi ở vùng nóng).
   - **Tối ưu kỹ thuật thuần túy tốc độ so sánh dominance** (bucket/index label theo `v` hoặc
     theo `K`) — giảm chi phí mỗi lần so sánh từ O(F) xuống thấp hơn, KHÔNG giảm kích thước
     frontier. Đây là engineering, cần tách rõ khỏi phần đóng góp lý thuyết của thesis.
   - Nới lỏng exactness (ví dụ ε-dominance) — **bị cấm** theo điều kiện DSIC đã khoá trước đó.
4. **Bài toán mở §7.3 thesis vẫn mở** — không có hướng nào trong số đã thử nghiệm (PCF, MST,
   resource-extension) giải quyết được gốc rễ của bùng nổ tổ hợp cho GW ở B_gw lớn/tw rộng.
   Cận dưới hình học có tính đến precedence (ví dụ assignment relaxation, §7.3 dòng 377) vẫn
   là hướng chưa thử, có thể đáng đầu tư tiếp nếu muốn giải bài toán mở này.

---

## 7. Trạng thái xử lý sau báo cáo

Theo yêu cầu, nghiên cứu Case 1 vs Case 2 đã **dừng** sau khi có đủ tín hiệu dứt khoát (không
chạy hết toàn bộ lưới target ban đầu n∈{20,30}×B_gw∈{3,4,5}×tw∈{60,120,240}×3 seed = 54 cell
— chỉ 1 cell bổ sung tại vùng nóng nhất đã đủ trả lời câu hỏi nghiên cứu với độ tin cậy cao,
100% trên hơn 2 triệu điểm dữ liệu chết).

File dữ liệu giữ lại (không xoá, làm bằng chứng lịch sử):
- `spec_2a_2b/results/research_case1_vs_case2_v1_partial.csv` — 23 cell, lưới rộng ban đầu
- `spec_2a_2b/results/research_case1_vs_case2_by_round_v1_partial.csv` — chi tiết theo round
- Kết quả vùng nóng (n=20,B_gw=4,tw=240) — in trực tiếp trong phiên làm việc, xem báo cáo này.

`run_2b_v2.py` (lưới 2b chính thức, không liên quan tới nhánh nghiên cứu này) chạy độc lập
suốt quá trình, không bị ảnh hưởng.
