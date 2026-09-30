# Test6 — Unified Forward Label-Setting DP (thay thế toàn bộ BFS level-wise)

**Mức độ rủi ro/tham vọng: CAO NHẤT trong toàn bộ chuỗi test.** Khác mọi test trước (vốn thử
compress một thành phần của BFS đã có), Test6 thử **thay thế toàn bộ cơ chế sinh route** bằng
một thuật toán khác hẳn. Nếu đúng, nó giải quyết dứt điểm T4 (cả phần giữa k=2..B-1, không chỉ
k=B). Nếu sai, gate sẽ chỉ ra chính xác chỗ gãy. **Không tin bất kỳ kết luận nào từ Test6 cho
tới khi Gate 1 pass tuyệt đối trên brute-force.**

**Đọc trước:** toàn bộ lịch sử [REJECTED] (Test3 Pareto, Test4 D2/D3 d≥2, Test5 UB1/UB2) — ý
tưởng Test6 khác về BẢN CHẤT sinh route, không phải một biến thể dominance khác trên cùng cơ
chế sinh cũ.

---

## 0. Ý tưởng cốt lõi và vì sao khác các lần trước

**Cơ chế sinh route CŨ (BFS hiện tại):** lấy `Seq(P)` (P là tập nhỏ hơn), CHÈN cặp
`(pickup_j, delivery_j)` vào một vị trí bất kỳ TRONG một sequence đã hoàn chỉnh của P — kể cả
vị trí "trước" các node đã cố định từ trước. Đây là phép **sửa lại quá khứ** của một route đã
có. Đã chứng minh (Test3/4/5): so sánh/loại route theo cách này giữa hai route khác nhau không
an toàn, vì thao tác "chèn giữa" có thể khai thác một cấu trúc cạnh mà route "tốt hơn" không có.

**Cơ chế sinh route MỚI (Test6):** không bao giờ sửa quá khứ. Route được xây bằng cách đi
**tuần tự đúng theo thời gian thực** — tại mỗi bước, chọn node tiếp theo để ghé (một pickup của
order chưa động tới, hoặc một delivery của order đang mang trên xe). Không có khái niệm "chèn
vào giữa" — muốn một order được ghé sớm, ta chỉ cần **chọn ghé nó sớm** ngay từ đầu, tạo thành
một nhánh riêng biệt trong cây tìm kiếm, không phải sửa một route đã có.

**Vì sao điều này làm dominance an toàn trở lại (lập luận, cần Gate 1 xác nhận):** hai trạng
thái quá trình xây route trùng nhau hoàn toàn về `(node hiện tại, tập order đang mang trên xe,
tập order đã giao xong)` sẽ đối mặt với **đúng cùng một tập lựa chọn tương lai** — vì tương lai
chỉ phụ thuộc "từ đây, còn có thể ghé đâu", không phụ thuộc "quá khứ cụ thể đã đi qua đâu". Nếu
một trạng thái tốt hơn hẳn (đến sớm hơn, chi phí thấp hơn, cùng tải trọng — tải trọng tự động
giống nhau vì cùng tập đang mang) thì trạng thái kia dư thừa cho **mọi phần mở rộng từ đây trở
đi**. Đây là dominance chuẩn của resource-constrained shortest path (Dumas, Desrosiers & Soumis
1991, *The pickup and delivery problem with time windows*, EJOR 54(1):7-22) — không phải phát
minh mới, nhưng **áp dụng đúng cách cho bài toán cụ thể này chưa được kiểm chứng**, và điểm khác
biệt so với các label đã REJECTED (Test3 §4, Test4 D2/D3) là: label ở đây bao gồm **chính xác
tập order đang mang + tập đã giao**, không phải một vài con số tóm tắt (arrival, K, W) như
trước — hai route "trông giống 4 con số" nhưng khác tập order đang mang được coi là **khác
trạng thái**, không so sánh với nhau.

---

## 1. Định nghĩa trạng thái (state)

