# ConvexHull Dominance Test v2 — Scope-Corrected + Safety Gate

> Sửa lỗi của v1: hull v1 tính trên TOÀN BỘ pool (mọi driver, mọi bundle gộp chung) — sai,
> vì dominance chỉ sound trong CÙNG (driver, bundle) theo đúng §7.4 đề cương. Route phục vụ
> bundle khác nhau không phải lựa chọn thay thế cho nhau trong WDP (mandatory fulfillment).
> File này KHÔNG dùng lại số 99.99% của v1 — con số đó không đáng tin, tính sai scope.

**Nhãn:** `[LOCK]` = cố định; `[IMPLEMENT]` = cần code; `[CHECK]` = gate bắt buộc pass;
`[STOP]` = điều kiện dừng, không được bỏ qua.

---

## 0. Bài học từ v1 — đọc trước khi code

Audit của v1 (100/100 bid chọn điểm trên hull) **không sai** — nó chỉ xác nhận thuật toán
hull được code đúng theo định nghĩa toán học của nó. Nó **không** xác nhận việc dùng hull
đó để prune có an toàn cho WDP. Hai câu hỏi khác nhau:
- "Điểm này có phải argmin của `K+bW` trên tập đã cho không?" → v1 đã trả lời đúng.
- "Có được phép xoá điểm không nằm trên hull đó khỏi route pool không?" → v1 CHƯA trả lời,
  và câu trả lời phụ thuộc scope: chỉ đúng khi hull tính trong cùng (driver, bundle).

## 1. Test A — Regroup đúng scope (dùng lại data DP đã có, không cần chạy lại)

`[IMPLEMENT]`

```python
from collections import defaultdict
import csv

def load_routes(path):
    routes = []
    with open(path) as f:
        for row in csv.DictReader(f):
            if row['driver_class'] != 'GW':
                continue
            if int(row['bundle_size']) > 4:
                continue
            routes.append({
                'route_id': row['route_id'],
                'driver': row['driver'],
                'bundle': tuple(sorted(row['bundle_orders'].split(';'))),  # chỉnh theo format thật
                'K': float(row['K_ir']),
                'W': float(row['W_ir']),
            })
    return routes


def pareto_filter(points):
    """points: list of (K, W, payload). Giữ điểm không bị dominate cả 2 trục."""
    pts = sorted(points, key=lambda p: (p[0], p[1]))
    result = []
    best_w = float('inf')
    for k, w, payload in pts:
        if w < best_w:
            result.append((k, w, payload))
            best_w = w
    return result


def lower_hull_on_pareto(pareto_pts):
    """pareto_pts đã sort K tăng dần, W giảm dần (đơn điệu) — Andrew's monotone chain 1 lần quét."""
    if len(pareto_pts) <= 2:
        return pareto_pts
    hull = []
    for p in pareto_pts:
        while len(hull) >= 2 and not turns_right(hull[-2], hull[-1], p):
            hull.pop()
        hull.append(p)
    return hull


def turns_right(a, b, c):
    # cross product (b-a) x (c-a) < 0 => turn right (giữ lower hull cho minimize K,W)
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]) < 0


def test_a_regroup(routes):
    groups = defaultdict(list)
    for r in routes:
        key = (r['driver'], r['bundle'])   # ĐÚNG SCOPE — cùng driver, cùng tập order
        groups[key].append((r['K'], r['W'], r['route_id']))

    total_before = sum(len(v) for v in groups.values())
    total_after = 0
    per_group_reduction = []

    for key, pts in groups.items():
        pareto_pts = pareto_filter(pts)
        hull_pts = lower_hull_on_pareto(pareto_pts)
        total_after += len(hull_pts)
        if len(pts) > 1:
            per_group_reduction.append(
                (key, len(pts), len(hull_pts), 100*(len(pts)-len(hull_pts))/len(pts))
            )

    print(f"Tổng điểm trước: {total_before}")
    print(f"Tổng điểm sau (đúng scope, chỉ trong cùng driver+bundle): {total_after}")
    print(f"Reduction TOÀN BÀI: {100*(total_before-total_after)/total_before:.1f}%")
    print(f"\nSố (driver,bundle) group có >1 route: {len(per_group_reduction)}")
    if per_group_reduction:
        avg_group_reduction = sum(r[3] for r in per_group_reduction)/len(per_group_reduction)
        print(f"Reduction trung bình MỖI group (chỉ tính group có >1 điểm): {avg_group_reduction:.1f}%")
        # In vài group tiêu biểu để soi bằng mắt
        for key, n_before, n_after, red in sorted(per_group_reduction, key=lambda x: -x[1])[:10]:
            print(f"  {key}: {n_before} -> {n_after} ({red:.1f}%)")

    return total_before, total_after


if __name__ == '__main__':
    routes = load_routes('route_details.csv')
    test_a_regroup(routes)
```

