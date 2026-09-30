---
name: T4_Verification_Spec
purpose: checklist to close out before showing T4_Local_Pruning_Frontier.tex to supervisor
status: draft — run each test, fill in the "Kết quả" cell, keep this file as the audit trail
---

# T4 — Việc cần làm trước khi đưa thầy xem

## 0. Vì sao cần file này

Report trước (`Audit report — T4 Local Pruning Frontier theorem`, chạy trên máy bạn) đã
PASS toàn bộ, nhưng đó là **tái lập** (rerun cùng code `hica_core.py`/`kstar_rule.py` trên
môi trường khác), không phải **kiểm chứng độc lập**. Vì code tất định (deterministic),
việc số khớp giữa hai máy là điều nên xảy ra, không phải bằng chứng toán học đúng thêm.

File này liệt kê 5 việc còn thiếu, xếp theo thứ tự ưu tiên. Ba việc đầu là bắt buộc trước
khi đưa thầy; hai việc sau có thể làm song song hoặc sau.

| # | Việc | Bắt buộc trước khi đưa thầy? | Ước lượng thời gian |
|---|---|---|---|
| 1 | Independent re-implementation (phương pháp khác, không phải rerun) | **Có** | 3–5 giờ |
| 2 | Chạy `kstar_rule.py` trên môi trường thesis thật (Py 3.7 + CPLEX) + instance RQ1 thật | **Có** | 1–2 giờ |
| 3 | Đối chiếu activation-rate log cũ: mọi route active ⊆ K\* | **Có** (kiểm miễn phí, dùng lại log cũ) | 30 phút |
| 4 | Hoàn tất literature check (Desrosiers & Lübbecke, Barnhart et al.) | Nên có, không bắt buộc | 2–4 giờ |
| 5 | Kiểm metadata reference (DOI/venue/year) | Nên có, không bắt buộc | 1 giờ |

---

## 1. Independent re-implementation — kiểm chứng THẬT SỰ độc lập

### 1.1 Vì sao rerun không đủ

`hica_core.py` và `kstar_rule.py` là code tôi (Claude) viết. Chạy lại trên máy khác chỉ
xác nhận code không fragile theo phiên bản Python/scipy — không xác nhận toán học đúng.
Một bug trong logic `dominator_lines`/`kstar` sẽ tái lập y hệt ở mọi máy.

### 1.2 Cách làm

Viết **một implementation thứ hai**, khác thuật toán, để tính $\mathcal{K}^\star$ và so
với `kstar_rule.py`. Không cần khác ngôn ngữ, chỉ cần khác **đường tính toán**:

- `kstar_rule.py` tính margin bằng cách: dựng các đường thẳng affine `(a, w)` trong
  `dominator_lines`, tìm envelope nhỏ nhất, lấy max trên các điểm kink + hai đầu mút
  (dùng tính lõm của $\mu_r$).
- Bản đối chiếu nên tính margin bằng cách **khác về cấu trúc**, ví dụ:
  - **Grid search thô**: chia $\Theta$ thành 2000–5000 điểm đều nhau, tính
    $\mu_r(b) = E_r(b) - c_r(b)$ trực tiếp tại từng điểm (không giả định lồi/lõm gì),
    lấy max. Đây không dùng cấu trúc affine/kink — nếu ra cùng dấu (dương/âm) và cùng
    tập $\mathcal{K}^\star$ với bản kink-based, thì hai cách tính hoàn toàn khác nhau
    đồng ý với nhau.
  - Hoặc **giải LP trực tiếp**: với mỗi route $r$, giải bài toán tối ưu hóa tuyến tính
    "maximize $t$ s.t. $t \le a_l + b \cdot w_l\ \forall l \in D(r)$, $t \le c_r(b)$... "
    — thực ra đơn giản hơn: chỉ cần
    `max_b min(E_r(b) - c_r(b))` qua `scipy.optimize.linprog` hoặc bằng cách liệt kê mọi
    cặp đường thẳng và giải giao điểm bằng công thức khác (Cramer thay vì chia trực tiếp).

