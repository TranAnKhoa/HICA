# T4 Diagnostic Experiment — Đo hiệu quả cắt nhánh của cận dưới hình học

**Mục tiêu:** Trả lời MỘT câu hỏi duy nhất — *cận dưới MST cắt được bao nhiêu % subset
trước khi phải chạy DFS?* — để quyết định có đáng đầu tư vào T4 (cận chặt hơn) hay không.

**KHÔNG phải mục tiêu:** không xây Algorithm B, không xây payment, không tối ưu hoá,
không sinh route pool để dùng thật. Đây là **thí nghiệm chẩn đoán**, chạy xong vứt đi cũng được.

**Thời lượng kỳ vọng:** 1 buổi. Nếu quá nửa ngày, dừng lại và báo — có gì đó sai scope.

---

## 0. Quyết định sẽ được đưa ra từ kết quả

| Tỷ lệ subset bị MST cắt | Kết luận | Hành động |
|---|---|---|
| > 70% | MST đã đủ tốt | Bỏ T4, dồn sức sang T5 (component decomposition) |
| 30–70% | Còn dư địa cải thiện | Đầu tư tìm cận chặt hơn (T4 đáng theo đuổi) |
| < 30% | Cận hình học vô dụng với dữ liệu này | Đổi hướng hoàn toàn |

Đây là lý do duy nhất của thí nghiệm. Mọi thứ không phục vụ bảng này đều là scope creep.

---

## 1. Sinh instance

### 1.1 Tham số

```
n_orders     ∈ {10, 15, 20, 30}
n_drivers    = max(3, n_orders // 4)
B (bundle cap) = 3
seeds        = 20 seed mỗi cấu hình (tổng 4 × 20 = 80 instance)
map          = vuông 20 × 20 km, toạ độ Euclidean
speed        = 20 km/h  →  time = distance × 3 (phút/km)
service time = 0 (đơn giản hoá, không ảnh hưởng kết luận)
```

### 1.2 Cách sinh

```
Với mỗi order o:
    pickup(o)   ~ Uniform trên map
    delivery(o) ~ Uniform trên map
    release(o)  ~ Uniform[0, 60] phút
    deadline(o) = release(o) + direct_time(pickup, delivery) + slack
                  với slack ~ Uniform[TW_MIN, TW_MAX]

Với mỗi driver i (chỉ sinh GW, KHÔNG cần OD cho thí nghiệm này):
    start(i)        ~ Uniform trên map
    capacity(i)     = 2
    available_from  = 0
    available_until = 240 phút
```

### 1.3 ⚠️ TW_MIN / TW_MAX — quét grid, KHÔNG chọn một giá trị

Đây là tham số **quyết định toàn bộ kết quả**, và là chỗ dễ tự lừa mình nhất.
Time window lỏng → MST không cắt được gì. Time window chặt → MST cắt gần hết.

**BẮT BUỘC:** chạy toàn bộ grid dưới đây, báo cáo **cả ba**, không được chọn một
cấu hình rồi báo cáo mỗi cấu hình đó.

```
TIGHT:  slack ~ Uniform[10, 30]  phút
MEDIUM: slack ~ Uniform[30, 60]  phút
LOOSE:  slack ~ Uniform[60, 120] phút
```

Tổng: 4 (n) × 3 (TW) × 20 (seed) = **240 instance**.

---

## 2. Thuật toán cần implement

### 2.1 Feasibility check (ground truth) — DFS đầy đủ

```
def is_feasible(driver, subset_S) -> bool:
    # Duyệt MỌI thứ tự pickup-delivery hợp lệ:
    #   - pickup(o) phải trước delivery(o) với mọi o in S
    #   - load sau mỗi event phải trong [0, capacity]
    #   - arrival tại mỗi node phải <= deadline của node đó
    #     (đến sớm thì chờ, được phép)
    #   - route phải xong trước available_until
    # Trả True ngay khi tìm thấy MỘT thứ tự khả thi (không cần duyệt hết)
    # Trả False nếu duyệt hết mà không thứ tự nào khả thi
```

Số thứ tự cần duyệt: (2k)!/2^k với k = |S|. Với B=3 tối đa 90 thứ tự → rẻ, không cần
tối ưu.

**Yêu cầu:** đây là ground truth, phải ĐÚNG TUYỆT ĐỐI. Viết unit test riêng.

### 2.2 Cận dưới MST

```
def mst_bound(driver, subset_S) -> float:
    nodes = [driver.start] + [pickup(o), delivery(o) for o in subset_S]
    # Đồ thị đầy đủ, trọng số = travel time giữa 2 node
    # Chạy Kruskal (hoặc Prim), trả tổng trọng số cây khung nhỏ nhất
    return total_weight
```

### 2.3 Cận dưới 1-tree (biến thể chặt hơn, cũng đo luôn)

```
def one_tree_bound(driver, subset_S) -> float:
    nodes_no_v = [pickup(o), delivery(o) for o in subset_S]
    mst_part   = MST(nodes_no_v)
    cheapest_from_v = min(travel_time(driver.start, u) for u in nodes_no_v)
    return mst_part + cheapest_from_v
```

