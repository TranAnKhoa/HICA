# ConvexHull Dominance Test — Quick Spec

> Mục đích: đo xem filtering Pareto points không nằm trên convex hull có cắt được bao nhiêu % frontier ở hot cell không, trước khi commit thời gian vào implement đúng trong Algorithm A.
> 
> Thực tế: chạy DP như bây giờ (không đổi), để nó output hết mọi label cuối cùng. Rồi post-process: tính convex hull của toàn bộ (K,W) điểm, loại điểm nằm trong, đo kết quả.

---

## 1. Input & Setup

**Hot cell (nơi cần cải thiện nhất):**
```
n = 20
B_gw = 4  (open-route bundle cap)
tw = 240  (time window width, phút)
n_drivers = 5 (chọn nhỏ để runtime quay lại)
```

**Instance:** 1 trong những instance đã chạy ở cell này từ trước (nếu có), hoặc sinh mới với seed cố định (không random).

**Output từ Algorithm A hiện tại (lấy sẵn):**
- File: `route_pool_manifest.json` — danh sách tất cả route
- File: `route_details.csv` — mỗi hàng 1 route: [route_id, driver, bundle_orders, K_ir, W_ir]
- Chỉ cần lọc hàng của GW (driver lớp GW) và bundle size ≤ B_gw = 4

## 2. Post-process: Convex Hull Dominance

```python
import numpy as np
from scipy.spatial import ConvexHull
import pandas as pd

# Load routes
routes_gw = pd.read_csv('route_details.csv')
routes_gw = routes_gw[routes_gw['driver_class'] == 'GW']
routes_gw = routes_gw[routes_gw['bundle_size'] <= 4]

# Extract (K, W) points
points = routes_gw[['K_ir', 'W_ir']].values  # shape: (N, 2)

print(f"Total Pareto points (before hull filtering): {len(points)}")

# Compute convex hull
try:
    hull = ConvexHull(points)
    hull_indices = hull.vertices  # indices of points on hull
    
    print(f"Points on convex hull: {len(hull_indices)}")
    print(f"Points INSIDE hull (can be pruned safely): {len(points) - len(hull_indices)}")
    print(f"Reduction: {100 * (len(points) - len(hull_indices)) / len(points):.1f}%")
    
    # Output hull points for manual check
    hull_points = points[hull_indices]
    print("\nConvex hull points (K, W):")
    for idx in sorted(hull_indices):
        print(f"  Route {routes_gw.iloc[idx]['route_id']}: "
              f"K={points[idx,0]:.1f}, W={points[idx,1]:.3f}")
    
except Exception as e:
    print(f"Hull computation failed: {e}")
    print("(This is expected if all points are collinear or there are < 3 points)")
```

## 3. Audit: Verify Hull = Set Needed by Linear Scalarization

Với mọi bid b_i trong range [θ_min, θ_max]:
- Tính `cost(b) = K + b·W` cho từng point
- Tìm min cost
- Xác nhận min cost luôn đạt trên hull, không bao giờ nằm strictly inside

```python
# Quick audit: random sample từ [18, 25] $/hr
np.random.seed(42)
bid_samples = np.random.uniform(18, 25, size=100)

for b in bid_samples:
    costs = points[:, 0] + b * points[:, 1]
    min_cost_idx = np.argmin(costs)
    
    # Check if this index is on hull
    is_on_hull = min_cost_idx in hull_indices
    
    if not is_on_hull:
        print(f"WARNING: bid b={b:.1f} selects non-hull point! "
              f"Index {min_cost_idx}, cost={costs[min_cost_idx]:.2f}")
        print(f"  This should NEVER happen if hull is computed correctly.")
        print(f"  Possible causes: numerical precision, degenerate case")

print(f"\nAudit complete: {sum(1 for b in bid_samples if np.argmin(points[:, 0] + b * points[:, 1]) in hull_indices)}/100 bids select hull points")
```

## 4. Interpretation Guide

| Scenario | Interpretation | Next Step |
|---|---|---|
| Reduction **≥ 50%** | Hull filtering rất mạnh trên cell này — đáng implement vào Algorithm A | Commit vào implement + audit trên tất cả hot cell khác (n=15,20,30 hoặc B_gw=3,4,5) |
| Reduction **20-50%** | Tạm tốt, dẩm cay — phụ thuộc thời gian, implement nếu còn slot | Đo thêm hot cell khác để kiểm xem consistent không, rồi quyết định |
| Reduction **< 20%** | Không đáng công, frontier quá "dày" (gần như toàn bộ trên hull) | Dừng lại, dùng convex-hull kết quả này để **thiết kế instance worst-case cho lower-bound T4**: ý muốn một instance sao cho **mọi Pareto point đều nằm trên hull** → hướng gốc (thử convex hull) cũng sẽ bất lực, làm lower-bound chặt hơn |

## 5. Script để chạy

```bash
# Chạy Algorithm A hiện tại trên hot cell
python t6_dp.py \
  --instance-file instances/hot_cell_n20_B4_tw240.json \
  --output-manifest route_pool_manifest.json \
  --output-details route_details.csv

# Post-process convex hull
python convex_hull_test.py < route_details.csv
```

**File `convex_hull_test.py`:** paste code ở mục 2-3 vào đây, chạy trực tiếp.

---

## 6. Time Budget

- Setup + run Algorithm A: **phụ thuộc scale cell, ước 30 min - 2 giờ cho n=20**
- Convex hull compute + audit: **< 5 phút**
- Interpretation + decision: **15 phút**

**Tổng: 1-3 giờ, tùy instance đã có hay sinh mới.**

---

## 7. Gate: Khi nào bỏ thí nghiệm này

Nếu trong quá trình chạy Algorithm A:
- Frontier size quá lớn (> 10 triệu label) → timeout, chỉ lấy partial result, ghi note
- Hull compute fail (numerical): OK, ghi note "degenerate/collinear", nhưng vẫn báo partial reduction nếu có

Không bỏ chỉ vì output chưa "đẹp" — dù partial, nó vẫn có thông tin.