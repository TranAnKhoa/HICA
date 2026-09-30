# Report: Test B — Hull Filtering tại DP Intermediate State

> Thực thi theo `Testb_hull_final.md`. Khác Test A (post-hoc trên route hoàn chỉnh), Test B
> sửa **DP thật** để lọc hull ngay tại mỗi state trung gian `(v, IV, Cd)`, đo liệu điều này
> có giảm peak frontier / tăng tốc DP thật hay không — đây là câu hỏi Test A không trả lời
> được.

**Kết luận một câu:** Peak frontier reduction chỉ **3.7%-15.4%** (mean=7.7%, median=6.2%)
— **thấp hơn cả Test A** (10.9-26.5%), và runtime gần như không đổi (speedup 0.97-1.16x,
trung bình 1.05x — về cơ bản không đáng kể). **Không implement chính thức vào
`dp_labeling.py`/`t6_dp.py`.** Proposition ở §0 của spec (supported completeness suffices)
**vẫn đúng và đáng viết vào luận văn** — đây là kết luận toán học độc lập với kết quả thực
nghiệm này.

---

## 0. An toàn thực thi — không sửa core đã verify

`t6_dp.py` đã PASS Gate 0/616/160 nhiều lần, được nhiều pipeline khác (2a/2b, RQ1, Test8)
phụ thuộc. Theo quyết định người dùng (2026-09-16), **không sửa file gốc** — tạo bản copy
riêng `spec_2a_2b`-adjacent: `experiments/T2BFS/t6_dp_hull.py`, giống hệt `t6_dp.py` ngoại
trừ 1 thay đổi duy nhất: thêm `hull_filter_on_pareto()` ngay sau `_filter_dominated_labels()`
tại mỗi key `(v, IV, Cd)`, ở cả 2 vị trí gọi dominance trong vòng lặp round-based (closure
delivery/home VÀ mở rộng pickup sang round kế). Hàm hull dùng lại nguyên
`lower_hull_on_pareto()` đã audit độc lập ở Test A (0 mismatch, brute-force numeric).

`run_dp()` trong bản copy nhận thêm tham số `use_hull_filter` (mặc định `True`); khi đặt
`False`, hành vi tương đương 100% `t6_dp.py` gốc — dùng để so sánh trực tiếp trên cùng
instance mà không cần chạy 2 module khác nhau.

## 1. Gate §3 — BẮT BUỘC trước khi tin số liệu, đã PASS

So sánh **hull của brute-force** (không phải toàn bộ Pareto set — đúng theo Proposition §0:
hull filter cố ý bỏ unsupported point) với output của `t6_dp_hull.run_dp(use_hull_filter=True)`,
trên n≤6:

```
Grid: n∈{3,4,5,6} × B∈{2,3} × tw∈{60,120} × spatial_mode∈{dispersed,clustered} × seed∈{0,1,2}
= 96 instance
Kết quả: 0/96 violation
[PASS] Mọi supported point (hull) của brute-force đều có mặt trong t6_dp_hull output.
```

`brute_force.py` (độc lập hoàn toàn với `t6_dp*`, không import chung logic) dùng làm oracle
— đúng tinh thần Gate 0 gốc của dự án. Test B được phép tiếp tục và tin cậy kết quả dưới đây.

## 2. Kết quả chính — 8 seed, cùng hot cell dùng ở Test A

n=20, B_gw=4, tw=240, n_drivers=5, dispersed — 8 seed giống hệt Test A để đối chiếu được.

| seed | peak (no hull) | peak (hull) | peak reduction | rt no-hull | rt hull | speedup |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 738,694 | 685,591 | 7.2% | 53.25s | 48.56s | 1.10x |
| 12345 | 631,024 | 607,389 | 3.7% | 41.20s | 41.43s | 0.99x |
| 8080 | 673,297 | 637,943 | 5.3% | 43.23s | 43.98s | 0.98x |
| 999 | 640,514 | 609,027 | 4.9% | 40.37s | 37.69s | 1.07x |
| 555 | 800,091 | 712,219 | 11.0% | 58.94s | 50.70s | 1.16x |
| 777 | 952,359 | 854,547 | 10.3% | 68.62s | 63.73s | 1.08x |
| 42 | 649,154 | 623,674 | 3.9% | 40.63s | 41.82s | 0.97x |
| 2026 | 1,153,873 | 976,551 | 15.4% | 76.54s | 71.70s | 1.07x |