**Khuyến nghị cụ thể — cách dễ làm nhất, tốn ít công nhất mà vẫn thật sự độc lập:**
Viết hàm `kstar_gridcheck(routes, q, lo, hi, n_grid=5000)` chạy **grid brute-force**, không
gọi bất kỳ hàm nào trong `kstar_rule.py`, tự viết lại từ đầu `E_r(b)` và `c_r(b)` từ dữ
liệu thô `(rid, bundle, K, W)`. So `kept` từ grid-check với `kept` từ `kstar_rule.py` trên
mọi driver pool đã có trong 9 seed cũ.

### 1.3 Tiêu chí pass

- Hai tập `kept` phải khớp **tuyệt đối** (set giống hệt nhau) trên toàn bộ 9 seed × mọi
  driver. Nếu grid quá thô có thể lệch ở route có margin gần 0 (biên) — nếu lệch, tăng
  `n_grid` lên 20000–50000 trước khi kết luận là bug thật.
- Nếu hai bản không khớp: đây là tín hiệu quan trọng, dừng lại, không đưa thầy, báo tôi.

### 1.4 Việc cần điền

| Seed | pool size | `kept` (kink-based) | `kept` (grid-based) | Khớp? |
|---|---|---|---|---|
| 0 | | | | |
| 1 | | | | |
| ... | | | | |

---

## 2. Chạy trên môi trường thesis thật (Python 3.7.7 + CPLEX) với instance RQ1 thật

### 2.1 Vì sao cần

Toàn bộ audit trước chạy trên instance **tổng hợp** (Euclidean ngẫu nhiên), không phải
instance RQ1 thật của thesis. `kstar_rule.py` là pure Python (không cần scipy), nên chạy
được thẳng trong môi trường Py 3.7 + CPLEX mà không cần sửa gì — đây là điểm đã thiết kế
sẵn để dùng cho bước này.

### 2.2 Cách làm

1. Trong pipeline thesis, sau bước Algorithm A (route pool đã sinh xong cho một instance
   RQ1 cụ thể), export mỗi driver's pool ra dạng
   `[(route_id, bundle_frozenset, K, W), ...]` và dict `q = {order_id: fd_price}`.
2. Gọi:
   ```python
   from kstar_rule import local_frontier
   kept, margin = local_frontier(routes_of_driver_i, q, THETA_MIN, THETA_MAX)
   ```
   (`THETA_MIN`, `THETA_MAX` lấy từ `rq1_cost_gen.THETA_MIN/THETA_MAX` hoặc tên tương
   đương trong code thesis.)
3. Tính tỉ lệ cắt: `1 - len(kept)/len(routes_of_driver_i)`, tổng hợp theo GW/OD, theo n,
   theo B — giống format bảng đã có trong audit report cũ.
4. Chạy Algorithm B + C (CPLEX, exact) **hai lần** trên vài instance nhỏ (n ≤ 10, vài bid
   profile): một lần trên pool đầy đủ, một lần trên pool đã cắt bởi K\*. So `Z*`,
   `Z*_{-i}` cho từng driver, và payment từng winner.

### 2.3 Tiêu chí pass

- `|Z*(full) - Z*(pruned)| ≤ 1e-6` (hoặc mip_rel_gap của CPLEX) trên mọi instance/bid thử.
- Mọi payment khớp trong cùng ngưỡng.
- Tỉ lệ cắt được ghi lại — đây **là kết quả thật cho thesis**, không chỉ để audit.

### 2.4 Việc cần điền

| Instance (n, B) | pool trước | pool sau K\* | tỉ lệ cắt | \|Z\*(full)-Z\*(pruned)\| max | runtime B: trước/sau | runtime C: trước/sau |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## 3. Đối chiếu activation-rate log cũ (miễn phí — dùng lại dữ liệu đã có)

### 3.1 Cách làm

Đã có log activation-rate cũ (`testC2_activation_rate.log`, `testC2_multi_instance.log`)
ghi lại route nào từng active qua 1000 bid vector (5 instance). Không cần chạy lại gì:

1. Với mỗi instance trong log, chạy `local_frontier` trên pool tương ứng (pool phải giữ
   nguyên, chưa bị cắt bởi rule nào khác — nếu log cũ đã chạy trên pool bị per-driver hull
   cắt trước thì phải tái tạo lại pool gốc).
2. Kiểm: **mọi route từng active trong log ⊆ K\*** — đây là hệ quả bắt buộc của Định lý
   4(a). Nếu có route active mà KHÔNG nằm trong K\*, có bug ở một trong hai chỗ (log cũ
   hoặc `kstar_rule.py`) — phải tìm ra chỗ nào trước khi đưa thầy.
