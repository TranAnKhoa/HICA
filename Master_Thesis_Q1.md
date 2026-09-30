# HICA-S v4 — Truthful Procurement for Three-Class Last-Mile Fleets

## Đề cương master thesis hướng tới một bài báo Q1

**Tên đề xuất (EN):** *Truthful Route-Bundle Procurement with Gigworkers and Occasional
Drivers in Hybrid Last-Mile Fleets*

**Tên đề xuất (VN):** Cơ chế mua dịch vụ giao hàng theo route-bundle có tính khuyến khích
tương thích cho đội xe hỗn hợp gigworker – occasional driver – fixed capacity

---

## Changelog v3 → v4 (đọc trước, vì bốn thay đổi này đổi cả định vị)

| # | Thay đổi | Lý do |
|---|---|---|
| **C1** | **Đổi taxonomy sang GW / OD / FD**, bỏ cách gọi "DD" và bỏ từ "hybrid" trong tên | Luy, Hiermann & Schiffer (POM 2024) đã thiết lập đúng taxonomy ba lớp này (fixed drivers + gigworkers destination-insensitive + occasional drivers destination-constrained). Bám theo họ mạnh hơn là tự đặt tên. Ngoài ra Li & Zhang **đã dùng** từ "hybrid crowdshipping system" cho nghĩa khác (crowd + dedicated), sẽ va chạm thuật ngữ |
| **C2** | **Sửa ô sai trong bảng literature**: Li & Zhang **CÓ** platform-side bundle generation | Section 3.2 của họ tên là "Bundle Generation and Bid Construction": platform nhận cost function + baseline routes, tự xác định tập bundle khả thi bằng cách giải PDP cho từng candidate, cắt nhánh theo bundle size limit và tính đơn điệu không gian của detour time. Carrier **không** tự liệt kê bundle. Ô cũ ghi ngược lại — reviewer sẽ bắt trong năm phút |
| **C3** | **Thêm Zou & Kafle (2022) vào bảng**, và hạ Theorem 3 khỏi contribution | Họ đã có exact VCG + Clarke pivot trên column pool do platform sinh, bid-independent, có backup, type 4 chiều, chứng minh DSIC trực tiếp. Phần *mechanism* của HICA-S không mới so với bài này. Phần *market structure* (hai lớp cùng bid) thì mới — họ chỉ có một lớp strategic |
| **C4** | **Dời trọng tâm kỹ thuật sang Algorithm A**, cụ thể là bài toán sinh bundle open-route không có anchor | Đây là chỗ **duy nhất** GW và OD thực sự khác nhau về mặt toán học. Ở tầng cơ chế chúng không phân biệt được — xem §4.2 |

**Thay đổi mang tính nguyên tắc:** v3 đặt novelty ở "hai lớp strategic ⇒ mechanism mới".
v4 bác bỏ điều đó (§4.2) và đặt novelty ở **một thành phần kỹ thuật không tầm thường**,
theo đúng chuẩn mà Li & Zhang đã dùng để vào TS (họ cũng không phát minh lý thuyết cơ
chế mới — họ có setting + một biến thể greedy của Lehmann et al. 2002 + regret bound).

---

## 0. Executive handoff

**Bài toán một câu:** trong một phiên điều phối tĩnh, platform tự sinh route-bundle từ
order nguyên tử cho hai lớp tài xế strategic có hình học tuyến khác nhau — **GW** chạy
open route, **OD** chỉ detour quanh chuyến cá nhân — rồi chọn allocation chung và trả
exact VCG payment trên một route range cố định trước bid, với **FD** (fixed capacity)
làm outside option giá công khai.

**Input tối thiểu:** orders + time windows; trạng thái/capacity công khai của tài xế; OD
destination + detour commitment; travel matrix xác định; hệ số quãng đường công khai
κ; một scalar bid (cost-unit/giờ) từ mỗi tài xế; FD cost công khai cho từng order.

**Output tối thiểu:** route pool cố định; route-bundle được chọn cho GW/OD; order chuyển
FD; objective chính xác; exact Clarke-pivot payment và utility mô phỏng của từng winner;
audit solver/provenance đầy đủ.

**Bốn điều kiện sống còn của theorem** (vi phạm một là mất quyền claim DSIC):
1. Route generation **không nhìn bid**.
2. Base solve và mọi removal solve dùng **đúng cùng** route range.
3. Base solve và mọi removal solve đều **exact** (OPTIMAL, gap chứng nhận = 0).
4. Private message chỉ là **một scalar**.

---

## 1. Taxonomy và ranh giới ba lớp

Bám theo Luy, Hiermann & Schiffer (POM 2024, 33(11):2177–2200), vốn đã tách rõ ba lớp
trong đội xe last-mile:

| Lớp | Ký hiệu | Hình học tuyến | Strategic? | Type riêng tư |
|---|---|---|---|---|
| **Gigworker** | GW | Open route: xuất phát từ vị trí hiện tại, kết thúc ở điểm giao cuối. **Không nhạy cảm với destination** | ✓ | θ_i scalar (cost-unit/h) |
| **Occasional driver** | OD | Destination-constrained: phải kết thúc tại personal destination, ràng buộc bởi detour budget | ✓ | θ_i scalar (cost-unit/h) |
| **Fixed capacity** | FD | — (không định tuyến trong mô hình) | ✗ | Giá công khai q_o |

Luy et al. nghiên cứu bài toán **strategic workforce planning** trên đúng ba lớp này:
chân trời dài (một năm), bất định về availability của crowd, **chi phí tài xế là input
đã biết**, dispatch tập trung, không có cơ chế elicit.

HICA-S lấy **đúng taxonomy đó** nhưng hỏi câu hỏi ở tầng **operational-tactical** dưới
**thông tin chi phí riêng tư**: trong một phiên điều phối, mua dịch vụ thế nào để khai
báo trung thực là chiến lược tối ưu?

Đây là định vị mạnh hơn hẳn "chúng tôi phát minh cấu trúc ba lớp" — cấu trúc đó đã có,
và việc nó đã được publish ở POM là **bằng chứng** rằng nó có giá trị vận hành thật.

---

## 2. Problem statement

### 2.1 Input

Trong một batch tĩnh:
- tập order O, mỗi order có pickup, delivery, demand, time windows, release time;
- tập gigworker G (vị trí bắt đầu, availability, capacity);
- tập occasional driver C (origin, **personal destination**, direct trip, **max detour**,
  availability, capacity);
- FD cost q_o công khai cho từng order;
- travel matrix xác định;
- bundle cap B (ví dụ 2, 3);
- hệ số quãng đường κ_i công khai/hợp đồng.

Mỗi tài xế i có **một** private type scalar θ_i. Chi phí thực khi i chạy route r:

```
C_ir(θ_i) = K_ir + θ_i · W_ir
```

K_ir (cost-unit) và W_ir (giờ) do platform tính từ route và dữ liệu công khai. Tài xế
báo b_i thay cho θ_i. Reported cost mà WDP nhìn thấy là `c_ir(b_i) = K_ir + b_i·W_ir`.

### 2.2 Hai công thức (K, W) theo lớp

**GW** — open route, tính trên toàn bộ tuyến:
```
K_ir = κ_i · total_route_distance_ir
W_ir = active_route_time_ir / 60
```