**Thống kê tổng hợp:**
```
peak_frontier reduction: mean=7.7%  median=6.2%  min=3.7%  max=15.4%
runtime speedup:         mean=1.05x median=1.07x min=0.97x max=1.16x
```

Cả 2 chỉ số đều **thấp hơn kỳ vọng** — thậm chí thấp hơn cả Test A (post-hoc, 10.9-26.5%).
`peak_frontier` giảm nhẹ (3.7-15.4%) nhưng runtime gần như không đổi (2/8 seed thậm chí hơi
chậm hơn không dùng hull: seed 12345, 42, 8080 có speedup <1.0x) — chi phí tính hull tại mỗi
state (thêm 1 bước sort + quét monotone chain cho mỗi key) gần như triệt tiêu lợi ích từ việc
có ít label hơn để mở rộng.

## 3. So sánh trực tiếp Test A vs Test B — không suy diễn được từ nhau

| | Test A (post-hoc, route hoàn chỉnh) | Test B (intermediate state, DP thật) |
|---|---:|---:|
| Đo ở đâu | Output cuối (bundle hoàn chỉnh) | Mọi state trung gian, mọi round |
| reduction mean | ~17.65% (8 seed) | ~7.7% (cùng 8 seed) |
| reduction range | 10.9% - 26.5% | 3.7% - 15.4% |
| Ý nghĩa | Redundancy trong route pool cuối | Tăng tốc DP thật |

Đúng như spec cảnh báo trước: **kết quả Test A không dự đoán được kết quả Test B**. Ở đây
Test B cho kết quả **kém hơn** Test A, không phải tốt hơn — và nguyên nhân **đã được kiểm
chứng là lời giải thích tầm thường (trivial), không phải hiệu ứng DP phức tạp nào**:

**Kiểm tra giả thuyết tầm thường (2026-09-16, theo yêu cầu người dùng — rẻ, dùng lại data/
code đã có, không chạy gì mới ngoài 1 lần đếm bổ sung):** so sánh số điểm trung bình mỗi
nhóm `(driver, bundle)` ở Test A với số label trung bình mỗi state trung gian `(v, IV, Cd)`
ở Test B, trên cùng seed:

```
avg_points_per_bundle_group (Test A, route hoàn chỉnh) = 25,239 / 12,390 = 2.037
avg_labels_per_state       (Test B, intermediate)      = 1.385 (seed=12345)
                                                          1.533 (seed=1)
                                                          1.340 (seed=8080)
                                                          1.409 (seed=999)
                                                          mean ≈ 1.417 qua 4 seed
```

