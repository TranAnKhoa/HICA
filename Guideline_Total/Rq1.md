# RQ1 — Complementarity GW×OD: Execution Spec

> File này để giao trực tiếp cho Claude Code (hoặc engineer bất kỳ) implement và chạy.
> Mọi tham số ở mục 1, 3-5 phải bị KHOÁ (commit + hash) TRƯỚC KHI chạy instance đầu tiên.
> Không sửa sau khi thấy kết quả — quy tắc cứng, không phải khuyến nghị. Dự án đã phạm
> lỗi này 2 lần trước đó (time window phi thực tế; release spread=3.0 chọn để đạt gate).
> Lần thứ ba sẽ làm mất giá trị của toàn bộ RQ1.

**Nhãn dùng trong file:** `[LOCK]` = không được đổi sau khi hash; `[IMPLEMENT]` = việc cần
code; `[CHECK]` = gate bắt buộc pass trước khi tin số liệu; `[DECISION]` = quy tắc áp dụng
sau khi có kết quả.

---

## 0. Câu hỏi nghiên cứu

Để hai lớp GW và OD cùng bid trong một cơ chế truthful chung có tạo giá trị (giảm true
system cost) so với: (a) chỉ một lớp bid, (b) xử lý tuần tự ưu tiên một lớp? Và: giá trị đó
(nếu có) phụ thuộc thế nào vào mức độ trùng lặp không gian ("alignment") giữa hành trình cá
nhân của OD và vùng demand?

---

## 1. Tiền đề bắt buộc: sinh private/public cost — khoá TRƯỚC mục 2

Instance hiện tại (sau khi sửa ready time OD) mới có location, time window, capacity, τ, κ —
**chưa có** θ_i (private, GW/OD) và q_o (public, FD). Đây là input còn thiếu, chặn toàn bộ
pipeline chứ không riêng RQ1 — khoá một lần, dùng chung cho mọi thực nghiệm về sau, không
khoá lại riêng cho từng RQ.

### 1.1 θ_i — value of time riêng từng tài xế (GW và OD)

`[LOCK]` Mặc định: **cùng một họ phân phối, cùng range, cho cả GW và OD** —
`θ_i ~ Uniform[θ_min, θ_max]` (đơn vị cost-unit/giờ, PHẢI cùng hệ đơn vị với κ — xem §1.3).

Lý do dùng chung một phân phối: §11 của đề cương lập luận GW và OD chia sẻ "cùng một miền"
type scalar. Cho hai phân phối tách biệt không căn cứ sẽ ngầm phá lập luận đó, và mở một
bậc tự do nghiên cứu viên có thể vô tình dùng để cân bằng/triệt complementarity ở RQ1 —
đúng loại bẫy đã cảnh báo ở alignment, chỉ chuyển sang biến khác. Nếu muốn hai lớp cạnh
tranh cân bằng hơn, sửa ở supply ratio (đã có trong lưới RQ1 §4), KHÔNG sửa ở θ.

**Neo giá trị:** `Uniform[18, 25]` (đơn vị gốc USD/giờ, theo Amazon Flex, do Li & Zhang —
benchmark gần nhất — dùng làm range VOT của crowd carrier). Quy đổi sang cost-unit riêng
của instance, giữ cùng range cho GW và OD.

**Nếu muốn có chênh lệch GW/OD:** chỉ làm khi có nguồn cụ thể (ví dụ khảo sát về
willingness-to-accept của occasional driver so với gig-platform target wage), trích dẫn rõ
trong bài — không tự chọn số để cân bằng thắng/thua.

### 1.2 q_o — chi phí FD (public, per order)

`[LOCK]` Công thức (theo cấu trúc Li & Zhang, neo vào biểu giá courier thật — FedEx
same-day):
```
q_o = base_fee + rate_per_km · max(0, dist(pickup_o, delivery_o) − free_radius)
```
Ba hằng số (`base_fee`, `rate_per_km`, `free_radius`) chọn một lần qua calibration pass
(§1.4), không chọn tuỳ ý, không đổi giữa các thực nghiệm.

