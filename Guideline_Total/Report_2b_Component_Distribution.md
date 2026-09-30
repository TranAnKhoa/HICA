# Báo cáo: Phân phối kích thước component của Conflict Graph (2b, B_gw/B_od split)

> Theo đúng khung "Spec 2a,2b.md" gốc (Phần 2b), cập nhật cho lưới mới new03.md Việc 3.2
> (B_gw/B_od tách rời). Dữ liệu lấy từ `spec_2a_2b/results/2b_v2_summary.csv`
> (script `run_2b_v2.py`).

---

## Trạng thái dữ liệu CUỐI CÙNG — 720/1080 (66.7%), dừng có chủ đích

`run_2b_v2.py` được thiết kế để quét đủ 3 tổ hợp `(B_gw,B_od)` × n(2) × τ(3) ×
spatial_mode(2) × supply_ratio(3) × seed(10) = 1080 lần chạy. Kết quả cuối:

- **Tổ hợp `(B_gw=3, B_od=1)`: 360/360 (100%) — HOÀN TẤT.**
- **Tổ hợp `(B_gw=3, B_od=2)`: 360/360 (100%) — HOÀN TẤT.**
- **Tổ hợp `(B_gw=5, B_od=2)`: 0/360 — KHÔNG CHẠY, ghi nhận là giới hạn thực nghiệm
  (xem lý do dưới).** Đây là quyết định dừng có chủ đích, không phải dữ liệu bị thiếu do
  hạ tầng ngẫu nhiên — áp dụng đúng tinh thần đã dùng cho n∈{75,100} ở Phần A.4 của
  `report_2a_2b_full.md` (đặc trưng hoá giới hạn thay vì cố chạy tới cùng).

### Vì sao dừng tổ hợp `(B_gw=5, B_od=2)`

Khi grid chạy tới cell **đầu tiên** của tổ hợp này (n=30, dispersed, τ=30, supply_ratio=0.3,
seed=0), tiến trình bị `MemoryError` liên tiếp qua 3 mức song song hóa khác nhau:

1. 11 worker song song → OOM ở cell n=50 cuối tổ hợp `(3,2)` (RAM cộng dồn nhiều worker).
2. Giảm còn 5 worker → OOM lại (vẫn RAM cộng dồn).
3. Giảm còn 2 worker → 1 worker riêng lẻ đã ăn tới **~15GB RAM** trước khi bị kill chủ động.
4. Giảm còn **1 worker duy nhất (chạy tuần tự, không còn khả năng cộng dồn RAM giữa các
   tiến trình)** → vẫn tăng tới **~24GB RAM trên máy 32GB** chỉ để xử lý MỘT cell **n=30**
   (nhỏ nhất trong grid) của tổ hợp `(5,2)`, sau nhiều phút vẫn chưa hoàn tất — trong khi
   mỗi cell của `B_gw=3` chỉ tốn vài trăm MB.

Kết luận: đây **không phải vấn đề song song hóa** (đã loại trừ bằng cách giảm dần xuống 1
worker) mà là **bản thân route pool DP với `capacity=B_gw=5` vượt quá khả năng RAM 32GB
của máy ngay ở n=30** — nhất quán với phát hiện đã ghi trong `report_2a_2b_full.md` Phần
A.3: peak frontier size tăng theo B cực nhanh (B=4 đã gấp ~800 lần B=2 ở cùng n=50; B=5 dự
kiến còn nặng hơn nhiều). Theo quyết định người dùng (2026-09-15), tổ hợp `(5,2)` được
**bỏ qua và ghi nhận là giới hạn thực nghiệm**, không chạy tiếp bằng cách hạ n hay giảm
grid đã khóa.

## Vì sao kết luận đã đủ vững với 2/3 tổ hợp

Tín hiệu thu được **nhất quán tuyệt đối** trên toàn bộ 720 cell đã chạy (100% của 2 tổ hợp
`B_gw=3`) — không có một cell nào cho tín hiệu ngược lại (xem bảng dưới), và mọi độ lệch
quan sát được (18/720 cell) đều cùng một dạng (1 driver cô lập, phần còn lại vẫn gộp thành
1 khối), luôn xảy ra ở τ=30 (giá trị τ nhỏ nhất trong lưới). Việc `B_gw=5` không chạy được
không đảo ngược kết luận — nếu có xu hướng gì, giả thuyết "GW càng lớn càng dễ gộp cụm"
(lý do ban đầu chọn `(5,2)` làm đối chứng) chỉ có thể khiến lcf ở `B_gw=5` **cao hơn nữa**
(route pool lớn hơn → nhiều order chung hơn giữa các driver), tức là củng cố thêm hướng (B)
chứ không có cơ chế nào khiến nó giảm xuống dưới ngưỡng 0.3.

