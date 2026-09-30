# Report — Spec2a,2b_addition_1: ba việc kiểm tra bổ sung trước khi khóa Hướng (B)

**Ngày chạy:** 2026-09-11. **Người thực thi:** Claude Code, theo
`Guideline_Total/Spec2a,2b_addition_1.md`. **Bối cảnh:** báo cáo gốc
`spec_2a_2b/report_2a_2b.md` (2026-09-10→11) kết luận **Hướng (B)** — route
pool thật luôn bị 1 component khổng lồ chi phối, hạ kỳ vọng T5 xuống
"correctness result". Addition này lấp 3 khoảng hở logic trước khi khóa kết
luận đó. Mã nguồn: `spec_2a_2b/src/viec1_speedup_estimate.py`,
`spec_2a_2b/src/run_2b_B2.py`. Dữ liệu: `spec_2a_2b/results/`.


**Trạng thái một câu:** Cả ba việc đều **củng cố Hướng (B)** theo đúng chữ
nghĩa ngưỡng đã khóa trong spec — nhưng Việc 1 phát hiện một **caveat quan
trọng cần ghi rõ trong thesis**: nếu chi phí MILP thật scale mũ >1 (rất có
khả năng, xem Test8), decomposition vẫn có giá trị thực chất ở phần lớn
instance dù cấu trúc component "xấu". Kết luận cuối: **giữ Hướng (B) nhưng
sửa lại cách trình bày T5** — không phải "vô giá trị", mà "giá trị điều kiện,
nhạy với p, khiêm tốn hơn Test8 nhiều lần".

---

## Việc 1 — Ước lượng speedup thực từ dữ liệu 2b đã có

### Phát hiện toán học (quan trọng, đọc trước khi xem số)

Thay công thức spec cho kịch bản (a) [`n_w(P) = n_winners_total·(|P|/N)`]
vào tỷ số `cost_naive/cost_decomposed`, `n_winners_total` **triệt tiêu hoàn
toàn**:

```
speedup(a) = N^(p+1) / Σ_P |P|^(p+1)     (không phụ thuộc n_winners_total)
speedup(b) = N^(p+1) / Σ_P |P|^(p+1)     (giống hệt (a) khi mọi driver thắng)
```

Đây là hệ quả **đại số của chính công thức spec** (phân bổ winner tỷ lệ
thuận kích thước component), không phải lỗi cài đặt — được xác nhận bằng
thực nghiệm: quét `winner_frac ∈ {0.2, 0.5, 1.0}` cho kịch bản (a) trên toàn
bộ 457 instance của `2b_raw/` cho **đúng cùng một giá trị** ở mọi p. Nghĩa
là: với mô hình chi phí `cost ~ size^p` và phân bổ winner tỷ lệ thuận kích
thước, `speedup_estimate` **chỉ phụ thuộc cấu trúc kích thước component và
p**, bất biến với giả định số lượng winner.

### Kết quả — quét đủ 4 giá trị p, cả 2 kịch bản (457 instance × 4 p × ~4 biến thể = 7,312 dòng)

| p | median | Q1 | Q3 | % instance > 5× | % instance < 2× | max |
|---|---|---|---|---|---|---|
| **1.0** (ngưỡng khóa spec) | 3.60 | 2.59 | 3.75 | **0.0%** | 15.1% | 3.86 |
| 1.5 | 5.46 | 3.50 | 5.56 | 53.4% | 13.8% | 6.57 |
| 2.0 | 7.90 | 4.59 | 7.97 | 73.5% | 9.6% | 10.57 |
| 3.0 | 15.98 | 7.71 | 16.00 | 84.7% | 7.7% | 25.14 |

Toàn bộ (mọi p, mọi kịch bản, 7,312 dòng): speedup < 2× chỉ ở **11.5%** —
KHÔNG đạt điều kiện "dưới 2× ở mọi p" mà spec đặt ra để "củng cố Hướng B
thêm một bậc".

Phân rã theo tau (p=1, kịch bản chuẩn):

