
### Đo lặp phần B=3 (giao thức machine-drift)

Tăng tốc so với C1: lần 1 (10 lần lặp) / lần 2 (đo lại, 10 lần lặp). Dữ liệu thô: `timing_label.json`, `timing_label3.json`.

| instance | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|
| n12_s42 | 0,65 / 0,67 | 1,12 / 1,18 | 1,15 / 1,19 | 0,81 / 0,88 | 0,86 / 0,85 |
| n10_s1 | 0,69 / 0,66 | 1,14 / 1,11 | 1,20 / 1,19 | 0,84 / 0,85 | 0,86 / 0,89 |
| n15_s7 | 0,79 / 0,78 | 1,15 / 1,18 | 1,18 / 1,16 | 0,90 / 0,93 | 0,94 / 0,96 |
| n12_s123 | 0,74 / 0,77 | 1,22 / 1,22 | 1,23 / 1,25 | 0,88 / 0,95 | 0,94 / 0,96 |
| n10_s999 | 0,64 / 0,67 | 1,07 / 1,17 | 1,23 / 1,34 | 0,83 / 0,90 | 0,90 / 0,90 |

Thứ tự các biến thể giống nhau ở cả hai lần trên mọi instance. Thay đổi lớn nhất của một tỉ lệ là 0,11 (C5 trên instance nhỏ nhất, 0,3 s mỗi lần chạy).

### Bảng E: thời gian đi đâu (cProfile, n12_s42, B=3, giây cho một lần chạy đủ 5 driver, đã gồm overhead của profiler)

| hạng | C1 | C4 | C6 |
|---|---|---|---|
| 1 | `run_round` 0,625 | `run_tier` 0,716 | `run_tier` 0,993 |
| 2 | `_try_delivery` 0,182 (34.827 lần gọi) | `_try_delivery` 0,207 | **`fd_dominated` 0,323 (19.553 lần gọi)** |
| 3 | `_try_pickup` 0,125 (32.724) | `_try_pickup` 0,147 | `_try_delivery` 0,159 |
| 4 | `_filter_dominated_labels` 0,106 (23.334) | `_filter_dominated_labels` 0,113 (18.539) | `_try_pickup` 0,138 |
| 5 | `travel_time` 0,073 | `travel_time` 0,082 | `travel_time` 0,096 |
| 6 | `kstar_pool` 0,058 | `kstar_pool` 0,066 | `_filter_dominated_labels` 0,095 (17.962) |

(Bỏ các dòng wrapper `build_all`/`run_cN`; đầu ra đầy đủ ở `audit_logs2/profile.log`.) Chi phí bên trong FD-dominance của C6: **tổng 0,323 s, trong đó số hạng hấp thụ A là 0,057 s (18%), còn tra cứu và test các bundle con là 0,266 s (82%).** Bản thân engine tier (C4 so với C1) thêm rất ít chi phí quản lý: cùng các hàm chiếm ưu thế, và `_filter_dominated_labels` được gọi ít lần hơn (18.539 so với 23.334 nhóm key) nhờ batch lớn hơn.

## 7. Diễn giải (mỗi biến thể một dòng)

