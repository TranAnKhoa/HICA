# Report: Convex Hull Dominance Test cho Algorithm A — v1 (sai scope) → v2 (đã sửa, 8 seed)

> Lịch sử: v1 (`Convex_hull.md`) tính hull sai scope (gộp toàn bộ bundle khác nhau của 1
> driver vào 1 hull) → 99.99% reduction, KHÔNG dùng số này ở đâu. v2 (`Convex_hull_02.md`)
> sửa scope đúng (mỗi `(driver, bundle)` riêng) — lần chạy đầu (1 seed) cho 13.4%, nhưng
> **chính thuật toán hull tự viết của v2 cũng có 1 bug** (phát hiện qua kiểm tay độc lập theo
> yêu cầu người dùng — xem mục 2) khiến con số ban đầu bị lệch nhẹ. Sau khi sửa bug + chạy
> **8 seed** (không phải 1), kết luận cuối dùng phân phối 8 điểm dữ liệu, không phải 1 số.

**Kết luận một câu:** Reduction thật (đúng scope, thuật toán đã sửa, 8 seed) dao động
**10.9%-26.5%**, mean=17.65%, median=17.85%, std=4.44 — **6/8 seed dưới ngưỡng 20%**, chỉ
2/8 vượt (1 trong đó là outlier rõ rệt). **Quyết định: KHÔNG implement convex-hull dominance
vào Algorithm A** — đa số tín hiệu nằm dưới ngưỡng "đáng công" của spec, và ngay cả ở mean
(~17.65%) vẫn dưới 20%. Không chạy Gate n≤6 đầy đủ (chỉ bắt buộc khi kết luận là implement).

---

## 1. Vì sao v1 sai — bài học kỹ thuật (không đổi so với bản trước)

v1 gộp **toàn bộ** điểm `(K,W)` của 1 driver (mọi bundle khác nhau) thành 1 tập rồi tính hull
chung. Sai vì route phục vụ bundle khác nhau là mandatory fulfillment khác nhau trong WDP
(Đề cương §7.4) — không thể thay thế nhau chỉ vì cùng chi phí thấp. Dominance gốc của
Algorithm A (`_pareto_front` trong `dp_labeling.py`) vốn đã tôn trọng đúng ranh giới này;
v1's hull-over-everything phá vỡ nó, cho ra 99.99% hoàn toàn không đại diện cho việc prune
hợp lệ nào.

## 2. Bug thứ hai — phát hiện qua kiểm tay độc lập (không phải audit tự động)

Sau khi có kết quả v2 đầu tiên (13.4%, 1 seed), người dùng yêu cầu 2 việc rẻ trước khi tin số
liệu: (1) chạy thêm seed để kiểm ổn định, (2) **kiểm tay thuật toán hull trên vài group cụ
thể, tách biệt khỏi câu hỏi "có đáng implement"** — với lý do "audit của v1 không bắt được
bug vì nó kiểm đúng thứ nó định nghĩa, không kiểm đúng thứ cần kiểm."

Việc (2) phát hiện đúng một bug thật: điều kiện `turns_right()` copy từ code mẫu trong
`Convex_hull_02.md` (`cross(...) < 0`) bị **sai dấu**, khiến `lower_hull_on_pareto()` **bỏ
sót** một số điểm hull hợp lệ. Phát hiện bằng cách:
- In toàn bộ điểm `(K,W)` của 5 group (driver,bundle) nhiều điểm nhất, đánh dấu điểm nào
  thuật toán claim là hull.
- Kiểm độc lập từng điểm bằng brute-force numeric (quét dày `b` từ 0 đến 200, bước 0.001):
  điểm nào từng là argmin của `K+b·W` với ít nhất 1 giá trị `b≥0` thì PHẢI nằm trên hull.
- Kết quả lần đầu: **13-18/45 điểm kiểm tra bị mismatch** (ví dụ điểm `K=22.702, W=8.0766`
  thực sự là argmin tại `b=5.0` nhưng thuật toán cũ không giữ lại).

**Sửa**: đổi điều kiện pop từ `cross < 0 → pop khi >0` (tức giữ khi `cross≤0`) sang **giữ khi
`cross≥0`, pop khi `cross<0`**. Xác nhận lại bằng đúng phép kiểm brute-force trên: **0/45
mismatch** trên cả 5 group sau khi sửa (`spec_2a_2b/src/convex_hull_manual_check.py`).

**Bài học ghi nhận rõ theo đúng tinh thần yêu cầu**: audit tự động của v1 (100/100 bid chọn
điểm trên hull) không hề sai về logic nó kiểm — nhưng nó chỉ xác nhận thuật toán tự nhất
quán với chính nó, không xác nhận thuật toán đúng theo định nghĩa toán học độc lập. Phép
kiểm brute-force numeric (không phụ thuộc code hull) mới là bằng chứng đáng tin.

## 3. Kết quả 8 seed (đúng scope, thuật toán đã sửa)