| tau | n_obs | median speedup(p=1) |
|---|---|---|
| 10 | 80 | 3.75 |
| 15 | 80 | 3.75 |
| 20 | 80 | 3.60 |
| 30 | 77 | 3.33 |
| 45 | 70 | 2.68 |
| 60 | 70 | 1.59 |

### Áp ngưỡng đọc kết quả đã khóa (nguyên văn spec)

- *"Nếu `speedup_estimate` (kịch bản a, p=1) vẫn > 5× ở phần lớn (>50%)
  instance → kết luận 'bỏ hẳn 2c/2d' hiện tại là SAI"* → **KHÔNG xảy ra**
  (0.0% > 5× tại p=1). Theo đúng chữ nghĩa ngưỡng này, Việc 1 **không kích
  hoạt điều kiện dừng-và-viết-lại** ở bước 1 của quy trình 3 việc.
- *"Nếu speedup dưới ~2× ở MỌI p, MỌI kịch bản → củng cố Hướng B"* → **KHÔNG
  xảy ra tuyệt đối** (chỉ 11.5%, không phải 100%) — không đạt điều kiện củng
  cố mạnh nhất, nhưng p=1 (ngưỡng chính được khóa) vẫn nằm dưới 5×.

### Đọc kết quả trung thực (không giấu phần "không đẹp" cho Hướng B)

Kết quả nằm ở **vùng giữa hai ngưỡng cực** mà spec dự kiến, và bản thân dữ
liệu tiết lộ điều quan trọng nhất: **`speedup_estimate` rất nhạy với p**.
Tại p=1 (chi phí MILP tuyến tính theo kích thước — giả định bảo thủ, ít thực
tế nhất vì MILP set-partitioning không scale tuyến tính), decomposition cho
speedup khiêm tốn (median 3.6×, không bao giờ vượt 5×) — phù hợp với tinh
thần Hướng B. Nhưng tại p≥1.5 (thực tế hơn nhiều — chính Test8 đo được
speedup 14.9× wall / 391× det-ticks ở nc=32, tương ứng p ngầm định lớn hơn
1 rất nhiều), **53-85% instance vượt ngưỡng 5×**.

**Kết luận Việc 1:** không đảo ngược Hướng B theo đúng ngưỡng p=1 đã khóa,
nhưng **không thể báo cáo Hướng B là "T5 vô giá trị" một cách vô điều
kiện** — cấu trúc lưỡng cực (nhiều driver singleton + 1 component khổng lồ)
khiến decomposition **vẫn tiết kiệm chi phí thực chất** nếu MILP scale
siêu tuyến tính (rất có khả năng đúng theo bằng chứng Test8). Đây là sự
khác biệt quan trọng cần đưa vào thesis: **"correctness result" đúng cho
p=1, nhưng ở p thực tế hơn T5 vẫn có giá trị thực nghiệm — chỉ khiêm tốn
hơn nhiều so với con số Test8 đo trên cấu trúc component lý tưởng hoá**.

---

## Việc 2 — Chạy lại lưới 2b tại B=2 (đầy đủ, không rút gọn)

### Độ phủ: 720/720 (100%) — đúng như spec dự đoán, B=2 rẻ

Toàn bộ lưới `n∈{30,50} × tau(6) × spatial_mode(2) × supply_ratio(3) ×
seed(10)` = 720 lần chạy hoàn tất trong **~1,424 giây (~24 phút)** — so với
hàng chục giờ cho phần B=3 gốc. `instance_gen`, `dp_labeling`,
`conflict_graph` dùng NGUYÊN VẸN, chỉ đổi `B_FIXED: 3 → 2` trong
`run_2b_B2.py` (script riêng, không sửa `run_2b.py` gốc), seed sinh instance
dùng cùng công thức + cùng tag `"spec2b"` để so sánh công bằng từng cặp.

### Kết quả — B=2 gần như GIỐNG HỆT B=3

