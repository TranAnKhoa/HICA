# Spec 2b — Follow-up: ba việc kiểm tra bắt buộc trước khi khóa kết luận Hướng (B)

## Bối cảnh

Report `Spec 2a+2b` (2026-09-10→11) kết luận **Hướng (B)**: route pool thật luôn có
1 component khổng lồ chi phối, nên hạ kỳ vọng T5 xuống "correctness result" và không
đầu tư 2c/2d ở mức speedup lớn.

Kết luận này **có cơ sở tốt nhưng chưa đủ để khóa** — có ba khoảng hở logic cần lấp
trước khi coi đây là kết luận cuối cùng đưa vào thesis. Cả ba đều rẻ so với chi phí đã
bỏ ra cho 2a/2b (B=3/B=4). Làm theo đúng thứ tự dưới đây — việc 1 rẻ nhất và có khả
năng tự nó đảo ngược kết luận, nên làm trước tiên.

**Nguyên tắc xuyên suốt (nhắc lại, không đổi so với spec gốc):** không sửa dominance
rule, không nới lỏng feasibility, không loại bỏ timeout khỏi thống kê, không dừng khi
"thấy tín hiệu đẹp" mà chưa chạy hết lưới đã khóa — áp dụng như cũ, kể cả khi tín hiệu
"đẹp" ở đây là ủng hộ Hướng B (nhẹ nhàng hơn về thiên vị, nhưng vẫn là thiên vị nếu
dừng sớm mà không kiểm hết).

---

## Việc 1 — ★ Ưu tiên cao nhất: Ước lượng speedup thực từ dữ liệu 2b đã có (không cần chạy lại)

### Vấn đề cần trả lời

`largest_component_fraction` cao không tự động nghĩa là decomposition vô dụng. Dữ
liệu đã tự báo cáo cấu trúc **lưỡng cực**: `median_component_size = 1.0` (nhiều driver
singleton) đi kèm 1 component khổng lồ. Nếu chi phí giải MILP tăng siêu tuyến tính
theo kích thước bài toán, decomposition vẫn có thể tiết kiệm đáng kể trên **tổng** chi
phí tính n counterfactual — vì phần lớn winner nếu rơi vào nhóm singleton sẽ được giải
gần O(1) thay vì O(N).

Kết luận "Hướng B → bỏ 2c/2d" hiện chưa tính đại lượng này. Phải tính trước khi khóa.

### Input

`results/2b_raw/*.json` — mỗi file đã có `component_sizes` (list đầy đủ, không chỉ
summary) cho từng instance. Không cần sinh instance mới, không cần chạy CPLEX/DP lại.

### Thủ tục

Với mỗi instance trong `2b_raw/`, và với mỗi số mũ giả định `p ∈ {1, 1.5, 2, 3}`
(quét cả 4 giá trị — không chọn trước một giá trị "có vẻ hợp lý" rồi chỉ báo cáo giá
trị đó):

```python
def speedup_estimate(component_sizes, n_winners_per_component, p):
    """
    component_sizes: list kích thước từng component trong instance
    n_winners_per_component: list cùng độ dài, số winner giả định rơi vào mỗi component
    p: số mũ giả định scaling chi phí giải MILP theo kích thước bài toán

    Vì 2b KHÔNG có Algorithm B (chưa có alloc*), "winner" ở đây là giả định:
    một driver bất kỳ trong route pool CÓ THỂ là winner. Dùng cả hai kịch bản dưới,
    không chỉ một:

    (a) uniform: mọi driver có xác suất là winner bằng nhau
        n_winners_in_P = n_winners_total * (|P| / N)
    (b) upper-bound: TẤT CẢ driver đều là winner (n_winners_total = N) — đây là
        kịch bản xấu nhất cho decomposition (điền đầy mọi component), dùng để
        biết cận trên chi phí, không phải ước lượng kỳ vọng thực tế
    """
    N = sum(component_sizes)
    cost_naive = n_winners_total * (N ** p)
    cost_decomposed = sum(
        n_w * (size ** p)
        for size, n_w in zip(component_sizes, n_winners_per_component)
    )
    return cost_naive / cost_decomposed
```

**Bắt buộc chạy CẢ HAI kịch bản (a) và (b)** cho mỗi instance, không chỉ một — kịch
bản (a) cho ước lượng thực tế hơn (không phải mọi driver đều thắng), kịch bản (b) cho
cận trên bảo thủ. Nếu chỉ chạy (b) và speedup vẫn thấp, đó là bằng chứng mạnh cho
Hướng B. Nếu chỉ chạy (a) và speedup cao, cần cả (b) để biết mức độ nhạy với giả định
tỷ lệ winner.

