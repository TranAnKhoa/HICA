#T4 Test
# Guideline thực nghiệm — Kiểm chứng BFS level-wise cho bài toán sinh bundle (HICA-S Algorithm A)

**Đối tượng thực hiện:** Claude Code
**Ngôn ngữ:** Python 3.11+, không cần thư viện ngoài (numpy tùy chọn)
**Thời lượng ước tính:** 1–2 buổi làm việc

---

## 0. Mục đích — đọc kỹ trước khi code

Đây **không phải** bài toán tối ưu. Đây là một thực nghiệm đo lường nhằm trả lời **đúng ba câu hỏi**, và mọi dòng code viết ra phải phục vụ một trong ba câu đó:

| # | Câu hỏi | Đại lượng đo |
|---|---|---|
| **Q1** | Thuật toán BFS level-wise (đề xuất) có **đầy đủ** (complete) không? | So khớp 100% với brute force |
| **Q2** | Mỗi subset phải lưu **bao nhiêu sequence** để giữ completeness? | Phân phối `|Seq(S)|` theo lớp tài xế, k, độ chặt TW |
| **Q3** | Bộ lọc `slack*` cắt được bao nhiêu % subset **trước khi** phải chèn? | Tỷ lệ prune, và kiểm phản chứng monotonicity |

**Q2 là câu hỏi quan trọng nhất.** Nếu `|Seq(S)|` bùng nổ theo k, toàn bộ hướng tiếp cận này sụp và cần biết sớm.

**Cảnh báo về tính trung thực của thực nghiệm:** không được điều chỉnh tham số sinh instance sau khi thấy kết quả, để đạt được con số mong muốn. Khóa grid tham số ở §5 **trước khi chạy**, báo cáo toàn bộ đường cong kể cả khi kết quả xấu. Kết quả xấu là một kết quả, không phải một thất bại.

---

## 1. Mô hình bài toán — chốt chính xác, không suy diễn thêm

### 1.1 Dữ liệu

```python
Order:   id, pickup_node, delivery_node, demand
Node:    id, x, y, ready_time (e), deadline (l), service_time (s)
Driver:  id, class ∈ {OD, GW}, start_node, capacity,
         start_time (t0),                    # THỜI ĐIỂM CỐ ĐỊNH, không phải biến
         home_node   (chỉ OD),
         tau         (chỉ OD, detour budget tính bằng phút)
```

**[LOCK] Giả định bắt buộc, không được nới:**

1. `start_time` của tài xế là **hằng số cho trước**, không phải biến quyết định. (Lý do: nếu nó là biến, bài toán rơi vào ca phức tạp của Gschwind & Drexl 2019 cần preprocessing O(r³); ta cố ý tránh.)
2. Travel time = Euclid distance / speed, **thỏa bất đẳng thức tam giác**. Kiểm tra assertion này khi sinh instance.
3. Cho phép chờ (waiting) tại mọi node, không phạt.
4. Lịch trình dùng chính sách **ASAP**: phục vụ mỗi node sớm nhất có thể.
5. Không có ràng buộc ride-time (thời gian tối đa từ pickup đến delivery của cùng order). Nếu sau này thêm vào, mọi kết luận trong file này phải kiểm lại.

### 1.2 Feasibility của một sequence

Sequence `R = (start, v1, ..., vm)` (với OD thì thêm `home` ở cuối) là khả thi khi và chỉ khi:

```
pairing + precedence:  pickup của order o xuất hiện trước delivery của o
time window:           B_i = max(A_i, e_i) và B_i ≤ l_i tại mọi node i
capacity:              load sau mỗi event ∈ [0, capacity]
OD only:               arrival(home) ≤ t0 + direct_time + tau
```

trong đó `A_i = D_{i-1} + t(v_{i-1}, v_i)`, `D_i = B_i + s_i`.

**Chú ý cho OD:** detour budget được cài đặt như một **deadline tại node home**, không phải một ràng buộc riêng biệt:
```python
deadline_home = driver.t0 + direct_time(start → home) + driver.tau
```
Sau bước này, OD và GW dùng **chung một hàm feasibility**; khác biệt duy nhất là GW không có node home bắt buộc.