```
Label = ( v,           # node hiện tại
          IV,          # tập order đang mang trên xe (đã pickup, chưa delivery)
          C,            # tập order đã giao xong (cả pickup lẫn delivery)
          t,            # thời điểm hiện tại (sau service_time tại v)
          K,            # chi phí quãng đường tích luỹ (κ · distance)
          W )           # thời lượng tính phí tích luỹ (theo đúng công thức §2.2 model gốc)
```

Ràng buộc bắt buộc: `|IV| + |C| ≤ B` tại mọi thời điểm (không vượt bundle cap).

**Với GW:** không có `home`. Một label là "bundle hoàn chỉnh hợp lệ" khi `IV = ∅` và
`1 ≤ |C| ≤ B` — chính C là bundle, K/W tính đúng công thức GW (toàn tuyến, §2.2 đề cương gốc).

**Với OD:** phải thêm bước bắt buộc ghé `home` sau khi `IV = ∅`. Một label là "hoàn chỉnh" khi
`v = home` và `IV = ∅`. K/W tính theo công thức OD (incremental so với direct trip, §2.2).

### 1.1 Transition (bước chuyển)

Từ `Label(v, IV, C, t, K, W)`:

```
(a) Pickup order j, với j ∉ IV ∪ C, |IV|+|C| < B, và order j "reachable" (đã có từ Test2):
    v' = pickup_node(j)
    t' = max(t + travel(v,v') , ready_time(v')) + service_time(v')
    NẾU t' > deadline(v'): loại nhánh này (infeasible)
    IV' = IV ∪ {j},  C' = C
    K' = K + κ·dist(v,v'),  W' += (theo công thức §2.2, xem §1.3)

(b) Delivery order j, với j ∈ IV:
    v' = delivery_node(j)
    (tương tự tính t', kiểm deadline, kiểm capacity — luôn thoả vì demand đã trừ khi giao)
    IV' = IV \ {j},  C' = C ∪ {j}

(c) [chỉ OD, khi IV=∅] Đi về home:
    v' = home
    kiểm t' ≤ deadline_home = t0 + direct_time(start→home) + tau
```

### 1.2 Dominance — điều kiện SOUND cần Gate 1 xác nhận

```
Label_a ⪰ Label_b  ⟺  v_a = v_b  AND  IV_a = IV_b  AND  C_a = C_b
                       AND  t_a ≤ t_b  AND  K_a ≤ K_b  AND  W_a ≤ W_b
                       (ít nhất một bất đẳng thức strict để loại b)
```

Khi hai label có cùng `(v, IV, C)`: tải trọng đã tự động bằng nhau (do `IV` giống hệt nhau).
Nếu `Label_a ⪰ Label_b`, xoá `Label_b` — theo lập luận §0.

**Vì sao đây khác các lần REJECTED:** D2/D3 (Test4) so sánh route CÙNG một tập S nhưng khác thứ
tự nội bộ — nghĩa là cùng `C`, nhưng có thể khác `v` (kết thúc ở node khác) và luôn `IV = ∅` cả
hai vì đã "xong". Ở đó dominance chỉ nhìn 4 con số tóm tắt, không nhìn "con đường cụ thể đã đi",
nên mất thông tin về khả năng chèn giữa. Ở đây, hai label cùng `(v, IV, C)` có thể đến từ **thứ
tự nội bộ khác nhau** (ví dụ đến `P2` sau khi đã pickup theo thứ tự O1 hay O3 trước), nhưng vì
`v` và `IV, C` giống hệt, **không tồn tại khái niệm "chèn giữa"** để phân biệt tương lai của
chúng — tương lai chỉ phụ thuộc đúng ba thứ đó.

### 1.3 Công thức K, W — khớp đúng model gốc, không tự chế