**Xác nhận: avg_labels_per_state (~1.42) thấp hơn rõ rệt avg_points_per_bundle_group
(~2.04)** — đúng khoảng 1.2-1.5 mà giả thuyết dự đoán. Điều này giải thích **tầm thường**
tại sao Test B cho reduction thấp hơn Test A: state trung gian vốn dĩ đã có ít điểm Pareto
hơn/nhóm ngay từ đầu (vì mỗi state là một "lát cắt" hẹp hơn route hoàn chỉnh — ít cơ hội tích
lũy nhiều biến thể K/W khác nhau tại cùng 1 vị trí/tập order chưa xong), nên tự nhiên có ít
dư địa hơn để convex hull cắt bớt. **Không cần viện tới cơ chế phức tạp nào (như "cắt nhánh
sớm rồi tái sinh qua đường khác ở round sau") để giải thích kết quả** — bản thân cấu trúc dữ
liệu ở tầng trung gian đã kém "dày" hơn tầng route hoàn chỉnh, độc lập với việc hull filter
có hoạt động đúng hay không.

## 4. Quyết định theo Interpretation Guide (`Testb_hull_final.md` §5)

| Peak frontier reduction (Test B) | Gate §3 | Quyết định |
|---|---|---|
| Nhỏ (tương tự hoặc thấp hơn Test A) | — | Vẫn giữ Proposition §0, đóng góp T4 chủ yếu dựa vào Proposition + lower-bound, không phải speedup thực tế |

Với mean=7.7% (thấp hơn cả Test A's 17.65%): **rơi đúng vào dòng "nhỏ"** của bảng quyết định.
**Không implement** `hull_filter_on_pareto` chính thức vào `dp_labeling.py`/`t6_dp.py` — chi
phí runtime thêm vào gần như triệt tiêu lợi ích, và mức giảm peak frontier quá khiêm tốn để
biện minh cho việc sửa vào core đã được verify kỹ (Gate 0/616/160).

## 5. Proposition §0 — vẫn đúng, vẫn đáng viết vào luận văn

Theo đúng tinh thần spec: **Proposition (Supported Completeness Suffices) là một correction
toán học cho định nghĩa completeness, độc lập với thực nghiệm này có cho speedup hay không.**
Chứng minh 3 dòng (mọi nơi trong pipeline — Algorithm B, mọi removal-solve của Algorithm C,
mọi deviation trong DSIC audit — đều chỉ chọn route bằng affine cost `K+b·W`, nên unsupported
point không bao giờ ảnh hưởng optimality/DSIC/IR) không phụ thuộc vào việc filter hull có
tăng tốc DP hay không. Đây là phần "chắc ăn" của thí nghiệm — Gate n≤6 (0/96 PASS) là bằng
chứng thực nghiệm hỗ trợ đúng đắn của chính Proposition (không phải cho việc implement nó vào
production DP).

**Hệ quả thực tế cho đóng góp T4**: đóng góp chính nằm ở **Proposition + Gate hoàn thành**
(một kết quả cấu trúc/lý thuyết đúng đắn), không phải ở speedup thực nghiệm — đúng như dòng
"nhỏ" trong bảng Interpretation đã dự trù cho trường hợp này.

## 6. Không trì hoãn RQ1

Theo đúng §6 của spec: EJOR cần cả (a) T4/T5 mạnh VÀ (b) RQ1 đáng kể. Test B (dù kết quả nhỏ)
+ Proposition §0 đã hoàn thành phần (a) ở mức "correctness/structural result" — không thay
thế RQ1. Việc tiếp theo ưu tiên là tiếp tục RQ1 (`Rq1.md`, hiện đã xong §1.1-1.4, đang ở §3
alignment metric), không đầu tư thêm vào tối ưu T4.

---

## File & tái tạo

```
experiments/T2BFS/t6_dp_hull.py       bản copy t6_dp.py + hull_filter_on_pareto tại
                                        mọi state trung gian (use_hull_filter param);
                                        2026-09-16 thêm n_states_total/n_labels_before_hull_total
                                        (chỉ đếm, không đổi logic filter/dominance nào —
                                        đã regression-check lại Gate §3 vẫn 0/96 PASS)
spec_2a_2b/src/gate_hull_n6.py        Gate §3 — 0/96 PASS
spec_2a_2b/src/test_b_hull_hotcell.py Test B chính — 8 seed, hot cell n=20/B_gw=4/tw=240
```
Chạy lại gate: `python gate_hull_n6.py`. Chạy lại Test B: `python test_b_hull_hotcell.py`
(cả hai dùng Python 3.7.7).

**Kiểm tra giả thuyết tầm thường** (mục 3): dùng `res["n_states_total"]` và
`res["n_labels_before_hull_total"]` từ `t6_dp_hull.run_dp()` — chia cho nhau để ra
`avg_labels_per_state`, so với `avg_points_per_bundle_group` đã có sẵn từ Test A
(`25239/12390`). Không cần chạy Test A/B lại, chỉ cần 1 lần chạy DP mới/seed để lấy 2 số
đếm bổ sung.
