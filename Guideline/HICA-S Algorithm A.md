# HICA-S Algorithm A — BFS Level-wise Bundle Generation
## Tài liệu tham chiếu đã kiểm chứng thực nghiệm (dùng để tiếp tục ở hội thoại khác)

**Trạng thái tại thời điểm viết:** thuật toán chính đã kiểm chứng completeness tuyệt đối trên
1.152+ instance nhỏ. Một hướng nén (Pareto-dominance) đã bị bác bỏ bằng thực nghiệm. Câu hỏi
lý thuyết trung tâm của thesis (T4 — cận đơn điệu rẻ để cắt cả cây con, không chỉ lọc theo
feasibility đã biết) **vẫn CHƯA giải được**. Tài liệu này tách rõ ba loại nội dung bằng nhãn:

- **[PROVEN]** — đã chứng minh trên giấy, đọc lại chứng minh sẽ tự kiểm được.
- **[VALIDATED]** — đã kiểm bằng thực nghiệm (brute force ground truth, gate pass), không phải chỉ suy diễn.
- **[REJECTED]** — đã thử, đã bác bỏ bằng thực nghiệm hoặc phản ví dụ, đừng thử lại theo cách cũ.
- **[OPEN]** — chưa có câu trả lời, là việc cần làm tiếp.

---

## 1. Bối cảnh bài toán (rút gọn)

HICA-S Algorithm A: platform sinh route-bundle từ order nguyên tử cho hai lớp tài xế —
**GW** (gigworker, open route, không có điểm kết cố định) và **OD** (occasional driver,
phải kết thúc tại `home`, có detour budget `tau`). Route generation **không được đọc bid**
(điều kiện DSIC). Bundle cap `B`.

### 1.1 Mô hình dữ liệu

```
Order:   pickup_node, delivery_node, demand
Node:    ready_time (e), deadline (l), service_time (s)
Driver:  class ∈ {OD, GW}, start_node, capacity, start_time t0 (HẰNG SỐ, không phải biến),
         home_node (chỉ OD), tau (chỉ OD, phút)
```

**[LOCK]** `start_time t0` của tài xế là hằng số cho trước, không phải biến quyết định.
Lý do: nếu để tự do, bài toán rơi vào ca phức tạp cần preprocessing O(r³) (Gschwind & Drexl
2019) vì ASAP không còn là chiến lược tối ưu. Khóa `t0` giữ được ASAP tối ưu, đơn giản hóa
toàn bộ phần dưới.

**[LOCK]** Travel time = distance/speed, thỏa bất đẳng thức tam giác. Mọi chứng minh dưới
đây phụ thuộc giả định này.

### 1.2 Feasibility của một sequence

Sequence `R = (start, v1, ..., vm [, home nếu OD])` khả thi khi:
```
precedence:    pickup(o) trước delivery(o), ∀o trong route
time window:   B_i = max(A_i, e_i) ≤ l_i,  với A_i = D_{i-1} + t(v_{i-1}, v_i), D_i = B_i + s_i
capacity:      load sau mỗi event ∈ [0, capacity]
OD only:       arrival(home) ≤ deadline_home := t0 + direct_time(start→home) + tau
```

**Điểm mấu chốt về OD:** detour budget được mô hình như **một deadline tại node home**,
không phải ràng buộc riêng biệt. Sau bước này, OD và GW dùng chung một hàm `is_feasible()`.

### 1.3 Slack

```
slack(R) = min over mọi node i trong R của (l_i - B_i)      # home tham gia với l_home = deadline_home
```

---

## 2. Thuật toán chính: BFS level-wise — [VALIDATED]

### 2.1 Pseudocode