### 1.3 `[CHECK]` Kiểm tra đơn vị — bắt buộc, dễ bị bỏ sót nhất

κ (cost-unit/km), θ (cost-unit/giờ), q_o (cost-unit) phải cùng một hệ đơn vị. Kiểm bằng:
lấy một route "điển hình" (median distance, tốc độ trung bình của instance), so
`κ · distance` với `θ_mean · time_hours`. Hai số hạng này nên cùng bậc độ lớn (trong
khoảng 2-5 lần nhau), KHÔNG lệch 10-100 lần. Nếu lệch, một số hạng sẽ luôn át số hạng kia
trong `K_ir + θ_i·W_ir`, khiến phần θ (tức toàn bộ private information) gần như không ảnh
hưởng đến allocation — cơ chế truthful trở nên vô nghĩa mà không ai nhận ra cho tới khi
phân tích kết quả xong.

### 1.4 Calibration pass — chạy một lần, khoá, không lặp lại giữa main experiments

Trên một batch pilot nhỏ (n, supply ratio giống lưới RQ1 §4 nhưng **không phải** instance
sẽ dùng để trả lời RQ1 thật): quét vài giá trị `base_fee`/`rate_per_km`, đo **FD rate** và
**win rate GW vs OD** trên batch đó.

M��c tiêu mềm (chọn bộ tham số đầu tiên đạt cả hai, rồi dừng lại):
- FD rate rơi vào khoảng ~10-50% (không phải 0% — FD không phải outside option thật nếu
  không bao giờ thắng; không phải ~100% — vậy mất lý do có crowdshipping).
- Không có lớp nào thắng 0% hoặc 100% tuyệt đối trên mọi supply ratio đã định ở §4.

Ghi bộ tham số cuối cùng (θ range, base_fee, rate_per_km, free_radius) vào
`rq1_locked_params.json` cùng các tham số khác — **không** tinh chỉnh lại sau khi đã thấy
RQ1 chạy.

---

## 2. Input cần có sẵn (ngoài §1)

- Algorithm A (route generation, bid-independent) — dùng nguyên bản, KHÔNG chờ acceleration
  (đã xác nhận decomposition T5 không giúp gì ở scale chính — không có lý do trì hoãn).
- Algorithm B (exact WDP MILP, §8 đề cương).
- Algorithm C — dùng **bản NAIVE** (§9.2), không dùng bất kỳ decomposition/warm-start nào.
  RQ1 không được phép bị nhiễu bởi rủi ro đúng-sai của một kỹ thuật tăng tốc đang thử nghiệm.
- Instance generator hiện tại (spatial_mode, phân phối τ, time window width) — **không đổi
  bất kỳ default nào ngoài hai trục được kiểm soát ở §4**, để không mở thêm bậc tự do
  nghiên cứu viên có thể vô tình khai thác.

## 3. Định nghĩa "alignment" — khoá một công thức duy nhất

```
corridor_k = đoạn thẳng (hoặc path) origin_k → destination_k, cho OD k
dist(o, corridor_k) = khoảng cách điểm-đến-đoạn từ pickup location của o tới corridor_k

alignment(instance) = (1/|O|) * Σ_o  1[ min_{k ∈ C} dist(o, corridor_k) ≤ r0 ]
```

`[LOCK] r0`: tính **một lần duy nhất**, TRƯỚC khi chạy RQ1, từ percentile-25 của phân phối
pairwise distance (driver corridor, order pickup) trên một **pilot instance trung lập**
(không phải instance sẽ dùng để trả lời RQ1). Ghi giá trị r0 (đơn vị km) vào
`rq1_locked_params.json`. Không tính lại r0 sau khi thấy kết quả.