| Biến thể | Quan sát (bằng chứng) | Ý nghĩa | Nên làm gì |
|---|---|---|---|
| Trần / Idea 2a | `wasted_share` 7,9–22,1% (trên 5%); sau tier 0,00% và 0 cặp cross-batch ở cả 10 cấu hình (Bảng C) | Vòng lặp production lãng phí công việc mà việc gom batch theo số sự kiện lấy lại hoàn toàn | Idea 2a **không** bị loại; C4 lấy trọn trần |
| **C4** | Qua G1–G4; R trùng C1; ext giảm 12,5–28,2%; thời gian 1,07–1,30× trên instance nhãn, 1,16× (align 0,90) và 1,07× (align 0,50) trên lưới | **Tăng tốc thật cho Algorithm A**, khiêm tốn, tăng theo B (trung vị 1,14× ở B=3, 1,28× ở B=4) | Báo cáo kèm điều kiện chính xác (n ≤ 15, B = 3, 4); không ngoại suy lên n = 20 |
| **C5** | Qua G1–G4, G7 (K\* trùng, 960 driver ngẫu nhiên không có phản ví dụ); thời gian 1,15–1,43× trên instance nhãn, 1,19×/1,14× trên lưới; chỉ lưu K\* (ít hơn R khoảng 8× route ở instance nhãn B=3; 5,65× ở align 0,90; xem bảng "closeness") | Bỏ bước hậu xử lý (`t_F` là 4–11% tổng thời gian của C1) **và** có mức tăng tốc của C4. Phần tăng thêm của C5 so với C4 gần bằng hoặc dưới `t_F`, đúng dự đoán | Báo cáo là "xuất thẳng K\*; phần tăng thêm so với C4 là bước hậu xử lý". Tiết kiệm bộ nhớ chỉ suy ra từ số route, **chưa đo** |
| **C6** | Qua G1–G6 (0 vi phạm trên 6.239 completion, mutation bị bắt); ext giảm 23–42% so với C1 (9–19% so với C4), nhưng thời gian 0,81–0,90× (B=3) và 0,86–1,01× (B=4) so với C1, 0,99×/0,74× trên lưới | Ít extension hơn, **không tăng tốc**: tra cứu các bundle con (82% chi phí FD) và số hạng A tốn hơn số extension bỏ được | Không claim tăng tốc. Hướng sau: tra cứu nhanh hơn (ví dụ chỉ mục bundle con tính sẵn); mọi tối ưu như vậy phải áp cho cả C1/C4 |
| **C7** | An toàn như C6 cộng frontier trong vòng lặp; thời gian 0,86–1,05× so với C1 | Gộp C6 với frontier trong vòng lặp không vượt C5 (1,15–1,43×) | C5 là ứng viên tốt hơn cho Algorithm A production |
| **C3** | ext giảm 15–37% (giống C2 trước đó); thời gian 0,64–0,79× so với C1 | Đánh giá rule một cách lười tốt hơn C2 trước đó (C2 là 0,48–0,80× trong `AUDIT_REPORT.md`, cài đặt khác, không chạy lại ở đây) nhưng vẫn chậm hơn C1 | Giữ C1 làm baseline; rule đường tắt ảo không đáng trong cài đặt này |
| **Rule kích hoạt với driver OD** | G5: 4.960 trong 9.517 lần discard được kiểm là driver OD; lưới: kích hoạt cho 30/30 driver GW và 30/30 driver OD ở cả hai alignment (C3, C6, C7) | Mâu thuẫn câu "never fires for occasional drivers" đối với các cài đặt label-setting này | Nêu số liệu nếu vẫn giữ câu đó |

**Biến thể có tiến gần K\* hơn không?** `|route giữ lại| / |K*|` (gộp; 1 = đúng K\*):

| tập | C1 | C3 | C6 | C5, C7 |
|---|---:|---:|---:|---:|
| instance nhãn, B=3 | 7,90 | 4,60 | 6,44 | 1 (theo cấu tạo, đã kiểm bằng G1/G7) |
| instance nhãn, B=4 | 8,60 | 5,06 | 7,41 | 1 |
| lưới, alignment 0,90 | 5,65 | 4,37 | 3,78 | 1 |
| lưới, alignment 0,50 | 2488 | 952 | 2096 | 1 (K\* rất nhỏ ở đó: 12 route trên 10 instance, nên tỉ lệ không có nhiều ý nghĩa) |

C3 và C6 tiến gần K\* hơn C1 nhưng vẫn còn xa; chỉ frontier trong vòng lặp đạt đúng K\*. (C4 giữ nguyên R như C1.)

## 8. Báo cáo này KHÔNG chứng minh điều gì