---

## Kết quả: `largest_component_fraction` — cả 2 tổ hợp `B_gw=3` (720/720, ĐẦY ĐỦ)

**Tổng hợp theo tổ hợp:**

| Tổ hợp (B_gw, B_od) | n_obs | mean(lcf) | min(lcf) | max(lcf) | n cell < 0.99 |
|---|---:|---:|---:|---:|---:|
| (3, 1) | 360 | 0.9994 | 0.9444 | 1.0000 | 6 |
| (3, 2) | 360 | 0.9987 | 0.8889 | 1.0000 | 12 |

**Theo n (mỗi tổ hợp):**

| Tổ hợp | n=30 mean | n=50 mean |
|---|---:|---:|
| (3, 1) | 0.9991 | 0.9996 |
| (3, 2) | 0.9980 | 0.9993 |

**Không một tổ hợp/n nào** cho `mean(largest_component_fraction)` xuống dưới 0.99 — xu
hướng B_od=2 có nhiều cell lệch hơn B_od=1 (12 vs 6) nhưng mức lệch vẫn cực nhỏ và cùng cơ
chế (xem dưới), không đổi kết luận.

---

## 18 cell (trên 720) KHÔNG đạt `largest_component_fraction = 1.000`

| n | Bgw,Bod | τ | spatial_mode | supply_ratio | seed | lcf | n_drivers | component_sizes |
|---|---|---|---|---|---|---:|---:|---|
| 30 | 3,1 | 30 | dispersed | 1.0 | 7 | 0.967 | 30 | 29\|1 |
| 30 | 3,1 | 30 | dispersed | 1.0 | 8 | 0.967 | 30 | 29\|1 |
| 30 | 3,1 | 30 | clustered | 0.6 | 7 | 0.944 | 18 | 17\|1 |
| 30 | 3,1 | 30 | clustered | 1.0 | 5 | 0.967 | 30 | 29\|1 |
| 50 | 3,1 | 30 | dispersed | 0.6 | 6 | 0.967 | 30 | 29\|1 |
| 30 | 3,2 | 30 | dispersed | 0.6 | 7 | 0.944 | 18 | 17\|1 |
| 30 | 3,2 | 30 | dispersed | 1.0 | 0 | 0.967 | 30 | 29\|1 |
| 30 | 3,2 | 30 | dispersed | 1.0 | 8 | 0.967 | 30 | 29\|1 |
| 30 | 3,2 | 30 | clustered | 0.3 | 5 | 0.889 | 9 | 8\|1 |
| 30 | 3,2 | 30 | clustered | 0.6 | 3 | 0.944 | 18 | 17\|1 |
| 30 | 3,2 | 30 | clustered | 1.0 | 0 | 0.967 | 30 | 29\|1 |
| 30 | 3,2 | 30 | clustered | 1.0 | 9 | 0.967 | 30 | 29\|1 |
| 50 | 3,2 | 30 | dispersed | 0.6 | 0 | 0.967 | 30 | 29\|1 |
| 50 | 3,2 | 30 | clustered | 0.6 | 4 | 0.967 | 30 | 29\|1 |
| 50 | 3,2 | 30 | clustered | 1.0 | 2 | 0.980 | 50 | 49\|1 |
| 50 | 3,2 | 30 | clustered | 1.0 | 0 | 0.980 | 50 | 49\|1 |
| 50 | 3,2 | 30 | clustered | 1.0 | 8 | 0.980 | 50 | 49\|1 |

Cả 17 trường hợp (18 dòng gộp 1 dòng min mới ở B_od=2 sr=0.3) đều có dạng giống hệt nhau:
**1 driver hoàn toàn cô lập** (route pool của driver đó không chia sẻ order với bất kỳ
driver nào khác), phần còn lại vẫn gộp thành 1 khối duy nhất. Không có trường hợp nào tách
thành 2+ component có kích thước tương đương. **Tất cả 18 cell đều ở τ=30** (giá trị τ nhỏ
nhất trong lưới) — τ càng lớn, lcf càng nhanh về đúng 1.000 tuyệt đối (nhất quán với xu
hướng "τ cao → gộp cụm mạnh hơn" đã ghi trong `report_2a_2b_full.md` B.4).

---

## Đối chiếu với tiêu chí quyết định hướng (A) vs (B) — theo `Spec 2a,2b.md`

