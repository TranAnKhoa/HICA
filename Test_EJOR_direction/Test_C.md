# Test C — Relaxed-Key Upper-Bound (hướng NG-route-style)

## 1. Test C giải quyết câu hỏi gì

Từ kết luận đã chốt: bottleneck thật ở vùng nóng (B_gw lớn, tw rộng) là **Case 2** — hơn 4
triệu label sống sót, tất cả đều hợp lệ, không cái nào dominate được cái nào. Ba hướng đã
thử (PCF, MST, IV-completion) đều thuộc họ "phát hiện chết sớm hơn" — và đã chứng minh họ
này bất lực ở đây vì **không có gì chết cả** để phát hiện sớm hơn.

Test C hỏi một câu khác hẳn: thay vì cố tránh sinh ra label, **có cách nào làm cho nhiều
cặp label hơn trở nên so sánh được với nhau không** — tức là nới lỏng chính điều kiện dùng
để quyết định "hai label này có được phép so dominance hay không".

### Vì sao dominance hiện tại bỏ lỡ nhiều cơ hội so sánh

Dominance hiện tại chỉ so 2 label khi chúng có **cùng key tuyệt đối** `(v, IV, C)` — cùng vị
trí, cùng tập đang mang, cùng tập đã giao **y hệt nhau**. Hai label chỉ khác nhau đúng 1 order
trong `C` (ví dụ một cái đã giao xong order 7, cái kia thì chưa, còn lại giống hệt) sẽ **không
bao giờ được so với nhau** — dù về bản chất, phần `C` đã giao xong không còn ảnh hưởng gì tới
khả năng hoàn tất phần *còn lại* của route nữa (đơn hàng đã giao thì đã giao xong, không tác
động ngược lại tương lai). Đây chính là chỗ có khả năng nới lỏng.

### Vì sao đây không phải "hồi sinh cái đã bị bác" (Lozano/MST)

Lozano/MST bị loại vì dùng bound theo *giá trị mục tiêu* phụ thuộc dual price → dính bid.
Test C không đụng gì tới giá trị mục tiêu hay bid — nó chỉ đổi **định nghĩa "so sánh được"**
giữa 2 label đã có sẵn K, W tính đúng theo cách cũ. Không vi phạm điều kiện "route generation
không đọc bid".

## 2. Vì sao phải làm bước "upper-bound" trước, chưa vội chứng minh safe

Nếu nới lỏng key mà route_pool cuối cùng bị **mất route hợp lệ** (một cặp label bị coi là
"a dominate b" trong khi thực ra a và b dẫn tới 2 tương lai khác nhau, không thể quy đổi cho
nhau) — kỹ thuật này **không safe**, không dùng được nguyên dạng.

Chứng minh safe tốn công (cần chỉ rõ điều kiện gì đủ để bỏ qua phần khác biệt trong key mà
không mất thông tin). Trước khi bỏ công đó, nên đo thử "nếu giả sử nới lỏng an toàn tuyệt
đối" thì frontier giảm được bao nhiêu — đây là **cận trên lạc quan** (optimistic upper
bound), không cần đúng, chỉ cần biết tiềm năng lớn hay nhỏ.

- Nếu upper-bound giảm **ít** (ví dụ <10-15%) → dừng luôn, không đáng đầu tư chứng minh gì
  cả, vì dù chứng minh xong cũng không cứu được nhiều.
- Nếu upper-bound giảm **nhiều** (ví dụ >50%) → đáng bỏ công tìm điều kiện safe thật, viết
  proof, đây mới là ứng viên thật cho A-T4/EJOR.

## 3. Cách đo cụ thể

### 3.1 Biến thể key thử nghiệm

Thử vài biến thể, từ lỏng nhất (rủi ro sai nhiều nhất, tiềm năng giảm nhiều nhất) đến chặt
hơn:

```python
def key_full(label):
    """Key gốc — dùng làm baseline để so sánh."""
    return (label.v, frozenset(label.IV), frozenset(label.C))

def key_drop_C(label):
    """Bỏ hẳn C. Giả thuyết: order đã giao xong không ảnh hưởng tương lai."""
    return (label.v, frozenset(label.IV))

def key_drop_C_size_only(label):
    """Thay C bằng |C| (giữ lại thông tin 'đã giao bao nhiêu', bỏ 'giao đúng những cái nào').
    Chặt hơn key_drop_C một chút — có thể ít sai hơn."""
    return (label.v, frozenset(label.IV), len(label.C))
```

### 3.2 Đo upper-bound (KHÔNG cần đúng, chỉ cần đo frontier)

