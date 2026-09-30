# Min-Max Bound Pruning — Cross-Driver Alternative Covering

> Động cơ: activation_rate 0.42-1.54% (Report Activation Rate) cho thấy cơ hội pruning lớn,
> nhưng 2 điều kiện cục bộ (hull riêng driver, hull toàn cục) đã REJECTED vì chúng bỏ qua
> cạnh tranh LIÊN DRIVER (route sống vì rẻ hơn TỔNG chi phí tách order ra driver khác, không
> phải vì rẻ trong pool riêng của chính nó). Điều kiện này nhắm thẳng vào đúng cơ chế đó.

**Nhãn:** `[LOCK]` = cố định; `[IMPLEMENT]` = cần code; `[CHECK]` `[STOP]` = gate bắt buộc,
không được bỏ qua hay "sửa nhẹ" cho pass.

---

## 0. Điều kiện — phát biểu chính xác

Với route `r` của driver `i`, phục vụ bundle `S`:

```
prune(r) := c_ir(b_min) ≥ Alt(S, i; b_max)
```

- `c_ir(b_min) = K_ir + b_min · W_ir` — chi phí của r tại kịch bản CÓ LỢI NHẤT cho nó
  (bid thấp nhất có thể trong range đã khoá).
- `Alt(S, i; b_max)` — chi phí rẻ nhất để phủ đúng tập order `S`, dùng **driver khác `i`**
  (mỗi route ứng viên định giá tại `b_max` — kịch bản BẤT LỢI NHẤT cho đối thủ) hoặc FD,
  KHÔNG dùng driver `i`.

**Vì sao an toàn (necessary condition):** với mọi bid vector `b` thật, `c_ir(b_i) ≥
c_ir(b_min)` và chi phí đối thủ thật `≤` giá trị tại `b_max`. Nếu ngay ở kịch bản lợi nhất
cho r mà vẫn thua kịch bản bất lợi nhất cho đối thủ, thì **không tồn tại** `b` nào khiến r
thắng thật — r có thể bị loại khỏi pool mà không mất route cần thiết nào.

## 1. `[IMPLEMENT]` Tính `Alt(S, i; b_max)`

`|S| ≤ B ≤ 5` nên đây là bài toán nhỏ — brute-force partition, không cần ILP.

```python
from itertools import product

def alt_cost(S, exclude_driver, pool_by_driver, fd_costs, b_max):
    """
    S: frozenset các order cần phủ.
    exclude_driver: driver i đang test (không được dùng trong alternative).
    Trả về chi phí rẻ nhất để phủ TOÀN BỘ S bằng driver khác + FD.
    """
    # Candidate route: mọi route của driver != exclude_driver có bundle LÀ SUBSET của S.
    # (Giới hạn phạm vi: không xét route "dư" (bundle ⊋ S) — đây là lựa chọn ĐƠN GIẢN HOÁ AN
    #  TOÀN, có thể làm Alt bị tính CAO hơn thật (bỏ sót vài phương án rẻ hơn), khiến điều
    #  kiện kém aggressive hơn mức tối đa có thể — nhưng KHÔNG làm mất tính an toàn (không
    #  bao giờ prune nhầm). Ghi rõ scope này khi báo cáo.)
    candidates = []
    for driver, routes in pool_by_driver.items():
        if driver == exclude_driver:
            continue
        for route in routes:
            if route.bundle <= S:  # subset
                cost_at_bmax = route.K + b_max * route.W
                candidates.append((route.bundle, cost_at_bmax))

    best = _min_cost_to_cover(S, candidates, fd_costs)
    return best


def _min_cost_to_cover(S, candidates, fd_costs):
    """
    Brute-force qua các cách partition S thành (subset phủ bởi 1 route) + phần còn lại FD.
    |S|<=5 => it phuong an, khong can toi uu hoa.
    Quy hoach dong tren bitmask cua S la du (2^5=32 trang thai).
    """
    order_list = sorted(S)
    n = len(order_list)
    idx = {o: k for k, o in enumerate(order_list)}
    full_mask = (1 << n) - 1

    # dp[mask] = chi phi re nhat de phu dung tap order tuong ung voi mask
    dp = [float('inf')] * (1 << n)
    dp[0] = 0.0
    cand_masks = []
    for bundle, cost in candidates:
        mask = 0
        valid = True
        for o in bundle:
            if o not in idx:
                valid = False
                break
            mask |= (1 << idx[o])
        if valid:
            cand_masks.append((mask, cost))

    for mask in range(1, 1 << n):
        # phuong an 1: order dau tien con lai trong mask di FD
        first_bit = (mask & -mask)
        first_order = order_list[first_bit.bit_length() - 1]
        dp[mask] = min(dp[mask], dp[mask ^ first_bit] + fd_costs[first_order])
        # phuong an 2: dung 1 candidate route phu 1 submask chua first_bit
        for cmask, cost in cand_masks:
            if (cmask & first_bit) and (cmask & mask) == cmask:  # cmask subset cua mask, chua first_bit
                dp[mask] = min(dp[mask], dp[mask ^ cmask] + cost)

    return dp[full_mask]
```

`[IMPLEMENT]` Tích hợp vào Algorithm A: sau khi sinh xong toàn bộ pool (không đổi logic sinh
route), thêm bước post-filter: với mỗi route, tính `alt_cost`, áp `prune()`, loại route thoả
điều kiện.

## 2. `[CHECK]` `[STOP]` Bước 1 — Audit trên ground truth ĐÃ CÓ (bắt buộc trước mọi thứ khác)