**OD** — incremental so với chuyến cá nhân trực tiếp:
```
detour_distance_ir = route_distance_ir − direct_distance_i
detour_time_ir     = route_time_ir   − direct_time_i
K_ir = κ_i · max(0, detour_distance_ir)
W_ir = max(0, detour_time_ir) / 60
```

### 2.3 Quyết định

Cơ chế quyết định đồng thời: bundle nào tồn tại; thứ tự pickup–delivery của mỗi bundle;
tài xế nào nhận bundle nào; order nào chuyển FD; payment cho từng winner.

### 2.4 Mục tiêu

Tối thiểu hóa tổng reported procurement cost cộng FD cost, trên toàn bộ feasible route
range đã công bố. Payment rule phải bảo đảm DSIC (single-parameter), IR cho winner, và
range-efficiency.

**Không** claim budget balance vô điều kiện. Có kết quả để dựa: Li & Zhang chứng minh
weak budget balance khi customer fare f_j = q_j, và strong budget balance khi f_j ≥ q_j
với ít nhất một bất đẳng thức strict. Nêu điều kiện, đừng nêu vô điều kiện.

---

## 3. Bảng định vị (đã sửa)

| Nghiên cứu | GW/open-route strategic | OD/detour strategic | FD/backup | Bundle từ đâu | Cơ chế IC | Khoảng cách tới HICA-S |
|---|---|---|---|---|---|---|
| Archetti et al. (2016) | Company fleet, cost đã biết | Có OD, không bid | — | — | Không | Nền route geometry của OD |
| **Zou & Kafle (2022)** | **Không** — một lớp crowdsourcee | Có, nhưng **mọi đơn xuất phát từ depot** (bài con là TSP) | Backup vehicle, non-strategic | **Platform sinh, branching** | **Exact VCG + Clarke pivot, DSIC, type 4 chiều** | **Chặn phần mechanism**: exact VCG trên platform-generated pool đã có. Không chặn market structure |
| Triki (2021) | Company fleet, không bid | OD submit bundle bids | — | Có | Không có IC proof | Đã ghép fleet + OD auction + routing nhưng payment không truthful |
| Mancini & Gansterer (2022) | Không | Có OD | — | Có (corridor) | Không | Endogenous bundle nhưng không có private-cost mechanism |
| Chen et al. (2023) | Không | Occasional courier | — | **Courier tự chọn** | DSIC nhưng **bundle cố định trong proof**; WDP là **set cover** | Chiều chọn bundle không được xử lý; bài toán selective phá nền H(m) bound |
| **Luy et al. (2024, POM)** | **Có GW** | **Có OD** | **Có FD** | — | **Không — cost là input đã biết** | **Xác lập taxonomy ba lớp**; bài toán là workforce planning dài hạn, không phải procurement |
| Oyama & Akamatsu (2025) | Một population duy nhất, không tách lớp | | Opt-out | Task chains (bundling) | **Truthful auction trong sub-problem**, master dùng fluid approximation | **Đe dọa novelty ở khung tổng quát**; khác ở chỗ họ không exact toàn cục và không tách hai geometry |
| Xu et al. (2026, TRE) | Full-time courier **non-strategic** | Crowd courier strategic | Có | Task định trước | Có | Hybrid + IC đã có, nhưng lớp thứ hai không bid và không có combinatorial route bidding |
| **Li & Zhang (2026, TS)** | **Không** | Crowd carrier strategic (baseline route + detour tolerance) | Dedicated delivery, fixed price | **Platform sinh qua PDP, cắt nhánh đệ quy** (§3.2) | **Exact VCG (§4.1) + greedy second-best với regret bound** | **Benchmark gần nhất.** Thiếu lớp GW strategic |
| **HICA-S** | **Strategic GW, open route** | **Strategic OD, destination-constrained** | FD giá công khai | **Platform sinh, \|S\| ≤ B, bid-independent** | Exact VCG trên fixed range | — |

Đọc bảng: **không dòng nào có cả GW-strategic và OD-strategic trong cùng một cơ chế
truthful.** Luy et al. có ba lớp nhưng không có cơ chế. Li & Zhang có cơ chế nhưng một
lớp. Đó là intersection gap.

Nhưng phải đọc tiếp §4 trước khi kết luận rằng intersection gap đó đủ làm một paper.

---

## 4. ★ Điều KHÔNG được claim — đọc kỹ, đây là phần giữ bài không bị đánh sập

### 4.1 Không claim taxonomy ba lớp là mới

Luy et al. (POM 2024) đã có. Viết là "chúng tôi lấy taxonomy đã được thiết lập trong
workforce-planning literature và đặt nó vào bài toán procurement dưới thông tin riêng
tư". Đây là điểm mạnh, không phải điểm yếu — nó chứng minh setting có giá trị thật.

### 4.2 ★★ Không claim "hai route geometry ⇒ cấu trúc cơ chế mới"

Đây là điều chỉnh quan trọng nhất của v4. Lý do:

Cả GW và OD đều có chi phí dạng `K_ir + θ_i·W_ir`, cùng một dạng hàm, và θ nằm **cùng
một miền** (scalar dương, cost-unit/giờ). Cái khác nhau chỉ là **cách platform tính**
(K, W) từ route — mà đó là một hàm **công khai**.

Hệ quả: WDP chỉ nhìn thấy các con số `(K_ir, W_ir)` và một scalar `b_i`. Nó **không có
cách nào** biết cột này sinh từ open-route DFS hay từ destination-constrained DFS. Hai
tài xế có cùng vector (K, W) trên cùng tập order là **không phân biệt được** với cơ chế.

Nói gọn: hai geometry tạo ra hai **phân phối cột** khác nhau, không tạo ra hai **cấu
trúc cơ chế** khác nhau. Và `mean θ_GW ≠ mean θ_OD` là hai giá trị trung bình của cùng
một biến, không phải hai miền type.

**Không được viết** trong abstract những câu ngụ ý mạnh hơn mô hình cho phép, kiểu "the
mechanism handles two distinct private-information structures".

Muốn hai miền thật sự khác nhau thì phải để một lớp có type **đa chiều** (ví dụ OD khai
cả θ lẫn detour tolerance). Nhưng §6.2 khóa detour là public, chính là để giữ DSIC. Trong
phạm vi assumption đã khóa, không có đường tạo phân biệt ở tầng cơ chế.

### 4.3 Không đề Theorem "DSIC" như một kết quả lý thuyết mới

VCG trên column pool cố định, bid-independent, cost tuyến tính theo report thì DSIC bất
kể column đến từ đâu. Proof không có bước nào nhìn vào GW hay OD. Đây là hệ quả trực
tiếp của Groves/VCG maximal-in-range. Ghi là **Proposition (adapted from Groves; see
Nisan & Ronen 2007)**, đặt trong phần model, không đặt trong contribution list.

### 4.4 Không claim "first ever"

Dùng "to the best of our systematic search". Và phải chạy systematic search thật (T3),
không phải directed search.

### 4.5 Không gọi chênh lệch payment–cost là "price of truthfulness về allocation"

Exact truthful allocation dưới true bids **chính là** minimum true cost trong fixed
range. Không có allocation inefficiency nào trong cùng range. Metric đúng là
**information rent / payment overhead**, và **price of bounded range** (so B với một
range rộng hơn).

---

## 5. Ba ứng viên đóng góp — xếp hạng, cần ít nhất MỘT

Thanh chuẩn thực tế: Li & Zhang vào TS với setting + một thành phần kỹ thuật không tầm
thường (biến thể greedy của Lehmann et al. + regret bound). Bạn không cần định lý mới.
Bạn cần **đúng một** thành phần như vậy.