`[IMPLEMENT]` Hàm sinh instance đạt alignment target: dùng một tham số điều khiển sẵn có
của generator (ví dụ xác suất đặt pickup order gần corridor OD thay vì uniform trong service
area) — hiệu chỉnh **một lần** bằng calibration curve (chạy generator ở vài giá trị tham số,
đo alignment thực tế đạt được, fit quan hệ) để biết cần đặt tham số nào cho mỗi target level.
Calibration curve này CHẠY TRƯỚC, KHÓA giá trị tham số cho từng level, KHÔNG hiệu chỉnh lại
trong lúc chạy main grid. Nếu một draw không rơi vào tolerance band, log là `[DEVIATION]` và
vẫn giữ, không loại bỏ để "làm đẹp" phân phối.

## 4. Lưới tham số khoá trước

| Trục | Giá trị | Ghi chú |
|---|---|---|
| `[LOCK]` alignment target | {0.10, 0.30, 0.50, 0.70, 0.90} | tolerance band ±0.05 |
| `[LOCK]` n (số order) | {10, 15, 20} | mở rộng {25,30} chỉ nếu core result đã xong và còn thời gian — không bắt buộc cho RQ1 |
| `[LOCK]` supply ratio (\|G\|,\|C\|) | {(2,2), (3,2), (2,3), (3,3)} | tổng driver ≈ n/4 đến n/3, tránh trường hợp một lớp luôn thắng trắng như ví dụ toy §16 |
| `[LOCK]` B | 3 | khớp giá trị dùng ở main experiment khác, không mở thêm trục |
| θ_i, q_o | theo §1, đã khoá | |
| τ distribution, κ, time window width, capacity | **giữ nguyên default hiện tại của generator** | không đổi cho riêng RQ1 |
| `[LOCK]` replications/cell | ≥ 25 paired instance | paired = cùng order draw + driver draw dùng cho cả 5 treatment |
| `[LOCK]` seed policy | 1 master seed/cell, sub-seed deterministic/replication | ghi log đầy đủ |

Tổng số cell: 5 alignment × 3 n × 4 supply ratio = 60 cell, × ≥25 replication = ≥1,500 instance
gốc, mỗi instance chạy 5 treatment.

## 5. Năm treatment — định nghĩa thuật toán chính xác

`[IMPLEMENT]` Hai treatment tuần tự là code path MỚI, chưa có ở đâu khác trong pipeline —
cần unit test riêng trước khi đưa vào main run (xem §7).

1. **JOINT** — pipeline chuẩn: A(G∪C) → B(full pool + FD) → C(naive, tất cả winner).
2. **GW-ONLY** — A(G) → B({G routes} + FD). OD không tồn tại trong bài toán này (không phải
   không bid — bị loại hẳn khỏi input), để có một thị trường một-lớp sạch.
3. **OD-ONLY** — đối xứng.
4. **OD-FIRST→GW**:
   - Pass 1: B({C routes} + FD) trên toàn bộ O → được tập order OD nhận (`O_OD`) và phần
     còn lại tạm thời là FD.
   - Pass 2: A(G) đã có sẵn (không đổi theo pass 1) → B({G routes} + FD) chỉ trên
     `O \ O_OD` → final: `O_OD` (OD) ∪ kết quả pass 2 (GW hoặc FD) cho phần còn lại.
5. **GW-FIRST→OD** — đối xứng, đảo vai trò pass 1/pass 2.

`[CHECK]` GW-ONLY/OD-ONLY không được tham chiếu route pool của lớp kia trong code (grep để
xác nhận, không chỉ nhìn output).

## 6. Metric

```
Complementarity gain = [min(C_GW-only, C_OD-only) − C_joint] / min(C_GW-only, C_OD-only)
```
Dùng **true cost** (K + θ·W, θ thật) để tính C của mỗi treatment, không dùng reported cost —
RQ1 hỏi về hiệu quả phân bổ thật, không phải về payment.

Báo cáo thêm mỗi cell: FD rate, tổng detour/distance, và so sánh JOINT với cả hai sequential
treatment (không chỉ với GW-only/OD-only) — nếu JOINT thắng GW-only/OD-only nhưng thua
sequential, đó là một kết luận khác hẳn ("thứ tự quan trọng hơn việc cùng bid").