Dùng lại chính 5 instance + `activated_real` đã có từ Report Activation Rate — **không cần
chạy lại WDP hay LHS sampling**, chỉ cần route pool + danh sách `activated_real` đã lưu.

```python
def audit_against_ground_truth(pool_by_driver, fd_costs, activated_real, b_min, b_max):
    violations = []
    for driver, routes in pool_by_driver.items():
        for route in routes:
            alt = alt_cost(route.bundle, driver, pool_by_driver, fd_costs, b_max)
            c_bmin = route.K + b_min * route.W
            would_prune = (c_bmin >= alt)
            if would_prune and route.id in activated_real:
                violations.append((route.id, driver, route.bundle, c_bmin, alt))
    return violations
```

**Điều kiện PASS: `len(violations) == 0` trên cả 5 instance.** Nếu FAIL dù chỉ 1 route —
dừng ngay, không tiếp tục các bước sau, quay lại rà lại logic `alt_cost` (khả năng cao: bỏ
sót một loại candidate, ví dụ route "dư" bị loại ở §1 lại chính là phương án rẻ nhất thật).

Đây là bước rẻ nhất (không cần CPLEX, không cần sample bid vector mới) nên làm TRƯỚC TIÊN —
nếu fail ở đây, tiết kiệm được toàn bộ công sức Gate n≤6 + đo prune rate phía sau.

## 3. `[CHECK]` `[STOP]` Bước 2 — Gate n≤6, brute-force

Chỉ chạy nếu Bước 1 PASS.

```
Grid: n∈{3,4,5,6} × B∈{2,3} × n_drivers∈{2,3,4} × tw∈{60,120} × seed∈{0,1,2}
Với mỗi instance: sinh route pool đầy đủ (brute-force, dùng lại oracle đã audit độc lập từ
Gate 0/616/160), áp prune(), so route CÒN LẠI sau prune với activated_real tính bằng CÁCH
KHÁC: quét ĐẦY ĐỦ (không LHS) mọi tổ hợp bid trên một lưới mịn (ví dụ 20 điểm/chiều thay vì
sample) — ở n≤6 đủ nhỏ để quét vét cạn khả thi.
```

**Điều kiện PASS: 0 vi phạm** — mọi route thật activate (theo quét vét cạn) đều KHÔNG bị
prune. Log riêng: bao nhiêu route bị prune đúng (không activate + bị prune) — đây là tín
hiệu sớm cho hiệu quả, nhưng không phải kết luận cuối (n≤6 quá nhỏ để đại diện).

## 4. Bước 3 — Đo prune rate thật, chỉ khi Bước 1+2 đều PASS

Mở rộng ra ngoài 5 instance gốc — dùng đúng grid quy mô đã dùng ở RQ1 (n∈{10,15,20},
supply ratio đã khoá) để có con số đại diện, không chỉ 5 điểm rời rạc:

```python
prune_rate = n_pruned / pool_size_original
```

Báo cáo theo từng (n, supply ratio) — giống format đã dùng ở mọi báo cáo trước, không gộp
thành 1 con số trung bình duy nhất che mất phân phối.

## 5. Interpretation

| Bước 1 | Bước 2 | Prune rate (Bước 3) | Quyết định |
|---|---|---|---|
| FAIL | (không chạy) | — | Dừng, sửa lại `alt_cost`, không tiếp tục |
| PASS | FAIL | — | Dừng, rà lại — có thể do sai khác giữa "quét vét cạn" và "LHS sample" ở Bước 1, cần hiểu tại sao trước khi tiếp tục |
| PASS | PASS | ≥ 30-50% | Đáng tích hợp vào Algorithm A chính thức — đo thêm ảnh hưởng runtime thật (giống Test B đã làm cho convex hull) |
| PASS | PASS | < 10-15% | An toàn nhưng không đủ mạnh để đáng công sửa production code — ghi nhận như một correctness result phụ, không implement |

## 6. Việc PHẢI làm khác — không lặp lại lỗi 2 lần trước

- **Không báo cáo prune rate trước khi Bước 1+2 đều PASS** — thứ tự này bắt buộc, đảo ngược
  thứ tự (đo hiệu quả trước, audit sau) đã là cách làm sai ở 2 lần trước.
- Nếu Bước 1 FAIL, ghi lại CHÍNH XÁC route nào vi phạm + tại sao (giống cách phân tích
  `gw0_r14` đã làm ở report activation rate §5.3) — đừng chỉ báo "fail", báo cơ chế cụ thể.
- Giữ nguyên quy mô 5 instance gốc cho Bước 1 để so sánh trực tiếp — không đổi instance khi
  audit.

## 7. Điểm dừng nếu hướng này cũng thất bại

Đây là hướng pruning cross-driver ĐẦU TIÊN được thử (khác hẳn 6+2 hướng trước, vốn đều là
trong-1-driver hoặc trong-1-bundle). Nếu nó cũng thất bại ở Bước 1 (không sửa được sau 1-2
lần thử) hoặc cho prune rate quá thấp ở Bước 3 — dừng hẳn nhánh "tìm pruning rule mới cho
Algorithm A", quay lại hoàn toàn với: (a) viết Proposition/Lemma đã có vào luận văn, (b)
tightness construction (nếu còn thời gian), (c) formalize phát hiện phụ RQ1 (OD-first vs
GW-first). Không mở thêm biến thể thứ 3 của hướng cross-driver — 2 lần thử đã đủ để đánh giá
độ khó của bài toán con này.