# Test nhanh — 3 việc follow-up sau kết luận Case 2

> Giả định: bạn adapt trực tiếp vào `t6_dp.py` / bản copy `run_dp_instrumented` đã dùng cho
> nghiên cứu Case 1 vs Case 2. Các tên hàm (`_try_pickup`, `_try_delivery`, `_try_home`,
> `_filter_dominated_labels`, `run_dp`) viết theo đúng tên đã xuất hiện trong tài liệu mô tả
> Algorithm A — sửa lại cho khớp signature thật trong code của bạn nếu khác.

---

## Test A — `attempts_per_closure` (đóng dứt điểm câu hỏi (a) vs (b))

**Mục đích:** biết chính xác mỗi label cha, khi bước vào closure (chuỗi delivery/home liên
tiếp trong cùng round), bị thử bao nhiêu thứ tự giao trước khi tất cả chết hoặc có cái sống.
Nếu trung bình ~1 → không có gì để tối ưu (đóng hẳn ý tưởng IV-completion). Nếu cao → còn
dư địa tiết kiệm overhead sinh label.

```python
# --- thêm vào bản instrumented, đặt ở đầu file cùng chỗ khai báo counter cũ ---
from collections import defaultdict

closure_attempts = defaultdict(int)   # key: id(label_cha_khi_vào_closure) -> số lần thử
closure_deaths    = defaultdict(int)  # cùng key -> số lần chết trong closure đó
closure_survivors = defaultdict(int)  # cùng key -> số label sống sót ra khỏi closure đó

def run_closure_instrumented(label, closure_root_id):
    """
    Gọi thay cho vòng lặp closure gốc (delivery/home lặp tới bão hoà).
    closure_root_id = id(label) TẠI THỜI ĐIỂM label vừa được sinh ra bởi pickup gần nhất
    (tức là điểm "vào closure" — set 1 lần trước khi bắt đầu đệ quy/vòng lặp closure).
    """
    stack = [label]
    while stack:
        cur = stack.pop()
        # --- thử delivery cho từng order trong IV ---
        for j in list(cur.IV):
            closure_attempts[closure_root_id] += 1
            child = _try_delivery(cur, j)   # trả None nếu infeasible
            if child is None:
                closure_deaths[closure_root_id] += 1
            else:
                stack.append(child)
        # --- thử home (chỉ OD, IV rỗng) ---
        if not cur.IV and driver_cls == "OD":
            closure_attempts[closure_root_id] += 1
            child = _try_home(cur)
            if child is None:
                closure_deaths[closure_root_id] += 1
            else:
                closure_survivors[closure_root_id] += 1
        elif not cur.IV:  # GW: IV rỗng là đã hoàn chỉnh, không "chết", tính là survivor
            closure_survivors[closure_root_id] += 1

# --- sau khi chạy xong toàn bộ instance, in thống kê ---
def report_closure_stats():
    n = len(closure_attempts)
    if n == 0:
        print("Không có closure nào được ghi nhận — kiểm lại điểm gọi hàm.")
        return
    mean_attempts = sum(closure_attempts.values()) / n
    all_dead_closures = sum(
        1 for k in closure_attempts
        if closure_survivors.get(k, 0) == 0
    )
    max_attempts = max(closure_attempts.values())
    print(f"Số closure quan sát:              {n}")
    print(f"Trung bình attempts/closure:       {mean_attempts:.2f}")
    print(f"Max attempts trong 1 closure:      {max_attempts}")
    print(f"Số closure toàn-bộ-chết (0 survivor): {all_dead_closures} "
          f"({100*all_dead_closures/n:.1f}%)")
    print(f"Attempts trung bình CHỈ trong closure toàn-chết: "
          f"{sum(v for k,v in closure_attempts.items() if closure_survivors.get(k,0)==0) / max(all_dead_closures,1):.2f}")
```

**Cách chạy:** chạy đúng cell nóng nhất đã dùng ở Vòng 2 (n=20, B_gw=4, tw=240, cùng seed),
gọi `report_closure_stats()` ở cuối.

**Cách đọc kết quả:**
- `mean_attempts ≈ 1.0–1.5` → kịch bản (a), đóng hẳn ý tưởng IV-completion, không cần làm gì
  thêm ở hướng này.
- `mean_attempts` cao rõ rệt (ví dụ > 3–4), đặc biệt **trong nhóm closure toàn-chết** → kịch
  bản (b) có thật, đáng thử patch nhỏ ở Test A2 dưới đây.

### Test A2 — patch thử (chỉ code nếu Test A cho tín hiệu (b))