### ★ Ứng viên 1 — Open-route bundle generation có bound (Algorithm A)

**Đây là chỗ duy nhất GW và OD khác nhau về mặt toán học.**

Bất đối xứng cụ thể:

- **OD có neo để cắt nhánh.** Detour đơn điệu theo tập order: thêm order chỉ làm detour
  tăng. Có budget τ_i nên có **điều kiện dừng tự nhiên**, và tính được **cận dưới**
  detour cho một tập trước khi enumerate hoán vị. Li & Zhang khai thác đúng tính chất
  này ("spatial monotonicity of detour time") để cắt nhánh đệ quy.
- **GW không có neo.** Open route không có điểm kết thúc cố định, không có detour budget.
  Ràng buộc duy nhất là time window + availability. Cận để cắt nhánh **yếu hơn hẳn**,
  và một tập order "xa" vẫn có thể khả thi nếu time window rộng.

Câu hỏi nghiên cứu cụ thể, kiểm được:

> Sinh đầy đủ open-route PDPTW bundle **không có anchor** thì cắt nhánh thế nào cho
> hiệu quả? Có dominance rule / cận bid-independent nào cho phép loại subset trước khi
> enumerate (2k)!/2^k hoán vị?

Nếu tìm được, đó là đóng góp thuật toán thật, nằm đúng lớp việc C&OR/EJOR đánh giá cao.
Và nó **giải thích được vì sao phải có hai lớp** — không phải vì cơ chế khác nhau, mà vì
bài toán sinh cột khác nhau về độ khó.

### ★ Ứng viên 2 — Cận cho counterfactual VCG (Algorithm C)

Ý tưởng: nếu việc loại winner i chỉ nhiễu loạn **connected component** chứa i trong
route-order conflict graph, thì p_i tính được bằng một lần giải cỡ component thay vì cỡ
toàn bài.

Mục tiêu định lý:
```
Tổng công counterfactual = O( Σ_{components} |component| )  thay vì  O( n × full problem )
```
Cộng một dominance rule: điều kiện nào cho phép tính p_i **dạng đóng** mà không cần
re-solve.

Đây đúng là thứ Nisan & Ronen (2007, "Computationally Feasible VCG Mechanisms") quan tâm,
và nó nâng bài từ application paper lên methodological paper.

### Ứng viên 3 — RQ1: giá trị của việc để cả hai lớp cùng bid

Thực nghiệm. Xem §11 để biết rủi ro và cái bẫy phải tránh.

**Có một trong ba là đủ. Có hai thì mạnh.**

---

## 6. Mô hình — assumption phải khóa trước khi code

### 6.1 Phạm vi được claim

- **[LOCK]** Static, deterministic, single-session procurement.
- **[LOCK]** Mandatory fulfillment: mỗi order được giao đúng một lần, bởi một route được
  chọn hoặc bởi FD.
- **[LOCK]** Unit-demand over routes: mỗi tài xế nhận tối đa một route.
- **[LOCK]** Bounded allocation range: cap B và mọi rule generate/prune cố định trước bid.
- **[LOCK]** Exact optimization: mọi solve dùng để claim DSIC phải OPTIMAL, gap chứng
  nhận = 0, tie-breaking deterministic và report-independent.
- **[LOCK]** Single-parameter private information: mỗi tài xế chỉ có một scalar θ_i.

Không claim: online IC, stochastic IC, budget balance vô điều kiện, coalition-proofness,
false-name-proofness, fairness, dynamic learning.

### 6.2 Public vs private

| Thành phần | GW | OD | Trạng thái |
|---|---|---|---|
| Start location, availability | Có | Có | Public/auditable |
| Capacity, vehicle class | Có | Có | Public |
| Personal destination | — | Có | **Public hoặc pre-committed trước bid** |
| Direct trip distance/time | — | Có | Platform tính |
| Max detour | — | Có | **Public hoặc pre-committed trước bid** |
| κ_i (hệ số quãng đường) | Có | Có | Public/contractual |
| θ_i (value of time) | Có | Có | **Private scalar** |
| b_i | Có | Có | Message duy nhất |

⚠️ **Điểm sẽ bị hỏi:** destination và detour tolerance là chiều strategic *thú vị nhất*
của OD, và bạn giả định chúng public. Phải trả lời trước trong Limitations, và trả lời
bằng cơ chế vận hành (platform quan sát được qua GPS/lịch sử chuyến; OD phải commit
trước khi phiên mở nên không lái được theo tập order) chứ không chỉ nói "we assume".

Lưu ý so sánh: Li & Zhang cho carrier khai **bốn** tham số (capacity, bundle size limit,
detour tolerance, VOT) cho mỗi baseline route. HICA-S khóa ba, giữ một. Tức report space
của bạn là **restriction** của họ. Được phép — nhưng không được viết như thể xử lý cấu
trúc thông tin phong phú hơn.

### 6.3 Feasibility của route

- pickup trước delivery cho từng order;
- order đã release khi được pickup;
- arrival/service trong time windows;
- load sau mỗi event trong [0, capacity_i];
- route hoàn thành trong availability interval;
- |S| ≤ B;
- **với OD:** detour_time ≤ max_detour **và** route kết thúc tại personal destination.

---

## 7. Algorithm A — Bounded Route Generation, hai geometry

### 7.1 Contract

**Input:** instance metadata, orders, drivers (public), travel matrix, config (B,
tolerances, dominance rules). **Không đọc bid.**

**Output:** route_pool, sparse route-order incidence, manifest, `allocation_range_hash`.

**Mục tiêu:** sinh **đầy đủ** mọi feasible route trong range đã định nghĩa. Không chọn
winner, không tối ưu theo bid.

### 7.2 Trình tự

1. Validate public instance, loại record invalid có reason code.
2. Với mỗi tài xế i, lập danh sách order individually reachable.
3. Tạo subset S với 1 ≤ |S| ≤ B từ danh sách đó.
4. **Cheap filters** (đây là chỗ hai lớp khác nhau — xem §7.3).
5. Với subset vượt filter, DFS mọi legal pickup-delivery sequence, prune partial khi vi
   phạm time/load/availability.
6. GW: route kết thúc ở delivery cuối. OD: append personal destination, kiểm detour.
7. Tính schedule, distance, K_ir, W_ir, audit fields.
8. Canonicalize duplicate.
9. Chỉ áp dụng dominance rule **đã chứng minh là bid-independent**.
10. Sort deterministic, gán route_id, xuất manifest + hash.

### 7.3 ★ Bất đối xứng cắt nhánh — trọng tâm kỹ thuật của bài

Số sequence hợp lệ về precedence cho k order, **trước** feasibility pruning, là
(2k)!/2^k:

| k | sequences/subset |
|---:|---:|
| 1 | 1 |
| 2 | 6 |
| 3 | 90 |
| 4 | 2,520 |

Khối lượng thô nếu mọi subset đều reachable:

| n orders | subsets ≤ B=3 | sequence checks ≤ B=3 | ≤ B=4 |
|---:|---:|---:|---:|
| 10 | 175 | 11,080 | 540,280 |
| 20 | 1,350 | 103,760 | 12,313,160 |
| 30 | 4,525 | 368,040 | 69,428,640 |
| 50 | 20,875 | 1,771,400 | 582,127,400 |

