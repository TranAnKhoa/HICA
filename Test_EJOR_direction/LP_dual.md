# LP-Dual Reduced-Cost Fixing — Global Relaxation, Not Local Proxy

> Khác về BẢN CHẤT với 3 hướng đã REJECTED (hull trong-driver, hull toàn cục, min-max
> cross-driver): những hướng đó đều XẤP XỈ sự cạnh tranh toàn cục bằng một mô hình đơn giản
> hoá (và đều sai vì bỏ sót ràng buộc "mỗi driver chỉ 1 route"). LP relaxation KHÔNG xấp xỉ
> — nó giải đúng bài toán toàn cục thật (mọi driver, mọi ràng buộc covering, cùng lúc), chỉ
> nới biến 0/1 thành [0,1]. Dual price tự động gộp hết tương tác giữa driver, không cần mô
> hình hoá tay.
>
> **Rủi ro RIÊNG của hướng này (khác 3 lần trước, không phải cùng lỗi lặp lại):** để rẻ, ta
> chỉ muốn kiểm 1 điểm biên của dải bid rồi suy ra an toàn cho toàn dải — dựa trên giả định
> "dual price chỉ tăng khi đối thủ đắt hơn". Giả định này CHƯA ĐƯỢC KIỂM CHỨNG trong đúng
> cấu trúc bài toán này. File này có bước kiểm riêng cho giả định đó TRƯỚC KHI tin shortcut.

**Nhãn:** `[LOCK]` `[IMPLEMENT]` `[CHECK]` `[STOP]` — như các file trước.

---

## 0. Điều kiện — phát biểu

Với route `r` của driver `i`, bundle `S`, tại một bid vector cụ thể `b`:

```
LP-relax(b): min Σ c_ir(b_i)·x_ir + Σ q_o·z_o    (x,z ∈ [0,1], ràng buộc y hệt Algorithm B)
```

Gọi `π_o(b)` là dual price của ràng buộc covering order `o` tại nghiệm LP tối ưu. Reduced
cost của route `r`:

```
rc_ir(b) = c_ir(b_i) − Σ_{o∈S} π_o(b)
```

**Điều kiện đủ để prune (tại MỘT bid `b` cụ thể):** nếu tồn tại một nghiệm nguyên khả thi
đã biết với giá trị `U` (ví dụ: dùng toàn FD, hoặc bất kỳ heuristic nhanh nào), và
`Z_LP(b) + rc_ir(b) > U`, thì `x_ir=1` không thể nằm trong bất kỳ lời giải nguyên tối ưu nào
tại bid `b` đó — đây là kỹ thuật "reduced-cost fixing" chuẩn trong MIP branch-and-bound, hợp
lệ vô điều kiện tại bid cố định.

**Điều kiện đề xuất để prune AN TOÀN CHO TOÀN DẢI** (chưa chứng minh — xem §1):
```
b* = (b_i = θ_min,  b_j = θ_max với mọi j≠i)   — điểm lợi nhất có thể cho r trong dải
prune(r) := rc_ir(b*) > 0   (dùng U = Z_LP(b*) chính nó làm cận, tức kiểm reduced cost dương)
```

## 1. `[CHECK]` `[STOP]` Bước 0 — Kiểm giả định đơn điệu TRƯỚC KHI tin shortcut

Đây là bước MỚI, không có ở 3 file trước, vì đây là rủi ro RIÊNG của hướng này.

**Giả định cần kiểm:** `rc_ir(b)` đạt giá trị NHỎ NHẤT (khó prune nhất) tại đúng `b*` — tức
với mọi `b` khác trong dải, `rc_ir(b) ≥ rc_ir(b*)`.

```python
def check_monotonicity_assumption(instance, route, n_grid_points=20):
    """
    Quét lưới thô trên dai bid (khong can day du parametric), so rc_ir tai b*
    voi rc_ir tai cac diem khac trong dai — tim phan vi du neu co.
    """
    i, S = route.driver, route.bundle
    b_star = {i: THETA_MIN, **{j: THETA_MAX for j in all_drivers if j != i}}
    rc_at_star = compute_reduced_cost(instance, route, b_star)

    violations = []
    # Quet luoi thua tren cac chieu khac (khong can day du, du de phat hien vi pham)
    for b_test in sample_grid_points(all_drivers, THETA_MIN, THETA_MAX, n_grid_points):
        rc_test = compute_reduced_cost(instance, route, b_test)
        if rc_test < rc_at_star - 1e-6:
            violations.append((b_test, rc_test, rc_at_star))
    return violations
```