Luôn báo median + IQR + 95% bootstrap CI, **clustered theo session/instance gốc** (không coi
5 treatment trên cùng instance là 5 draw độc lập).

## 7. Gate bắt buộc trước khi tin số liệu

- `[CHECK]` Dry run n≤6, 1 alignment level, so JOINT với brute-force toàn bộ 5 phương án —
  xác nhận hai treatment tuần tự (code path mới) cho đúng kết quả brute-force trước khi chạy
  grid đầy đủ.
- `[CHECK]` Mọi solve trong cả 5 treatment phải OPTIMAL, gap chứng nhận = 0. Bất kỳ
  TIME_LIMIT nào → loại khỏi bảng kinh tế RQ1, chỉ dùng cho ghi chú scalability riêng.
- `[CHECK]` Với mỗi cell, xác nhận không có driver "thắng trắng luôn luôn" trên toàn bộ 25+
  replication (nếu có, supply ratio đó bị lỗi thiết kế, không phải kết quả — sửa ratio, KHÔNG
  sửa để "câu" complementarity).

## 8. Quy tắc chống bịa kết quả (không thương lượng)

1. Hash `rq1_locked_params.json` (SHA-256) + timestamp, ghi log **trước** instance đầu tiên.
2. Chạy cả 60 cell, báo cáo **toàn bộ** đường cong complementarity gain theo alignment —
   không được chỉ trình bày cell có tín hiệu đẹp.
3. Nếu phát hiện cần sửa generator/tham số giữa chừng: dừng, ghi `[DEVIATION]` + lý do, chạy
   lại **toàn bộ grid từ đầu** với tham số mới — không patch một phần.
4. Không tinh chỉnh alignment target, supply ratio, θ range hay q_o formula sau khi xem kết
   quả sơ bộ.
5. Kết luận được chấp nhận dù ra chiều nào — kể cả "complementarity chỉ đáng kể ở alignment
   phi thực tế" là một kết quả hợp lệ, phải viết vào bài, không phải thất bại cần giấu.

## 9. `[DECISION]` Sau khi có kết quả

- Complementarity gain đáng kể (vài % trở lên) và bền qua một dải alignment hợp lý (không chỉ
  ở góc cực đoan) → giữ RQ1 làm kết quả thực nghiệm chính, tăng trọng số target TRE.
- Complementarity nhỏ/chỉ xuất hiện ở alignment phi thực tế → đây vẫn là một finding hợp lệ
  ("hai lớp chỉ bổ trợ khi hành trình OD trùng vùng demand ở mức X") — chuyển toàn bộ trọng
  tâm bài sang phần lý thuyết/cấu trúc (Lemma T4, Proposition T5, và hướng compact-formulation
  nếu có kết quả) — target xuống thuần C&OR.
- Nếu JOINT thua cả hai sequential treatment ở phần lớn cell → đây là tín hiệu ngược đáng chú
  ý, cần điều tra riêng trước khi viết bất kỳ kết luận nào về "giá trị của cùng bid".

## 10. Thứ tự thực thi

1. Implement θ_i, q_o generation (§1.1-1.2); chạy unit-check đơn vị (§1.3).
2. Chạy calibration pass cho q_o + θ range trên batch pilot (§1.4); khoá bộ tham số.
3. Implement alignment metric + chạy calibration curve (khoá tham số generator cho mỗi
   target level, §3).
4. Implement 2 sequential treatment (code path mới, §5).
5. Dry run gate (§7) ở n≤6.
6. Khoá `rq1_locked_params.json` (đầy đủ: θ, q_o, r0, alignment targets, supply ratio, seed
   policy), hash, log.
7. Chạy full 60-cell grid, naive Algorithm C.
8. Phân tích theo §6, xuất toàn bộ đường cong, không cherry-pick.
