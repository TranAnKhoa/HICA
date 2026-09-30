# Test B — Hull Filtering tại DP Intermediate State (Supported-Solutions Framing)

> Test A (post-hoc, trên route đã hoàn thành) đo redundancy ở OUTPUT cuối — không đo được
> liệu hull có cắt label TRONG LÚC DP chạy, đúng nơi T4 thật sự nghẽn (631,024 label ở hot
> cell). Test B sửa DP thật để đo đúng câu hỏi đó. KHÔNG có điều kiện "chỉ làm nếu Test A
> ≥20%" — Test A và Test B đo hai đại lượng khác nhau, kết quả Test A thấp không dự đoán
> được kết quả Test B (hiệu ứng cắt sớm nhân dồn qua nhiều tầng DP).

**Nhãn:** `[LOCK]` = cố định; `[IMPLEMENT]` = cần code; `[CHECK]` = gate bắt buộc;
`[THEORY]` = phần lý thuyết cần viết chính thức vào luận văn, không chỉ chạy số.

---

## 0. Nền tảng lý thuyết — đọc trước khi code (đây là phần nâng T4 lên một bậc)

Khái niệm đang dùng có tên chính thức trong multi-objective combinatorial optimization:
- **Supported efficient solution**: điểm Pareto-optimal đạt được bởi weighted-sum/linear
  scalarization `min{w1·K + w2·W}` với một `w ≥ 0` nào đó — tương đương điểm nằm trên lower
  convex hull của Pareto front.
- **Unsupported efficient solution**: Pareto-optimal nhưng KHÔNG đạt được bởi bất kỳ linear
  scalarization nào — nằm "lõm vào trong" so với hull.

Tài liệu nền: Ehrgott, M. (2005) *Multicriteria Optimization*, Springer — chương về
supported/unsupported. Thuật toán tìm supported points trực tiếp (không cần liệt kê hết
Pareto set trước): "Dichotomic Approach", phát hiện độc lập bởi Aneja & Nair (1979), Cohen
(1978), Dial (1979) — xem tổng hợp trong Bökler, F. (2018) *Output-sensitive Complexity of
Multiobjective Combinatorial Optimization Problems*.

### `[THEORY]` Proposition — viết chính thức vào luận văn, không chỉ ghi trong log thí nghiệm