- **n = 20 trở lên, và B = 4 trên lưới chính.** B=4 chỉ chạy trên năm instance nhãn (n ≤ 15). Mức tăng tốc của C4/C5 tăng theo B trong dữ liệu (trung vị C4 từ 1,14× lên 1,28×), nên kích thước lớn hơn có thể cho kết quả khác theo cả hai hướng.
- **Máy khác, bản Python khác.** Mọi thứ là Python thuần 3.7.7 trên một máy với chế độ nguồn Balanced. Chi phí tương đối của tra cứu dictionary (làm C6 chậm) và của batch lớn hơn (làm C4 nhanh) có thể khác ở nơi khác.
- **Các biến thể chưa được tối ưu.** Phần tra cứu của C6 chưa tối ưu, và đặc tả cấm tối ưu một biến thể mà không áp dụng cho C1. Một FD-dominance được tinh chỉnh có thể đổi kết luận; thí nghiệm này không nói được.
- **Machine drift.** Anchor lệch tới +19% ở một instance trong lượt đầu và +11,6% ở instance nhỏ nhất trong lượt lặp. Tỉ lệ lặp lại được ở B=3 (Mục 6), nhưng B=4 và lưới (5 lần lặp) chỉ đo một lần.
- **Chiều sâu thống kê.** Trung vị của 10 lần chạy ghép cặp (5 lần với các lần chạy trên 20 s và với lưới); có IQR nhưng không có khoảng tin cậy.
- **Tình trạng chứng minh.** Idea 3 (FD-dominance giữa label đã sinh) và giả thuyết frontier trong vòng lặp ("K\* của bundle nhỏ hơn là đủ") là **chưa được chứng minh**. Bằng chứng: 6.239 completion được kiểm với bộ đánh giá độc lập (B=3, n ≤ 10), K\* trùng trên 30 instance, 960 driver ngẫu nhiên (n=6..9, B=3), brute force cho n=5,6 và các mutation test. G5 chỉ bao phủ B=3; đợt săn ngẫu nhiên của G7 chỉ ở B=3; G3 dùng 20 profile mỗi instance.
- **Bộ nhớ.** Mức tiết kiệm bộ nhớ của frontier trong vòng lặp được suy ra từ số route, không đo.
- **Hòa phân bổ.** G3 so tập người thắng, giá trị và payment; các hòa giữa phân bổ cùng chi phí không được phân tích riêng (không profile nào khác nhau).
- **Bản sao.** Ba label cùng key có (t,K,W) bằng hệt nhau được mở rộng hai lần trên n15_s7 ở B=4 khi dùng tier (Bảng C). Không ảnh hưởng tính đúng, ghi để đầy đủ.

## 9. Câu đề xuất cho bản thảo (chỉ những gì bằng chứng ủng hộ)

1. *Algorithm A (xử lý theo số sự kiện).* "Processing labels in tiers of equal event count `m = abs(IV) + 2 abs(C)` puts all labels with the same key `(v, IV, C)` into one dominance batch. On the five experimental instances this removed 12.5–16.8% (B=3) and 19.9–28.2% (B=4) of the extension attempts, left the route pool and the frontier unchanged, and reduced running time by a median factor of 1.14 (B=3) and 1.28 (B=4) in our pure-Python implementation." Nêu rõ rằng vòng lặp production chỉ so sánh label trong cùng một round/lần lặp closure.
2. *Frontier trong vòng lặp.* "Testing frontier membership as soon as all routes of a bundle size are complete outputs the frontier directly and stores no other route; median speed-ups 1.20 (B=3) and 1.38 (B=4) relative to the baseline." Thêm rằng điều này được kiểm nghiệm thực nghiệm, chưa được chứng minh.
3. *FD-dominance giữa các label đã sinh.* "Safe in all tests (0 violations in 6,239 completions checked against an independent evaluator; mutations detected) and reduces extensions by a further 9–19% but did not reduce running time (0.8–1.05×)." **Không** gọi đó là tăng tốc và **không** gọi là đã chứng minh.
4. *Rule đường tắt ảo.* Giữ kết luận của audit trước: nó bỏ được extension nhưng chậm hơn baseline (ở đây 0,64–0,79× kể cả khi đánh giá lười).
5. Câu "never fires for occasional drivers" nên bỏ hoặc nêu điều kiện (nó kích hoạt cho mọi driver OD trong mẫu lưới).
6. Đừng bao giờ viết "K\* speeds up the pipeline" mà không kèm điều kiện; các mức tăng tốc ở trên chỉ cho Algorithm A, không cho B/C.

## Phụ lục: file

`audit_logs2/`: `phase1_answers.md`, `phase1_ceiling.{log,json}`, `phase1_example.log`, `phase1_after_tier.{log,json}`, `regression*.log`, `gate_equal.{log,json}`, `gate_wdp.{log,json}`, `gate_audit.{log,json}`, `gate_audit_after_refactor.log`, `timing_label.{log,json}`, `timing_label3.json`, `timing_label3_rerun.log`, `timing_grid.{log,json}`, `anchor*.log`, `profile.{log,json}`, `tables.md`, `environment.txt`, `lock_sha256_{before,mid,after}.txt`.