```
Seq[{o}] = mọi sequence khả thi của order đơn o                    # k=1: đúng 1 sequence/order

for k = 2 to B:
    for each subset S, |S| = k:
        if FILTER_SLACK_STAR(S) == PRUNE:          # §3, cắt bằng cận đã biết, KHÔNG chèn thử gì
            Seq[S] = []; continue

        j = một phần tử bất kỳ của S                # chọn TẬP cha — an toàn, xem Định lý 2.2
        P = S \ {j}
        if Seq[P] == []: Seq[S] = []; continue      # downward-closedness, Định lý 2.3

        Seq[S] = []
        for each R in Seq[P]:                        # TOÀN BỘ sequence của P — KHÔNG chọn 1 cái
            for each vị trí hợp lệ (a, b) để chèn (pickup_j tại a, delivery_j tại b, a<b):
                R' = insert(R, pickup_j@a, delivery_j@b)
                if is_feasible(R'): Seq[S].append(canonical(R'))
        Seq[S] = dedupe(Seq[S])
```

### 2.2 Định lý bất biến chọn cha — [PROVEN]

**Phát biểu:** với `S`, `|S|=k`, chọn **bất kỳ** `j ∈ S`, đặt `P = S\{j}`. Mọi sequence khả
thi của `S` sinh được bằng cách chèn `(pickup_j, delivery_j)` vào một sequence nào đó của `P`.

**Chứng minh:** lấy `R` là sequence khả thi bất kỳ của `S`. Xóa cặp `(pickup_j, delivery_j)`
khỏi `R`, nối tắt hai đầu. Do bất đẳng thức tam giác, mọi arrival time trong sequence mới chỉ
sớm lên hoặc giữ nguyên so với `R` → không deadline nào bị vi phạm; ready time xử lý bằng chờ
(waiting luôn được phép); load tại mọi điểm chỉ giảm. Vậy sequence thu được khả thi cho `P`.
Do đó `R` sinh lại được bằng cách chèn `(pickup_j, delivery_j)` vào đúng sequence đó. ∎

**Hệ quả thực dụng:** chọn `j` nào cũng được (kể cả bừa), mỗi subset sinh đúng **một lần**
thay vì `k` lần từ `k` parent khác nhau.

**[VALIDATED]** Test2: 29.056 subset, `set(BFS[S]) == set(BRUTE_FORCE[S])` khớp tuyệt đối
100% trên toàn bộ n≤6, B≤4, mọi (class, tw_width, tau, seed).

### 2.3 Định lý downward-closedness — [PROVEN]

**Phát biểu:** nếu `S` infeasible (không có sequence khả thi nào) thì mọi superset của `S`
cũng infeasible.

**Chứng minh:** hệ quả trực tiếp của 2.2 — nếu `Seq[P] = []` thì không có gì để chèn vào,
`Seq[S] = []`. ∎

### 2.4 Cảnh báo tuyệt đối — lỗi dễ mắc nhất

> **Chọn một TẬP cha thì an toàn (Định lý 2.2). Chọn MỘT SEQUENCE đại diện của tập cha
> (ví dụ "chỉ giữ sequence có slack lớn nhất") thì KHÔNG an toàn — mất completeness.**

Phản ví dụ cụ thể (đã dựng bằng số, xem lịch sử hội thoại gốc): hai sequence A, B của
cùng một tập 2-order có slack khác nhau (A cao hơn B). Order thứ 3 nằm đúng trên một cạnh
mà chỉ B có (A "nén gọn" hai order đầu, vô tình phá mất cạnh đó để đổi lấy slack cao hơn).
Nếu chỉ giữ A (theo tiêu chí "slack cao nhất"), order thứ 3 không chèn được — dù thực ra
{3 order} khả thi qua B. Đây là lý do §2.1 viết rõ "TOÀN BỘ sequence của P — KHÔNG chọn 1 cái".

---

## 3. Bộ lọc slack* — [VALIDATED], cắt cây con hợp lệ

### 3.1 Định nghĩa

```
slack_star(S) = max over mọi sequence khả thi R của S của slack(R)
              = -infinity nếu S infeasible
```

Hàm của **tập** S, không phụ thuộc sequence đại diện nào — khác hẳn maximin-slack-của-một-witness
đã bị bác bỏ ở §2.4.

### 3.2 Định lý đơn điệu — [PROVEN], [VALIDATED]