3. Tính thêm: hoạt động active/kept ratio (0.42–1.54% / (38.8% trung bình theo audit
   tổng hợp) — con số này khớp với "price of locality" nếu tỉ lệ active thấp hơn nhiều
   so với tỉ lệ kept.

### 3.2 Tiêu chí pass

- 0 route active nằm ngoài K\*, trên toàn bộ 5 instance × 1000 bid vector của log cũ.

### 3.3 Việc cần điền

| Instance | # route active (log cũ) | # route active ⊆ K\*? | Ngoại lệ (nếu có) |
|---|---|---|---|
| | | | |

---

## 4. Hoàn tất literature check (nên có, không chặn việc đưa thầy)

Đã tìm 3 nhánh liên quan (Beasley 1987 / Müller 1998 column dominance; Pereira & Averbakh
2013 robust interval-cost set covering; Aggarwal & Hartline 2006 + Kempe-Salek-Moore 2010
composability trong VCG). Chưa kiểm nhánh gần nhất về mặt ứng dụng: **dominance trong
branch-and-price / column generation cho crew scheduling và vehicle routing** — đây là nơi
nhiều khả năng nhất có rule tương tự.

Việc cần làm:
1. Đọc Desrosiers & Lübbecke, "A Primer in Column Generation" (chương về dominance rules
   trong pricing problem) — tìm xem có phiên bản "so sánh cột với cột nested/subset,
   uniform theo dual price hoặc theo một khoảng" hay không.
2. Đọc Barnhart, Johnson, Nemhauser, Savelsbergh & Vance (1998), "Branch-and-Price: Column
   Generation for Solving Huge Integer Programs" — mục về column elimination/dominance.
3. Nếu tìm thấy rule gần hơn 3 nhánh đã có, cập nhật Remark 18 trong file tex — không
   xóa 3 nhánh cũ, thêm vào.

---

## 5. Kiểm metadata reference (nên có, không chặn)

Các reference mới thêm ở Remark 18 lấy từ search, **chưa xác nhận qua nguồn gốc**:
- Beasley (1987) — rule lấy từ một bài trích dẫn thứ cấp (arXiv:2601.14424), chưa đọc bản
  gốc EJOR 31:85–93.
- Müller (1998) — đã đọc bản PDF gốc trực tiếp (không qua trích dẫn thứ cấp), tương đối
  tin cậy hơn, nhưng vẫn nên xác nhận đây đúng là bài được publish (không phải chỉ là
  bản draft/tech report).
- Pereira & Averbakh — hai nguồn cho năm khác nhau (2011 online-first vs 2013 print),
  cần chốt năm nào dùng để cite.
- Aggarwal & Hartline (2006) — chưa fetch trực tiếp, chỉ biết qua trích dẫn trong
  Kempe-Salek-Moore. Cần tìm bản gốc SODA 2006 để xác nhận Definition 5.2 đúng là
  composability như mô tả.

Việc: tìm và fetch từng bản gốc, xác nhận title/venue/year/trang, sửa lại
"References to verify before use" trong file tex thành reference đã xác nhận.

---

## 6. Sau khi xong mục 1–3 (bắt buộc)

- Nếu tất cả pass: file `T4_Local_Pruning_Frontier.tex`/`.pdf` sẵn sàng đưa thầy, kèm
  bảng kết quả điền ở mục 1–3 làm phụ lục audit (không cần đưa thầy code, chỉ cần bảng
  số + câu "đã kiểm chứng bằng cách tính margin theo phương pháp khác (grid brute-force)
  và cho kết quả giống hệt, đã chạy trên môi trường thesis thật với instance RQ1").
- Nếu mục 1 hoặc 3 fail: **không đưa thầy**, báo lại — đây có thể là bug thật trong chứng
  minh hoặc trong code, cần xác định trước khi tiếp tục.
- Nếu mục 2 cho tỉ lệ cắt quá thấp (ví dụ dưới 10%) trên instance RQ1 thật: vẫn đưa thầy
  được (Định lý 4 vẫn đúng), nhưng cần nói rõ trong phần "ý nghĩa thực tế" rằng K\* có
  thể không mạnh trên chính distribution RQ1 dùng — đây là phát hiện thật, không phải
  thất bại của chứng minh.