Dùng nguyên công thức từ đề cương/reference (không định nghĩa lại):
```
GW:  K = κ · total_route_distance,  W = active_route_time / 60
OD:  K = κ · max(0, detour_distance),  W = max(0, detour_time) / 60
     (detour = so với direct trip start→home)
```
Với OD, `K, W` chỉ tính được đầy đủ **sau khi** đã biết toàn bộ route + đã về home — trong lúc
DP đang chạy giữa chừng, tích luỹ `K, W` theo từng cạnh là tích luỹ **quãng đường/thời gian
thô**, trừ đi phần `direct_time`/`direct_distance` **một lần duy nhất khi hoàn thành** (không
trừ dần từng bước — tránh sai số cộng dồn). Ghi rõ điểm này trong code, đây là chỗ dễ lẫn.

---

## 2. Việc 1 — ★★★ GATE EXACTNESS (bắt buộc, nghiêm ngặt hơn mọi gate trước)

Đây là gate quan trọng nhất của toàn bộ chuỗi test. Không chuyển sang Việc 2 nếu chưa pass
tuyệt đối.

### 2.1 Cách chạy

Trên **toàn bộ** grid nhỏ đã có ground truth (n≤6, B≤4, class∈{GW,OD}, mọi tw_width/tau):

```
for mỗi instance:
    run_dp(driver, orders, B) → Front_DP = { mọi label hoàn chỉnh còn sống sót sau dominance,
                                              gộp theo mọi kích thước |C| từ 1 đến B }

    for mỗi subset S, |S| = 1..B (đã có Seq(S) từ Test2/brute-force làm ground truth):
        bundle_exists_DP    = tồn tại ít nhất 1 label hoàn chỉnh với C = S?
        bundle_exists_TRUTH = |Seq(S)| > 0 ?  (Test2 ground truth)

        pareto_DP    = { (K,W) của mọi label hoàn chỉnh với C=S, không bị dominate lẫn nhau }
        pareto_TRUTH = { (K,W) Pareto-optimal của Seq(S), tính từ brute-force }
```

### 2.2 Ba gate con — TẤT CẢ bắt buộc = 0 vi phạm tuyệt đối

```
Gate 1.A (bundle completeness):
    bundle_exists_DP == bundle_exists_TRUTH  ∀ S, ∀ instance
    → vi phạm nếu DP nói "không tồn tại" mà thực ra tồn tại, HOẶC ngược lại (nếu DP báo tồn
      tại bundle infeasible thì đó là lỗi feasibility check, nghiêm trọng hơn, dừng ngay)

Gate 1.B (Pareto completeness — SO VỚI GROUND TRUTH ĐỘC LẬP, không so DP với chính DP):
    ∀ điểm p ∈ pareto_TRUTH, ∃ điểm p' ∈ pareto_DP với K'≤K, W'≤W (dung sai 1e-9)
    → vi phạm nếu DP làm mất một điểm Pareto-optimal thật

Gate 1.C (Pareto soundness — không được "ảo giác" ra điểm tốt hơn thật):
    ∀ điểm p' ∈ pareto_DP, phải tồn tại MỘT sequence khả thi thật (kiểm bằng is_feasible()
    gốc của Test2, KHÔNG phải feasibility check tự viết trong t6_dp.py) đạt đúng (K',W') đó
    → vi phạm nếu DP báo cáo (K,W) không có sequence thật nào đạt được (lỗi tích luỹ K/W,
      đặc biệt nguy hiểm với công thức detour của OD, xem §1.3)
```

**Nếu BẤT KỲ gate nào fail dù chỉ 1 lần: DỪNG NGAY, in phản ví dụ đầy đủ** (instance seed, S,
label path đầy đủ dẫn tới điểm sai, so sánh với sequence brute-force tương ứng). Không chạy
Việc 2, không diễn giải, không "tỷ lệ nhỏ chấp nhận được" — đây là gate đúng/sai tuyệt đối,
giống Test2 §1, không phải gate thống kê.

### 2.3 Kiểm tra riêng: dominance áp dụng GIỮA CHỪNG có an toàn không