**Phát biểu:** `S ⊆ S' ⟹ slack_star(S') ≤ slack_star(S)`.

**Phác chứng minh:** lấy `R'` đạt `slack_star(S')`. Xóa các order thừa (không thuộc `S`) khỏi
`R'` → sequence `R` của `S`, khả thi (theo 2.2 áp dụng lặp lại). Do tam giác, mọi arrival trong
`R` sớm hơn hoặc bằng trong `R'` → slack tại mỗi node còn lại lớn hơn hoặc bằng → `slack(R) ≥
slack(R')`. Vậy `slack_star(S) ≥ slack(R) ≥ slack_star(S') `. ∎

**[VALIDATED]** Test2 §4.3: quét toàn bộ cặp `S ⊂ S'` trên ground-truth brute force của
1.152 instance nhỏ (n≤6) — **0 phản ví dụ**. Định lý sống sót một nỗ lực phá có chủ đích.

### 3.3 Bộ lọc dùng trong BFS

```python
def FILTER_SLACK_STAR(S):
    bound = min(slack_star(S \ {j}) for j in S)   # tra bảng level trước, O(k)
    if bound < 0: return PRUNE                     # slack_star(S) ≤ bound < 0, chắc chắn infeasible
    return KEEP
```

**[VALIDATED]** Test2 §4.4: 0 trường hợp cắt nhầm trên toàn bộ 1.152 instance nhỏ.

### 3.4 Hiệu lực thực nghiệm — catch rate mạnh nhưng KHÔNG cứu được bùng nổ

**[VALIDATED]**, số liệu từ Test2 `big_raw.csv` (602.752 dòng, n=8..15):

| lớp | k | catch rate (đúng bao nhiêu % subset infeasible được lọc trước) |
|---|---|---|
| GW | 2 | 17,8% |
| GW | 3 | 60,3% |
| GW | 4 | **89,0%** |

Bộ lọc **làm tốt việc của nó** — không phải "yếu". Nhưng phát hiện quan trọng hơn nằm ở
mối tương quan giữa `tw_width` và cả hai đại lượng (% infeasible thật, catch rate) cùng lúc:

| tw_width (GW) | % subset infeasible thật | median `|Seq(S)|` tại k=B=4 |
|---|---:|---:|
| 30 | 48,6% | 0 |
| 60 | 3,6% | 91 |
| 120 | 0,0% | 1.399 |
| 240 | 0,0% | **2.520** (= trần lý thuyết `(2k)!/2^k`) |

**Kết luận cấu trúc [VALIDATED]:** hai đại lượng nghịch biến gần như hoàn hảo. Đúng chỗ
bundle bùng nổ (TW lỏng) là đúng chỗ **không có gì để cắt** (infeasible rate → 0%). Đây
không phải đặc thù của `slack_star` — **bất kỳ bound nào dựa trên "biết trước feasibility"
đều chịu chung số phận**: bound chỉ có giá trị khi có nhiều case infeasible để bắt, mà
"nhiều case infeasible" và "bundle nhỏ tự nhiên" luôn đi cùng nhau. Đây là lập luận cấu
trúc, không phụ thuộc bound cụ thể nào — nó đóng lại cả một họ hướng tiếp cận
(feasibility-based pruning nói chung), không chỉ riêng `slack_star`.

---

## 4. Đã thử và BỊ BÁC BỎ: nén bằng Pareto-dominance — [REJECTED]

### 4.1 Ý tưởng (tưởng dùng được)

Thay vì lưu toàn bộ `Seq(S)` (bùng nổ theo §3.4), chỉ giữ tập không bị thống trị:
```
label(seq) = (end_node, arrival_time_tại_end_node, K, W)     # K, W: xem ghi chú thuật ngữ §4.4
label1 dominates label2 ⟺ cùng end_node, arrival1≤arrival2, K1≤K2, W1≤W2, ≥1 strict
Pareto(S) = sequence trong Seq(S) không bị dominate bởi sequence nào khác trong Seq(S)
```
Ý định: level sau chỉ chèn từ `Pareto(P)` thay vì `Seq(P)`.