### Output bắt buộc

Bảng: `speedup_estimate` (median + IQR qua toàn bộ 429 instance đã có) là hàm của
`(p, kịch bản a/b, tau, spatial_mode, supply_ratio)` — tái dùng đúng cấu trúc phân rã
đã có ở report gốc §2.3, không cần lưới tham số mới.

### Ngưỡng đọc kết quả (khóa trước khi xem số, không điều chỉnh sau)

- Nếu `speedup_estimate` (kịch bản a, p=1 — giả định bảo thủ nhất) vẫn **> 5×** ở phần
  lớn (>50%) instance nhờ phần singleton đông đảo → kết luận "bỏ hẳn 2c/2d" hiện tại
  là **sai**, cần viết lại thành "2c/2d vẫn có giá trị nhưng speedup không đồng đều
  giữa winner, khiêm tốn hơn Test8 nhiều".
- Nếu `speedup_estimate` dưới ~2× ở mọi p, mọi kịch bản → củng cố Hướng B, tăng độ tin
  cậy của kết luận gốc.
- Không tự chọn một ngưỡng khác sau khi thấy số liệu để "cứu" kết luận có sẵn theo
  hướng nào — báo cáo số thật, để ngưỡng trên tự quyết định câu trả lời.

---

## Việc 2 — Chạy lại lưới 2b tại B=2

### Vấn đề cần trả lời

Toàn bộ 2b (429 quan sát, nền tảng của kết luận Hướng B) chỉ chạy ở **B=3 cố định**.
Nhưng §1.3 của chính report 2a vừa kết luận: B=2 là mức **duy nhất** phẳng tuyệt đối
đến n=100, trong khi B=3 đã "sống sót chật vật" (vỡ ở tw=240, n>75) và B=4 vỡ trước
n=50 ở hầu hết tw.

Nếu main experiment cuối cùng buộc phải dùng B=2 vì lý do khả thi tính toán, thì kết
luận Hướng B — vốn chỉ được kiểm ở B=3 — **có thể không áp dụng được** cho B thực tế
sẽ dùng. Bundle size nhỏ hơn có cơ chế hợp lý để giảm overlap giữa route pool của các
driver khác nhau (mỗi route chạm ít order hơn → ít driver tình cờ chạm cùng order).

### Thủ tục

Chạy lại **đúng nguyên lưới đã khóa ở `config/grid_2b.yaml`** (tau × spatial_mode ×
supply_ratio × seed), chỉ đổi `B: 3 → B: 2`. Không đổi bất kỳ tham số nào khác.

```
Lưới: n ∈ {30, 50}  ×  tau (6 giá trị)  ×  spatial_mode (2)  ×  supply_ratio (3)  ×  seed (10)
    = 720 lần chạy (giống hệt cấu trúc 2b gốc, đổi B)
```

Vì B=2 theo §1.3 chạy dưới 1 giây/instance ngay cả ở n=100, chi phí máy cho toàn bộ
720 lần chạy này thấp hơn nhiều so với những gì đã tốn cho phần B=3/B=4 của 2a — **nên
chạy đủ 720, không cần rút gọn độ phủ như đã làm ở 2b gốc (59.6%)**. Nếu vẫn không đủ
thời gian, có thể mở rộng thêm n∈{75,100} vì B=2 rẻ (đã có `probe_scaling.py` cho khung
này).

### Output bắt buộc

Đúng cấu trúc bảng đã dùng ở report gốc §2.3 (theo n, theo mode, theo supply_ratio,
theo tau) — nhưng cho B=2, đặt cạnh bảng B=3 gốc để so sánh trực tiếp.

### Đọc kết quả

- Nếu B=2 cho `largest_component_fraction` thấp hơn rõ rệt (đặc biệt nếu chạm ngưỡng
  <0.3 mà B=3 chưa từng đạt) → kết luận Hướng B/A phụ thuộc B, phải viết lại toàn bộ
  §3 report gốc theo B, không phải một kết luận chung cho mọi B.
- Nếu B=2 vẫn cho fraction cao tương tự B=3 → củng cố Hướng B thêm một bậc (đúng ở cả
  hai B chính đang xét), kết luận có thể coi là bền theo B.

---

## Việc 3 — Hoàn thành nốt phần n=50 còn thiếu trong lưới 2b (B=3, gốc)

### Vấn đề cần trả lời