Đây là phép kiểm bổ sung, tách biệt khỏi 2.2, nhắm đúng vào giả thuyết mới nhất (dominance an
toàn ngay cả khi `IV ≠ ∅`, không chỉ khi đã hoàn thành):

```
Chạy 2 phiên bản DP song song:
    DP_full:   KHÔNG áp dụng dominance ở bất kỳ đâu — giữ MỌI label (kể cả label bị "thống trị")
    DP_prune:  áp dụng dominance (§1.2) ngay khi có thể, xuyên suốt quá trình

So sánh: mọi label HOÀN CHỈNH mà DP_full tìm được, DP_prune có tìm được một label hoàn chỉnh
với (C giống hệt, K≤, W≤) hay không?
```

**Đây chính là câu hỏi trung tâm của toàn bộ Test6** — nếu Gate này pass tuyệt đối, giả thuyết
ở `§0` được xác nhận thực nghiệm: dominance áp dụng NGAY CẢ KHI route chưa hoàn thành (`IV≠∅`)
vẫn an toàn, khác hẳn kết luận đã có ở Test4 Việc 4 (dominance giữa các route **đã hoàn thành**
của các tập S khác nhau thì KHÔNG an toàn). Ghi rõ trong report: đây là điểm phân biệt quan
trọng nhất — Test6 không mâu thuẫn với Test4, vì chúng dominance ở hai loại đối tượng khác nhau
(label giữa chừng của MỘT quá trình xây dựng liên tục, và route đã-xong của các tập KHÁC NHAU).

---

## 3. Việc 2 — chỉ chạy nếu Việc 1 pass tuyệt đối: đo state space thật

```
n_states_visited(instance)      = tổng số label DP_prune từng tạo ra (trước và sau dominance)
n_states_survived(instance)     = số label còn sống sau dominance tại từng thời điểm
n_states_theoretical_upper      = Σ_{k=0}^{B} C(m,k) · 2^k   (m = |reachable_orders|)
```

So sánh `n_states_visited` với tổng `n_feasible_sequences` mà Test2 đã đo (bùng nổ tới 2520 ở
k=4/tw=240). Kỳ vọng: `n_states_visited ≪ n_feasible_sequences` vì dominance cắt bớt xuyên
suốt, không chỉ ở cuối.

**Ba ô trọng tâm giống Test4/Test5** (GW, B=4, k=3-4, tw∈{120,240}) — đo tại đây trước tiên.

---

## 4. Việc 3 — chỉ chạy nếu Việc 2 cho tín hiệu tốt: đo thời gian thật (wall-clock)

```
t_DP(instance)          = thời gian chạy toàn bộ DP (một lượt, sinh MỌI bundle 1..B cùng lúc)
t_BFS_current(instance) = thời gian BFS hiện tại (Test2, chạy hết k=1..B) trên CÙNG instance
speedup = t_BFS_current / t_DP
```

Chạy ở cả n≤6 (đối chứng) và **n=10, n=15** (theo đúng bài học Test4.1 — không tin số đo ở n
nhỏ). Đây là con số quyết định Test6 có đáng thay thế Algorithm A hiện tại hay không.

---

## 5. Grid và tham số

Giống hệt Test2-5, không đổi:
```
n_orders: {3,4,5,6} (Việc 1, bắt buộc đủ) · {10,15} (Việc 3)
B: {2,3,4}
tw_width: {30,60,120,240}
tau: {15,30,60} (OD, generator đã patch, chỉ cell đạt feasibility_rate_k1≥0.5)
SEEDS_PER_CELL: 8 (Việc 1) · 3 (Việc 3, theo tiền lệ Test4.1)
```

---

## 6. Thứ tự thực thi — TUYỆT ĐỐI không nhảy bước