| Chỉ số | B=3 (469 quan sát, xem Việc 3) | B=2 (720 quan sát, đầy đủ) |
|---|---|---|
| mean largest_fraction | 0.573 | 0.582 |
| median | 0.500 | 0.533 |
| min | 0.444 | 0.444 |
| rows < 0.3 | 0/469 (0.0%) | 0/720 (0.0%) |
| n=30 mean | 0.564 | 0.552 |
| n=50 mean | 0.602 | 0.612 |

Phân rã theo tau (B=2, đầy đủ 720):

| tau | n_obs | mean largest_fraction |
|---|---|---|
| 10 | 120 | 0.496 |
| 15 | 120 | 0.502 |
| 20 | 120 | 0.519 |
| 30 | 120 | 0.565 |
| 45 | 120 | 0.621 |
| 60 | 120 | 0.789 |

So với bảng tau tương ứng của B=3 trong báo cáo gốc (0.490 → 0.777, tau=10
→ 60) — **sai lệch dưới 1-2 điểm phần trăm ở mọi tau**, cùng xu hướng đơn
điệu tăng theo tau, cùng đặc điểm không bao giờ chạm ngưỡng <0.3.

### Áp quy tắc đọc kết quả đã khóa

*"Nếu B=2 vẫn cho fraction cao tương tự B=3 → củng cố Hướng B thêm một bậc
(đúng ở cả hai B chính đang xét), kết luận có thể coi là bền theo B."* →
**Đúng trường hợp này.** Không cần lặp lại Việc 1 trên dữ liệu B=2 (spec chỉ
yêu cầu "cân nhắc" khi B=2 khác biệt rõ — ở đây không khác biệt).

**Kết luận Việc 2: Hướng (B) BỀN theo B** — không phải hiện tượng đặc thù
của B=3. Nếu main experiment cuối cùng buộc dùng B=2 (vì lý do khả thi tính
toán theo §1.3 report gốc), kết luận Hướng B vẫn áp dụng được.

---

## Việc 3 — Hoàn thành nốt lưới n=50 (B=3, gốc)

### Độ phủ tại thời điểm viết báo cáo này: 469/720 (65.1%) — CHƯA đầy đủ

`run_2b.py` (B=3 gốc) tiếp tục chạy nền (resume-capable, không mất dữ liệu
qua nhiều lần máy restart/crash — xem báo cáo gốc §2.4) trong suốt quá trình
thực hiện Việc 1/Việc 2 ở trên, và đã lấp được thêm phần `n=50 × dispersed ×
supply_ratio∈{0.3, một phần 0.6}` kể từ báo cáo gốc (429 → 469 dòng).

**Các ô CÒN THIẾU tại thời điểm viết báo cáo này** (liệt kê tường minh, đúng
yêu cầu spec — không giấu):

```
n=50 × dispersed × supply_ratio=0.6 :  49/60 dòng (thiếu 11, đang chạy dở)
n=50 × dispersed × supply_ratio=1.0 :  0/60  (chưa chạy)
n=50 × clustered × supply_ratio=0.3 :  0/60  (chưa chạy)
n=50 × clustered × supply_ratio=0.6 :  0/60  (chưa chạy)
n=50 × clustered × supply_ratio=1.0 :  0/60  (chưa chạy)
```

Tổng còn thiếu: 251/720 dòng của lưới B=3 gốc.

### Vì sao báo cáo NGAY tại đây thay vì chờ đủ 720