### 4.2 Vì sao về lý thuyết nó có vẻ hợp lý nhưng thực ra không

Dominance 4-chiều này đúng chuẩn cho DP kiểu ESPPRC/labeling (Feillet et al. 2004, Ropke &
Cordeau 2009) — nhưng các thuật toán đó **chỉ cho phép nối order mới vào CUỐI route** (route
"grows" tuần tự). PDPTW ở đây cho phép chèn **vào giữa** tuyến (giữa hai node bất kỳ), và khả
năng chèn-giữa phụ thuộc **tập cạnh cụ thể** của sequence — thứ mà 4 con số của label không
nhìn thấy được. Hai sequence cùng `(end_node, arrival, K, W)` có thể có tập cạnh hoàn toàn
khác nhau → một cái có "khe hở hình học" cho order tiếp theo, cái kia không, dù label giống
hệt nhau ở 4 chiều đã chọn.

### 4.3 Bằng chứng thực nghiệm bác bỏ — [REJECTED], số liệu Test3

Chạy `BFS_PARETO` (giống BFS §2.1, nhưng level sau chỉ chèn từ `Pareto[P]`) trên đúng
29.056 subset đã có ground truth. Đo `VIOLATION` = tồn tại sequence trong `BRUTE_FORCE[S]`
mà `BFS_PARETO` không sinh ra được.

| lớp | subset | violation | rate |
|---|---|---|---|
| GW | 7.264 | 2.271 | **31,26%** |
| OD | 21.792 | 0 | 0,00% (không có ý nghĩa — OD gần như không có gì để mất, xem §5) |

**GW theo k:**

| k | subset | violation rate | deep violation (lan sang k+1) |
|---|---|---:|---:|
| 1 | 1.440 | 0% | — |
| 2 | 2.976 | 0% | — |
| 3 | 2.176 | **79,96%** | 848 (trong 1.740 violation ở k=3, ~48,7%) |
| 4 (=B) | 672 | **79,02%** | (không có level sau để kiểm) |

**Đọc kết quả:** violation tập trung đúng ở k=3,4 — đúng nơi compression có giá trị nhất
(vì `Seq(S)` lớn nhất ở đó). Compression tiềm năng rất hấp dẫn trên giấy (median
`|Pareto(S)|/|Seq(S)|` giảm còn 0,44% ở k=4) nhưng vô dụng vì gần 80% số lần dùng nó sẽ
làm mất completeness đúng ở chỗ cần nó nhất.