```
Việc 1 (Gate 1.A, 1.B, 1.C, và §2.3)  →  BẤT KỲ vi phạm nào  ⟹  DỪNG NGAY
                                          Không kết luận "gần đúng". Tìm cho ra lỗi:
                                          - Lỗi feasibility check (transition sai)?
                                          - Lỗi công thức K/W (đặc biệt OD detour, §1.3)?
                                          - Dominance thực sự KHÔNG sound (giả thuyết §0 sai)?
                                          → Phải phân loại được lỗi thuộc nhóm nào trước khi
                                            quyết định sửa code hay từ bỏ hướng tiếp cận.
    ↓ pass tuyệt đối (đây là kịch bản hy vọng, KHÔNG phải kịch bản mặc định)
Việc 2  →  n_states_visited vẫn xấp xỉ n_feasible_sequences cũ (không nén được gì)
           ⟹  dominance kỹ thuật đúng nhưng vô dụng thực tế, ghi nhận, dừng
    ↓ nén được đáng kể
Việc 3  →  đo speedup thật ở n=10,15  →  quyết định thay thế Algorithm A hay không
```

---

## 7. Những điều KHÔNG được làm

1. **Không** dùng `is_feasible()` tự viết riêng cho Test6 làm ground truth — Gate 1.C bắt buộc
   đối chiếu với `is_feasible()` gốc đã dùng xuyên suốt Test2-5. Hai bên phải là hai cài đặt
   độc lập kiểm tra lẫn nhau, không phải cùng một hàm gọi hai lần.
2. **Không** kết luận dominance "chắc đúng vì lý thuyết đã có" — Dumas et al. 1991 chứng minh
   cho một class bài toán cụ thể; việc **map đúng** bài toán HICA-S (đặc biệt: bundle cap B như
   một ràng buộc SỐ LƯỢNG order touched, không phải ràng buộc kiểu VRPTW thông thường; công
   thức detour riêng cho OD) vào đúng khuôn của lý thuyết đó là việc CẦN KIỂM, không phải suy
   diễn.
3. **Không** bỏ qua §2.3 (kiểm dominance giữa chừng) — đây là phép kiểm phân biệt trực tiếp
   giữa "Test6 đúng như kỳ vọng" và "Test6 mắc đúng lỗi cũ nhưng nguỵ trang khác đi". Nếu bỏ
   qua bước này mà chỉ kiểm Gate 1.A/B/C, có rủi ro pass giả nếu bug che lấp bug.
4. **Không** trộn lẫn `K, W` tích luỹ thô với công thức detour cuối cùng của OD — đây là lỗi
   dễ mắc nhất (nêu rõ ở §1.3), và một lỗi ở đây có thể làm Gate 1.C fail vì lý do hoàn toàn
   khác với việc dominance sai.
5. **Không** vội kết luận "Test6 thay thế được Algorithm A" chỉ từ Việc 1 pass — phải đủ cả
   Việc 2 (nén thật) và Việc 3 (nhanh thật ở n lớn) mới đủ căn cứ thay đổi kiến trúc.

---

## 8. Báo cáo cần trả về

`Test6_report.md`:

1. Sai lệch so với spec (nếu có), công khai ngay đầu.
2. Kết quả Gate 1.A/1.B/1.C — pass/fail tuyệt đối. **Nếu fail, đây là phần quan trọng nhất của
   report**: phản ví dụ đầy đủ, phân loại nguyên nhân (lỗi cài đặt vs lỗi giả thuyết), và đánh
   giá liệu lỗi có sửa được hay giả thuyết `§0` bị bác bỏ hoàn toàn.
3. Kết quả §2.3 (dominance giữa chừng) — đây là câu trả lời trực tiếp cho câu hỏi mở đầu hội
   thoại dẫn tới Test6.
4. Nếu Việc 1 pass: bảng state space (Việc 2) và thời gian thật (Việc 3), theo đúng 3 ô trọng
   tâm quen thuộc.
5. Kết luận: Test6 có thay thế được Algorithm A hiện tại hay không, và nếu có, phạm vi nào
   (n, B, tw_width nào) đã được xác nhận — không ngoại suy ra ngoài phạm vi đã đo.