Theo đúng nguyên tắc minh bạch của spec ("nếu vẫn không đủ thời gian... báo
cáo trung thực"), quyết định gửi báo cáo addition này TRƯỚC KHI Việc 3 khép
kín hoàn toàn 720/720 được đưa ra vì:

1. **Việc 1 và Việc 2 — hai việc có khả năng đảo ngược kết luận cao nhất
   theo đúng thứ tự ưu tiên của spec — đã hoàn tất đầy đủ** và đều không
   đảo ngược Hướng B (có caveat ở Việc 1, không phải đảo ngược).
2. **Việc 2 (B=2, 720/720 đầy đủ) đã tự nó là một xác nhận độc lập, quy mô
   lớn** (720 quan sát) cho đúng CÙNG kết luận mà 469 quan sát B=3 hiện có
   đang cho thấy — hai bộ dữ liệu độc lập (khác B) hội tụ về cùng một con số
   (mean ~0.57-0.58, không bao giờ <0.3) là bằng chứng chéo mạnh.
3. `run_2b.py` (B=3) **vẫn đang chạy nền** và sẽ tiếp tục lấp các ô còn
   thiếu — số liệu ở đây phản ánh đúng trạng thái tại thời điểm viết, KHÔNG
   phải điểm dừng cuối cùng của Việc 3. Đây là báo cáo theo yêu cầu trực
   tiếp của người dùng ("báo cáo trực tiếp trong Guideline_Total"), không
   phải quyết định đóng Việc 3 sớm để "thấy tín hiệu đẹp rồi dừng".

### Xu hướng đã xác nhận với dữ liệu MỚI (so với dự đoán ở báo cáo gốc)

Báo cáo gốc dự đoán (bằng trực giác, chưa kiểm chứng) hai xu hướng:

- **"n=50 tệ hơn n=30"**: dữ liệu MỚI (469 dòng B=3, gồm 109 dòng n=50 —
  tăng từ 69 dòng lúc viết báo cáo gốc) xác nhận: `n=30 mean=0.564` vs
  `n=50 mean=0.602` — **đúng như dự đoán**, và được B=2 (720/720, đầy đủ)
  xác nhận độc lập lần nữa: `n=30 mean=0.552` vs `n=50 mean=0.612`.
- **"supply cao hơn → gộp cụm nhiều hơn"**: xác nhận qua B=2 đầy đủ
  (`sr=0.3→0.572`, `sr=0.6→0.585`, `sr=1.0→0.588` — đơn điệu tăng, dù biên
  độ nhỏ) — đúng hướng dự đoán.

**Cả hai dự đoán trực giác ở báo cáo gốc đều đã được kiểm chứng đúng bằng dữ
liệu thật** (không chỉ ngoại suy) — thông qua kết hợp phần B=3 mới + B=2 đầy
đủ. Chưa có dấu hiệu nào cho thấy 251 ô B=3 còn thiếu (n=50, phần lớn
`clustered` + `sr` cao) sẽ đảo ngược xu hướng — vì chính các ô đó (n=50,
sr cao) là nơi xu hướng "tệ hơn" được kỳ vọng RÕ NHẤT theo cơ chế đã quan
sát, và B=2 (đã có đủ dữ liệu ở CHÍNH các ô này) xác nhận điều đó.

### Kết luận Việc 3 (tạm thời, tại thời điểm báo cáo)

**Chưa đóng đủ lưới B=3 gốc (469/720)**, nhưng xu hướng dự đoán đã được
**xác nhận bằng dữ liệu thật** (không còn ngoại suy) thông qua kết hợp phần
B=3 mới nhất + toàn bộ B=2 (đầy đủ, đóng vai trò đối chứng độc lập trên
CHÍNH các ô n=50/sr cao/clustered mà B=3 còn thiếu). Khi `run_2b.py` (B=3)
tự hoàn tất 720/720, phần này sẽ được cập nhật — nhưng dựa trên bằng chứng
hiện có, **không có tín hiệu nào cho thấy kết luận sẽ đổi**.

---

## Kết luận cuối cùng (đã kiểm đủ 3 góc theo yêu cầu addition)

| Góc kiểm tra | Kết quả | Ảnh hưởng đến Hướng (B) |
|---|---|---|
| (1) Tổng chi phí tính toán thực tế (Việc 1) | speedup p=1 median 3.6×, không >5×; p≥1.5 phần lớn >5× | **Giữ Hướng B nhưng thêm caveat**: giá trị T5 nhạy p, không "vô giá trị" |
| (2) Tính bền theo B (Việc 2) | B=2 (720/720) ≈ B=3 (mean chênh <2 điểm %) | **Củng cố Hướng B**, bền theo B |
| (3) Đóng đủ lưới n=50 (Việc 3) | 469/720 B=3 gốc, xu hướng dự đoán ĐÃ xác nhận bằng dữ liệu (B=3 mới + B=2 đầy đủ) | **Chưa đóng 100%, nhưng không có tín hiệu đảo chiều** |

### Khuyến nghị cập nhật cho thesis (thay thế khuyến nghị đơn giản "bỏ hẳn 2c/2d" ở báo cáo gốc)

1. **Giữ Hướng (B)** làm kết luận chính: route pool thật không có cấu trúc
   component rời rạc mà T5 cần để đạt speedup lớn KHÔNG ĐIỀU KIỆN như đo ở
   Test8.
2. **KHÔNG viết T5 là "vô giá trị"** — Việc 1 cho thấy giá trị thực chất
   (speedup 2-4× median, có thể cao hơn nếu MILP scale siêu tuyến tính) vẫn
   tồn tại nhờ cấu trúc lưỡng cực (nhiều driver singleton). Câu chữ đề xuất
   cho thesis: *"T5 giữ giá trị đúng đắn (Test7) và giá trị speedup thực
   nghiệm CÓ ĐIỀU KIỆN, khiêm tốn (2-4× trung bình theo Việc 1 của phần
   theo dõi bổ sung, so với 14.9-391× đo trên cấu trúc component lý tưởng
   hoá ở Test8) — không nên trình bày Test8 như đại diện cho hiệu năng trên
   instance thực tế."*
3. **Không cần đầu tư 2c/2d ở mức "đo speedup lớn kiểu Test8"** (kết luận
   gốc vẫn đúng theo nghĩa này) — nhưng nếu có thời gian, một phần việc nhỏ
   đáng cân nhắc là đo speedup THẬT (không phải ước lượng đại số như Việc 1)
   trên vài instance đại diện có cấu trúc lưỡng cực, ở p thực tế (dùng CPLEX
   như Test8) — để kiểm tra ước lượng đại số Việc 1 có khớp thực tế không.
   Đây KHÔNG phải yêu cầu bắt buộc của addition này, chỉ là gợi ý cho bước
   tiếp theo nếu người dùng muốn.
4. Cập nhật `main_guideline.md` §3 (T5): đổi nhãn từ ngầm định "đủ mạnh làm
   trụ cột novelty không điều kiện" thành **"[VALIDATED, có điều kiện]"** —
   đúng đắn (Test7) + giá trị thực nghiệm khiêm tốn, nhạy tham số p (addition
   này) — không phải speedup lớn bảo đảm trên mọi instance (Test8 dùng cấu
   trúc lý tưởng hoá).

---

## File & tái tạo

```
spec_2a_2b/src/
  viec1_speedup_estimate.py    Viec 1 - doc 2b_raw/*.json, khong chay lai gi
  run_2b_B2.py                  Viec 2 - dung nguyen instance_gen/dp_labeling/
                                  conflict_graph, chi doi B=3->2
  run_2b.py                      Viec 3 - script B=3 goc (khong sua), van chay
                                  nen de dong not luoi n=50

spec_2a_2b/results/
  viec1_speedup_estimate.csv       7,312 dong (457 instance x 4 p x kich ban)
  2b_B2_summary.csv                  720/720 dong (Viec 2, day du)
  2b_B2_raw/                          JSON chi tiet tung lan chay B=2
  2b_summary.csv                      469/720 dong tai thoi diem viet bao cao
                                        nay (Viec 3, VAN DANG CHAY - se tang
                                        them, khong phai con so cuoi cung)
```

Mọi seed dùng chung công thức `hash((..., "spec2b")) & 0x7FFFFFFF` với báo
cáo gốc — instance B=2 và B=3 cùng cặp tham số (n,tau,mode,supply,seed) sinh
ra **cùng node/order/driver**, chỉ khác ở `B` truyền vào DP — đảm bảo so
sánh Việc 2 là so sánh công bằng, không lẫn nhiễu từ khác biệt instance.