```python
from collections import defaultdict

def measure_relaxed_frontier(all_labels_by_round, key_fn):
    """
    all_labels_by_round: danh sách tất cả label đã sinh ra trong 1 lần chạy DP gốc
    (lấy TRƯỚC khi DP gốc tự làm dominance theo key_full — cần log lại toàn bộ label
    sinh ra, không chỉ label sống sót cuối cùng).

    Áp lại dominance THEO key_fn (thô hơn), đếm frontier cuối cùng.
    Đây chỉ là đo optimistic bound — KHÔNG dùng kết quả này làm route_pool thật.
    """
    buckets = defaultdict(list)  # key -> list of (K, W, label)
    for label in all_labels_by_round:
        k = key_fn(label)
        buckets[k].append(label)

    total_frontier = 0
    for k, labels in buckets.items():
        # Pareto filter thuần trên (K, W) trong bucket này
        pareto = []
        for lb in sorted(labels, key=lambda x: x.K):
            if not any(p.W <= lb.W for p in pareto):
                pareto.append(lb)
        total_frontier += len(pareto)
    return total_frontier

# --- cách dùng ---
# frontier_baseline = measure_relaxed_frontier(all_labels, key_full)
# frontier_drop_C   = measure_relaxed_frontier(all_labels, key_drop_C)
# print(f"Baseline (key gốc):     {frontier_baseline}")
# print(f"Relaxed (bỏ C):         {frontier_drop_C}  "
#       f"({100*(1 - frontier_drop_C/frontier_baseline):.1f}% giảm)")
```

**Lưu ý kỹ thuật quan trọng:** phải log **toàn bộ label được sinh ra trước dominance gốc**,
không phải chỉ frontier cuối cùng — vì nếu áp `key_drop_C` lên frontier đã lọc theo
`key_full`, một số label lẽ ra phải bị gộp lại đã bị dominance gốc loại mất từ trước, làm
sai lệch kết quả đo (đánh giá thấp tiềm năng thật). Nếu việc log toàn bộ label tốn bộ nhớ quá
lớn ở cell nóng (7 triệu lượt), có thể ước lượng trên n nhỏ hơn (n=10-15) trước, xem xu
hướng % giảm có ổn định không rồi mới quyết định có cần đo đúng ở n=20 hay không.

### 3.3 Kiểm mức độ "sai" nếu dùng thật (bước sau, chỉ làm nếu upper-bound hứa hẹn)

```python
def audit_relaxed_key_safety(instance, key_fn, n_max=6):
    """
    Chạy DP với key_fn thay key_full, KHÔNG tin thẳng (K,W) đã lưu khi 2 label có key
    giống nhau nhưng C khác nhau — với mỗi cặp bị "gộp nhầm" khả dĩ, kiểm tra bằng cách
    mở rộng cả 2 tới cùng một node tương lai xem (K,W) cuối cùng có thực sự giống nhau
    (hoặc một cái luôn tốt hơn cái kia) hay không.

    So route_pool cuối với brute-force trên n <= n_max. Trả về:
      - route_pool khớp 100% -> key_fn AN TOÀN trên instance này
      - thiếu route nào đó -> key_fn KHÔNG an toàn, ghi lại instance phản ví dụ cụ thể
    """
    pass  # code thật tuỳ theo cấu trúc t6_dp.py — đây là khung, cần điền theo harness đã có
```

## 4. Tiêu chí đọc kết quả

| % giảm frontier (upper-bound, key_drop_C) | Hành động tiếp theo |
|---|---|
| < 15% | Dừng hẳn hướng relaxed-key. Case 2 coi như đã hết đường, viết kết quả phủ định vào thesis. |
| 15% – 50% | Đáng ghi nhận nhưng chưa chắc đáng công chứng minh — cân nhắc thời gian còn lại của thesis trước khi quyết định. |
| > 50% | Đáng đầu tư: chuyển sang bước `audit_relaxed_key_safety`, tìm phản ví dụ trên n≤6 trước, rồi mới nghĩ tới điều kiện safe tổng quát và viết proof. |

## 5. Nếu upper-bound tốt nhưng key_drop_C KHÔNG safe — bước tiếp theo là gì

Nếu tìm được phản ví dụ (route_pool thiếu route hợp lệ), đừng bỏ cuộc ngay — thử các biến
thể *chặt hơn* theo thứ tự:

1. `key_drop_C_size_only` (giữ |C|, bỏ danh tính) — an toàn hơn `key_drop_C` nếu vấn đề nằm
   ở chỗ 2 order khác nhau trong C có deadline/vị trí ảnh hưởng khác nhau tới bước home/kết
   thúc route.
2. Giữ nguyên `C` nhưng **nới lỏng theo t**: cho phép 2 label so dominance dù `t` lệch nhau
   trong một ngưỡng nhỏ ε cố định (định trước, không phụ thuộc bid) — đổi lại phải chứng
   minh phần chênh lệch t đó không thể "lật ngược" thứ tự dominate ở phần route còn lại.
3. Nếu cả hai đều không an toàn — đây tự nó là bằng chứng cho thấy `C` (hoặc `t` chính xác)
   mang thông tin thực sự cần thiết cho tính đúng đắn, không phải dư thừa — một kết luận cấu
   trúc đáng viết ra, tương tự các REJECTED trước đó trong dự án.

## 6. Thứ tự việc làm

1. Log toàn bộ label sinh ra (trước dominance gốc) trên **n=10-15**, B_gw=4, tw=240 — nhỏ
   hơn cell nóng thật để đo nhanh trước.
2. Chạy `measure_relaxed_frontier` với `key_full` và `key_drop_C`, so % giảm.
3. Theo bảng ở mục 4 mà quyết định dừng hay đi tiếp.
4. Nếu đi tiếp: chạy `audit_relaxed_key_safety` trên n≤6 để tìm phản ví dụ trước khi nghĩ
   tới proof tổng quát.