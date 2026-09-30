# HICA-S — Nhận xét và cross-check về novelty, tính khả thi và dữ liệu

**Thời điểm cross-check:** 12/08/2026

Đã cross-check lại đến ngày 12/08/2026 và cập nhật trực tiếp `HICA_Master_Thesis_Q1.md`.

## Kết luận thẳng

Đây là một đề tài **đáng đầu tư theo dạng Conditional GO**:

- Đủ tốt để làm master thesis.
- Có novelty hợp lý để nhắm TR-E/COR.
- Chưa thể khẳng định chắc chắn Q1, vì có vài paper năm 2025–2026 nằm rất sát.
- Q1 chỉ khả thi nếu ngoài framing mới, bạn tạo được đóng góp tính toán hoặc structural result thực sự.

## Novelty có phải là “chưa ai kết hợp DD × OD × IC”?

Không nên phát biểu đơn giản như vậy, vì technically không hoàn toàn đúng.

Các paper đã ghép nhiều phần:

- Luy et al. đã nghiên cứu đúng hybrid workforce gồm DD và OD, nhưng không có mechanism design hay truthful bidding. [POM paper](https://doi.org/10.1177/10591478241268602)
- Triki đã kết hợp company fleet, OD combinatorial auction và routing, nhưng company fleet không phải bidder và không chứng minh IC. [Journal of Cleaner Production](https://doi.org/10.1016/j.jclepro.2021.127057)
- Li–Zhang đã có OD, order bundles, VCG và dedicated delivery backup; nhưng chỉ OD đấu giá, còn dedicated service là fixed-price backup. [Transportation Science](https://doi.org/10.1287/trsc.2025.0089)
- Xu et al. đã có strategic crowd couriers, full-time couriers và IC; nhưng full-time couriers không strategic và delivery tasks được định trước. [TR-E](https://doi.org/10.1016/j.tre.2026.104919)
- Oyama–Akamatsu đã có heterogeneous crowd drivers, task-bundling và truthful auction trong framework khá tổng quát. Đây là paper đe dọa novelty mạnh nhất, dù họ không tách DD và OD thành hai strategic route geometries. [TR-C](https://doi.org/10.1016/j.trc.2025.105110)

Novelty chính xác và defensible của bạn phải là:

> Chưa tìm thấy nghiên cứu nào trong đó cả dedicated gig drivers và opportunistic drivers đều là strategic suppliers; hai nhóm có hai miền route khác nhau — open routes và destination-constrained routes; platform tạo multi-order route-bundles từ atomic orders; và bundling, allocation cùng truthful payments được quyết định trong một cơ chế thống nhất.

Nói ngắn hơn:

> **Strategic DD + strategic OD + distinct route geometries + platform-generated bundles + exact IC procurement.**

Đây là novelty theo **giao điểm đầy đủ**, không phải novelty của từng thành phần.

## Rủi ro publication lớn nhất

Nếu paper chỉ làm:

> “Lấy Li–Zhang rồi biến dedicated backup thành strategic DD”

thì reviewer có thể xem đây là incremental extension.

Để đủ lực Q1, ít nhất phải đạt một trong ba kết quả:

1. Một structural result chỉ xuất hiện khi DD open routes và OD destination-constrained routes cùng tồn tại.
2. Một thuật toán exact route generation/VCG reoptimization nhanh hơn rõ ràng cách naive.
3. Chứng minh bằng thực nghiệm rằng strategic DD làm thay đổi đáng kể bundle structure, allocation, payments hoặc giá trị của hybrid fleet so với fixed-cost DD.

VCG tự nó không phải novelty; VCG là công cụ. Novelty phải nằm ở problem structure và computational mechanism.

## Dataset: không cần phụ thuộc Meituan

Lựa chọn tốt nhất cho main experiment là [Grubhub MDRP public instances](https://github.com/grubhub/mdrplib).

Dataset này có:

- 240 instances từ 10 seed instances thực tế;
- atomic meal-delivery orders;
- restaurant/customer locations;
- placement và ready times;
- courier schedules, IDs và movements;
- evaluator công khai.

Nó rất phù hợp để tạo phần DD của HICA-S và đã được Luy et al. dùng cho hybrid DD–OD research.

Thiết kế dataset hợp lý nhất:

| Thành phần | Nguồn |
|---|---|
| Orders, pickup–delivery, time information | Grubhub MDRP |
| DD shifts và availability | Historical Grubhub couriers |
| OD origins/destinations | Semi-synthetic trong cùng coordinate system |
| Phân phối OD trip length/time | Hiệu chỉnh từ NYC TLC/NHTS hoặc crowdshipping papers |
| Private cost θᵢ | Synthetic factorial distributions, literature-calibrated |
| Robustness/scalability | Cainiao LaDe hoặc Amazon Last Mile |

OD trips nên được tạo semi-synthetic vì Grubhub không chứa personal trips. Có thể hiệu chỉnh phân phối bằng [NYC TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) hoặc [NHTS](https://www.fhwa.dot.gov/policyinformation/nextgen-nhts-data.cfm), nhưng không ghép trực tiếp tọa độ hai dataset khác thành một thành phố giả.

Private cost cũng phải synthetic. Gần như không có public dataset chứa “true private opportunity cost” vì đây chính là thông tin ẩn mà mechanism cần elicitation. Điều đó không làm paper mất giá trị, miễn là:

- ghi rõ đây là simulated private type;
- dùng nhiều distribution families;
- chạy sensitivity analysis rộng;
- không tuyên bố các costs này là observed driver costs.

Hai dataset robustness tốt:

- [Cainiao LaDe](https://github.com/wenhaomin/LaDe): khoảng 10.677 triệu packages, 21 nghìn couriers, sáu tháng, năm thành phố.
- [Amazon Last Mile Challenge](https://www.amazon.science/publications/2021-amazon-last-mile-routing-research-challenge-data-set): 9.184 historical routes với package/stop/route features.

## Còn Meituan?

Meituan rất hấp dẫn nhưng không nên để thesis phụ thuộc vào nó.

INFORMS TSL và Meituan từng cấp quyền sử dụng operational food-delivery data cho challenge 2024–2025, nhưng đây không phải dataset công khai vô điều kiện và deadline đã qua. Bạn có thể liên hệ ban tổ chức để hỏi research reuse. [Thông báo chính thức của INFORMS](https://connect.informs.org/discussion/deadline-on-march-15-2025-the-first-informs-tsl-data-driven-research-challenge-5)

Ngay cả khi lấy được Meituan data, nó có khả năng chỉ cung cấp:

- order;
- platform couriers;
- dispatch;
- pickup/delivery timestamps;
- routes.

Nó vẫn không cung cấp OD personal trips và true private costs. Do đó Meituan chỉ nên là case study bổ sung, không phải điều kiện để bắt đầu.

## Quyết định cuối cùng

Tôi đánh giá:

- Problem relevance: cao.
- Intersection novelty: khá cao nhưng hẹp.
- Data feasibility: cao.
- Master feasibility: khá tốt nếu giữ static, B ≤ 3, single-parameter types.
- Q1 potential: có, nhưng cần computational contribution rõ.
- Nguy cơ lớn nhất: bị xem là specialization của Li–Zhang/Oyama thay vì một problem class mới.

Vì vậy bạn có thể đầu tư vào đề tài này, nhưng 4–6 tuần đầu phải dành cho hai “kill tests”:

1. Prototype chứng minh HICA-S tạo kết quả khác đáng kể fixed-cost DD backup.
2. Literature matrix chứng minh hai strategic route classes không thể chỉ trivially encode vào các framework hiện tại.

Nếu qua được hai test này, đề tài chuyển từ “novel framing” thành một research project Q1 thực sự có cơ sở.