**Với OD**, phần lớn subset bị loại **trước** khi vào DFS, bằng một cận dưới detour:
```
LB_detour(S) ≥ 2·max_{j∈S} dist(corridor_i, j)   (hoặc cận chặt hơn)
nếu LB_detour(S) > τ_i  →  loại S, và loại mọi superset của S
```
Tính đơn điệu theo tập cho phép loại **cả cây con** — đúng cơ chế Li & Zhang dùng.

**Với GW**, không có τ. Cận khả dụng duy nhất đến từ time window:
```
nếu earliest_completion(S) > latest_deadline(S)  →  loại S
```
Cận này **yếu hơn nhiều** và **không đơn điệu theo tập một cách hữu ích** — thêm order
có thể làm route dài hơn nhưng vẫn nằm trong time window rộng.

**Đây là bài toán mở của thesis.** Ứng viên hướng giải:

- **Cận dựa trên spanning structure:** cận dưới thời gian route cho tập S bằng
  1-tree/assignment relaxation trên các node pickup–delivery của S, có tính precedence.
  Đơn điệu theo tập → prune được cả cây con.
- **Dominance giữa các route cùng driver, cùng tập order** (an toàn, đã chứng minh
  được — xem §7.4).
- **Dominance giữa các tập** — khó hơn, và là chỗ có thể có kết quả mới: điều kiện nào
  cho phép nói "nếu S không khả thi thì S ∪ {j} không khả thi" khi không có detour budget.

### 7.4 Dominance an toàn (bid-independent) — đã chứng minh được

Với cùng driver i và **cùng tập order S**, xóa r₂ nếu tồn tại r₁ cùng feasibility
semantics sao cho:
```
K_{i,r₁} ≤ K_{i,r₂}   và   W_{i,r₁} ≤ W_{i,r₂},   ít nhất một strict
```
Vì b_i ≥ 0, r₁ không đắt hơn r₂ với **mọi** report khả dĩ, nên r₂ không bao giờ cần.

**Không được prune** vì: reported cost hiện tại cao, top-k theo bid, predicted winner
probability, hay learned score dùng bid.

### 7.5 Acceptance tests

- n ≤ 6: route set phải **giống brute-force 100%** theo canonical signature.
- Mỗi route pass independent schedule/capacity/detour validator.
- **Đổi bid của bất kỳ ai phải cho cùng route count, signature và
  `allocation_range_hash`** — đây là gate quan trọng nhất của cả Algorithm A.
- Recompute cost khớp K + bW trong 1e-6.
- Mỗi pruning rule có unit test counterexample + proof note; rule chưa chứng minh thì
  **tắt** trong main experiment.

---

## 8. Algorithm B — Exact Winner Determination

### 8.1 Mô hình

Ký hiệu: R_i tập route của i; a_or = 1 nếu route r phục vụ order o; x_ir ∈ {0,1};
z_o = 1 nếu order o dùng FD; q_o là FD cost.

```
min   Σ_i Σ_{r∈R_i} (K_ir + b_i·W_ir)·x_ir  +  Σ_o q_o·z_o

s.t.  Σ_i Σ_{r∈R_i} a_or·x_ir + z_o = 1        ∀o ∈ O
      Σ_{r∈R_i} x_ir ≤ 1                        ∀i ∈ G ∪ C
      x_ir, z_o ∈ {0,1}
```

Equality ở ràng buộc order bảo đảm không trùng, không sót. FD làm model luôn feasible.

### 8.2 Tie-breaking deterministic

Nếu nhiều optimum: (1) cố định primary objective tại optimum trong tolerance; (2)
minimize số order dùng FD; (3) chọn lexicographic theo sorted route_id, **không dùng
bid**. Không dùng epsilon tùy tiện đủ lớn để đổi primary optimum.

### 8.3 Failure policy

- OPTIMAL → chuyển sang Algorithm C.
- TIME_LIMIT chưa đóng bound → **chỉ dùng cho scalability stats**, không claim DSIC.
- INFEASIBLE → là bug dữ liệu/model, vì FD phải bảo đảm feasibility.
- Order cover ≠ 1 lần, hoặc driver nhận > 1 route → fail hard.

---

## 9. Algorithm C — Exact Clarke-Pivot Payments

### 9.1 Công thức

Chỉ winner cần payment. Với winner i có reported cost `c_i(x*)` trên route được chọn,
giải lại WDP sau khi disable **toàn bộ** route của i:

```
Z*_{−i} = min reported cost khi i vắng mặt (cùng range, cùng tie-break)
p_i     = c_i(x*) + Z*_{−i} − Z*
u_i     = p_i − (K_{i,r*} + θ_i·W_{i,r*})       [simulated, dùng θ THẬT]
```
Loser nhận 0.

**Không** thay bằng bid × workload, second price theo route riêng lẻ, hay marginal-cost
approximation rồi vẫn gọi là exact VCG.

### 9.2 Naive trước, accelerated sau

Phiên bản đầu **bắt buộc** là naive exact: clone model, đặt upper bound mọi x_ir của i
về 0, solve OPTIMAL.

Acceleration được phép: model reuse + đổi variable bounds; incumbent/basis warm start;
**decomposition theo connected component của route-order conflict graph**; proven bounds;
parallel solves.

Mọi accelerated payment phải khớp naive exact ≤ 1e-6 trên validation set ≥ 100
counterfactual. Skip rule heuristic hoặc time-limited solve **không** được gắn nhãn exact.

### 9.3 Chỗ có thể thành định lý

Xây conflict graph: node = driver, cạnh giữa i và k nếu tồn tại route của i và route
của k chia sẻ ít nhất một order. Giả thuyết cần chứng minh:

> **Claim (cần proof):** Nếu i thuộc component P, thì `Z*_{−i} − Z*` chỉ phụ thuộc vào
> các driver và order trong P. Do đó counterfactual của i giải được trên sub-instance
> giới hạn ở P.

Nếu đúng, tổng công là `Σ_P |winners in P| × solve(P)` thay vì `n × solve(full)`. Với
instance thưa (detour budget chặt, time window hẹp), component nhỏ và speedup lớn.

**Cảnh báo:** claim này **không hiển nhiên** vì FD tạo coupling toàn cục qua objective.
Cần kiểm cẩn thận: FD cost là separable per-order nên có thể vẫn tách được, nhưng phải
chứng minh, không giả định. Đây chính là chỗ có nội dung lý thuyết.

### 9.4 Mechanism audit (bắt buộc, không thay thế proof)

Với mỗi micro/test instance: chạy truthful b_i = θ_i; với từng driver, giữ report của
người khác cố định, thử multiplier {0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0} × θ_i;
re-run B và C trên **cùng `allocation_range_hash`**; tính realized utility bằng θ_i
**thật**. Truthful utility không được thấp hơn best deviation quá 1e-6.

---

## 10. Theorem package — phiên bản trung thực

| # | Phát biểu | Mức độ | Vai trò trong paper |
|---|---|---|---|
| P1 | Algorithm A sinh mọi feasible route có \|S\| ≤ B | Routine (definitional) | Model section |
| P2 | Với B cố định, enumeration polynomial theo \|O\| | Routine (counting) | Model section |
| P3 | Exact allocation + Clarke pivot trên report-independent range là DSIC, IR, range-efficient | **Hệ quả của Groves/VCG** — ghi rõ "adapted from" | Model section, **không** phải contribution |
| **T4** | **Bound cho open-route bundle generation** (§7.3) | **Cần chứng minh — ứng viên contribution 1** | Core |
| **T5** | **Component decomposition cho counterfactual** (§9.3) | **Cần chứng minh — ứng viên contribution 2** | Core |