**Kỳ vọng thực tế (không phải v1's 99.99%):** phần lớn (driver, bundle) group, nhất là
bundle_size lớn (3-4), rất có thể chỉ còn 1-vài sequence sống sót sau dominance hiện tại
(§7.4 đã cắt gần hết trong cùng group rồi) — reduction toàn bài **thật sự có thể chỉ vài %
đến vài chục %**. Đừng kỳ vọng lặp lại con số ấn tượng của v1 — con số đó sai vì sai scope,
không phải vì "may mắn".

## 2. `[CHECK]` `[STOP]` — Gate bắt buộc trước khi tin BẤT KỲ con số reduction nào

Đây không phải bước tuỳ chọn. Nếu Test A cho reduction hấp dẫn nhưng gate này fail, KHÔNG
được implement vào Algorithm A — dừng lại, báo cáo fail, không tìm cách "sửa nhẹ" cho pass.

```python
def brute_force_routes(instance, driver):
    """Enumerate TOÀN BỘ route hợp lệ cho driver, không dùng bất kỳ pruning nào."""
    # Dùng lại logic đã có ở n<=6 gate của Algorithm A (§7.5 đề cương) — không viết mới.
    ...


def gate_n6_hull_vs_bruteforce(instance_n6, hull_pruned_pool, driver):
    bf_pool = brute_force_routes(instance_n6, driver)
    bf_by_bundle = defaultdict(list)
    for r in bf_pool:
        bf_by_bundle[r['bundle']].append((r['K'], r['W']))

    hull_by_bundle = defaultdict(list)
    for r in hull_pruned_pool:
        if r['driver'] == driver:
            hull_by_bundle[r['bundle']].append((r['K'], r['W']))

    for bundle, bf_pts in bf_by_bundle.items():
        bf_hull = lower_hull_on_pareto(pareto_filter([(k,w,None) for k,w in bf_pts]))
        pruned_hull = hull_by_bundle.get(bundle, [])

        # Điều kiện PASS: mọi điểm brute-force-hull PHẢI có mặt trong hull đã prune
        for k, w, _ in bf_hull:
            if (k, w) not in [(pk, pw) for pk, pw in pruned_hull]:
                print(f"[FAIL] Bundle {bundle}: brute-force hull point ({k},{w}) "
                      f"bị thiếu trong pruned pool!")
                return False
    print("[PASS] Mọi điểm hull brute-force đều có mặt trong pruned pool, mọi bundle, n<=6.")
    return True
```

**Điều kiện pass thật sự cần kiểm — 3 lớp, không chỉ 1:**

| # | Kiểm gì | Vì sao cần |
|---|---|---|
| `[CHECK]` 1 | Hull tính đúng scope (driver, bundle) — không pool qua bundle khác | Đã sửa ở Test A, đây là lỗi của v1 |
| `[CHECK]` 2 | n≤6: pruned pool khớp brute-force hull, MỌI bundle, MỌI driver | Bắt buộc theo chuẩn §7.5 đã có sẵn trong đề cương cho mọi pruning rule mới |
| `[CHECK]` 3 | Đổi bid bất kỳ (giống gate `allocation_range_hash` §7.5) → route count/signature của pruned pool KHÔNG đổi | Xác nhận rule vẫn bid-independent sau khi thêm — dễ vô tình phá nếu code sai |

## 3. Test B (tuỳ chọn, sau khi Test A + gate pass) — Hull tại DP intermediate state

Đây mới là chỗ đo đúng liệu hull có **thật sự tăng tốc Algorithm A** hay không — Test A chỉ
đo reduction trên route đã hoàn thành (output cuối), không đo được liệu DP có tốn ít label
hơn TRONG LÚC chạy.

`[IMPLEMENT]` (cần sửa `dp_labeling.py`, không phải post-process):
- Tại mỗi state (vị trí hiện tại, tập order đã pickup, tập đã giao) — đúng key mà dominance
  hiện tại đang dùng để so sánh Pareto — thêm bước: sau khi lọc Pareto (đã có), lọc tiếp
  bằng hull trên đúng state đó, trước khi mở rộng sang state kế tiếp.
- Đo: peak frontier size TRƯỚC/SAU khi thêm hull filter tại từng state, trên đúng hot cell
  (n=20, B_gw=4, tw=240) đã dùng ở v1.
- So sánh với 631,024 label (peak frontier hiện tại, đã đo ở v1).

**Chỉ làm bước này nếu Test A + Gate đã pass** — nếu Test A cho reduction thấp, khả năng
cao Test B cũng không đáng đầu tư công sửa DP.

## 4. Interpretation Guide (thay bảng cũ của v1)

| Test A reduction (đúng scope) | Gate n≤6 | Quyết định |
|---|---|---|
| ≥ 20% | PASS | Làm Test B (đo tại DP intermediate state), nếu Test B cũng giảm frontier đáng kể → implement chính thức |
| ≥ 20% | **FAIL** | **KHÔNG implement** — rule sai đâu đó (bug hoặc scope vẫn chưa đúng), sửa lại từ đầu, không patch tạm |
| < 20% | (không cần chạy gate) | Dừng — không đáng công. Dùng số liệu này làm bằng chứng cho hướng lower-bound (instance thực tế đã "dày" ngay cả sau dominance hiện có + hull) |

## 5. Việc cần báo cáo lại (khác v1)

1. Reduction TOÀN BÀI đúng scope (Test A) — con số thật, không phải 99.99%.
2. Phân phối reduction theo từng (driver, bundle) group — group nào cắt được nhiều, group
   nào không cắt được gì (bundle_size=1 chắc chắn không cắt được gì vì chỉ 1 điểm/group).
3. Kết quả gate n≤6 — PASS/FAIL rõ ràng, không diễn giải mềm.
4. Nếu qua được Test A+gate: kết quả Test B (frontier size tại DP, trước/sau).

Không báo cáo lại số reduction toàn-pool kiểu v1 trong bất kỳ bản viết nào của thesis — con
số đó sai và không đại diện cho bất kỳ điều gì hữu ích.