Report gốc dừng ở 429/720 (59.6%) và biện minh phần n=50 chưa chạy (`supply_ratio ∈
{0.6, 1.0}`, `spatial_mode = clustered`) bằng lập luận trực giác *"không có cơ chế nào
để đảo ngược xu hướng gộp cụm"* — đây là một **dự đoán chưa kiểm chứng**, dùng để biện
minh cho việc dừng sớm. Bản thân guideline gốc đã cảnh báo đúng dạng lỗi này: quyết
định dừng dựa trên niềm tin về xu hướng thay vì dữ liệu thật, dù ở đây thiên về hướng
"khiêm tốn" (Hướng B) chứ không phải hướng "kịch tính", vẫn là một khoảng trống thực
nghiệm cần lấp trước khi khóa kết luận.

### Thủ tục

Chạy nốt các ô còn thiếu của lưới `grid_2b.yaml` gốc (B=3):

```
n = 50  ×  tau (6 giá trị)  ×  spatial_mode = clustered  ×  supply_ratio ∈ {0.3,0.6,1.0}  ×  seed (10)
n = 50  ×  tau (6 giá trị)  ×  spatial_mode = dispersed  ×  supply_ratio ∈ {0.6,1.0}      ×  seed (10)
```

(Phần `n=50 × dispersed × supply_ratio=0.3` đã có trong 429 dòng — không chạy lại.)

Dùng đúng `run_2b.py` đã có khả năng resume — không viết script mới, không đổi
`instance_gen.py`/`conflict_graph.py`.

### Output bắt buộc

Cập nhật bảng §2.3 (theo n, mode, supply_ratio) với đầy đủ 720/720 dòng, không còn ô
trống. Nếu xu hướng "n=50 tệ hơn n=30" và "supply cao hơn → gộp cụm nhiều hơn" được
xác nhận đúng như dự đoán ở bản dừng sớm → ghi rõ trong báo cáo cập nhật rằng dự đoán
đã được kiểm chứng, không còn là ngoại suy. Nếu xu hướng đảo ngược ở phần dữ liệu mới
→ viết lại kết luận theo dữ liệu thật, không giữ nguyên kết luận cũ.

---

## Thứ tự thực hiện và điều kiện dừng

```
1. Việc 1 (xử lý dữ liệu có sẵn, không chạy gì mới)  ← làm trước, rẻ nhất
     → nếu speedup_estimate cao → dừng lại đây, báo cáo ngay, ĐỔI kết luận
       thành "2c/2d vẫn có giá trị có điều kiện" trước khi làm Việc 2/3
     → nếu speedup_estimate thấp → tiếp tục Việc 2

2. Việc 2 (chạy lại ở B=2)
     → nếu B=2 khác biệt rõ so với B=3 → viết lại kết luận theo B,
       CÂN NHẮC lặp lại Việc 1 trên dữ liệu B=2 mới
     → nếu B=2 giống B=3 → tiếp tục Việc 3

3. Việc 3 (đóng nốt lưới n=50, B=3)
     → chỉ cần làm nếu Việc 1 và 2 đều củng cố Hướng B, để đóng lưới hoàn chỉnh
       trước khi khóa kết luận cuối cùng
```

**Không làm cả ba song song rồi chọn kết quả nào "đẹp hơn"** — làm tuần tự theo đúng
thứ tự trên, vì Việc 1 rẻ nhất và có khả năng đảo ngược kết luận cao nhất; không cần
tốn công Việc 2/3 nếu Việc 1 đã cho thấy cần viết lại toàn bộ hướng đi.

---

## Việc KHÔNG được làm (nhắc lại, áp dụng như spec gốc)

- Không chọn một giá trị `p` hay một kịch bản (a)/(b) duy nhất ở Việc 1 rồi chỉ báo
  cáo giá trị đó — phải quét đủ và báo cáo toàn bộ.
- Không dừng Việc 2/3 giữa chừng vì "đã thấy đủ tín hiệu" mà không ghi rõ phần bị bỏ
  qua, đúng tinh thần minh bạch đã áp dụng tốt trong report gốc.
- Không lặng lẽ đổi ngưỡng đọc kết quả (>5×, <2× ở Việc 1) sau khi thấy số liệu để
  khớp với kết luận đã viết sẵn.
- Không sửa `dp_labeling.py`, `conflict_graph.py`, dominance rule — ba việc này chỉ
  cần chạy lại lưới hoặc xử lý dữ liệu đã có, không đụng vào thuật toán cốt lõi.

---

## Sau khi hoàn thành

Gửi lại một bản cập nhật của report gốc (không cần viết lại từ đầu — chỉ thêm phần
"Cập nhật sau follow-up" với kết quả 3 việc trên), kèm kết luận cuối cùng đã được kiểm
đủ ba góc: (1) tổng chi phí tính toán thực tế, không chỉ fraction; (2) tính bền theo B;
(3) đóng đủ lưới n=50 đã khóa.