### 1.3 Định nghĩa slack

Với một sequence khả thi R, dưới lịch ASAP:

```python
slack(R) = min over all nodes i in R of (l_i - B_i)
```

Với OD, node `home` có `l_home = deadline_home` như trên và tham gia vào min.

Với một **tập** S (không phải sequence):

```python
slack_star(S) = max over all feasible sequences R of S of slack(R)
              = -infinity nếu S không có sequence khả thi nào
```

`slack_star` là hàm của **tập**, không phụ thuộc sequence đại diện nào. Đây là điểm mấu chốt — xem §3.3.

---

## 2. Thành phần 1 — Brute force (ground truth)

Đây là chuẩn đối chiếu, viết đơn giản nhất có thể, ưu tiên **đúng** hơn nhanh.

```
BRUTE_FORCE(driver, orders, B):
    result = {}
    for each subset S of orders với 1 ≤ |S| ≤ B:
        feasible_seqs = []
        for each permutation của 2|S| node (pickup+delivery của S):
            if không thỏa precedence: bỏ qua
            if not is_feasible(sequence): bỏ qua
            feasible_seqs.append(canonical(sequence))
        result[S] = feasible_seqs
    return result
```

Yêu cầu:
- Viết `is_feasible()` **một lần duy nhất**, dùng chung cho cả brute force lẫn BFS. Nếu viết hai bản, sai lệch giữa chúng sẽ ngụy trang thành lỗi thuật toán.
- `canonical(seq)` = tuple các node id theo thứ tự — dùng để so khớp tập hợp.
- Không tối ưu gì cả. Chấp nhận chậm.

---

## 3. Thành phần 2 — BFS level-wise (thuật toán cần kiểm chứng)

### 3.1 Cấu trúc

```
BFS_GENERATE(driver, orders, B):
    Seq[{o}] = tất cả sequence khả thi của từng order đơn, ∀o reachable
    # với 1 order: đúng 1 sequence (start → P → D → [home])

    for k = 2 to B:
        for each subset S với |S| = k:
            # BƯỚC LỌC (§3.3)
            if FILTER_SLACK_STAR(S) == PRUNE:
                Seq[S] = []
                đếm vào prune_counter
                continue

            # BƯỚC CHỌN PARENT
            j = một order bất kỳ trong S          # xem §3.2: chọn cách nào cũng đúng
            P = S \ {j}
            if Seq[P] rỗng: Seq[S] = []; continue   # downward-closedness

            # BƯỚC CHÈN — chèn vào MỌI sequence, MỌI vị trí
            Seq[S] = []
            for each sequence R in Seq[P]:              # ← TẤT CẢ, không chọn 1 cái
                for each vị trí a để chèn P_j:
                    for each vị trí b > a để chèn D_j:
                        R' = insert(R, P_j at a, D_j at b)
                        if is_feasible(R'):
                            Seq[S].append(canonical(R'))
            Seq[S] = deduplicate(Seq[S])
    return Seq
```

### 3.2 Vì sao chọn parent set nào cũng được (đã chứng minh)

Lấy R là sequence khả thi bất kỳ của S. Xóa cặp (P_j, D_j) khỏi R rồi nối tắt. Do bất đẳng thức tam giác, mọi arrival time chỉ sớm lên hoặc giữ nguyên → không deadline nào bị vi phạm; ready time xử lý bằng chờ; load chỉ giảm. Vậy sequence thu được khả thi cho `S \ {j}`, tức nó nằm trong `Seq[S\{j}]`. Do đó R **luôn** sinh lại được bằng cách chèn (P_j, D_j) vào một phần tử của `Seq[S\{j}]`.

Hệ quả: chọn parent tùy ý → mỗi subset sinh đúng **một lần** thay vì k lần.

**Cảnh báo tuyệt đối:** chọn **tập** cha thì vô hại; chọn **một sequence** trong tập cha thì **mất completeness**. Đã có phản ví dụ. Đây là lỗi dễ mắc nhất khi tối ưu code — đừng "cải tiến" bằng cách chỉ giữ sequence tốt nhất.