### 2.4 Luật cắt

```
budget(S) = max(deadline(o) for o in S)      # LƯU Ý: max, KHÔNG phải min
                                              # dùng min sẽ cắt nhầm bundle khả thi

prune_mst(S)     = mst_bound(S)      > budget(S)
prune_1tree(S)   = one_tree_bound(S) > budget(S)
```

### 2.5 ⚠️ Kiểm tra soundness — GATE BẮT BUỘC

```
Với MỌI (driver, subset) đã xét:
    assert NOT (prune_mst(S) AND is_feasible(S))
    assert NOT (prune_1tree(S) AND is_feasible(S))
```

Nếu assertion này fail dù chỉ MỘT lần → cận không sound → **DỪNG NGAY**, báo lại,
không chạy tiếp. Đây là lỗi nghiêm trọng nhất có thể xảy ra (nó sẽ phá DSIC trong
hệ thống thật).

---

## 3. Quy trình đo

Với mỗi instance, mỗi driver:

```
1. Lọc size-1 (bước 0):
   Với mỗi order o, kiểm is_feasible(driver, {o}).
   survivors_1 = các order pass.

2. Sinh subset size 2 từ survivors_1, size 3 từ subset size-2 đã pass.
   (Chỉ mở rộng từ subset đã sống sót — đúng nguyên tắc đơn điệu.)

3. Với MỖI subset S sinh ra ở size >= 2, ghi lại:
   - k = |S|
   - mst_bound(S), one_tree_bound(S), budget(S)
   - prune_mst(S), prune_1tree(S)          (bool)
   - is_feasible(S)                         (ground truth, luôn tính để đo)
   - thời gian chạy DFS (giây)
   - thời gian chạy MST (giây)
```

**Lưu ý quan trọng:** ở thí nghiệm này, LUÔN chạy DFS cho mọi subset kể cả subset đã
bị cận cắt — vì cần ground truth để đo. Trong hệ thống thật thì không làm vậy.

---

## 4. Metric phải báo cáo

Cắt theo từng nhóm (n_orders × TW_setting × k), và tổng hợp:

```
prune_rate_mst     = (# subset bị MST cắt) / (# subset đã xét)
prune_rate_1tree   = (# subset bị 1-tree cắt) / (# subset đã xét)

infeasible_rate    = (# subset thật sự infeasible) / (# subset đã xét)

# ĐÂY LÀ METRIC QUAN TRỌNG NHẤT:
recall_mst     = (# subset infeasible BỊ MST cắt) / (# subset infeasible)
recall_1tree   = (# subset infeasible BỊ 1-tree cắt) / (# subset infeasible)
   → "trong số các bundle thật sự chết, cận bắt được bao nhiêu %"
   → recall thấp = cận lỏng, còn nhiều dư địa cho T4

improvement_1tree_over_mst = recall_1tree - recall_mst
   → 1-tree chặt hơn MST bao nhiêu, tính bằng điểm phần trăm

# Tiết kiệm thời gian ước tính:
time_saved = (# subset bị cắt) × avg_DFS_time - (# subset đã xét) × avg_MST_time
```

Báo cáo dạng bảng, kèm median + IQR qua 20 seed. Không báo mỗi giá trị trung bình.

---

## 5. Output cần có

1. **Bảng chính:** prune_rate và recall theo (n_orders × TW_setting), cho cả MST và 1-tree.
2. **Bảng phụ:** phân rã theo k (=2 vs =3) — cận có yếu đi khi bundle lớn hơn không?
3. **File CSV thô** để phân tích thêm.
4. **Xác nhận soundness gate đã pass** (không có assertion nào fail).
5. **Một đoạn văn ngắn** trả lời trực tiếp: recall_mst rơi vào khoảng nào,
   1-tree cải thiện được bao nhiêu, và theo bảng ở §0 thì kết luận là gì.

---

## 6. Những điều KHÔNG được làm

- **Không** tinh chỉnh TW_MIN/TW_MAX sau khi thấy kết quả. Grid đã khoá ở §1.3.
  (Đây là lỗi đã xảy ra 2 lần trong dự án này với time window và release spread —
  không được lần thứ 3.)
- **Không** thêm cận mới (sector, precedence...) trong lần chạy này. Chỉ MST và 1-tree.
- **Không** implement OD (occasional driver). Chỉ GW — vì T4 là về open-route không anchor.
- **Không** tối ưu hoá code cho tới khi có kết quả. Chạy chậm nhưng đúng > chạy nhanh nhưng sai.
- **Không** dùng bid/giá ở bất kỳ đâu. Thí nghiệm này hoàn toàn không có khái niệm giá.

---

## 7. Ghi chú kỹ thuật

- Dùng Python thuần + numpy là đủ. Không cần solver (Gurobi/CPLEX) cho thí nghiệm này.
- MST: `scipy.sparse.csgraph.minimum_spanning_tree` hoặc tự viết Kruskal (~20 dòng).
- Set seed rõ ràng, log lại, để tái lập được.
- Nếu instance nào chạy > 60 giây, log lại và bỏ qua — đừng để một instance làm treo cả run.