Chạy trên vài chục route (ưu tiên route GẦN biên prune — `rc_ir(b*)` gần 0, vì đây là chỗ
vi phạm (nếu có) dễ đổi kết luận prune/không-prune nhất) trên 3-5 instance.

**`[STOP]` Điều kiện bắt buộc trước khi dùng shortcut:** `0 violations`. Nếu có vi phạm dù
chỉ 1 — **không dùng shortcut 1-điểm**, chuyển sang phương án dự phòng ở §4 (đắt hơn nhưng
an toàn chắc chắn: kiểm nhiều điểm hoặc parametric LP đầy đủ).

## 2. `[CHECK]` `[STOP]` Bước 1 — Audit trên ground truth đã có (giống mọi lần trước)

Chỉ chạy nếu Bước 0 (§1) pass.

```python
def audit_lp_dual_pruning(pool_by_driver, fd_costs, activated_real, theta_min, theta_max):
    violations = []
    for driver, routes in pool_by_driver.items():
        for route in routes:
            b_star = {driver: theta_min, **{j: theta_max for j in pool_by_driver if j != driver}}
            rc = compute_reduced_cost_via_lp(pool_by_driver, fd_costs, route, b_star)
            would_prune = (rc > 1e-9)
            if would_prune and route.id in activated_real:
                violations.append((route.id, driver, route.bundle, rc))
    return violations
```

Dùng lại đúng 5 instance + `activated_real` từ Report Activation Rate — không cần chạy WDP
mới, chỉ cần giải thêm LP relaxation (rẻ hơn hẳn giải nguyên, và chỉ cần 1 lần/route thay vì
1000 lần bid vector).

**Điều kiện PASS: 0 vi phạm trên cả 5 instance.** Nếu fail, ghi lại route cụ thể + `rc` của
nó + truy nguyên bằng cách giải WDP thật tại đúng `b*` (giống cách đã làm ở Min-Max Bound
§6.3) — không chỉ báo "fail".

## 3. Bước 2 — Gate n≤6 + đo prune rate (chỉ nếu Bước 0+1 PASS)

Giống cấu trúc mọi file trước — brute-force so sánh ở n≤6, rồi đo prune rate thật trên grid
n∈{10,15,20} đã dùng ở RQ1.

## 4. Phương án dự phòng — nếu Bước 0 fail

Không bỏ hẳn hướng LP-dual chỉ vì shortcut 1-điểm fail — thử bản đắt hơn nhưng chắc chắn an
toàn: kiểm reduced cost tại **mọi đỉnh** của hộp `[θ_min,θ_max]^m` mà route `r` có thể liên
quan (thực ra chỉ cần 2 đỉnh: `b*` và đỉnh đối lập, vì reduced cost của `r` chỉ phụ thuộc
trực tiếp vào `b_i` của chính driver `i`, còn ảnh hưởng của driver khác đi qua dual — nếu
giả định đơn điệu SAI, cần parametric LP thật (theo dõi vùng bid mà basis tối ưu không đổi)
— đắt hơn hẳn, chỉ làm nếu §1 cho thấy vi phạm phổ biến, không phải hiếm).

## 5. Interpretation

| Bước 0 | Bước 1 | Prune rate | Quyết định |
|---|---|---|---|
| FAIL | — | — | Chuyển §4 (đắt hơn), không kết luận hướng LP-dual chết chỉ vì shortcut chết |
| PASS | FAIL | — | Dừng, truy nguyên cơ chế cụ thể (giống Min-Max §6.3), đừng sửa nhẹ cho pass |
| PASS | PASS | Cao (so activation_rate đã biết ~1-2%, kỳ vọng prune rate gần 98-99% nếu đúng) | Đo ảnh hưởng runtime thật trước khi implement (bài học Test A vs Test B — prune pool không tự động nghĩa DP nhanh hơn) |
| PASS | PASS | Thấp | Ghi nhận correctness result, không implement |

## 6. Nhắc lại — không phải hướng cuối cùng duy nhất

Song song/độc lập với file này: **compact arc-based MILP** (đề xuất từ đầu, chưa từng test)
vẫn là một hướng mở, khác loại hoàn toàn (né enumeration thay vì lọc nó). Không nên coi thất
bại hay thành công của LP-dual là kết luận cuối cho toàn bộ câu hỏi "còn cách nào tăng tốc
Algorithm A không".