Cùng hot cell: n=20, B_gw=4, tw=240, n_drivers=5, dispersed. Chạy DP thật (`dp_labeling.py`,
không sửa) cho từng seed, 8 seed độc lập (không phải 1 lưới đầy đủ — theo đúng tinh thần "chỉ
đủ để biết 13.4% có đại diện hay không", không nhân rộng toàn bộ grid).

| seed | Pareto points | hull points | reduction toàn bài | reduction bundle_size=4 | ≥20%? |
|---:|---:|---:|---:|---:|:---:|
| 1 | 25,742 | 22,943 | 10.9% | 11.9% | |
| 12345 (gốc) | 25,239 | 22,021 | 12.8% | 14.1% | |
| 8080 | 27,995 | 23,403 | 16.4% | 18.1% | |
| 999 | 29,914 | 24,763 | 17.2% | 18.9% | |
| 555 | 32,187 | 26,218 | 18.5% | 20.2% | |
| 777 | 30,112 | 24,515 | 18.6% | 20.4% | |
| 42 | 33,387 | 26,626 | 20.3% | 22.2% | ✓ |
| 2026 | 42,271 | 31,049 | **26.5%** (outlier) | 28.7% | ✓ |

**Thống kê tổng hợp (8 seed):**
```
mean   = 17.65%
median = 17.85%
std    = 4.44
min    = 10.9%   (seed=1)
max    = 26.5%   (seed=2026)
6/8 seed dưới ngưỡng 20%; 2/8 vượt (seed=42 sát ngưỡng 20.3%, seed=2026 là outlier rõ rệt)
```

Phân phối tập trung khá rõ quanh 15-18%, KHÔNG phải "ổn định tuyệt đối ở 1 mức" như seed gốc
đơn lẻ (12.8-13.4%) gợi ý ban đầu, nhưng cũng KHÔNG phải phân tán vô định — đa số khối lượng
nằm dưới ngưỡng 20%, chỉ 1 seed (2026) tách biệt hẳn khỏi phần còn lại.

### Theo bundle_size (nhất quán qua mọi seed)

Reduction luôn tăng đơn điệu theo bundle_size ở cả 8 seed: `bundle_size=1` luôn 0% (hiển
nhiên, 1 điểm/group), `bundle_size=2` luôn <6%, `bundle_size=3` luôn 7-17%, `bundle_size=4`
luôn cao nhất (12-29%) — đây là pattern ổn định, không đổi giữa các seed, chỉ độ lớn thay
đổi.

## 4. Quyết định theo Interpretation Guide (`Convex_hull_02.md` §4)

| Test A reduction | Gate n≤6 | Quyết định áp dụng |
|---|---|---|
| < 20% | (không cần chạy gate) | Dừng — không đáng công |
| ≥ 20% | PASS | Làm Test B, nếu Test B cũng giảm frontier đáng kể → implement chính thức |

Với 6/8 seed (75%) dưới ngưỡng và mean/median (~17.65%/17.85%) đều dưới 20%: **quyết định
là DỪNG, không implement** — seed 2026 (26.5%) là ngoại lệ cần ghi nhận nhưng không đủ để
đảo ngược kết luận tổng thể dựa trên đa số dữ liệu quan sát được. Không cần chạy Gate n≤6
đầy đủ (gate chỉ bắt buộc khi kết luận đi theo hướng implement).

**Về seed 2026 (outlier)**: nếu muốn hiểu tại sao seed này lệch hẳn, đây có thể là hướng tìm
hiểu riêng (có thể liên quan cấu trúc instance cụ thể khiến nhiều route Pareto "gần thẳng
hàng" hơn) — nhưng không bắt buộc cho quyết định implement/không-implement đã đủ rõ từ đa số
seed còn lại.

## 5. Ý nghĩa — dùng làm bằng chứng cho hướng lower-bound T4

Không đổi so với kết luận trước: reduction ở mức 10-27% (không đạt ngưỡng ≥50% như v1 sai
tưởng, và cũng không đạt ổn định ≥20% như cần để implement) cho thấy frontier Pareto hiện tại
(sau dominance gốc) đã tương đối "dày" — phần lớn các group `(driver, bundle)` chỉ có 1-2
điểm Pareto, không còn nhiều dư địa để một quy tắc hình học đơn giản (convex hull) cắt thêm.
Dữ liệu 8 seed này (đặc biệt bảng theo bundle_size, nhất quán qua mọi seed) là nguồn phù hợp
để thiết kế instance worst-case cho lower-bound T4.

---

## File & tái tạo

```
spec_2a_2b/src/convex_hull_test.py         v1 — SAI SCOPE, chỉ giữ đối chiếu lịch sử,
                                             KHÔNG dùng số liệu ở đâu khác
spec_2a_2b/src/convex_hull_test_v2.py      v2 — ĐÚNG SCOPE, đã sửa bug turns_right (2026-09-16)
spec_2a_2b/src/convex_hull_manual_check.py kiểm tay độc lập (brute-force numeric) —
                                             phát hiện bug turns_right, xác nhận 0 mismatch
                                             sau khi sửa trên 5 group nhiều điểm nhất
```
Chạy lại 1 seed: `python -c "import convex_hull_test_v2 as C; C.run_one_seed(<seed>)"`.
Chạy kiểm tay: `python convex_hull_manual_check.py`. Cả hai dùng Python 3.7.7
(`C:\Users\An Khoa\AppData\Local\Programs\Python\Python37\python.exe`).