Ý tưởng: ngay sau khi một label vừa pickup xong (trước khi bước vào closure), nếu `|IV|`
đã đạt kích thước sẽ không tăng nữa trong closure này (tức chuẩn bị giao hết), thử trước
**một hoán vị bất kỳ** khả thi của toàn bộ IV bằng cách chạy nhanh (không tạo label con,
chỉ tính toán số học) — nếu **không hoán vị nào** thỏa deadline, bỏ qua toàn bộ closure,
không sinh bất kỳ label con nào.

```python
from itertools import permutations

def iv_completion_feasible(label) -> bool:
    """
    Kiểm tra thuần số học (KHÔNG sinh label con): có tồn tại thứ tự giao |IV| order
    hiện tại sao cho tất cả đều đúng deadline không, xuất phát từ (v=label.v, t=label.t).
    Trả True nếu CÓ ÍT NHẤT MỘT thứ tự khả thi (không cần biết thứ tự nào, DP gốc sẽ tự
    tìm lại khi thật sự mở rộng — hàm này chỉ dùng để PRUNE SỚM khi trả False).
    """
    iv_list = list(label.IV)
    if not iv_list:
        return True
    for perm in permutations(iv_list):
        t = label.t
        v = label.v
        ok = True
        for order_id in perm:
            travel = travel_time(v, delivery_node[order_id])   # dùng đúng travel matrix của bạn
            arrive = t + travel
            if arrive > deadline[delivery_node[order_id]]:
                ok = False
                break
            t = arrive + service_time(delivery_node[order_id])
            v = delivery_node[order_id]
        if ok:
            return True
    return False

# --- điểm chèn: ngay sau _try_pickup thành công, TRƯỚC khi đẩy vào closure ---
# if not iv_completion_feasible(new_label):
#     continue   # bỏ qua hẳn, không chạy closure cho label này
```

**Gate bắt buộc trước khi tin kết quả:** so sánh route_pool (canonical signature) của bản
có patch vs bản gốc trên **n ≤ 6, mọi B, ≥30 instance** — phải khớp 100%. Đây là điều kiện
cần chứng minh đúng (đơn điệu: thêm order tương lai không thể cứu deadline IV đã lỡ), nhưng
vẫn phải test thực nghiệm trước khi tin.

---

## Test B — Bucket/index hoá dominance (engineering thuần, không đổi kết quả)

**Mục đích:** dominance hiện tại rất có thể đang so `O(F²)` hoặc `O(F)` mỗi lần chèn trên
toàn bộ frontier tại 1 key. Vì so sánh chỉ có ý nghĩa giữa các label **cùng `v`**, bucket
theo `v` trước, rồi trong mỗi bucket có thể sort theo `K` để cắt sớm bằng branch-and-bound
đơn giản (nếu `K_new ≥ K_max_hiện_có_trong_bucket` và không tốt hơn ở W thì loại ngay).

```python
import bisect

class DominanceBucket:
    """Một bucket ứng với 1 key (v, IV, C). Giữ frontier Pareto (K,W) đã sort theo K."""
    def __init__(self):
        self.K_sorted = []   # danh sách K đã sort tăng dần
        self.labels = []     # labels tương ứng, cùng thứ tự với K_sorted

    def try_insert(self, new_label):
        """Trả True nếu new_label được giữ lại (không bị dominate), False nếu bị loại."""
        idx = bisect.bisect_left(self.K_sorted, new_label.K)
        # Kiểm các label có K <= new_label.K: nếu có label nào W <= new_label.W -> dominated
        for i in range(idx - 1, -1, -1):
            if self.labels[i].W <= new_label.W:
                return False   # bị dominate, dừng ngay không cần quét tiếp
            if self.labels[i].K < new_label.K:  # đã chắc chắn không thể dominate thêm nữa
                # (không break cứng vì có thể còn K bằng nhau phía trước idx, tuỳ cách bisect)
                pass
        # Xoá các label bị new_label dominate (K >= new_label.K và W >= new_label.W)
        keep_idx = []
        for i in range(len(self.labels)):
            if self.K_sorted[i] >= new_label.K and self.labels[i].W >= new_label.W \
               and not (self.K_sorted[i] == new_label.K and self.labels[i].W == new_label.W):
                continue  # label cũ bị new_label dominate -> loại
            keep_idx.append(i)
        self.K_sorted = [self.K_sorted[i] for i in keep_idx]
        self.labels   = [self.labels[i]   for i in keep_idx]
        insert_pos = bisect.bisect_left(self.K_sorted, new_label.K)
        self.K_sorted.insert(insert_pos, new_label.K)
        self.labels.insert(insert_pos, new_label)
        return True

# --- cách dùng: thay _filter_dominated_labels bằng bucket theo key ---
buckets = defaultdict(DominanceBucket)  # key = (v, frozenset(IV), frozenset(C))

def insert_label_bucketed(label):
    key = (label.v, frozenset(label.IV), frozenset(label.C))
    return buckets[key].try_insert(label)
```

