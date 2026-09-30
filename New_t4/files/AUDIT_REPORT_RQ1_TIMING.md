# Audit report — dp_fast.py (LB2 label rule) trên instance RQ1 thật: wall-clock đo được

**Ngày chạy:** 2026-09-23
**Thay thế phần suy đoán ở `AUDIT_REPORT_LABEL_RULE.md` §6** ("chưa đo, chỉ suy đoán từ
tỉ lệ giá FD") bằng số đo thật, trực tiếp trên đúng 5 instance RQ1 đã dùng ở các report
K* trước (`kstar_rq1_crosscheck.py`).

**Kết luận một câu:** trên instance RQ1 thật, rule label mới cho **speedup 1.4×–2.6×
trên GW** (nơi rule fire), **tiết kiệm 44–63% label extension**, tổng thể toàn instance
**2.10× wall-clock, 56.8% extension saved** — mạnh hơn hẳn instance tổng hợp dùng để
audit toán học trước đó (nơi speedup dao động 0.75×–3.1× tuỳ giá FD, quanh 1× ở mức giá
mặc định). Đúng như `.tex` đã suy đoán ("this must be measured, not assumed") — RQ1
thật đúng là ở trong "chế độ hiệu quả" của rule.

---

## 1. Việc phải sửa trước khi đo được đúng — không chỉ là chạy code có sẵn

Code gốc trong `New_t4/files` (`hica_core.py`, `dp_rules.py`, `dp_fast.py`) được viết
và audit trên **instance tổng hợp** (`hica_core.random_instance`), khác RQ1 thật ở 3
điểm — nếu không sửa, số đo sẽ sai, không phải chỉ "xấp xỉ":

1. **`SERVICE`**: hard-code `2.0` phút/stop trong `hica_core.py`, nhưng RQ1 thật dùng
   `SERVICE_MIN=5.0` (`instance_gen.py`). Đã patch `SERVICE` trên cả 3 module (sau khi
   import, vì `dp_rules.py`/`dp_fast.py` copy giá trị vào namespace riêng lúc
   `from hica_core import SERVICE`).
2. **`ready_time_d`**: RQ1 thật có opening time cho delivery (`instance_gen.py` dòng
   228: `ready_d = ready_p`, xác nhận đối chiếu với `t6_dp.py::_try_delivery` dòng 155 —
   driver **phải chờ** nếu đến delivery sớm). Code gốc giả định delivery không có
   opening time. Đã sửa **theo đúng Remark "Delivery time windows with an opening time"**
   của `T4_Label_Rule.tex` (không đổi thuật toán/chứng minh, chỉ mở rộng đúng phạm vi đã
   chứng minh an toàn): thêm `Order.e_d`, sửa `simulate()`, `stop_e()`,
   `future_stops()`, `absorption()` trong `dp_rules.py`, và nhánh onboard/future-delivery
   absorption trong `dp_fast.py`.
3. **`driver.t1`**: RQ1 thật **không có deadline cứng `t1` cho bất kỳ driver nào**
   (không xuất hiện trong `t2_gen.py`/`instance_gen.py`/`t6_dp.py` — GW là open-route,
   OD chỉ bị ràng buộc bởi `τ`). Ban đầu tôi đặt nhầm `t1 = t0 + availability_min` cho
   GW (đọc sai một field chỉ là metadata — comment gốc trong `t2_gen.py` dòng 185 nói rõ
   "ghi nhận, KHÔNG ép thành ràng buộc feasibility riêng"). Đã sửa: `t1 = +∞` cho cả
   GW và OD.
4. **Tọa độ/travel time**: `hica_core.dist()/tt()` giả định toạ độ `(x,y)` trực tiếp;
   `instance_gen.py` không xuất toạ độ node ra ngoài, chỉ có hàm `travel_time(a,b)`.
   Đã patch `dist`/`tt` của cả 3 module thành wrapper gọi thẳng `travel_time` thật của
   RQ1 (Euclidean, cùng `SPEED_KMH=20` — đã khớp sẵn, không cần suy diễn toạ độ).

**Xác nhận cầu nối đúng** (không chỉ tin, đã kiểm tra chéo): route pool sau Pareto
filter của `gw0` (n=10, seed=999) tính ra qua cầu nối này = **254 route**, khớp chính
xác với con số đã biết từ `kstar_rq1_crosscheck.py` (report trước, độc lập).

**Re-audit an toàn sau khi sửa**: chạy lại `kstar_equal` trên instance n=10/seed=999
với đúng setup RQ1 (SERVICE=5.0, có `e_d`) — `kstar_equal=True` trên cả 4 driver, xác
nhận rule vẫn an toàn sau khi mở rộng đúng phạm vi.

---

## 2. Kết quả — 5 instance RQ1 thật, so ext/wall-clock có/không rule (LB2)

| n | n_drv | seed | driver | cls | B | ext (off→on) | saved | wall (off→on, s) | speedup | fired |
|---:|---:|---:|---|---|---:|---|---:|---|---:|---:|
| 12 | 5 | 42 | gw0 | GW | 3 | 22,844→9,736 | 57.4% | 0.24→0.10 | **2.45×** | 4,583 |
| 12 | 5 | 42 | gw1 | GW | 3 | 22,844→10,025 | 56.1% | 0.20→0.12 | 1.74× | 4,743 |
| 12 | 5 | 42 | od0/od1/od2 | OD | 3 | không đổi | 0.0% | ~0 | ~1.0× | 0 |
| 10 | 4 | 1 | gw0 | GW | 3 | 22,162→12,153 | 45.2% | 0.25→0.14 | 1.81× | 4,454 |
| 10 | 4 | 1 | gw1 | GW | 3 | 22,162→12,318 | 44.4% | 0.23→0.16 | 1.44× | 4,566 |
| 10 | 4 | 1 | od0/od1 | OD | 3 | không đổi | 0.0% | ~0 | ~1.0× | 0 |
| 15 | 5 | 7 | gw0 | GW | 3 | 74,044→27,195 | 63.3% | 0.88→0.34 | **2.60×** | 14,618 |
| 15 | 5 | 7 | gw1 | GW | 3 | 74,046→28,073 | 62.1% | 0.88→0.38 | 2.34× | 15,372 |
| 15 | 5 | 7 | od0/od1/od2 | OD | 3 | không đổi | 0.0% | ~0 | ~1.0× | 0 |
| 12 | 6 | 123 | gw0 | GW | 3 | 34,260→14,158 | 58.7% | 0.37→0.20 | 1.87× | 6,435 |
| 12 | 6 | 123 | gw1 | GW | 3 | 34,265→14,189 | 58.6% | 0.45→0.17 | **2.57×** | 6,611 |
| 12 | 6 | 123 | gw2 | GW | 3 | 34,264→13,787 | 59.8% | 0.36→0.18 | 2.04× | 6,277 |
| 12 | 6 | 123 | od0/od1/od2 | OD | 3 | không đổi | 0.0% | ~0 | ~1.0× | 0 |
| 10 | 4 | 999 | gw0 | GW | 3 | 16,277→8,499 | 47.8% | 0.16→0.10 | 1.64× | 3,721 |
| 10 | 4 | 999 | gw1 | GW | 3 | 16,277→8,069 | 50.4% | 0.15→0.10 | 1.53× | 3,546 |
| 10 | 4 | 999 | od0/od1 | OD | 3 | không đổi | 0.0% | ~0 | ~1.0× | 0 |

**Tổng toàn bộ 5 instance × mọi driver:** wall-clock **4.21s → 2.00s (speedup 2.10×)**,
label extensions **56.8% saved**.

---

## 3. Đọc kết quả — GW vs OD hoàn toàn khác nhau

- **GW: rule fire mạnh, hiệu quả rõ rệt.** 44–63% extension saved, speedup **1.4×–2.6×**
  trên mọi instance/seed đã thử, không có ngoại lệ. Đây là driver có route pool lớn
  (hàng trăm route sau Pareto filter, hàng chục nghìn sequence thô), rule cắt được nhánh
  sớm trước khi enumerate hết.
- **OD: rule không fire một lần nào** (`fired=0` tuyệt đối, mọi instance). Route pool
  của OD vốn đã rất nhỏ (5–24 route sau filter, theo dữ liệu report K* trước) vì bị chặn
  chặt bởi `τ` (detour budget) — không có gì để cắt thêm, đúng như dự đoán cấu trúc: OD
  đã "tự pruned" bởi ràng buộc τ trước khi rule label kịp có cơ hội fire.

Đây khác biệt rõ so với bảng "giá FD scaled" trong `.tex` (đo trên instance tổng hợp,
GW và OD trộn chung) — trên RQ1 thật, **toàn bộ lợi ích tập trung ở GW**, và OD hoàn
toàn trung tính (không lợi, không hại, vì rule không bao giờ fire ở đó).

---

## 4. So với suy đoán trong `AUDIT_REPORT_LABEL_RULE.md` §6 — đúng hướng, mạnh hơn dự kiến

`.tex` gợi ý: trên RQ1, K* hậu xử lý cắt 77–97% (so với ~61% trên instance tổng hợp) —
FD tương đối rẻ hơn trên RQ1, nên rule label **có thể** hiệu quả hơn. Số đo thật xác
nhận đúng hướng suy đoán này, và **mạnh hơn** những gì bảng "giá FD × 1.0" của `.tex`
gợi ý (speedup ≈1.0×, 27–30% ext saved trên instance tổng hợp ở mức giá FD "mặc định")
— trên RQ1 thật, GW đạt speedup trung bình ~2× và ext saved 44–63%, cao hơn hẳn mức
"giá FD × 1.0" và gần với mức "giá FD × 0.6" (2.8–3.1×, 73–76% saved) của bảng đó.

---

## 5. Giới hạn của số đo này

- Chỉ đo trên **enumerator Python thuần** (`dp_fast.py`), không phải implementation
  production tối ưu (C/Cython hay tích hợp trực tiếp vào `t6_dp.py`) — số tuyệt đối
  (0.1–0.9s/driver) không phản ánh runtime thật của pipeline `spec_2a_2b`, chỉ tỉ lệ
  speedup/ext-saved là có ý nghĩa so sánh.
- Chỉ đo ở `B=3` (khớp 5 instance RQ1 gốc đã dùng cho K* crosscheck) — chưa đo `B=4`
  trên RQ1 thật (đã đo trên instance tổng hợp, xem `AUDIT_REPORT_LABEL_RULE.md` §3.2).
- Rule mới **chưa được tích hợp vào `t6_dp.py`** (Algorithm A production) — đây vẫn là
  một audit độc lập trên implementation riêng (`dp_fast.py`), không phải số đo của
  pipeline chính.

---

## File & tái tạo

```
New_t4/files/dp_fast_rq1.py            Cau noi RQ1 that -> hica_core.Order/Driver,
                                         do wall-clock/ext co-khong rule tren 5 instance
New_t4/files/dp_fast_rq1_results.csv   Ket qua day du (16 dong: 5 instance x 3-6 driver)
New_t4/files/hica_core.py              SUA: Order.e_d, simulate() cho tai delivery
New_t4/files/dp_rules.py               SUA: stop_e/future_stops/absorption mo rong dung
                                         Remark cua .tex (delivery opening time)
New_t4/files/dp_fast.py                SUA: cho tai delivery, A tinh ca onboard/future
                                         delivery
```

Chạy lại (Python 3.13, anaconda, không cần CPLEX):
```
"C:\Users\An Khoa\anaconda3\python.exe" dp_fast_rq1.py
```