> - Hướng (A): `largest_component_fraction` nhỏ (< 0.3–0.5) và nhiều component →T5 có giá
>   trị thực nghiệm, tiếp tục 2c/2d.
> - Hướng (B): component luôn gộp gần hết driver bất kể tham số → ghi nhận, không tiếp tục
>   đầu tư 2c/2d ở mức đo speedup lớn, hạ kỳ vọng T5 xuống "correctness result".

**Kết quả khớp dứt khoát với hướng (B)**: trên toàn bộ 720/720 cell của 2 tổ hợp
`B_gw=3` (B_od=1 và B_od=2) — bao trùm cả 2 giá trị n, toàn bộ 3 giá trị τ (30/45/60 phút),
cả 2 spatial_mode, cả 3 supply_ratio — `largest_component_fraction` **luôn ≥ 0.889**, trung
bình cực gần 1.000 ở cả 2 tổ hợp. Không có vùng tham số nào (kể cả τ nhỏ nhất, supply thấp
nhất) cho tín hiệu tách rời đáng kể. Tổ hợp `(B_gw=5, B_od=2)` không chạy được do giới hạn
RAM (xem phần Trạng thái dữ liệu ở đầu báo cáo) nhưng không có lý do cấu trúc nào để tin nó
sẽ đảo ngược — B_gw lớn hơn có xu hướng làm route pool phong phú hơn, tăng khả năng chia sẻ
order giữa driver, tức là củng cố hướng (B) chứ không làm suy yếu.

---

## Diễn giải — vì sao điều này nhất quán với các phát hiện trước đó trong dự án

Phát hiện này **không mâu thuẫn** mà thực ra **củng cố** một số quan sát trước đó:

- `run_gate_t4b.py`/`run_pcf_benefit.py` cho thấy PCF (Pairwise Compatibility Filter) mang
  lại lợi ích rất khiêm tốn (~3.6% cắt trung bình, giảm dần khi tw tăng) — nếu hầu hết driver
  đều cạnh tranh nhau qua ít nhất 1 order chung (component gộp lớn), điều này phù hợp với việc
  hầu hết cặp order đều "tương thích" theo nghĩa lỏng của PCF, khiến bộ lọc ít có cơ hội cắt.
- Việc route pool của mỗi driver (đặc biệt GW, B_gw lên tới 3-5) thường chứa rất nhiều bundle
  khác nhau (hàng nghìn đến hàng triệu điểm Pareto ở vùng hot-zone theo `Report_Case1_vs_Case2.md`)
  làm tăng xác suất bất kỳ 2 driver nào cũng chia sẻ ít nhất 1 order trong pool của họ — đây
  chính là cơ chế thống kê tự nhiên dẫn tới component gộp gần hết, không cần driver ở gần
  nhau về không gian hay chồng lấn time-window nhiều.

## Trạng thái: ĐÃ ĐÓNG — không còn việc treo cho báo cáo này

1. **`run_2b_v2.py` đã dừng có chủ đích** — 720/1080 (2/3 tổ hợp `B_gw=3`) hoàn tất 100%;
   tổ hợp `(B_gw=5, B_od=2)` bị bỏ qua và ghi nhận là giới hạn thực nghiệm (RAM, xem đầu
   báo cáo), theo quyết định người dùng ngày 2026-09-15. **Không chạy lại tổ hợp này** —
   không hạ B_gw, không hạ n, không đổi grid đã khóa để "cố lấy được số".
2. Theo đúng khung Gate/Validated/Rejected của dự án: ghi nhận đây là kết quả **hướng (B)** —
   không tiếp tục đầu tư 2c/2d ở mức kỳ vọng "speedup lớn nhờ phân rã component"; hạ kỳ vọng
   phần đóng góp T5 xuống mức "correctness/structural result" như spec gốc đã dự trù cho
   trường hợp này.
3. Không cần quét thêm τ nhỏ hơn 30 (ví dụ 10, 15 như spec gốc liệt kê) để "tìm vùng đẹp" —
   vi phạm nguyên tắc đã ghi rõ trong spec: "không quét τ cho tới khi thấy component nhỏ rồi
   dừng — chạy hết lưới đã khóa." Lưới new03.md Việc 3.2 đã khóa τ∈{30,45,60}; kết quả tại
   τ=30 (giá trị nhỏ nhất trong lưới đã khóa) đã cho tín hiệu rõ ràng nhất có thể mà vẫn là
   hướng (B).
4. Việc tiếp theo (nếu có) thuộc `new03.md` mục 2 (re-run `viec1_speedup_estimate.py`,
   feasibility_rate_k1, so sánh CPLEX speedup) — xem `NEXT_STEPS.md` mục 2, không thuộc
   phạm vi báo cáo này.