**Cách đo:** chạy đúng cell n=20/B_gw=4/tw=240, so `wall_clock` bản gốc (`_filter_dominated_labels`
kiểu O(F) quét toàn bucket mỗi lần) vs bản bucket hoá trên. Đây **không** phải thử để giảm
`frontier_lastround` (vẫn ~4.5M như cũ, đúng dự đoán) — chỉ đo xem tổng wall-clock có giảm
nhờ mỗi lần so sánh rẻ hơn hay không.

**Gate bắt buộc:** route_pool cuối cùng phải **giống hệt** bản gốc (canonical signature),
n≤6 khớp brute-force. Đây thuần là tối ưu tốc độ, không được phép đổi kết quả.

---

## Test C — Khung thử nghiệm sơ bộ: relaxed key (hướng NG-route, CHỈ ĐỂ THĂM DÒ)

**Cảnh báo:** đây là bản **not-safe-by-default** — dùng để đo xem "nếu nới lỏng key thì
frontier giảm bao nhiêu và có làm mất route hợp lệ nào không", **không phải** bản để dùng
thật trong pipeline. Mục tiêu của test này chỉ là đo tiềm năng (upper bound speedup) trước
khi đầu tư công chứng minh safe.

```python
def relaxed_key(label, ng_neighborhood_size=None):
    """
    Thử nghiệm: thay vì key = (v, frozenset(IV), frozenset(C)) đầy đủ,
    dùng key thô hơn để CHO PHÉP nhiều label hơn được so dominance với nhau.

    Biến thể đơn giản nhất để đo thử: bỏ hẳn `C` ra khỏi key, chỉ giữ (v, frozenset(IV)).
    Lý do thử biến thể này trước: một khi IV giống hệt nhau, phần "đã giao xong" (C) không
    ảnh hưởng tới TƯƠNG LAI của route (route completion chỉ phụ thuộc v, IV hiện tại, và t) —
    NHƯNG t và K/W tích luỹ CÓ chịu ảnh hưởng bởi lịch sử qua C, nên đây có thể KHÔNG SAFE.
    Đây chính là điều cần kiểm bằng gate n<=6, không được giả định đúng.
    """
    return (label.v, frozenset(label.IV))   # relaxed: bỏ C

# --- chạy song song 2 bản: key gốc vs relaxed_key, trên CÙNG n<=6 instance ---
# 1. Đếm frontier_lastround của cả 2 bản -> đo % giảm tiềm năng.
# 2. Với relaxed_key: SAU KHI có "frontier thô", phải lọc lại bằng full-feasibility-check
#    (không tin thẳng K/W đã lưu, vì 2 label cùng relaxed-key có thể có t/K/W thật khác nhau
#    ứng với các con đường C khác nhau tới đó) rồi so sánh route_pool cuối với brute-force.
# 3. Nếu route_pool cuối bị THIẾU route hợp lệ nào so với brute-force -> relaxed_key này
#    UNSAFE, không dùng được nguyên dạng, cần thiết kế điều kiện chặt hơn (đây chính là nội
#    dung cần "chứng minh" nếu muốn đi tiếp hướng EJOR).
```

**Cách chạy nhanh để có tín hiệu ban đầu (chưa cần safe):**
1. Trên n≤6, chạy DP với `relaxed_key` thay `key` gốc, KHÔNG áp full-feasibility-check lại
   (biết trước có thể sai) — chỉ đo `frontier_lastround` giảm bao nhiêu % so với bản gốc.
   Đây là **upper-bound optimistic** — nếu ngay cả upper-bound này giảm không đáng kể (ví dụ
   <10%), hướng NG-route không đáng đầu tư tiếp, dừng ở đây.
2. Nếu upper-bound giảm nhiều (ví dụ >50%), mới đáng bỏ công thiết kế điều kiện safe thật
   sự (bước 2-3 ở trên) và viết proof.

---

## Thứ tự chạy đề xuất

1. **Test A** trước tiên (rẻ nhất, đóng dứt điểm 1 câu hỏi cụ thể).
2. Nếu Test A ra tín hiệu (b) → **Test A2**, đo real speedup + gate n≤6.
3. **Test B** độc lập, chạy bất cứ lúc nào (không phụ thuộc kết quả A) — lợi ích chắc chắn
   có (dù nhỏ), rủi ro thấp, nên làm sớm cho pipeline hiện tại đỡ chậm.
4. **Test C bước 1** (chỉ đo upper-bound, chưa cần safe) — nếu tín hiệu yếu, dừng luôn, tiết
   kiệm được nhiều công sức chứng minh không cần thiết.