**Cần ít nhất một trong T4/T5 thành công.** Nếu cả hai thất bại, bài rơi xuống mức
application paper và phải hạ target xuống C&OR thuần thuật toán hoặc một venue nhỏ hơn.

---

## 11. ★ Biện minh single-parameter — tài sản riêng của bạn

Đây là phần **không ai khác trong dòng này có**, và nó đến từ bốn vòng đo trước đó.

Chi phí thật của tài xế có hai chiều: chi phí/km (α) và chi phí/giờ (β). Vì sao được
phép quy về một scalar?

Bằng chứng đo được:
- Trong hình học giao hàng chặng cuối, `t(B) ≈ d(B)/s + service(B)`. Khi service nhỏ và
  s ít biến thiên, các vector `v_B = (d(B), t(B))` gần **cùng một tia**.
- Đo được: σ_ψ ≈ 1° (độ trải góc của bundle trong menu), **trung vị số quạt = 1** ở
  cửa sổ thời gian chặt — tức thứ tự bundle hằng trên toàn miền type.
- Mất mát welfare do bỏ chiều thứ hai: **0,002–0,05%**, với baseline chiếu **không**
  oracle cũng chỉ 0,075%.
- Kết luận **bền** khi ép hệ số biến thiên tốc độ lên **8 lần** mức quan sát: gap vẫn 0.
  Lý do cấu trúc: đổi tốc độ **xoay** menu của một tài xế chứ **không trải** nó; độ trải
  do biến thiên `service(B)/d(B)` quyết định, và tốc độ không đụng vào đại lượng đó.

**Cách viết trong paper** (Model assumptions, một đoạn ngắn + một hình):

> Ta mô hình type như một scalar. Điều này không phải giả định thuận tiện: trong hình học
> last-mile, thời gian tuyến gần tỷ lệ thuận với quãng đường, khiến hàm chi phí đa chiều
> sập về một tham số hiệu dụng. Ta định lượng điều này bằng độ trải góc của menu bundle
> và mất mát welfare khi chiếu về một chiều, đồng thời nêu điều kiện định lượng (σ_ψ, số
> quạt) khi nào biểu diễn một tham số **không** còn đủ.

Đoạn này làm ba việc cùng lúc: (a) bảo vệ assumption trung tâm; (b) biện minh cho lựa
chọn mô hình của **cả một lớp paper** bao gồm Li & Zhang — nghĩa là bạn đóng góp cho
literature chứ không chỉ dùng nó; (c) preempt câu hỏi khó nhất mà reviewer sẽ hỏi.

Ước lượng nửa trang + một hình. Đừng bỏ.

---

## 12. Thực nghiệm

### 12.1 RQ và map

| RQ | Treatment | Đối chứng | Outcome chính |
|---|---|---|---|
| **RQ1** Để cả hai lớp cùng bid có giá trị không? | HICA-S B=3 | GW-only, OD-only, OD-first→GW, GW-first→OD | True system cost, FD rate, distance/detour |
| **RQ2** Endogenous bundling có giá trị không? | B = 2/3/(4) | B=1, fixed heuristic bundles | Cost, FD rate, bundle size, runtime |
| **RQ3** Truthful procurement tốn gì? | Exact VCG | Pay-as-bid, posted price, full-info oracle | Payout, information rent |
| **RQ4** Exact payment có khả thi không? | Accelerated C | Naive C | Runtime, speed-up, equality error |
| **RQ5** Bền không? | Full grid | Baseline | Paired effect, solve rate |

### 12.2 ⚠️ Bẫy phải tránh ở RQ1 — nghiêm túc

Complementarity GW–OD lớn nhất khi **hai lớp cạnh tranh cùng một tập order**. Cái điều
khiển điều đó là tham số alignment giữa destination của OD và vùng demand — một tham số
**bạn tự chọn**.

**Nếu RQ1 ra yếu rồi tăng alignment cho tới khi có tín hiệu, đó là bịa kết quả bằng
tham số thiết kế.** Đây là loại lỗi đã xảy ra hai lần trong dự án này (time window phi
thực tế; release spread = 3,0 chọn để đạt gate). Không được lần thứ ba.