### 3.3 Bộ lọc slack* — cần kiểm chứng bằng thực nghiệm

**Mệnh đề cần kiểm:** với `S ⊆ S'`, ta có `slack_star(S') ≤ slack_star(S)`.

*Phác chứng minh:* lấy sequence R' của S' đạt `slack_star(S')`. Xóa các order thừa → sequence R của S, khả thi (§3.2). Do tam giác, mọi arrival trong R sớm hơn hoặc bằng trong R' → slack tại mỗi node còn lại lớn hơn hoặc bằng → `slack(R) ≥ slack(R')`. Vậy `slack_star(S) ≥ slack(R) ≥ slack_star(S')`. ∎

*Trạng thái:* chứng minh trên **có vẻ đúng nhưng chưa được kiểm chứng độc lập**. Nhiệm vụ của thực nghiệm là **cố phá nó** (§4.3).

**Bộ lọc:**
```python
def FILTER_SLACK_STAR(S):
    bound = min(slack_star(S \ {j}) for j in S)   # tất cả tập con thiếu 1 phần tử
    if bound < 0:
        return PRUNE
    return KEEP
```

`slack_star(S\{j})` đã tính ở level trước → tra bảng, O(k).

---

## 4. Kiểm chứng bắt buộc — gate không được bỏ qua

### 4.1 Gate completeness (quan trọng nhất)

Với **mọi** instance test:
```python
assert set(BFS_GENERATE(...)[S]) == set(BRUTE_FORCE(...)[S])  for every S
```
Sai một trường hợp = thuật toán hỏng. Dừng lại, báo cáo subset nào lệch, sequence nào bị thiếu/thừa, và in ra sequence đó kèm lịch trình đầy đủ.

Chạy gate này trên **toàn bộ** instance có n ≤ 6, B ≤ 3.

### 4.2 Gate feasibility validator độc lập

Viết một hàm `validate(sequence)` **riêng biệt**, cách cài đặt khác `is_feasible()` (ví dụ: tính lại toàn bộ lịch từ đầu bằng vòng lặp thô, không dùng cấu trúc dữ liệu tăng tốc nào). Mọi sequence trong output phải pass validator này.

### 4.3 Test phản chứng monotonicity của slack*

Đây là test **cố tình đi tìm lỗi** trong chứng minh §3.3:

```python
for each pair (S, S') với S ⊂ S':
    if slack_star(S') > slack_star(S) + 1e-9:
        BÁO CÁO PHẢN VÍ DỤ   # chứng minh sai → bộ lọc không hợp lệ
```

Chạy trên toàn bộ instance nhỏ. Nếu tìm được phản ví dụ, **đây là phát hiện quan trọng nhất của cả thực nghiệm** — in ra đầy đủ hai tập, hai sequence tối ưu, và lịch trình của chúng.

### 4.4 Test bộ lọc không cắt nhầm

```python
for each S bị FILTER_SLACK_STAR loại:
    assert BRUTE_FORCE[S] == []   # phải thật sự infeasible
```

---

## 5. Sinh instance — khóa grid TRƯỚC khi chạy

```python
GRID = {
    "n_orders":     [4, 5, 6],            # cho gate correctness (brute force còn chạy nổi)
    "n_orders_big": [8, 10, 12, 15],      # cho đo Q2 (chỉ chạy BFS, không brute force)
    "B":            [2, 3, 4],
    "driver_class": ["OD", "GW"],
    "tw_width":     [30, 60, 120, 240],   # phút — biến điều khiển chính cho Q2
    "tau":          [15, 30, 60],         # phút, chỉ OD
    "area_km":      10,
    "speed_kmh":    20,
    "service_min":  5,
    "seeds":        list(range(30)),      # 30 realization mỗi cell
}
```

**Cách sinh:**
- Node ngẫu nhiên đều trong hình vuông `area_km × area_km`.
- `ready_time` của pickup ~ U[0, 120]; `deadline = ready + tw_width`.
- Delivery: `ready = ready_pickup`, `deadline = deadline_pickup + tw_width`.
- OD: `home` ngẫu nhiên; `direct_time` tính từ start→home; `tau` theo grid.
- GW: không home; availability = [t0, t0 + 480].
- **Assert bất đẳng thức tam giác** trên ma trận travel time sau khi sinh.

---

## 6. Số liệu cần log — mỗi dòng một (instance, driver, subset)

```csv
instance_id, seed, n_orders, B, driver_class, tw_width, tau,
subset_id, k, 
n_feasible_sequences,        # ← Q2: ĐẠI LƯỢNG QUAN TRỌNG NHẤT
n_insertion_attempts,        # số phép thử chèn thực tế
n_permutations_bruteforce,   # (2k)!/2^k để so sánh
was_pruned_by_filter,        # bool
slack_star,
walltime_bfs_ms, walltime_bruteforce_ms
```

---

## 7. Báo cáo cần xuất ra

### 7.1 Bảng correctness
| n | B | lớp | #instance | completeness pass | validator pass | phản ví dụ monotonicity | filter cắt nhầm |

### 7.2 Biểu đồ Q2 — cốt lõi
- **Hình 1:** `n_feasible_sequences` (median + IQR + max) theo trục k, một đường cho mỗi `tw_width`, tách panel OD / GW.
- **Hình 2:** tỷ lệ `n_insertion_attempts / n_permutations_bruteforce` theo k — cho thấy tiết kiệm thực tế so với enumeration đầy đủ.

### 7.3 Bảng Q3 — hiệu lực bộ lọc
| lớp | tw_width | k | % subset bị filter cắt | % subset infeasible thật | tỷ lệ bắt được |

### 7.4 Bảng bất đối xứng OD vs GW
Cùng tham số, so sánh trực tiếp `n_feasible_sequences` giữa hai lớp. Đây là dữ liệu cho §7.3 của đề cương, dù T4 thành công hay không.

---

## 8. Ngưỡng diễn giải — quyết định trước, không đổi sau

| Kết quả Q2 (median `n_feasible_sequences` tại k=B) | Kết luận |
|---|---|
| ≤ 5 | Hướng tiếp cận khả thi. Tiếp tục sang thiết kế bound mạnh hơn. |
| 5–50 | Khả thi nhưng cần dominance an toàn để nén. Ưu tiên tìm dominance trước khi làm gì khác. |
| > 50 hoặc tăng theo cấp số nhân theo k | **Hướng này không dùng được ở quy mô đó.** Báo cáo trung thực, chuyển trọng tâm sang T5 (component decomposition). |

| Kết quả Q3 (% subset bị filter cắt) | Kết luận |
|---|---|
| ≥ 30% | Bộ lọc có giá trị thật, viết vào paper. |
| 10–30% | Yếu, cần bound mạnh hơn (hướng arc-charging + PMTN). |
| < 10% | Bộ lọc gần như vô dụng, không đáng viết. |

---

## 9. Những gì KHÔNG làm trong vòng thực nghiệm này

- Không cài đặt WDP (Algorithm B) hay payment (Algorithm C).
- Không cài đặt bound arc-charging/PMTN — đó là vòng sau, chỉ làm nếu Q3 cho kết quả yếu.
- Không tối ưu tốc độ trước khi gate §4.1 pass 100%.
- Không thêm ràng buộc ride-time, không thêm nhiều tài xế, không thêm bid.
- Không "cải tiến" bằng cách giữ ít sequence hơn — sẽ phá completeness.

---

## 10. Định dạng báo cáo cuối

Một file `REPORT.md` gồm:
1. Bảng correctness (§7.1) — nếu có bất kỳ ô nào fail, dừng và báo cáo chi tiết, không chạy tiếp phần đo.
2. Hai biểu đồ Q2 (§7.2) + bảng số liệu thô kèm theo.
3. Bảng Q3 (§7.3), bảng bất đối xứng (§7.4).
4. Kết luận theo đúng ngưỡng §8 — **viết thẳng kết luận kể cả khi nó bác bỏ hướng tiếp cận**.
5. Danh sách mọi bất thường quan sát được, kể cả thứ chưa giải thích được.

Toàn bộ code, seed, và CSV thô phải lưu lại để chạy lại được.