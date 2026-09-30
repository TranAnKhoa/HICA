# Guideline đọc và tóm tắt paper cho HICA-S

Đừng đọc theo năm xuất bản. Với HICA-S, nên đọc theo thứ tự: **xác lập DD–OD → kiểm tra novelty → thiết kế bundling/routing → chứng minh IC → xây thuật toán exact**.

## Nhóm A — Hiểu đúng bài toán HICA-S

### 1. Luy, Hiermann & Schiffer (2024)

[*Strategic Workforce Planning in Crowdsourced Delivery With Hybrid Driver Fleets*](https://doi.org/10.1177/10591478241268602)

Đây nên là paper đầu tiên vì nó cung cấp:

- định nghĩa DD và OD mà HICA đang sử dụng;
- bằng chứng hybrid DD–OD không phải bối cảnh tưởng tượng;
- khác biệt acceptance behavior giữa hai nhóm;
- cách sử dụng Grubhub data để xây hybrid instances.

Chỉ cần đọc kỹ Introduction, Problem Setting, Experimental Setup và Managerial Results. Chưa cần đào sâu MDP/ADP.

**Output sau khi đọc:** viết được một trang “HICA operational context” và bảng phân biệt DD–OD–backup.

---

### 2. Archetti, Savelsbergh & Speranza (2016)

[*The Vehicle Routing Problem with Occasional Drivers*](https://doi.org/10.1016/j.ejor.2016.03.049)

Paper nền tảng cho route geometry của OD:

- OD có destination cá nhân;
- detour cost;
- company fleet và occasional drivers;
- compensation schemes;
- giá trị của OD đối với delivery system.

**Output:** formalize được feasible route của OD và giải thích tại sao OD không thể được coi đơn giản là một DD rẻ hơn.

## Nhóm B — Ba paper gần HICA nhất

Đây là ba PDF đã có. Nên đọc theo đúng thứ tự dưới đây.

### 3. Li & Zhang (2026) — paper gần nhất trực tiếp

[*Auction Mechanism Design for Order Allocation and Payment in a Crowdshipping System*](https://doi.org/10.1287/trsc.2025.0089)

Đây là paper benchmark số một của HICA-S. Phải đọc gần như toàn bộ, kể cả supplementary material.

Tập trung vào:

- carriers submit bundle bids như thế nào;
- winner-determination formulation;
- fixed-price dedicated backup;
- exact VCG payment;
- approximate mechanism;
- bundle-size và bid-count restrictions;
- budget/profit conditions.

Câu hỏi phải trả lời sau khi đọc:

> Nếu dedicated backup của Li–Zhang được thay bằng một tập strategic DD, chính xác formulation, payment và computational structure thay đổi ở đâu?

Nếu không trả lời được câu này, novelty HICA còn yếu.

---

### 4. Xu et al. (2026)

[*Incentive-Compatible Auction Mechanisms for Crowdshipping*](https://doi.org/10.1016/j.tre.2026.104919)

Paper này cho thấy hybrid logistics + IC đã tồn tại, nhưng:

- chỉ crowd couriers strategic;
- full-time couriers là backup/non-strategic capacity;
- delivery tasks được xác định trước;
- mỗi crowd courier nhận tối đa một task;
- combinatorial bidding phức tạp hơn vẫn là phần mở.

Đọc kỹ:

- type và bidding model;
- allocation problem;
- tại sao họ dùng Leonard/proxy mechanism thay vì VCG;
- proof IC;
- polynomial-time argument;
- vai trò của full-time couriers.

**Output:** bảng so sánh “Xu versus HICA-S” ở cấp assumptions, variables, mechanism và guarantees.

---

### 5. Oyama & Akamatsu (2025) — paper đe dọa novelty mạnh nhất

[*A Market-Based Efficient Matching Mechanism for Crowdsourced Delivery Systems with Demand/Supply Elasticities*](https://doi.org/10.1016/j.trc.2025.105110)

Paper này khó hơn hai paper trên nhưng phải đọc kỹ vì framework rất tổng quát:

- heterogeneous driver preferences;
- task-bundling;
- truthful auction trong particle subproblems;
- fluid–particle decomposition;
- task-chain network;
- tránh enumeration bundle.

Câu hỏi quan trọng:

> HICA-S có phải chỉ là một special case của framework Oyama–Akamatsu không?

HICA phải trả lời “không” bằng ít nhất một trong các lý do:

- hai strategic supplier classes tạo ra hai feasible route domains khác nhau;
- platform-generated pickup–delivery routes khác task-chain abstraction của họ;
- exact VCG counterfactual computation tạo ra bài toán mới;
- hybrid interaction tạo structural/computational result mới.

**Output:** một memo 2–3 trang giải thích vì sao HICA không phải relabeling của framework này.

## Nhóm C — Các “near miss” cần dùng để bảo vệ novelty

### 6. Triki (2021)

[*Using Combinatorial Auctions for the Procurement of Occasional Drivers in Freight Transportation*](https://doi.org/10.1016/j.jclepro.2021.127057)

Paper này đã có:

- company fleet;
- OD combinatorial bids;
- vehicle routing;
- winner determination;
- real bookstore case study.

Nhưng:

- company fleet không strategic;
- payment không được thiết kế để bảo đảm IC;
- bundles chủ yếu đến từ bidders, không phải platform-generated bid-independent range.

Đây là benchmark tốt cho claim:

> Hybrid routing + auction đã có; truthful hybrid procurement với cả hai supplier classes thì chưa.

---

### 7. Chen et al. (2023)

[*A Truthful Combinatorial Reverse Auction Mechanism for Crowdshipping*](https://doi.org/10.1109/JIOT.2023.3279104)

Đọc để hiểu:

- truthful approximate allocation;
- polynomial-time mechanism;
- approximation ratio;
- monotonic allocation và threshold payment;
- khác biệt giữa exact VCG và approximate truthful mechanism.

Paper này giúp quyết định sau này có thực sự cần VCG hay nên phát triển một single-parameter monotone mechanism.

## Nhóm D — Bundling do platform tạo

### 8. Çınar et al. (2025)

[*Pricing, Bundling, and Driver Behavior in Crowdsourced Delivery*](https://arxiv.org/abs/2507.03634)

Đây là paper quan trọng nhất cho Algorithm A của HICA:

- platform đồng thời quyết định bundle, assignment và compensation;
- bundle không được giả định có sẵn;
- acceptance probability thay cho truthful bidding;
- exact column generation;
- dominance và pruning;
- xử lý tới 120 tasks và 60 drivers.

HICA cần kế thừa phần computational bundling nhưng thay behavioral acceptance model bằng truthful procurement.

**Output:** xác định những pricing-subproblem và pruning rules nào có thể chuyển sang HICA.

---

### 9. Zhu et al. (2026)

[*Optimizing Order Bundling and Dispatching in Online Food Delivery*](https://doi.org/10.1016/j.cor.2026.107387)

Paper này đại diện cho phía DD/platform delivery:

- joint bundling–matching–routing;
- courier nhận nhiều orders;
- thuật toán chạy nhanh trên dữ liệu platform thực;
- không có private cost hoặc IC.

Đọc để thiết kế:

- DD route generation;
- practical bundle restrictions;
- baseline BMR;
- metrics về delay, distance và bundle quality.

Đây sẽ là benchmark operational, không phải mechanism benchmark.

---

### 10. Mancini et al. (2024)

[*Bundles Generation and Pricing in Crowdshipping*](https://doi.org/10.1016/j.ejtl.2024.100142)

Paper này nằm giữa Çınar và HICA:

- platform partition orders thành bundles;
- định giá bundles;
- OD acceptance;
- static và dynamic auction simulation;
- third-party backup.

Đọc chủ yếu Introduction, bundle-generation model, pricing schemes và experiments. Không cần dành nhiều thời gian bằng Li–Zhang hoặc Oyama–Akamatsu.

## Nhóm E — Nền tảng mechanism design cần cho proof

### 11. Archer & Tardos (2001)

[*Truthful Mechanisms for One-Parameter Agents*](https://research.google/pubs/truthful-mechanisms-for-one-parameter-agents/)

Đây là lý thuyết trực tiếp cho giả định:

\[
C_{ir}(\theta_i)=K_{ir}+\theta_iW_{ir}.
\]

Phải hiểu:

- single-parameter domain;
- monotonicity;
- threshold/integral payment;
- điều kiện cần và đủ cho truthfulness.

Sau paper này, phải quyết định rõ:

- dùng general VCG argument; hay
- dùng single-parameter monotonicity argument.

Không nên trộn hai proof một cách mơ hồ.

---

### 12. Nisan & Ronen (2007)

[*Computationally Feasible VCG Mechanisms*](https://doi.org/10.1613/JAIR.2046)

Paper này giải thích lỗi nguy hiểm nhất của HICA:

> Không thể lấy một heuristic routing/allocation, gắn VCG payment vào rồi tuyên bố truthful.

Nếu allocation không exact hoặc không maximal-in-range trên một range cố định, IC có thể mất.

Đọc kỹ phần:

- vì sao approximate VCG thường không truthful;
- fixed outcome range;
- computational feasibility;
- quan hệ giữa allocation algorithm và payment rule.

## Nhóm F — Thuật toán exact routing

### 13. Ropke & Cordeau (2009)

[*Branch and Cut and Price for the Pickup and Delivery Problem with Time Windows*](https://doi.org/10.1287/trsc.1090.0272)

Đây là paper kỹ thuật cho set-partitioning formulation:

- mỗi column là một feasible route;
- master problem chọn routes;
- pricing subproblem sinh routes;
- pickup–delivery precedence;
- capacity và time windows;
- branch-cut-and-price.

Không cần implement toàn bộ ngay. Đọc để biết Algorithm A/B của HICA đang đứng trên nền thuật toán nào.

## Thứ tự rút gọn nếu chỉ đọc 8 paper

Nếu thời gian hạn chế, đọc đúng thứ tự:

1. Luy et al. — hiểu DD–OD.
2. Li & Zhang — closest benchmark.
3. Xu et al. — hybrid IC benchmark.
4. Oyama & Akamatsu — kiểm tra nguy cơ specialization.
5. Triki — routing + dedicated fleet + auction.
6. Çınar et al. — endogenous platform bundling.
7. Archer & Tardos — proof single-parameter IC.
8. Nisan & Ronen — tránh sai khi kết hợp heuristic với VCG.

Sau đó mới đọc Zhu và Ropke–Cordeau để xây thuật toán.

## Cách đọc mỗi paper

Không nên chỉ highlight. Với mỗi paper, điền đúng 10 trường:

| Trường cần ghi | Câu hỏi |
|---|---|
| Actors | Ai tham gia hệ thống? |
| Strategic agents | Ai có thể khai gian? |
| Private information | Cost, detour, destination hay valuation nào là private? |
| Bundle owner | Platform hay driver tạo bundle? |
| Route geometry | Open, depot-return hay destination-constrained? |
| Allocation | Biến quyết định và objective là gì? |
| Payment | Posted price, pay-as-bid, VCG hay proxy auction? |
| Guarantee | IC, IR, budget balance, approximation? |
| Computation | MILP, greedy, column generation hay decomposition? |
| Remaining gap | HICA bổ sung điều gì không trivial? |

Sau khi đọc xong paper số 5, nên dừng lại và viết literature-positioning memo trước khi đọc tiếp. Nếu lúc đó chưa giải thích được HICA khác Li–Zhang, Xu và Oyama–Akamatsu ở đâu về mặt toán học, chưa nên bắt đầu code cơ chế.