Quy tắc: **khóa alignment grid trước khi chạy**, báo cáo toàn bộ đường cong, và chấp
nhận kết luận dù ra sao. Nếu complementarity chỉ đáng kể ở alignment cao phi thực tế,
đó là **kết quả** ("hai lớp bổ trợ nhau chỉ khi hành trình cá nhân của OD trùng vùng
demand ở mức X"), không phải thất bại.

### 12.3 Rủi ro đã biết của RQ1

Trong lớp bài toán này, chênh lệch chất lượng phân bổ đo được là **nhỏ**: greedy vs exact
optimal chỉ 0,76% total-cost gap. Joint vs sequential là phép so khác nhưng cùng *loại*
đại lượng. Chuẩn bị tinh thần cho khả năng RQ1 trả về vài phần trăm — và chuẩn bị sẵn
việc dồn trọng tâm sang T4/T5 nếu vậy.

Đó là lý do RQ1 phải chạy **sớm**, ngay sau khi naive C hoạt động, trước khi đầu tư vào
acceleration.

### 12.4 Bốn tầng instance

| Tầng | n orders | Realization tối thiểu | Mục đích |
|---|---|---:|---|
| Hand-check | 3–5 | 5 | Kiểm công thức, dấu payment, tie-break |
| Exhaustive micro | 3, 5, 8 | 30 mỗi n | So A/B/C với brute force, deviation tests |
| Main exact | 10, 15, 20, 30 | ≥20 paired mỗi n | Kết quả kinh tế/vận hành |
| Scalability | 10–50 | ≥10 paired mỗi cell | Route growth, solve rate, runtime |

CI **bootstrap clustered theo operational session**, không coi nhiều random draw trên
cùng session là độc lập.

### 12.5 Metric

```
Complementarity gain = [min(C_GW-only, C_OD-only) − C_joint] / min(C_GW-only, C_OD-only)
Bundling gain        = (C_B1 − C_B3) / C_B1
Information rent     = Σ_i [p_i − true_cost_i(selected route)]
Payment overhead     = Information rent / Σ_i true_cost_i
Price of range B     = (C_B − C_Bmax) / C_Bmax
Payment speed-up     = runtime_naive_C / runtime_accelerated_C
```
Luôn báo median + IQR + 95% paired bootstrap CI, và cả giá trị tuyệt đối lẫn phần trăm.

### 12.6 Về dữ liệu — một cảnh báo

Nếu dùng backbone meal-delivery (kiểu Grubhub MDRP): pickup gom cụm ở nhà hàng, **không
phân tán**, khác với câu chuyện dispersed-pickup PDP. Nghiêm trọng hơn: OD detour trên
chuyến cá nhân để giao **đồ ăn nóng** (SLA 30–45 phút) là giả định vận hành gượng.
Crowdshipping OD hợp với parcel hơn hẳn.

Hai lựa chọn: (a) đổi backbone sang parcel/same-day delivery; (b) giữ và viết rõ rằng
OD layer là counterfactual thiết kế, không phải mô tả thị trường hiện có. Reviewer ngành
transportation sẽ nêu điểm này nếu bạn không nêu trước.

---

## 13. Go/no-go sớm

Tiếp tục theo framing này chỉ khi, trong 4–6 tuần đầu:

1. Systematic search không tìm thấy bài đã có **cả** GW-strategic **và** OD-strategic
   trong cùng cơ chế truthful với platform-generated bundle.
2. Prototype giải exact WDP + payments ở n ≥ 10, B = 2 hoặc 3.
3. **Ít nhất một** trong T4/T5 có tín hiệu khả quan trên giấy (không cần proof xong, cần
   biết hướng chứng minh có đường đi).

Nếu (1) hỏng → chuyển hẳn sang computational contribution (T5).
Nếu (2) hỏng → giảm B, hoặc giới hạn một loại route constraint.
Nếu (3) hỏng và RQ1 cũng yếu → **không giữ framing này**; viết lại thành application
paper và hạ target.

---

## 14. Journal fit

- **C&OR — target chính.** Chấp nhận "cấu trúc combinatorial mới + đóng góp thuật toán
  mạnh" mà không đòi lý thuyết kinh tế mới. Cần T4 hoặc T5 đủ mạnh + test quy mô thuyết
  phục.
- **TRE — target thứ hai, phụ thuộc RQ1.** Ưu tiên managerial insight hơn độ sâu lý
  thuyết. Nếu complementarity rõ ràng và có ý nghĩa vận hành, đây là target thực tế nhất.
- **EJOR — stretch, điều kiện kép.** Cần (a) T4 hoặc T5 là kết quả complexity/dominance
  thật, VÀ (b) RQ1 đáng kể.
- **TS / TR-B — ngoài tầm cho MVP.** Li & Zhang vừa publish ở TS trong đúng ngách này;
  thanh chuẩn đã bị neo cao bởi chính bài đang dùng làm benchmark.

---

## 15. Loại khỏi scope (giữ nguyên từ v3)

Rolling horizon/online arrivals; type thay đổi trong session; học preference; type đa
chiều; khai gian destination/capacity/time window; customer bidding/double auction;
dynamic IC; fairness/carbon đồng thời; cơ chế xấp xỉ thứ hai; field experiment; fleet
repositioning.

Thêm một phần vào thì phải bỏ một phần có độ khó tương đương.

---

## 16. ★ VÍ DỤ MẪU ĐẦU-CUỐI — kiểm tay được

Toàn bộ số dưới đây là **[ILL]**, để kiểm công thức và hiểu luồng, không phải dữ liệu
thị trường.

### 16.1 Input

**Tham số công khai:** κ = 0.5 cost-unit/km cho mọi tài xế; B = 2; tốc độ 20 km/h.

**Orders (4):**

| order | pickup | delivery | FD cost q_o |
|---|---|---|---:|
| o1 | P1 | D1 | 15 |
| o2 | P2 | D2 | 45 |
| o3 | P3 | D3 | 40 |
| o4 | P4 | D4 | 50 |

**Drivers:**

| id | lớp | start | destination | direct trip | max detour | capacity | θ **thật** (private) |
|---|---|---|---|---|---:|---:|---:|
| g1 | GW | S1 | — (open) | — | — | 2 | **20** |
| g2 | GW | S2 | — (open) | — | — | 2 | **30** |
| c1 | OD | O1 | Dest1 | 10 km / 30 min | 20 min | 2 | **12** |
| c2 | OD | O2 | Dest2 | 8 km / 24 min | 18 min | 2 | **16** |

Baseline truthful: b_i = θ_i.

### 16.2 Algorithm A — chạy và output

**Input Algorithm A đọc:** orders, drivers (public), travel matrix, B, κ.
**Không đọc:** θ, b.

#### Trace cho c1 (OD) — cho thấy anchor hoạt động

Subset ≤ 2 từ {o1,o2,o3,o4}: C(4,1) + C(4,2) = 4 + 6 = **10 subset**.

Bước filter bằng cận dưới detour (trước khi enumerate hoán vị):

| subset | LB detour (min) | vs τ = 20 | kết quả |
|---|---:|---|---|
| {o1} | 34 | > 20 | **loại** |
| {o2} | 15 | ≤ 20 | giữ |
| {o3} | 18 | ≤ 20 | giữ |
| {o4} | 29 | > 20 | **loại** |
| {o1,·} (3 subset) | ≥ 34 | > 20 | **loại cả cây con** (đơn điệu) |
| {o4,·} (2 subset còn lại) | ≥ 29 | > 20 | **loại cả cây con** |
| {o2,o3} | 20 | ≤ 20 | giữ |

→ Chỉ **3 subset** vào DFS thay vì 10. Enumerate hoán vị: {o2} và {o3} mỗi cái 1
sequence; {o2,o3} có 6 sequence, 2 khả thi, giữ cái tốt hơn theo dominance §7.4.

Kết quả cho c1: 3 route (nhưng {o3} bị dominance loại khi so với {o2,o3} — không, dominance
chỉ áp dụng **trong cùng tập order**, nên giữ cả 3; ở đây ta chỉ liệt kê 2 route được
dùng để cho ví dụ gọn).

#### Trace cho g1 (GW) — cho thấy thiếu anchor

Không có τ. Filter duy nhất: time window.

| subset | earliest completion | latest deadline | kết quả |
|---|---:|---:|---|
| {o1} | 36 | 90 | giữ |
| {o2} | 48 | 100 | giữ |
| {o3} | 55 | 50 | **loại** (TW) |
| {o4} | 60 | 95 | giữ |
| {o1,o2} | 72 | 100 | giữ |
| {o1,o4} | 96 | 95 | **loại** (TW) |
| {o2,o4} | 105 | 95 | **loại** (TW) |
| {o1,o3}, {o2,o3}, {o3,o4} | — | — | loại (chứa o3) |

→ 4 subset vào DFS. **Nhưng chú ý:** để loại {o1,o4} ta phải **tính xong** earliest
completion, tức phải chạy DFS một phần — khác hẳn OD nơi cận dưới tính được mà không
cần đụng tới hoán vị. Và {o1} khả thi, {o4} khả thi, mà {o1,o4} không — nên **không có
tính đơn điệu để loại cây con**.

**Đây chính xác là bài toán T4 phải giải:** tìm cận đơn điệu, tính được rẻ, cho open
route.

#### Output route_pool (rút gọn cho ví dụ)

| route | driver | lớp | bundle | dist / detour_dist | time / detour_time | **K** | **W (h)** |
|---|---|---|---|---:|---:|---:|---:|
| r1 | g1 | GW | {o1} | 12 km | 36 min | 6.0 | 0.600 |
| r2 | g1 | GW | {o2} | 16 km | 48 min | 8.0 | 0.800 |
| r3 | g1 | GW | {o1,o2} | 22 km | 72 min | 11.0 | 1.200 |
| r4 | g2 | GW | {o3} | 10 km | 30 min | 5.0 | 0.500 |
| r5 | g2 | GW | {o4} | 14 km | 42 min | 7.0 | 0.700 |
| r6 | g2 | GW | {o3,o4} | 20 km | 60 min | 10.0 | 1.000 |
| r7 | c1 | OD | {o2} | 4 km | 15 min | 2.0 | 0.250 |
| r8 | c1 | OD | {o2,o3} | 6 km | 20 min | 3.0 | 0.333 |
| r9 | c2 | OD | {o4} | 3 km | 15 min | 1.5 | 0.250 |

Kèm: `route_order_incidence` (sparse), `manifest` (route count theo driver/bundle size,
runtime, pruning count theo rule, config hash), và **`allocation_range_hash`**.

#### Cần prove gì ở Algorithm A

| # | Phát biểu | Cách chứng minh |
|---|---|---|
| **A-P1** | Completeness: mọi feasible route có \|S\| ≤ B đều nằm trong pool | Quy nạp theo \|S\|; mỗi filter phải kèm bổ đề "filter không loại nhầm route khả thi" |
| **A-P2** | Fixed-B polynomial: \|pool\| = O(\|O\|^B · (2B)!/2^B · \|drivers\|) | Đếm trực tiếp; B là hằng |
| **A-P3** | Bid-independence: pool và hash bất biến dưới mọi thay đổi b | Cấu trúc code (A không nhận b làm tham số) + regression test §7.5 |
| **A-P4** | Dominance §7.4 an toàn | Nếu K₁≤K₂, W₁≤W₂ và b≥0 thì c₁≤c₂ với mọi b ⇒ r₂ không cần |
| **★ A-T4** | **Cận đơn điệu cho open route** | **CHƯA CÓ — ứng viên contribution 1** |

Kiểm chứng bắt buộc: n ≤ 6 phải khớp brute-force 100%; đổi bid phải cho cùng hash.

### 16.3 Algorithm B — matching

**Input:** route_pool + bid truthful (b_g1=20, b_g2=30, b_c1=12, b_c2=16) + q_o.

Reported cost `c = K + b·W`:

| route | driver | bundle | K | W | b | **c** |
|---|---|---|---:|---:|---:|---:|
| r1 | g1 | {o1} | 6.0 | 0.600 | 20 | **18.0** |
| r2 | g1 | {o2} | 8.0 | 0.800 | 20 | **24.0** |
| r3 | g1 | {o1,o2} | 11.0 | 1.200 | 20 | **35.0** |
| r4 | g2 | {o3} | 5.0 | 0.500 | 30 | **20.0** |
| r5 | g2 | {o4} | 7.0 | 0.700 | 30 | **28.0** |
| r6 | g2 | {o3,o4} | 10.0 | 1.000 | 30 | **40.0** |
| r7 | c1 | {o2} | 2.0 | 0.250 | 12 | **5.0** |
| r8 | c1 | {o2,o3} | 3.0 | 0.333 | 12 | **7.0** |
| r9 | c2 | {o4} | 1.5 | 0.250 | 16 | **5.5** |

Giải MILP §8.1. Duyệt các phương án chính:

| phương án | tổng |
|---|---:|
| FD(o1)=15 + c1-r8{o2,o3}=7 + c2-r9{o4}=5.5 | **27.5** ← tối ưu |
| g1-r1{o1}=18 + c1-r8=7 + c2-r9=5.5 | 30.5 |
| g1-r3{o1,o2}=35 + g2-r4{o3}=20 + c2-r9=5.5 | 60.5 |
| FD(o1)=15 + c1-r7{o2}=5 + g2-r4{o3}=20 + c2-r9=5.5 | 45.5 |
| FD tất cả | 150 |

**Output allocation:**
```
Z* = 27.5
c1 → r8 = {o2, o3}     (reported cost 7.0)
c2 → r9 = {o4}         (reported cost 5.5)
o1 → FD                (cost 15)
g1, g2 → không thắng
Coverage: o1(FD), o2(c1), o3(c1), o4(c2) — mỗi order đúng 1 lần ✓
```

Chú ý cấu trúc kết quả: **cả hai winner đều là OD** vì chi phí incremental của họ thấp
hơn hẳn; **FD thắng o1** vì không GW nào rẻ hơn 15; **GW hoàn toàn bị loại** ở instance
này. Đó là tín hiệu instance chưa cân — trong experiment thật phải quét supply ratio để
tránh mọi instance đều có kết cấu này (nếu GW không bao giờ thắng thì RQ1 trả về 0 một
cách tầm thường).

#### Cần prove gì ở Algorithm B

| # | Phát biểu | Ghi chú |
|---|---|---|
| **B-P1** | Solve tới OPTIMAL với gap chứng nhận = 0 | Điều kiện của mọi claim DSIC |
| **B-P2** | Tie-break deterministic và **không dùng bid** | Nếu tie-break phụ thuộc bid, DSIC hỏng |
| **B-P3** | Range-efficiency: allocation là min reported cost **trong range đã công bố** | Hiển nhiên nếu B-P1 đúng; phải nói rõ "trong range", không phải toàn cục |

Kiểm chứng: n ≤ 6 khớp complete enumeration; recomputed objective khớp solver ≤ 1e-6.

### 16.4 Algorithm C — payment

Chỉ tính cho winner: c1 và c2.

#### p_c1 — loại toàn bộ route của c1 (r7, r8), giải lại

| phương án (không có c1) | tổng |
|---|---:|
| g1-r3{o1,o2}=35 + g2-r4{o3}=20 + c2-r9{o4}=5.5 | **60.5** ← tối ưu |
| FD(o1)=15 + g1-r2{o2}=24 + g2-r4{o3}=20 + c2-r9=5.5 | 64.5 |
| g1-r3=35 + g2-r6{o3,o4}=40 | 75.0 |
| FD(o1)=15 + FD(o2)=45 + g2-r4=20 + c2-r9=5.5 | 85.5 |

```
Z*_{−c1} = 60.5
p_c1 = c_c1 + Z*_{−c1} − Z*  =  7.0 + 60.5 − 27.5  =  40.0
true cost của c1 = K + θ·W = 3.0 + 12(0.333) = 7.0
u_c1 = 40.0 − 7.0 = 33.0
```

#### p_c2 — loại r9, giải lại

| phương án (không có c2) | tổng |
|---|---:|
| FD(o1)=15 + c1-r8{o2,o3}=7 + g2-r5{o4}=28 | **50.0** ← tối ưu |
| g1-r1{o1}=18 + c1-r8=7 + g2-r5=28 | 53.0 |
| FD(o1)=15 + c1-r7{o2}=5 + g2-r6{o3,o4}=40 | 60.0 |
| FD(o1)=15 + c1-r8=7 + FD(o4)=50 | 72.0 |

```
Z*_{−c2} = 50.0
p_c2 = 5.5 + 50.0 − 27.5 = 28.0
true cost của c2 = 1.5 + 16(0.25) = 5.5
u_c2 = 28.0 − 5.5 = 22.5
```

#### Bảng tổng kết tài chính

| đại lượng | giá trị |
|---|---:|
| Reported operating cost của allocation | 12.5 |
| FD cost | 15.0 |
| **Z\*** | **27.5** |
| Payment cho c1 | 40.0 |
| Payment cho c2 | 28.0 |
| **Tổng payout cho tài xế** | **68.0** |
| Tổng chi của platform (payout + FD) | 83.0 |
| **Information rent** = (40−7) + (28−5.5) | **55.5** |
| Chi nếu dùng FD cho tất cả | 150.0 |
| Tiết kiệm so với all-FD | 67.0 |

Hai điều đọc được, và **cả hai phải vào paper như hai metric tách biệt**:
- Chi phí vận hành của allocation là 27.5, nhưng platform chi 83.0. Chênh lệch là
  **information rent của VCG**, không phải bug.
- Platform vẫn tiết kiệm so với all-FD (83 < 150), tức budget feasibility giữ ở instance
  này. Nhưng đây là **quan sát**, không phải định lý — muốn claim phải nêu điều kiện
  (xem §2.4).

#### Kiểm DSIC — c1 thử khai sai

**Overbid nhẹ, b_c1 = 20 (thật 12):**
- r8 mới: 3.0 + 20(0.333) = 9.67; r7 mới: 2.0 + 20(0.25) = 7.0
- WDP: FD(o1)=15 + c1-r8=9.67 + c2-r9=5.5 = 30.17 → c1 **vẫn thắng r8**
- `Z*_{−c1} = 60.5` **không đổi** (không phụ thuộc bid của c1)
- `p_c1 = 9.67 + 60.5 − 30.17 = 40.0` — **y hệt**
- `u_c1 = 40.0 − 7.0 (true cost) = 33.0` — **không tăng** ✓

**Overbid mạnh, b_c1 = 200:**
- r8 mới: 3.0 + 200(0.333) = 69.67
- WDP: g1-r3=35 + g2-r4=20 + c2-r9=5.5 = 60.5 rẻ hơn phương án chứa c1 → c1 **thua**
- `u_c1 = 0 < 33.0` ✓

**Underbid, b_c1 = 5:**
- r8 mới: 3.0 + 5(0.333) = 4.67
- WDP: FD(o1)=15 + 4.67 + 5.5 = 25.17; c1 vẫn thắng r8
- `p_c1 = 4.67 + 60.5 − 25.17 = 40.0` — **y hệt**; `u_c1 = 33.0` ✓

Ba ca cho thấy đúng cơ chế Clarke pivot: payment của c1 **không phụ thuộc** bid của c1
miễn c1 còn thắng cùng bundle; khai sai chỉ có thể làm mất bundle.

#### Cần prove gì ở Algorithm C

| # | Phát biểu | Ghi chú |
|---|---|---|
| **C-P1** | Base solve và mọi removal solve dùng **cùng** range + cùng tie-break | Vi phạm là mất DSIC — kiểm bằng `allocation_range_hash` |
| **C-P2** | Mọi removal solve OPTIMAL | Điều kiện của exact VCG |
| **C-P3** | DSIC + IR (hệ quả Groves/VCG maximal-in-range) | Ghi "adapted from", không phải theorem mới |
| **C-P4** | Accelerated ≡ naive exact | Correctness property, không phải theorem |
| **★ C-T5** | **Component decomposition: `Z*_{−i} − Z*` chỉ phụ thuộc component chứa i** | **CHƯA CÓ — ứng viên contribution 2.** Cẩn thận: FD tạo coupling toàn cục qua objective, phải chứng minh separability chứ không giả định |

Trong ví dụ này, conflict graph có bao nhiêu component? g1–c1 chia sẻ o2; c1–g2 chia sẻ
o3; g2–c2 chia sẻ o4 → **một component duy nhất**, decomposition không giúp gì. Instance
thật với detour budget chặt và time window hẹp sẽ tách thành nhiều component — và
**đo phân phối kích thước component là một trong những việc đầu tiên nên làm** để biết
T5 có đáng theo đuổi không.

### 16.5 Luồng dữ liệu tổng kết

```
orders + drivers(public) + travel matrix + B + κ
        │
        ▼
   ALGORITHM A  (KHÔNG đọc bid)
        │  → route_pool: (driver, bundle, sequence, K, W)
        │  → allocation_range_hash
        │  → prove: completeness, polynomial, bid-independence, dominance
        │  → ★ prove: cận đơn điệu cho open route (T4)
        ▼
   θ_i (private) ──► b_i (report, 1 scalar)
        │
        ▼
   ALGORITHM B  (exact MILP set-partitioning)
        │  → allocation: ai nhận route nào, order nào về FD
        │  → Z*
        │  → prove: OPTIMAL, tie-break bid-independent, range-efficiency
        ▼
   ALGORITHM C  (n_winners lần removal solve, exact)
        │  → Z*_{−i} cho từng winner
        │  → p_i = c_i + Z*_{−i} − Z*
        │  → u_i (dùng θ THẬT), IR flag
        │  → prove: cùng range, cùng tie-break, OPTIMAL
        │  → ★ prove: component decomposition (T5)
        ▼
   Metrics: true system cost, information rent, FD rate,
            complementarity gain, runtime, speed-up
```

---

## 17. Việc đầu tiên nên làm

Không phải T0–T3 như v3. Mà là:

1. **Phác trên giấy** xem T4 (cận đơn điệu cho open route) hoặc T5 (component
   decomposition) có đường chứng minh không. Vài ngày, không cần code.
2. Nếu có ít nhất một hướng đi được → xây prototype theo trình tự v3 (oracle nhỏ →
   Algorithm A theo cấp B → B → naive C).
3. Chạy RQ1 **sớm**, ngay sau naive C hoạt động, trước khi đầu tư acceleration.

Nếu cả T4 và T5 đều không có đường, biết sớm và điều chỉnh framing — mất vài ngày thay
vì vài tháng.

---

## 18. Reference backbone (kiểm lại metadata qua DOI trước khi viết)

- Archetti, Savelsbergh & Speranza (2016), *The Vehicle Routing Problem with Occasional
  Drivers*, EJOR.
- Zou & Kafle (2022), Transportation Letters — exact VCG trên platform-generated jobs,
  type 4 chiều, DSIC.
- Triki (2021), J. Cleaner Production — combinatorial procurement of occasional drivers.
- Mancini & Gansterer (2022), Omega — bundle generation cho OD.
- Chen et al. (2023), IEEE IoT Journal — truthful combinatorial reverse auction, chi phí
  2 chiều, set cover.
- **Luy, Hiermann & Schiffer (2024), Production and Operations Management 33(11):
  2177–2200** — *Strategic Workforce Planning in Crowdsourced Delivery With Hybrid Driver
  Fleets*. **Nguồn của taxonomy FD/GW/OD.**
- Oyama & Akamatsu (2025), Transportation Research Part C 174: 105110 — market-based
  matching, task-bundling, truthful sub-auction. **Threat lớn nhất ở khung tổng quát.**
- Xu, Wang, Liu, Huang & Zhang (2026), Transportation Research Part E — incentive-
  compatible auction mechanisms for crowdshipping.
- **Li & Zhang (2026), Transportation Science** — DOI 10.1287/trsc.2025.0089.
  **Benchmark gần nhất.** §3.2 bundle generation; §4.1 VCG; §4.2 greedy + second-best;
  Prop 5 regret bound; Prop 9 optimality bound; Prop 10 complexity.
- Lehmann, O'Callaghan & Shoham (2002), JACM — greedy + critical payment, single-minded.
- Nisan & Ronen (2007), JAIR — *Computationally Feasible VCG Mechanisms*. **Nền cho T5.**
- Ropke & Cordeau (2009), Transportation Science — exact PDPTW backbone.

Ba paper cần đọc **trước tiên**, có mục đích cụ thể:

| Đọc | Để trả lời |
|---|---|
| Li & Zhang §3.2 + Online Appendix | Thuật toán cắt nhánh của họ khai thác đơn điệu detour thế nào — và bước nào **không** áp được cho open route |
| Lehmann et al. (2002) | Kỹ thuật greedy + critical payment; chỗ nào dựa vào single-minded |
| Nisan & Ronen (2007) | Khung "computationally feasible VCG"; có kết quả nào về decomposition counterfactual chưa |