**Kết luận:** [REJECTED] dứt khoát theo ngưỡng tự đặt trước khi chạy (violation >1% = "không
hiếm" = không dùng được). Không thử lại nén-4-chiều theo cách này. Muốn nén phải tìm dominance
mang theo đủ thông tin hình học (tập cạnh, hoặc tương đương) — nhưng lúc đó label không còn
gọn để có lợi ích nén nữa; đây có thể chính là nội dung thật của câu hỏi T4.

### 4.4 Ghi chú thuật ngữ cần sửa khi viết tiếp

Thực nghiệm Test3 định nghĩa `K = load hiện tại`, `W = D_end - t0` (thời gian đã trôi qua) —
**khác** với `K, W` gốc trong model HICA-S (K = κ·distance là chi phí, W = active_route_time
là thời lượng tính phí). Với mục đích kiểm feasibility (không phải kiểm cost), `(arrival,
load)` mới là đại lượng đúng cần dùng — việc dùng nhầm tên `K,W` không đổi kết luận (dominance
theo bất kỳ vector rút gọn nào cũng dính đúng lỗi hình học ở §4.2), nhưng cần đổi tên biến
trước khi viết vào thesis để tránh nhầm với K,W kinh tế của model chính.

---

## 5. OD: bug data đã tìm và sửa — [VALIDATED, đã patch]

### 5.1 Bug gốc

`ready_time_pickup ~ U[0,120]` sinh độc lập với `t0` và `tau` → pickup thường sẵn sàng
**sau khi** `deadline_home = t0 + direct_time + tau` đã trôi qua. Hệ quả: OD chết ngay ở
k=1 (0,8–27,4% sống tùy tau), khiến toàn bộ Q2/Q3 của OD trong Test2 vô nghĩa.

### 5.2 Hai patch

```python
# Patch 1 — neo ready_time theo tau
ready_time_pickup = t0 + random.uniform(0, tau)

# Patch 2 — corridor-weighted P/D sampling (vì patch 1 chưa đủ, xem §5.3)
CORRIDOR_BUFFER_KM = 3.0    # [thiết kế, không phải giá trị khóa cứng — xem cảnh báo]
CORRIDOR_SHARE = 0.7        # 70% điểm P/D trong buffer quanh corridor start→home
```

### 5.3 Kết quả sau patch

| tau (phút) | feasibility_rate_k1 GỐC | +patch1 | +patch1+2 |
|---|---:|---:|---:|
| 15 | 0,8% | 3,9% | 6,5% |
| 30 | 5,1% | 17,2% | 34,5% |
| 60 | 27,4% | 53,3% | **67,2%** |

`tw_width` không ảnh hưởng (khớp cả trước/sau patch) — biến điều khiển feasibility của OD
là `tau`, không phải `tw_width`.

**Cảnh báo cần làm rõ trước khi tin `tau=15` là "giới hạn vật lý":** báo cáo Test3 kết
luận tau=15 không đạt ngưỡng 50% dù đã patch, và gọi đây là giới hạn hình học. Nhưng chỉ
một mức buffer (3km, 70%) được thử — **chưa loại trừ** khả năng buffer hẹp hơn cải thiện
thêm. Trước khi khóa kết luận này vào thesis, nên quét độ nhạy buffer (1km, 2km, 3km,
5km × vài mức share) ở đúng `tau=15` để biết đây thật sự là giới hạn của `tau` hay chỉ là
giới hạn của một lựa chọn buffer cụ thể.

### 5.4 Bundling OD sau patch — hiếm nhưng có thật, không còn 0 tuyệt đối

| tau | k=1 | k=2 | k=3 | k=4 |
|---|---:|---:|---:|---:|
| 30 | 58,8% | 2,6% | 0,0% | 0,0% |
| 60 | 71,3% | 22,4% | 1,7% | 0,01% |

So với Test2 gốc (max quan sát ở k≥2 = đúng 0 trên 205.440 subset), đây là thay đổi định
tính: OD **có** bundle ở k=2 (tau=60: 22,4%), nhưng bundling (k≥2) **vẫn hiếm**. Sau khi
loại hai nguồn lỗi đã biết, cách đọc hợp lý nhất là: đây là tính chất kinh tế thật của
detour budget (vài chục phút không đủ nhét 2+ cặp pickup-delivery), không phải lỗi data —
nhưng xem cảnh báo §5.3 trước khi khẳng định chắc.

---

## 6. Tổng kết trạng thái theo 3 câu hỏi gốc (Q1/Q2/Q3)

| Câu hỏi | Kết luận | Trạng thái |
|---|---|---|
| **Q1** BFS complete? | Có, tuyệt đối trong phạm vi đã kiểm | [VALIDATED] |
| **Q2** `|Seq(S)|` bị chặn nhỏ? | KHÔNG — bùng nổ tới trần lý thuyết ở GW, B≥3, TW≥60 | [VALIDATED] |
| **Q3** `slack_star` đủ mạnh để cứu Q2? | KHÔNG — catch rate cao (89%) nhưng đúng chỗ cần cắt nhất thì không có gì để cắt | [VALIDATED] |

---

## 7. Vấn đề mở — T4 CHƯA GIẢI [OPEN]

**Câu hỏi còn nguyên:** tìm một cận `LB(S)` sao cho:
1. Tính rẻ, **không cần enumerate sequence nào** của S.
2. Đơn điệu: `S ⊆ S' ⟹ LB(S) ≤ LB(S')` (hoặc dạng tương đương cho phép cắt cả cây con).
3. **Không dựa vào "đã biết S infeasible"** — phải bắt được cả trường hợp S feasible nhưng
   dẫn tới bùng nổ số sequence (đây là khác biệt với `slack_star`, vốn chỉ bắt được
   infeasibility, không bắt được "feasible nhưng nhiều biến thể").

**Điều §3.4 đã chứng minh:** không có bound nào chỉ dựa trên feasibility-đã-biết giải
quyết được câu hỏi này, vì bùng nổ xảy ra đúng ở vùng feasibility gần như tuyệt đối. T4
cần đo một đại lượng khác — có thể là "độ đa dạng hình học cần thiết" chứ không phải
"khả thi hay không".

**Hai điều đã biết KHÔNG dùng được (đừng thử lại):**
- Chọn 1 sequence đại diện theo bất kỳ scalar/vector nào (§2.4, §4).
- Nén Pareto trên `(end_node, arrival, load, elapsed)` (§4.3).

**Hướng đã đề xuất nhưng CHƯA CODE, CHƯA TEST (không được coi là kết quả):**
- Arc-charging (`p̃_j = s_j + ½min_in(j) + ½min_out(j)`, tính trên tập node cố định của
  driver, không phụ thuộc S) kết hợp với PMTN (Liu 2010, `1|pmtn,prec,r_j|L_max`, O(n²))
  làm cận `L_max` cho từng subset. Đây là hướng biến travel-time-phụ-thuộc-thứ-tự thành
  processing-time-cố-định để dùng được máy móc scheduling một-máy đã có sẵn công thức
  (Horn 1974; Baker, Lawler, Lenstra & Rinnooy Kan 1983). **Chưa kiểm chứng monotonicity
  của bound này trên dữ liệu thật, chưa kiểm chứng nó có bắt được ca bùng nổ ở §3.4 hay
  không.** Việc tiếp theo nếu theo hướng này: implement arc-charging + PMTN, chạy đúng
  gate completeness/monotonicity-counterexample-search như Test2 đã làm cho `slack_star`,
  trên đúng bộ instance đã bùng nổ (GW, B=4, tw_width≥60) để xem nó có cắt được gì không.

**Nếu hướng arc-charging+PMTN cũng thất bại:** theo go/no-go đã định trong đề cương gốc,
chuyển trọng tâm sang T5 (component decomposition cho counterfactual VCG payment) hoặc
chấp nhận giới hạn B≤2 cho GW như một ràng buộc mô hình tường minh, không phải thất bại
thuật toán.

---

## 8. File/code gốc (tham chiếu, không có trong hội thoại mới)

| File | Nội dung |
|---|---|
| `Guideline/Test2.md`, `Test3.md` | Spec gốc của hai vòng thực nghiệm |
| `Output/Test2/gate_summary.csv`, `small_raw.csv`, `big_raw.csv` | Dữ liệu thô Q1/Q2/Q3 |
| `Output/Test3/pareto_raw.csv`, `pareto_summary.txt` | Dữ liệu Pareto violation |
| `Output/Test3/od_patched_*.csv` | Dữ liệu OD sau 2 patch |
| `experiments/T2BFS/t2_core.py` | `is_feasible`, `validate`, `brute_force`, `bfs_generate`, `bfs_generate_pareto` |
| `experiments/T2BFS/t2_gen.py` | Sinh instance (đã patch OD) |

**Khi tiếp tục ở hội thoại mới:** dán file này làm ngữ cảnh, không cần dán lại toàn bộ
lịch sử hội thoại gốc. Mọi thứ đánh dấu [VALIDATED]/[PROVEN] có thể tin dùng ngay;
mọi thứ [OPEN] là việc cần làm; đừng thử lại bất kỳ điều gì đánh dấu [REJECTED] theo
đúng cách cũ mà không có ý tưởng mới thật sự khác.