> **Proposition (Supported Completeness Suffices).** Reported cost của mọi route là hàm
> affine theo bid: `c_ir(b_i) = K_ir + b_i·W_ir`. Mọi nơi trong pipeline dùng route pool
> (Algorithm B, mọi removal-solve của Algorithm C, mọi phương án deviation trong DSIC audit
> §9.4) đều chọn route bằng cách minimize đúng hàm affine này tại một `b_i ≥ 0` cụ thể. Do
> đó, với mỗi (driver, bundle), Algorithm A chỉ cần sinh **supported efficient points**
> (điểm trên convex hull của tập (K,W) khả thi) — unsupported efficient point không bao giờ
> là argmin của `K+b·W` với bất kỳ `b≥0`, nên bỏ qua chúng không ảnh hưởng DSIC, IR, hay
> optimality của mechanism.
>
> **Hệ quả (Gate mới):** completeness gate ở §7.5 đề cương ("n≤6 phải khớp brute-force
> 100%") **chặt hơn mức toán học cần thiết** — chỉ cần khớp **hull của brute-force**, không
> cần khớp toàn bộ Pareto set của brute-force.

Proof 3 dòng: (i) x* tối ưu của WDP luôn chọn, cho mỗi (driver,bundle) được dùng, route rẻ
nhất theo `K+b_i·W_ir` — đây là định nghĩa supported point. (ii) `Z*_{-i}` dùng cùng bid
vector (chỉ khác driver i bị loại) — cùng lập luận. (iii) DSIC audit (§9.4) chỉ thử các
`b_i'` khác nhau, mỗi lần vẫn chỉ query argmin theo affine cost — không có bước nào trong
toàn bộ pipeline từng cần một route không phải supported point.

## 1. Input cần có sẵn

- `dp_labeling.py` hiện tại — sẽ SỬA trực tiếp (không phải post-process như Test A).
- Đúng hot cell đã dùng ở Test A: n=20, B_gw=4, tw=240, n_drivers=5 — GIỮ NGUYÊN để so sánh
  được với peak_frontier=631,024 đã đo trước.
- Định nghĩa key dominance hiện tại (driver, vị trí hiện tại, tập order đã pickup, tập đã
  giao) — dùng lại NGUYÊN, chỉ thêm bước lọc sau bước Pareto filter đã có.

## 2. `[IMPLEMENT]` Sửa DP — thêm hull filter tại mỗi state

Vị trí sửa: ngay sau bước `_pareto_front()` hiện có trong `dp_labeling.py`, TRƯỚC khi mở
rộng sang state kế tiếp (đúng round-based procedure đã mô tả trong
`Lemma_TestC_and_AlgorithmA.tex`).

```python
def hull_filter_on_pareto(pareto_labels):
    """
    pareto_labels: list các label đã qua Pareto filter, mỗi label có (K, W) tích luỹ tới
    state hiện tại (không phải route hoàn chỉnh — đây là partial cost tới state này).
    Trả về subset chỉ gồm supported points (trên lower convex hull).

    Dùng lại ĐÚNG hàm lower_hull_on_pareto() đã viết và audit ở Test A/v2 —
    không viết lại từ đầu, tránh lặp lại bug turns_right() đã sửa.
    """
    if len(pareto_labels) <= 2:
        return pareto_labels  # không đủ điểm để hull loại gì
    sorted_labels = sorted(pareto_labels, key=lambda l: (l.K, l.W))
    return lower_hull_on_pareto(sorted_labels)  # import từ convex_hull_test_v2.py, đã audit


# Trong vòng lặp round-based hiện tại của dp_labeling.py:
for state_key, labels_at_state in current_round_states.items():
    pareto_labels = _pareto_front(labels_at_state)          # bước đã có, KHÔNG đổi
    surviving_labels = hull_filter_on_pareto(pareto_labels)  # BƯỚC MỚI
    # chỉ surviving_labels được mở rộng sang round kế tiếp
```

**Đo trước/sau, tại MỌI round, không chỉ round cuối:**
```python
frontier_sizes_before_hull = []  # sau Pareto filter, trước hull
frontier_sizes_after_hull = []   # sau hull filter

# log tại mỗi round:
frontier_sizes_before_hull.append(sum(len(v) for v in pareto_by_state.values()))
frontier_sizes_after_hull.append(sum(len(v) for v in hull_by_state.values()))
```

Báo cáo: peak frontier trước/sau (so trực tiếp với 631,024 đã biết), và đường cong frontier
size theo round (biết hull có giúp đều hay chỉ giúp ở vài round cụ thể).

## 3. `[CHECK]` Gate — ĐÃ SỬA theo Proposition ở §0 (khác gate cũ)

Gate cũ (đã dùng ở Test A/v2): so route pool đã hull-prune với **hull của brute-force**.
Đây **chính là gate đúng** theo Proposition — giữ nguyên, không đổi:

```python
def gate_n6_hull_vs_bruteforce_hull(instance_n6, hull_pruned_pool, driver):
    """
    So sánh với HULL của brute-force, KHÔNG phải toàn bộ Pareto set của brute-force.
    Đây là điểm khác biệt quan trọng: nếu so với toàn bộ Pareto set, gate sẽ luôn "fail"
    một cách vô nghĩa (vì hull filter CỐ Ý bỏ unsupported point) — không phải bug.
    """
    bf_pool = brute_force_routes(instance_n6, driver)  # dùng lại logic đã có §7.5
    bf_by_bundle = defaultdict(list)
    for r in bf_pool:
        bf_by_bundle[r['bundle']].append((r['K'], r['W']))

    for bundle, bf_pts in bf_by_bundle.items():
        bf_hull = lower_hull_on_pareto(pareto_filter([(k,w,None) for k,w in bf_pts]))
        pruned_at_bundle = [(k,w) for k,w in hull_pruned_pool if matches(bundle)]

        for k, w, _ in bf_hull:
            if (k, w) not in pruned_at_bundle:
                print(f"[FAIL] Bundle {bundle}: brute-force HULL point ({k},{w}) thiếu!")
                return False
    print("[PASS] Mọi supported point brute-force đều có mặt.")
    return True
```

`[CHECK]` **Bổ sung — kiểm tay độc lập bắt buộc, đúng thói quen đã có giá trị ở vòng trước:**
với 5 group (state) có nhiều điểm nhất, quét brute-force numeric `b` từ 0 đến giá trị lớn
(theo đúng cách đã bắt bug `turns_right()` trước) để xác nhận KHÔNG có supported point nào
bị `hull_filter_on_pareto()` bỏ sót ở tầng INTERMEDIATE (khác Test A vốn kiểm ở route hoàn
chỉnh) — đây là phép kiểm MỚI, chưa làm, vì logic hull ở state trung gian dùng partial
(K,W) chứ không phải route cost cuối cùng, có thể có edge case khác.

## 4. Việc PHẢI báo cáo, phân biệt rõ với Test A

| Đại lượng | Test A (đã có) | Test B (file này) |
|---|---|---|
| Đo ở đâu | Route hoàn chỉnh (output cuối DP) | Mỗi state trung gian, mọi round |
| Ý nghĩa reduction | Redundancy trong route pool cuối | **Tăng tốc DP thật** (ít label hơn cần mở rộng) |
| Kỳ vọng | 10-27% (đã đo, 8 seed) | Có thể khác hẳn — hiệu ứng nhân dồn qua nhiều round |
| Gate | Không bắt buộc (không implement) | **Bắt buộc trước khi implement** |

Không suy diễn kết quả Test B từ Test A — báo cáo Test B như một thí nghiệm độc lập.

## 5. Interpretation

| Peak frontier reduction (Test B) | Gate §3 | Quyết định |
|---|---|---|
| Đáng kể (ví dụ ≥30%, hoặc runtime hot cell giảm rõ) | PASS | Implement chính thức vào `dp_labeling.py`, viết Proposition (§0) + kết quả vào phần T4 chính thức |
| Đáng kể | **FAIL** | Không implement, tìm lại bug (ưu tiên: logic partial-cost tại state trung gian có khác route cost cuối theo cách nào đó chưa tính tới) |
| Nhỏ (tương tự hoặc thấp hơn Test A) | — | Vẫn giữ Proposition §0 (đúng bất kể % — nó là toán học, không phụ thuộc thực nghiệm), nhưng đóng góp T4 chủ yếu dựa vào Proposition + lower-bound, không phải vào speedup thực tế |

**Quan trọng: dù Test B ra sao, Proposition ở §0 vẫn ĐÚNG và ĐÁNG viết vào luận văn** — nó
là một correction toán học cho định nghĩa completeness, độc lập với việc thực nghiệm có cho
speedup hay không. Đây là phần "chắc ăn" của cả thí nghiệm này, không phụ thuộc con số.

## 6. Nhắc lại về EJOR — không tự động chỉ vì Test B thành công

Theo đúng §14 đề cương: EJOR cần CẢ (a) T4/T5 mạnh VÀ (b) RQ1 đáng kể. Test B + Proposition
§0 (nếu tốt) nâng đáng kể phần (a) — nhưng không thay thế được RQ1. Ưu tiên vẫn: chạy Test B
xong, tiếp tục RQ1 theo `RQ1_execution_spec.md` đã khoá, không trì hoãn RQ1 để tối ưu thêm
T4.